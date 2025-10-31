"""
Business rule validation for the Sitzplatz-Manager application.

This module provides validators for:
- Room overlap detection
- Seat positioning within rooms
- Capacity checking (overbooking detection)
- Student date range validation
- Assignment conflict detection
"""

from datetime import datetime
from typing import List, Tuple, Dict, Optional
from models.room import Room
from models.seat import Seat
from models.student import Student
from models.assignment import Assignment


class Validator:
    """Business rule validator for seating management."""

    @staticmethod
    def validate_room_overlap(rooms: List[Room]) -> Tuple[bool, List[Tuple[str, str]]]:
        """Check if any rooms overlap on the canvas.

        Args:
            rooms: List of Room objects to check

        Returns:
            Tuple of (is_valid, conflicts) where:
                is_valid: True if no overlaps detected, False otherwise
                conflicts: List of tuples (room1_id, room2_id) that overlap
        """
        conflicts = []

        for i, room1 in enumerate(rooms):
            for room2 in rooms[i+1:]:
                # Check if rectangles overlap
                # Two rectangles DON'T overlap if one is completely to the left/right/above/below the other
                # So they DO overlap if NONE of these conditions are true
                if not (
                    room1.x + room1.width <= room2.x or  # room1 is completely left of room2
                    room2.x + room2.width <= room1.x or  # room2 is completely left of room1
                    room1.y + room1.height <= room2.y or  # room1 is completely above room2
                    room2.y + room2.height <= room1.y     # room2 is completely above room1
                ):
                    conflicts.append((room1.id, room2.id))

        return (len(conflicts) == 0, conflicts)

    @staticmethod
    def validate_seat_in_room(seat: Seat, room: Room) -> bool:
        """Verify that a seat is positioned within its assigned room bounds.

        Args:
            seat: Seat object to validate
            room: Room object that should contain the seat

        Returns:
            True if seat is within room bounds, False otherwise
        """
        # Check if seat's room_id matches
        if seat.room_id != room.id:
            return False

        # Check if seat position is within room boundaries
        return room.contains_point(seat.x, seat.y)

    @staticmethod
    def validate_capacity(students: List[Student], seats: List[Seat], day: str) -> Tuple[bool, Dict[str, int]]:
        """Check if there are enough seats for all students on a given day.

        Args:
            students: List of all students
            seats: List of all available seats
            day: Day of week (e.g., "monday") - lowercase

        Returns:
            Tuple of (is_valid, details) where:
                is_valid: True if capacity is sufficient, False if overbooking
                details: Dict with 'students_count', 'seats_count', 'excess'
        """
        # Count students available on this day
        students_available = sum(1 for s in students if s.is_available_on(day))
        seats_count = len(seats)

        is_valid = students_available <= seats_count
        excess = max(0, students_available - seats_count)

        return (is_valid, {
            'students_count': students_available,
            'seats_count': seats_count,
            'excess': excess
        })

    @staticmethod
    def validate_student_date_range(student: Student) -> Tuple[bool, Optional[str]]:
        """Verify that a student's date range is valid.

        Checks that valid_from is before or equal to valid_until.
        If valid_until is "ongoing", it's always valid.

        Args:
            student: Student object to validate

        Returns:
            Tuple of (is_valid, error_message) where:
                is_valid: True if date range is valid, False otherwise
                error_message: Description of the issue, or None if valid
        """
        # "ongoing" is always valid
        if student.valid_until.lower() == "ongoing":
            return (True, None)

        try:
            # Parse dates in ISO format (YYYY-MM-DD)
            date_from = datetime.strptime(student.valid_from, "%Y-%m-%d")
            date_until = datetime.strptime(student.valid_until, "%Y-%m-%d")

            if date_from > date_until:
                return (False, f"valid_from ({student.valid_from}) is after valid_until ({student.valid_until})")

            return (True, None)

        except ValueError as e:
            return (False, f"Invalid date format: {str(e)}")

    @staticmethod
    def validate_assignment_conflicts(assignments: List[Assignment]) -> List[Dict[str, str]]:
        """Detect conflicts in assignments (same seat or student assigned multiple times).

        Conflicts occur when:
        1. Same seat is assigned to multiple students on same day/week
        2. Same student is assigned to multiple seats on same day/week

        Args:
            assignments: List of Assignment objects to check

        Returns:
            List of conflict dictionaries with 'type', 'day', 'week', and conflict details
        """
        conflicts = []

        # Group assignments by (week, day)
        assignments_by_day = {}
        for assignment in assignments:
            key = (assignment.week, assignment.day)
            if key not in assignments_by_day:
                assignments_by_day[key] = []
            assignments_by_day[key].append(assignment)

        # Check each day for conflicts
        for (week, day), day_assignments in assignments_by_day.items():
            # Check for duplicate seat assignments
            seat_usage = {}
            for assignment in day_assignments:
                if assignment.seat_id in seat_usage:
                    conflicts.append({
                        'type': 'duplicate_seat',
                        'week': week,
                        'day': day,
                        'seat_id': assignment.seat_id,
                        'student_ids': [seat_usage[assignment.seat_id], assignment.student_id]
                    })
                else:
                    seat_usage[assignment.seat_id] = assignment.student_id

            # Check for duplicate student assignments
            student_usage = {}
            for assignment in day_assignments:
                if assignment.student_id in student_usage:
                    conflicts.append({
                        'type': 'duplicate_student',
                        'week': week,
                        'day': day,
                        'student_id': assignment.student_id,
                        'seat_ids': [student_usage[assignment.student_id], assignment.seat_id]
                    })
                else:
                    student_usage[assignment.student_id] = assignment.seat_id

        return conflicts

    @staticmethod
    def validate_all_seats_in_rooms(seats: List[Seat], rooms: List[Room]) -> Tuple[bool, List[str]]:
        """Validate that all seats are properly positioned within their assigned rooms.

        Args:
            seats: List of all seats to validate
            rooms: List of all rooms

        Returns:
            Tuple of (is_valid, invalid_seat_ids) where:
                is_valid: True if all seats are valid, False otherwise
                invalid_seat_ids: List of seat IDs that are not in their rooms
        """
        # Create room lookup dictionary
        room_dict = {room.id: room for room in rooms}

        invalid_seats = []

        for seat in seats:
            # Check if room exists
            if seat.room_id not in room_dict:
                invalid_seats.append(seat.id)
                continue

            # Check if seat is within room bounds
            room = room_dict[seat.room_id]
            if not Validator.validate_seat_in_room(seat, room):
                invalid_seats.append(seat.id)

        return (len(invalid_seats) == 0, invalid_seats)
