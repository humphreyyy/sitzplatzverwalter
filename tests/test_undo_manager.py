"""Unit tests for UndoManager."""

import unittest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.undo_manager import UndoManager, StateSnapshot


class TestUndoManager(unittest.TestCase):
    """Tests for UndoManager class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.undo_manager = UndoManager(max_states=50)
        self.sample_state = {
            "floorplan": {"rooms": [], "seats": []},
            "students": [],
            "assignments": {},
            "metadata": {"last_user": "test"}
        }

    def test_initialization(self) -> None:
        """Test UndoManager initialization."""
        self.assertIsNotNone(self.undo_manager)
        self.assertEqual(self.undo_manager.max_states, 50)
        self.assertEqual(len(self.undo_manager.undo_stack), 0)
        self.assertEqual(len(self.undo_manager.redo_stack), 0)

    def test_push_state(self) -> None:
        """Test pushing a state to undo stack."""
        self.undo_manager.push_state(self.sample_state)

        self.assertEqual(len(self.undo_manager.undo_stack), 1)
        snapshot = self.undo_manager.undo_stack[0]
        self.assertIsInstance(snapshot, StateSnapshot)
        self.assertEqual(snapshot.floorplan, {"rooms": [], "seats": []})

    def test_push_multiple_states(self) -> None:
        """Test pushing multiple states."""
        state1 = self.sample_state.copy()
        state2 = self.sample_state.copy()
        state2["students"] = ["student1"]

        self.undo_manager.push_state(state1)
        self.undo_manager.push_state(state2)

        self.assertEqual(len(self.undo_manager.undo_stack), 2)

    def test_can_undo_empty(self) -> None:
        """Test undo availability when stack is empty."""
        self.assertFalse(self.undo_manager.can_undo())

    def test_can_undo_with_one_state(self) -> None:
        """Test undo availability with single state."""
        self.undo_manager.push_state(self.sample_state)
        # Need at least 2 states to undo (current + previous)
        self.assertFalse(self.undo_manager.can_undo())

    def test_can_undo_with_multiple_states(self) -> None:
        """Test undo availability with multiple states."""
        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.push_state(self.sample_state)
        self.assertTrue(self.undo_manager.can_undo())

    def test_undo_operation(self) -> None:
        """Test undo operation."""
        state1 = self.sample_state.copy()
        state2 = self.sample_state.copy()
        state2["students"] = ["student1"]

        self.undo_manager.push_state(state1)
        self.undo_manager.push_state(state2)

        # Undo from state2 to state1
        previous = self.undo_manager.undo()

        self.assertIsNotNone(previous)
        self.assertEqual(len(self.undo_manager.undo_stack), 1)
        self.assertEqual(len(self.undo_manager.redo_stack), 1)

    def test_undo_empty_returns_none(self) -> None:
        """Test undo on empty stack returns None."""
        result = self.undo_manager.undo()
        self.assertIsNone(result)

    def test_redo_operation(self) -> None:
        """Test redo operation."""
        state1 = self.sample_state.copy()
        state2 = self.sample_state.copy()
        state2["students"] = ["student1"]

        self.undo_manager.push_state(state1)
        self.undo_manager.push_state(state2)
        self.undo_manager.undo()

        # Redo back to state2
        redone = self.undo_manager.redo()

        self.assertIsNotNone(redone)
        self.assertEqual(redone["students"], ["student1"])
        self.assertEqual(len(self.undo_manager.undo_stack), 2)
        self.assertEqual(len(self.undo_manager.redo_stack), 0)

    def test_redo_empty_returns_none(self) -> None:
        """Test redo on empty stack returns None."""
        result = self.undo_manager.redo()
        self.assertIsNone(result)

    def test_can_redo_empty(self) -> None:
        """Test redo availability when stack is empty."""
        self.assertFalse(self.undo_manager.can_redo())

    def test_can_redo_after_undo(self) -> None:
        """Test redo availability after undo."""
        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.undo()

        self.assertTrue(self.undo_manager.can_redo())

    def test_redo_stack_cleared_on_new_action(self) -> None:
        """Test redo stack is cleared when new action is performed."""
        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.undo()

        self.assertTrue(self.undo_manager.can_redo())

        # New action should clear redo stack
        self.undo_manager.push_state(self.sample_state)

        self.assertFalse(self.undo_manager.can_redo())

    def test_max_states_limit(self) -> None:
        """Test maximum states limit enforcement."""
        undo_manager = UndoManager(max_states=5)

        # Push 10 states
        for i in range(10):
            state = self.sample_state.copy()
            state["students"] = [f"student{i}"]
            undo_manager.push_state(state)

        # Should only keep 5 most recent
        self.assertEqual(len(undo_manager.undo_stack), 5)

    def test_state_to_dict(self) -> None:
        """Test StateSnapshot to_dict conversion."""
        snapshot = StateSnapshot(
            timestamp=1234567890.0,
            floorplan={"rooms": []},
            students=[],
            assignments={},
            metadata={"user": "test"}
        )

        state_dict = snapshot.to_dict()
        self.assertIn("floorplan", state_dict)
        self.assertIn("students", state_dict)
        self.assertIn("assignments", state_dict)
        self.assertIn("metadata", state_dict)

    def test_clear_stacks(self) -> None:
        """Test clearing both stacks."""
        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.undo()

        self.assertTrue(len(self.undo_manager.undo_stack) > 0)
        self.assertTrue(len(self.undo_manager.redo_stack) > 0)

        self.undo_manager.clear()

        self.assertEqual(len(self.undo_manager.undo_stack), 0)
        self.assertEqual(len(self.undo_manager.redo_stack), 0)

    def test_get_undo_count(self) -> None:
        """Test undo count reporting."""
        self.assertEqual(self.undo_manager.get_undo_count(), 0)

        self.undo_manager.push_state(self.sample_state)
        self.assertEqual(self.undo_manager.get_undo_count(), 0)

        self.undo_manager.push_state(self.sample_state)
        self.assertEqual(self.undo_manager.get_undo_count(), 1)

    def test_get_redo_count(self) -> None:
        """Test redo count reporting."""
        self.assertEqual(self.undo_manager.get_redo_count(), 0)

        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.undo()

        self.assertEqual(self.undo_manager.get_redo_count(), 1)

    def test_get_state_info(self) -> None:
        """Test state info reporting."""
        self.undo_manager.push_state(self.sample_state)
        self.undo_manager.push_state(self.sample_state)

        info = self.undo_manager.get_state_info()

        self.assertIn("undo_available", info)
        self.assertIn("redo_available", info)
        self.assertIn("undo_count", info)
        self.assertIn("redo_count", info)
        self.assertIn("max_states", info)
        self.assertTrue(info["undo_available"])
        self.assertFalse(info["redo_available"])


if __name__ == "__main__":
    unittest.main()
