"""Data models for Sitzplatz-Manager."""

from .room import Room
from .seat import Seat
from .student import Student
from .assignment import Assignment

__all__ = ["Room", "Seat", "Student", "Assignment"]
