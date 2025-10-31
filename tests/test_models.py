"""Unit tests for data models."""

import unittest
from models import Room, Seat, Student, Assignment


class TestRoom(unittest.TestCase):
    """Tests for Room model."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.room = Room(
            id="room_001",
            name="Klassenraum A",
            x=50,
            y=50,
            width=400,
            height=300,
            color="#1e3a5f"
        )

    def test_room_creation(self) -> None:
        """Test room can be created with required attributes."""
        self.assertEqual(self.room.id, "room_001")
        self.assertEqual(self.room.name, "Klassenraum A")
        self.assertEqual(self.room.x, 50)
        self.assertEqual(self.room.y, 50)
        self.assertEqual(self.room.width, 400)
        self.assertEqual(self.room.height, 300)
        self.assertEqual(self.room.color, "#1e3a5f")

    def test_contains_point_inside(self) -> None:
        """Test point inside room is correctly detected."""
        self.assertTrue(self.room.contains_point(100, 100))
        self.assertTrue(self.room.contains_point(200, 200))
        self.assertTrue(self.room.contains_point(450, 350))

    def test_contains_point_outside(self) -> None:
        """Test point outside room is correctly detected."""
        self.assertFalse(self.room.contains_point(0, 0))
        self.assertFalse(self.room.contains_point(500, 400))
        self.assertFalse(self.room.contains_point(100, 400))

    def test_contains_point_boundary(self) -> None:
        """Test boundary points are correctly detected."""
        # Bottom-left corner
        self.assertTrue(self.room.contains_point(50, 50))
        # Top-right corner
        self.assertTrue(self.room.contains_point(450, 350))

    def test_room_to_dict(self) -> None:
        """Test room can be converted to dictionary."""
        room_dict = self.room.to_dict()
        self.assertEqual(room_dict["id"], "room_001")
        self.assertEqual(room_dict["name"], "Klassenraum A")
        self.assertEqual(room_dict["x"], 50)

    def test_room_from_dict(self) -> None:
        """Test room can be created from dictionary."""
        data = {
            "id": "room_002",
            "name": "Klassenraum B",
            "x": 100,
            "y": 100,
            "width": 500,
            "height": 400,
            "color": "#e31e24"
        }
        room = Room.from_dict(data)
        self.assertEqual(room.id, "room_002")
        self.assertEqual(room.name, "Klassenraum B")
        self.assertEqual(room.color, "#e31e24")

    def test_get_display_name(self) -> None:
        """Test display name is returned correctly."""
        self.assertEqual(self.room.get_display_name(), "Klassenraum A")


class TestSeat(unittest.TestCase):
    """Tests for Seat model."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.seat = Seat(
            id="seat_001",
            room_id="room_001",
            number=1,
            x=70,
            y=80,
            properties={"near_window": True, "near_door": False}
        )

    def test_seat_creation(self) -> None:
        """Test seat can be created with required attributes."""
        self.assertEqual(self.seat.id, "seat_001")
        self.assertEqual(self.seat.room_id, "room_001")
        self.assertEqual(self.seat.number, 1)
        self.assertEqual(self.seat.x, 70)
        self.assertEqual(self.seat.y, 80)

    def test_has_property(self) -> None:
        """Test seat property checking."""
        self.assertTrue(self.seat.has_property("near_window"))
        self.assertFalse(self.seat.has_property("near_door"))
        self.assertFalse(self.seat.has_property("nonexistent"))

    def test_get_display_name(self) -> None:
        """Test seat display name."""
        self.assertEqual(self.seat.get_display_name(), "Seat 1")

    def test_seat_to_dict(self) -> None:
        """Test seat can be converted to dictionary."""
        seat_dict = self.seat.to_dict()
        self.assertEqual(seat_dict["id"], "seat_001")
        self.assertEqual(seat_dict["room_id"], "room_001")
        self.assertEqual(seat_dict["number"], 1)
        self.assertEqual(seat_dict["properties"]["near_window"], True)

    def test_seat_from_dict(self) -> None:
        """Test seat can be created from dictionary."""
        data = {
            "id": "seat_002",
            "room_id": "room_001",
            "number": 2,
            "x": 100,
            "y": 100,
            "properties": {"near_window": False}
        }
        seat = Seat.from_dict(data)
        self.assertEqual(seat.id, "seat_002")
        self.assertEqual(seat.number, 2)


class TestStudent(unittest.TestCase):
    """Tests for Student model."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.student = Student(
            id="student_001",
            name="Alice Schmidt",
            weekly_pattern={
                "monday": True,
                "tuesday": True,
                "wednesday": False,
                "thursday": True,
                "friday": True,
                "saturday": False,
                "sunday": False
            },
            valid_from="2025-10-01",
            valid_until="ongoing",
            requirements=["near_window"]
        )

    def test_student_creation(self) -> None:
        """Test student can be created with required attributes."""
        self.assertEqual(self.student.id, "student_001")
        self.assertEqual(self.student.name, "Alice Schmidt")
        self.assertTrue(self.student.weekly_pattern["monday"])
        self.assertFalse(self.student.weekly_pattern["wednesday"])

    def test_is_available_on(self) -> None:
        """Test student availability checking."""
        self.assertTrue(self.student.is_available_on("monday"))
        self.assertTrue(self.student.is_available_on("Monday"))  # Case insensitive
        self.assertFalse(self.student.is_available_on("wednesday"))
        self.assertFalse(self.student.is_available_on("nonexistent"))

    def test_has_requirement(self) -> None:
        """Test student requirement checking."""
        self.assertTrue(self.student.has_requirement("near_window"))
        self.assertFalse(self.student.has_requirement("near_door"))

    def test_get_display_name(self) -> None:
        """Test student display name."""
        self.assertEqual(self.student.get_display_name(), "Alice Schmidt")

    def test_student_to_dict(self) -> None:
        """Test student can be converted to dictionary."""
        student_dict = self.student.to_dict()
        self.assertEqual(student_dict["id"], "student_001")
        self.assertEqual(student_dict["name"], "Alice Schmidt")
        self.assertEqual(student_dict["valid_from"], "2025-10-01")
        self.assertIn("near_window", student_dict["requirements"])

    def test_student_from_dict(self) -> None:
        """Test student can be created from dictionary."""
        data = {
            "id": "student_002",
            "name": "Bob Mueller",
            "weekly_pattern": {"monday": True, "tuesday": False},
            "valid_from": "2025-10-01",
            "valid_until": "2025-12-31",
            "requirements": []
        }
        student = Student.from_dict(data)
        self.assertEqual(student.id, "student_002")
        self.assertEqual(student.name, "Bob Mueller")
        self.assertEqual(student.valid_until, "2025-12-31")


class TestAssignment(unittest.TestCase):
    """Tests for Assignment model."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.assignment = Assignment(
            student_id="student_001",
            seat_id="seat_001",
            day="monday",
            week="2025-W43"
        )

    def test_assignment_creation(self) -> None:
        """Test assignment can be created with required attributes."""
        self.assertEqual(self.assignment.student_id, "student_001")
        self.assertEqual(self.assignment.seat_id, "seat_001")
        self.assertEqual(self.assignment.day, "monday")
        self.assertEqual(self.assignment.week, "2025-W43")

    def test_get_key(self) -> None:
        """Test assignment key generation."""
        key = self.assignment.get_key()
        self.assertEqual(key, "2025-W43_monday_student_001")

    def test_get_display_name(self) -> None:
        """Test assignment display name."""
        display = self.assignment.get_display_name()
        self.assertIn("student_001", display)
        self.assertIn("seat_001", display)

    def test_assignment_to_dict(self) -> None:
        """Test assignment can be converted to dictionary."""
        assignment_dict = self.assignment.to_dict()
        self.assertEqual(assignment_dict["student_id"], "student_001")
        self.assertEqual(assignment_dict["seat_id"], "seat_001")
        self.assertEqual(assignment_dict["day"], "monday")
        self.assertEqual(assignment_dict["week"], "2025-W43")

    def test_assignment_from_dict(self) -> None:
        """Test assignment can be created from dictionary."""
        data = {
            "student_id": "student_002",
            "seat_id": "seat_002",
            "day": "tuesday",
            "week": "2025-W44"
        }
        assignment = Assignment.from_dict(data)
        self.assertEqual(assignment.student_id, "student_002")
        self.assertEqual(assignment.day, "tuesday")


if __name__ == "__main__":
    unittest.main()
