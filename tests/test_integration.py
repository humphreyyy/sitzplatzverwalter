"""Integration tests for Sitzplatz-Manager.

Tests the interaction between layers:
- Data Layer (DataManager, LockManager, UndoManager)
- Logic Layer (AssignmentEngine, Validator, PdfExporter)
- GUI Layer components
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from data.data_manager import DataManager
from data.undo_manager import UndoManager
from data.lock_manager import LockManager
from logic.assignment_engine import AssignmentEngine
from logic.validator import Validator
from models.student import Student
from models.seat import Seat
from models.room import Room
from models.assignment import Assignment


class TestDataLogicIntegration(unittest.TestCase):
    """Test integration between Data and Logic layers."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)
        self.validator = Validator()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_assignment_engine_with_data_persistence(self) -> None:
        """Test AssignmentEngine with data save/load cycle."""
        # Create test data
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]

        # Run assignment
        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        # Verify assignment works
        self.assertEqual(len(assignments), 2)
        self.assertEqual(len(conflicts), 0)

        # Save to data manager
        data = self.data_manager.load_data()
        data["students"] = [
            {"id": s.id, "name": s.name, "weekly_pattern": s.weekly_pattern}
            for s in students
        ]
        data["floorplan"]["seats"] = [
            {"id": s.id, "room_id": s.room_id, "number": s.number, "x": s.x, "y": s.y}
            for s in seats
        ]
        data["assignments"]["2025-W43"] = {
            "monday": [
                {"student_id": a.student_id, "seat_id": a.seat_id}
                for a in assignments
            ]
        }
        self.data_manager.save_data(data, create_backup=False)

        # Load and verify
        loaded_data = self.data_manager.load_data()
        self.assertEqual(len(loaded_data["assignments"]["2025-W43"]["monday"]), 2)

    def test_validator_with_loaded_data(self) -> None:
        """Test Validator validates loaded data correctly."""
        # Create valid data
        data = self.data_manager._create_empty_data()
        data["floorplan"]["rooms"] = [
            {"id": "r1", "name": "Room A", "x": 50, "y": 50, "width": 400, "height": 300}
        ]
        data["floorplan"]["seats"] = [
            {"id": "s1", "room_id": "r1", "number": 1, "x": 60, "y": 60}
        ]

        # Validate
        is_valid, errors = self.data_manager.validate_data(data)
        self.assertTrue(is_valid)

    def test_undo_manager_with_assignment_changes(self) -> None:
        """Test UndoManager tracks assignment changes."""
        undo_manager = UndoManager()

        # Create initial state
        state1 = {
            "assignments": {"2025-W43": {"monday": []}},
            "timestamp": datetime.now().isoformat()
        }
        undo_manager.push_state(state1)

        # Modify state
        state2 = {
            "assignments": {"2025-W43": {"monday": [{"student_id": "st1", "seat_id": "s1"}]}},
            "timestamp": datetime.now().isoformat()
        }
        undo_manager.push_state(state2)

        # Verify undo available
        self.assertTrue(undo_manager.can_undo())
        self.assertEqual(undo_manager.get_undo_count(), 1)

        # Undo
        reverted = undo_manager.undo()
        self.assertIsNotNone(reverted)
        self.assertEqual(len(reverted["assignments"]["2025-W43"]["monday"]), 0)

    def test_data_manager_with_lock_manager(self) -> None:
        """Test DataManager with LockManager file locking."""
        lock_manager = LockManager(self.temp_dir.name)

        # Acquire lock
        success, lock_info = lock_manager.acquire_lock("test_user")
        self.assertTrue(success)

        # Verify lock file exists
        lock_file = Path(self.temp_dir.name) / "data.lock"
        self.assertTrue(lock_file.exists())

        # Data operations should work while locked
        data = self.data_manager.load_data()
        self.assertIsNotNone(data)

        # Release lock
        lock_manager.release_lock()

        # After release, lock file should be gone
        self.assertFalse(lock_file.exists())

    def test_complete_assignment_workflow(self) -> None:
        """Test complete workflow: create data → validate → assign → save."""
        # Create floorplan
        data = self.data_manager.load_data()
        room = Room(id="r1", name="Classroom", x=50, y=50, width=400, height=300)
        data["floorplan"]["rooms"] = [{
            "id": room.id,
            "name": room.name,
            "x": room.x,
            "y": room.y,
            "width": room.width,
            "height": room.height
        }]

        # Add seats
        seats_data = []
        seats = []
        for i in range(3):
            seat = Seat(id=f"s{i}", room_id="r1", number=i+1, x=60+i*20, y=60)
            seats.append(seat)
            seats_data.append({
                "id": seat.id,
                "room_id": seat.room_id,
                "number": seat.number,
                "x": seat.x,
                "y": seat.y
            })
        data["floorplan"]["seats"] = seats_data

        # Add students
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
        ]
        data["students"] = [{
            "id": s.id,
            "name": s.name,
            "weekly_pattern": s.weekly_pattern
        } for s in students]

        # Validate
        is_valid, errors = self.data_manager.validate_data(data)
        self.assertTrue(is_valid, f"Data validation failed: {errors}")

        # Run assignment
        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )
        self.assertEqual(len(assignments), 2)

        # Save assignments
        data["assignments"]["2025-W43"] = {
            "monday": [
                {"student_id": a.student_id, "seat_id": a.seat_id}
                for a in assignments
            ]
        }

        # Save to file
        self.data_manager.save_data(data, create_backup=False)

        # Load and verify
        loaded = self.data_manager.load_data()
        self.assertEqual(len(loaded["students"]), 2)
        self.assertEqual(len(loaded["assignments"]["2025-W43"]["monday"]), 2)


class TestMultiStepWorkflow(unittest.TestCase):
    """Test complex multi-step workflows across layers."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)
        self.undo_manager = UndoManager()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_create_assign_undo_workflow(self) -> None:
        """Test: Create → Assign → Undo → Verify state."""
        # Step 1: Create data
        data = self.data_manager.load_data()
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]

        # Step 2: Save initial state (UndoManager stores: floorplan, students, assignments, metadata)
        state1 = {
            "assignments": {},
            "floorplan": {"rooms": [], "seats": []},
            "students": [],
            "metadata": {}
        }
        self.undo_manager.push_state(state1)

        # Step 3: Run assignment
        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        # Step 4: Save assigned state
        state2 = {
            "assignments": {
                "2025-W43": {"monday": [(a.student_id, a.seat_id) for a in assignments]}
            },
            "floorplan": {"rooms": [], "seats": []},
            "students": [],
            "metadata": {}
        }
        self.undo_manager.push_state(state2)

        # Step 5: Verify we can undo
        self.assertTrue(self.undo_manager.can_undo())

        # Step 6: Undo
        reverted = self.undo_manager.undo()
        self.assertIsNotNone(reverted)
        self.assertIn("assignments", reverted)
        self.assertEqual(len(reverted["assignments"]), 0)

    def test_multiple_assignments_persist(self) -> None:
        """Test that multiple day assignments persist correctly."""
        data = self.data_manager.load_data()

        # Create students and seats
        students = [
            Student(id="st1", name="Alice", weekly_pattern={
                "monday": True, "tuesday": True, "wednesday": True
            }),
            Student(id="st2", name="Bob", weekly_pattern={
                "monday": True, "tuesday": True, "wednesday": False
            }),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]

        # Assign for each day
        assignments_dict = {}
        for day in ["monday", "tuesday", "wednesday"]:
            assignments, conflicts = AssignmentEngine.assign_day(
                students=students,
                seats=seats,
                day=day,
                week="2025-W43"
            )
            assignments_dict[day] = [(a.student_id, a.seat_id) for a in assignments]

        # Verify assignments
        self.assertEqual(len(assignments_dict["monday"]), 2)
        self.assertEqual(len(assignments_dict["tuesday"]), 2)
        self.assertEqual(len(assignments_dict["wednesday"]), 1)  # Only Alice

        # Save to data manager
        data["assignments"]["2025-W43"] = {
            "monday": [{"student_id": s, "seat_id": st} for s, st in assignments_dict["monday"]],
            "tuesday": [{"student_id": s, "seat_id": st} for s, st in assignments_dict["tuesday"]],
            "wednesday": [{"student_id": s, "seat_id": st} for s, st in assignments_dict["wednesday"]],
        }
        self.data_manager.save_data(data, create_backup=False)

        # Load and verify
        loaded = self.data_manager.load_data()
        self.assertEqual(len(loaded["assignments"]["2025-W43"]["wednesday"]), 1)


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity across operations."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_data_survives_save_load_cycle(self) -> None:
        """Test that complex data structures survive save/load."""
        # Create comprehensive data
        data = self.data_manager._create_empty_data()
        data["floorplan"]["rooms"] = [
            {"id": "r1", "name": "Classroom A", "x": 0, "y": 0, "width": 500, "height": 400},
            {"id": "r2", "name": "Classroom B", "x": 600, "y": 0, "width": 500, "height": 400}
        ]
        data["floorplan"]["seats"] = [
            {"id": f"s{i}", "room_id": f"r{(i % 2) + 1}", "number": i, "x": i*20, "y": 0}
            for i in range(10)
        ]
        data["students"] = [
            {
                "id": f"st{i}",
                "name": f"Student {i}",
                "weekly_pattern": {
                    "monday": i % 2 == 0,
                    "tuesday": i % 3 == 0,
                    "wednesday": True
                }
            }
            for i in range(5)
        ]

        # Save
        self.data_manager.save_data(data, create_backup=False)

        # Load
        loaded = self.data_manager.load_data()

        # Verify
        self.assertEqual(len(loaded["floorplan"]["rooms"]), 2)
        self.assertEqual(len(loaded["floorplan"]["seats"]), 10)
        self.assertEqual(len(loaded["students"]), 5)
        self.assertEqual(loaded["floorplan"]["rooms"][0]["name"], "Classroom A")
        self.assertEqual(loaded["students"][0]["name"], "Student 0")

    def test_backup_contains_exact_copy(self) -> None:
        """Test that backup contains exact copy of original data."""
        # Create data
        data = self.data_manager._create_empty_data()
        data["test_key"] = "test_value"
        self.data_manager.save_data(data, create_backup=False)

        # Create backup
        backup_file = self.data_manager.backup_data()

        # Load backup
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)

        # Verify
        self.assertEqual(backup_data["test_key"], "test_value")


if __name__ == "__main__":
    unittest.main()
