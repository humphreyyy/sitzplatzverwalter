"""UndoManager handles undo/redo state management."""

import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import logging

from config import UNDO_STACK_MAX

logger = logging.getLogger(__name__)


@dataclass
class StateSnapshot:
    """Represents a snapshot of application state at a point in time.

    Attributes:
        timestamp: When snapshot was taken (Unix timestamp)
        floorplan: Complete floorplan state (rooms and seats)
        students: All student records
        assignments: All assignments for all weeks
        metadata: Last modified user, etc
    """
    timestamp: float
    floorplan: Dict[str, Any]
    students: List[Dict[str, Any]]
    assignments: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "floorplan": self.floorplan,
            "students": self.students,
            "assignments": self.assignments,
            "metadata": self.metadata
        }


class UndoManager:
    """Manages undo/redo state stacks with memory bounds.

    Provides:
    - Stack-based undo/redo system
    - Memory-bounded history (max 50 states)
    - State snapshot capture and restoration
    """

    def __init__(self, max_states: int = UNDO_STACK_MAX):
        """Initialize UndoManager.

        Args:
            max_states: Maximum number of states to keep in memory
        """
        self.undo_stack: List[StateSnapshot] = []
        self.redo_stack: List[StateSnapshot] = []
        self.max_states = max_states
        logger.debug(f"UndoManager initialized with max_states={max_states}")

    def push_state(self, state: Dict[str, Any]) -> None:
        """Add a new state to the undo stack.

        Clears redo stack when new action is performed.
        Removes oldest state if max capacity is reached.

        Args:
            state: Dictionary with complete application state
        """
        try:
            snapshot = StateSnapshot(
                timestamp=time.time(),
                floorplan=state.get("floorplan", {}),
                students=state.get("students", []),
                assignments=state.get("assignments", {}),
                metadata=state.get("metadata", {})
            )

            self.undo_stack.append(snapshot)

            # Keep only max_states most recent states
            if len(self.undo_stack) > self.max_states:
                removed = self.undo_stack.pop(0)
                logger.debug(f"Removed oldest state from undo stack")

            # Clear redo stack when new action is performed
            redo_count = len(self.redo_stack)
            self.redo_stack.clear()

            logger.debug(f"Pushed state. Undo: {len(self.undo_stack)}, Redo: {len(self.redo_stack)}")

        except Exception as e:
            logger.error(f"Error pushing state: {e}")
            raise

    def undo(self) -> Optional[Dict[str, Any]]:
        """Move current state to redo and return previous state.

        Returns:
            Previous state dictionary if available, None otherwise
        """
        try:
            if not self.undo_stack:
                logger.debug("Nothing to undo")
                return None

            # Move current state to redo
            current = self.undo_stack.pop()
            self.redo_stack.append(current)

            # Get previous state
            if self.undo_stack:
                previous = self.undo_stack[-1]
                logger.debug(f"Undo performed. Undo: {len(self.undo_stack)}, Redo: {len(self.redo_stack)}")
                return previous.to_dict()

            logger.debug("No previous state available")
            return None

        except Exception as e:
            logger.error(f"Error during undo: {e}")
            raise

    def redo(self) -> Optional[Dict[str, Any]]:
        """Move state from redo back to undo stack.

        Returns:
            Next state dictionary if available, None otherwise
        """
        try:
            if not self.redo_stack:
                logger.debug("Nothing to redo")
                return None

            # Move state from redo to undo
            state = self.redo_stack.pop()
            self.undo_stack.append(state)

            logger.debug(f"Redo performed. Undo: {len(self.undo_stack)}, Redo: {len(self.redo_stack)}")
            return state.to_dict()

        except Exception as e:
            logger.error(f"Error during redo: {e}")
            raise

    def can_undo(self) -> bool:
        """Check if undo operation is available.

        Returns:
            True if there are states to undo to, False otherwise
        """
        # Need at least one state in undo stack to undo
        return len(self.undo_stack) > 1

    def can_redo(self) -> bool:
        """Check if redo operation is available.

        Returns:
            True if there are states to redo to, False otherwise
        """
        return len(self.redo_stack) > 0

    def clear(self) -> None:
        """Clear all undo and redo stacks.

        Resets to initial empty state.
        """
        self.undo_stack.clear()
        self.redo_stack.clear()
        logger.debug("Undo/Redo stacks cleared")

    def get_undo_count(self) -> int:
        """Get number of undo states available.

        Returns:
            Number of states in undo stack
        """
        # Subtract 1 because first state is "current"
        return max(0, len(self.undo_stack) - 1)

    def get_redo_count(self) -> int:
        """Get number of redo states available.

        Returns:
            Number of states in redo stack
        """
        return len(self.redo_stack)

    def get_state_info(self) -> Dict[str, Any]:
        """Get information about current undo/redo state.

        Returns:
            Dictionary with undo/redo statistics
        """
        return {
            "undo_available": self.can_undo(),
            "redo_available": self.can_redo(),
            "undo_count": self.get_undo_count(),
            "redo_count": self.get_redo_count(),
            "max_states": self.max_states,
            "current_usage": f"{len(self.undo_stack)}/{self.max_states}"
        }
