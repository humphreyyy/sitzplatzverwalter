"""LockManager handles file locking for multi-user support."""

import json
import os
import socket
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

from config import LOCK_FILE, LOCK_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class LockManager:
    """Manages file locking to prevent concurrent modifications.

    Provides:
    - Lock acquisition and release
    - Stale lock detection (timeout)
    - Lock status queries
    - Multi-user coordination
    """

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize LockManager.

        Args:
            data_dir: Directory containing lock file. Defaults to current directory.
        """
        self.data_dir = Path(data_dir) if data_dir else Path.cwd()
        self.lock_file = self.data_dir / LOCK_FILE
        self.timeout_seconds = LOCK_TIMEOUT_SECONDS
        self._lock_info: Optional[Dict] = None

    def acquire_lock(self, user: str) -> Tuple[bool, Optional[Dict]]:
        """Try to acquire a file lock.

        Args:
            user: Username or identifier (e.g., "admin@PC-01")

        Returns:
            Tuple of (success, existing_lock_info_if_failed)
            - If successful: (True, None)
            - If another user holds lock: (False, lock_info)
        """
        try:
            # If lock exists, check if it's stale
            if self.lock_file.exists():
                with open(self.lock_file, 'r', encoding='utf-8') as f:
                    existing_lock = json.load(f)

                # Check if lock is stale
                if self._is_lock_stale(existing_lock):
                    logger.info(f"Removing stale lock from {existing_lock.get('user')}")
                    self.lock_file.unlink()
                else:
                    logger.warning(f"Lock held by {existing_lock.get('user')} on {existing_lock.get('hostname')}")
                    return False, existing_lock

            # Create new lock
            lock_data = self._create_lock_data(user)

            # Ensure directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)

            # Write lock file
            with open(self.lock_file, 'w', encoding='utf-8') as f:
                json.dump(lock_data, f, indent=2)

            self._lock_info = lock_data
            logger.info(f"Lock acquired by {user}")
            return True, None

        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            raise

    def release_lock(self) -> bool:
        """Release the current lock.

        Returns:
            True if lock was released, False if no lock to release
        """
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                self._lock_info = None
                logger.info("Lock released")
                return True
            return False

        except Exception as e:
            logger.warning(f"Error releasing lock: {e}")
            return False

    def is_locked(self) -> bool:
        """Check if file is currently locked.

        Returns:
            True if locked by another user, False if unlocked or own lock
        """
        try:
            if not self.lock_file.exists():
                return False

            with open(self.lock_file, 'r', encoding='utf-8') as f:
                lock_data = json.load(f)

            # If lock is stale, it's effectively not locked
            if self._is_lock_stale(lock_data):
                return False

            # If this is our own lock, it's not locked (from perspective of another process)
            return lock_data != self._lock_info

        except Exception as e:
            logger.warning(f"Error checking lock status: {e}")
            return False

    def get_lock_info(self) -> Optional[Dict]:
        """Get information about current lock holder.

        Returns:
            Dictionary with lock information if locked, None otherwise
        """
        try:
            if not self.lock_file.exists():
                return None

            with open(self.lock_file, 'r', encoding='utf-8') as f:
                lock_data = json.load(f)

            if self._is_lock_stale(lock_data):
                return None

            return lock_data

        except Exception as e:
            logger.warning(f"Error reading lock info: {e}")
            return None

    def is_stale_lock(self) -> bool:
        """Check if current lock is stale (older than timeout).

        Returns:
            True if lock exists and is stale, False otherwise
        """
        try:
            if not self.lock_file.exists():
                return False

            with open(self.lock_file, 'r', encoding='utf-8') as f:
                lock_data = json.load(f)

            return self._is_lock_stale(lock_data)

        except Exception as e:
            logger.warning(f"Error checking lock staleness: {e}")
            return False

    def update_lock_timestamp(self) -> bool:
        """Update the timestamp in the lock file to prove app is still running.

        Returns:
            True if successful, False if no lock to update
        """
        try:
            if not self.lock_file.exists():
                return False

            if self._lock_info is None:
                return False

            # Update timestamp
            self._lock_info["timestamp"] = datetime.utcnow().isoformat() + "Z"

            with open(self.lock_file, 'w', encoding='utf-8') as f:
                json.dump(self._lock_info, f, indent=2)

            return True

        except Exception as e:
            logger.warning(f"Error updating lock timestamp: {e}")
            return False

    # ========================================================================
    # Private helper methods
    # ========================================================================

    def _create_lock_data(self, user: str) -> Dict:
        """Create lock data structure.

        Args:
            user: Username or identifier

        Returns:
            Dictionary with lock information
        """
        return {
            "locked": True,
            "user": user,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "pid": os.getpid(),
            "hostname": socket.gethostname()
        }

    def _is_lock_stale(self, lock_data: Dict) -> bool:
        """Check if a lock is older than the timeout threshold.

        Args:
            lock_data: Lock information dictionary

        Returns:
            True if lock is older than timeout, False otherwise
        """
        try:
            timestamp_str = lock_data.get("timestamp", "")
            if not timestamp_str:
                return True

            # Parse ISO format timestamp
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1]

            lock_time = datetime.fromisoformat(timestamp_str)
            current_time = datetime.utcnow()

            age_seconds = (current_time - lock_time).total_seconds()
            is_stale = age_seconds > self.timeout_seconds

            if is_stale:
                logger.debug(f"Lock is stale: {age_seconds:.0f}s old (timeout: {self.timeout_seconds}s)")

            return is_stale

        except Exception as e:
            logger.warning(f"Error checking lock staleness: {e}")
            return False

    def _process_exists(self, pid: int) -> bool:
        """Check if a process with given PID exists (platform-specific).

        Args:
            pid: Process ID to check

        Returns:
            True if process exists, False otherwise
        """
        try:
            # Check if process exists without sending signal
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False
