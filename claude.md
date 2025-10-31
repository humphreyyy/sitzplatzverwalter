# Sitzplatz-Manager - Project Context for Claude

**Last Updated:** 2025-10-31

## Project Overview

**Name:** Sitzplatz-Manager

**Description:** Desktop application for managing student seating assignments in a classroom with visual floorplan editor

**Purpose:** Help teachers/administrators organize and automate student seating arrangements with support for:
- Weekly attendance patterns
- Automatic intelligent assignment
- Manual override capability
- Multi-user collaboration with file locking
- PDF export of seating plans

## Tech Stack

- **Language:** Python 3.9+
- **GUI Framework:** Tkinter (built-in, cross-platform)
- **Image Processing:** Pillow
- **PDF Generation:** ReportLab
- **Packaging:** PyInstaller
- **Data Storage:** JSON files
- **Concurrency:** File-based locking mechanism

## Architecture Type

**Three-Layer Modular Architecture:**
- **Data Layer** (data/): JSON I/O, file locking, undo/redo
- **Logic Layer** (logic/): Business rules, assignment algorithm, validation
- **GUI Layer** (gui/): Tkinter user interface

## Project Structure

```
sitzplatzverwalter/
├── gui/                    # Tkinter GUI components
├── logic/                  # Business logic and algorithms
├── data/                   # Data access and persistence
├── models/                 # Data model definitions
├── config.py              # Configuration and constants
├── main.py                # Application entry point
├── data.json              # Application data (runtime)
├── data.lock              # Multi-user lock file
├── assets/                # Static resources (images)
└── backups/               # Automatic backup directory
```

## Key Design Decisions

1. **Separation of Concerns:** Clear boundaries between UI, logic, and data enable independent testing and maintenance

2. **File-Based Architecture:** Uses JSON + file locking for simplicity, network drive compatibility, and easy backups

3. **Assignment Algorithm:** Priority-based: previous seat holders → requirement matches → alphabetical order

4. **Undo/Redo:** Stack-based with max 50 states, memory-bounded

5. **Multi-User Support:** File lock mechanism with 1-hour timeout, automatic stale lock detection

6. **German UI:** All user-facing text in German, consistent with Dittmann brand colors

## Coding Conventions

### Python Style
- **Type Hints:** All function signatures must include type hints
- **Docstrings:** Public methods and classes require docstrings
- **Dataclasses:** Use `@dataclass` for all model definitions in models/
- **Naming:** snake_case for functions/variables, PascalCase for classes
- **Constants:** SCREAMING_SNAKE_CASE in config.py

### UI/UX
- **Language:** German only, all menus/buttons/dialogs
- **Colors:** Dittmann brand colors
  - `#1e3a5f` (Dark blue, primary)
  - `#e31e24` (Red, accent)
  - `#a8c5dd` (Light blue, secondary)
- **Status Colors:** Green (free), Yellow (occupied), Red (conflict)
- **Fonts:** System default, readable sans-serif

### Data Organization
- **Models Location:** `models/` directory, one class per file
- **Configuration:** Centralized in `config.py`
- **JSON Keys:** snake_case (not camelCase)
- **Dates:** ISO format (YYYY-MM-DD)
- **Timestamps:** ISO 8601 with timezone (UTC)

## Current Implementation Status

- [x] **Phase 1: Architecture** ✓ Complete
  - ARCHITECTURE.md created with complete specifications
  - claude.md created (this file)
  - PROGRESS.md created

- [ ] **Phase 2: Data Layer** (Next)
  - Implement models: Seat, Room, Student, Assignment
  - Implement DataManager (JSON I/O, backup)
  - Implement LockManager (file locking)
  - Implement UndoManager (undo/redo)
  - Unit tests for data layer

- [ ] **Phase 3: Business Logic**
  - AssignmentEngine (seat assignment algorithm)
  - Validator (business rule validation)
  - PdfExporter (PDF generation)
  - Logic tests

- [ ] **Phase 4: GUI Implementation**
  - MainWindow with menu/toolbar/tabs
  - FloorplanTab (room/seat editor with drag&drop)
  - StudentsTab (student management)
  - PlanningTab (weekly assignment interface)
  - Dialogs and error handling

- [ ] **Phase 5: Testing & QA**
  - Unit tests for all components
  - Integration testing (layers working together)
  - E2E testing (full workflows)
  - Multi-user testing
  - Bug documentation

- [ ] **Phase 6: Deployment**
  - PyInstaller build configuration
  - Package structure with assets
  - German user guide
  - Windows executable creation

## Key Files Reference

- **ARCHITECTURE.md** - Complete technical specification and design rationale
- **PROGRESS.md** - Implementation progress tracking
- **TEST_REPORT.md** - Test results and coverage (created during Phase 5)
- **BUGS.md** - Known issues and limitations (created during Phase 5)

## Important Constants

**From config.py:**
- `UNDO_STACK_MAX = 50` - Maximum undo states
- `LOCK_TIMEOUT_SECONDS = 3600` - Lock file timeout (1 hour)
- `AUTO_BACKUP_INTERVAL = 300` - Backup frequency (5 minutes)

**Weekdays (German):**
- Monday → Montag
- Tuesday → Dienstag
- Wednesday → Mittwoch
- Thursday → Donnerstag
- Friday → Freitag
- Saturday → Samstag
- Sunday → Sonntag

## Data File Schemas

### data.json
Contains complete application state: floorplan (rooms + seats), students, and assignments by week/day.

Example structure:
```json
{
  "metadata": {...},
  "floorplan": {
    "rooms": [...],
    "seats": [...]
  },
  "students": [...],
  "assignments": {
    "2025-W43": {
      "monday": [{"student_id": "...", "seat_id": "..."}],
      ...
    }
  }
}
```

### data.lock
Multi-user lock file, prevents concurrent modifications.

Example:
```json
{
  "locked": true,
  "user": "admin@PC-01",
  "timestamp": "2025-10-31T14:30:00Z",
  "pid": 12345,
  "hostname": "PC-01"
}
```

See ARCHITECTURE.md for complete schemas and examples.

## Assignment Algorithm Overview

**Priority-based automatic seating:**
1. Get students available on that day
2. Get free seats
3. Sort students: previous seat holders first, then alphabetically
4. For each student, try to assign:
   - Previous seat first (if available)
   - Requirement-matching seat (if has requirements)
   - Any free seat (fallback)
5. Track and report conflicts (unassigned students)

See ARCHITECTURE.md section 6 for pseudocode and detailed implementation guide.

## Multi-User File Locking

**Lock Mechanism:**
- Lock file: `data.lock` in project root
- Acquired on app startup, released on close/save
- Timeout: 1 hour (automatic stale lock removal)
- Read-only mode: If file is locked by another user

**Edge Cases Handled:**
- Stale locks from crashed processes
- Lock file corruption
- Multi-user concurrent access
- Network drive delays

See ARCHITECTURE.md section 7 for complete details.

## Next Steps (Phase 2)

1. Create models in models/ directory with dataclass definitions
2. Implement DataManager for JSON I/O and backup
3. Implement LockManager for multi-user file locking
4. Implement UndoManager for undo/redo functionality
5. Write unit tests for each data module
6. Document any deviations from ARCHITECTURE.md

All implementation must follow the specifications in ARCHITECTURE.md. If deviations are necessary, update ARCHITECTURE.md first and document the reason.

## Communication

For questions about:
- **Architecture/Design:** See ARCHITECTURE.md
- **Progress:** See PROGRESS.md
- **Bugs/Issues:** See BUGS.md (created Phase 5)
- **Test Coverage:** See TEST_REPORT.md (created Phase 5)
- **Implementation Details:** Docstrings in source code

---

**Auto-generated by Architecture Phase. Updates preserved across phases.**
