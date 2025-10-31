"""Assignment model for Sitzplatz-Manager."""

from dataclasses import dataclass


@dataclass
class Assignment:
    """Represents an assignment of a student to a seat on a specific day.

    Attributes:
        student_id: Reference to Student.id
        seat_id: Reference to Seat.id
        day: Day of week (e.g., "monday", lowercase)
        week: Week identifier (e.g., "2025-W43")
    """
    student_id: str
    seat_id: str
    day: str
    week: str

    def get_key(self) -> str:
        """Return unique identifier for this assignment.

        Returns:
            Composite key for the assignment
        """
        return f"{self.week}_{self.day}_{self.student_id}"

    def get_display_name(self) -> str:
        """Return formatted display name for UI.

        Returns:
            Formatted assignment description
        """
        return f"Student {self.student_id} -> Seat {self.seat_id}"

    def to_dict(self) -> dict:
        """Convert assignment to dictionary for JSON serialization.

        Returns:
            Dictionary representation of assignment
        """
        return {
            "student_id": self.student_id,
            "seat_id": self.seat_id,
            "day": self.day,
            "week": self.week
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Assignment":
        """Create Assignment instance from dictionary.

        Args:
            data: Dictionary with assignment data

        Returns:
            Assignment instance
        """
        return cls(
            student_id=data["student_id"],
            seat_id=data["seat_id"],
            day=data["day"],
            week=data["week"]
        )
