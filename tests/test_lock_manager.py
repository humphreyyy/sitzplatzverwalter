"""Unit tests for LockManager."""

import unittest
import tempfile
import time
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.lock_manager import LockManager


class TestLockManager(unittest.TestCase):
    """Tests for LockManager class."""

    def setUp(self) -> None:
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lock_manager = LockManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        if self.lock_manager.lock_file.exists():
            self.lock_manager.release_lock()
        self.temp_dir.cleanup()

    def test_initialization(self) -> None:
        """Test LockManager initialization."""
        self.assertIsNotNone(self.lock_manager)
        self.assertFalse(self.lock_manager.lock_file.exists())

    def test_acquire_lock_success(self) -> None:
        """Test successful lock acquisition."""
        success, existing_lock = self.lock_manager.acquire_lock("user@PC-01")

        self.assertTrue(success)
        self.assertIsNone(existing_lock)
        self.assertTrue(self.lock_manager.lock_file.exists())

    def test_acquire_lock_already_locked(self) -> None:
        """Test acquiring lock when another user has it."""
        # First user acquires lock
        self.lock_manager.acquire_lock("user1@PC-01")

        # Second manager tries to acquire
        lock_manager2 = LockManager(self.temp_dir.name)
        success, existing_lock = lock_manager2.acquire_lock("user2@PC-02")

        self.assertFalse(success)
        self.assertIsNotNone(existing_lock)
        self.assertEqual(existing_lock["user"], "user1@PC-01")

    def test_release_lock(self) -> None:
        """Test lock release."""
        self.lock_manager.acquire_lock("user@PC-01")
        self.assertTrue(self.lock_manager.lock_file.exists())

        released = self.lock_manager.release_lock()
        self.assertTrue(released)
        self.assertFalse(self.lock_manager.lock_file.exists())

    def test_is_locked(self) -> None:
        """Test lock status checking."""
        self.assertFalse(self.lock_manager.is_locked())

        self.lock_manager.acquire_lock("user@PC-01")
        self.assertFalse(self.lock_manager.is_locked())  # Own lock doesn't count

        # Different manager sees lock
        lock_manager2 = LockManager(self.temp_dir.name)
        self.assertTrue(lock_manager2.is_locked())

    def test_get_lock_info(self) -> None:
        """Test retrieving lock information."""
        self.assertIsNone(self.lock_manager.get_lock_info())

        self.lock_manager.acquire_lock("user@PC-01")
        lock_info = self.lock_manager.get_lock_info()

        self.assertIsNotNone(lock_info)
        self.assertEqual(lock_info["user"], "user@PC-01")
        self.assertTrue(lock_info["locked"])
        self.assertIn("timestamp", lock_info)
        self.assertIn("pid", lock_info)
        self.assertIn("hostname", lock_info)

    def test_stale_lock_detection(self) -> None:
        """Test detection of stale locks."""
        # Create a lock with old timestamp
        self.lock_manager.acquire_lock("user@PC-01")

        # Manually modify timestamp to be old
        import json
        with open(self.lock_manager.lock_file, 'r') as f:
            lock_data = json.load(f)

        # Set timestamp to 2 hours ago (beyond 1 hour timeout)
        from datetime import datetime, timedelta
        old_time = (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z"
        lock_data["timestamp"] = old_time

        with open(self.lock_manager.lock_file, 'w') as f:
            json.dump(lock_data, f)

        # Now the stale lock should be removed when another process tries to acquire
        lock_manager2 = LockManager(self.temp_dir.name)
        success, existing_lock = lock_manager2.acquire_lock("user2@PC-02")

        self.assertTrue(success)  # Should succeed because old lock is stale
        self.assertTrue(lock_manager2.lock_file.exists())

    def test_update_lock_timestamp(self) -> None:
        """Test updating lock timestamp for heartbeat."""
        self.lock_manager.acquire_lock("user@PC-01")

        import json
        with open(self.lock_manager.lock_file, 'r') as f:
            original_lock = json.load(f)
        original_time = original_lock["timestamp"]

        time.sleep(0.1)
        updated = self.lock_manager.update_lock_timestamp()
        self.assertTrue(updated)

        with open(self.lock_manager.lock_file, 'r') as f:
            updated_lock = json.load(f)
        updated_time = updated_lock["timestamp"]

        self.assertNotEqual(original_time, updated_time)

    def test_update_lock_without_lock(self) -> None:
        """Test updating lock when no lock exists."""
        updated = self.lock_manager.update_lock_timestamp()
        self.assertFalse(updated)

    def test_can_acquire_lock_after_release(self) -> None:
        """Test acquiring new lock after release."""
        self.lock_manager.acquire_lock("user@PC-01")
        self.lock_manager.release_lock()

        # Should be able to acquire again
        success, _ = self.lock_manager.acquire_lock("user@PC-01")
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()
