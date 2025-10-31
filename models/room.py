"""Room model for Sitzplatz-Manager."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Room:
    """Represents a classroom or room in the floorplan.

    Attributes:
        id: Unique identifier (e.g., "room_001")
        name: Display name (e.g., "Klassenraum A")
        x: Canvas X position in pixels
        y: Canvas Y position in pixels
        width: Room width in pixels
        height: Room height in pixels
        color: Hex color for drawing (e.g., "#1e3a5f")
    """
    id: str
    name: str
    x: float
    y: float
    width: float
    height: float
    color: str = "#1e3a5f"

    def contains_point(self, px: float, py: float) -> bool:
        """Check if point (px, py) is within room bounds.

        Args:
            px: X coordinate to check
            py: Y coordinate to check

        Returns:
            True if point is inside room, False otherwise
        """
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)

    def get_display_name(self) -> str:
        """Return formatted display name for UI.

        Returns:
            Formatted room name
        """
        return self.name

    def to_dict(self) -> dict:
        """Convert room to dictionary for JSON serialization.

        Returns:
            Dictionary representation of room
        """
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "color": self.color
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Room":
        """Create Room instance from dictionary.

        Args:
            data: Dictionary with room data

        Returns:
            Room instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
            color=data.get("color", "#1e3a5f")
        )
