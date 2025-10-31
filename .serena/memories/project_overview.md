# Sitzplatz-Manager Project Overview

## Project Purpose
Desktop application for managing student seating assignments in classrooms with visual floorplan editor. Supports weekly attendance patterns, automatic intelligent assignment, manual override, multi-user collaboration with file locking, and PDF export.

## Tech Stack
- **Language:** Python 3.9+
- **GUI Framework:** Tkinter (built-in, cross-platform)
- **Image Processing:** Pillow
- **PDF Generation:** ReportLab (optional)
- **Data Storage:** JSON files
- **Concurrency:** File-based locking mechanism
- **Build Tool:** PyInstaller (Phase 6)

## Architecture
**Three-Layer Modular Architecture:**
- **Data Layer** (data/): JSON I/O, file locking, undo/redo
- **Logic Layer** (logic/): Business rules, assignment algorithm, validation
- **GUI Layer** (gui/): Tkinter user interface

## Project Structure
```
sitzplatzverwalter/
├── gui/                    # GUI components (Phase 4 - IN PROGRESS)
├── logic/                  # Business logic (Phase 3 - COMPLETE)
│   ├── assignment_engine.py   # Intelligent seat assignment
│   ├── validator.py           # Business rule validation
│   └── pdf_exporter.py        # PDF report generation
├── data/                   # Data access (Phase 2 - COMPLETE)
│   ├── data_manager.py
│   ├── lock_manager.py
│   └── undo_manager.py
├── models/                 # Data models (Phase 2 - COMPLETE)
│   ├── seat.py
│   ├── room.py
│   ├── student.py
│   └── assignment.py
├── tests/                  # Unit tests (119 passing)
├── config.py              # Configuration and constants
├── main.py                # Application entry point
├── data.json              # Application data (runtime)
├── data.lock              # Multi-user lock file
└── ARCHITECTURE.md        # Complete technical specification
```

## Implementation Status
- [x] **Phase 1: Architecture** ✓ Complete
- [x] **Phase 2: Data Layer** ✓ Complete (63 tests passing)
- [x] **Phase 3: Business Logic** ✓ Complete (56 tests passing)
- [ ] **Phase 4: GUI Implementation** (3 hours est.) - IN PROGRESS
- [ ] **Phase 5: Testing & QA** (1.5 hours est.)
- [ ] **Phase 6: Deployment** (30 min est.)

## Phase 4 GUI Components to Implement
1. **MainWindow** - Menu bar, toolbar, status bar, tab container
2. **FloorplanTab** - Canvas with drag&drop, room/seat editor
3. **StudentsTab** - CRUD operations, search, student management
4. **PlanningTab** - Weekly assignments, auto-assignment button
5. **Dialogs** - Room properties, seat properties, confirmation dialogs
6. **Error Handling** - User-friendly error messages
