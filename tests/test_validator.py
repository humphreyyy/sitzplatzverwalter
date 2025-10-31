"""
Unit tests for the Validator module.

Tests business rule validation including:
- Room overlap detection
- Seat positioning validation
- Capacity checking
- Date range validation
- Assignment conflict detection
"""

import unittest
from logic.validator import Validator
from models.room import Room
from models.seat import Seat
from models.student import Student
from models.assignment import Assignment


class TestValidator(unittest.TestCase):
    """Test cases for the Validator class."""

    def test_validate_room_overlap_no_overlap(self):
        """Test that non-overlapping rooms are validated correctly."""
        room1 = Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f")
        room2 = Room(id="room_002", name="Room B", x=150, y=0, width=100, height=100, color="#1e3a5f")

        is_valid, conflicts = Validator.validate_room_overlap([room1, room2])

        self.assertTrue(is_valid)
        self.assertEqual(len(conflicts), 0)

    def test_validate_room_overlap_with_overlap(self):
        """Test that overlapping rooms are detected."""
        room1 = Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f")
        room2 = Room(id="room_002", name="Room B", x=50, y=50, width=100, height=100, color="#1e3a5f")

        is_valid, conflicts = Validator.validate_room_overlap([room1, room2])

        self.assertFalse(is_valid)
        self.assertEqual(len(conflicts), 1)
        self.assertIn(("room_001", "room_002"), conflicts)

    def test_validate_room_overlap_edge_touching(self):
        """Test that rooms touching at edges are considered valid (not overlapping)."""
        room1 = Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f")
        room2 = Room(id="room_002", name="Room B", x=100, y=0, width=100, height=100, color="#1e3a5f")

        is_valid, conflicts = Validator.validate_room_overlap([room1, room2])

        self.assertTrue(is_valid)
        self.assertEqual(len(conflicts), 0)

    def test_validate_room_overlap_multiple_overlaps(self):
        """Test detection of multiple overlapping rooms."""
        room1 = Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f")
        room2 = Room(id="room_002", name="Room B", x=50, y=50, width=100, height=100, color="#1e3a5f")
        room3 = Room(id="room_003", name="Room C", x=75, y=75, width=100, height=100, color="#1e3a5f")

        is_valid, conflicts = Validator.validate_room_overlap([room1, room2, room3])

        self.assertFalse(is_valid)
        # Should have 3 conflicts: 1-2, 1-3, 2-3
        self.assertEqual(len(conflicts), 3)

    def test_validate_room_overlap_empty_list(self):
        """Test that empty room list is valid."""
        is_valid, conflicts = Validator.validate_room_overlap([])

        self.assertTrue(is_valid)
        self.assertEqual(len(conflicts), 0)

    def test_validate_seat_in_room_valid(self):
        """Test that a seat within room bounds is valid."""
        room = Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f")
        seat = Seat(id="seat_001", room_id="room_001", number=1, x=50, y=50, properties={})

        is_valid = Validator.validate_seat_in_room(seat, room)

        self.assertTrue(is_valid)

    def test_validate_seat_in_room_outside_bounds(self):
        """Test that a seat outside room bounds is invalid."""
        room = Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f")
        seat = Seat(id="seat_001", room_id="room_001", number=1, x=150, y=150, properties={})

        is_valid = Validator.validate_seat_in_room(seat, room)

        self.assertFalse(is_valid)

    def test_validate_seat_in_room_wrong_room_id(self):
        """Test that a seat with wrong room_id is invalid."""
        room = Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f")
        seat = Seat(id="seat_001", room_id="room_002", number=1, x=50, y=50, properties={})

        is_valid = Validator.validate_seat_in_room(seat, room)

        self.assertFalse(is_valid)

    def test_validate_seat_in_room_on_edge(self):
        """Test that a seat on the room edge is valid."""
        room = Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f")
        seat = Seat(id="seat_001", room_id="room_001", number=1, x=100, y=100, properties={})

        is_valid = Validator.validate_seat_in_room(seat, room)

        self.assertTrue(is_valid)

    def test_validate_capacity_sufficient(self):
        """Test capacity validation when there are enough seats."""
        students = [
            Student(id="s1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="s2", name="Bob", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="seat_001", room_id="room_001", number=1, x=0, y=0),
            Seat(id="seat_002", room_id="room_001", number=2, x=10, y=0),
            Seat(id="seat_003", room_id="room_001", number=3, x=20, y=0),
        ]

        is_valid, details = Validator.validate_capacity(students, seats, "monday")

        self.assertTrue(is_valid)
        self.assertEqual(details['students_count'], 2)
        self.assertEqual(details['seats_count'], 3)
        self.assertEqual(details['excess'], 0)

    def test_validate_capacity_overbooking(self):
        """Test capacity validation when there are too many students."""
        students = [
            Student(id="s1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="s2", name="Bob", weekly_pattern={"monday": True}),
            Student(id="s3", name="Charlie", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="seat_001", room_id="room_001", number=1, x=0, y=0),
            Seat(id="seat_002", room_id="room_001", number=2, x=10, y=0),
        ]

        is_valid, details = Validator.validate_capacity(students, seats, "monday")

        self.assertFalse(is_valid)
        self.assertEqual(details['students_count'], 3)
        self.assertEqual(details['seats_count'], 2)
        self.assertEqual(details['excess'], 1)

    def test_validate_capacity_no_students_available(self):
        """Test capacity validation when no students are available on the day."""
        students = [
            Student(id="s1", name="Alice", weekly_pattern={"monday": False}),
            Student(id="s2", name="Bob", weekly_pattern={"tuesday": True}),
        ]
        seats = [
            Seat(id="seat_001", room_id="room_001", number=1, x=0, y=0),
        ]

        is_valid, details = Validator.validate_capacity(students, seats, "monday")

        self.assertTrue(is_valid)
        self.assertEqual(details['students_count'], 0)
        self.assertEqual(details['seats_count'], 1)
        self.assertEqual(details['excess'], 0)

    def test_validate_student_date_range_valid(self):
        """Test valid student date range."""
        student = Student(
            id="s1",
            name="Alice",
            valid_from="2025-01-01",
            valid_until="2025-12-31"
        )

        is_valid, error = Validator.validate_student_date_range(student)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_student_date_range_ongoing(self):
        """Test student with 'ongoing' end date."""
        student = Student(
            id="s1",
            name="Alice",
            valid_from="2025-01-01",
            valid_until="ongoing"
        )

        is_valid, error = Validator.validate_student_date_range(student)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_student_date_range_invalid(self):
        """Test invalid student date range (from > until)."""
        student = Student(
            id="s1",
            name="Alice",
            valid_from="2025-12-31",
            valid_until="2025-01-01"
        )

        is_valid, error = Validator.validate_student_date_range(student)

        self.assertFalse(is_valid)
        self.assertIn("valid_from", error)
        self.assertIn("valid_until", error)

    def test_validate_student_date_range_same_date(self):
        """Test student with same start and end date (valid)."""
        student = Student(
            id="s1",
            name="Alice",
            valid_from="2025-06-01",
            valid_until="2025-06-01"
        )

        is_valid, error = Validator.validate_student_date_range(student)

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_student_date_range_invalid_format(self):
        """Test student with invalid date format."""
        student = Student(
            id="s1",
            name="Alice",
            valid_from="01-01-2025",  # Wrong format
            valid_until="2025-12-31"
        )

        is_valid, error = Validator.validate_student_date_range(student)

        self.assertFalse(is_valid)
        self.assertIn("Invalid date format", error)

    def test_validate_assignment_conflicts_no_conflicts(self):
        """Test assignment validation with no conflicts."""
        assignments = [
            Assignment(student_id="s1", seat_id="seat_001", day="monday", week="2025-W43"),
            Assignment(student_id="s2", seat_id="seat_002", day="monday", week="2025-W43"),
        ]

        conflicts = Validator.validate_assignment_conflicts(assignments)

        self.assertEqual(len(conflicts), 0)

    def test_validate_assignment_conflicts_duplicate_seat(self):
        """Test detection of duplicate seat assignment."""
        assignments = [
            Assignment(student_id="s1", seat_id="seat_001", day="monday", week="2025-W43"),
            Assignment(student_id="s2", seat_id="seat_001", day="monday", week="2025-W43"),
        ]

        conflicts = Validator.validate_assignment_conflicts(assignments)

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'duplicate_seat')
        self.assertEqual(conflicts[0]['seat_id'], 'seat_001')

    def test_validate_assignment_conflicts_duplicate_student(self):
        """Test detection of duplicate student assignment."""
        assignments = [
            Assignment(student_id="s1", seat_id="seat_001", day="monday", week="2025-W43"),
            Assignment(student_id="s1", seat_id="seat_002", day="monday", week="2025-W43"),
        ]

        conflicts = Validator.validate_assignment_conflicts(assignments)

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'duplicate_student')
        self.assertEqual(conflicts[0]['student_id'], 's1')

    def test_validate_assignment_conflicts_different_days_no_conflict(self):
        """Test that same seat on different days is not a conflict."""
        assignments = [
            Assignment(student_id="s1", seat_id="seat_001", day="monday", week="2025-W43"),
            Assignment(student_id="s2", seat_id="seat_001", day="tuesday", week="2025-W43"),
        ]

        conflicts = Validator.validate_assignment_conflicts(assignments)

        self.assertEqual(len(conflicts), 0)

    def test_validate_assignment_conflicts_different_weeks_no_conflict(self):
        """Test that same seat in different weeks is not a conflict."""
        assignments = [
            Assignment(student_id="s1", seat_id="seat_001", day="monday", week="2025-W43"),
            Assignment(student_id="s2", seat_id="seat_001", day="monday", week="2025-W44"),
        ]

        conflicts = Validator.validate_assignment_conflicts(assignments)

        self.assertEqual(len(conflicts), 0)

    def test_validate_all_seats_in_rooms_valid(self):
        """Test validation of all seats within rooms."""
        rooms = [
            Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f"),
        ]
        seats = [
            Seat(id="seat_001", room_id="room_001", number=1, x=10, y=10),
            Seat(id="seat_002", room_id="room_001", number=2, x=20, y=20),
        ]

        is_valid, invalid_seats = Validator.validate_all_seats_in_rooms(seats, rooms)

        self.assertTrue(is_valid)
        self.assertEqual(len(invalid_seats), 0)

    def test_validate_all_seats_in_rooms_invalid(self):
        """Test validation with seats outside room bounds."""
        rooms = [
            Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f"),
        ]
        seats = [
            Seat(id="seat_001", room_id="room_001", number=1, x=10, y=10),
            Seat(id="seat_002", room_id="room_001", number=2, x=200, y=200),
        ]

        is_valid, invalid_seats = Validator.validate_all_seats_in_rooms(seats, rooms)

        self.assertFalse(is_valid)
        self.assertEqual(len(invalid_seats), 1)
        self.assertIn("seat_002", invalid_seats)

    def test_validate_all_seats_in_rooms_missing_room(self):
        """Test validation with seat referencing non-existent room."""
        rooms = [
            Room(id="room_001", name="Room A", x=0, y=0, width=100, height=100, color="#1e3a5f"),
        ]
        seats = [
            Seat(id="seat_001", room_id="room_999", number=1, x=10, y=10),
        ]

        is_valid, invalid_seats = Validator.validate_all_seats_in_rooms(seats, rooms)

        self.assertFalse(is_valid)
        self.assertEqual(len(invalid_seats), 1)
        self.assertIn("seat_001", invalid_seats)


if __name__ == '__main__':
    unittest.main()
