# Development Commands - Sitzplatz-Manager

## Testing
```bash
# Run all unit tests
python3 -m pytest tests/ -v
python3 -m unittest discover tests/ -v

# Run specific test file
python3 -m pytest tests/test_assignment_engine.py -v

# Run with coverage
python3 -m pytest tests/ --cov=logic --cov=data --cov=models
```

## Running the Application
```bash
# When GUI is complete (Phase 4)
python3 main.py

# Current status (before GUI implementation)
python3 main.py  # Shows status message
```

## Code Quality
```bash
# Format code (if using black)
python3 -m black . --line-length=100

# Lint code (if using pylint)
python3 -m pylint logic/ data/ models/ gui/

# Type checking (if using mypy)
python3 -m mypy logic/ data/ models/ gui/ --strict
```

## Common Workflows

### When Implementing Phase 4 GUI
1. Create new GUI module file
2. Implement component class with type hints
3. Add docstrings to public methods
4. Test integration with logic layer
5. Run full test suite: `python3 -m pytest tests/ -v`

### When Adding New Models
1. Create dataclass in models/
2. Add to models/__init__.py exports
3. Create unit tests in tests/test_models.py
4. Ensure type hints on all fields

### When Adding Business Logic
1. Create module in logic/
2. Import models and validators
3. Implement with type hints
4. Add docstrings to public methods
5. Create comprehensive unit tests
6. Run tests before committing

## Git Commands
```bash
# View project status
git status

# Stage changes
git add .

# Commit with message
git commit -m "Phase 4: Implement MainWindow"

# View recent commits
git log --oneline -10
```

## System Information
- **Platform:** Darwin (macOS)
- **Python:** 3.9+
- **Test Framework:** unittest, pytest
- **Package Manager:** pip
