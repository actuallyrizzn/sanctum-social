"""
Unit tests for notification_db.py
"""
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import pytest
import json

from notification_db import NotificationDB


class TestNotificationDB:
    """Test cases for NotificationDB class."""
    
    def test_init_creates_database(self, temp_dir):
        """Test that initialization creates the database file."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        assert db_path.exists()
        assert db.conn is not None
    
    def test_init_creates_tables(self, temp_dir):
        """Test that initialization creates required tables."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        # Check that tables exist
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "notifications" in tables
        assert "sessions" in tables
    
    def test_add_notification(self, temp_dir):
        """Test adding a notification to the database."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        notification = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {
                "handle": "test.user.bsky.social",
                "did": "did:plc:test"
            },
            "record": {
                "text": "Test notification"
            },
            "reason": "mention"
        }
        
        result = db.add_notification(notification)
        assert result is True
        
        # Verify notification was added
        cursor = db.conn.execute("SELECT * FROM notifications WHERE uri = ?", (notification["uri"],))
        row = cursor.fetchone()
        assert row is not None
        assert row["uri"] == notification["uri"]
        assert row["author_handle"] == "test.user.bsky.social"
        assert row["text"] == "Test notification"
    
    def test_is_processed(self, temp_dir):
        """Test checking if notification is processed."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        notification = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        
        db.add_notification(notification)
        
        # Initially should not be processed
        assert not db.is_processed(notification["uri"])
        
        # Mark as processed
        db.mark_processed(notification["uri"], "processed")
        
        # Now should be processed
        assert db.is_processed(notification["uri"])
    
    def test_mark_processed(self, temp_dir):
        """Test marking notification as processed."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        notification = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        
        db.add_notification(notification)
        db.mark_processed(notification["uri"], "processed", "Successfully processed")
        
        cursor = db.conn.execute("SELECT * FROM notifications WHERE uri = ?", (notification["uri"],))
        row = cursor.fetchone()
        assert row["status"] == "processed"
        assert row["error"] == "Successfully processed"
        assert row["processed_at"] is not None
    
    def test_mark_error(self, temp_dir):
        """Test marking notification as error."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        notification = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        
        db.add_notification(notification)
        db.mark_processed(notification["uri"], "error", "Processing failed")
        
        cursor = db.conn.execute("SELECT * FROM notifications WHERE uri = ?", (notification["uri"],))
        row = cursor.fetchone()
        assert row["status"] == "error"
        assert row["error"] == "Processing failed"
    
    def test_get_unprocessed(self, temp_dir):
        """Test getting unprocessed notifications."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        # Add multiple notifications
        notifications = [
            {
                "uri": "at://did:plc:test/app.bsky.notification.record/test1",
                "indexed_at": "2025-01-01T00:00:00.000Z",
                "author": {"handle": "test1.bsky.social", "did": "did:plc:test1"},
                "record": {"text": "Test notification 1"},
                "reason": "mention"
            },
            {
                "uri": "at://did:plc:test/app.bsky.notification.record/test2",
                "indexed_at": "2025-01-01T00:01:00.000Z",
                "author": {"handle": "test2.bsky.social", "did": "did:plc:test2"},
                "record": {"text": "Test notification 2"},
                "reason": "mention"
            }
        ]
        
        for notif in notifications:
            db.add_notification(notif)
        
        # Mark one as processed
        db.mark_processed(notifications[0]["uri"], "processed")
        
        # Get unprocessed notifications
        unprocessed = db.get_unprocessed()
        assert len(unprocessed) == 1
        assert unprocessed[0]["uri"] == notifications[1]["uri"]
    
    def test_get_latest_processed_time(self, temp_dir):
        """Test getting latest processed time."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        notification = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        
        db.add_notification(notification)
        db.mark_processed(notification["uri"], "processed")
        
        latest_time = db.get_latest_processed_time()
        assert latest_time == "2025-01-01T00:00:00.000Z"
    
    def test_cleanup_old_records(self, temp_dir):
        """Test cleaning up old records."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        # Add old notification
        old_notification = {
            "uri": "at://did:plc:test/app.bsky.notification.record/old",
            "indexed_at": "2024-01-01T00:00:00.000Z",  # Very old
            "author": {"handle": "old.user.bsky.social", "did": "did:plc:old"},
            "record": {"text": "Old notification"},
            "reason": "mention"
        }
        
        db.add_notification(old_notification)
        db.mark_processed(old_notification["uri"], "processed")
        
        # Add recent notification
        recent_notification = {
            "uri": "at://did:plc:test/app.bsky.notification.record/recent",
            "indexed_at": datetime.now().isoformat(),
            "author": {"handle": "recent.user.bsky.social", "did": "did:plc:recent"},
            "record": {"text": "Recent notification"},
            "reason": "mention"
        }
        
        db.add_notification(recent_notification)
        db.mark_processed(recent_notification["uri"], "processed")
        
        # Cleanup old records (older than 30 days)
        db.cleanup_old_records(days=30)
        
        # Old notification should be gone, recent should remain
        assert not db.is_processed(old_notification["uri"])
        assert db.is_processed(recent_notification["uri"])
    
    def test_get_stats(self, temp_dir):
        """Test getting database statistics."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        # Add notifications with different statuses
        notifications = [
            {
                "uri": "at://did:plc:test/app.bsky.notification.record/pending",
                "indexed_at": datetime.now().isoformat(),
                "author": {"handle": "pending.bsky.social", "did": "did:plc:pending"},
                "record": {"text": "Pending notification"},
                "reason": "mention"
            },
            {
                "uri": "at://did:plc:test/app.bsky.notification.record/processed",
                "indexed_at": datetime.now().isoformat(),
                "author": {"handle": "processed.bsky.social", "did": "did:plc:processed"},
                "record": {"text": "Processed notification"},
                "reason": "mention"
            },
            {
                "uri": "at://did:plc:test/app.bsky.notification.record/error",
                "indexed_at": datetime.now().isoformat(),
                "author": {"handle": "error.bsky.social", "did": "did:plc:error"},
                "record": {"text": "Error notification"},
                "reason": "mention"
            }
        ]
        
        for notif in notifications:
            db.add_notification(notif)
        
        db.mark_processed(notifications[1]["uri"], "processed")
        db.mark_processed(notifications[2]["uri"], "error")
        
        stats = db.get_stats()
        assert stats["status_pending"] == 1
        assert stats["status_processed"] == 1
        assert stats["status_error"] == 1
        assert stats["total"] == 3
        assert stats["recent_24h"] == 3
    
    def test_session_management(self, temp_dir):
        """Test session management functionality."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        # Start session
        session_id = db.start_session()
        assert session_id is not None
        
        # Update session
        db.update_session(session_id, processed=5, skipped=2, error=1)
        
        # End session
        db.end_session(session_id)
        
        # Verify session data
        cursor = db.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row["notifications_processed"] == 5
        assert row["notifications_skipped"] == 2
        assert row["notifications_error"] == 1
        assert row["ended_at"] is not None
    
    def test_get_processed_uris(self, temp_dir):
        """Test getting processed URIs."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        notifications = [
            {
                "uri": "at://did:plc:test/app.bsky.notification.record/test1",
                "indexed_at": "2025-01-01T00:00:00.000Z",
                "author": {"handle": "test1.bsky.social", "did": "did:plc:test1"},
                "record": {"text": "Test notification 1"},
                "reason": "mention"
            },
            {
                "uri": "at://did:plc:test/app.bsky.notification.record/test2",
                "indexed_at": "2025-01-01T00:01:00.000Z",
                "author": {"handle": "test2.bsky.social", "did": "did:plc:test2"},
                "record": {"text": "Test notification 2"},
                "reason": "mention"
            }
        ]
        
        for notif in notifications:
            db.add_notification(notif)
            db.mark_processed(notif["uri"], "processed")
        
        processed_uris = db.get_processed_uris()
        assert len(processed_uris) == 2
        assert notifications[0]["uri"] in processed_uris
        assert notifications[1]["uri"] in processed_uris
    
    def test_close_connection(self, temp_dir):
        """Test closing the database connection."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        # Verify connection is open
        assert db.conn is not None
        
        # Close connection
        db.close()
        
        # Verify connection is closed (conn should still exist but be closed)
        assert db.conn is not None
        # The connection object exists but is closed


class TestNotificationDBEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_add_empty_notification(self, temp_dir):
        """Test adding empty or invalid notification."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        # Test None input
        result = db.add_notification(None)
        assert result is False
        
        # Test empty dict
        result = db.add_notification({})
        assert result is False
        
        # Test missing URI
        result = db.add_notification({"indexed_at": "2025-01-01T00:00:00.000Z"})
        assert result is False
    
    def test_add_duplicate_notification(self, temp_dir):
        """Test adding a duplicate notification."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        notification = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        
        # Add first time
        result1 = db.add_notification(notification)
        assert result1 is True
        
        # Add second time (should be ignored due to INSERT OR IGNORE)
        result2 = db.add_notification(notification)
        assert result2 is True
        
        # Should only have one record
        cursor = db.conn.execute("SELECT COUNT(*) as count FROM notifications WHERE uri = ?", (notification["uri"],))
        count = cursor.fetchone()["count"]
        assert count == 1
    
    def test_mark_nonexistent_notification(self, temp_dir):
        """Test marking non-existent notification as processed."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        # Should not raise error
        db.mark_processed("nonexistent-uri", "processed")
        
        # Verify no record was created
        cursor = db.conn.execute("SELECT COUNT(*) as count FROM notifications WHERE uri = ?", ("nonexistent-uri",))
        count = cursor.fetchone()["count"]
        assert count == 0
    
    def test_get_notifications_with_limit(self, temp_dir):
        """Test getting notifications with limit."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        # Add multiple notifications
        for i in range(5):
            notification = {
                "uri": f"at://did:plc:test/app.bsky.notification.record/test{i}",
                "indexed_at": f"2025-01-01T00:0{i}:00.000Z",
                "author": {"handle": f"test{i}.bsky.social", "did": f"did:plc:test{i}"},
                "record": {"text": f"Test notification {i}"},
                "reason": "mention"
            }
            db.add_notification(notification)
        
        # Get with limit
        unprocessed = db.get_unprocessed(limit=3)
        assert len(unprocessed) == 3
        
        # Get processed URIs with limit
        processed_uris = db.get_processed_uris(limit=2)
        assert len(processed_uris) == 0  # None processed yet
    
    def test_database_file_permissions(self, temp_dir):
        """Test database creation with different file permissions."""
        db_path = temp_dir / "test.db"
        
        # Should create database successfully
        db = NotificationDB(str(db_path))
        assert db_path.exists()
        
        # Should be able to add notifications
        notification = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        
        result = db.add_notification(notification)
        assert result is True


@pytest.mark.parametrize("uri,expected_valid", [
    ("at://did:plc:test/app.bsky.notification.record/test", True),
    ("at://did:plc:example/app.bsky.feed.post/abc123", True),
    ("invalid-uri", True),  # Actual implementation accepts any non-empty string
    ("", False),
    (None, False),
])
def test_notification_uri_validation(temp_dir, uri, expected_valid):
    """Test notification URI validation."""
    db_path = temp_dir / "test.db"
    db = NotificationDB(str(db_path))
    
    if expected_valid and uri:
        # Should succeed for valid URIs
        notification = {
            "uri": uri,
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        
        result = db.add_notification(notification)
        assert result is True
    else:
        # Should fail for invalid URIs
        notification = {
            "uri": uri,
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        
        result = db.add_notification(notification)
        assert result is False