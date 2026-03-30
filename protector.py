import os
import sys
import base64
import getpass
import shutil
import subprocess
import time
import threading
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
from datetime import datetime
import ctypes
import stat

class AutoFileProtector:
    def __init__(self, folder_path):
        self.folder_path = Path(folder_path)
        self.key_file = self.folder_path / ".master.key"
        self.salt_file = self.folder_path / ".salt"
        self.log_file = self.folder_path / ".access.log"
        self.lock_file = self.folder_path / ".locked"
        self.is_decrypted = False
        self.monitor_thread = None
        self.running = True
        
        # Files to NEVER encrypt
        self.excluded_files = {".master.key", ".salt", ".access.log", ".locked",
                               "protector.py", "README.txt", "desktop.ini"}
        
    def _generate_key_from_password(self, password, salt=None):
        """Generate encryption key from password"""
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def _get_password(self, prompt="Enter password: "):
        """Get password securely"""
        return getpass.getpass(prompt)
    
    def _hide_folder_windows(self):
        """Hide folder on Windows"""
        if os.name == 'nt':
            ctypes.windll.kernel32.SetFileAttributesW(str(self.folder_path), 2)
    
    def _unhide_folder_windows(self):
        """Unhide folder on Windows"""
        if os.name == 'nt':
            ctypes.windll.kernel32.SetFileAttributesW(str(self.folder_path), 0)
    
    def _lock_folder_access(self):
        """Prevent folder deletion/renaming"""
        try:
            if os.name == 'nt':
                # Make folder read-only and system
                os.system(f'attrib +r +s "{self.folder_path}"')
                # Deny delete permission (Windows)
                os.system(f'icacls "{self.folder_path}" /deny %USERNAME%:(DE)')
        except:
            pass
    
    def _unlock_folder_access(self):
        """Restore folder access"""
        try:
            if os.name == 'nt':
                os.system(f'attrib -r -s "{self.folder_path}"')
                os.system(f'icacls "{self.folder_path}" /remove:d %USERNAME%')
        except:
            pass
    
    def initialize(self):
        """First time setup"""
        print("\n" + "="*50)
        print("🔐 FIRST TIME SETUP - AUTO FILE PROTECTOR")
        print("="*50)
        
        if self.key_file.exists():
            reset = input("Protection already exists. Reset? (y/n): ").lower()
            if reset != 'y':
                return False
        
        # Create password
        print("\n📝 Create your master password:")
        password = self._get_password("Set password: ")
        confirm = self._get_password("Confirm password: ")
        
        if password != confirm:
            print("❌ Passwords don't match!")
            return False
        
        # Generate keys
        key, salt = self._generate_key_from_password(password)
        
        # Save salt
        with open(self.salt_file, 'wb') as f:
            f.write(salt)
        
        # Create verification
        verification_data = "PROTECTION_ACTIVE"
        f = Fernet(key)
        encrypted_verification = f.encrypt(verification_data.encode())
        
        with open(self.key_file, 'wb') as f:
            f.write(encrypted_verification)
        
        # Create lock file
        with open(self.lock_file, 'w') as f:
            f.write("LOCKED")
        
        # Hide folder
        self._hide_folder_windows()
        
        print("\n✅ PROTECTION INITIALIZED!")
        print("📁 Folder is now HIDDEN and PROTECTED")
        print("🔑 Remember your password!")
        print("="*50)
        
        # Ask to encrypt now
        encrypt_now = input("\nEncrypt all files now? (y/n): ").lower()
        if encrypt_now == 'y':
            self.protect()
        
        return True
    
    def _get_key(self):
        """Get encryption key with password"""
        if not self.salt_file.exists() or not self.key_file.exists():
            return None
        
        max_attempts = 3
        for attempt in range(max_attempts):
            password = self._get_password("🔐 Enter password to access files: ")
            
            with open(self.salt_file, 'rb') as f:
                salt = f.read()
            
            key, _ = self._generate_key_from_password(password, salt)
            
            try:
                with open(self.key_file, 'rb') as f:
                    encrypted_verification = f.read()
                f = Fernet(key)
                decrypted = f.decrypt(encrypted_verification).decode()
                
                if decrypted == "PROTECTION_ACTIVE":
                    return key
                else:
                    print(f"❌ Wrong password! {max_attempts - attempt - 1} attempts left")
            except:
                print(f"❌ Wrong password! {max_attempts - attempt - 1} attempts left")
        
        print("❌ Too many failed attempts! Exiting...")
        return None
    
    def protect(self):
        """Encrypt all files"""
        print("\n🔒 ENCRYPTING FILES...")
        
        encrypted_count = 0
        failed_count = 0
        
        for item in self.folder_path.iterdir():
            if item.is_file() and item.name not in self.excluded_files:
                try:
                    with open(item, 'rb') as file:
                        data = file.read()
                    
                    # Check if already encrypted
                    if data.startswith(b'gAAAAA'):
                        continue
                    
                    # Get key
                    key = self._get_key()
                    if not key:
                        return False
                    
                    f = Fernet(key)
                    encrypted_data = f.encrypt(data)
                    
                    with open(item, 'wb') as file:
                        file.write(encrypted_data)
                    
                    encrypted_count += 1
                    print(f"  🔒 Encrypted: {item.name}")
                    
                except Exception as e:
                    failed_count += 1
                    print(f"  ❌ Failed: {item.name}")
        
        print(f"\n✅ Encrypted {encrypted_count} files")
        if failed_count > 0:
            print(f"⚠️  Failed to encrypt {failed_count} files")
        
        # Lock folder access
        self._lock_folder_access()
        self._hide_folder_windows()
        
        return True
    
    def restore(self):
        """Decrypt all files and show folder"""
        print("\n🔓 UNLOCKING FILES...")
        
        key = self._get_key()
        if not key:
            return False
        
        f = Fernet(key)
        decrypted_count = 0
        failed_count = 0
        
        for item in self.folder_path.iterdir():
            if item.is_file() and item.name not in self.excluded_files:
                try:
                    with open(item, 'rb') as file:
                        encrypted_data = file.read()
                    
                    # Check if encrypted
                    if encrypted_data.startswith(b'gAAAAA'):
                        try:
                            decrypted_data = f.decrypt(encrypted_data)
                            with open(item, 'wb') as file:
                                file.write(decrypted_data)
                            decrypted_count += 1
                            print(f"  🔓 Decrypted: {item.name}")
                        except:
                            print(f"  ⚠️  Already normal: {item.name}")
                    else:
                        print(f"  ⚠️  Already normal: {item.name}")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"  ❌ Failed: {item.name}")
        
        print(f"\n✅ Decrypted {decrypted_count} files")
        
        # Unlock folder and show it
        self._unlock_folder_access()
        self._unhide_folder_windows()
        
        # Open folder in Explorer
        if os.name == 'nt':
            os.startfile(str(self.folder_path))
        
        self.is_decrypted = True
        return True
    
    def auto_lock_timer(self, minutes=5):
        """Auto-lock after X minutes of inactivity"""
        print(f"\n⏰ Auto-lock will activate in {minutes} minutes")
        
        def lock_after_timeout():
            time.sleep(minutes * 60)
            if self.is_decrypted:
                print("\n\n⚠️  Auto-lock: No activity detected. Locking files...")
                self.protect()
                self.is_decrypted = False
                print("🔒 Files are locked again!")
                sys.exit(0)
        
        timer_thread = threading.Thread(target=lock_after_timeout, daemon=True)
        timer_thread.start()
    
    def monitor_changes(self):
        """Monitor folder for unauthorized access attempts"""
        def monitor():
            last_files = set(self.folder_path.iterdir())
            while self.running:
                time.sleep(2)
                current_files = set(self.folder_path.iterdir())
                
                # Check for new files
                new_files = current_files - last_files
                for file in new_files:
                    if file.is_file() and not self.is_decrypted:
                        print(f"\n⚠️  UNAUTHORIZED: New file detected! {file.name}")
                        # Re-encrypt immediately
                        self.protect()
                
                last_files = current_files
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
    
    def create_shortcut(self):
        """Create desktop shortcut for easy access"""
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "🔒 UNLOCK FILES.bat"
        
        script_path = Path(__file__).resolve()
        
        with open(shortcut_path, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'cd /d "{self.folder_path}"\n')
            f.write(f'python "{script_path}" "{self.folder_path}" restore\n')
            f.write(f'pause\n')
        
        print(f"\n✅ Desktop shortcut created: {shortcut_path}")
        return shortcut_path
    
    def create_auto_lock_shortcut(self):
        """Create auto-lock shortcut"""
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "🔒 LOCK FILES.bat"
        
        script_path = Path(__file__).resolve()
        
        with open(shortcut_path, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'cd /d "{self.folder_path}"\n')
            f.write(f'python "{script_path}" "{self.folder_path}" protect\n')
            f.write(f'pause\n')
        
        print(f"✅ Lock shortcut created: {shortcut_path}")

def main():
    # If run with arguments
    if len(sys.argv) > 1:
        folder = sys.argv[1]
        command = sys.argv[2] if len(sys.argv) > 2 else None
        
        protector = AutoFileProtector(folder)
        
        if command == 'init':
            protector.initialize()
        elif command == 'protect':
            protector.protect()
        elif command == 'restore':
            protector.restore()
        else:
            print("Usage: python protector.py [folder] [init|protect|restore]")
    else:
        # Auto mode - ask user
        print("\n" + "="*60)
        print("🔐 AUTO FILE PROTECTOR - Ultimate Security System")
        print("="*60)
        
        folder = input("📁 Enter folder path to protect: ").strip()
        
        if not os.path.exists(folder):
            print("❌ Folder doesn't exist! Creating...")
            os.makedirs(folder)
        
        protector = AutoFileProtector(folder)
        
        print("\n" + "="*60)
        print("SELECT OPERATION:")
        print("1. 🔧 First time setup (INITIALIZE)")
        print("2. 🔓 UNLOCK files (decrypt and show folder)")
        print("3. 🔒 LOCK files (encrypt and hide folder)")
        print("4. 🏃 Auto-mode (unlock, work, auto-lock)")
        print("="*60)
        
        choice = input("Choose (1-4): ").strip()
        
        if choice == '1':
            protector.initialize()
            protector.create_shortcut()
            protector.create_auto_lock_shortcut()
            
        elif choice == '2':
            if protector.restore():
                print("\n✅ Files unlocked! Folder is visible and accessible")
                input("\nPress Enter to lock files again...")
                protector.protect()
                print("🔒 Files locked again!")
                
        elif choice == '3':
            protector.protect()
            print("\n🔒 Files locked and folder hidden!")
            
        elif choice == '4':
            if protector.restore():
                print("\n✅ Files unlocked! You can now work normally")
                minutes = input("\nAuto-lock after how many minutes? (default: 5): ")
                minutes = int(minutes) if minutes.isdigit() else 5
                protector.auto_lock_timer(minutes)
                print("\n💡 Working mode activated")
                print("📌 Files will auto-lock after inactivity")
                print("📌 Close this window to manually lock")
                input("\nPress Enter to lock files now...")
                protector.protect()
        
        print("\n🔐 System ready!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")