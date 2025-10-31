"""DataManager handles JSON I/O, backup, and data validation."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from config import DATA_FILE, LOCK_FILE, BACKUP_DIR
from models import Room, Seat, Student, Assignment

logger = logging.getLogger(__name__)


class DataManager:
    """Manages all data persistence operations for the application.

    Handles:
    - Loading and saving JSON data files
    - Automatic backup creation
    - Data validation
    - File I/O with error handling
    """

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize DataManager.

        Args:
            data_dir: Directory for data files. Defaults to current directory.
        """
        self.data_dir = Path(data_dir) if data_dir else Path.cwd()
        self.data_file = self.data_dir / DATA_FILE
        self.backup_dir = self.data_dir / BACKUP_DIR

        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)

    def load_data(self) -> Dict[str, Any]:
        """Load data from JSON file.

        Returns:
            Dictionary containing application data

        Raises:
            FileNotFoundError: If data file doesn't exist
            json.JSONDecodeError: If JSON is malformed
        """
        try:
            if not self.data_file.exists():
                logger.info(f"Data file not found at {self.data_file}, creating new data")
                return self._create_empty_data()

            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"Loaded data from {self.data_file}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {self.data_file}: {e}")
            self._backup_corrupt_file()
            raise

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def save_data(self, data: Dict[str, Any], create_backup: bool = True) -> None:
        """Save data to JSON file with optional backup.

        Args:
            data: Data dictionary to save
            create_backup: Whether to create backup before saving

        Raises:
            IOError: If save operation fails
        """
        try:
            if create_backup and self.data_file.exists():
                self.backup_data()

            # Ensure directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first (atomic write)
            temp_file = self.data_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Move temp file to actual file (atomic on most systems)
            temp_file.replace(self.data_file)

            logger.info(f"Saved data to {self.data_file}")

        except Exception as e:
            logger.error(f"Error saving data: {e}")
            raise

    def backup_data(self) -> str:
        """Create timestamped backup of current data file.

        Returns:
            Path to backup file created

        Raises:
            IOError: If backup operation fails
        """
        try:
            if not self.data_file.exists():
                logger.warning("No data file to backup")
                return ""

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"data_{timestamp}.json"

            shutil.copy2(self.data_file, backup_file)
            logger.info(f"Created backup at {backup_file}")

            return str(backup_file)

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise

    def _backup_corrupt_file(self) -> None:
        """Backup corrupt data file with timestamp."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupt_file = self.backup_dir / f"data_CORRUPT_{timestamp}.json"
            shutil.copy2(self.data_file, corrupt_file)
            logger.info(f"Backed up corrupt file to {corrupt_file}")
        except Exception as e:
            logger.warning(f"Could not backup corrupt file: {e}")

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate data structure and integrity.

        Args:
            data: Data dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Check required top-level keys
        required_keys = ["metadata", "floorplan", "students", "assignments"]
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")

        # Validate metadata
        if "metadata" in data:
            metadata = data["metadata"]
            if not isinstance(metadata, dict):
                errors.append("metadata must be a dictionary")
            elif "version" not in metadata:
                errors.append("metadata missing 'version'")

        # Validate floorplan
        if "floorplan" in data:
            floorplan = data["floorplan"]
            if not isinstance(floorplan, dict):
                errors.append("floorplan must be a dictionary")
            else:
                if "rooms" not in floorplan:
                    errors.append("floorplan missing 'rooms'")
                if "seats" not in floorplan:
                    errors.append("floorplan missing 'seats'")

                # Validate room references in seats
                if "rooms" in floorplan and "seats" in floorplan:
                    room_ids = {room["id"] for room in floorplan.get("rooms", [])}
                    for seat in floorplan.get("seats", []):
                        if seat.get("room_id") not in room_ids:
                            errors.append(f"Seat {seat.get('id')} references non-existent room")

        # Validate students
        if "students" in data:
            if not isinstance(data["students"], list):
                errors.append("students must be a list")

        # Validate assignments
        if "assignments" in data:
            if not isinstance(data["assignments"], dict):
                errors.append("assignments must be a dictionary")

        is_valid = len(errors) == 0
        return is_valid, errors

    def _create_empty_data(self) -> Dict[str, Any]:
        """Create an empty data structure with required fields.

        Returns:
            Empty data dictionary with proper structure
        """
        return {
            "metadata": {
                "version": "1.0",
                "last_modified": datetime.utcnow().isoformat() + "Z",
                "last_user": "system"
            },
            "floorplan": {
                "rooms": [],
                "seats": []
            },
            "students": [],
            "assignments": {}
        }

    def get_backup_files(self) -> List[Path]:
        """Get list of backup files, sorted by date (newest first).

        Returns:
            List of Path objects for backup files
        """
        if not self.backup_dir.exists():
            return []

        backup_files = sorted(
            self.backup_dir.glob("data_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return backup_files

    def restore_from_backup(self, backup_file: Path) -> Dict[str, Any]:
        """Restore data from a backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            Restored data dictionary

        Raises:
            FileNotFoundError: If backup file doesn't exist
            json.JSONDecodeError: If backup file is corrupted
        """
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Restored data from backup: {backup_file}")
            return data
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            raise

    def clear_old_backups(self, keep_count: int = 10) -> int:
        """Delete old backup files, keeping only the most recent ones.

        Args:
            keep_count: Number of backups to keep

        Returns:
            Number of backups deleted
        """
        backup_files = self.get_backup_files()
        deleted_count = 0

        for backup_file in backup_files[keep_count:]:
            try:
                backup_file.unlink()
                logger.info(f"Deleted old backup: {backup_file}")
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Could not delete backup {backup_file}: {e}")

        return deleted_count

    # ========================================================================
    # Convenience methods for model conversion
    # ========================================================================

    def get_rooms(self, data: Dict[str, Any]) -> List[Room]:
        """Extract and convert rooms from data.

        Args:
            data: Data dictionary

        Returns:
            List of Room objects
        """
        rooms = []
        for room_dict in data.get("floorplan", {}).get("rooms", []):
            rooms.append(Room.from_dict(room_dict))
        return rooms

    def get_seats(self, data: Dict[str, Any]) -> List[Seat]:
        """Extract and convert seats from data.

        Args:
            data: Data dictionary

        Returns:
            List of Seat objects
        """
        seats = []
        for seat_dict in data.get("floorplan", {}).get("seats", []):
            seats.append(Seat.from_dict(seat_dict))
        return seats

    def get_students(self, data: Dict[str, Any]) -> List[Student]:
        """Extract and convert students from data.

        Args:
            data: Data dictionary

        Returns:
            List of Student objects
        """
        students = []
        for student_dict in data.get("students", []):
            students.append(Student.from_dict(student_dict))
        return students

    def get_assignments(self, data: Dict[str, Any]) -> List[Assignment]:
        """Extract and convert assignments from data.

        Args:
            data: Data dictionary

        Returns:
            List of Assignment objects
        """
        assignments = []
        for week, days in data.get("assignments", {}).items():
            for day, day_assignments in days.items():
                for assignment_dict in day_assignments:
                    assignment_dict["week"] = week
                    assignment_dict["day"] = day
                    assignments.append(Assignment.from_dict(assignment_dict))
        return assignments
