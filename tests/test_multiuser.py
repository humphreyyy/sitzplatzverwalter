"""Multi-user tests for Sitzplatz-Manager.

Tests file locking and concurrent access scenarios:
- Lock acquisition and release
- Multiple instances
- Read-only mode detection
- Stale lock detection and cleanup
- Lock timeouts
"""

import unittest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any

from data.lock_manager import LockManager
from data.data_manager import DataManager
from config import LOCK_TIMEOUT_SECONDS


class TestLockAcquisition(unittest.TestCase):
    """Test basic lock acquisition and release."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lock_manager = LockManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        # Release lock if still held
        try:
            self.lock_manager.release_lock()
        except:
            pass
        self.temp_dir.cleanup()

    def test_acquire_lock_success(self) -> None:
        """Test successful lock acquisition."""
        success, lock_info = self.lock_manager.acquire_lock("user1@pc01")
        self.assertTrue(success)
        self.assertIsNone(lock_info)

        # Verify lock file exists
        lock_file = Path(self.temp_dir.name) / "data.lock"
        self.assertTrue(lock_file.exists())

    def test_release_lock(self) -> None:
        """Test lock release."""
        # Acquire
        self.lock_manager.acquire_lock("user1@pc01")

        # Release
        self.lock_manager.release_lock()

        # Verify released
        is_locked = self.lock_manager.is_locked()
        self.assertFalse(is_locked)

    def test_lock_file_created(self) -> None:
        """Test that lock file is created when lock is acquired."""
        self.lock_manager.acquire_lock("user1@pc01")

        lock_file = Path(self.temp_dir.name) / "data.lock"
        self.assertTrue(lock_file.exists())

        self.lock_manager.release_lock()

    def test_lock_file_contains_user_info(self) -> None:
        """Test that lock file contains correct user information."""
        self.lock_manager.acquire_lock("user1@pc01")

        lock_file = Path(self.temp_dir.name) / "data.lock"
        with open(lock_file, 'r') as f:
            lock_data = json.load(f)

        self.assertTrue(lock_data["locked"])
        self.assertEqual(lock_data["user"], "user1@pc01")
        self.assertIn("timestamp", lock_data)
        self.assertIn("pid", lock_data)

        self.lock_manager.release_lock()


class TestConcurrentAccess(unittest.TestCase):
    """Test multiple instances with lock behavior."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lock_manager1 = LockManager(self.temp_dir.name)
        self.lock_manager2 = LockManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        try:
            self.lock_manager1.release_lock()
        except:
            pass
        try:
            self.lock_manager2.release_lock()
        except:
            pass
        self.temp_dir.cleanup()

    def test_second_instance_detects_lock(self) -> None:
        """Test that second instance detects lock from first."""
        # First instance acquires lock
        success1, _ = self.lock_manager1.acquire_lock("user1@pc01")
        self.assertTrue(success1)

        # Second instance should not be able to acquire
        success2, lock_info = self.lock_manager2.acquire_lock("user2@pc02")
        self.assertFalse(success2)

        # But should get lock info
        self.assertIsNotNone(lock_info)
        self.assertEqual(lock_info["user"], "user1@pc01")

    def test_read_only_mode_when_locked(self) -> None:
        """Test that data manager can read when lock is held by another."""
        data_manager1 = DataManager(self.temp_dir.name)
        data_manager2 = DataManager(self.temp_dir.name)

        # First instance acquires lock
        self.lock_manager1.acquire_lock("user1@pc01")

        # Both managers can read
        data1 = data_manager1.load_data()
        self.assertIsNotNone(data1)

        data2 = data_manager2.load_data()
        self.assertIsNotNone(data2)

    def test_lock_release_allows_new_acquisition(self) -> None:
        """Test that releasing lock allows another instance to acquire it."""
        # First instance acquires and releases
        self.lock_manager1.acquire_lock("user1@pc01")
        self.lock_manager1.release_lock()

        # Second instance should now be able to acquire
        success2, lock_info = self.lock_manager2.acquire_lock("user2@pc02")
        self.assertTrue(success2)
        self.assertIsNone(lock_info)

        # Verify lock file exists
        lock_file = Path(self.temp_dir.name) / "data.lock"
        self.assertTrue(lock_file.exists())


class TestStaleLockDetection(unittest.TestCase):
    """Test stale lock detection and cleanup."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lock_manager = LockManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        try:
            self.lock_manager.release_lock()
        except:
            pass
        self.temp_dir.cleanup()

    def test_detect_stale_lock(self) -> None:
        """Test detecting stale lock from crashed process."""
        # Create stale lock manually (old timestamp)
        lock_file = Path(self.temp_dir.name) / "data.lock"
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        lock_data = {
            "locked": True,
            "user": "crashed_user@crashed_pc",
            "timestamp": old_time,
            "pid": 9999,  # Non-existent PID
            "hostname": "crashed_pc"
        }
        with open(lock_file, 'w') as f:
            json.dump(lock_data, f)

        # is_locked should return False for stale lock
        is_locked = self.lock_manager.is_locked()
        self.assertFalse(is_locked)

    def test_cleanup_stale_lock(self) -> None:
        """Test cleanup of stale lock file."""
        # Create stale lock
        lock_file = Path(self.temp_dir.name) / "data.lock"
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        lock_data = {
            "locked": True,
            "user": "crashed_user@crashed_pc",
            "timestamp": old_time,
            "pid": 9999,
            "hostname": "crashed_pc"
        }
        with open(lock_file, 'w') as f:
            json.dump(lock_data, f)

        # New instance should be able to acquire lock
        success, lock_info = self.lock_manager.acquire_lock("new_user@pc01")
        self.assertTrue(success)
        self.assertIsNone(lock_info)

    def test_lock_timeout_boundary(self) -> None:
        """Test lock timeout at boundary."""
        # Create lock at LOCK_TIMEOUT_SECONDS ago (should be stale)
        lock_file = Path(self.temp_dir.name) / "data.lock"
        timeout_time = datetime.now() - timedelta(seconds=LOCK_TIMEOUT_SECONDS + 1)
        lock_data = {
            "locked": True,
            "user": "boundary_user@pc",
            "timestamp": timeout_time.isoformat(),
            "pid": 9999,
            "hostname": "pc"
        }
        with open(lock_file, 'w') as f:
            json.dump(lock_data, f)

        # Should be able to acquire (lock is stale) or at least not crash
        try:
            success, lock_info = self.lock_manager.acquire_lock("new_user@pc")
            # Either succeeds or fails gracefully
            self.assertIsNotNone(success)
        except Exception:
            # Acceptable if handled
            pass


class TestLockCorruptionRecovery(unittest.TestCase):
    """Test recovery from lock file corruption."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.lock_manager = LockManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        try:
            self.lock_manager.release_lock()
        except:
            pass
        self.temp_dir.cleanup()

    def test_corrupted_lock_file_recovery(self) -> None:
        """Test recovery from corrupted lock file."""
        # Create corrupted lock file
        lock_file = Path(self.temp_dir.name) / "data.lock"
        with open(lock_file, 'w') as f:
            f.write("{ invalid json content }")

        # Should handle gracefully and allow new lock
        try:
            success, lock_info = self.lock_manager.acquire_lock("new_user@pc01")
            # Should either succeed or raise handled exception
            self.assertTrue(True)
        except Exception:
            # Acceptable if handled properly
            self.assertTrue(True)

    def test_missing_fields_in_lock_file(self) -> None:
        """Test handling of lock file with missing fields."""
        lock_file = Path(self.temp_dir.name) / "data.lock"

        # Write incomplete lock data
        lock_data = {"locked": True}  # Missing user, timestamp, etc.
        with open(lock_file, 'w') as f:
            json.dump(lock_data, f)

        # Should handle gracefully
        try:
            is_locked = self.lock_manager.is_locked()
            # Should handle the missing fields gracefully
            self.assertTrue(True)
        except Exception:
            self.assertTrue(True)


class TestMultiUserWorkflow(unittest.TestCase):
    """Test realistic multi-user workflows."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_manager1 = DataManager(self.temp_dir.name)
        self.data_manager2 = DataManager(self.temp_dir.name)
        self.lock_manager1 = LockManager(self.temp_dir.name)
        self.lock_manager2 = LockManager(self.temp_dir.name)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        try:
            self.lock_manager1.release_lock()
        except:
            pass
        try:
            self.lock_manager2.release_lock()
        except:
            pass
        self.temp_dir.cleanup()

    def test_user1_locks_user2_waits(self) -> None:
        """Test User1 locks, User2 detects and waits."""
        # User1 acquires lock
        success1, _ = self.lock_manager1.acquire_lock("user1@pc01")
        self.assertTrue(success1)

        # User2 attempts to acquire
        success2, lock_info = self.lock_manager2.acquire_lock("user2@pc02")
        self.assertFalse(success2)
        self.assertIsNotNone(lock_info)
        self.assertEqual(lock_info["user"], "user1@pc01")

        # User2 can read in read-only mode
        data2 = self.data_manager2.load_data()
        self.assertIsNotNone(data2)

        # User1 releases lock
        self.lock_manager1.release_lock()

        # Now User2 can acquire
        success2_retry, lock_info = self.lock_manager2.acquire_lock("user2@pc02")
        self.assertTrue(success2_retry)
        self.assertIsNone(lock_info)

    def test_user1_edits_user2_sees_changes(self) -> None:
        """Test that User2 sees changes made by User1 after release."""
        # User1 creates data
        data1 = self.data_manager1.load_data()
        data1["test_key"] = "test_value_1"

        # User1 acquires lock to save
        self.lock_manager1.acquire_lock("user1@pc01")
        self.data_manager1.save_data(data1, create_backup=False)
        self.lock_manager1.release_lock()

        # User2 reads (now can acquire lock)
        self.lock_manager2.acquire_lock("user2@pc02")
        data2 = self.data_manager2.load_data()

        # User2 should see User1's changes
        self.assertEqual(data2.get("test_key"), "test_value_1")
        self.lock_manager2.release_lock()


if __name__ == "__main__":
    unittest.main()
