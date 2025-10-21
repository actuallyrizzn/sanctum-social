"""
Unit tests for queue_manager.py
"""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import json
import tempfile
import shutil
from queue_manager import (
    load_notification,
    list_notifications,
    delete_by_handle,
    count_by_handle,
    stats,
    QUEUE_DIR,
    QUEUE_ERROR_DIR,
    QUEUE_NO_REPLY_DIR
)


class TestQueueManager:
    """Test cases for queue_manager module."""
    
    def test_load_notification_success(self, tmp_path):
        """Test successful notification loading."""
        # Create a test notification file
        notification_data = {
            "uri": "at://test.bsky.social/post/123",
            "text": "Test notification",
            "author": {"handle": "test.user.bsky.social"}
        }
        
        notification_file = tmp_path / "test_notification.json"
        with open(notification_file, 'w') as f:
            json.dump(notification_data, f)
        
        # Test loading
        result = load_notification(notification_file)
        
        assert result == notification_data
    
    def test_load_notification_file_not_found(self, tmp_path):
        """Test loading notification from non-existent file."""
        non_existent_file = tmp_path / "non_existent.json"
        
        result = load_notification(non_existent_file)
        
        assert result is None
    
    def test_load_notification_invalid_json(self, tmp_path):
        """Test loading notification with invalid JSON."""
        invalid_json_file = tmp_path / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write("invalid json content")
        
        result = load_notification(invalid_json_file)
        
        assert result is None
    
    @patch('queue_manager.QUEUE_DIR', Path("test_queue"))
    @patch('queue_manager.QUEUE_ERROR_DIR', Path("test_queue/errors"))
    @patch('queue_manager.QUEUE_NO_REPLY_DIR', Path("test_queue/no_reply"))
    def test_list_notifications_queue_only(self, tmp_path):
        """Test listing notifications from queue directory only."""
        # Create test queue structure
        queue_dir = tmp_path / "test_queue"
        queue_dir.mkdir()
        
        # Create test notifications
        notification1 = {
            "uri": "at://test1.bsky.social/post/123",
            "text": "Test notification 1",
            "author": {"handle": "test1.bsky.social"}
        }
        notification2 = {
            "uri": "at://test2.bsky.social/post/456",
            "text": "Test notification 2",
            "author": {"handle": "test2.bsky.social"}
        }
        
        with open(queue_dir / "notif1.json", 'w') as f:
            json.dump(notification1, f)
        with open(queue_dir / "notif2.json", 'w') as f:
            json.dump(notification2, f)
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', queue_dir):
            with patch('queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing
                    result = list_notifications()
                    
                    assert len(result) == 2
                    assert any(n["uri"] == "at://test1.bsky.social/post/123" for n in result)
                    assert any(n["uri"] == "at://test2.bsky.social/post/456" for n in result)
    
    @patch('queue_manager.QUEUE_DIR', Path("test_queue"))
    @patch('queue_manager.QUEUE_ERROR_DIR', Path("test_queue/errors"))
    @patch('queue_manager.QUEUE_NO_REPLY_DIR', Path("test_queue/no_reply"))
    def test_list_notifications_with_handle_filter(self, tmp_path):
        """Test listing notifications with handle filter."""
        # Create test queue structure
        queue_dir = tmp_path / "test_queue"
        queue_dir.mkdir()
        
        # Create test notifications
        notification1 = {
            "uri": "at://test1.bsky.social/post/123",
            "text": "Test notification 1",
            "author": {"handle": "test1.bsky.social"}
        }
        notification2 = {
            "uri": "at://test2.bsky.social/post/456",
            "text": "Test notification 2",
            "author": {"handle": "test2.bsky.social"}
        }
        
        with open(queue_dir / "notif1.json", 'w') as f:
            json.dump(notification1, f)
        with open(queue_dir / "notif2.json", 'w') as f:
            json.dump(notification2, f)
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', queue_dir):
            with patch('queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing with filter
                    result = list_notifications(handle_filter="test1.bsky.social")
                    
                    assert len(result) == 1
                    assert result[0]["uri"] == "at://test1.bsky.social/post/123"
    
    @patch('queue_manager.QUEUE_DIR', Path("test_queue"))
    @patch('queue_manager.QUEUE_ERROR_DIR', Path("test_queue/errors"))
    @patch('queue_manager.QUEUE_NO_REPLY_DIR', Path("test_queue/no_reply"))
    def test_list_notifications_show_all(self, tmp_path):
        """Test listing notifications from all directories."""
        # Create test queue structure
        queue_dir = tmp_path / "test_queue"
        error_dir = queue_dir / "errors"
        no_reply_dir = queue_dir / "no_reply"
        
        queue_dir.mkdir()
        error_dir.mkdir()
        no_reply_dir.mkdir()
        
        # Create test notifications in different directories
        queue_notification = {
            "uri": "at://queue.bsky.social/post/123",
            "text": "Queue notification",
            "author": {"handle": "queue.bsky.social"}
        }
        error_notification = {
            "uri": "at://error.bsky.social/post/456",
            "text": "Error notification",
            "author": {"handle": "error.bsky.social"}
        }
        no_reply_notification = {
            "uri": "at://noreply.bsky.social/post/789",
            "text": "No reply notification",
            "author": {"handle": "noreply.bsky.social"}
        }
        
        with open(queue_dir / "queue_notif.json", 'w') as f:
            json.dump(queue_notification, f)
        with open(error_dir / "error_notif.json", 'w') as f:
            json.dump(error_notification, f)
        with open(no_reply_dir / "noreply_notif.json", 'w') as f:
            json.dump(no_reply_notification, f)
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', queue_dir):
            with patch('queue_manager.QUEUE_ERROR_DIR', error_dir):
                with patch('queue_manager.QUEUE_NO_REPLY_DIR', no_reply_dir):
                    # Test listing all
                    result = list_notifications(show_all=True)
                    
                    assert len(result) == 3
                    assert any(n["uri"] == "at://queue.bsky.social/post/123" for n in result)
                    assert any(n["uri"] == "at://error.bsky.social/post/456" for n in result)
                    assert any(n["uri"] == "at://noreply.bsky.social/post/789" for n in result)
    
    def test_delete_by_handle_success(self, tmp_path):
        """Test successful deletion by handle."""
        # Create test queue structure
        queue_dir = tmp_path / "test_queue"
        queue_dir.mkdir()
        
        # Create test notifications
        notification1 = {
            "uri": "at://test1.bsky.social/post/123",
            "text": "Test notification 1",
            "author": {"handle": "test1.bsky.social"}
        }
        notification2 = {
            "uri": "at://test2.bsky.social/post/456",
            "text": "Test notification 2",
            "author": {"handle": "test2.bsky.social"}
        }
        
        with open(queue_dir / "notif1.json", 'w') as f:
            json.dump(notification1, f)
        with open(queue_dir / "notif2.json", 'w') as f:
            json.dump(notification2, f)
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', queue_dir):
            # Mock console.print and Confirm.ask
            with patch('queue_manager.console.print') as mock_print:
                with patch('queue_manager.Confirm.ask', return_value=True):
                    delete_by_handle("test1.bsky.social")
                    
                    # Verify only test1 notification was deleted
                    remaining_files = list(queue_dir.glob("*.json"))
                    assert len(remaining_files) == 1
                    assert remaining_files[0].name == "notif2.json"
    
    def test_count_by_handle(self, tmp_path):
        """Test counting notifications by handle."""
        # Create test queue structure
        queue_dir = tmp_path / "test_queue"
        queue_dir.mkdir()
        
        # Create test notifications
        notification1 = {
            "uri": "at://test1.bsky.social/post/123",
            "text": "Test notification 1",
            "author": {"handle": "test1.bsky.social"}
        }
        notification2 = {
            "uri": "at://test1.bsky.social/post/456",
            "text": "Test notification 2",
            "author": {"handle": "test1.bsky.social"}
        }
        notification3 = {
            "uri": "at://test2.bsky.social/post/789",
            "text": "Test notification 3",
            "author": {"handle": "test2.bsky.social"}
        }
        
        with open(queue_dir / "notif1.json", 'w') as f:
            json.dump(notification1, f)
        with open(queue_dir / "notif2.json", 'w') as f:
            json.dump(notification2, f)
        with open(queue_dir / "notif3.json", 'w') as f:
            json.dump(notification3, f)
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', queue_dir):
            # Mock console.print
            with patch('queue_manager.console.print') as mock_print:
                count_by_handle()
                
                # Verify that console.print was called
                assert mock_print.call_count > 0
    
    def test_stats(self, tmp_path):
        """Test queue statistics."""
        # Create test queue structure
        queue_dir = tmp_path / "test_queue"
        queue_dir.mkdir()
        
        # Create test notifications
        notification1 = {
            "uri": "at://test1.bsky.social/post/123",
            "text": "Test notification 1",
            "author": {"handle": "test1.bsky.social"}
        }
        
        with open(queue_dir / "notif1.json", 'w') as f:
            json.dump(notification1, f)
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', queue_dir):
            # Mock console.print
            with patch('queue_manager.console.print') as mock_print:
                stats()
                
                # Verify that console.print was called
                assert mock_print.call_count > 0
    
    def test_delete_by_handle_user_cancels(self, tmp_path):
        """Test deletion by handle when user cancels."""
        # Create test queue structure
        queue_dir = tmp_path / "test_queue"
        queue_dir.mkdir()
        
        # Create test notifications
        notification1 = {
            "uri": "at://test1.bsky.social/post/123",
            "text": "Test notification 1",
            "author": {"handle": "test1.bsky.social"}
        }
        
        with open(queue_dir / "notif1.json", 'w') as f:
            json.dump(notification1, f)
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', queue_dir):
            # Mock console.print and Confirm.ask
            with patch('queue_manager.console.print') as mock_print:
                with patch('queue_manager.Confirm.ask', return_value=False):
                    delete_by_handle("test1.bsky.social")
                    
                    # Verify file was not deleted
                    assert len(list(queue_dir.glob("*.json"))) == 1
    
    def test_queue_directories_defined(self):
        """Test that queue directories are properly defined."""
        assert QUEUE_DIR == Path("queue")
        assert QUEUE_ERROR_DIR == QUEUE_DIR / "errors"
        assert QUEUE_NO_REPLY_DIR == QUEUE_DIR / "no_reply"
    
    @patch('queue_manager.QUEUE_DIR', Path("test_queue"))
    def test_list_notifications_empty_queue(self, tmp_path):
        """Test listing notifications from empty queue."""
        # Create empty queue directory
        queue_dir = tmp_path / "test_queue"
        queue_dir.mkdir()
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', queue_dir):
            with patch('queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing
                    result = list_notifications()
                    
                    assert result == []
    
    @patch('queue_manager.QUEUE_DIR', Path("test_queue"))
    def test_list_notifications_nonexistent_directories(self, tmp_path):
        """Test listing notifications when directories don't exist."""
        # Don't create any directories
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', tmp_path / "nonexistent"):
            with patch('queue_manager.QUEUE_ERROR_DIR', tmp_path / "nonexistent" / "errors"):
                with patch('queue_manager.QUEUE_NO_REPLY_DIR', tmp_path / "nonexistent" / "no_reply"):
                    # Test listing
                    result = list_notifications()
                    
                    assert result == []
    
    def test_load_notification_permission_error(self, tmp_path):
        """Test loading notification with permission error."""
        # Create a file that can't be read
        notification_file = tmp_path / "test_notification.json"
        notification_file.write_text('{"test": "data"}')
        
        # Mock open to raise permission error
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = load_notification(notification_file)
            
            assert result is None
    
    @patch('queue_manager.QUEUE_DIR', Path("test_queue"))
    def test_list_notifications_with_invalid_json_files(self, tmp_path):
        """Test listing notifications with invalid JSON files."""
        # Create test queue structure
        queue_dir = tmp_path / "test_queue"
        queue_dir.mkdir()
        
        # Create valid notification
        valid_notification = {
            "uri": "at://valid.bsky.social/post/123",
            "text": "Valid notification",
            "author": {"handle": "valid.bsky.social"}
        }
        
        with open(queue_dir / "valid.json", 'w') as f:
            json.dump(valid_notification, f)
        
        # Create invalid JSON file
        with open(queue_dir / "invalid.json", 'w') as f:
            f.write("invalid json content")
        
        # Mock the queue directories
        with patch('queue_manager.QUEUE_DIR', queue_dir):
            with patch('queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing
                    result = list_notifications()
                    
                    # Should only return valid notifications
                    assert len(result) == 1
                    assert result[0]["uri"] == "at://valid.bsky.social/post/123"
