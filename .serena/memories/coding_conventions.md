# Coding Conventions - Sitzplatz-Manager

## Python Style
- **Type Hints:** MANDATORY on all function signatures
- **Docstrings:** Required for all public methods and classes
- **Dataclasses:** Use `@dataclass` for all model definitions in models/
- **Naming:** 
  - `snake_case` for functions/variables/modules
  - `PascalCase` for classes
  - `SCREAMING_SNAKE_CASE` for constants (config.py)
- **Constants:** Keep all in config.py, centralized

## UI/UX Standards
- **Language:** German ONLY for all user-facing text
- **Colors (Dittmann Brand):**
  - `#1e3a5f` (Dark blue, primary)
  - `#e31e24` (Red, accent)
  - `#a8c5dd` (Light blue, secondary)
- **Status Colors:**
  - Green (#90EE90) = Free seat
  - Yellow (#FFD700) = Occupied seat
  - Red (#FF6B6B) = Conflict
- **Fonts:** System default, readable sans-serif

## Data Organization
- **Models Location:** `models/` directory, one class per file
- **Configuration:** Centralized in `config.py`
- **JSON Keys:** snake_case (NOT camelCase)
- **Dates:** ISO format (YYYY-MM-DD)
- **Timestamps:** ISO 8601 with timezone (UTC)

## German UI Texts
All UI texts defined in config.py UI_TEXTS dictionary:
- Menu labels: "Datei", "Bearbeiten", "Hilfe"
- Buttons: "Speichern", "Abbrechen", "Automatisch zuteilen"
- Tab names: "Raumplan", "Studenten", "Wochenplanung"
- Status: "Datei gesperrt", "Schreibgeschützt", "Konflikte"

## Important Constants (config.py)
- `UNDO_STACK_MAX = 50` - Maximum undo states
- `LOCK_TIMEOUT_SECONDS = 3600` - Lock file timeout (1 hour)
- `AUTO_BACKUP_INTERVAL = 300` - Backup frequency (5 minutes)
- `DEFAULT_CANVAS_WIDTH = 1000`, `DEFAULT_CANVAS_HEIGHT = 700`
- `DEFAULT_SEAT_SIZE = 20` - Seat circle radius

## Weekday Mappings (from config.py)
- Monday → "Montag" (abbr: "Mo")
- Tuesday → "Dienstag" (abbr: "Di")
- Wednesday → "Mittwoch" (abbr: "Mi")
- Thursday → "Donnerstag" (abbr: "Do")
- Friday → "Freitag" (abbr: "Fr")
- Saturday → "Samstag" (abbr: "Sa")
- Sunday → "Sonntag" (abbr: "So")
