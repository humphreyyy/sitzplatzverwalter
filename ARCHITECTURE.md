# Sitzplatz-Manager - System Architecture

## 1. Project Overview

**Name:** Sitzplatz-Manager
**Purpose:** Desktop application for managing student seating assignments with visual floorplan editor
**Target Users:** Teachers/administrators managing classroom seating
**Tech Stack:** Python 3.9+, Tkinter, Pillow, ReportLab, PyInstaller

---

## 2. Project Structure

```
sitzplatzverwalter/
├── gui/                      # User Interface Layer
│   ├── __init__.py
│   ├── main_window.py        # Main application window with menu/toolbar/tabs
│   ├── floorplan_tab.py      # Floorplan editor (Canvas with drag&drop)
│   ├── students_tab.py       # Student management interface
│   ├── planning_tab.py       # Weekly planning with assignment canvas
│   └── dialogs.py            # Modal dialogs (lock warning, properties, etc)
│
├── logic/                    # Business Logic Layer
│   ├── __init__.py
│   ├── assignment_engine.py  # Seat assignment algorithm
│   ├── validator.py          # Business rule validation
│   └── pdf_exporter.py       # PDF generation from assignments
│
├── data/                     # Data Access Layer
│   ├── __init__.py
│   ├── data_manager.py       # Load/save/backup JSON
│   ├── lock_manager.py       # File locking for multi-user
│   └── undo_manager.py       # Undo/Redo state management
│
├── models/                   # Data Model Definitions
│   ├── __init__.py
│   ├── seat.py              # Seat dataclass
│   ├── room.py              # Room dataclass
│   ├── student.py           # Student dataclass
│   └── assignment.py        # Assignment dataclass
│
├── config.py                 # Configuration: colors, constants, German text
├── main.py                   # Application entry point
├── data.json                 # Application data (created at runtime)
├── data.lock                 # Lock file for multi-user support
├── assets/
│   └── grundriss.png        # Floorplan background image
└── backups/                 # Automatic backup directory
```

---

## 3. Data Models

All models defined as Python dataclasses with type hints and validation.

### 3.1 Room

```python
@dataclass
class Room:
    id: str                    # Unique identifier (e.g., "room_001")
    name: str                  # Display name (e.g., "Klassenraum A")
    x: float                   # Canvas X position
    y: float                   # Canvas Y position
    width: float              # Room width in pixels
    height: float             # Room height in pixels
    color: str                # Hex color for drawing (#1e3a5f, #e31e24, or #a8c5dd)

    def contains_point(self, px: float, py: float) -> bool:
        """Check if point (px, py) is within room bounds."""
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height
```

### 3.2 Seat

```python
@dataclass
class Seat:
    id: str                    # Unique identifier (e.g., "seat_001")
    room_id: str              # Reference to Room.id
    number: int               # Seat number within room (e.g., 1, 2, 3)
    x: float                  # Canvas X position
    y: float                  # Canvas Y position (position within room)
    properties: dict          # Flexible properties (e.g., {"near_window": True})

    def get_display_name(self) -> str:
        """Return formatted display name."""
        return f"Seat {self.number}"
```

### 3.3 Student

```python
@dataclass
class Student:
    id: str                    # Unique identifier (e.g., "student_001")
    name: str                 # Student name
    weekly_pattern: dict      # Attendance per day: {"monday": True, "tuesday": False, ...}
    valid_from: str           # Start date (ISO format: YYYY-MM-DD)
    valid_until: str          # End date (ISO format: YYYY-MM-DD) or "ongoing"
    requirements: list        # List of seat property requirements (e.g., ["near_window"])

    def is_available_on(self, day: str) -> bool:
        """Check if student is available on given day."""
        day_lower = day.lower()
        return self.weekly_pattern.get(day_lower, False)
```

### 3.4 Assignment

```python
@dataclass
class Assignment:
    student_id: str           # Reference to Student.id
    seat_id: str             # Reference to Seat.id
    day: str                 # Day of week (e.g., "monday")
    week: str                # Week identifier (e.g., "2025-W43")

    def get_key(self) -> str:
        """Return unique identifier for this assignment."""
        return f"{self.week}_{self.day}_{self.student_id}"
```

---

## 4. JSON Data Schemas

### 4.1 data.json Structure

Complete JSON file containing floorplan, students, and assignments.

```json
{
  "metadata": {
    "version": "1.0",
    "last_modified": "2025-10-31T14:30:00Z",
    "last_user": "admin@PC-01"
  },
  "floorplan": {
    "rooms": [
      {
        "id": "room_001",
        "name": "Klassenraum A",
        "x": 50,
        "y": 50,
        "width": 400,
        "height": 300,
        "color": "#1e3a5f"
      }
    ],
    "seats": [
      {
        "id": "seat_001",
        "room_id": "room_001",
        "number": 1,
        "x": 70,
        "y": 80,
        "properties": {
          "near_window": true,
          "near_door": false
        }
      }
    ]
  },
  "students": [
    {
      "id": "student_001",
      "name": "Alice Schmidt",
      "weekly_pattern": {
        "monday": true,
        "tuesday": true,
        "wednesday": false,
        "thursday": true,
        "friday": true,
        "saturday": false,
        "sunday": false
      },
      "valid_from": "2025-10-01",
      "valid_until": "ongoing",
      "requirements": ["near_window"]
    }
  ],
  "assignments": {
    "2025-W43": {
      "monday": [
        {
          "student_id": "student_001",
          "seat_id": "seat_001"
        }
      ],
      "tuesday": [],
      "wednesday": [],
      "thursday": [],
      "friday": [],
      "saturday": [],
      "sunday": []
    }
  }
}
```

### 4.2 data.lock Structure

Lock file for multi-user support, prevents concurrent modifications.

```json
{
  "locked": true,
  "user": "admin@PC-01",
  "timestamp": "2025-10-31T14:30:00Z",
  "pid": 12345,
  "hostname": "PC-01"
}
```

---

## 5. Component Architecture

### 5.1 Data Layer (data/)

**DataManager**: Handles all JSON I/O operations
- `load_data() -> dict`: Load data.json into memory
- `save_data(data: dict)`: Save data to JSON file with backup
- `backup_data()`: Create timestamped backup
- `validate_data(data: dict) -> bool`: Verify data integrity

**LockManager**: Manages file locking for multi-user scenarios
- `acquire_lock(user: str) -> bool`: Try to acquire lock, return success
- `release_lock()`: Release current lock
- `is_locked() -> bool`: Check if file is locked
- `get_lock_info() -> dict`: Retrieve lock metadata
- `is_stale_lock(max_age_seconds: 3600) -> bool`: Check if lock is older than threshold

**UndoManager**: Stack-based undo/redo system
- `push_state(state: dict)`: Add state to undo stack (max 50)
- `undo() -> dict`: Retrieve previous state, return it
- `redo() -> dict`: Retrieve next state
- `can_undo() -> bool`: Check if undo is available
- `can_redo() -> bool`: Check if redo is available
- `clear()`: Reset stacks

### 5.2 Logic Layer (logic/)

**AssignmentEngine**: Core algorithm for automatic seat assignment
- `assign_week(students: list, seats: list, week: str) -> (assignments: list, conflicts: list)`:
  Main algorithm, returns both successful assignments and conflict list
- `get_priority_sort_key(student: Student) -> tuple`: Generate sort key for prioritization
- `find_seat_for_student(student: Student, available_seats: list) -> Seat`:
  Find best seat matching preferences
- `track_conflicts(students: list, assigned_count: int) -> list`:
  Identify unassigned students

**Validator**: Business rule validation
- `validate_room_overlap(rooms: list) -> bool`: Check for overlapping rooms
- `validate_seat_in_room(seat: Seat, room: Room) -> bool`: Verify seat belongs to room
- `validate_capacity(students: list, seats: list) -> (bool, dict)`: Check overbooking
- `validate_student_date_range(student: Student) -> bool`: Verify date range is valid
- `validate_assignment_conflicts(assignments: list) -> list`: Detect conflicts

**PdfExporter**: PDF generation from assignments
- `export_week_to_pdf(week: str, assignments: dict, floorplan: dict) -> bytes`: Generate PDF
- `capture_canvas_snapshot(canvas: Canvas) -> Image`: Create image from canvas
- `generate_report(week: str, statistics: dict) -> PDF`: Create formatted report

### 5.3 GUI Layer (gui/)

**MainWindow**: Top-level application window
- Menu bar: File (New, Open, Save, Export PDF), Edit (Undo, Redo), Help
- Toolbar: Save, Undo, Redo, Export buttons with icons
- Status bar: Lock status, last save time, user info
- Tab container: 3 tabs (Raumplan, Studenten, Wochenplanung)

**FloorplanTab**: Visual editor for rooms and seats
- Canvas with grundriss.png as background layer
- Add Room button → Click to draw room (rectangle)
- Add Seat button → Click to place seat (circle)
- Drag & drop existing rooms/seats
- Right-click context menu: Properties, Delete
- Properties panel: Editable fields for selected element

**StudentsTab**: Manage student records
- Left panel: Student list with search box, Add/Delete buttons
- Right panel: Edit form with:
  - Name field (text)
  - Weekly pattern: 7 checkboxes (Mon-Sun)
  - Valid from/until: Date pickers
  - Requirements: Multi-select checkboxes (near_window, near_door, etc)
  - Save/Cancel buttons

**PlanningTab**: Weekly assignment and visualization
- Week selector (dropdown or forward/backward buttons)
- 7 tabs for each day (Montag through Sonntag)
- Per-day canvas showing:
  - All seats with color coding
    * Green: Free seat
    * Yellow: Occupied seat (student assigned)
    * Red: Conflict (overbooking)
  - List of present students for that day
  - Conflict indicator and count
- "Automatisch zuteilen" button: Runs assignment algorithm
- Manual assignment: Drag student to seat or vice versa

**Dialogs**: Modal dialogs for special interactions
- Lock warning: Show if file is locked by another user, offer read-only mode
- Room properties: Edit room name, color, dimensions
- Seat properties: Edit seat number, properties/requirements
- Confirm dialogs: Before destructive operations

### 5.4 Configuration (config.py)

```python
# Colors (Dittmann brand colors)
COLOR_PRIMARY = "#1e3a5f"      # Dark blue
COLOR_ACCENT = "#e31e24"        # Red
COLOR_LIGHT = "#a8c5dd"         # Light blue

# Seat status colors
COLOR_FREE = "#90EE90"          # Green
COLOR_OCCUPIED = "#FFD700"      # Yellow
COLOR_CONFLICT = "#FF6B6B"      # Red

# UI Constants
UNDO_STACK_MAX = 50
LOCK_TIMEOUT_SECONDS = 3600     # 1 hour
AUTO_BACKUP_INTERVAL = 300      # 5 minutes

# German weekday names
WEEKDAYS = {
    "monday": "Montag",
    "tuesday": "Dienstag",
    "wednesday": "Mittwoch",
    "thursday": "Donnerstag",
    "friday": "Freitag",
    "saturday": "Samstag",
    "sunday": "Sonntag"
}

WEEKDAY_ABBR = {
    "monday": "Mo",
    "tuesday": "Di",
    "wednesday": "Mi",
    "thursday": "Do",
    "friday": "Fr",
    "saturday": "Sa",
    "sunday": "So"
}
```

---

## 6. Assignment Algorithm (Core Business Logic)

### 6.1 High-Level Algorithm

```
FOR each day in week:
    students_for_day = [s for s in all_students if s.is_available_on(day)]
    available_seats = [seat for seat in all_seats if not assigned(seat, day)]

    IF count(students_for_day) > count(available_seats):
        add_capacity_conflict(day, count_excess)

    # Sort by priority: previous seat > requirements match > alphabetical
    sorted_students = sort_by_priority(students_for_day)

    assignments_this_day = []
    conflicts_this_day = []

    FOR each student in sorted_students:
        seat = find_best_seat(student, available_seats)

        IF seat found:
            create_assignment(student, seat, day)
            remove_seat_from_available(seat)
        ELSE:
            add_conflict(student)

    assignments[day] = assignments_this_day
    conflicts[day] = conflicts_this_day

RETURN assignments, conflicts
```

### 6.2 Priority Sort Key

Students are sorted using a composite key to determine assignment order:

```python
def get_priority_sort_key(student: Student, previous_assignments: dict) -> tuple:
    """
    Returns tuple for sorting: (priority_level, name)
    Lower values sort first (higher priority).
    """
    # Level 0: Student had seat on this day in previous week
    has_previous = 1 if student.id in previous_assignments else 0

    # Name for tie-breaking
    return (has_previous, student.name)
```

Students with previous seats are assigned first, then alphabetically.

### 6.3 Seat Selection

For each student, seats are selected in this order of preference:

1. **Previous Seat**: If student had a seat last week, try to assign same seat
2. **Requirements Match**: Find a seat that matches all student requirements
3. **Nearest Match**: Find seat closest to requirement match (partial match)
4. **Any Free Seat**: Assign any available seat in the room

---

## 7. File Locking Mechanism

### 7.1 Lock Workflow

**Acquiring a Lock:**
1. Check if `data.lock` exists
2. If not exists: Create new lock file with current user/PID/timestamp
3. If exists: Compare timestamp with current time
   - If < 1 hour old: Lock is valid, app goes to read-only mode
   - If >= 1 hour old: Lock is stale, delete and acquire new lock

**Releasing a Lock:**
- On application close or explicit save operation
- Delete `data.lock` file
- If delete fails (file permissions), log warning but continue

**Heartbeat (Optional):**
- Periodically update timestamp in lock file to prove app is still running
- Prevents stale lock detection for long-running sessions

### 7.2 Read-Only Mode

When another user has the file locked:
- Display warning dialog: "File is locked by [user@hostname], opened in read-only mode"
- Disable all editing buttons (Add, Delete, Assign, etc)
- Allow navigation and viewing only
- "Save" button disabled
- Display lock info in status bar

### 7.3 Lock File Timeout

Default timeout: 1 hour (3600 seconds)
- If lock file is older than this, assume previous instance crashed
- Automatically acquire new lock and proceed with editing

---

## 8. Undo/Redo System

### 8.1 State Snapshot

Each undo state captures:
```python
@dataclass
class StateSnapshot:
    timestamp: float           # When snapshot was taken
    floorplan: dict           # Complete floorplan state
    students: list            # All student records
    assignments: dict         # All assignments for all weeks
    metadata: dict            # Last modified user, etc
```

### 8.2 Stack-Based Implementation

```python
class UndoManager:
    def __init__(self, max_states: int = 50):
        self.undo_stack: list[StateSnapshot] = []
        self.redo_stack: list[StateSnapshot] = []
        self.max_states = max_states

    def push_state(self, state: dict):
        """Add new state to undo stack, clear redo stack."""
        self.undo_stack.append(StateSnapshot(time.time(), **state))
        if len(self.undo_stack) > self.max_states:
            self.undo_stack.pop(0)  # Remove oldest
        self.redo_stack.clear()     # Clear redo when new action

    def undo(self) -> dict:
        """Move current state to redo, return previous state."""
        if not self.undo_stack:
            return None
        self.redo_stack.append(self.undo_stack.pop())
        return self.undo_stack[-1] if self.undo_stack else None

    def redo(self) -> dict:
        """Move state from redo back to undo."""
        if not self.redo_stack:
            return None
        self.undo_stack.append(self.redo_stack.pop())
        return self.undo_stack[-1]
```

### 8.3 When Snapshots Are Taken

- After adding/deleting/modifying rooms
- After adding/deleting/modifying students
- After running automatic assignment
- After manual assignment change
- Before saving (to allow undo of save)

---

## 9. Error Handling & Edge Cases

### 9.1 Data Integrity

**Corrupt JSON File:**
- Attempt to parse JSON, catch JSONDecodeError
- Log error with timestamp and file location
- Create backup of corrupt file with timestamp
- Prompt user to recover from backup or start fresh
- Application starts with empty floorplan if user chooses new start

**Missing grundriss.png:**
- Check for image file at startup in assets/ directory
- If not found, log warning
- Display canvas with gray background instead
- Floorplan editor still functional but without image background
- Show warning in status bar: "Background image not found"

**Stale Lock File:**
- If lock file is older than 1 hour, automatically remove it
- Log action with timestamp
- Proceed with normal editing after acquiring new lock

### 9.2 Assignment Conflicts

**Overbooking (More Students than Seats):**
- Return list of unassigned students (conflicts)
- Display conflict count in Planning tab
- Color conflicted seats red
- Provide interface to manually resolve (move student to different day or remove)

**Overlapping Room Definitions:**
- Validator.validate_room_overlap() detects overlaps
- Alert user during room creation
- Prevent saving floorplan with overlaps
- Allow user to adjust room dimensions interactively

**Invalid Date Ranges:**
- Student.valid_until must be >= Student.valid_from
- Validator catches this before saving
- Display error dialog with correction required

### 9.3 Multi-User Scenarios

**Concurrent Save Attempts:**
- User A tries to save while User B has lock
- User A's save fails, displays message: "File is locked by User B"
- User A's changes are preserved in current session (undo available)
- User A can retry after User B releases lock or timeout occurs

**Stale PID (Process Died):**
- Check if process PID in lock file still exists
- On Windows: Use `tasklist`, on Linux/Mac: Use `ps`
- If not found, treat lock as stale, allow new lock acquisition

### 9.4 Boundary Conditions

**Zero Students:**
- Assignment algorithm handles empty student list gracefully
- Returns empty assignments, no conflicts
- Floorplan can still be displayed

**Single Seat Room:**
- Multiple students available but only 1 seat
- First student (by priority) gets seat
- Others appear in conflict list

**Empty Floorplan:**
- User can view/edit students even without rooms
- Assignment algorithm skips (no seats to assign to)
- Display message: "No rooms defined" in Planning tab

---

## 10. Implementation Sequence

### Phase 2: Data Layer
Implement models/, data/ modules
- Define dataclasses with validation
- Implement JSON serialization
- Build lock management
- Test file I/O

### Phase 3: Business Logic
Implement logic/ modules
- Build assignment algorithm with test cases
- Implement validators
- Create PDF export functionality
- Unit test each component

### Phase 4: GUI
Implement gui/ modules
- Create Tkinter main window structure
- Implement floorplan editor with drag&drop
- Build student management interface
- Create planning/assignment interface

### Phase 5: Integration & Testing
- Connect all layers
- E2E testing (create floorplan → add students → assign → export)
- Multi-user testing
- Performance/stress testing

### Phase 6: Deployment
- PyInstaller build configuration
- Package creation with assets
- User documentation (German)
- Installer creation

---

## 11. Design Decisions & Rationale

1. **Three-Layer Architecture**: Clear separation of concerns (Data/Logic/GUI) enables independent testing and future enhancements

2. **Dataclasses for Models**: Type hints + lightweight syntax, better than plain dictionaries

3. **File-Based Locking**: Simple implementation compatible with network drives, no need for database

4. **JSON Storage**: Human-readable, easy to backup, no database dependency

5. **Stack-Based Undo**: Memory-efficient with bounded history (50 states max)

6. **German UI**: All user-facing text in German with internationalization-ready structure for future expansion

7. **Dittmann Colors**: Brand consistency, provided color palette is professional and accessible

---

## 12. Future Extensibility

- **Database Backend**: Replace JSON I/O with SQLite/PostgreSQL
- **Network Sync**: Cloud-based storage with automatic sync
- **Advanced Scheduling**: Time slots within days, recurring patterns
- **Student Groups**: Assign whole groups to table clusters
- **Mobile App**: Cross-platform assignment viewing (Qt/Flutter)
- **Analytics**: Seating pattern analysis, student preference learning
