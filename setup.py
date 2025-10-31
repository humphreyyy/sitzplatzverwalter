"""
Setup configuration for py2app to create macOS application bundle.

This script builds the Sitzplatz-Manager macOS app (.app bundle) with:
- All Python dependencies included
- Assets bundled (images, templates)
- German localization support
- Proper GUI application setup
"""

from setuptools import setup
from pathlib import Path

# Read version and metadata
PROJECT_NAME = "Sitzplatz-Manager"
VERSION = "1.0.0"
AUTHOR = "Sitzplatz Team"
DESCRIPTION = "Desktop application for managing student seating assignments"

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent

# Data files to include in the app bundle
DATA_FILES = [
    ("assets", ["assets/Grundriss.png"]),
]

# py2app options
OPTIONS = {
    "py2app": {
        # App information
        "argv_emulation": False,
        "iconfile": None,  # Optional: add icon.icns if available

        # Python configuration
        "packages": [
            "gui",
            "data",
            "logic",
            "models",
        ],

        # Include all necessary modules
        "includes": [
            "tkinter",
            "json",
            "logging",
            "dataclasses",
            "reportlab",
        ],

        # Exclude unnecessary modules to reduce bundle size
        "excludes": [
            "pytest",
            "unittest",
            "email",
            "html",
            "http",
            "urllib",
            "asyncio",
        ],

        # Data files (assets, templates, etc.)
        "resources": [
            "assets",
        ],

        # Framework search paths (if needed)
        "frameworks": [],

        # Plist entries for macOS app
        "plist": {
            "CFBundleName": PROJECT_NAME,
            "CFBundleVersion": VERSION,
            "CFBundleShortVersionString": VERSION,
            "CFBundleIdentifier": "de.sitzplatz.manager",
            "CFBundleDocumentTypes": [],
            "NSHumanReadableCopyright": "Copyright 2025 Sitzplatz Team",
            "NSHighResolutionCapable": True,
            "NSSupportsAutomaticGraphicsSwitching": True,
        },
    }
}

setup(
    name=PROJECT_NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    app=["main.py"],
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=["py2app"],
)
