"""
Assignment engine for automatic seat allocation.

This module implements the core algorithm for intelligently assigning students
to seats based on:
- Previous seat assignments (continuity)
- Student requirements (seat properties)
- Availability patterns (weekly schedules)
- Conflict tracking and resolution
"""

from typing import List, Dict, Tuple, Optional, Set
from models.student import Student
from models.seat import Seat
from models.assignment import Assignment


class AssignmentEngine:
    """Core algorithm for automatic seat assignment."""

    @staticmethod
    def assign_week(
        students: List[Student],
        seats: List[Seat],
        week: str,
        previous_assignments: Optional[Dict[str, List[Assignment]]] = None
    ) -> Tuple[Dict[str, List[Assignment]], Dict[str, List[str]]]:
        """Assign students to seats for an entire week.

        Args:
            students: List of all students
            seats: List of all available seats
            week: Week identifier (e.g., "2025-W43")
            previous_assignments: Optional dict of previous week's assignments by day

        Returns:
            Tuple of (assignments, conflicts) where:
                assignments: Dict mapping day -> list of Assignment objects
                conflicts: Dict mapping day -> list of unassigned student IDs
        """
        if previous_assignments is None:
            previous_assignments = {}

        # Days of the week (lowercase, as used in models)
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        week_assignments = {}
        week_conflicts = {}

        for day in days:
            # Get previous assignments for this day if available
            prev_day_assignments = previous_assignments.get(day, [])

            # Assign seats for this day
            day_assignments, day_conflicts = AssignmentEngine.assign_day(
                students=students,
                seats=seats,
                day=day,
                week=week,
                previous_assignments=prev_day_assignments
            )

            week_assignments[day] = day_assignments
            week_conflicts[day] = day_conflicts

        return (week_assignments, week_conflicts)

    @staticmethod
    def assign_day(
        students: List[Student],
        seats: List[Seat],
        day: str,
        week: str,
        previous_assignments: Optional[List[Assignment]] = None
    ) -> Tuple[List[Assignment], List[str]]:
        """Assign students to seats for a single day.

        Algorithm:
        1. Filter students available on this day
        2. Sort by priority (previous seat holders first, then alphabetically)
        3. For each student, find best matching seat:
           - Try previous seat first
           - Try seats matching all requirements
           - Try any free seat
        4. Track conflicts (unassigned students)

        Args:
            students: List of all students
            seats: List of all available seats
            day: Day of week (e.g., "monday") - lowercase
            week: Week identifier (e.g., "2025-W43")
            previous_assignments: Optional list of previous assignments for this day

        Returns:
            Tuple of (assignments, conflicts) where:
                assignments: List of Assignment objects for this day
                conflicts: List of student IDs that couldn't be assigned
        """
        if previous_assignments is None:
            previous_assignments = []

        # Build previous assignment lookup: student_id -> seat_id
        prev_assignment_map = {
            a.student_id: a.seat_id for a in previous_assignments
        }

        # Filter students available on this day
        available_students = [s for s in students if s.is_available_on(day)]

        # Sort students by priority
        sorted_students = sorted(
            available_students,
            key=lambda s: AssignmentEngine.get_priority_sort_key(s, prev_assignment_map)
        )

        # Track available seats (initially all seats)
        available_seats = seats.copy()
        assignments = []
        conflicts = []

        # Assign each student
        for student in sorted_students:
            # Get previous seat if exists
            prev_seat_id = prev_assignment_map.get(student.id)
            prev_seat = None
            if prev_seat_id:
                prev_seat = next((s for s in available_seats if s.id == prev_seat_id), None)

            # Find best seat for student
            assigned_seat = AssignmentEngine.find_seat_for_student(
                student=student,
                available_seats=available_seats,
                previous_seat=prev_seat
            )

            if assigned_seat:
                # Create assignment
                assignment = Assignment(
                    student_id=student.id,
                    seat_id=assigned_seat.id,
                    day=day,
                    week=week
                )
                assignments.append(assignment)

                # Remove seat from available pool
                available_seats.remove(assigned_seat)
            else:
                # Could not assign - add to conflicts
                conflicts.append(student.id)

        return (assignments, conflicts)

    @staticmethod
    def get_priority_sort_key(student: Student, prev_assignment_map: Dict[str, str]) -> Tuple[int, str]:
        """Generate sort key for student priority.

        Priority order:
        1. Students with previous seat assignments (priority 0)
        2. Students without previous seats (priority 1)
        3. Within each priority level, sort alphabetically by name

        Args:
            student: Student to generate key for
            prev_assignment_map: Dict mapping student_id -> seat_id for previous assignments

        Returns:
            Tuple (priority_level, name) for sorting
                Lower priority_level = higher priority
        """
        # Priority 0: Had previous seat
        # Priority 1: No previous seat
        has_previous = 0 if student.id in prev_assignment_map else 1

        return (has_previous, student.name)

    @staticmethod
    def find_seat_for_student(
        student: Student,
        available_seats: List[Seat],
        previous_seat: Optional[Seat] = None
    ) -> Optional[Seat]:
        """Find the best matching seat for a student.

        Preference order:
        1. Previous seat (if available and student had one)
        2. Seat matching ALL student requirements
        3. Seat matching SOME requirements (best partial match)
        4. Any available seat

        Args:
            student: Student to find seat for
            available_seats: List of seats still available
            previous_seat: Student's previous seat (if any)

        Returns:
            Best matching Seat, or None if no seats available
        """
        if not available_seats:
            return None

        # 1. Try previous seat first (if available)
        if previous_seat and previous_seat in available_seats:
            return previous_seat

        # 2. Try seats matching ALL requirements
        if student.requirements:
            perfect_matches = [
                seat for seat in available_seats
                if all(seat.has_property(req) for req in student.requirements)
            ]
            if perfect_matches:
                return perfect_matches[0]  # Return first perfect match

            # 3. Try partial matches (seats matching SOME requirements)
            partial_matches = []
            for seat in available_seats:
                match_count = sum(1 for req in student.requirements if seat.has_property(req))
                if match_count > 0:
                    partial_matches.append((match_count, seat))

            if partial_matches:
                # Sort by match count (descending) and return best
                partial_matches.sort(key=lambda x: x[0], reverse=True)
                return partial_matches[0][1]

        # 4. Fallback: return any available seat
        return available_seats[0] if available_seats else None

    @staticmethod
    def get_assignment_statistics(
        assignments: Dict[str, List[Assignment]],
        conflicts: Dict[str, List[str]],
        students: List[Student],
        seats: List[Seat]
    ) -> Dict[str, any]:
        """Calculate statistics about assignments.

        Args:
            assignments: Assignment results by day
            conflicts: Conflict results by day
            students: All students
            seats: All seats

        Returns:
            Dictionary with statistics:
                - total_assignments: Total assignments across all days
                - total_conflicts: Total conflicts across all days
                - occupancy_rate: Average seat occupancy percentage
                - days_with_conflicts: Number of days with conflicts
                - conflict_rate: Percentage of student-days with conflicts
        """
        total_assignments = sum(len(day_assigns) for day_assigns in assignments.values())
        total_conflicts = sum(len(day_conflicts) for day_conflicts in conflicts.values())

        # Calculate occupancy rate
        total_seats = len(seats) * 7  # 7 days
        occupancy_rate = (total_assignments / total_seats * 100) if total_seats > 0 else 0

        # Count days with conflicts
        days_with_conflicts = sum(1 for conflicts_list in conflicts.values() if conflicts_list)

        # Calculate conflict rate
        total_student_days = 0
        for student in students:
            total_student_days += sum(1 for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                                     if student.is_available_on(day))

        conflict_rate = (total_conflicts / total_student_days * 100) if total_student_days > 0 else 0

        return {
            'total_assignments': total_assignments,
            'total_conflicts': total_conflicts,
            'occupancy_rate': round(occupancy_rate, 2),
            'days_with_conflicts': days_with_conflicts,
            'conflict_rate': round(conflict_rate, 2),
            'total_seats': len(seats),
            'total_students': len(students)
        }
