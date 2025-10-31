"""GUI layer for Sitzplatz-Manager.

Tkinter-based user interface components:
- MainWindow: Main application window
- FloorplanTab: Floorplan editor
- StudentsTab: Student management
- PlanningTab: Weekly planning and assignment
- Dialogs: Modal dialogs for user interactions
"""

from gui.main_window import MainWindow, run_application
from gui.floorplan_tab import FloorplanTab
from gui.students_tab import StudentsTab, StudentDialog
from gui.planning_tab import PlanningTab

__all__ = [
    "MainWindow",
    "run_application",
    "FloorplanTab",
    "StudentsTab",
    "StudentDialog",
    "PlanningTab",
]
