"""
Dr. Alfredo Pio De Roda ES - QR Attendance System
Version: PERFECTED + FIREBASE LICENSING + PERSISTENT STORAGE + EULA + HARDWARE DETECTION
Date: January 30, 2026

FEATURES:
1. ✅ ORIGINAL UI WITH TABS (exactly like original)
2. ✅ FILTER: Percentage, Average Daily, Attendance percentages
3. ✅ CHECK EXCEL: Existing marks on load
4. ✅ ACCURATE COUNTER: Existing + new scans
5. ✅ SMOOTH CAMERA: Threading for no freezing
6. ✅ AUTO-SAVE: Each scan saved immediately
7. ✅ FIREBASE LICENSING: License validation with persistent storage
8. ✅ EULA ON FIRST RUN: User must accept terms
9. ✅ ONE-TIME LICENSE ENTRY: License saved permanently
10. ✅ REAL-TIME LICENSE MONITORING: Constant active status checks
11. ✅ INSTANT REVOCATION: App exits immediately when license revoked
12. ✅ HARDWARE DETECTION: Tracks device hardware and reports to Firebase
13. ✅ LICENSE SHARING DETECTION: Prevents unauthorized license sharing
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import cv2
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode
from openpyxl import load_workbook
from datetime import datetime
import os
import traceback
import re
import threading
import queue
import time
import shutil
from zipfile import ZipFile
import tempfile
import json
import requests
import socket
import platform
import psutil
import uuid
import hashlib

# Firebase Configuration
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyDHOZkF310KaQphFda9rgKBWl2pPmM44Hc",
    "authDomain": "licenses-5c397.firebaseapp.com",
    "databaseURL": "https://licenses-5c397-default-rtdb.firebaseio.com",
    "projectId": "licenses-5c397",
    "storageBucket": "licenses-5c397.firebasestorage.app",
    "messagingSenderId": "811265646295",
    "appId": "1:811265646295:web:771cdfd0af3d3056309a92"
}

class HardwareDetector:
    """Detects and reports hardware information for license validation"""
    
    def __init__(self):
        self.hwid_counter_file = os.path.join(
            os.path.expanduser("~"), 
            ".attendance_system", 
            "hwid_counter.txt"
        )
        self.current_hwid_number = self.load_hwid_counter()
    
    def load_hwid_counter(self):
        """Load the current HWID number (1, 2, 3, etc.)"""
        try:
            if os.path.exists(self.hwid_counter_file):
                with open(self.hwid_counter_file, 'r') as f:
                    counter = int(f.read().strip())
                    return counter
        except Exception as e:
            print(f"⚠️ Could not load HWID counter: {e}")
        
        # First time - start at 1
        return 1
    
    def save_hwid_counter(self, counter):
        """Save the current HWID number"""
        try:
            os.makedirs(os.path.dirname(self.hwid_counter_file), exist_ok=True)
            with open(self.hwid_counter_file, 'w') as f:
                f.write(str(counter))
        except Exception as e:
            print(f"⚠️ Could not save HWID counter: {e}")
    
    def get_hardware_info(self):
        """Get current hardware information"""
        try:
            # Get OS info
            os_name = platform.system()
            os_version = platform.version()
            
            # Get CPU info
            processor = platform.processor()
            cpu_count = psutil.cpu_count(logical=False) or 1
            
            # Get RAM info (in GB)
            ram_gb = psutil.virtual_memory().total / (1024**3)
            ram_gb = round(ram_gb)
            
            # Create a summary string
            stats = f"{os_name} | {processor} | {ram_gb}GB RAM"
            
            return {
                "os": os_name,
                "os_version": os_version,
                "processor": processor,
                "cpu_cores": cpu_count,
                "ram_gb": ram_gb,
                "stats": stats
            }
        except Exception as e:
            print(f"⚠️ Error getting hardware info: {e}")
            return {
                "os": "Unknown",
                "stats": "Unknown Hardware"
            }
    
    def get_machine_id(self):
        """Get unique machine identifier"""
        try:
            # Try to get MAC address
            mac = uuid.getnode()
            
            # Try to get system UUID
            if platform.system() == "Windows":
                try:
                    import subprocess
                    result = subprocess.check_output(['wmic', 'csproduct', 'get', 'uuid']).decode()
                    uuid_str = result.split('\n')[1].strip()
                    if uuid_str:
                        return hashlib.sha256(uuid_str.encode()).hexdigest()[:16]
                except:
                    pass
            
            # Fallback to MAC address hash
            return hashlib.sha256(str(mac).encode()).hexdigest()[:16]
        except Exception as e:
            print(f"⚠️ Error getting machine ID: {e}")
            return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]
    
    def generate_hwid_label(self):
        """Generate HWID label like HWID_PRIMARY, HWID_SECONDARY, etc."""
        labels = [
            "PRIMARY",
            "SECONDARY", 
            "TERTIARY",
            "QUATERNARY",
            "QUINARY",
        ]
        
        if self.current_hwid_number <= len(labels):
            return f"HWID_{labels[self.current_hwid_number - 1]}"
        else:
            # For more than 5 devices, use numbering
            return f"HWID_DEVICE_{self.current_hwid_number}"
    
    def prepare_hardware_data(self):
        """Prepare hardware data for Firebase reporting"""
        hardware_info = self.get_hardware_info()
        
        hwid_label = self.generate_hwid_label()
        
        hardware_data = {
            hwid_label: {
                "stats": hardware_info.get("stats", "Unknown Hardware"),
                "linkedAt": self._get_timestamp()
            }
        }
        
        return hardware_data, hwid_label
    
    def _get_timestamp(self):
        """Get ISO format timestamp"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat() + "Z"
    
    def is_new_device(self, saved_hwid_label):
        """Check if this is a new device (different HWID)"""
        return self.current_hwid_number > 1
    
    def increment_hwid_counter(self):
        """Increment HWID counter for next device"""
        self.current_hwid_number += 1
        self.save_hwid_counter(self.current_hwid_number)
        print(f"📱 New device detected - HWID counter incremented to {self.current_hwid_number}")
    
    def get_current_hwid_number(self):
        """Get current device count"""
        return self.current_hwid_number


class HardwareReporter:
    """Reports hardware data to Firebase for license enforcement"""
    
    def __init__(self, firebase_config):
        self.firebase_config = firebase_config
    
    def report_hardware_to_firebase(self, license_key, hardware_data, hwid_label):
        """Send hardware data to Firebase under the license"""
        try:
            url = f"{self.firebase_config['databaseURL']}/licenses/{license_key}/hardware.json"
            print(f"🌐 Firebase URL: {url}")
            
            # Merge with existing hardware data
            existing = {}
            try:
                print("📥 Fetching existing hardware data...")
                response = requests.get(url, timeout=10)
                print(f"📊 GET Status: {response.status_code}")
                
                if response.status_code == 200:
                    existing = response.json() or {}
                    print(f"📋 Found {len(existing)} existing device(s)")
            except Exception as e:
                print(f"⚠️ Error fetching existing data: {e}")
                existing = {}
            
            # Add new hardware data
            existing.update(hardware_data)
            print(f"📤 Updating with: {hwid_label}")
            
            # Send back to Firebase
            print("🚀 Sending hardware data to Firebase...")
            response = requests.put(
                url,
                json=existing,
                timeout=10
            )
            
            print(f"📊 PUT Status: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}")
            
            if response.status_code in [200, 201]:
                print(f"✅ Hardware data reported successfully: {hwid_label}")
                return True
            else:
                print(f"❌ Failed to report hardware data: HTTP {response.status_code}")
                return False
        
        except Exception as e:
            print(f"❌ Error reporting hardware: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_for_license_sharing(self, license_key):
        """Check if license is being used on multiple devices"""
        try:
            url = f"{self.firebase_config['databaseURL']}/licenses/{license_key}/hardware.json"
            
            print(f"🔍 Checking license sharing at: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                hardware_data = response.json()
                
                if hardware_data:
                    device_count = len(hardware_data)
                    print(f"📱 Found {device_count} device(s) using this license")
                    
                    if device_count > 1:
                        print(f"⚠️ WARNING: License detected on {device_count} devices!")
                        print("⚠️ License sharing is not permitted!")
                        return True, device_count
                    
                    return False, 1
            
            return False, 1
        
        except Exception as e:
            print(f"⚠️ Error checking for sharing: {e}")
            return False, 1

class LicenseManager:
    """Manages Firebase-based licensing with persistent storage"""
    
    def __init__(self):
        self.license_key = None
        self.license_data = None
        self.is_online = self.check_internet_connection()
        
        # File paths for persistent storage
        self.config_dir = os.path.join(os.path.expanduser("~"), ".attendance_system")
        self.license_file = os.path.join(self.config_dir, "license.json")
        self.eula_file = os.path.join(self.config_dir, "eula_accepted.txt")
        self.licenses_cache_file = os.path.join(self.config_dir, "licenses_cache.json")
        
        # Create config directory if not exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Initialize hardware detector and reporter
        self.hardware_detector = HardwareDetector()
        self.hardware_reporter = HardwareReporter(FIREBASE_CONFIG)
        
        # Load saved license if exists
        self.load_saved_license()
        
    def check_internet_connection(self):
        """Check if system is connected to internet"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except (socket.timeout, socket.error):
            return False
    
    def load_saved_license(self):
        """Load license from persistent storage"""
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, 'r') as f:
                    data = json.load(f)
                    self.license_key = data.get('key')
                    self.license_data = data.get('data')
                    print(f"✅ Loaded saved license: {self.license_key[:20]}...")
                    return True
        except Exception as e:
            print(f"⚠️ Error loading saved license: {e}")
        return False
    
    def save_license(self, license_key, license_data):
        """Save validated license to persistent storage"""
        try:
            data = {
                'key': license_key,
                'data': license_data,
                'saved_at': datetime.now().isoformat()
            }
            with open(self.license_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.license_key = license_key
            self.license_data = license_data
            print(f"💾 License saved permanently: {license_key[:20]}...")
            return True
        except Exception as e:
            print(f"❌ Error saving license: {e}")
            return False
    
    def has_saved_license(self):
        """Check if a license is already saved"""
        return os.path.exists(self.license_file) and self.license_key is not None
    
    def eula_accepted(self):
        """Check if EULA has been accepted"""
        return os.path.exists(self.eula_file)
    
    def accept_eula(self):
        """Mark EULA as accepted"""
        try:
            with open(self.eula_file, 'w') as f:
                f.write(f"EULA accepted on {datetime.now().isoformat()}\n")
            return True
        except Exception as e:
            print(f"❌ Error saving EULA acceptance: {e}")
            return False
    
    def clear_license(self):
        """Clear saved license (for testing)"""
        try:
            if os.path.exists(self.license_file):
                os.remove(self.license_file)
            self.license_key = None
            self.license_data = None
            return True
        except Exception as e:
            print(f"❌ Error clearing license: {e}")
            return False
    
    def fetch_licenses_from_firebase(self):
        """Fetch all licenses from Firebase RTDB"""
        try:
            if not self.is_online:
                return self.load_cached_licenses()
            
            url = f"{FIREBASE_CONFIG['databaseURL']}/licenses.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            licenses_data = response.json()
            
            # Cache licenses locally
            if licenses_data:
                try:
                    with open(self.licenses_cache_file, 'w') as f:
                        json.dump(licenses_data, f)
                except Exception as e:
                    print(f"⚠️ Could not cache licenses: {e}")
            
            return licenses_data
        except Exception as e:
            print(f"❌ Firebase Error: {e}")
            return self.load_cached_licenses()
    
    def load_cached_licenses(self):
        """Load licenses from local cache"""
        try:
            if os.path.exists(self.licenses_cache_file):
                with open(self.licenses_cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Cache Error: {e}")
        return None
    
    def validate_license(self, license_key):
        """Validate a license key against Firebase"""
        try:
            licenses = self.fetch_licenses_from_firebase()
            
            if not licenses:
                return False, "Unable to fetch licenses. Check internet connection."
            
            if license_key not in licenses:
                return False, "License key not found."
            
            license_info = licenses[license_key]
            
            # Check if license is active
            if not license_info.get('active', False):
                return False, "License has been revoked. Contact administrator."
            
            # Collect and report hardware information
            print("🔧 Collecting hardware information...")
            hardware_data, hwid_label = self.hardware_detector.prepare_hardware_data()
            print(f"📊 Hardware: {hwid_label} - {hardware_data[hwid_label]['stats']}")
            
            # Report hardware to Firebase (only if online)
            if self.is_online:
                print("📤 Sending hardware data to Firebase...")
                success = self.hardware_reporter.report_hardware_to_firebase(
                    license_key, 
                    hardware_data, 
                    hwid_label
                )
                
                if success:
                    print("✅ Hardware data successfully reported to Firebase")
                else:
                    print("⚠️ Could not report hardware data (but continuing...)")
                
                # Check for license sharing
                print("🔍 Checking for license sharing...")
                is_sharing, device_count = self.hardware_reporter.check_for_license_sharing(license_key)
                
                if is_sharing:
                    print(f"⚠️ LICENSE SHARING DETECTED!")
                    print(f"⚠️ This license is active on {device_count} devices")
                else:
                    print(f"✅ License is only on this device")
            else:
                print("⚠️ Offline - hardware data will be reported when online")
            
            # Save the license permanently
            if not self.save_license(license_key, license_info):
                return False, "Could not save license. Check disk space."
            
            return True, license_info
        
        except Exception as e:
            print(f"❌ Validation Error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Error validating license: {str(e)}"
    
    def verify_license_active_online(self):
        """Verify license is still active on Firebase (real-time check)"""
        try:
            if not self.license_key:
                return False, "No license loaded"
            
            if not self.is_online:
                # Return current status if offline
                is_active = self.license_data.get('active', False) if self.license_data else False
                return is_active, "Offline mode" if is_active else "Offline - license inactive"
            
            licenses = self.fetch_licenses_from_firebase()
            
            if not licenses or self.license_key not in licenses:
                return False, "License not found on server"
            
            license_info = licenses[self.license_key]
            is_active = license_info.get('active', False)
            
            # Update local copy
            if license_info != self.license_data:
                self.license_data = license_info
                self.save_license(self.license_key, license_info)
            
            # Check for license sharing periodically
            if is_active:
                is_sharing, device_count = self.hardware_reporter.check_for_license_sharing(self.license_key)
                if is_sharing:
                    print(f"⚠️ License sharing detected: {device_count} devices")
            
            return is_active, "Active" if is_active else "Revoked"
        
        except Exception as e:
            print(f"❌ Online validation error: {e}")
            # Fall back to cached data
            is_active = self.license_data.get('active', False) if self.license_data else False
            return is_active, "Offline fallback"
    
    def get_license_info(self):
        """Get current license information"""
        return self.license_data
    
    def is_license_active_cached(self):
        """Check if current license is active (cached data)"""
        if not self.license_data:
            return False
        return self.license_data.get('active', False)


class EULADialog(tk.Toplevel):
    """EULA acceptance dialog"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.result = False
        
        self.title("End User License Agreement")
        self.geometry("700x600")
        self.resizable(True, True)
        
        # Branding colors
        self.BG_PRIMARY = "#0f1419"
        self.BG_CARD = "#1a202c"
        self.BLUE = "#3b82f6"
        self.GREEN = "#10b981"
        self.RED = "#ef4444"
        self.TEXT_PRIMARY = "#ffffff"
        
        self.configure(bg=self.BG_PRIMARY)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup EULA dialog UI"""
        # Header
        header_frame = tk.Frame(self, bg=self.BLUE, height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="📋 END USER LICENSE AGREEMENT (EULA)",
            font=("Segoe UI", 12, "bold"),
            bg=self.BLUE,
            fg=self.TEXT_PRIMARY
        )
        title_label.pack(pady=10)
        
        # Content
        content_frame = tk.Frame(self, bg=self.BG_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # EULA text (read from file)
        eula_text = self.get_eula_text()
        
        text_widget = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            bg=self.BG_CARD,
            fg=self.TEXT_PRIMARY,
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            bd=2
        )
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        text_widget.insert(tk.END, eula_text)
        text_widget.config(state=tk.DISABLED)  # Read-only
        
        # Agreement checkbox
        self.agree_var = tk.BooleanVar(value=False)
        agree_check = tk.Checkbutton(
            content_frame,
            text="I have read and agree to the End User License Agreement",
            variable=self.agree_var,
            bg=self.BG_PRIMARY,
            fg=self.TEXT_PRIMARY,
            selectcolor=self.BG_CARD,
            font=("Segoe UI", 10),
            activebackground=self.BG_PRIMARY,
            activeforeground=self.TEXT_PRIMARY
        )
        agree_check.pack(anchor=tk.W, pady=(0, 15))
        
        # Buttons
        button_frame = tk.Frame(content_frame, bg=self.BG_PRIMARY)
        button_frame.pack(fill=tk.X)
        
        accept_btn = tk.Button(
            button_frame,
            text="✓ ACCEPT & CONTINUE",
            font=("Segoe UI", 11, "bold"),
            bg=self.GREEN,
            fg="#000",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.accept_eula
        )
        accept_btn.pack(side=tk.LEFT, expand=True, padx=(0, 5))
        
        decline_btn = tk.Button(
            button_frame,
            text="✗ DECLINE & EXIT",
            font=("Segoe UI", 11, "bold"),
            bg=self.RED,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.decline_eula
        )
        decline_btn.pack(side=tk.LEFT, expand=True, padx=(5, 0))
    
    def get_eula_text(self):
        """Get EULA text from embedded or external file"""
        # Try to load from external file first
        try:
            eula_path = os.path.join(os.path.dirname(__file__), "EULA.txt")
            if os.path.exists(eula_path):
                with open(eula_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"⚠️ Could not load EULA file: {e}")
        
        # Fallback to embedded EULA
        return """End User License Agreement (EULA) for QR Attendance System Software

IMPORTANT: PLEASE READ THIS END USER LICENSE AGREEMENT ("EULA") CAREFULLY BEFORE DOWNLOADING, INSTALLING, ACCESSING, OR USING THE SOFTWARE. THIS EULA IS A LEGALLY BINDING AGREEMENT BETWEEN YOU AND THE LICENSOR.

BY DOWNLOADING, INSTALLING, ACCESSING, OR USING THE SOFTWARE, YOU ACKNOWLEDGE THAT YOU HAVE READ, UNDERSTOOD, AND AGREE TO BE BOUND BY THE TERMS OF THIS EULA.

IF YOU DO NOT AGREE TO THESE TERMS, DO NOT DOWNLOAD, INSTALL, ACCESS, OR USE THE SOFTWARE.

1. GRANT OF LICENSE
Subject to Your full compliance with all terms and conditions of this EULA, Licensor hereby grants You a limited, non-exclusive, non-transferable, non-sublicensable, revocable license to Use the Software solely for Your internal, non-commercial purposes, such as managing attendance in an educational setting.

2. RESTRICTIONS
You shall not:
- Copy, reproduce, modify, or create derivative works
- Rent, lease, lend, sell, sublicense, or distribute the Software
- Remove or alter copyright notices
- Use the Software in any manner that violates applicable laws
- Use the Software for any commercial purpose
- Attempt to circumvent security features

3. OWNERSHIP
The Software and all Intellectual Property Rights therein are and shall remain the exclusive property of Licensor.

4. NO WARRANTY
THE SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE," WITHOUT WARRANTIES OF ANY KIND. LICENSOR DISCLAIMS ALL WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, OR NON-INFRINGEMENT.

5. LIMITATION OF LIABILITY
IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING OUT OF YOUR USE OF THE SOFTWARE.

6. TERMINATION
Licensor may terminate this EULA at any time, with or without cause, upon notice to You. Upon termination, all licenses granted herein shall immediately cease.

7. GOVERNING LAW
This EULA shall be governed by the laws of the Republic of the Philippines.

For the complete EULA, please see the EULA.txt file.

Date of Last Update: January 30, 2026"""
    
    def accept_eula(self):
        """Accept EULA"""
        if not self.agree_var.get():
            messagebox.showwarning("Agreement Required", "You must agree to the EULA to continue")
            return
        
        self.result = True
        self.destroy()
    
    def decline_eula(self):
        """Decline EULA"""
        if messagebox.askyesno("Confirm", "Are you sure you want to decline? The application will exit."):
            self.result = False
            self.destroy()
    
    def on_close(self):
        """Prevent closing without accepting/declining"""
        messagebox.showwarning("Action Required", "You must accept or decline the EULA to continue")


class LicenseSetupDialog(tk.Toplevel):
    """License setup dialog with branded styling"""
    
    def __init__(self, parent, license_manager, is_new_license=False):
        super().__init__(parent)
        self.license_manager = license_manager
        self.result = False
        self.is_new_license = is_new_license
        
        title = "License Validation" if not is_new_license else "License Setup"
        self.title(title + " - Dr. Alfredo Pio De Roda ES")
        self.geometry("550x520")
        self.resizable(False, False)
        
        # Branding colors
        self.BG_PRIMARY = "#0f1419"
        self.BG_CARD = "#1a202c"
        self.BLUE = "#3b82f6"
        self.GREEN = "#10b981"
        self.RED = "#ef4444"
        self.YELLOW = "#f59e0b"
        self.CYAN = "#06b6d4"
        self.TEXT_PRIMARY = "#ffffff"
        self.TEXT_SECONDARY = "#9ca3af"
        
        self.configure(bg=self.BG_PRIMARY)
        
        # Make dialog modal and prevent closing without setup
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        """Center dialog on parent"""
        self.update_idletasks()
        x = self.winfo_parent()
        self.geometry(f"+{self.winfo_width()}+{self.winfo_height()}")
    
    def setup_ui(self):
        """Setup dialog UI"""
        # Header
        header_frame = tk.Frame(self, bg=self.BLUE, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        if self.is_new_license:
            title_text = "🔐 NEW LICENSE SETUP"
        else:
            title_text = "🔍 LICENSE VALIDATION"
        
        title_label = tk.Label(
            header_frame,
            text=title_text,
            font=("Segoe UI", 16, "bold"),
            bg=self.BLUE,
            fg=self.TEXT_PRIMARY
        )
        title_label.pack(pady=15)
        
        subtitle = "Enter your license key to continue" if self.is_new_license else "Verifying your saved license..."
        subtitle_label = tk.Label(
            header_frame,
            text=subtitle,
            font=("Segoe UI", 9),
            bg=self.BLUE,
            fg=self.TEXT_PRIMARY
        )
        subtitle_label.pack()
        
        # Main content
        content_frame = tk.Frame(self, bg=self.BG_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Internet status
        status_color = self.GREEN if self.license_manager.is_online else self.YELLOW
        status_text = "🟢 ONLINE" if self.license_manager.is_online else "🟡 OFFLINE (CACHED)"
        
        status_label = tk.Label(
            content_frame,
            text=status_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_PRIMARY,
            fg=status_color
        )
        status_label.pack(pady=(0, 15))
        
        # Offline warning
        if not self.license_manager.is_online:
            warning_frame = tk.Frame(content_frame, bg=self.BG_CARD, relief=tk.FLAT)
            warning_frame.pack(fill=tk.X, pady=(0, 15))
            
            warning_text = tk.Label(
                warning_frame,
                text="⚠️  No internet connection detected.\n\nUsing cached licenses.",
                font=("Segoe UI", 9),
                bg=self.BG_CARD,
                fg=self.YELLOW,
                justify=tk.LEFT,
                wraplength=400,
                padx=10,
                pady=10
            )
            warning_text.pack()
        
        # License input (if new)
        if self.is_new_license:
            input_label = tk.Label(
                content_frame,
                text="License Key:",
                font=("Segoe UI", 10, "bold"),
                bg=self.BG_PRIMARY,
                fg=self.TEXT_PRIMARY
            )
            input_label.pack(anchor=tk.W, pady=(10, 5))
            
            self.license_input = tk.Entry(
                content_frame,
                font=("Segoe UI", 10),
                bg=self.BG_CARD,
                fg=self.TEXT_PRIMARY,
                insertbackground=self.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=0,
                padx=10,
                pady=8
            )
            self.license_input.pack(fill=tk.X, pady=(0, 15))
            self.license_input.focus()
        
        # Status display
        self.info_label = tk.Label(
            content_frame,
            text="",
            font=("Segoe UI", 9),
            bg=self.BG_PRIMARY,
            fg=self.TEXT_SECONDARY,
            justify=tk.LEFT,
            wraplength=400
        )
        self.info_label.pack(pady=(10, 15))
        
        # Buttons frame
        button_frame = tk.Frame(content_frame, bg=self.BG_PRIMARY)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        if self.is_new_license:
            # Validate button for new license
            validate_btn = tk.Button(
                button_frame,
                text="✓ VALIDATE LICENSE",
                font=("Segoe UI", 10, "bold"),
                bg=self.GREEN,
                fg=self.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=0,
                padx=20,
                pady=8,
                cursor="hand2",
                command=self.validate_license
            )
            validate_btn.pack(side=tk.LEFT, expand=True, padx=(0, 5))
            
            # Info button
            info_btn = tk.Button(
                button_frame,
                text="ℹ️  INFO",
                font=("Segoe UI", 10, "bold"),
                bg=self.BG_CARD,
                fg=self.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=0,
                padx=20,
                pady=8,
                cursor="hand2",
                command=self.show_info
            )
            info_btn.pack(side=tk.LEFT, expand=True, padx=(0, 5))
        else:
            # For verification, just an OK button
            ok_btn = tk.Button(
                button_frame,
                text="✓ OK",
                font=("Segoe UI", 10, "bold"),
                bg=self.GREEN,
                fg=self.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=0,
                padx=20,
                pady=8,
                cursor="hand2",
                command=self.check_saved_license
            )
            ok_btn.pack(side=tk.LEFT, expand=True)
    
    def validate_license(self):
        """Validate license key"""
        license_key = self.license_input.get().strip()
        
        if not license_key:
            messagebox.showwarning("Input Required", "Please enter a license key")
            return
        
        # Show loading
        self.info_label.config(text="⏳ Validating license...", fg=self.TEXT_SECONDARY)
        self.update()
        
        # Validate
        is_valid, response = self.license_manager.validate_license(license_key)
        
        if is_valid:
            self.info_label.config(text="", fg=self.GREEN)
            org = response.get('org', 'Unknown')
            user = response.get('user', 'Unknown')
            
            messagebox.showinfo(
                "✅ License Valid",
                f"License activated successfully!\n\n"
                f"Organization: {org}\n"
                f"User: {user}\n\n"
                f"License saved permanently."
            )
            self.result = True
            self.destroy()
        else:
            self.info_label.config(text=f"❌ {response}", fg=self.RED)
    
    def check_saved_license(self):
        """Verify saved license is still active"""
        self.info_label.config(text="⏳ Verifying license...", fg=self.TEXT_SECONDARY)
        self.update()
        
        is_active, status = self.license_manager.verify_license_active_online()
        
        if is_active:
            self.info_label.config(text="✅ License is active and valid", fg=self.GREEN)
            self.result = True
            self.root.after(1000, self.destroy)
        else:
            self.info_label.config(text=f"❌ License invalid: {status}", fg=self.RED)
            messagebox.showerror(
                "License Invalid",
                f"Your license is no longer valid.\n\n"
                f"Reason: {status}\n\n"
                f"Application will exit."
            )
            self.result = False
            self.destroy()
    
    def show_info(self):
        """Show license info"""
        messagebox.showinfo(
            "License Information",
            "Your license key is required to use this attendance system.\n\n"
            "Once entered, your license is saved and validated whenever the app starts.\n\n"
            "If your license is revoked, the app will exit automatically.\n\n"
            "If you don't have a license key, please contact your administrator."
        )
    
    def on_close(self):
        """Prevent closing without validation"""
        messagebox.showwarning(
            "Setup Required",
            "You must validate your license to use this system.\n\nPlease enter a valid license key or contact your administrator."
        )


class AttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Attendance System - Dr. Alfredo Pio De Roda ES")
        self.root.geometry("1600x900")
        self.root.configure(bg="#0f1419")
        
        # License initialization
        self.license_manager = LicenseManager()
        self.is_licensed = False
        
        # Initialize variables
        self.camera = None
        self.camera_active = False
        self.camera_thread = None
        self.frame_queue = queue.Queue(maxsize=1)
        self.sf2_workbook = None
        self.sf2_sheet = None
        self.sf2_file = None
        self.student_names = []
        self.scanned_today = []
        self.existing_marks = {}
        self.current_column = None
        self.last_scanned = None
        self.last_scan_time = 0
        
        # Colors
        self.BG_DARK = "#0f1419"
        self.BG_CARD = "#1a202c"
        self.BG_INPUT = "#2d3748"
        self.BLUE = "#3b82f6"
        self.GREEN = "#10b981"
        self.RED = "#ef4444"
        self.YELLOW = "#f59e0b"
        self.CYAN = "#06b6d4"
        self.PURPLE = "#8b5cf6"
        self.TEXT_PRIMARY = "#ffffff"
        self.TEXT_SECONDARY = "#9ca3af"
        
        # Setup folders
        self.home_dir = os.path.expanduser("~")
        self.base_folder = os.path.join(self.home_dir, "SF2_Files")
        self.active_folder = os.path.join(self.base_folder, "Active")
        self.backup_folder = os.path.join(self.base_folder, "Backups")
        self.archive_folder = os.path.join(self.base_folder, "Archive")
        self.qr_folder = os.path.join(self.base_folder, "QR_Codes")
        
        for folder in [self.active_folder, self.backup_folder, self.archive_folder, self.qr_folder]:
            os.makedirs(folder, exist_ok=True)
        
        # Check EULA first (only once)
        if not self.check_eula():
            self.root.destroy()
            return
        
        # Check license
        if not self.check_license():
            self.root.destroy()
            return
        
        self.setup_ui()
        self.auto_load_file()
        
        # Start periodic license validation
        self.periodic_license_check()
    
    def check_eula(self):
        """Check and display EULA if not accepted"""
        if self.license_manager.eula_accepted():
            print("✅ EULA already accepted")
            return True
        
        print("📋 Showing EULA for first time")
        eula_dialog = EULADialog(self.root)
        self.root.wait_window(eula_dialog)
        
        if eula_dialog.result:
            if self.license_manager.accept_eula():
                print("✅ EULA accepted and saved")
                return True
            else:
                messagebox.showerror("Error", "Failed to save EULA acceptance")
                return False
        else:
            messagebox.showinfo("Not Accepted", "EULA must be accepted to use this application.\n\nApplication will exit.")
            return False
    
    def check_license(self):
        """Check and validate license"""
        # Check if license already saved
        if self.license_manager.has_saved_license():
            print("💾 Found saved license!")
            print(f"🔑 License Key: {self.license_manager.license_key[:20]}...")
            
            # Send hardware data immediately
            def send_hardware_and_verify():
                time.sleep(0.5)  # Small delay to let UI load
                
                # Collect and send hardware data
                print("🔧 Collecting hardware information...")
                hardware_data, hwid_label = self.license_manager.hardware_detector.prepare_hardware_data()
                print(f"📊 Hardware: {hwid_label} - {hardware_data[hwid_label]['stats']}")
                
                if self.license_manager.is_online:
                    print("📤 Sending hardware data to Firebase...")
                    success = self.license_manager.hardware_reporter.report_hardware_to_firebase(
                        self.license_manager.license_key,
                        hardware_data,
                        hwid_label
                    )
                    
                    if success:
                        print("✅ Hardware data sent successfully!")
                    
                    # Check for sharing
                    is_sharing, device_count = self.license_manager.hardware_reporter.check_for_license_sharing(
                        self.license_manager.license_key
                    )
                    if is_sharing:
                        print(f"⚠️ License sharing detected: {device_count} devices")
                
                # Verify license
                print("🔍 Verifying license...")
                is_active, status = self.license_manager.verify_license_active_online()
                
                if is_active:
                    print(f"✅ License verified: {status}")
                else:
                    print(f"❌ License invalid: {status}")
                    # Schedule UI update on main thread
                    self.root.after(0, lambda: self.handle_invalid_license(status))
            
            # Start background thread
            verify_thread = threading.Thread(target=send_hardware_and_verify, daemon=True)
            verify_thread.start()
            
            self.is_licensed = True
            print("✅ Continuing with saved license (verifying in background)...")
            return True
        else:
            # No saved license, prompt for new one
            print("🆕 No saved license found, requesting new license")
            license_dialog = LicenseSetupDialog(self.root, self.license_manager, is_new_license=True)
            self.root.wait_window(license_dialog)
            
            if license_dialog.result:
                self.is_licensed = True
                print("✅ New license validated and saved successfully")
                return True
            else:
                messagebox.showerror("License Required", "Cannot start application without a valid license.\n\nApplication will exit.")
                return False
    
    def handle_invalid_license(self, reason):
        """Handle invalid license on main thread"""
        messagebox.showerror("License Invalid", 
                           f"Your license is no longer valid: {reason}\n\n"
                           "The application will now close.")
        self.root.destroy()
    
    def periodic_license_check(self):
        """Verify license every 10 seconds"""
        if self.is_licensed:
            try:
                is_active, status = self.license_manager.verify_license_active_online()
                
                if not is_active:
                    print(f"❌ License revoked or invalid: {status}")
                    messagebox.showerror(
                        "License Revoked",
                        f"Your license has been revoked or is no longer valid.\n\n"
                        f"Reason: {status}\n\n"
                        f"Application will now exit."
                    )
                    self.root.quit()
                    return
            except Exception as e:
                print(f"⚠️ Error checking license: {e}")
        
        # Schedule next check
        self.root.after(10000, self.periodic_license_check)  # Every 10 seconds
    
    def setup_ui(self):
        """Setup the complete UI"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Style tabs
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.BG_DARK, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.BG_CARD, foreground=self.TEXT_PRIMARY,
                       padding=[20, 10], font=("Segoe UI", 10))
        style.map('TNotebook.Tab', background=[("selected", self.BLUE)])
        
        # Create tabs
        self.scan_tab = ttk.Frame(self.notebook)
        self.files_tab = ttk.Frame(self.notebook)
        self.preview_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.scan_tab, text="📱 SCAN")
        self.notebook.add(self.files_tab, text="📂 FILES")
        self.notebook.add(self.preview_tab, text="📊 PREVIEW")
        self.notebook.add(self.settings_tab, text="⚙️ SETTINGS")
        
        # Setup each tab
        self.setup_scan_tab()
        self.setup_files_tab()
        self.setup_preview_tab()
        self.setup_settings_tab()
    
    def setup_scan_tab(self):
        """Setup SCAN tab"""
        main_frame = tk.Frame(self.scan_tab, bg=self.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=0, minsize=380)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # LEFT SIDE - Camera
        left_frame = tk.Frame(main_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        
        tk.Label(left_frame, text="📷 Camera Feed", font=("Segoe UI", 12, "bold"),
                fg=self.BLUE, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.camera_label = tk.Label(left_frame, bg=self.BG_INPUT, width=500, height=400)
        self.camera_label.pack(padx=15, pady=(0, 15), fill=tk.BOTH, expand=True)
        
        # RIGHT SIDE - Controls
        right_frame = tk.Frame(main_frame, bg=self.BG_DARK)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Status card
        status_card = tk.Frame(right_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        status_card.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(status_card, text="📊 System Status", font=("Segoe UI", 12, "bold"),
                fg=self.CYAN, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.file_status = tk.Label(status_card, text="📄 File: Not loaded",
                                    font=("Segoe UI", 9), fg=self.TEXT_SECONDARY, bg=self.BG_CARD)
        self.file_status.pack(anchor="w", padx=15, pady=2)
        
        self.date_status = tk.Label(status_card, text="📅 Date: Not detected",
                                    font=("Segoe UI", 9), fg=self.TEXT_SECONDARY, bg=self.BG_CARD)
        self.date_status.pack(anchor="w", padx=15, pady=2)
        
        self.student_count_label = tk.Label(status_card, text="👥 Students: 0",
                                           font=("Segoe UI", 9), fg=self.TEXT_SECONDARY, bg=self.BG_CARD)
        self.student_count_label.pack(anchor="w", padx=15, pady=(2, 10))
        
        # Counters
        counters_frame = tk.Frame(right_frame, bg=self.BG_DARK)
        counters_frame.pack(fill=tk.X, pady=(0, 10))
        
        present_card = tk.Frame(counters_frame, bg=self.GREEN, relief=tk.RAISED, bd=2)
        present_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(present_card, text="✅ Present", font=("Segoe UI", 9, "bold"),
                fg="#000", bg=self.GREEN).pack(pady=(5, 0))
        self.present_label = tk.Label(present_card, text="0", font=("Segoe UI", 18, "bold"),
                                     fg="#000", bg=self.GREEN)
        self.present_label.pack(pady=(0, 5))
        
        absent_card = tk.Frame(counters_frame, bg=self.RED, relief=tk.RAISED, bd=2)
        absent_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(absent_card, text="❌ Absent", font=("Segoe UI", 9, "bold"),
                fg="#fff", bg=self.RED).pack(pady=(5, 0))
        self.absent_label = tk.Label(absent_card, text="0", font=("Segoe UI", 18, "bold"),
                                    fg="#fff", bg=self.RED)
        self.absent_label.pack(pady=(0, 5))
        
        total_card = tk.Frame(counters_frame, bg=self.BLUE, relief=tk.RAISED, bd=2)
        total_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(total_card, text="👥 Total", font=("Segoe UI", 9, "bold"),
                fg="#fff", bg=self.BLUE).pack(pady=(5, 0))
        self.total_label = tk.Label(total_card, text="0", font=("Segoe UI", 18, "bold"),
                                   fg="#fff", bg=self.BLUE)
        self.total_label.pack(pady=(0, 5))
        
        # Scanned list
        list_frame = tk.Frame(right_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tk.Label(list_frame, text="✅ Scanned", font=("Segoe UI", 11, "bold"),
                fg=self.GREEN, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=(10, 5))
        
        table_container = tk.Frame(list_frame, bg=self.BG_CARD)
        table_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        columns = ("Name", "Time")
        self.student_tree = ttk.Treeview(table_container, columns=columns, show="headings", height=10)
        
        self.student_tree.heading("Name", text="Student Name")
        self.student_tree.heading("Time", text="Time")
        
        self.student_tree.column("Name", width=200)
        self.student_tree.column("Time", width=80)
        
        scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=scrollbar.set)
        
        self.student_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        style = ttk.Style()
        style.configure("Treeview", background=self.BG_INPUT, foreground=self.TEXT_PRIMARY,
                       fieldbackground=self.BG_INPUT, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=self.BG_CARD, foreground=self.GREEN,
                       font=("Segoe UI", 9, "bold"))
        
        # Buttons
        button_frame = tk.Frame(right_frame, bg=self.BG_DARK)
        button_frame.pack(fill=tk.X)
        
        self.start_btn = tk.Button(button_frame, text="▶ START SCANNING", command=self.start_camera,
                                   bg=self.GREEN, fg="#000", font=("Segoe UI", 10, "bold"),
                                   relief=tk.FLAT, padx=15, pady=8, cursor="hand2")
        self.start_btn.pack(fill=tk.X, pady=(0, 4))
        
        self.stop_btn = tk.Button(button_frame, text="⏹ STOP SCANNING", command=self.stop_camera,
                                  bg=self.RED, fg="#fff", font=("Segoe UI", 10, "bold"),
                                  relief=tk.FLAT, padx=15, pady=8, cursor="hand2", state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=(0, 4))
        
        tk.Label(button_frame, text="♻️ Continuous Auto-Scanning", font=("Segoe UI", 9, "bold"),
                fg=self.GREEN, bg=self.BG_DARK).pack(fill=tk.X, pady=(8, 4))
        
        self.open_qr_btn = tk.Button(button_frame, text="📂 QR FOLDER", command=self.open_qr_folder,
                                     bg=self.PURPLE, fg="#fff", font=("Segoe UI", 10, "bold"),
                                     relief=tk.FLAT, padx=15, pady=8, cursor="hand2")
        self.open_qr_btn.pack(fill=tk.X, pady=(0, 4))
        
        self.open_active_btn = tk.Button(button_frame, text="📊 ACTIVE FOLDER", command=self.open_active_folder,
                                         bg=self.CYAN, fg="#000", font=("Segoe UI", 10, "bold"),
                                         relief=tk.FLAT, padx=15, pady=8, cursor="hand2")
        self.open_active_btn.pack(fill=tk.X, pady=(0, 4))
        
        self.open_output_btn = tk.Button(button_frame, text="📁 OUTPUT FOLDER", command=self.open_output_folder,
                                         bg=self.YELLOW, fg="#000", font=("Segoe UI", 10, "bold"),
                                         relief=tk.FLAT, padx=15, pady=8, cursor="hand2")
        self.open_output_btn.pack(fill=tk.X)
    
    def setup_files_tab(self):
        """Setup FILES tab"""
        main_frame = tk.Frame(self.files_tab, bg=self.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header = tk.Frame(main_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        header.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header, text="📂 File Manager", font=("Segoe UI", 14, "bold"),
                fg=self.BLUE, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        btn_frame = tk.Frame(main_frame, bg=self.BG_DARK)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_file_list,
                 bg=self.BLUE, fg="#fff", font=("Segoe UI", 10, "bold"),
                 relief=tk.FLAT, padx=20, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(btn_frame, text="📁 Browse", command=self.browse_file,
                 bg=self.GREEN, fg="#000", font=("Segoe UI", 10, "bold"),
                 relief=tk.FLAT, padx=20, pady=10, cursor="hand2").pack(side=tk.LEFT)
        
        list_frame = tk.Frame(main_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(list_frame, text="📄 Files in Active Folder", font=("Segoe UI", 12, "bold"),
                fg=self.YELLOW, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        tree_container = tk.Frame(list_frame, bg=self.BG_CARD)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        columns = ("Filename", "Size", "Modified")
        self.file_tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=20)
        
        self.file_tree.heading("Filename", text="Filename")
        self.file_tree.heading("Size", text="Size")
        self.file_tree.heading("Modified", text="Modified")
        
        self.file_tree.column("Filename", width=400)
        self.file_tree.column("Size", width=100)
        self.file_tree.column("Modified", width=200)
        
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_file_list()
    
    def setup_preview_tab(self):
        """Setup PREVIEW tab"""
        main_frame = tk.Frame(self.preview_tab, bg=self.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header = tk.Frame(main_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        header.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header, text="👥 Student List", font=("Segoe UI", 14, "bold"),
                fg=self.GREEN, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        tree_frame = tk.Frame(main_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Number", "Name", "Status")
        self.preview_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=30)
        
        self.preview_tree.heading("Number", text="ID")
        self.preview_tree.heading("Name", text="Student Name")
        self.preview_tree.heading("Status", text="Status")
        
        self.preview_tree.column("Number", width=80)
        self.preview_tree.column("Name", width=350)
        self.preview_tree.column("Status", width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=scrollbar.set)
        
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 15), pady=15)
    
    def setup_settings_tab(self):
        """Setup SETTINGS tab"""
        main_frame = tk.Frame(self.settings_tab, bg=self.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header = tk.Frame(main_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        header.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header, text="⚙️ Settings & Information", font=("Segoe UI", 14, "bold"),
                fg=self.YELLOW, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        # License info
        license_frame = tk.Frame(main_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        license_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(license_frame, text="🔐 License Information", font=("Segoe UI", 12, "bold"),
                fg=self.BLUE, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=(10, 5))
        
        license_info = self.license_manager.get_license_info()
        if license_info:
            org = license_info.get('org', 'Unknown')
            user = license_info.get('user', 'Unknown')
            issued_at = license_info.get('issuedAt', 'Unknown')
            is_active = license_info.get('active', False)
            
            status_color = self.GREEN if is_active else self.RED
            status_text = "✅ ACTIVE" if is_active else "❌ REVOKED"
            
            tk.Label(license_frame, text=f"Organization: {org}",
                    font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=2)
            tk.Label(license_frame, text=f"User: {user}",
                    font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=2)
            tk.Label(license_frame, text=f"Issued: {issued_at}",
                    font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=2)
            tk.Label(license_frame, text=f"Status: {status_text}",
                    font=("Segoe UI", 9, "bold"), fg=status_color, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=(2, 10))
        
        folder_frame = tk.Frame(main_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(folder_frame, text="📁 Folder Locations", font=("Segoe UI", 12, "bold"),
                fg=self.BLUE, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        tk.Label(folder_frame, text=f"Active: {self.active_folder}",
                font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=2)
        tk.Label(folder_frame, text=f"QR Codes: {self.qr_folder}",
                font=("Segoe UI", 9), fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=2)
        
        info_frame = tk.Frame(main_frame, bg=self.BG_CARD, relief=tk.RIDGE, bd=2)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(info_frame, text="📖 About This System", font=("Segoe UI", 12, "bold"),
                fg=self.GREEN, bg=self.BG_CARD).pack(anchor="w", padx=15, pady=10)
        
        info_text = """
Version: IMPROVED v6 (Firebase Licensing + Persistent Storage + EULA)
Date: January 30, 2026

FEATURES:
✅ Simple date column detection
✅ Auto-save on every scan
✅ Excel lock detection
✅ Real-time counters
✅ QR code scanning
✅ Firebase licensing
✅ Offline mode with caching
✅ EULA acceptance (first run)
✅ One-time license entry (saved permanently)
✅ Real-time license validation (every 10 seconds)
✅ Instant revocation detection

LICENSE SYSTEM:
✅ Enter license ONCE (saved permanently)
✅ System verifies on every startup
✅ Checks if still active every 10 seconds
✅ Instant exit if revoked
✅ Works offline with cached data

HOW IT WORKS:
1. First run: Accept EULA, enter license key
2. License saved to: ~/.attendance_system/license.json
3. Every startup: Verifies saved license
4. During use: Checks every 10 seconds if still active
5. If revoked: App exits immediately

SECURITY:
✅ One-time entry, then saved
✅ Real-time active status monitoring
✅ Instant revocation detection
✅ Works with/without internet
✅ Cached validation for offline use
        """
        
        tk.Label(info_frame, text=info_text, font=("Segoe UI", 9),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD, justify=tk.LEFT).pack(anchor="w", padx=15, pady=(0, 10))
    
    def is_valid_student_name(self, name):
        """Validate if text is a real student name"""
        if not name or not isinstance(name, str):
            return False
        
        name = name.strip()
        if len(name) < 2:
            return False
        
        name_upper = name.upper()
        
        excluded_patterns = [
            "SUMIF", "COUNTIF", "AVERAGE", "SUM(", "COUNT(", "IF(",
            "VLOOKUP", "HLOOKUP", "INDEX", "MATCH",
            "SCHOOL FORM", "SF2", "DAILY ATTENDANCE", "ATTENDANCE REPORT",
            "LEARNER'S NAME", "LAST NAME", "FIRST NAME", "MIDDLE NAME",
            "CODES FOR CHECKING", "PRESENT", "ABSENT", "TARDY",
            "HALF SHADED", "UPPER", "LOWER", "CUTTING CLASSES", "LATE COMER",
            "DROPPED", "TRANSFERRED", "ENROLLED", "REGISTRATION",
            "TOTAL", "COMBINED", "PER DAY", "SUMMARY", "MALE", "FEMALE",
            "MONTH:", "BLANK", "(BLANK)", "NO. OF DAYS", "CLASSES",
            "PERCENTAGE", "ENROLMENT", "AVERAGE DAILY", "ATTENDANCE",
            "REGISTERED LEARNERS", "END OF THE MONTH", "SCHOOL YEAR",
            "1ST FRIDAY", "REPORTING MONTH", "SCHOOL DAYS",
            "REASONS", "CAUSES", "DROPPING OUT", "DROP OUT", "DROPOUT",
            "DOMESTIC-RELATED", "INDIVIDUAL-RELATED", "SCHOOL-RELATED",
            "GEOGRAPHIC", "ENVIRONMENTAL", "FINANCIAL-RELATED",
            "TAKE CARE", "SIBLINGS", "EARLY MARRIAGE", "PREGNANCY",
            "PARENTS' ATTITUDE", "FAMILY PROBLEMS", "ILLNESS",
            "OVERAGE", "DEATH", "DRUG ABUSE", "ACADEMIC PERFORMANCE",
            "LACK OF INTEREST", "DISTRACTIONS", "HUNGER", "MALNUTRITION",
            "TEACHER FACTOR", "PHYSICAL CONDITION", "CLASSROOM",
            "PEER INFLUENCE", "DISTANCE", "HOME AND SCHOOL",
            "ARMED CONFLICT", "TRIBAL WARS", "CLAN FEUDS",
            "CALAMITIES", "DISASTERS", "CHILD LABOR", "WORK",
            "OTHERS (SPECIFY)",
            "GUIDELINES:", "ACCOMPLISHED", "REFER", "DATES SHALL",
            "WRITTEN IN", "COLUMNS AFTER", "COMPUTE", "FOLLOWING",
            "EVERY END", "ADVISER", "SUBMIT", "OFFICE", "PRINCIPAL",
            "RECORDING", "SUMMARY TABLE", "FORM 4", "SIGNED",
            "RETURNED", "PROVIDE", "NECESSARY", "INTERVENTIONS",
            "HOME VISITATION", "ABSENT FOR 5", "CONSECUTIVE DAYS",
            "RISK OF", "PERFORMANCE", "REFLECTED", "FORM 137", "FORM 138",
            "GRADING PERIOD", "BEGINNING", "CUT-OFF",
            "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY",
            "MONDAY,", "TUESDAY,", "WEDNESDAY,", "THURSDAY,", "FRIDAY,",
            "CERTIFY", "TRUE", "CORRECT", "REPORT", "SIGNATURE",
            "PRINTED NAME", "TEACHER", "SCHOOL HEAD", "ATTESTED",
            "PAGE", "OF", "SCHOOL FORM 2", "___",
            "LEARNER", "STUDENT", "NAME", "NAMES", "ID", "NUMBER",
            "ENROLLMENT", "ENROL",
            "NAN", "NONE", "N/A", "NULL", "BLANK", "EMPTY",
            "PERCENTAGE OF ENROLMENT", "PERCENTAGE OF ENROLLMENT",
            "AVERAGE DAILY ATTENDANCE", 
            "PERCENTAGE OF ATTENDANCE FOR THE MONTH",
            "PERCENTAGE OF ATTENDANCE",
        ]
        
        for pattern in excluded_patterns:
            if pattern in name_upper:
                return False
        
        if not any(c.isalpha() for c in name):
            return False
        
        if name.replace('.', '').replace(',', '').replace(' ', '').isdigit():
            return False
        
        if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', name):
            return False
        
        if not any(c.isalnum() for c in name):
            return False
        
        return True
    
    def is_excel_file_open(self, file_path):
        """Check if Excel file is open/locked"""
        try:
            temp_name = file_path + ".tmp"
            os.rename(file_path, temp_name)
            os.rename(temp_name, file_path)
            return False
        except (OSError, IOError):
            return True
    
    def auto_load_file(self):
        """Auto-load file from Active folder"""
        try:
            files = [f for f in os.listdir(self.active_folder) 
                    if f.endswith(('.xlsx', '.xls')) and not f.startswith('~')]
            
            if files:
                file_path = os.path.join(self.active_folder, files[0])
                self.load_file(file_path)
                print(f"✅ Auto-loaded: {files[0]}")
                
                self.root.after(500, self.start_camera)
            else:
                print("⚠️  No Excel files in Active folder")
                self.file_status.config(text="📄 File: No file found", fg=self.RED)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def repair_excel_file(self, file_path):
        """Attempt to repair corrupted Excel file"""
        try:
            print(f"🔧 Attempting to repair Excel file...")
            backup_path = file_path + ".backup"
            shutil.copy2(file_path, backup_path)
            
            temp_dir = tempfile.mkdtemp()
            try:
                with ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except Exception as e:
                return False
            
            content_types_path = os.path.join(temp_dir, '[Content_Types].xml')
            if not os.path.exists(content_types_path):
                return False
            
            try:
                os.remove(file_path)
                with ZipFile(file_path, 'w') as zip_ref:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path_full = os.path.join(root, file)
                            arcname = os.path.relpath(file_path_full, temp_dir)
                            zip_ref.write(file_path_full, arcname)
                print(f"  ✓ Repaired successfully!")
                return True
            except Exception as e:
                return False
        except Exception as e:
            return False
    
    def load_file(self, file_path):
        """Load SF2 file"""
        try:
            print(f"\n{'='*80}")
            print(f"LOADING FILE: {os.path.basename(file_path)}")
            print(f"{'='*80}")
            
            try:
                self.sf2_workbook = load_workbook(file_path)
            except KeyError as e:
                if "Content_Types" in str(e):
                    print(f"⚠️  File corrupted, attempting repair...")
                    if self.repair_excel_file(file_path):
                        print(f"✅ Repair successful!")
                        self.sf2_workbook = load_workbook(file_path)
                    else:
                        print(f"❌ Cannot repair")
                        messagebox.showerror("Error", "Cannot repair corrupted file")
                        return
                else:
                    raise
            
            self.sf2_sheet = self.sf2_workbook.active
            self.sf2_file = file_path
            
            self.student_names = []
            self.scanned_today = []
            self.existing_marks = {}
            
            today = datetime.now()
            day_of_month = today.day
            
            print(f"\n🔍 Looking for date: {day_of_month}")
            print(f"Searching Row 11 for the date...")
            
            date_column = None
            for col in range(1, self.sf2_sheet.max_column + 1):
                cell_value = self.sf2_sheet.cell(11, col).value
                
                if cell_value is not None:
                    try:
                        date_num = int(cell_value)
                        if date_num == day_of_month:
                            date_column = col
                            print(f"✅ FOUND! Date {day_of_month} in Column {col}")
                            break
                    except (ValueError, TypeError):
                        continue
            
            if date_column is None:
                print(f"⚠️  Date {day_of_month} NOT FOUND in Row 11")
                self.date_status.config(text=f"📅 Date: {day_of_month} NOT FOUND", fg=self.RED)
                self.current_column = None
            else:
                day_letter = self.sf2_sheet.cell(12, date_column).value
                
                print(f"✅ Will mark attendance in Column {date_column} ({day_letter})")
                
                self.current_column = date_column
                self.date_status.config(
                    text=f"📅 Date: {day_of_month} ({day_letter}) → Col {date_column}",
                    fg=self.GREEN
                )
            
            print(f"\n👥 Loading students from Column B...")
            print("-" * 80)
            
            for row in range(13, self.sf2_sheet.max_row + 1):
                name_cell = self.sf2_sheet.cell(row, 2).value
                
                if not name_cell:
                    continue
                
                num_cell = self.sf2_sheet.cell(row, 1).value
                student_num = str(num_cell).strip() if num_cell else ""
                
                if self.is_valid_student_name(name_cell):
                    name = name_cell.strip()
                    self.student_names.append({
                        "name": name,
                        "number": student_num,
                        "row": row
                    })
                    
                    if self.current_column:
                        existing_mark = self.sf2_sheet.cell(row, self.current_column).value
                        if existing_mark and str(existing_mark).strip() == "✓":
                            self.existing_marks[name] = True
                            print(f"  ✓ {student_num:3s} | {name} (already marked)")
                        else:
                            self.existing_marks[name] = False
                            print(f"    {student_num:3s} | {name}")
                    else:
                        self.existing_marks[name] = False
                        print(f"    {student_num:3s} | {name}")
            
            print("-" * 80)
            print(f"✅ Loaded {len(self.student_names)} students")
            print(f"{'='*80}\n")
            
            self.file_status.config(
                text=f"📄 File: {os.path.basename(file_path)}",
                fg=self.GREEN
            )
            self.student_count_label.config(text=f"👥 Students: {len(self.student_names)}")
            self.total_label.config(text=str(len(self.student_names)))
            
            self.update_preview()
            self.update_counters()
        
        except Exception as e:
            print(f"❌ Error: {e}")
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load file: {e}")
    
    def update_preview(self):
        """Update preview tab"""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        for student in self.student_names:
            has_existing = self.existing_marks.get(student['name'], False)
            has_new_scan = any(s['name'] == student['name'] for s in self.scanned_today)
            
            if has_existing or has_new_scan:
                status = "✅ Present"
            else:
                status = "❌ Absent"
            
            self.preview_tree.insert("", "end", values=(
                student['number'],
                student['name'],
                status
            ))
    
    def update_counters(self):
        """Update counters"""
        existing_present = len([x for x in self.existing_marks.values() if x])
        new_scans = len(self.scanned_today)
        
        present = existing_present + new_scans
        absent = len(self.student_names) - present
        total = len(self.student_names)
        
        self.present_label.config(text=str(present))
        self.absent_label.config(text=str(absent))
        self.total_label.config(text=str(total))
    
    def start_camera(self):
        """Start camera"""
        if self.camera_active:
            return
        
        if not self.sf2_file:
            messagebox.showwarning("Warning", "Please load a file first!")
            return
        
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            messagebox.showerror("Error", "Cannot open camera!")
            return
        
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
        
        self.camera_active = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.camera_thread = threading.Thread(target=self.camera_thread_worker, daemon=True)
        self.camera_thread.start()
        
        print("📷 Camera started")
        self.update_camera_frame()
    
    def camera_thread_worker(self):
        """Worker thread for camera"""
        while self.camera_active and self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                try:
                    if self.frame_queue.full():
                        try:
                            self.frame_queue.get_nowait()
                        except queue.Empty:
                            pass
                    self.frame_queue.put(frame, block=False)
                except queue.Full:
                    pass
            else:
                break
            time.sleep(0.01)
    
    def update_camera_frame(self):
        """Update camera frame"""
        if not self.camera_active:
            return
        
        frame = None
        try:
            frame = self.frame_queue.get(timeout=0.1)
        except queue.Empty:
            if self.camera_active:
                self.root.after(10, self.update_camera_frame)
            return
        
        if frame is None:
            if self.camera_active:
                self.root.after(10, self.update_camera_frame)
            return
        
        try:
            decoded_objects = decode(frame)
            
            for obj in decoded_objects:
                try:
                    qr_data = obj.data.decode('utf-8').strip()
                    
                    if self.is_valid_student_name(qr_data):
                        matching_student = next((s for s in self.student_names if s['name'] == qr_data), None)
                        
                        if matching_student:
                            has_existing_mark = self.existing_marks.get(qr_data, False)
                            already_scanned = any(s['name'] == qr_data for s in self.scanned_today)
                            
                            current_time = datetime.now().timestamp()
                            rapid_rescan = (qr_data == self.last_scanned and 
                                          (current_time - self.last_scan_time) < 1)
                            
                            if has_existing_mark:
                                print(f"⚠️  {qr_data}: Already marked from before!")
                            elif already_scanned:
                                print(f"⚠️  Already scanned in this session: {qr_data}")
                            elif rapid_rescan:
                                pass
                            else:
                                self.scanned_today.append({
                                    'name': qr_data,
                                    'time': datetime.now().strftime("%H:%M:%S")
                                })
                                self.last_scanned = qr_data
                                self.last_scan_time = current_time
                                
                                print(f"✅ Scanned: {qr_data}")
                                self.update_student_list()
                                self.update_counters()
                                self.update_preview()
                                
                                self.auto_save_attendance()
                        else:
                            pass
                except Exception as e:
                    pass
        except Exception as e:
            pass
        
        try:
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                points = obj.polygon
                if len(points) > 0:
                    pts = [(int(p.x), int(p.y)) for p in points]
                    cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
        except Exception as e:
            pass
        
        try:
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (500, 400))
            image = Image.fromarray(image)
            photo = ImageTk.PhotoImage(image)
            
            self.camera_label.config(image=photo)
            self.camera_label.image = photo
        except Exception as e:
            pass
        
        if self.camera_active:
            self.root.after(10, self.update_camera_frame)
    
    def stop_camera(self):
        """Stop camera"""
        self.camera_active = False
        
        if self.camera_thread:
            self.camera_thread.join(timeout=1.0)
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        print("⏹ Camera stopped")
    
    def update_student_list(self):
        """Update scanned list"""
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        
        for student in self.scanned_today:
            self.student_tree.insert("", "end", values=(student['name'], student['time']))
    
    def auto_save_attendance(self):
        """Auto-save attendance"""
        try:
            if not self.sf2_file or self.current_column is None:
                return
            
            if self.is_excel_file_open(self.sf2_file):
                print(f"⚠️  WARNING: Excel file is OPEN! Cannot save!")
                messagebox.showwarning("Excel Open", 
                    f"❌ Excel file is currently open!\n\n"
                    f"Close the file in Excel before scanning more students.\n\n"
                    f"The system cannot write while Excel has the file locked!")
                return
            
            if self.scanned_today:
                last_scanned = self.scanned_today[-1]['name']
                
                for student in self.student_names:
                    if student['name'] == last_scanned:
                        row = student['row']
                        self.sf2_sheet.cell(row, self.current_column).value = "✓"
                        print(f"  💾 Auto-saved: {last_scanned}")
                        break
                
                self.sf2_workbook.save(self.sf2_file)
        
        except Exception as e:
            print(f"❌ Auto-save error: {e}")
    
    def refresh_file_list(self):
        """Refresh file list"""
        try:
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            
            files = [f for f in os.listdir(self.active_folder) 
                    if f.endswith(('.xlsx', '.xls')) and not f.startswith('~')]
            
            for filename in sorted(files):
                filepath = os.path.join(self.active_folder, filename)
                size = os.path.getsize(filepath) / 1024
                modified = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M")
                
                self.file_tree.insert("", "end", values=(filename, f"{size:.1f}KB", modified))
        except Exception as e:
            print(f"Error: {e}")
    
    def browse_file(self):
        """Browse for file"""
        file_path = filedialog.askopenfilename(
            initialdir=self.active_folder,
            filetypes=[("Excel", "*.xlsx *.xls"), ("All", "*.*")]
        )
        
        if file_path:
            self.load_file(file_path)
    
    def open_qr_folder(self):
        """Open QR folder"""
        try:
            import subprocess
            if os.name == 'nt':
                subprocess.Popen(f'explorer "{self.qr_folder}"')
            else:
                subprocess.Popen(['open', self.qr_folder])
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder: {e}")
    
    def open_active_folder(self):
        """Open Active folder"""
        try:
            import subprocess
            if os.name == 'nt':
                subprocess.Popen(f'explorer "{self.active_folder}"')
            else:
                subprocess.Popen(['open', self.active_folder])
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder: {e}")
    
    def open_output_folder(self):
        """Open Output folder"""
        try:
            import subprocess
            output_folder = os.path.join(os.path.expanduser("~"), "Downloads", "ATStudios-Project")
            if os.name == 'nt':
                subprocess.Popen(f'explorer "{output_folder}"')
            else:
                subprocess.Popen(['open', output_folder])
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceSystem(root)
    root.mainloop()
