"""Student model for Sitzplatz-Manager."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Student:
    """Represents a student in the system.

    Attributes:
        id: Unique identifier (e.g., "student_001")
        name: Student name
        weekly_pattern: Attendance per day: {"monday": True, "tuesday": False, ...}
        valid_from: Start date (ISO format: YYYY-MM-DD)
        valid_until: End date (ISO format: YYYY-MM-DD) or "ongoing"
        requirements: List of seat property requirements (e.g., ["near_window"])
    """
    id: str
    name: str
    weekly_pattern: Dict[str, bool] = field(default_factory=lambda: {
        "monday": True,
        "tuesday": True,
        "wednesday": True,
        "thursday": True,
        "friday": True,
        "saturday": False,
        "sunday": False
    })
    valid_from: str = "2025-01-01"
    valid_until: str = "ongoing"
    requirements: List[str] = field(default_factory=list)

    def is_available_on(self, day: str) -> bool:
        """Check if student is available on given day.

        Args:
            day: Day name (e.g., "monday", "tuesday") - case insensitive

        Returns:
            True if student is available on that day, False otherwise
        """
        day_lower = day.lower()
        return self.weekly_pattern.get(day_lower, False)

    def has_requirement(self, requirement: str) -> bool:
        """Check if student has a specific requirement.

        Args:
            requirement: Requirement name to check

        Returns:
            True if student has the requirement, False otherwise
        """
        return requirement in self.requirements

    def get_display_name(self) -> str:
        """Return formatted display name for UI.

        Returns:
            Student name
        """
        return self.name

    def to_dict(self) -> dict:
        """Convert student to dictionary for JSON serialization.

        Returns:
            Dictionary representation of student
        """
        return {
            "id": self.id,
            "name": self.name,
            "weekly_pattern": self.weekly_pattern,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "requirements": self.requirements
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        """Create Student instance from dictionary.

        Args:
            data: Dictionary with student data

        Returns:
            Student instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            weekly_pattern=data.get("weekly_pattern", {}),
            valid_from=data.get("valid_from", "2025-01-01"),
            valid_until=data.get("valid_until", "ongoing"),
            requirements=data.get("requirements", [])
        )
