"""Planning tab for weekly seating assignments.

Provides interface for automatic and manual seat assignments with conflict detection and statistics.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import logging
from typing import Optional, Dict, Any, List
import datetime

from config import UI_TEXTS, COLOR_PRIMARY, COLOR_ACCENT, COLOR_LIGHT, WEEKDAYS
from data.data_manager import DataManager
from data.undo_manager import UndoManager
from logic.assignment_engine import AssignmentEngine
from logic.validator import Validator

logger = logging.getLogger(__name__)


class PlanningTab:
    """Tab for managing weekly seating assignments."""

    def __init__(
        self,
        parent: tk.Frame,
        data_manager: DataManager,
        undo_manager: UndoManager,
        main_window: Any
    ) -> None:
        """Initialize the PlanningTab.

        Args:
            parent: Parent frame
            data_manager: Data manager instance
            undo_manager: Undo manager instance
            main_window: Reference to main window for callbacks
        """
        self.parent = parent
        self.data_manager = data_manager
        self.undo_manager = undo_manager
        self.main_window = main_window

        # UI components
        self.week_var = tk.StringVar()
        self.day_var = tk.StringVar()
        self.tree_views: Dict[str, ttk.Treeview] = {}
        self.statistics_label: Optional[tk.Label] = None

        # Create GUI
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the tab widgets."""
        # Control frame
        control_frame = tk.Frame(self.parent, bg=COLOR_PRIMARY, height=50)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)

        # Week selector
        tk.Label(control_frame, text="Week:", bg=COLOR_PRIMARY, fg="white").pack(side=tk.LEFT, padx=10, pady=5)
        self.week_var.set(self._get_current_week())
        week_entry = tk.Entry(control_frame, textvariable=self.week_var, width=10)
        week_entry.pack(side=tk.LEFT, padx=5, pady=5)

        # Control buttons with proper styling for macOS compatibility
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

        # Auto-assign button
        auto_assign_btn = tk.Button(
            control_frame, text=UI_TEXTS["auto_assign"],
            command=self._auto_assign, **button_style
        )
        auto_assign_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Clear assignments button
        clear_btn = tk.Button(
            control_frame, text="Clear", command=self._clear_assignments, **button_style
        )
        clear_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Main content frame with tabs for each day
        notebook = ttk.Notebook(self.parent)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a tab for each day
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            frame = tk.Frame(notebook)
            notebook.add(frame, text=WEEKDAYS[day])

            # Create treeview for day
            columns = ("Seat#", "Student Name", "Room")
            tree = ttk.Treeview(frame, columns=columns, height=20)
            tree.column("#0", width=0, stretch=tk.NO)

            tree.heading("#0", text="", anchor=tk.W)
            for col in columns:
                tree.column(col, anchor=tk.CENTER, width=100)
                tree.heading(col, text=col, anchor=tk.CENTER)

            # Scrollbars
            vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            tree.configure(yscroll=vsb.set, xscroll=hsb.set)

            tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)

            self.tree_views[day] = tree

        # Statistics frame
        stats_frame = tk.Frame(self.parent, bg=COLOR_LIGHT, height=50)
        stats_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.statistics_label = tk.Label(stats_frame, text="Ready", bg=COLOR_LIGHT, fg=COLOR_PRIMARY)
        self.statistics_label.pack(side=tk.LEFT, padx=10, pady=5)

        self.refresh()

    def _auto_assign(self) -> None:
        """Perform automatic seat assignment for the selected week."""
        try:
            week = self.week_var.get().strip()
            if not week:
                messagebox.showerror("Error", "Please enter a week (e.g., 2025-W43)")
                return

            data = self.data_manager.get_data()

            # Get students and seats
            students = data.get("students", [])
            seats = data.get("floorplan", {}).get("seats", [])

            if not students:
                messagebox.showwarning("Warning", "No students found")
                return

            if not seats:
                messagebox.showwarning("Warning", "No seats found")
                return

            # Get previous week assignments (if any)
            previous_week = self._get_previous_week(week)
            previous_assignments = data.get("assignments", {}).get(previous_week, {})

            # Run assignment engine
            assignments, conflicts = AssignmentEngine.assign_week(
                students=students,
                seats=seats,
                week=week,
                previous_assignments=previous_assignments
            )

            # Get statistics
            statistics = AssignmentEngine.get_assignment_statistics(
                assignments=assignments,
                conflicts=conflicts,
                students=students,
                seats=seats
            )

            # Save assignments
            if "assignments" not in data:
                data["assignments"] = {}
            data["assignments"][week] = assignments

            # Save state for undo
            self.undo_manager.push_state(data)
            self.data_manager.save_data()

            # Refresh display
            self.refresh()

            # Show statistics
            stats_msg = (
                f"Assignments: {statistics.get('total_assignments', 0)} | "
                f"Conflicts: {statistics.get('conflicts', 0)} | "
                f"Occupancy: {statistics.get('occupancy_rate', 0):.1%}"
            )
            messagebox.showinfo("Assignment Complete", stats_msg)
            self.main_window._update_status(f"Auto-assignment complete for week {week}")
            logger.info(f"Auto-assignment completed for week {week}")

        except Exception as e:
            logger.error(f"Error in auto-assignment: {e}")
            messagebox.showerror("Error", f"Auto-assignment failed: {e}")

    def _clear_assignments(self) -> None:
        """Clear all assignments for the selected week."""
        try:
            week = self.week_var.get().strip()
            if not week:
                messagebox.showerror("Error", "Please enter a week")
                return

            if messagebox.askyesno("Confirm", f"Clear all assignments for week {week}?"):
                data = self.data_manager.get_data()
                if "assignments" in data and week in data["assignments"]:
                    del data["assignments"][week]

                # Save state for undo
                self.undo_manager.push_state(data)
                self.data_manager.save_data()

                self.refresh()
                self.main_window._update_status(f"Assignments cleared for week {week}")
                logger.info(f"Assignments cleared for week {week}")

        except Exception as e:
            logger.error(f"Error clearing assignments: {e}")
            messagebox.showerror("Error", f"Failed to clear assignments: {e}")

    def refresh(self) -> None:
        """Refresh the assignment display for the selected week."""
        try:
            week = self.week_var.get().strip()
            data = self.data_manager.get_data()

            # Get students and seats for lookup
            students = {s["id"]: s for s in data.get("students", [])}
            seats = {s["id"]: s for s in data.get("floorplan", {}).get("seats", [])}
            rooms = {r["id"]: r for r in data.get("floorplan", {}).get("rooms", [])}

            # Get assignments for the week
            assignments = data.get("assignments", {}).get(week, {})

            # Clear and populate treeviews
            for day, tree in self.tree_views.items():
                # Clear existing items
                for item in tree.get_children():
                    tree.delete(item)

                # Get assignments for this day
                day_assignments = assignments.get(day, [])

                # Display assignments
                for assignment in day_assignments:
                    student_id = assignment.get("student_id")
                    seat_id = assignment.get("seat_id")

                    student_name = students.get(student_id, {}).get("name", "Unknown")
                    seat_number = seats.get(seat_id, {}).get("number", "?")
                    room_id = seats.get(seat_id, {}).get("room_id", "")
                    room_name = rooms.get(room_id, {}).get("name", "")

                    values = (seat_number, student_name, room_name)
                    tree.insert("", "end", values=values)

            # Update statistics
            if assignments:
                total_assignments = sum(len(day_asn) for day_asn in assignments.values())
                if self.statistics_label:
                    self.statistics_label.config(
                        text=f"Week {week}: {total_assignments} assignments, "
                             f"{len(data.get('students', []))} students, "
                             f"{len(data.get('floorplan', {}).get('seats', []))} seats"
                    )
            else:
                if self.statistics_label:
                    self.statistics_label.config(text=f"Week {week}: No assignments")

        except Exception as e:
            logger.error(f"Error refreshing planning tab: {e}")

    @staticmethod
    def _get_current_week() -> str:
        """Get the current week in ISO format.

        Returns:
            Week string (e.g., "2025-W43")
        """
        return datetime.datetime.now().strftime("%Y-W%V")

    @staticmethod
    def _get_previous_week(week: str) -> str:
        """Get the previous week.

        Args:
            week: Week string (e.g., "2025-W43")

        Returns:
            Previous week string
        """
        try:
            parts = week.split("-W")
            year = int(parts[0])
            week_num = int(parts[1])

            if week_num == 1:
                return f"{year - 1}-W52"
            else:
                return f"{year}-W{week_num - 1:02d}"
        except Exception:
            return week  # Fallback
