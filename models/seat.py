"""Seat model for Sitzplatz-Manager."""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Seat:
    """Represents a seat in a room.

    Attributes:
        id: Unique identifier (e.g., "seat_001")
        room_id: Reference to Room.id
        number: Seat number within room (e.g., 1, 2, 3)
        x: Canvas X position relative to room
        y: Canvas Y position relative to room
        properties: Flexible properties (e.g., {"near_window": True})
    """
    id: str
    room_id: str
    number: int
    x: float
    y: float
    properties: Dict[str, Any] = field(default_factory=dict)

    def get_display_name(self) -> str:
        """Return formatted display name for UI.

        Returns:
            Formatted seat name (e.g., "Seat 1")
        """
        return f"Seat {self.number}"

    def has_property(self, prop: str) -> bool:
        """Check if seat has a specific property.

        Args:
            prop: Property name to check

        Returns:
            True if property exists and is truthy, False otherwise
        """
        return self.properties.get(prop, False)

    def to_dict(self) -> dict:
        """Convert seat to dictionary for JSON serialization.

        Returns:
            Dictionary representation of seat
        """
        return {
            "id": self.id,
            "room_id": self.room_id,
            "number": self.number,
            "x": self.x,
            "y": self.y,
            "properties": self.properties
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Seat":
        """Create Seat instance from dictionary.

        Args:
            data: Dictionary with seat data

        Returns:
            Seat instance
        """
        return cls(
            id=data["id"],
            room_id=data["room_id"],
            number=data["number"],
            x=data["x"],
            y=data["y"],
            properties=data.get("properties", {})
        )
