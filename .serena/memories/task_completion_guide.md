# Task Completion Guide - Sitzplatz-Manager

## After Completing Implementation Tasks

### 1. Testing
```bash
# Run all unit tests
python3 -m pytest tests/ -v

# Verify all tests pass with 100% pass rate
# - Phase 2 tests: 63 tests
# - Phase 3 tests: 56 tests
# - Phase 4+ tests: varies by phase
```

### 2. Code Quality Checks
- ✓ All functions have type hints
- ✓ All public methods have docstrings
- ✓ Follow snake_case for functions/variables
- ✓ Follow PascalCase for classes
- ✓ All UI text is German (from config.py)

### 3. Integration Testing
- ✓ Verify new component integrates with data layer
- ✓ Verify new component integrates with logic layer
- ✓ Test with real data from data.json
- ✓ Verify undo/redo functionality works

### 4. Git Commit
```bash
# Stage all changes
git add .

# Create meaningful commit message
git commit -m "Phase X: [Brief description of what was implemented]"

# Example:
# git commit -m "Phase 4: Implement MainWindow with menu and toolbar"
```

### 5. Documentation Updates
- [ ] Update PROGRESS.md with completion status
- [ ] Create PHASE4_SUMMARY.md if phase is complete
- [ ] Update ARCHITECTURE.md if design changes
- [ ] Update README.md if user-facing changes

### 6. Verification Checklist
Before marking task complete:
- [ ] Code compiles/runs without errors
- [ ] All unit tests pass (100%)
- [ ] Type hints on all functions
- [ ] Docstrings on public methods
- [ ] German text in UI (from config.py)
- [ ] Follows coding conventions
- [ ] Integrates with existing layers
- [ ] Git commit created

## Phase-Specific Completion

### Phase 4 (GUI Implementation)
Additional checks:
- [ ] MainWindow runs without errors
- [ ] All tabs load and display
- [ ] Dialogs appear correctly
- [ ] User can interact with floorplan
- [ ] Student CRUD operations work
- [ ] Auto-assignment functionality works
- [ ] Menus and buttons are functional
- [ ] Status bar updates correctly

### Test Suite After Phase 4
Expected: All 119 previous tests + new GUI integration tests
- Phase 2: 63 tests ✓
- Phase 3: 56 tests ✓
- Phase 4: ~20-30 GUI tests (estimated)
- **Total:** ~140-150 tests, 100% passing

## Dependencies to Install
As needed:
```bash
pip install tkinter  # Usually built-in
pip install pillow   # Image processing (if not installed)
pip install reportlab  # PDF generation (optional)
pip install pytest   # Testing (if not installed)
```

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Import errors | Check __init__.py exports |
| Type hint errors | Use full import paths for types |
| German text not displaying | Ensure UTF-8 encoding on file |
| Tkinter not found | Python needs to include Tkinter |
| Tests fail | Run one test at a time to isolate issue |

## Milestone Dates
- Phase 1: Architecture ✓ (2025-10-31)
- Phase 2: Data Layer ✓ (2025-10-31)
- Phase 3: Business Logic ✓ (2025-10-31)
- Phase 4: GUI Implementation (IN PROGRESS)
- Phase 5: Testing & QA (Next)
- Phase 6: Deployment (Final)
