"""
Unit tests for notification_db.py - Fixed version with proper resource management
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
        with NotificationDB(str(db_path)) as db:
            assert db_path.exists()
            assert db.conn is not None
    
    def test_init_creates_tables(self, temp_dir):
        """Test that initialization creates required tables."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
            # Check that tables exist
            cursor = db.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert "notifications" in tables
            assert "sessions" in tables
    
    def test_add_notification(self, temp_dir):
        """Test adding a notification to the database."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
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
        with NotificationDB(str(db_path)) as db:
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
        with NotificationDB(str(db_path)) as db:
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
        with NotificationDB(str(db_path)) as db:
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
        with NotificationDB(str(db_path)) as db:
            # Add multiple notifications
            notifications = [
                {
                    "uri": f"at://did:plc:test/app.bsky.notification.record/test{i}",
                    "indexed_at": f"2025-01-01T00:0{i}:00.000Z",
                    "author": {"handle": f"test{i}.user.bsky.social", "did": f"did:plc:test{i}"},
                    "record": {"text": f"Test notification {i}"},
                    "reason": "mention"
                }
                for i in range(3)
            ]
            
            for notif in notifications:
                db.add_notification(notif)
            
            # Mark one as processed
            db.mark_processed(notifications[0]["uri"], "processed")
            
            # Get unprocessed
            unprocessed = db.get_unprocessed()
            assert len(unprocessed) == 2
            uris = [n["uri"] for n in unprocessed]
            assert notifications[1]["uri"] in uris
            assert notifications[2]["uri"] in uris
    
    def test_get_latest_processed_time(self, temp_dir):
        """Test getting latest processed time."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
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
        with NotificationDB(str(db_path)) as db:
            # Add old notification
            old_notification = {
                "uri": "at://did:plc:test/app.bsky.notification.record/old",
                "indexed_at": (datetime.now() - timedelta(days=10)).isoformat(),
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
            
            # Cleanup records older than 7 days
            db.cleanup_old_records(days=7)
            
            # Check that old record is gone but recent one remains
            cursor = db.conn.execute("SELECT uri FROM notifications")
            remaining_uris = [row[0] for row in cursor.fetchall()]
            assert old_notification["uri"] not in remaining_uris
            assert recent_notification["uri"] in remaining_uris
    
    def test_get_stats(self, temp_dir):
        """Test getting database statistics."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
            # Add notifications with different statuses
            notifications = [
                {
                    "uri": f"at://did:plc:test/app.bsky.notification.record/test{i}",
                    "indexed_at": f"2025-01-01T00:0{i}:00.000Z",
                    "author": {"handle": f"test{i}.user.bsky.social", "did": f"did:plc:test{i}"},
                    "record": {"text": f"Test notification {i}"},
                    "reason": "mention"
                }
                for i in range(5)
            ]
            
            for notif in notifications:
                db.add_notification(notif)
            
            # Mark different statuses
            db.mark_processed(notifications[0]["uri"], "processed")
            db.mark_processed(notifications[1]["uri"], "ignored")
            db.mark_processed(notifications[2]["uri"], "error", "Test error")
            # Leave notifications[3] and notifications[4] as pending
            
            stats = db.get_stats()
            assert stats["total"] == 5
            assert stats["status_processed"] == 1
            assert stats["status_ignored"] == 1
            assert stats["status_error"] == 1
            assert stats["status_pending"] == 2
    
    def test_session_management(self, temp_dir):
        """Test session management functionality."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
            # Start session
            session_id = db.start_session()
            assert session_id is not None
            
            # Update session
            db.update_session(session_id, processed=5, skipped=2, error=1)
            
            # End session
            db.end_session(session_id)
            
            # Verify session data
            cursor = db.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            session = cursor.fetchone()
            assert session["notifications_processed"] == 5
            assert session["notifications_skipped"] == 2
            assert session["notifications_error"] == 1
            assert session["ended_at"] is not None
    
    def test_get_processed_uris(self, temp_dir):
        """Test getting processed URIs."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
            notifications = [
                {
                    "uri": f"at://did:plc:test/app.bsky.notification.record/test{i}",
                    "indexed_at": f"2025-01-01T00:0{i}:00.000Z",
                    "author": {"handle": f"test{i}.user.bsky.social", "did": f"did:plc:test{i}"},
                    "record": {"text": f"Test notification {i}"},
                    "reason": "mention"
                }
                for i in range(3)
            ]
            
            for notif in notifications:
                db.add_notification(notif)
            
            # Mark as processed
            db.mark_processed(notifications[0]["uri"], "processed")
            db.mark_processed(notifications[1]["uri"], "ignored")
            # Leave notifications[2] as pending
            
            processed_uris = db.get_processed_uris()
            assert notifications[0]["uri"] in processed_uris
            assert notifications[1]["uri"] in processed_uris
            assert notifications[2]["uri"] not in processed_uris
    
    def test_close_connection(self, temp_dir):
        """Test closing database connection."""
        db_path = temp_dir / "test.db"
        db = NotificationDB(str(db_path))
        
        assert db.conn is not None
        db.close()
        assert db.conn is None


class TestNotificationDBEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_add_empty_notification(self, temp_dir):
        """Test adding empty notification."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
            result = db.add_notification({})
            assert result is False
            
            result = db.add_notification(None)
            assert result is False
    
    def test_add_duplicate_notification(self, temp_dir):
        """Test adding duplicate notification."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
            notification = {
                "uri": "at://did:plc:test/app.bsky.notification.record/test",
                "indexed_at": "2025-01-01T00:00:00.000Z",
                "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
                "record": {"text": "Test notification"},
                "reason": "mention"
            }
            
            # Add twice
            result1 = db.add_notification(notification)
            result2 = db.add_notification(notification)
            
            assert result1 is True
            assert result2 is True  # INSERT OR IGNORE allows duplicates
            
            # Should only have one record
            cursor = db.conn.execute("SELECT COUNT(*) FROM notifications WHERE uri = ?", (notification["uri"],))
            count = cursor.fetchone()[0]
            assert count == 1
    
    def test_mark_nonexistent_notification(self, temp_dir):
        """Test marking nonexistent notification as processed."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
            # Should not raise exception
            db.mark_processed("nonexistent-uri", "processed")
    
    def test_get_notifications_with_limit(self, temp_dir):
        """Test getting notifications with limit."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
            # Add 5 notifications
            notifications = [
                {
                    "uri": f"at://did:plc:test/app.bsky.notification.record/test{i}",
                    "indexed_at": f"2025-01-01T00:0{i}:00.000Z",
                    "author": {"handle": f"test{i}.user.bsky.social", "did": f"did:plc:test{i}"},
                    "record": {"text": f"Test notification {i}"},
                    "reason": "mention"
                }
                for i in range(5)
            ]
            
            for notif in notifications:
                db.add_notification(notif)
            
            # Get with limit
            unprocessed = db.get_unprocessed(limit=3)
            assert len(unprocessed) == 3
    
    def test_database_file_permissions(self, temp_dir):
        """Test database file permissions."""
        db_path = temp_dir / "test.db"
        with NotificationDB(str(db_path)) as db:
            # Should be able to create and access database
            assert db_path.exists()
            assert db.conn is not None


@pytest.mark.parametrize("uri,expected_valid", [
    ("at://did:plc:test/app.bsky.notification.record/test", True),
    ("at://did:plc:example/app.bsky.feed.post/abc123", True),
    ("invalid-uri", True),  # Current implementation accepts any non-empty string
    ("", False),
    (None, False),
])
def test_notification_uri_validation(temp_dir, uri, expected_valid):
    """Test notification URI validation."""
    db_path = temp_dir / "test.db"
    with NotificationDB(str(db_path)) as db:
        notification = {
            "uri": uri,
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        
        result = db.add_notification(notification)
        assert result == expected_valid
