"""Unit tests for GUI components.

Tests MainWindow, FloorplanTab, StudentsTab, and PlanningTab functionality
focusing on integration and data handling.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import tempfile
import json
from pathlib import Path

from config import UI_TEXTS, WEEKDAYS
from data.data_manager import DataManager
from data.undo_manager import UndoManager


class TestGUIConstants(unittest.TestCase):
    """Test that GUI constants are properly configured."""

    def test_ui_texts_german(self) -> None:
        """Test that UI texts are in German."""
        german_texts = [
            UI_TEXTS.get("file_menu") == "Datei",
            UI_TEXTS.get("edit_menu") == "Bearbeiten",
            UI_TEXTS.get("help_menu") == "Hilfe",
            UI_TEXTS.get("save") == "Speichern",
            UI_TEXTS.get("add_student") == "Schüler hinzufügen",
            UI_TEXTS.get("auto_assign") == "Automatisch zuteilen",
        ]

        self.assertTrue(all(german_texts), "Some UI texts are not in German")

    def test_ui_texts_completeness(self) -> None:
        """Test that all required UI texts are present."""
        required_keys = [
            "app_title", "file_menu", "edit_menu", "help_menu",
            "save", "save_button", "cancel", "add_student",
            "floorplan_tab", "students_tab", "planning_tab"
        ]

        for key in required_keys:
            self.assertIn(key, UI_TEXTS, f"Missing UI text: {key}")

    def test_weekdays_complete(self) -> None:
        """Test that all weekdays are defined."""
        expected_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in expected_days:
            self.assertIn(day, WEEKDAYS, f"Missing weekday: {day}")


class TestUndoManagerIntegration(unittest.TestCase):
    """Test UndoManager integration with GUI."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.undo_manager = UndoManager()

    def test_push_and_undo_state(self) -> None:
        """Test pushing and undoing state."""
        state1 = {"value": 1}
        state2 = {"value": 2}

        self.undo_manager.push_state(state1)
        self.undo_manager.push_state(state2)

        # Verify can undo
        self.assertTrue(self.undo_manager.can_undo())

        # Undo to state1
        self.undo_manager.undo()
        self.assertEqual(self.undo_manager.get_undo_count(), 0)

    def test_redo_after_undo(self) -> None:
        """Test redo functionality."""
        state1 = {"value": 1}
        state2 = {"value": 2}

        self.undo_manager.push_state(state1)
        self.undo_manager.push_state(state2)
        self.undo_manager.undo()

        # Verify can redo
        self.assertTrue(self.undo_manager.can_redo())

        # Redo to state2
        self.undo_manager.redo()
        self.assertEqual(self.undo_manager.get_redo_count(), 0)

    def test_clear_undo_stack(self) -> None:
        """Test clearing undo stack."""
        self.undo_manager.push_state({"value": 1})
        self.undo_manager.push_state({"value": 2})

        self.undo_manager.clear()

        # Should not be able to undo
        self.assertFalse(self.undo_manager.can_undo())

    def test_multiple_undo_redo_cycles(self) -> None:
        """Test multiple undo/redo cycles."""
        for i in range(5):
            self.undo_manager.push_state({"value": i})

        # Undo all states
        for _ in range(4):
            self.assertTrue(self.undo_manager.can_undo())
            self.undo_manager.undo()

        self.assertFalse(self.undo_manager.can_undo())

        # Redo all states
        for _ in range(4):
            self.assertTrue(self.undo_manager.can_redo())
            self.undo_manager.redo()

        self.assertFalse(self.undo_manager.can_redo())


class TestDataManagerBasics(unittest.TestCase):
    """Test basic DataManager functionality for GUI use."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_data_creates_empty_file(self) -> None:
        """Test that load_data creates empty file structure if missing."""
        # Load non-existent file (should create empty structure)
        data = self.data_manager.load_data()

        self.assertIsNotNone(data)
        self.assertIn("floorplan", data)
        self.assertIn("students", data)
        self.assertIn("assignments", data)

    def test_load_data_consistency(self) -> None:
        """Test that load_data returns consistent structure."""
        data1 = self.data_manager.load_data()
        data2 = self.data_manager.load_data()

        # Both should have same structure (timestamps will differ)
        self.assertEqual(data1["floorplan"], data2["floorplan"])
        self.assertEqual(data1["students"], data2["students"])
        self.assertEqual(data1["assignments"], data2["assignments"])

    def test_save_and_reload(self) -> None:
        """Test saving and reloading data."""
        data = self.data_manager.load_data()

        # Add a student
        data["students"].append({
            "id": "s1",
            "name": "Test Student",
            "valid_from": "2025-01-01",
            "valid_until": "2025-12-31",
            "weekly_pattern": {},
            "requirements": {}
        })

        self.data_manager.save_data(data, create_backup=False)

        # Create new manager and reload
        data_manager2 = DataManager(self.temp_dir.name)
        loaded_data = data_manager2.load_data()

        self.assertEqual(len(loaded_data["students"]), 1)
        self.assertEqual(loaded_data["students"][0]["name"], "Test Student")


class TestGUIIntegrationWithLogic(unittest.TestCase):
    """Test GUI integration with business logic layer."""

    def test_assignment_engine_available(self) -> None:
        """Test that AssignmentEngine is available for GUI."""
        from logic.assignment_engine import AssignmentEngine

        # Verify key methods exist
        self.assertTrue(hasattr(AssignmentEngine, 'assign_week'))
        self.assertTrue(hasattr(AssignmentEngine, 'assign_day'))
        self.assertTrue(hasattr(AssignmentEngine, 'get_assignment_statistics'))

    def test_validator_available(self) -> None:
        """Test that Validator is available for GUI."""
        from logic.validator import Validator

        # Verify key methods exist
        self.assertTrue(hasattr(Validator, 'validate_room_overlap'))
        self.assertTrue(hasattr(Validator, 'validate_seat_in_room'))
        self.assertTrue(hasattr(Validator, 'validate_capacity'))

    def test_pdf_exporter_available(self) -> None:
        """Test that PdfExporter is available for GUI."""
        from logic.pdf_exporter import PdfExporter

        # Verify key methods exist
        self.assertTrue(hasattr(PdfExporter, 'export_week_to_pdf'))
        self.assertTrue(hasattr(PdfExporter, 'save_pdf_to_file'))


class TestFloorplanDataStructure(unittest.TestCase):
    """Test data structures for floorplan."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_room_structure(self) -> None:
        """Test that rooms can be added to floorplan."""
        data = self.data_manager.load_data()

        room = {
            "id": "room_1",
            "name": "Test Room",
            "x": 50,
            "y": 50,
            "width": 300,
            "height": 200
        }

        data["floorplan"]["rooms"].append(room)
        self.data_manager.save_data(data, create_backup=False)

        # Reload and verify
        data_manager2 = DataManager(self.temp_dir.name)
        loaded_data = data_manager2.load_data()

        self.assertEqual(len(loaded_data["floorplan"]["rooms"]), 1)
        self.assertEqual(loaded_data["floorplan"]["rooms"][0]["name"], "Test Room")

    def test_seat_structure(self) -> None:
        """Test that seats can be added to floorplan."""
        data = self.data_manager.load_data()

        seat = {
            "id": "seat_1",
            "number": 1,
            "room_id": "room_1",
            "x": 100,
            "y": 100
        }

        data["floorplan"]["seats"].append(seat)
        self.data_manager.save_data(data, create_backup=False)

        # Reload and verify
        data_manager2 = DataManager(self.temp_dir.name)
        loaded_data = data_manager2.load_data()

        self.assertEqual(len(loaded_data["floorplan"]["seats"]), 1)
        self.assertEqual(loaded_data["floorplan"]["seats"][0]["number"], 1)


class TestStudentDataStructure(unittest.TestCase):
    """Test data structures for students."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_student_structure(self) -> None:
        """Test student data structure."""
        data = self.data_manager.load_data()

        student = {
            "id": "student_1",
            "name": "Max Müller",
            "valid_from": "2025-01-01",
            "valid_until": "2025-12-31",
            "weekly_pattern": {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False
            },
            "requirements": {
                "near_window": False,
                "near_door": False
            }
        }

        data["students"].append(student)
        self.data_manager.save_data(data, create_backup=False)

        # Reload and verify
        data_manager2 = DataManager(self.temp_dir.name)
        loaded_data = data_manager2.load_data()

        self.assertEqual(len(loaded_data["students"]), 1)
        self.assertEqual(loaded_data["students"][0]["name"], "Max Müller")
        self.assertTrue(loaded_data["students"][0]["weekly_pattern"]["monday"])

    def test_student_filtering(self) -> None:
        """Test that students can be filtered by name."""
        data = self.data_manager.load_data()

        # Add multiple students
        students = [
            {"id": "s1", "name": "Alice", "valid_from": "2025-01-01", "valid_until": "2025-12-31",
             "weekly_pattern": {}, "requirements": {}},
            {"id": "s2", "name": "Bob", "valid_from": "2025-01-01", "valid_until": "2025-12-31",
             "weekly_pattern": {}, "requirements": {}},
            {"id": "s3", "name": "Charlie", "valid_from": "2025-01-01", "valid_until": "2025-12-31",
             "weekly_pattern": {}, "requirements": {}},
        ]

        data["students"] = students

        # Filter by substring
        filtered = [s for s in data["students"] if "li" in s["name"].lower()]
        self.assertEqual(len(filtered), 2)  # Alice and Charlie


class TestAssignmentDataStructure(unittest.TestCase):
    """Test data structures for weekly assignments."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_assignment_structure(self) -> None:
        """Test assignment data structure."""
        data = self.data_manager.load_data()

        week = "2025-W43"
        assignment = {
            "monday": [
                {"student_id": "student_1", "seat_id": "seat_1"},
                {"student_id": "student_2", "seat_id": "seat_2"},
            ],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": [],
            "saturday": [],
            "sunday": []
        }

        data["assignments"][week] = assignment
        self.data_manager.save_data(data, create_backup=False)

        # Reload and verify
        data_manager2 = DataManager(self.temp_dir.name)
        loaded_data = data_manager2.load_data()

        self.assertIn(week, loaded_data["assignments"])
        self.assertEqual(len(loaded_data["assignments"][week]["monday"]), 2)


class TestGUIWorkflow(unittest.TestCase):
    """Test complete GUI workflow scenarios."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)
        self.undo_manager = UndoManager()

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_create_floorplan_workflow(self) -> None:
        """Test creating a floorplan (add rooms and seats)."""
        data = self.data_manager.load_data()

        # Add room
        room = {"id": "room_1", "name": "Klassenraum A", "x": 50, "y": 50, "width": 300, "height": 200}
        data["floorplan"]["rooms"].append(room)

        # Add seats
        for i in range(1, 11):
            seat = {
                "id": f"seat_{i}",
                "number": i,
                "room_id": "room_1",
                "x": 100 + (i % 5) * 30,
                "y": 100 + (i // 5) * 30
            }
            data["floorplan"]["seats"].append(seat)

        self.undo_manager.push_state(data)
        self.data_manager.save_data(data, create_backup=False)

        # Verify
        loaded_data = self.data_manager.load_data()
        self.assertEqual(len(loaded_data["floorplan"]["rooms"]), 1)
        self.assertEqual(len(loaded_data["floorplan"]["seats"]), 10)

    def test_add_students_workflow(self) -> None:
        """Test adding students to the system."""
        data = self.data_manager.load_data()

        # Add students
        for i in range(1, 6):
            student = {
                "id": f"student_{i}",
                "name": f"Student {i}",
                "valid_from": "2025-01-01",
                "valid_until": "2025-12-31",
                "weekly_pattern": {
                    "monday": True, "tuesday": True, "wednesday": True,
                    "thursday": True, "friday": True, "saturday": False, "sunday": False
                },
                "requirements": {}
            }
            data["students"].append(student)

        self.undo_manager.push_state(data)
        self.data_manager.save_data(data, create_backup=False)

        # Verify
        loaded_data = self.data_manager.load_data()
        self.assertEqual(len(loaded_data["students"]), 5)

    def test_undo_redo_workflow(self) -> None:
        """Test undo/redo functionality in GUI workflow."""
        data1 = self.data_manager.load_data()
        self.undo_manager.push_state(data1)

        # Create multiple states
        data2 = self.data_manager.load_data()
        data2["students"].append({"id": "s1", "name": "Test", "valid_from": "2025-01-01",
                                  "valid_until": "2025-12-31", "weekly_pattern": {}, "requirements": {}})
        self.undo_manager.push_state(data2)

        data3 = self.data_manager.load_data()
        data3["students"].append({"id": "s2", "name": "Test2", "valid_from": "2025-01-01",
                                  "valid_until": "2025-12-31", "weekly_pattern": {}, "requirements": {}})
        self.undo_manager.push_state(data3)

        # Verify undo works
        self.assertTrue(self.undo_manager.can_undo())
        self.undo_manager.undo()
        self.undo_manager.undo()
        self.assertEqual(self.undo_manager.get_undo_count(), 0)

        # Verify redo works
        self.assertTrue(self.undo_manager.can_redo())
        self.undo_manager.redo()
        self.assertEqual(self.undo_manager.get_redo_count(), 1)


class TestGUIComponentAvailability(unittest.TestCase):
    """Test that all GUI components can be imported."""

    def test_can_import_gui_modules(self) -> None:
        """Test that GUI modules can be imported (without Tkinter display)."""
        # Note: Tkinter may not be available, but we can check if modules compile
        try:
            import py_compile
            gui_files = [
                "gui/main_window.py",
                "gui/floorplan_tab.py",
                "gui/students_tab.py",
                "gui/planning_tab.py"
            ]

            for gui_file in gui_files:
                # Just compile the file to check syntax
                py_compile.compile(gui_file, doraise=True)

        except Exception as e:
            self.fail(f"GUI module compilation failed: {e}")


if __name__ == "__main__":
    unittest.main()
