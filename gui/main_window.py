"""Main application window for Sitzplatz-Manager.

Implements the primary GUI with menu bar, toolbar, status bar, and tabbed interface.
Coordinates between data layer (DataManager, LockManager, UndoManager) and GUI components.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from config import (
    UI_TEXTS, COLOR_PRIMARY, COLOR_ACCENT, COLOR_LIGHT,
    DATA_FILE, BACKUP_DIR, AUTO_BACKUP_INTERVAL
)
from data.data_manager import DataManager
from data.lock_manager import LockManager
from data.undo_manager import UndoManager
from logic.validator import Validator
from logic.assignment_engine import AssignmentEngine
from logic.pdf_exporter import PdfExporter
from gui.floorplan_tab import FloorplanTab
from gui.students_tab import StudentsTab
from gui.planning_tab import PlanningTab

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window with menu bar, toolbar, status bar, and tabbed interface."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the main application window.

        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title(UI_TEXTS["app_title"])
        self.root.geometry("1400x900")

        # Set Dittmann brand colors
        self.root.configure(bg=COLOR_LIGHT)

        # Initialize data layer
        # Use current working directory for data files (or parent directory if in app bundle)
        data_dir = Path.cwd()
        self.data_manager = DataManager(str(data_dir))
        self.lock_manager = LockManager()
        self.undo_manager = UndoManager()

        # Track file lock status
        self.is_locked = False
        self.lock_user = None

        # --- NEW: Load data into memory ---
        try:
            self.current_data = self.data_manager.load_data()
            logger.info("Initial data loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load initial data: {e}", exc_info=True)
            messagebox.showerror("Fehler beim Laden", f"Konnte data.json nicht laden: {e}\nEine neue Datei wird erstellt.")
            self.current_data = self.data_manager._create_empty_data()

        # Push the initial state to the undo manager
        self.undo_manager.push_state(self.current_data)
        # --- END NEW ---

        # Try to acquire file lock
        self._acquire_lock()

        # Build GUI structure
        self._create_menu_bar()
        self._create_toolbar()
        self._create_tabs()
        self._create_status_bar()

        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Start auto-backup timer
        self._setup_auto_backup()

        logger.info("MainWindow initialized successfully")

    def _acquire_lock(self) -> None:
        """Acquire file lock and switch to read-only mode if locked by another user."""
        try:
            lock_info = self.lock_manager.acquire_lock("default_user@sitzplatz")
            if lock_info is None:
                self.is_locked = False
                logger.info("File lock acquired")
            else:
                self.is_locked = True
                self.lock_user = lock_info.get("user", "Unknown")
                logger.warning(f"File locked by {self.lock_user}. Read-only mode enabled.")
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            self.is_locked = False

    def _create_menu_bar(self) -> None:
        """Create and configure the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=UI_TEXTS["file_menu"], menu=file_menu)
        file_menu.add_command(label=UI_TEXTS["new"], command=self._new_file)
        file_menu.add_command(label=UI_TEXTS["open"], command=self._open_file)
        file_menu.add_command(label=UI_TEXTS["save"], command=self._save_file)
        file_menu.add_command(label=UI_TEXTS["save_as"], command=self._save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label=UI_TEXTS["export_pdf"], command=self._export_pdf)
        file_menu.add_separator()
        file_menu.add_command(label=UI_TEXTS["exit"], command=self._on_window_close)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=UI_TEXTS["edit_menu"], menu=edit_menu)
        edit_menu.add_command(label=UI_TEXTS["undo"], command=self._undo)
        edit_menu.add_command(label=UI_TEXTS["redo"], command=self._redo)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=UI_TEXTS["help_menu"], menu=help_menu)
        help_menu.add_command(label=UI_TEXTS["about"], command=self._show_about)

    def _create_toolbar(self) -> None:
        """Create and configure the toolbar with buttons."""
        toolbar = tk.Frame(self.root, bg=COLOR_PRIMARY, height=40)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)

        # Toolbar buttons with proper styling for macOS compatibility
        button_style = {
            "bg": COLOR_ACCENT,
            "fg": "white",
            "font": ("Helvetica", 12, "bold"),
            "relief": tk.RAISED,
            "bd": 2,
            "activebackground": "#b5181b",
            "activeforeground": "white",
            "padx": 10,
            "pady": 5
        }

        save_btn = tk.Button(
            toolbar, text=UI_TEXTS["save_button"],
            command=self._save_file, **button_style
        )
        save_btn.pack(side=tk.LEFT, padx=5, pady=5)

        undo_btn = tk.Button(
            toolbar, text=UI_TEXTS["undo"],
            command=self._undo, **button_style
        )
        undo_btn.pack(side=tk.LEFT, padx=5, pady=5)

        redo_btn = tk.Button(
            toolbar, text=UI_TEXTS["redo"],
            command=self._redo, **button_style
        )
        redo_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def _create_tabs(self) -> None:
        """Create the tabbed interface with three main tabs."""
        from tkinter import ttk

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # FloorplanTab
        self.floorplan_frame = tk.Frame(self.notebook)
        self.notebook.add(self.floorplan_frame, text=UI_TEXTS["floorplan_tab"])
        self.floorplan_tab = FloorplanTab(
            self.floorplan_frame, self.data_manager, self.undo_manager, self, self.current_data
        )

        # StudentsTab
        self.students_frame = tk.Frame(self.notebook)
        self.notebook.add(self.students_frame, text=UI_TEXTS["students_tab"])
        self.students_tab = StudentsTab(
            self.students_frame, self.data_manager, self.undo_manager, self, self.current_data
        )

        # PlanningTab
        self.planning_frame = tk.Frame(self.notebook)
        self.notebook.add(self.planning_frame, text=UI_TEXTS["planning_tab"])
        self.planning_tab = PlanningTab(
            self.planning_frame, self.data_manager, self.undo_manager, self, self.current_data
        )

    def _create_status_bar(self) -> None:
        """Create status bar at the bottom of the window."""
        self.status_frame = tk.Frame(self.root, bg=COLOR_LIGHT, height=25)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)

        # Status text
        self.status_label = tk.Label(
            self.status_frame, text="Ready", bg=COLOR_LIGHT, fg=COLOR_PRIMARY
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Lock status
        self.lock_status_label = tk.Label(
            self.status_frame, text="", bg=COLOR_LIGHT, fg=COLOR_ACCENT
        )
        self.lock_status_label.pack(side=tk.RIGHT, padx=10, pady=5)

        self._update_lock_status()

    def _update_lock_status(self) -> None:
        """Update the lock status indicator in the status bar."""
        if self.is_locked:
            self.lock_status_label.config(text=f"⚠ {UI_TEXTS['file_locked']} ({self.lock_user})")
        else:
            self.lock_status_label.config(text="")

    def _update_status(self, message: str) -> None:
        """Update the status message in the status bar.

        Args:
            message: The status message to display
        """
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def _new_file(self) -> None:
        """Create a new file."""
        if self.is_locked:
            messagebox.showerror("Error", UI_TEXTS["file_locked"])
            return

        if messagebox.askyesno("New File", "Create a new file? Unsaved changes will be lost."):
            try:
                self.current_data = self.data_manager._create_empty_data()
                self.undo_manager.clear()
                self.undo_manager.push_state(self.current_data)
                self._refresh_all_tabs()
                self._update_status("New file created")
                logger.info("New file created")
            except Exception as e:
                logger.error(f"Error creating new file: {e}")
                messagebox.showerror("Error", f"Failed to create new file: {e}")

    def _open_file(self) -> None:
        """Open an existing file."""
        if self.is_locked:
            messagebox.showerror("Error", UI_TEXTS["file_locked"])
            return

        file_path = filedialog.askopenfilename(
            initialdir=".",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.current_data = self.data_manager.load_data(file_path)
                self.undo_manager.clear()
                self.undo_manager.push_state(self.current_data)
                self._refresh_all_tabs()
                self._update_status(f"Opened: {Path(file_path).name}")
                logger.info(f"File opened: {file_path}")
            except Exception as e:
                logger.error(f"Error opening file: {e}")
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def _save_file(self) -> None:
        """Save the current file."""
        if self.is_locked:
            messagebox.showerror("Error", UI_TEXTS["file_locked"])
            return

        try:
            self.data_manager.save_data(self.current_data)
            self._update_status(f"{UI_TEXTS['last_saved']}: {self._get_timestamp()}")
            logger.info("File saved")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def _save_as_file(self) -> None:
        """Save file with a new name."""
        if self.is_locked:
            messagebox.showerror("Error", UI_TEXTS["file_locked"])
            return

        file_path = filedialog.asksaveasfilename(
            initialdir=".",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.data_manager.save_data(self.current_data, file_path)
                self._update_status(f"Saved as: {Path(file_path).name}")
                logger.info(f"File saved as: {file_path}")
            except Exception as e:
                logger.error(f"Error saving file: {e}")
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def _export_pdf(self) -> None:
        """Export the current week's seating plan as PDF."""
        try:
            data = self.data_manager.get_data()
            if not data:
                messagebox.showwarning("Warning", "No data to export")
                return

            # Get current week (placeholder - should be selectable)
            import datetime
            current_week = datetime.datetime.now().strftime("%Y-W%V")

            # Get assignments for the week
            assignments = data.get("assignments", {}).get(current_week, {})
            if not assignments:
                messagebox.showwarning("Warning", f"No assignments for week {current_week}")
                return

            # Prepare data for PDF export
            students_list = data.get("students", [])
            seats_list = data.get("floorplan", {}).get("seats", [])

            # Export PDF
            if not PdfExporter.is_available():
                messagebox.showerror("Error", "ReportLab is not installed. Install with: pip install reportlab")
                return

            pdf_bytes = PdfExporter.export_week_to_pdf(
                week=current_week,
                assignments=assignments,
                students=students_list,
                seats=seats_list,
                statistics={}  # Could calculate statistics here
            )

            # Ask user where to save
            file_path = filedialog.asksaveasfilename(
                initialfile=f"sitzplan_{current_week}.pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if file_path:
                PdfExporter.save_pdf_to_file(pdf_bytes, file_path)
                self._update_status(f"PDF exported: {Path(file_path).name}")
                messagebox.showinfo("Success", f"PDF exported to {Path(file_path).name}")
                logger.info(f"PDF exported: {file_path}")

        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            messagebox.showerror("Error", f"Failed to export PDF: {e}")

    def _undo(self) -> None:
        """Undo the last change."""
        if self.is_locked:
            messagebox.showerror("Error", UI_TEXTS["file_locked"])
            return

        try:
            new_state = self.undo_manager.undo()
            if new_state:
                self.current_data = new_state
                self._refresh_all_tabs()
                self._update_status("Change undone")
                logger.info("Undo performed")
            else:
                self._update_status("Nothing to undo")
        except Exception as e:
            logger.error(f"Error undoing: {e}")
            self._update_status(f"Nothing to undo: {e}")

    def _redo(self) -> None:
        """Redo the last undone change."""
        if self.is_locked:
            messagebox.showerror("Error", UI_TEXTS["file_locked"])
            return

        try:
            new_state = self.undo_manager.redo()
            if new_state:
                self.current_data = new_state
                self._refresh_all_tabs()
                self._update_status("Change redone")
                logger.info("Redo performed")
            else:
                self._update_status("Nothing to redo")
        except Exception as e:
            logger.error(f"Error redoing: {e}")
            self._update_status(f"Nothing to redo: {e}")

    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            UI_TEXTS["about"],
            "Sitzplatz-Manager\n\nVersion 1.0\n\nDesktop application for managing "
            "student seating assignments.\n\nPowered by Tkinter and Python 3.9+"
        )

    def _refresh_all_tabs(self) -> None:
        """Refresh all tabs with current data."""
        if hasattr(self, 'floorplan_tab'):
            self.floorplan_tab.refresh()
        if hasattr(self, 'students_tab'):
            self.students_tab.refresh()
        if hasattr(self, 'planning_tab'):
            self.planning_tab.refresh()

    def _setup_auto_backup(self) -> None:
        """Set up automatic backup timer."""
        # Schedule auto-backup every AUTO_BACKUP_INTERVAL seconds
        self._auto_backup()

    def _auto_backup(self) -> None:
        """Perform automatic backup and reschedule."""
        try:
            self.data_manager.backup_data()
        except Exception as e:
            logger.warning(f"Auto-backup failed: {e}")

        # Reschedule auto-backup
        self.root.after(AUTO_BACKUP_INTERVAL * 1000, self._auto_backup)

    def _on_window_close(self) -> None:
        """Handle window close event."""
        if messagebox.askyesno("Quit", "Are you sure you want to exit?"):
            try:
                # Save unsaved changes
                self._save_file()
            except Exception as e:
                logger.error(f"Error saving on exit: {e}")

            try:
                # Release file lock
                self.lock_manager.release_lock()
            except Exception as e:
                logger.error(f"Error releasing lock: {e}")

            logger.info("Application closed")
            self.root.destroy()

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp formatted for display.

        Returns:
            Formatted timestamp string
        """
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def run_application() -> None:
    """Run the Sitzplatz-Manager application."""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    run_application()
