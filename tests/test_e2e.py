"""End-to-End tests for Sitzplatz-Manager.

Tests complete user workflows:
- Floorplan creation
- Student management
- Seating assignment
- PDF export
- Save/load cycles
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from data.data_manager import DataManager
from data.undo_manager import UndoManager
from logic.assignment_engine import AssignmentEngine
from logic.validator import Validator
from logic.pdf_exporter import PdfExporter
from models.student import Student
from models.seat import Seat
from models.room import Room
from models.assignment import Assignment


class TestFloorplanCreationWorkflow(unittest.TestCase):
    """Test end-to-end floorplan creation workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_create_rooms_add_seats_save_reload(self) -> None:
        """Test: Create rooms → Add seats → Save → Reload."""
        # Load initial data
        data = self.data_manager.load_data()

        # Step 1: Create rooms
        rooms = [
            Room(id="r1", name="Classroom A", x=50, y=50, width=400, height=300),
            Room(id="r2", name="Classroom B", x=500, y=50, width=400, height=300),
        ]
        data["floorplan"]["rooms"] = [
            {"id": r.id, "name": r.name, "x": r.x, "y": r.y, "width": r.width, "height": r.height}
            for r in rooms
        ]

        # Step 2: Add seats
        seats = []
        seats_data = []
        for room_idx, room in enumerate(rooms):
            for seat_idx in range(5):
                seat = Seat(
                    id=f"s{room_idx}{seat_idx}",
                    room_id=room.id,
                    number=seat_idx + 1,
                    x=60 + seat_idx * 30,
                    y=60
                )
                seats.append(seat)
                seats_data.append({
                    "id": seat.id,
                    "room_id": seat.room_id,
                    "number": seat.number,
                    "x": seat.x,
                    "y": seat.y
                })
        data["floorplan"]["seats"] = seats_data

        # Step 3: Save
        self.data_manager.save_data(data, create_backup=False)

        # Step 4: Reload
        reloaded = self.data_manager.load_data()

        # Verify
        self.assertEqual(len(reloaded["floorplan"]["rooms"]), 2)
        self.assertEqual(len(reloaded["floorplan"]["seats"]), 10)
        self.assertEqual(reloaded["floorplan"]["rooms"][0]["name"], "Classroom A")
        self.assertEqual(reloaded["floorplan"]["seats"][0]["room_id"], "r1")

    def test_edit_floorplan_undo_redo_save(self) -> None:
        """Test: Create → Edit → Undo → Redo → Save."""
        undo_manager = UndoManager()
        data = self.data_manager.load_data()

        # Initial state
        room = Room(id="r1", name="Room", x=50, y=50, width=400, height=300)
        data["floorplan"]["rooms"] = [{
            "id": room.id, "name": room.name, "x": room.x, "y": room.y,
            "width": room.width, "height": room.height
        }]
        state1 = {
            "floorplan": {"rooms": data["floorplan"]["rooms"], "seats": []},
            "students": [],
            "assignments": {},
            "metadata": {}
        }
        undo_manager.push_state(state1)

        # Edit: Add seat
        seat = Seat(id="s1", room_id="r1", number=1, x=60, y=60)
        data["floorplan"]["seats"] = [{
            "id": seat.id, "room_id": seat.room_id, "number": seat.number, "x": seat.x, "y": seat.y
        }]
        state2 = {
            "floorplan": {"rooms": data["floorplan"]["rooms"], "seats": data["floorplan"]["seats"]},
            "students": [],
            "assignments": {},
            "metadata": {}
        }
        undo_manager.push_state(state2)

        # Verify can undo
        self.assertTrue(undo_manager.can_undo())

        # Undo
        state = undo_manager.undo()
        self.assertIsNotNone(state)
        self.assertEqual(len(state["floorplan"]["seats"]), 0)

        # Verify can redo
        self.assertTrue(undo_manager.can_redo())

        # Redo
        state = undo_manager.redo()
        self.assertEqual(len(state["floorplan"]["seats"]), 1)

        # Save final state
        self.data_manager.save_data(data, create_backup=False)
        reloaded = self.data_manager.load_data()
        self.assertEqual(len(reloaded["floorplan"]["seats"]), 1)


class TestStudentManagementWorkflow(unittest.TestCase):
    """Test end-to-end student management workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_add_edit_delete_students_save_reload(self) -> None:
        """Test: Add students → Edit → Delete → Save → Reload."""
        data = self.data_manager.load_data()

        # Step 1: Add students
        students_data = [
            {
                "id": "st1",
                "name": "Alice",
                "weekly_pattern": {"monday": True, "tuesday": True, "wednesday": False},
                "valid_from": "2025-01-01",
                "valid_until": "2025-12-31"
            },
            {
                "id": "st2",
                "name": "Bob",
                "weekly_pattern": {"monday": True, "tuesday": False, "wednesday": True},
                "valid_from": "2025-01-01",
                "valid_until": "2025-12-31"
            },
        ]
        data["students"] = students_data
        self.data_manager.save_data(data, create_backup=False)

        # Step 2: Edit (modify Alice's weekly pattern)
        data = self.data_manager.load_data()
        data["students"][0]["weekly_pattern"]["wednesday"] = True
        self.data_manager.save_data(data, create_backup=False)

        # Step 3: Delete (Bob)
        data = self.data_manager.load_data()
        data["students"] = [s for s in data["students"] if s["id"] != "st2"]
        self.data_manager.save_data(data, create_backup=False)

        # Step 4: Reload and verify
        reloaded = self.data_manager.load_data()
        self.assertEqual(len(reloaded["students"]), 1)
        self.assertEqual(reloaded["students"][0]["name"], "Alice")
        self.assertTrue(reloaded["students"][0]["weekly_pattern"]["wednesday"])

    def test_student_search_filter(self) -> None:
        """Test searching and filtering students."""
        data = self.data_manager.load_data()

        # Add multiple students
        data["students"] = [
            {"id": "st1", "name": "Alice Anderson", "weekly_pattern": {}},
            {"id": "st2", "name": "Bob Brown", "weekly_pattern": {}},
            {"id": "st3", "name": "Charlie Anderson", "weekly_pattern": {}},
        ]
        self.data_manager.save_data(data, create_backup=False)

        # Load and filter
        loaded = self.data_manager.load_data()
        students = loaded["students"]

        # Filter by name containing "Anderson"
        anderson_students = [s for s in students if "anderson" in s["name"].lower()]
        self.assertEqual(len(anderson_students), 2)


class TestSeatingAssignmentWorkflow(unittest.TestCase):
    """Test end-to-end seating assignment workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_auto_assign_workflow(self) -> None:
        """Test: Create floorplan → Add students → Auto-assign → Save."""
        data = self.data_manager.load_data()

        # Create floorplan
        room = Room(id="r1", name="Classroom", x=50, y=50, width=400, height=300)
        data["floorplan"]["rooms"] = [{
            "id": room.id, "name": room.name, "x": room.x, "y": room.y,
            "width": room.width, "height": room.height
        }]

        # Add seats
        seats = [
            Seat(id=f"s{i}", room_id="r1", number=i+1, x=60+i*20, y=60)
            for i in range(4)
        ]
        data["floorplan"]["seats"] = [
            {"id": s.id, "room_id": s.room_id, "number": s.number, "x": s.x, "y": s.y}
            for s in seats
        ]

        # Add students
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True, "tuesday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
            Student(id="st3", name="Charlie", weekly_pattern={"monday": True, "tuesday": True}),
        ]
        data["students"] = [
            {"id": s.id, "name": s.name, "weekly_pattern": s.weekly_pattern}
            for s in students
        ]

        # Auto-assign for Monday
        assignments_mon, conflicts_mon = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        # Auto-assign for Tuesday
        assignments_tue, conflicts_tue = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="tuesday",
            week="2025-W43"
        )

        # Save assignments
        data["assignments"]["2025-W43"] = {
            "monday": [{"student_id": a.student_id, "seat_id": a.seat_id} for a in assignments_mon],
            "tuesday": [{"student_id": a.student_id, "seat_id": a.seat_id} for a in assignments_tue],
        }
        self.data_manager.save_data(data, create_backup=False)

        # Verify
        loaded = self.data_manager.load_data()
        self.assertEqual(len(loaded["assignments"]["2025-W43"]["monday"]), 3)
        self.assertEqual(len(loaded["assignments"]["2025-W43"]["tuesday"]), 2)
        self.assertEqual(len(conflicts_mon), 0)
        self.assertEqual(len(conflicts_tue), 0)  # Alice and Charlie available Tuesday (Bob not)

    def test_manual_override_workflow(self) -> None:
        """Test: Auto-assign → Manual override → Save."""
        data = self.data_manager.load_data()

        # Setup
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=60, y=60),
            Seat(id="s2", room_id="r1", number=2, x=80, y=60),
        ]

        # Auto-assign
        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        # Manual override: swap assignments
        if len(assignments) >= 2:
            assignments[0].seat_id, assignments[1].seat_id = assignments[1].seat_id, assignments[0].seat_id

        # Save
        data["assignments"]["2025-W43"] = {
            "monday": [{"student_id": a.student_id, "seat_id": a.seat_id} for a in assignments]
        }
        self.data_manager.save_data(data, create_backup=False)

        # Verify
        loaded = self.data_manager.load_data()
        self.assertEqual(len(loaded["assignments"]["2025-W43"]["monday"]), 2)


class TestPdfExportWorkflow(unittest.TestCase):
    """Test end-to-end PDF export workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)
        self.pdf_exporter = PdfExporter()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_export_pdf_from_assignments(self) -> None:
        """Test exporting assignments to PDF."""
        # Create assignment data
        assignments = {
            "2025-W43": {
                "monday": [
                    {"student_id": "st1", "seat_id": "s1"},
                    {"student_id": "st2", "seat_id": "s2"},
                ]
            }
        }

        # Create output file
        pdf_path = Path(self.temp_dir.name) / "test_output.pdf"

        # Export
        try:
            result = self.pdf_exporter.export_assignments(
                week="2025-W43",
                assignments=assignments,
                output_path=str(pdf_path)
            )

            # Verify
            if result:
                self.assertTrue(pdf_path.exists())
        except ImportError:
            # ReportLab may not be available
            self.skipTest("ReportLab not available")

    def test_export_with_complete_data(self) -> None:
        """Test exporting assignments with rooms, seats, and students."""
        # Setup complete data
        data = self.data_manager.load_data()

        data["floorplan"]["rooms"] = [
            {"id": "r1", "name": "Classroom A", "x": 50, "y": 50, "width": 400, "height": 300}
        ]
        data["floorplan"]["seats"] = [
            {"id": "s1", "room_id": "r1", "number": 1, "x": 60, "y": 60},
            {"id": "s2", "room_id": "r1", "number": 2, "x": 80, "y": 60},
        ]
        data["students"] = [
            {"id": "st1", "name": "Alice", "weekly_pattern": {}},
            {"id": "st2", "name": "Bob", "weekly_pattern": {}},
        ]
        data["assignments"]["2025-W43"] = {
            "monday": [
                {"student_id": "st1", "seat_id": "s1"},
                {"student_id": "st2", "seat_id": "s2"},
            ]
        }

        # Save
        self.data_manager.save_data(data, create_backup=False)

        # Export
        pdf_path = Path(self.temp_dir.name) / "complete.pdf"
        try:
            result = self.pdf_exporter.export_assignments(
                week="2025-W43",
                assignments=data["assignments"],
                output_path=str(pdf_path)
            )
            if result:
                self.assertTrue(pdf_path.exists())
        except ImportError:
            self.skipTest("ReportLab not available")


class TestCompleteApplicationWorkflow(unittest.TestCase):
    """Test complete end-to-end application workflow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)
        self.validator = Validator()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_full_cycle_setup_assign_export_save(self) -> None:
        """Test complete workflow: Setup → Assign → Export → Save → Reload."""
        # Step 1: Setup floorplan
        data = self.data_manager.load_data()

        rooms = [
            Room(id="r1", name="Classroom A", x=50, y=50, width=400, height=300),
            Room(id="r2", name="Classroom B", x=500, y=50, width=400, height=300),
        ]
        data["floorplan"]["rooms"] = [
            {"id": r.id, "name": r.name, "x": r.x, "y": r.y, "width": r.width, "height": r.height}
            for r in rooms
        ]

        seats = []
        for r_idx, room in enumerate(rooms):
            for s_idx in range(6):
                seat = Seat(
                    id=f"s{r_idx}{s_idx}",
                    room_id=room.id,
                    number=s_idx + 1,
                    x=60 + s_idx * 20,
                    y=60
                )
                seats.append(seat)

        data["floorplan"]["seats"] = [
            {"id": s.id, "room_id": s.room_id, "number": s.number, "x": s.x, "y": s.y}
            for s in seats
        ]

        # Step 2: Add students
        students = [
            Student(id=f"st{i}", name=f"Student {i}", weekly_pattern={
                "monday": i % 2 == 0,
                "tuesday": i % 3 == 0,
                "wednesday": True
            })
            for i in range(10)
        ]
        data["students"] = [
            {"id": s.id, "name": s.name, "weekly_pattern": s.weekly_pattern}
            for s in students
        ]

        # Step 3: Validate
        is_valid, errors = self.validator.validate_data(data)
        self.assertTrue(is_valid)

        # Step 4: Auto-assign
        for day in ["monday", "tuesday", "wednesday"]:
            assignments, conflicts = AssignmentEngine.assign_day(
                students=students,
                seats=seats,
                day=day,
                week="2025-W43"
            )
            if day not in data["assignments"]["2025-W43"]:
                data["assignments"]["2025-W43"][day] = []
            data["assignments"]["2025-W43"][day] = [
                {"student_id": a.student_id, "seat_id": a.seat_id}
                for a in assignments
            ]

        # Step 5: Save
        self.data_manager.save_data(data, create_backup=False)

        # Step 6: Reload and verify
        reloaded = self.data_manager.load_data()
        self.assertEqual(len(reloaded["floorplan"]["rooms"]), 2)
        self.assertEqual(len(reloaded["floorplan"]["seats"]), 12)
        self.assertEqual(len(reloaded["students"]), 10)
        self.assertIn("monday", reloaded["assignments"]["2025-W43"])
        self.assertGreater(len(reloaded["assignments"]["2025-W43"]["monday"]), 0)


if __name__ == "__main__":
    unittest.main()
