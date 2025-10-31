"""
Unit tests for the AssignmentEngine module.

Tests the automatic seat assignment algorithm including:
- Priority sorting
- Seat matching (previous, requirements, fallback)
- Conflict tracking
- Week-level assignment
- Statistics calculation
"""

import unittest
from logic.assignment_engine import AssignmentEngine
from models.student import Student
from models.seat import Seat
from models.assignment import Assignment


class TestAssignmentEngine(unittest.TestCase):
    """Test cases for the AssignmentEngine class."""

    def test_assign_day_empty_students(self):
        """Test assignment with no students."""
        students = []
        seats = [Seat(id="s1", room_id="r1", number=1, x=0, y=0)]

        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        self.assertEqual(len(assignments), 0)
        self.assertEqual(len(conflicts), 0)

    def test_assign_day_empty_seats(self):
        """Test assignment with no seats."""
        students = [Student(id="st1", name="Alice", weekly_pattern={"monday": True})]
        seats = []

        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        self.assertEqual(len(assignments), 0)
        self.assertEqual(len(conflicts), 1)
        self.assertIn("st1", conflicts)

    def test_assign_day_single_student_single_seat(self):
        """Test simple assignment: one student, one seat."""
        students = [Student(id="st1", name="Alice", weekly_pattern={"monday": True})]
        seats = [Seat(id="s1", room_id="r1", number=1, x=0, y=0)]

        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        self.assertEqual(len(assignments), 1)
        self.assertEqual(len(conflicts), 0)
        self.assertEqual(assignments[0].student_id, "st1")
        self.assertEqual(assignments[0].seat_id, "s1")
        self.assertEqual(assignments[0].day, "monday")
        self.assertEqual(assignments[0].week, "2025-W43")

    def test_assign_day_sufficient_capacity(self):
        """Test assignment with sufficient seats for all students."""
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
            Seat(id="s3", room_id="r1", number=3, x=20, y=0),
        ]

        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        self.assertEqual(len(assignments), 2)
        self.assertEqual(len(conflicts), 0)

    def test_assign_day_overbooking(self):
        """Test assignment with more students than seats (overbooking)."""
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
            Student(id="st3", name="Charlie", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]

        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        self.assertEqual(len(assignments), 2)
        self.assertEqual(len(conflicts), 1)
        self.assertIn("st3", conflicts)  # Charlie is last alphabetically

    def test_assign_day_students_not_available(self):
        """Test that students not available on day are not assigned."""
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": False, "tuesday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]

        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43"
        )

        # Only Bob should be assigned
        self.assertEqual(len(assignments), 1)
        self.assertEqual(len(conflicts), 0)
        self.assertEqual(assignments[0].student_id, "st2")

    def test_get_priority_sort_key_with_previous(self):
        """Test priority sorting: students with previous seats first."""
        student1 = Student(id="st1", name="Bob")
        student2 = Student(id="st2", name="Alice")
        prev_map = {"st2": "s1"}  # Alice had previous seat

        key1 = AssignmentEngine.get_priority_sort_key(student1, prev_map)
        key2 = AssignmentEngine.get_priority_sort_key(student2, prev_map)

        # Alice (with previous) should have lower key (higher priority)
        self.assertLess(key2, key1)

    def test_get_priority_sort_key_alphabetical(self):
        """Test priority sorting: alphabetical when no previous seats."""
        student1 = Student(id="st1", name="Bob")
        student2 = Student(id="st2", name="Alice")
        prev_map = {}  # No previous assignments

        key1 = AssignmentEngine.get_priority_sort_key(student1, prev_map)
        key2 = AssignmentEngine.get_priority_sort_key(student2, prev_map)

        # Alice should come before Bob alphabetically
        self.assertLess(key2, key1)

    def test_find_seat_for_student_no_seats(self):
        """Test seat finding with no available seats."""
        student = Student(id="st1", name="Alice")
        available_seats = []

        seat = AssignmentEngine.find_seat_for_student(student, available_seats)

        self.assertIsNone(seat)

    def test_find_seat_for_student_previous_seat_preferred(self):
        """Test that previous seat is preferred when available."""
        student = Student(id="st1", name="Alice")
        seat1 = Seat(id="s1", room_id="r1", number=1, x=0, y=0)
        seat2 = Seat(id="s2", room_id="r1", number=2, x=10, y=0)
        available_seats = [seat1, seat2]

        seat = AssignmentEngine.find_seat_for_student(student, available_seats, previous_seat=seat2)

        self.assertEqual(seat.id, "s2")  # Should get previous seat

    def test_find_seat_for_student_requirements_match(self):
        """Test that seats matching requirements are preferred."""
        student = Student(id="st1", name="Alice", requirements=["near_window"])
        seat1 = Seat(id="s1", room_id="r1", number=1, x=0, y=0, properties={})
        seat2 = Seat(id="s2", room_id="r1", number=2, x=10, y=0, properties={"near_window": True})
        available_seats = [seat1, seat2]

        seat = AssignmentEngine.find_seat_for_student(student, available_seats)

        self.assertEqual(seat.id, "s2")  # Should get matching seat

    def test_find_seat_for_student_partial_match(self):
        """Test partial requirements matching."""
        student = Student(id="st1", name="Alice", requirements=["near_window", "near_door"])
        seat1 = Seat(id="s1", room_id="r1", number=1, x=0, y=0, properties={})
        seat2 = Seat(id="s2", room_id="r1", number=2, x=10, y=0, properties={"near_window": True})
        available_seats = [seat1, seat2]

        seat = AssignmentEngine.find_seat_for_student(student, available_seats)

        self.assertEqual(seat.id, "s2")  # Should get partial match

    def test_find_seat_for_student_fallback(self):
        """Test fallback to any seat when no requirements match."""
        student = Student(id="st1", name="Alice", requirements=["near_window"])
        seat1 = Seat(id="s1", room_id="r1", number=1, x=0, y=0, properties={})
        available_seats = [seat1]

        seat = AssignmentEngine.find_seat_for_student(student, available_seats)

        self.assertEqual(seat.id, "s1")  # Should get any available seat

    def test_assign_day_with_previous_assignments(self):
        """Test that previous seat assignments are respected."""
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]
        prev_assignments = [
            Assignment(student_id="st1", seat_id="s2", day="monday", week="2025-W42"),
            Assignment(student_id="st2", seat_id="s1", day="monday", week="2025-W42"),
        ]

        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43",
            previous_assignments=prev_assignments
        )

        # Check that students got their previous seats
        assignment_map = {a.student_id: a.seat_id for a in assignments}
        self.assertEqual(assignment_map["st1"], "s2")
        self.assertEqual(assignment_map["st2"], "s1")

    def test_assign_week_all_days(self):
        """Test week-level assignment covers all days."""
        students = [Student(id="st1", name="Alice", weekly_pattern={
            "monday": True, "tuesday": True, "wednesday": True,
            "thursday": True, "friday": True, "saturday": False, "sunday": False
        })]
        seats = [Seat(id="s1", room_id="r1", number=1, x=0, y=0)]

        assignments, conflicts = AssignmentEngine.assign_week(
            students=students,
            seats=seats,
            week="2025-W43"
        )

        # Check that all 7 days are present
        self.assertEqual(len(assignments), 7)
        self.assertEqual(len(conflicts), 7)

        # Check weekday assignments
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            self.assertEqual(len(assignments[day]), 1)
            self.assertEqual(len(conflicts[day]), 0)

        # Check weekend (no assignment)
        for day in ["saturday", "sunday"]:
            self.assertEqual(len(assignments[day]), 0)
            self.assertEqual(len(conflicts[day]), 0)

    def test_assign_week_with_previous_week(self):
        """Test week assignment with previous week's data."""
        students = [Student(id="st1", name="Alice", weekly_pattern={"monday": True})]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]
        previous_week = {
            "monday": [Assignment(student_id="st1", seat_id="s2", day="monday", week="2025-W42")]
        }

        assignments, conflicts = AssignmentEngine.assign_week(
            students=students,
            seats=seats,
            week="2025-W43",
            previous_assignments=previous_week
        )

        # Alice should get her previous seat (s2)
        self.assertEqual(assignments["monday"][0].seat_id, "s2")

    def test_get_assignment_statistics(self):
        """Test statistics calculation."""
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True, "tuesday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]
        assignments = {
            "monday": [
                Assignment(student_id="st1", seat_id="s1", day="monday", week="2025-W43"),
                Assignment(student_id="st2", seat_id="s2", day="monday", week="2025-W43"),
            ],
            "tuesday": [
                Assignment(student_id="st1", seat_id="s1", day="tuesday", week="2025-W43"),
            ],
        }
        conflicts = {
            "monday": [],
            "tuesday": [],
        }

        stats = AssignmentEngine.get_assignment_statistics(
            assignments=assignments,
            conflicts=conflicts,
            students=students,
            seats=seats
        )

        self.assertEqual(stats['total_assignments'], 3)
        self.assertEqual(stats['total_conflicts'], 0)
        self.assertEqual(stats['total_seats'], 2)
        self.assertEqual(stats['total_students'], 2)
        self.assertGreater(stats['occupancy_rate'], 0)

    def test_get_assignment_statistics_with_conflicts(self):
        """Test statistics with conflicts."""
        students = [Student(id="st1", name="Alice", weekly_pattern={"monday": True})]
        seats = []
        assignments = {"monday": []}
        conflicts = {"monday": ["st1"]}

        stats = AssignmentEngine.get_assignment_statistics(
            assignments=assignments,
            conflicts=conflicts,
            students=students,
            seats=seats
        )

        self.assertEqual(stats['total_assignments'], 0)
        self.assertEqual(stats['total_conflicts'], 1)
        self.assertEqual(stats['days_with_conflicts'], 1)

    def test_assign_day_priority_order(self):
        """Test that students with previous seats get priority."""
        students = [
            Student(id="st1", name="Alice", weekly_pattern={"monday": True}),
            Student(id="st2", name="Bob", weekly_pattern={"monday": True}),
            Student(id="st3", name="Charlie", weekly_pattern={"monday": True}),
        ]
        seats = [
            Seat(id="s1", room_id="r1", number=1, x=0, y=0),
            Seat(id="s2", room_id="r1", number=2, x=10, y=0),
        ]
        # Charlie had a previous seat
        prev_assignments = [
            Assignment(student_id="st3", seat_id="s1", day="monday", week="2025-W42"),
        ]

        assignments, conflicts = AssignmentEngine.assign_day(
            students=students,
            seats=seats,
            day="monday",
            week="2025-W43",
            previous_assignments=prev_assignments
        )

        # Charlie should get assigned (has previous), one of Alice/Bob should not
        assignment_ids = [a.student_id for a in assignments]
        self.assertIn("st3", assignment_ids)
        self.assertEqual(len(conflicts), 1)


if __name__ == '__main__':
    unittest.main()
