"""Configuration and constants for Sitzplatz-Manager application."""

from typing import Dict

# ============================================================================
# Colors (Dittmann Brand Colors)
# ============================================================================
COLOR_PRIMARY = "#1e3a5f"          # Dark blue, primary brand color
COLOR_ACCENT = "#e31e24"            # Red, accent color
COLOR_LIGHT = "#a8c5dd"             # Light blue, secondary color

# Seat status colors
COLOR_FREE = "#90EE90"              # Green
COLOR_OCCUPIED = "#FFD700"          # Yellow (gold)
COLOR_CONFLICT = "#FF6B6B"          # Red

# ============================================================================
# UI Constants
# ============================================================================
UNDO_STACK_MAX = 50                 # Maximum number of undo states to keep
LOCK_TIMEOUT_SECONDS = 3600         # 1 hour - lock file expiration
AUTO_BACKUP_INTERVAL = 300          # 5 minutes - automatic backup frequency

# ============================================================================
# File Names and Paths
# ============================================================================
DATA_FILE = "data.json"             # Application data file
LOCK_FILE = "data.lock"             # Multi-user lock file
BACKUP_DIR = "backups"              # Backup directory name
ASSETS_DIR = "assets"               # Assets directory name

# ============================================================================
# German Weekday Names
# ============================================================================
WEEKDAYS: Dict[str, str] = {
    "monday": "Montag",
    "tuesday": "Dienstag",
    "wednesday": "Mittwoch",
    "thursday": "Donnerstag",
    "friday": "Freitag",
    "saturday": "Samstag",
    "sunday": "Sonntag"
}

# Abbreviated weekday names
WEEKDAY_ABBR: Dict[str, str] = {
    "monday": "Mo",
    "tuesday": "Di",
    "wednesday": "Mi",
    "thursday": "Do",
    "friday": "Fr",
    "saturday": "Sa",
    "sunday": "So"
}

# Reverse mapping
WEEKDAY_FROM_GERMAN: Dict[str, str] = {v: k for k, v in WEEKDAYS.items()}

# ============================================================================
# German UI Text
# ============================================================================
UI_TEXTS: Dict[str, str] = {
    # Main window
    "app_title": "Sitzplatz-Manager",
    "file_menu": "Datei",
    "edit_menu": "Bearbeiten",
    "help_menu": "Hilfe",
    "new": "Neu",
    "open": "Öffnen",
    "save": "Speichern",
    "save_as": "Speichern unter",
    "export_pdf": "Als PDF exportieren",
    "exit": "Beenden",
    "undo": "Rückgängig",
    "redo": "Wiederherstellen",
    "about": "Über",

    # Tabs
    "floorplan_tab": "Raumplan",
    "students_tab": "Studenten",
    "planning_tab": "Wochenplanung",

    # Buttons
    "add_room": "Raum hinzufügen",
    "add_seat": "Sitzplatz hinzufügen",
    "add_student": "Schüler hinzufügen",
    "delete": "Löschen",
    "save_button": "Speichern",
    "cancel": "Abbrechen",
    "auto_assign": "Automatisch zuteilen",

    # Properties
    "name": "Name",
    "number": "Nummer",
    "room": "Raum",
    "color": "Farbe",
    "position": "Position",
    "properties": "Eigenschaften",
    "requirements": "Anforderungen",
    "weekly_pattern": "Wochenplan",
    "valid_from": "Gültig ab",
    "valid_until": "Gültig bis",
    "near_window": "Nächst Fenster",
    "near_door": "Nächst Tür",

    # Status messages
    "file_locked": "Datei gesperrt",
    "read_only": "Schreibgeschützt",
    "last_saved": "Zuletzt gespeichert",
    "unsaved_changes": "Ungespeicherte Änderungen",
    "conflicts": "Konflikte",
    "free_seats": "Freie Plätze",
}

# ============================================================================
# Application Settings
# ============================================================================
DEFAULT_ROOM_WIDTH = 400            # Default room width in pixels
DEFAULT_ROOM_HEIGHT = 300           # Default room height in pixels
DEFAULT_SEAT_SIZE = 20              # Default seat circle radius in pixels
DEFAULT_CANVAS_WIDTH = 1000         # Default canvas width
DEFAULT_CANVAS_HEIGHT = 700         # Default canvas height

# ============================================================================
# Data Validation Rules
# ============================================================================
MIN_ROOM_WIDTH = 50
MAX_ROOM_WIDTH = 2000
MIN_ROOM_HEIGHT = 50
MAX_ROOM_HEIGHT = 2000

MIN_SEAT_NUMBER = 1
MAX_SEAT_NUMBER = 999

# ============================================================================
# Assignment Algorithm Constants
# ============================================================================
# Priority levels for student sorting (lower = higher priority)
PRIORITY_PREVIOUS_SEAT = 0
PRIORITY_REQUIREMENTS_MATCH = 1
PRIORITY_ALPHABETICAL = 2
