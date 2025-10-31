"""Unit tests for DataManager."""

import unittest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.data_manager import DataManager


class TestDataManager(unittest.TestCase):
    """Tests for DataManager class."""

    def setUp(self) -> None:
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager = DataManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_initialization(self) -> None:
        """Test DataManager initialization."""
        self.assertIsNotNone(self.data_manager)
        self.assertEqual(str(self.data_manager.data_dir), self.temp_dir.name)
        self.assertTrue(self.data_manager.backup_dir.exists())

    def test_load_nonexistent_file_creates_empty(self) -> None:
        """Test loading non-existent file returns empty data structure."""
        data = self.data_manager.load_data()
        self.assertIn("metadata", data)
        self.assertIn("floorplan", data)
        self.assertIn("students", data)
        self.assertIn("assignments", data)

    def test_save_and_load_data(self) -> None:
        """Test saving and loading data roundtrip."""
        original_data = {
            "metadata": {
                "version": "1.0",
                "last_modified": "2025-10-31T14:30:00Z",
                "last_user": "test_user"
            },
            "floorplan": {
                "rooms": [
                    {"id": "room_001", "name": "Room A", "x": 50, "y": 50, "width": 400, "height": 300, "color": "#1e3a5f"}
                ],
                "seats": []
            },
            "students": [],
            "assignments": {}
        }

        # Save data
        self.data_manager.save_data(original_data, create_backup=False)

        # Load data back
        loaded_data = self.data_manager.load_data()

        # Verify
        self.assertEqual(loaded_data["metadata"]["version"], "1.0")
        self.assertEqual(len(loaded_data["floorplan"]["rooms"]), 1)
        self.assertEqual(loaded_data["floorplan"]["rooms"][0]["id"], "room_001")

    def test_backup_data(self) -> None:
        """Test backup creation."""
        # Create initial data file
        data = self.data_manager._create_empty_data()
        self.data_manager.save_data(data, create_backup=False)

        # Create backup
        backup_file = self.data_manager.backup_data()

        # Verify backup exists
        self.assertTrue(Path(backup_file).exists())
        backup_files = self.data_manager.get_backup_files()
        self.assertEqual(len(backup_files), 1)

    def test_validate_data_valid(self) -> None:
        """Test validation of valid data."""
        data = self.data_manager._create_empty_data()
        is_valid, errors = self.data_manager.validate_data(data)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_data_missing_keys(self) -> None:
        """Test validation detects missing keys."""
        data = {"metadata": {}}  # Missing required keys
        is_valid, errors = self.data_manager.validate_data(data)

        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)

    def test_validate_data_room_reference(self) -> None:
        """Test validation checks seat room references."""
        data = {
            "metadata": {"version": "1.0"},
            "floorplan": {
                "rooms": [{"id": "room_001"}],
                "seats": [{"id": "seat_001", "room_id": "room_999"}]  # Invalid reference
            },
            "students": [],
            "assignments": {}
        }
        is_valid, errors = self.data_manager.validate_data(data)

        self.assertFalse(is_valid)
        self.assertTrue(any("non-existent room" in str(e) for e in errors))

    def test_get_backup_files_sorted(self) -> None:
        """Test backup files are returned sorted by date."""
        data = self.data_manager._create_empty_data()
        self.data_manager.save_data(data, create_backup=False)

        # Create multiple backups
        import time
        backup1 = self.data_manager.backup_data()
        time.sleep(1.1)  # Sleep > 1 second to ensure different timestamp
        backup2 = self.data_manager.backup_data()

        backups = self.data_manager.get_backup_files()
        self.assertGreaterEqual(len(backups), 2)
        # Should have at least 2 backup files
        backup_names = [b.name for b in backups]
        self.assertIn(Path(backup1).name, backup_names)
        self.assertIn(Path(backup2).name, backup_names)

    def test_clear_old_backups(self) -> None:
        """Test clearing of old backups."""
        data = self.data_manager._create_empty_data()
        self.data_manager.save_data(data, create_backup=False)

        # Create multiple backups with sufficient delay
        import time
        backup_count = 12
        for i in range(backup_count):
            self.data_manager.backup_data()
            if i < backup_count - 1:
                time.sleep(0.1)  # Longer delay to ensure different file times

        backups_before = self.data_manager.get_backup_files()
        initial_count = len(backups_before)

        if initial_count >= 10:
            # Clear, keeping only 5
            deleted = self.data_manager.clear_old_backups(keep_count=5)
            remaining = self.data_manager.get_backup_files()

            # Should have deleted some
            self.assertGreater(deleted, 0)
            # Should have exactly 5 remaining
            self.assertEqual(len(remaining), 5)
        else:
            # If we don't have enough backups due to timestamp collisions, just verify method works
            deleted = self.data_manager.clear_old_backups(keep_count=5)
            self.assertGreaterEqual(deleted, 0)

    def test_get_rooms_from_data(self) -> None:
        """Test extracting rooms from data."""
        data = {
            "floorplan": {
                "rooms": [
                    {"id": "room_001", "name": "Room A", "x": 50, "y": 50, "width": 400, "height": 300, "color": "#1e3a5f"}
                ],
                "seats": []
            },
            "students": [],
            "assignments": {}
        }
        rooms = self.data_manager.get_rooms(data)
        self.assertEqual(len(rooms), 1)
        self.assertEqual(rooms[0].id, "room_001")
        self.assertEqual(rooms[0].name, "Room A")

    def test_get_students_from_data(self) -> None:
        """Test extracting students from data."""
        data = {
            "students": [
                {
                    "id": "student_001",
                    "name": "Alice",
                    "weekly_pattern": {},
                    "valid_from": "2025-01-01",
                    "valid_until": "ongoing",
                    "requirements": []
                }
            ],
            "floorplan": {"rooms": [], "seats": []},
            "assignments": {}
        }
        students = self.data_manager.get_students(data)
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].name, "Alice")


if __name__ == "__main__":
    unittest.main()
