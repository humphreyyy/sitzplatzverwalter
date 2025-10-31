"""Students tab for managing student records and preferences.

Provides CRUD operations for student data including attendance patterns and seating requirements.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import logging
from typing import Optional, Dict, Any, List

from config import UI_TEXTS, COLOR_PRIMARY, COLOR_ACCENT, COLOR_LIGHT, WEEKDAYS
from data.data_manager import DataManager
from data.undo_manager import UndoManager

logger = logging.getLogger(__name__)


class StudentsTab:
    """Tab for managing student records and preferences."""

    def __init__(
        self,
        parent: tk.Frame,
        data_manager: DataManager,
        undo_manager: UndoManager,
        main_window: Any,
        current_data: Dict[str, Any]
    ) -> None:
        """Initialize the StudentsTab.

        Args:
            parent: Parent frame
            data_manager: Data manager instance
            undo_manager: Undo manager instance
            main_window: Reference to main window for callbacks
            current_data: Current application data dictionary
        """
        self.parent = parent
        self.data_manager = data_manager
        self.undo_manager = undo_manager
        self.main_window = main_window
        self.current_data = current_data

        # UI components
        self.tree_view: Optional[ttk.Treeview] = None
        self.search_var = tk.StringVar()

        # Create GUI
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the tab widgets."""
        # Toolbar frame
        toolbar = tk.Frame(self.parent, bg=COLOR_PRIMARY, height=40)
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

        add_btn = tk.Button(
            toolbar, text=UI_TEXTS["add_student"],
            command=self._add_student, **button_style
        )
        add_btn.pack(side=tk.LEFT, padx=5, pady=5)

        delete_btn = tk.Button(
            toolbar, text=UI_TEXTS["delete"],
            command=self._delete_student, **button_style
        )
        delete_btn.pack(side=tk.LEFT, padx=5, pady=5)

        tk.Label(toolbar, text="Search:", bg=COLOR_PRIMARY, fg="white").pack(
            side=tk.LEFT, padx=10, pady=5
        )

        search_entry = tk.Entry(toolbar, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5, pady=5)
        search_entry.bind("<KeyRelease>", lambda e: self._filter_students())

        # Table frame
        table_frame = tk.Frame(self.parent, bg=COLOR_LIGHT)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create treeview
        columns = ("ID", "Name", "Valid From", "Valid Until", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
        self.tree_view = ttk.Treeview(table_frame, columns=columns, height=25)
        self.tree_view.column("#0", width=0, stretch=tk.NO)

        # Define column headings
        self.tree_view.heading("#0", text="", anchor=tk.W)
        for i, col in enumerate(columns):
            self.tree_view.column(col, anchor=tk.CENTER, width=60)
            self.tree_view.heading(col, text=col, anchor=tk.CENTER)

        # Add scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_view.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree_view.xview)
        self.tree_view.configure(yscroll=vsb.set, xscroll=hsb.set)

        # Grid layout
        self.tree_view.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Bind double-click to edit
        self.tree_view.bind("<Double-1>", self._on_double_click)

        self.refresh()

    def _add_student(self) -> None:
        """Add a new student."""
        dialog = StudentDialog(self.parent, "Add Student")
        self.parent.wait_window(dialog.dialog)

        if dialog.result:
            try:
                data = self.current_data
                students = data.get("students", [])

                new_student = {
                    "id": f"student_{len(students) + 1}",
                    "name": dialog.result["name"],
                    "valid_from": dialog.result.get("valid_from", "2025-01-01"),
                    "valid_until": dialog.result.get("valid_until", "2025-12-31"),
                    "weekly_pattern": dialog.result.get("weekly_pattern", {
                        "monday": True, "tuesday": True, "wednesday": True,
                        "thursday": True, "friday": True, "saturday": False, "sunday": False
                    }),
                    "requirements": dialog.result.get("requirements", {})
                }

                students.append(new_student)
                data["students"] = students

                # Save state for undo
                self.undo_manager.push_state(data)
                self.data_manager.save_data(self.current_data)

                self.refresh()
                self.main_window._update_status(f"Student added: {new_student['name']}")
                logger.info(f"Student added: {new_student['name']}")

            except Exception as e:
                logger.error(f"Error adding student: {e}")
                messagebox.showerror("Error", f"Failed to add student: {e}")

    def _delete_student(self) -> None:
        """Delete the selected student."""
        selection = self.tree_view.selection()
        if not selection:
            messagebox.showwarning("Warning", "Select a student to delete")
            return

        item = selection[0]
        student_name = self.tree_view.item(item)["values"][1] if self.tree_view.item(item)["values"] else "Unknown"

        if messagebox.askyesno("Delete", f"Delete student '{student_name}'?"):
            try:
                data = self.current_data
                student_id = self.tree_view.item(item)["values"][0]
                students = data.get("students", [])
                students[:] = [s for s in students if s["id"] != student_id]
                data["students"] = students

                # Save state for undo
                self.undo_manager.push_state(data)
                self.data_manager.save_data(self.current_data)

                self.refresh()
                self.main_window._update_status(f"Student deleted: {student_name}")
                logger.info(f"Student deleted: {student_name}")

            except Exception as e:
                logger.error(f"Error deleting student: {e}")
                messagebox.showerror("Error", f"Failed to delete student: {e}")

    def _on_double_click(self, event: tk.Event) -> None:
        """Handle double-click to edit student.

        Args:
            event: Click event
        """
        item = self.tree_view.selection()[0]
        values = self.tree_view.item(item)["values"]
        if values:
            student_id = values[0]
            self._edit_student(student_id)

    def _edit_student(self, student_id: str) -> None:
        """Edit a student's information.

        Args:
            student_id: ID of student to edit
        """
        try:
            data = self.current_data
            students = data.get("students", [])
            student = next((s for s in students if s["id"] == student_id), None)

            if not student:
                messagebox.showerror("Error", "Student not found")
                return

            dialog = StudentDialog(self.parent, "Edit Student", student)
            self.parent.wait_window(dialog.dialog)

            if dialog.result:
                student.update(dialog.result)

                # Save state for undo
                self.undo_manager.push_state(data)
                self.data_manager.save_data(self.current_data)

                self.refresh()
                self.main_window._update_status(f"Student updated: {student['name']}")
                logger.info(f"Student updated: {student['name']}")

        except Exception as e:
            logger.error(f"Error editing student: {e}")
            messagebox.showerror("Error", f"Failed to edit student: {e}")

    def _filter_students(self) -> None:
        """Filter students by search text."""
        search_text = self.search_var.get().lower()

        # Clear existing items
        for item in self.tree_view.get_children():
            self.tree_view.delete(item)

        try:
            data = self.current_data
            students = data.get("students", [])

            # Filter and display students
            for student in students:
                if search_text in student.get("name", "").lower():
                    pattern = student.get("weekly_pattern", {})
                    values = (
                        student["id"],
                        student.get("name", ""),
                        student.get("valid_from", ""),
                        student.get("valid_until", ""),
                        "✓" if pattern.get("monday") else "✗",
                        "✓" if pattern.get("tuesday") else "✗",
                        "✓" if pattern.get("wednesday") else "✗",
                        "✓" if pattern.get("thursday") else "✗",
                        "✓" if pattern.get("friday") else "✗",
                        "✓" if pattern.get("saturday") else "✗",
                        "✓" if pattern.get("sunday") else "✗",
                    )
                    self.tree_view.insert("", "end", values=values)

        except Exception as e:
            logger.error(f"Error filtering students: {e}")

    def refresh(self) -> None:
        """Refresh the student list."""
        self._filter_students()


class StudentDialog:
    """Dialog for editing student information."""

    def __init__(self, parent: tk.Widget, title: str, student: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the student dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            student: Existing student data (if editing)
        """
        self.result: Optional[Dict[str, Any]] = None
        self.student = student or {}

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x500")

        # Name
        tk.Label(self.dialog, text=UI_TEXTS["name"]).pack(padx=10, pady=5)
        self.name_var = tk.StringVar(value=self.student.get("name", ""))
        tk.Entry(self.dialog, textvariable=self.name_var, width=40).pack(padx=10, pady=5)

        # Valid from
        tk.Label(self.dialog, text=UI_TEXTS["valid_from"]).pack(padx=10, pady=5)
        self.valid_from_var = tk.StringVar(value=self.student.get("valid_from", "2025-01-01"))
        tk.Entry(self.dialog, textvariable=self.valid_from_var, width=40).pack(padx=10, pady=5)

        # Valid until
        tk.Label(self.dialog, text=UI_TEXTS["valid_until"]).pack(padx=10, pady=5)
        self.valid_until_var = tk.StringVar(value=self.student.get("valid_until", "2025-12-31"))
        tk.Entry(self.dialog, textvariable=self.valid_until_var, width=40).pack(padx=10, pady=5)

        # Weekly pattern
        tk.Label(self.dialog, text=UI_TEXTS["weekly_pattern"]).pack(padx=10, pady=5)
        pattern_frame = tk.Frame(self.dialog)
        pattern_frame.pack(padx=10, pady=5, fill=tk.X)

        pattern = self.student.get("weekly_pattern", {
            "monday": True, "tuesday": True, "wednesday": True,
            "thursday": True, "friday": True, "saturday": False, "sunday": False
        })

        self.pattern_vars: Dict[str, tk.BooleanVar] = {}
        for day, display_name in WEEKDAYS.items():
            var = tk.BooleanVar(value=pattern.get(day, True))
            self.pattern_vars[day] = var
            tk.Checkbutton(pattern_frame, text=display_name, variable=var).pack(anchor=tk.W)

        # Buttons with proper styling for macOS compatibility
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)

        dialog_button_style = {
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

        tk.Button(button_frame, text=UI_TEXTS["save_button"], command=self._save, **dialog_button_style).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text=UI_TEXTS["cancel"], command=self.dialog.destroy, **dialog_button_style).pack(side=tk.LEFT, padx=5)

    def _save(self) -> None:
        """Save student information."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a name")
            return

        self.result = {
            "name": name,
            "valid_from": self.valid_from_var.get(),
            "valid_until": self.valid_until_var.get(),
            "weekly_pattern": {day: var.get() for day, var in self.pattern_vars.items()},
            "requirements": self.student.get("requirements", {})
        }

        self.dialog.destroy()
