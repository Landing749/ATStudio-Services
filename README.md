<p align="center">
  <img src="https://via.placeholder.com/1280x320/0f1419/3b82f6?text=QR+Attendance+System+v6+%7C+Jan+2026" alt="QR Attendance System Banner" width="90%"/>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python version"></a>
  <img src="https://img.shields.io/badge/Tkinter-GUI-success?style=for-the-badge" alt="GUI">
  <img src="https://img.shields.io/badge/Firebase-Licensing-orange?style=for-the-badge&logo=firebase&logoColor=white" alt="Firebase">
  <img src="https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/Code-100%25_Human_Written-2ecc71?style=for-the-badge&logo=code&logoColor=white" alt="Fully human written">
</p>

Modern QR-code based attendance system built specifically for DepEd School Form 2 (SF2) daily attendance sheets.  
Designed and developed for **Dr. Alfredo Pio De Roda Elementary School**, Tanza, Calabarzon, Philippines (January 2026).

Features strong Firebase-based licensing, hardware fingerprinting to prevent sharing, EULA enforcement, offline caching, real-time revocation, corrupted Excel auto-repair, threaded camera for smooth scanning, and a clean dark-themed Tkinter interface.

## ✨ Detailed Feature Overview

| Category                  | Feature                                                                 | Technical Details & Benefits                                                                                          | Status |
|---------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|--------|
| **QR Code Generator**     | Batch QR generation from SF2 Excel                                      | Extracts student names from Column B (row 13+), applies strict validation filter (excludes headers, formulas, dates, totals, gender summaries, etc.) | ✓      |
|                           | High-reliability QR codes                                               | Uses `qrcode` library with ERROR_CORRECT_H → tolerant to printing damage, dirt, or poor lighting                       | ✓      |
|                           | Smart name filtering                                                    | Rejects patterns like "SUMIF", "TOTAL MALE", "AVERAGE DAILY", dates, numbers-only, short strings, etc.               | ✓      |
|                           | Progress bar & status feedback                                          | Real-time progress bar, status label updates during generation                                                        | ✓      |
| **Attendance Scanner**    | Real-time webcam QR scanning                                            | Threaded OpenCV + pyzbar → no UI freeze, 30 FPS target, frame queue for smooth performance                           | ✓      |
|                           | Automatic date column detection                                         | Scans row 11 for today's day number, uses matching column (handles DepEd SF2 layout perfectly)                       | ✓      |
|                           | Existing mark detection & duplicate prevention                          | Checks current "✓" in column + 1-second rescan cooldown per student                                                   | ✓      |
|                           | Auto-save after every scan                                              | Immediate `workbook.save()` after each valid scan, with file-lock check via rename trick                              | ✓      |
|                           | Live counters (present/absent/total)                                    | Combines pre-existing marks + new scans for accurate real-time statistics                                            | ✓      |
|                           | Corrupted Excel auto-repair                                             | If `[Content_Types].xml` missing → unzips, re-zips file structure automatically                                       | ✓      |
| **Licensing & Security**  | Firebase Realtime Database licensing                                    | One-time key entry → saved forever in `~/.attendance_system/license.json`                                            | ✓      |
|                           | Real-time revocation (kill switch)                                      | Polls `active` flag every ~10 seconds → exits immediately if set to `false`                                          | ✓      |
|                           | Hardware fingerprinting & anti-sharing                                  | SHA-256 hash of MAC/UUID + OS/CPU/RAM stats → reports to `/licenses/{key}/hardware` → detects >1 device              | ✓      |
|                           | Persistent HWID counter                                                 | Increments device count (PRIMARY → SECONDARY → …) stored in `hwid_counter.txt`                                       | ✓      |
|                           | Offline mode with caching                                               | Uses `licenses_cache.json` when offline → shows warning but continues working                                        | ✓      |
|                           | EULA acceptance modal on first run                                      | Scrollable text dialog, mandatory checkbox, saved in `eula_accepted.txt`                                             | ✓      |
| **User Interface**        | Modern dark theme                                                       | #0f1419 background, #1a202c cards, #3b82f6 accents, color-coded status (green/red/yellow)                           | ✓      |
|                           | Tabbed layout                                                           | Scan (camera + preview), Files (browser), Preview (student list + status), Settings (license info & folders)         | ✓      |
|                           | File auto-load & folder integration                                     | Auto-loads first .xlsx from `~/SF2_Files/Active/` on startup                                                        | ✓      |
|                           | Visual feedback                                                         | Camera feed with green QR outline, live counters, warning popups, console logging                                    | ✓      |

## 📂 Folder Structure (Created Automatically)
~/SF2_Files/
├── Active/                     # Put your working SF2 .xlsx files here (app auto-loads first one)
├── QR_Codes/                   # Generated QR PNG files (named after student e.g. Juan_Dela_Cruz.png)
└── .attendance_system/         # Hidden config folder (do not delete unless resetting license)
├── license.json            # Saved license key + data
├── eula_accepted.txt       # Timestamp of EULA acceptance
├── licenses_cache.json     # Offline copy of Firebase licenses
└── hwid_counter.txt        # Current device count for this license (1 = PRIMARY, 2 = SECONDARY…)
text## 🚀 Quick Start

1. Make sure you have Python 3.8+ installed

2. Create virtual environment (recommended)
bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
# or
venv\Scripts\activate         # Windows

Install dependencies

Bashpip install -r requirements.txt
# or manually:
pip install openpyxl qrcode[pil] pyzbar opencv-python pillow requests psutil

Run the programs

Bash# Generate QR codes
python qr_generator_IMPROVED.py

# Run attendance system (with licensing)
python attendance_system_WITH_FIREBASE_LICENSING_V2.py
🔒 License Anti-Sharing & Revocation Flow (Detailed)


















































































StepActionLocation / MethodConsequence if Failed / DetectedNotes / Timing1App launchLocal——2Check for saved license & EULA files~/.attendance_system/Missing → show EULA + license entry modalOne-time only3User accepts EULA + enters license keyTkinter modal dialogKey saved forever in license.jsonNever asked again4Validate key against FirebaseGET /licenses/{key}.jsonNot found / active:false → error & exitFalls back to cache if offline5Collect hardware fingerprintLocal (MAC hash + CPU/RAM/OS info)—SHA-256 truncated to 16 chars6Report hardware data to FirebasePUT /licenses/{key}/hardware—Merges with existing entries7Count number of HWID entries under licenseRead /hardware object length>1 → sharing detected (console warning)Labels: PRIMARY, SECONDARY, …8Periodic license check (every ~10 seconds)root.after(10000, verify_function)active = false → immediate graceful exitMost powerful revocation mechanism9Offline fallbackLoad from licenses_cache.jsonContinues with last known good state + "Offline" warningCache updated on successful online fetch10Sharing / revocation detectedLocal logic after Firebase responseShow message (if UI still responsive) → sys.exit()Almost instant (<1s after poll)
🛠️ Expanded Troubleshooting Guide
































































































#Problem DescriptionLikely Causes (Most → Least Common)Step-by-Step FixPrevention / Best Practice1Camera does not open / black screenPermissions denied, no webcam, wrong index1. Check privacy settings
2. Test index 0,1,2…
3. ls /dev/video* (Linux)Use external USB webcam if built-in problematic2"Excel file is open" warning every scanSF2 open in Microsoft ExcelClose Excel completely (check Task Manager)Train users: close file before scanning3App exits immediately after launchLicense revoked or multiple devices detected1. Check Firebase active field
2. Delete local license.json to re-enter keyMonitor hardware entries in Firebase console4No students appear in listWrong column, filtered out, bad SF2 format1. Confirm names in Column B row 13+
2. Temporarily disable some filters in is_valid_student_nameUse official DepEd SF2 template5QR codes not scanning reliablyPoor print quality, bad lighting, camera focus1. Regenerate with larger box_size
2. Improve lighting
3. Hold 10–20 cm awayLaminate QR codes, use matte sticker paper6"Corrupted file" message & repair failsDamaged zip structure in .xlsx1. Restore from backup
2. Open in Excel → Save As new fileBackup Active folder weekly7License validation fails even with internetWrong Firebase config, firewall, database rules1. Verify FIREBASE_CONFIG values
2. Test URL in browser
3. Check firewall/proxyUse school/office Wi-Fi for first validation8App freezes / very slow scanningLarge SF2 file, low RAM, old CPU1. Reduce student count per file
2. Close other programs
3. Increase sleep time in threadSplit classes into separate SF2 files9EULA / license not savingNo write permission in home directory1. Run as administrator once
2. Check folder permissions
3. Manually create .attendance_systemAvoid running from restricted network drives10"Offline mode" stays foreverNo internet ever, cache corrupted1. Connect to internet
2. Delete licenses_cache.json
3. Restart appValidate license online at least once a month11Multiple HWIDs appear under one licenseSame key used on different computers1. Revoke in Firebase
2. Issue new key
3. Educate users not to share keyUse unique keys per teacher/computer12Console shows many "⚠️ Error …" messagesNetwork timeout, Firebase unreachableUsually harmless if offline mode works — ignore unless app misbehavesAdd logging to file if needed for support
When asking for help (e.g. opening an issue):
Please include:

Exact error message / popup text
Console output (copy-paste last 10–20 lines)
Your operating system + Python version
Whether you were online or offline at the time of the issue
Steps you already tried

📸 Screenshots

  QR Code Generator - File Loaded and Ready
  Attendance Scanner - Live Scanning in Progress


  Preview Tab - Scanned Students List & Status
  Settings Tab - License & Folder Information

Replace the placeholder paths (screenshots/...) with your actual screenshot files once you add them to the repository.
📜 License & Legal Notice
This software is provided exclusively for educational use at Dr. Alfredo Pio De Roda Elementary School.
Any form of unauthorized redistribution, commercial use, reverse engineering, or removal of licensing/hardware checks is strictly prohibited.

100% human-written code
Created by Athan Meir
Tanza, Calabarzon, Philippines
January 30, 2026
