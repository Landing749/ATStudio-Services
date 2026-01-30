# QR Attendance System  
**Dr. Alfredo Pio De Roda Elementary School Edition**

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

Tailored QR attendance solution for DepEd SF2 forms — Dr. Alfredo Pio De Roda ES, Tanza, Calabarzon, Philippines (Jan 2026)

## Core Features Overview

| Category                  | Feature                                      | Description / Benefit                                                                                     | Status |
|---------------------------|----------------------------------------------|-----------------------------------------------------------------------------------------------------------|--------|
| QR Code Generator         | Batch QR from SF2 Excel                      | Extracts names from Column B (row 13+), strict filtering (skips headers, formulas, totals, dates, etc.)   | ✓      |
|                           | High-reliability QR codes                    | ERROR_CORRECT_H level — tolerant to damage, poor print quality, low light                                 | ✓      |
|                           | Smart name validation                        | Rejects invalid patterns ("SUMIF", "TOTAL MALE", "NAN", numbers-only, short strings, etc.)                | ✓      |
|                           | Real-time progress & status                  | Progress bar + status label during generation                                                             | ✓      |
| Attendance Scanner        | Threaded real-time QR scanning               | OpenCV + pyzbar, no UI freeze, ~30 FPS, frame queue                                                       | ✓      |
|                           | Auto date-column detection                   | Reads row 11, marks correct column in DepEd SF2 layout                                                    | ✓      |
|                           | Existing mark detection                      | Prevents overwriting already present "✓"                                                                 | ✓      |
|                           | Duplicate / rapid rescan prevention          | 1-second cooldown per student                                                                             | ✓      |
|                           | Auto-save per scan                           | Immediate save + file-lock check (rename trick)                                                           | ✓      |
|                           | Live attendance counters                     | Present / Absent / Total — combines existing + new scans                                                  | ✓      |
|                           | Corrupted .xlsx auto-repair                  | Fixes missing `[Content_Types].xml` by unzip/rezip                                                        | ✓      |
| Licensing & Security      | Firebase Realtime Database licensing         | One-time key entry, saved forever locally                                                                 | ✓      |
|                           | Real-time revocation                         | Polls `active` flag every ~10 s → instant exit if revoked                                                 | ✓      |
|                           | Hardware fingerprinting                      | SHA-256 (MAC/UUID + OS/CPU/RAM) → detects sharing                                                         | ✓      |
|                           | Persistent HWID counter                      | PRIMARY → SECONDARY → … (saved in hwid_counter.txt)                                                       | ✓      |
|                           | Offline mode with caching                    | Uses `licenses_cache.json` when offline, shows warning                                                    | ✓      |
|                           | EULA modal on first run                      | Scrollable text, mandatory checkbox, saved acceptance                                                    | ✓      |
| User Interface            | Modern dark theme                            | #0f1419 BG, #1a202c cards, #3b82f6 accents, color-coded status                                            | ✓      |
|                           | Tabbed layout                                | Scan (camera), Files (browser), Preview (list), Settings (license/folders)                                | ✓      |
|                           | Auto-load active SF2                         | Loads first .xlsx from `~/SF2_Files/Active/` on startup                                                   | ✓      |
|                           | Visual scanning feedback                     | Green QR outline on camera feed, live counters, warning popups                                            | ✓      |

## Folder Structure (Auto-created)

| Folder / File                        | Purpose                                                                                   |
|--------------------------------------|-------------------------------------------------------------------------------------------|
| `~/SF2_Files/Active/`                | Place current SF2 .xlsx files here (app auto-loads first one)                             |
| `~/SF2_Files/QR_Codes/`              | Generated student QR PNGs (named after student e.g. Juan_Dela_Cruz.png)                   |
| `~/.attendance_system/license.json`  | Saved license key + data                                                                  |
| `~/.attendance_system/eula_accepted.txt` | EULA acceptance timestamp                                                              |
| `~/.attendance_system/licenses_cache.json` | Offline cache of Firebase licenses                                                     |
| `~/.attendance_system/hwid_counter.txt` | Hardware ID counter for sharing detection                                             |

## Quick Start Steps

| Step | Action                                                                 | Command / Note                                           |
|------|------------------------------------------------------------------------|----------------------------------------------------------|
| 1    | Ensure Python 3.8+ is installed                                        | Download from python.org if needed                       |
| 2    | Create virtual environment (recommended)                               | `python -m venv venv`                                    |
| 3    | Activate environment                                                   | Linux/macOS: `source venv/bin/activate`<br>Windows: `venv\Scripts\activate` |
| 4    | Install dependencies                                                   | `pip install -r requirements.txt`                        |
| 5    | Generate student QR codes                                              | `python qr_generator_IMPROVED.py`                        |
| 6    | Launch attendance scanner (with licensing)                             | `python attendance_system_WITH_FIREBASE_LICENSING_V2.py` |

## License Anti-Sharing & Revocation Flow

| Step | Action                                      | Location / Method                          | Consequence if Failed / Detected                          | Notes / Timing                     |
|------|---------------------------------------------|--------------------------------------------|------------------------------------------------------------|------------------------------------|
| 1    | App launch                                  | Local                                      | —                                                          | —                                  |
| 2    | Check saved license & EULA files            | `~/.attendance_system/`                    | Missing → show EULA + license modal                        | One-time only                      |
| 3    | User accepts EULA + enters key              | Tkinter modal                              | Key saved forever in `license.json`                        | Never asked again                  |
| 4    | Validate key against Firebase               | `GET /licenses/{key}.json`                 | Not found / `active:false` → exit                          | Falls back to cache if offline     |
| 5    | Collect hardware fingerprint                | Local (MAC hash + CPU/RAM/OS)              | —                                                          | SHA-256 truncated to 16 chars      |
| 6    | Report hardware data                        | `PUT /licenses/{key}/hardware`             | —                                                          | Merges with existing entries       |
| 7    | Count HWID entries under license            | Read `/hardware` object length             | >1 → sharing detected (console warning)                    | PRIMARY, SECONDARY… labels         |
| 8    | Periodic check (~every 10 s)                | `root.after(10000, …)`                     | `active` = false → immediate exit                          | Strongest revocation method        |
| 9    | Offline fallback                            | `licenses_cache.json`                      | Continues + "Offline mode" warning                         | Cache updated when online          |
| 10   | Sharing / revocation detected               | Local logic after Firebase response        | Show message → `sys.exit()`                                | <1 s after poll                    |

## Troubleshooting Guide

| #  | Problem                                      | Most Likely Cause(s)                          | Step-by-Step Fix                                                                 | Prevention / Best Practice                        |
|----|----------------------------------------------|-----------------------------------------------|----------------------------------------------------------------------------------|---------------------------------------------------|
| 1  | Camera black / won't open                    | Permissions, no device, wrong index           | Check privacy settings → test indices 0,1,2… → `ls /dev/video*` (Linux)          | Use external USB webcam if built-in fails         |
| 2  | "Excel file is open" warning                 | SF2 open in Excel                             | Close Excel (check Task Manager)                                                 | Always close file before scanning                 |
| 3  | App exits immediately                        | Revoked license or sharing detected           | Check `active` in Firebase → delete local `license.json` to re-enter             | Monitor hardware entries in Firebase              |
| 4  | No students loaded                           | Wrong column / filtered out                   | Names in Col B row 13+ → temp disable filters in `is_valid_student_name`         | Follow official DepEd SF2 template                |
| 5  | QR scanning unreliable                       | Bad print, lighting, distance                 | Regenerate larger → better light → hold 10–20 cm                                 | Laminate, use matte sticker paper                 |
| 6  | Corrupted file warning & repair fails        | Damaged .xlsx zip structure                   | Restore backup → open in Excel → Save As new                                     | Weekly backup of Active folder                    |
| 7  | License validation fails (online)            | Wrong config, firewall, DB rules              | Verify `FIREBASE_CONFIG` → test URL → check firewall/proxy                       | Use school Wi-Fi for first validation             |
| 8  | App freezes / slow scanning                  | Large file, low RAM, old hardware             | Reduce students per file → close apps → increase thread sleep                    | Split large classes into multiple SF2 files       |
| 9  | EULA/license not saving                      | No write permission                           | Run as admin once → check folder perms → create `.attendance_system` manually    | Avoid restricted/network drives                   |
| 10 | Stuck in "Offline mode"                      | No internet, corrupted cache                  | Connect → delete `licenses_cache.json` → restart                                 | Validate online at least monthly                  |
| 11 | Multiple HWIDs under one license             | Key shared across computers                   | Revoke in Firebase → issue new key → educate users                               | Unique keys per teacher/device                    |
| 12 | Many "⚠️ Error" messages in console          | Network timeout / Firebase unreachable        | Usually safe if offline mode works — ignore unless malfunction                   | Add file logging if support needed                |

**When reporting issues** — include: error text, console output (last 10–20 lines), OS + Python version, online/offline status, steps tried.

## Screenshots

<p align="center">
  <img src="screenshots/1-qr-generator-loaded.png" alt="QR Generator – File Loaded & Ready" width="45%"/>
  <img src="screenshots/2-scanner-in-action.png" alt="Scanner – Live QR Scanning" width="45%"/>
</p>

<p align="center">
  <img src="screenshots/3-preview-tab.png" alt="Preview Tab – Scanned Students & Status" width="45%"/>
  <img src="screenshots/4-settings-license.png" alt="Settings Tab – License & Folder Info" width="45%"/>
</p>

> Add your real screenshots to a `screenshots/` folder in the repo and update paths.

**100% human-written code**  
Athan Meir — Tanza, Calabarzon, Philippines — January 30, 2026
