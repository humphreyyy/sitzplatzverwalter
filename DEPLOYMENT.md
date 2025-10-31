# Sitzplatz-Manager - Deployment & Build Guide

**Version:** 1.0
**Last Updated:** 2025-10-31
**Platform:** macOS (Intel + Apple Silicon)

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Build Process](#build-process)
4. [Distribution](#distribution)
5. [Installation for End Users](#installation-for-end-users)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Options](#advanced-options)

---

## Overview

This document describes how to build and distribute the Sitzplatz-Manager macOS application. The application is packaged using **py2app**, which creates a native macOS application bundle (.app).

### Technology Stack

- **Builder:** py2app 0.28+
- **Language:** Python 3.9+
- **GUI Framework:** Tkinter (built-in)
- **Key Dependencies:** ReportLab (PDF export)
- **Package Manager:** pip3

### Build Artifacts

- `Sitzplatz-Manager.app/` - The macOS application bundle (ready to run)
- `dist/` - Distribution directory containing the app
- `build/` - Temporary build directory (can be deleted)

---

## Prerequisites

### System Requirements

**For Building:**
- macOS 10.13 or higher
- Python 3.9 or higher
- pip3 (Python package manager)
- Xcode Command Line Tools (optional but recommended)

**For Running the App:**
- macOS 10.13 or higher
- No additional software required
- ~50 MB disk space

### Installation of Build Tools

1. **Install Python 3.9+** (if not already installed):
   ```bash
   # Using Homebrew
   brew install python@3.11

   # Or download from python.org
   # https://www.python.org/downloads/
   ```

2. **Verify Python Installation:**
   ```bash
   python3 --version
   ```

3. **Install Build Dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

---

## Build Process

### Quick Build

The easiest way to build the app is using the provided build script:

```bash
# Navigate to project directory
cd /path/to/sitzplatzverwalter

# Build the app
./build_macos.sh build

# The app will be created at: dist/Sitzplatz-Manager.app
```

### Manual Build Steps

If you prefer to build manually:

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Clean previous builds
rm -rf build dist

# 3. Run py2app
python3 setup.py py2app

# 4. The app is now in dist/Sitzplatz-Manager.app
open dist/Sitzplatz-Manager.app
```

### Build Script Options

The `build_macos.sh` script provides several options:

```bash
# Clean build artifacts
./build_macos.sh clean

# Build the app
./build_macos.sh build

# Test the built app
./build_macos.sh test

# Full workflow: clean, build, and test
./build_macos.sh all

# Show help
./build_macos.sh help
```

---

## Distribution

### Preparing for Distribution

1. **Clean Build:**
   ```bash
   ./build_macos.sh clean
   ./build_macos.sh build
   ```

2. **Create Distribution Package:**
   ```bash
   # Create a distribution directory
   mkdir -p dist_final

   # Copy the app
   cp -r dist/Sitzplatz-Manager.app dist_final/

   # Copy documentation
   cp ANLEITUNG.txt dist_final/
   cp README.md dist_final/
   cp LICENSE dist_final/ (if applicable)
   ```

3. **Verify Contents:**
   ```bash
   ls -la dist_final/
   # Expected:
   # - Sitzplatz-Manager.app/
   # - ANLEITUNG.txt
   # - README.md
   ```

### Creating a DMG Installer (Optional)

For a professional installation experience, you can create a DMG (Disk Image):

```bash
# Create a temporary directory
mkdir -p DMG_temp
cp -r dist/Sitzplatz-Manager.app DMG_temp/
cp ANLEITUNG.txt DMG_temp/README.txt

# Create the DMG
hdiutil create -volname "Sitzplatz-Manager" \
  -srcfolder DMG_temp \
  -ov -format UDZO \
  Sitzplatz-Manager.dmg

# Cleanup
rm -rf DMG_temp
```

The resulting `Sitzplatz-Manager.dmg` can be distributed to users.

### Code Signing (Optional - Requires Apple Developer Account)

If you have an Apple Developer account and certificate:

```bash
# Sign the app
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application" \
  dist/Sitzplatz-Manager.app

# Verify signature
codesign -d dist/Sitzplatz-Manager.app
```

---

## Installation for End Users

### For macOS Users

#### Method 1: Direct App Bundle

1. Download `Sitzplatz-Manager.app` (or decompress the DMG)
2. Double-click the app
3. If you get a security warning:
   - Right-click the app
   - Select "Open"
   - Click "Open" in the confirmation dialog
4. The app launches

#### Method 2: From DMG File

1. Download `Sitzplatz-Manager.dmg`
2. Double-click to mount the disk image
3. Drag `Sitzplatz-Manager.app` to the Applications folder
4. Open Applications folder and double-click `Sitzplatz-Manager.app`

#### Security Prompt

On first launch, macOS may show a security warning since the app is not signed:

```
"Sitzplatz-Manager" cannot be opened because it is from an unidentified developer.
```

To resolve:
1. Go to **System Preferences** → **Security & Privacy**
2. Click the lock icon to unlock (if needed)
3. Click **Open Anyway** next to the Sitzplatz-Manager entry
4. Click **Open** in the confirmation dialog

---

## Troubleshooting

### Build Issues

#### Issue: `py2app: command not found`

**Solution:** Install py2app
```bash
pip3 install py2app
```

#### Issue: `ImportError: No module named 'reportlab'`

**Solution:** Install dependencies
```bash
pip3 install -r requirements.txt
```

#### Issue: Build fails with architecture mismatch

**Solution:** Ensure you're using the same Python architecture
```bash
# Check Python architecture
python3 -c "import struct; print(f'{struct.calcsize(\"P\") * 8}-bit')"

# For Apple Silicon (M1/M2/M3):
# Use native Python installed via Homebrew or python.org
```

#### Issue: `data.json` or assets not included in app bundle

**Solution:** Verify `setup.py` configuration
```bash
# Check that resources are properly defined in setup.py
grep -A 5 "resources" setup.py

# Rebuild
rm -rf build dist
python3 setup.py py2app
```

### Runtime Issues

#### Issue: App won't launch after building

**Solution:**
1. Check for permission errors:
   ```bash
   chmod +x dist/Sitzplatz-Manager.app/Contents/MacOS/Sitzplatz-Manager
   ```

2. Check the app logs:
   ```bash
   cat ~/Library/Logs/Sitzplatz-Manager.log
   ```

#### Issue: "dyld: Library not loaded" error

**Solution:** This usually means a dependency is missing. Rebuild:
```bash
pip3 install --upgrade -r requirements.txt
rm -rf build dist
python3 setup.py py2app
```

#### Issue: App crashes on launch

**Solution:**
1. Check the system log:
   ```bash
   log show --predicate 'process == "Sitzplatz-Manager"' --last 1h
   ```

2. Try running from terminal for debugging:
   ```bash
   dist/Sitzplatz-Manager.app/Contents/MacOS/Sitzplatz-Manager
   ```

---

## Advanced Options

### Building for Specific Architecture

By default, py2app builds for the current architecture. To build universal binaries (Intel + Apple Silicon):

1. Ensure Python is installed via Homebrew (which supports universal builds)
2. Modify `setup.py`:
   ```python
   OPTIONS = {
       "py2app": {
           # ... existing options ...
           "arch": "universal2",  # Intel + Apple Silicon
       }
   }
   ```

3. Rebuild:
   ```bash
   python3 setup.py py2app
   ```

### Customizing the App Icon

1. Create an icon file (1024x1024 PNG recommended)
2. Convert to ICNS format:
   ```bash
   # Using online tool or ImageMagick
   convert icon.png -define icon:auto-resize icon.icns
   ```

3. Update `setup.py`:
   ```python
   OPTIONS = {
       "py2app": {
           "iconfile": "icon.icns",
           # ... other options ...
       }
   }
   ```

4. Rebuild:
   ```bash
   rm -rf build dist
   python3 setup.py py2app
   ```

### Including Additional Files

To include additional files (documents, config files, etc.):

1. Update `setup.py` data_files:
   ```python
   DATA_FILES = [
       ("assets", ["assets/Grundriss.png"]),
       ("docs", ["README.md", "ANLEITUNG.txt"]),
   ]
   ```

2. Rebuild:
   ```bash
   python3 setup.py py2app
   ```

### Environment Variables for Build Debugging

```bash
# Enable verbose output
python3 setup.py py2app -v

# Show all included modules
python3 setup.py py2app --verbose-build
```

---

## Version Updates

### When to Rebuild

- After updating Python or dependencies
- After changing Python code
- After adding new files or assets
- Before distributing to users

### Version Numbering

Update version in `setup.py`:

```python
VERSION = "1.0.1"  # Increment after changes
```

Also update in:
- `config.py` (if applicable)
- Release notes
- ANLEITUNG.txt

---

## Testing the Build

### Automated Testing

Use the build script:
```bash
./build_macos.sh all
```

### Manual Testing Checklist

After building, verify:

- [ ] App launches without errors
- [ ] All GUI tabs load correctly (Grundriss, Schüler, Planung)
- [ ] Can create a new project
- [ ] Can add students and rooms
- [ ] Can save data
- [ ] Can perform undo/redo
- [ ] Can export to PDF
- [ ] Application closes cleanly

### Testing on Clean System

To test like an end user:

1. Copy `dist/Sitzplatz-Manager.app` to another Mac
2. Try to launch it
3. Test all features
4. Report any issues

---

## Performance Notes

### App Bundle Size

- Typical size: 100-200 MB
- Python runtime: ~80 MB
- Dependencies: ~30 MB
- Code and assets: ~10 MB

### Startup Time

- First launch: 3-5 seconds (Python initialization)
- Subsequent launches: 1-2 seconds

### Optimization Tips

- The app will be faster on SSDs
- Ensure sufficient RAM (2 GB minimum recommended)
- Close other applications for better performance

---

## Security Considerations

### Code Signing

For distribution beyond internal use, consider:
1. Obtaining an Apple Developer account ($99/year)
2. Code signing the app with your certificate
3. Creating a notarized version for Gatekeeper compatibility

### Data Privacy

The app stores data locally in:
- `data.json` (application data)
- `backups/` (automatic backups)
- No data is sent to external servers

### Backup Security

Ensure data backups are:
- Stored in secure locations
- Backed up regularly
- Protected with appropriate file permissions

---

## Support Resources

### Documentation Files

- `README.md` - Project overview and technical documentation
- `ANLEITUNG.txt` - User guide (German)
- `ARCHITECTURE.md` - System design and architecture
- `TEST_REPORT.md` - Testing results and coverage

### Build Script Help

```bash
./build_macos.sh help
```

### Python py2app Documentation

- https://py2app.readthedocs.io/
- https://py2app.readthedocs.io/en/latest/setup.html

---

## Changelog

### Version 1.0 (2025-10-31)

- Initial macOS release
- py2app-based deployment
- Support for Intel and Apple Silicon Macs
- Automated build script
- German user guide

---

**Last Updated:** 2025-10-31
**Maintained by:** Sitzplatz Team
