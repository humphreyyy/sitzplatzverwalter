# Sitzplatz-Manager - Compact Execution Guide

**Task:** Python Desktop App für Studenten-Sitzplatz-Verwaltung mit Tkinter

**🔑 WICHTIG:** Alle Agents aktualisieren automatisch `claude.md` mit Projekt-Context. Claude Code liest diese Datei automatisch bei jedem Start!

## Projekt-Spec

- Visueller Grundriss (grundriss.png als Background)
- 6 Studenten, wöchentliche Anwesenheitsmuster
- Automatische Zuteilung + manuelles Override
- File-Locking für Multi-User (Netzwerklaufwerk)
- Undo/Redo
- PDF Export
- Deutsche UI mit Dittmann Farben: `#1e3a5f`, `#e31e24`, `#a8c5dd`

## Tech Stack

```
Python 3.9+, Tkinter, Pillow, ReportLab, PyInstaller
```

## Sub-Agents Setup (WICHTIG: Zuerst ausführen!)

**Option A - Claude erstellt sie automatisch (EINFACHSTE):**

```
Create 6 sub-agents in .claude/agents/ directory:

1. architect.md (model: claude-sonnet-4-5-20250929)
   - Senior Python architect for system design
   - Design only, no implementation
   - Output: ARCHITECTURE.md, data schemas, pseudocode

2. data-impl.md (model: claude-haiku-4-5-20250929)
   - Implement data layer: models, JSON I/O, locking, undo
   - Follow specs exactly, type hints + docstrings

3. logic-impl.md (model: claude-sonnet-4-5-20250929)
   - Implement complex algorithms: assignment, validation, PDF
   - Focus on edge cases and efficiency

4. gui-impl.md (model: claude-sonnet-4-5-20250929)
   - Implement Tkinter GUI: Canvas with drag&drop, 3 tabs
   - German text, Dittmann colors (#1e3a5f, #e31e24, #a8c5dd)

5. tester.md (model: claude-haiku-4-5-20250929)
   - Write unit + integration tests
   - Test edge cases, document bugs in BUGS.md

6. deployer.md (model: claude-haiku-4-5-20250929)
   - PyInstaller build script, deployment package
   - German user guide (ANLEITUNG.txt)

Create these files now with appropriate system prompts.
```

**Option B - Manuell erstellen:**

Erstelle Ordner `.claude/agents/` und füge folgende Dateien hinzu:

**architect.md:**
```markdown
---
name: architect
description: System architect
model: claude-sonnet-4-5-20250929
---
Senior Python architect. Design only, no code. Output: ARCHITECTURE.md.
```

**data-impl.md:**
```markdown
---
name: data-impl
description: Data layer implementer
model: claude-haiku-4-5-20250929
---
Implement data layer: models, JSON I/O, locking. Follow specs exactly.
```

**logic-impl.md:**
```markdown
---
name: logic-impl
description: Business logic implementer
model: claude-sonnet-4-5-20250929
---
Implement algorithms: assignment, validation, PDF. Handle edge cases.
```

**gui-impl.md:**
```markdown
---
name: gui-impl
description: GUI implementer
model: claude-sonnet-4-5-20250929
---
Implement Tkinter GUI: Canvas, drag&drop, 3 tabs. German text, Dittmann colors.
```

**tester.md:**
```markdown
---
name: tester
description: QA tester
model: claude-haiku-4-5-20250929
---
Write tests, test edge cases. Document bugs in BUGS.md.
```

**deployer.md:**
```markdown
---
name: deployer
description: Deployment specialist
model: claude-haiku-4-5-20250929
---
PyInstaller build, package creation, German user guide.
```

**Verify agents:** Run `/agent list` - sollte alle 6 zeigen.

## Execution Plan

### Phase 1: Architecture (30 min)
```
Use the architect sub-agent.

Design:
- Project structure (folders: gui/, logic/, data/, models/)
- Data models (Seat, Room, Student, Assignment as dataclasses)
- JSON schema for data.json
- Assignment algorithm (pseudocode)
- GUI structure (3 tabs: Raumplan, Studenten, Wochenplanung)
- Lock mechanism (data.lock with PID, timestamp)

Output: ARCHITECTURE.md

/clear when done
```

### Phase 2: Data Layer (1.5h)
```
Use the data-impl sub-agent.

Implement according to ARCHITECTURE.md:

Files to create:
- config.py (colors, constants, German weekdays)
- models/seat.py, room.py, student.py, assignment.py
- data/data_manager.py (load, save, backup)
- data/lock_manager.py (acquire, release, heartbeat)
- data/undo_manager.py (push, undo, redo, max 50 states)

Test: Basic unit tests for each module.

/clear when done
```

### Phase 3: Business Logic (2h)
```
Use the logic-impl sub-agent.

Implement:
- logic/assignment_engine.py
  Algorithm: For each day, get students, sort by priority 
  (previous seat > requirements > alphabetical), assign seats, track conflicts
  
- logic/validator.py
  Validate room overlap, seat in room, capacity conflicts
  
- logic/pdf_exporter.py
  Capture canvas screenshots, generate PDF with ReportLab

/clear when done
```

### Phase 4: GUI (3h)
```
Use the gui-impl sub-agent.

Implement Tkinter GUI:

- gui/main_window.py
  Menu, toolbar (save/undo/redo), status bar, 3 tabs
  Lock check on startup → read-only if locked
  
- gui/floorplan_tab.py
  Canvas with grundriss.png background
  Add rooms (rectangles) and seats (circles) via buttons
  Drag & drop, properties panel
  
- gui/students_tab.py
  Left: student list with search
  Right: form (name, weekday checkboxes, date pickers, requirements)
  
- gui/planning_tab.py
  Week selector, day tabs (Mo-So)
  Canvas per day with colored seats (green=free, yellow=occupied, red=conflict)
  "Automatisch zuteilen" button → calls assignment_engine
  Side panel: present students, conflicts
  
- gui/dialogs.py
  Lock warning, room properties, seat properties

Colors from config.py. All text German.

/clear when done
```

### Phase 5: Testing (1.5h)
```
Use the tester sub-agent.

Test checklist:
- Unit tests for assignment_engine (0 students, overbooking, requirements)
- Integration: data layer ↔ logic ↔ GUI
- E2E: Create floorplan → Add students → Assign week → PDF export → Save/Load
- Multi-user: Two instances, lock behavior
- Edge cases: corrupt JSON, missing image, stale lock

Output: TEST_REPORT.md, BUGS.md

Fix critical bugs before proceeding.

/clear when done
```

### Phase 6: Deployment (30 min)
```
Use the deployer sub-agent.

Create:
- build.py using PyInstaller (--onefile --windowed)
- Deploy folder structure:
  deploy/SitzplanManager/
  ├── SitzplanManager.exe
  ├── assets/grundriss.png
  ├── data.json (empty initial)
  ├── backups/
  └── ANLEITUNG.txt (German user guide)

Test .exe on Windows.

Done!
```

## Data Structures (Quick Ref)

**data.json:**
```json
{
  "floorplan": {
    "rooms": [{"id", "name", "x", "y", "width", "height", "color"}],
    "seats": [{"id", "roomId", "number", "x", "y", "properties": {}}]
  },
  "students": [{"id", "name", "weekly_pattern": {"monday": bool}, "valid_from", "valid_until", "requirements": []}],
  "assignments": {
    "2025-W43": {
      "monday": [{"studentId", "seatId"}]
    }
  }
}
```

**data.lock:**
```json
{
  "locked": true,
  "user": "admin@PC-01",
  "timestamp": "2025-10-30T14:30:00",
  "pid": 12345
}
```

## Assignment Algorithm (Core Logic)

```python
for day in week:
    students = get_students_for_day(day)
    available_seats = get_free_seats(day)
    
    # Sort: previous seat holders first, then alphabetical
    students.sort(key=lambda s: (not has_previous_seat(s), s.name))
    
    for student in students:
        seat = find_seat(student, available_seats):
            # Try: 1) previous seat, 2) requirements match, 3) any free
        if seat:
            assign(student, seat, day)
        else:
            conflicts.append(student)
```

## Progress Tracking

Create PROGRESS.md:
```markdown
- [x] Phase 1: Architecture
- [ ] Phase 2: Data Layer
- [ ] Phase 3: Business Logic  
- [ ] Phase 4: GUI
- [ ] Phase 5: Testing
- [ ] Phase 6: Deployment
```

Update after each phase. Use `/clear` between phases.

## Key Success Factors

1. **Use `/clear` after each phase** - saves tokens
2. **Let sub-agents work** - don't debug in main context
3. **Haiku for simple** (data, tests, build) - **Sonnet for complex** (architecture, algorithms, GUI)
4. **Test incrementally** - after each layer
5. **Checkpoints** - save .tar.gz after each phase

## Troubleshooting

- **Sub-agent doesn't find files?** → Explicit paths in prompt
- **Context full?** → `/clear` and resume with checklist
- **Code doesn't work?** → Tester agent with failing test, then fix
- **Merge conflicts?** → Avoid parallel work on same files

## Estimated Metrics

- Time: 8-10 hours
- Tokens: ~55k (with Haiku/Sonnet mix)
- Cost: $6-8
- Files: ~20 Python files + assets

---

## Start Command

**Schritt 1: Agents erstellen (einmalig, 5 Min)**
```
[Option A Prompt von oben verwenden, Claude erstellt die Agent-Dateien]

# Oder Option B: Manuell Dateien anlegen in .claude/agents/

# Dann verifizieren:
/agent list
```

**Schritt 2: Projekt starten**
```
Build Sitzplatz-Manager Desktop App using multi-agent architecture.

Project spec: Python Tkinter app for student seat management.
- Visual floorplan (grundriss.png background)
- 6 students, weekly patterns
- Automatic assignment + manual override
- File locking for multi-user
- Undo/Redo, PDF export
- German UI, Dittmann colors (#1e3a5f, #e31e24, #a8c5dd)

Start with Phase 1: Use architect sub-agent to design the system.
Follow phases 1-6 from this execution guide.
Use /clear between phases to save tokens.

Ready? Let's begin with architecture!
```

---

**Token-optimiert. Direkt verwendbar. Viel Erfolg! 🚀**
