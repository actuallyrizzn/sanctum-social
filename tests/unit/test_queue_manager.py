"""
Unit tests for queue_manager.py
"""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import json
import tempfile
import shutil
from utils.queue_manager import (
    load_notification,
    list_notifications,
    delete_by_handle,
    count_by_handle,
    stats,
    QUEUE_DIR,
    QUEUE_ERROR_DIR,
    QUEUE_NO_REPLY_DIR,
    QueueError,
    TransientQueueError,
    PermanentQueueError
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
        
        with pytest.raises(QueueError):
            load_notification(non_existent_file)
    
    def test_load_notification_invalid_json(self, tmp_path):
        """Test loading notification with invalid JSON."""
        invalid_json_file = tmp_path / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write("invalid json content")
        
        with pytest.raises(PermanentQueueError):
            load_notification(invalid_json_file)
    
    @patch('utils.queue_manager.QUEUE_DIR', Path("test_queue"))
    @patch('utils.queue_manager.QUEUE_ERROR_DIR', Path("test_queue/errors"))
    @patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', Path("test_queue/no_reply"))
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
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            with patch('utils.queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing
                    result = list_notifications()
                    
                    assert len(result) == 2
                    assert any(n["uri"] == "at://test1.bsky.social/post/123" for n in result)
                    assert any(n["uri"] == "at://test2.bsky.social/post/456" for n in result)
    
    @patch('utils.queue_manager.QUEUE_DIR', Path("test_queue"))
    @patch('utils.queue_manager.QUEUE_ERROR_DIR', Path("test_queue/errors"))
    @patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', Path("test_queue/no_reply"))
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
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            with patch('utils.queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing with filter
                    result = list_notifications(handle_filter="test1.bsky.social")
                    
                    assert len(result) == 1
                    assert result[0]["uri"] == "at://test1.bsky.social/post/123"
    
    @patch('utils.queue_manager.QUEUE_DIR', Path("test_queue"))
    @patch('utils.queue_manager.QUEUE_ERROR_DIR', Path("test_queue/errors"))
    @patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', Path("test_queue/no_reply"))
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
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            with patch('utils.queue_manager.QUEUE_ERROR_DIR', error_dir):
                with patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', no_reply_dir):
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
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            # Mock console.print and Confirm.ask
            with patch('utils.queue_manager.console.print') as mock_print:
                with patch('utils.queue_manager.Confirm.ask', return_value=True):
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
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            # Mock console.print
            with patch('utils.queue_manager.console.print') as mock_print:
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
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            # Mock console.print
            with patch('utils.queue_manager.console.print') as mock_print:
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
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            # Mock console.print and Confirm.ask
            with patch('utils.queue_manager.console.print') as mock_print:
                with patch('utils.queue_manager.Confirm.ask', return_value=False):
                    delete_by_handle("test1.bsky.social")
                    
                    # Verify file was not deleted
                    assert len(list(queue_dir.glob("*.json"))) == 1
    
    def test_queue_directories_defined(self):
        """Test that queue directories are properly defined."""
        assert QUEUE_DIR == Path("queue")
        assert QUEUE_ERROR_DIR == QUEUE_DIR / "errors"
        assert QUEUE_NO_REPLY_DIR == QUEUE_DIR / "no_reply"
    
    @patch('utils.queue_manager.QUEUE_DIR', Path("test_queue"))
    def test_list_notifications_empty_queue(self, tmp_path):
        """Test listing notifications from empty queue."""
        # Create empty queue directory
        queue_dir = tmp_path / "test_queue"
        queue_dir.mkdir()

        # Mock the queue directories
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            with patch('utils.queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing
                    result = list_notifications()
                    
                    assert result is None
    
    @patch('utils.queue_manager.QUEUE_DIR', Path("test_queue"))
    def test_list_notifications_nonexistent_directories(self, tmp_path):
        """Test listing notifications when directories don't exist."""
        # Don't create any directories

        # Mock the queue directories
        with patch('utils.queue_manager.QUEUE_DIR', tmp_path / "nonexistent"):
            with patch('utils.queue_manager.QUEUE_ERROR_DIR', tmp_path / "nonexistent" / "errors"):
                with patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', tmp_path / "nonexistent" / "no_reply"):
                    # Test listing
                    result = list_notifications()
                    
                    assert result is None
    
    def test_load_notification_permission_error(self, tmp_path):
        """Test loading notification with permission error."""
        # Create a file that can't be read
        notification_file = tmp_path / "test_notification.json"
        notification_file.write_text('{"test": "data"}')
        
        # Mock open to raise permission error
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(TransientQueueError):
                load_notification(notification_file)
    
    @patch('utils.queue_manager.QUEUE_DIR', Path("test_queue"))
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
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            with patch('utils.queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing
                    result = list_notifications()
                    
                    # Should only return valid notifications
                    assert len(result) == 1
                    assert result[0]["uri"] == "at://valid.bsky.social/post/123"

    def test_list_notifications_with_handle_filter_no_matches(self, tmp_path):
        """Test listing notifications with handle filter that matches nothing."""
        # Create queue directory
        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()
        
        # Create valid notification file
        notification_file = queue_dir / "test_notification.json"
        notification_data = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": "Test notification"},
            "reason": "mention"
        }
        notification_file.write_text(json.dumps(notification_data))
        
        # Mock the queue directories
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            with patch('utils.queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing with filter that won't match
                    result = list_notifications(handle_filter="nonexistent")
                    
                    assert result is None

    def test_list_notifications_with_long_text_truncation(self, tmp_path):
        """Test listing notifications with long text that gets truncated."""
        # Create queue directory
        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()
        
        # Create notification with long text
        long_text = "This is a very long notification text that should be truncated when displayed in the table because it exceeds the 40 character limit"
        notification_file = queue_dir / "test_notification.json"
        notification_data = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social", "did": "did:plc:test"},
            "record": {"text": long_text},
            "reason": "mention"
        }
        notification_file.write_text(json.dumps(notification_data))
        
        # Mock the queue directories
        with patch('utils.queue_manager.QUEUE_DIR', queue_dir):
            with patch('utils.queue_manager.QUEUE_ERROR_DIR', queue_dir / "errors"):
                with patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', queue_dir / "no_reply"):
                    # Test listing
                    result = list_notifications()
                    
                    assert result is not None
                    assert len(result) == 1
                    assert result[0]['record']['text'] == long_text

    def test_cli_main_list_command(self):
        """Test CLI main function with list command."""
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Execute the CLI main block code
            import argparse
            
            parser = argparse.ArgumentParser(description="Manage Void bot notification queue")
            subparsers = parser.add_subparsers(dest='command', help='Commands')
            
            # List command
            list_parser = subparsers.add_parser('list', help='List notifications in queue')
            list_parser.add_argument('--handle', help='Filter by handle (partial match)')
            list_parser.add_argument('--all', action='store_true', help='Include errors and no_reply folders')
            
            # Delete command
            delete_parser = subparsers.add_parser('delete', help='Delete notifications from a specific handle')
            delete_parser.add_argument('handle', help='Handle to delete notifications from')
            delete_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
            delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
            
            # Stats command
            stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
            
            # Count command
            count_parser = subparsers.add_parser('count', help='Show detailed count by handle')
            
            args = parser.parse_args(['list'])
            
            if args.command == 'list':
                list_notifications(args.handle, args.all)
            elif args.command == 'delete':
                delete_by_handle(args.handle, args.dry_run, args.force)
            elif args.command == 'stats':
                stats()
            elif args.command == 'count':
                count_by_handle()
            else:
                parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify output contains expected message (no valid notifications due to corrupted files)
        assert 'No notifications found in queue' in output

    def test_cli_main_delete_command(self):
        """Test CLI main function with delete command."""
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Execute the CLI main block code
            import argparse
            
            parser = argparse.ArgumentParser(description="Manage Void bot notification queue")
            subparsers = parser.add_subparsers(dest='command', help='Commands')
            
            # List command
            list_parser = subparsers.add_parser('list', help='List notifications in queue')
            list_parser.add_argument('--handle', help='Filter by handle (partial match)')
            list_parser.add_argument('--all', action='store_true', help='Include errors and no_reply folders')
            
            # Delete command
            delete_parser = subparsers.add_parser('delete', help='Delete notifications from a specific handle')
            delete_parser.add_argument('handle', help='Handle to delete notifications from')
            delete_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
            delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
            
            # Stats command
            stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
            
            # Count command
            count_parser = subparsers.add_parser('count', help='Show detailed count by handle')
            
            args = parser.parse_args(['delete', 'test.user.bsky.social', '--force'])
            
            if args.command == 'list':
                list_notifications(args.handle, args.all)
            elif args.command == 'delete':
                delete_by_handle(args.handle, args.dry_run, args.force)
            elif args.command == 'stats':
                stats()
            elif args.command == 'count':
                count_by_handle()
            else:
                parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify output contains expected message (queue has notifications)
        assert 'test.user.bsky.social' in output

    def test_cli_main_stats_command(self):
        """Test CLI main function with stats command."""
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Execute the CLI main block code
            import argparse
            
            parser = argparse.ArgumentParser(description="Manage Void bot notification queue")
            subparsers = parser.add_subparsers(dest='command', help='Commands')
            
            # List command
            list_parser = subparsers.add_parser('list', help='List notifications in queue')
            list_parser.add_argument('--handle', help='Filter by handle (partial match)')
            list_parser.add_argument('--all', action='store_true', help='Include errors and no_reply folders')
            
            # Delete command
            delete_parser = subparsers.add_parser('delete', help='Delete notifications from a specific handle')
            delete_parser.add_argument('handle', help='Handle to delete notifications from')
            delete_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
            delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
            
            # Stats command
            stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
            
            # Count command
            count_parser = subparsers.add_parser('count', help='Show detailed count by handle')
            
            args = parser.parse_args(['stats'])
            
            if args.command == 'list':
                list_notifications(args.handle, args.all)
            elif args.command == 'delete':
                delete_by_handle(args.handle, args.dry_run, args.force)
            elif args.command == 'stats':
                stats()
            elif args.command == 'count':
                count_by_handle()
            else:
                parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify output contains expected message
        assert 'Queue Statistics' in output

    def test_cli_main_count_command(self):
        """Test CLI main function with count command."""
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Execute the CLI main block code
            import argparse
            
            parser = argparse.ArgumentParser(description="Manage Void bot notification queue")
            subparsers = parser.add_subparsers(dest='command', help='Commands')
            
            # List command
            list_parser = subparsers.add_parser('list', help='List notifications in queue')
            list_parser.add_argument('--handle', help='Filter by handle (partial match)')
            list_parser.add_argument('--all', action='store_true', help='Include errors and no_reply folders')
            
            # Delete command
            delete_parser = subparsers.add_parser('delete', help='Delete notifications from a specific handle')
            delete_parser.add_argument('handle', help='Handle to delete notifications from')
            delete_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
            delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
            
            # Stats command
            stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
            
            # Count command
            count_parser = subparsers.add_parser('count', help='Show detailed count by handle')
            
            args = parser.parse_args(['count'])
            
            if args.command == 'list':
                list_notifications(args.handle, args.all)
            elif args.command == 'delete':
                delete_by_handle(args.handle, args.dry_run, args.force)
            elif args.command == 'stats':
                stats()
            elif args.command == 'count':
                count_by_handle()
            else:
                parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify output contains expected message (no valid notifications due to corrupted files)
        assert 'No notifications found in any queue' in output

    def test_cli_main_no_command(self):
        """Test CLI main function with no command (should print help)."""
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Execute the CLI main block code
            import argparse
            
            parser = argparse.ArgumentParser(description="Manage Void bot notification queue")
            subparsers = parser.add_subparsers(dest='command', help='Commands')
            
            # List command
            list_parser = subparsers.add_parser('list', help='List notifications in queue')
            list_parser.add_argument('--handle', help='Filter by handle (partial match)')
            list_parser.add_argument('--all', action='store_true', help='Include errors and no_reply folders')
            
            # Delete command
            delete_parser = subparsers.add_parser('delete', help='Delete notifications from a specific handle')
            delete_parser.add_argument('handle', help='Handle to delete notifications from')
            delete_parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without deleting')
            delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
            
            # Stats command
            stats_parser = subparsers.add_parser('stats', help='Show queue statistics')
            
            # Count command
            count_parser = subparsers.add_parser('count', help='Show detailed count by handle')
            
            args = parser.parse_args([])
            
            if args.command == 'list':
                list_notifications(args.handle, args.all)
            elif args.command == 'delete':
                delete_by_handle(args.handle, args.dry_run, args.force)
            elif args.command == 'stats':
                stats()
            elif args.command == 'count':
                count_by_handle()
            else:
                parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify output contains help message
        assert 'Manage Void bot notification queue' in output

    def test_cli_main_function_list_with_handle(self):
        """Test CLI main function with list command and handle filter."""
        import utils.queue_manager
        from unittest.mock import patch
        
        with patch('utils.queue_manager.list_notifications') as mock_list_notifications:
            with patch('sys.argv', ['queue_manager.py', 'list', '--handle', 'test.user']):
                try:
                    utils.queue_manager.main()
                except SystemExit:
                    pass
            
            mock_list_notifications.assert_called_once_with('test.user', False)

    def test_cli_main_function_list_with_all(self):
        """Test CLI main function with list command and --all flag."""
        import utils.queue_manager
        from unittest.mock import patch
        
        with patch('utils.queue_manager.list_notifications') as mock_list_notifications:
            with patch('sys.argv', ['queue_manager.py', 'list', '--all']):
                try:
                    utils.queue_manager.main()
                except SystemExit:
                    pass
            
            mock_list_notifications.assert_called_once_with(None, True)

    def test_cli_main_function_delete_with_dry_run(self):
        """Test CLI main function with delete command and dry-run."""
        import utils.queue_manager
        from unittest.mock import patch
        
        with patch('utils.queue_manager.delete_by_handle') as mock_delete:
            with patch('sys.argv', ['queue_manager.py', 'delete', 'test.user', '--dry-run']):
                try:
                    utils.queue_manager.main()
                except SystemExit:
                    pass
            
            mock_delete.assert_called_once_with('test.user', True, False)

    def test_cli_main_function_delete_with_force(self):
        """Test CLI main function with delete command and force."""
        import utils.queue_manager
        from unittest.mock import patch
        
        with patch('utils.queue_manager.delete_by_handle') as mock_delete:
            with patch('sys.argv', ['queue_manager.py', 'delete', 'test.user', '--force']):
                try:
                    utils.queue_manager.main()
                except SystemExit:
                    pass
            
            mock_delete.assert_called_once_with('test.user', False, True)

    def test_cli_main_function_stats(self):
        """Test CLI main function with stats command."""
        import utils.queue_manager
        from unittest.mock import patch
        
        with patch('utils.queue_manager.stats') as mock_stats:
            with patch('sys.argv', ['queue_manager.py', 'stats']):
                try:
                    utils.queue_manager.main()
                except SystemExit:
                    pass
            
            mock_stats.assert_called_once()

    def test_cli_main_function_count(self):
        """Test CLI main function with count command."""
        import utils.queue_manager
        from unittest.mock import patch
        
        with patch('utils.queue_manager.count_by_handle') as mock_count:
            with patch('sys.argv', ['queue_manager.py', 'count']):
                try:
                    utils.queue_manager.main()
                except SystemExit:
                    pass
            
            mock_count.assert_called_once()

    def test_cli_main_function_no_command(self):
        """Test CLI main function with no command (should print help)."""
        import utils.queue_manager
        from unittest.mock import patch
        
        with patch('utils.queue_manager.argparse.ArgumentParser.print_help') as mock_help:
            with patch('sys.argv', ['queue_manager.py']):
                try:
                    utils.queue_manager.main()
                except SystemExit:
                    pass
            
            mock_help.assert_called_once()

    def test_list_notifications_unknown_directory(self):
        """Test list_notifications with unknown directory source."""
        import utils.queue_manager
        from unittest.mock import patch, Mock
        from pathlib import Path
        
        # Create a mock directory that doesn't match any known directories
        mock_dir = Mock(spec=Path)
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = []
        
        # Mock the directory constants to return different values
        with patch('utils.queue_manager.QUEUE_DIR', Path('/queue')), \
             patch('utils.queue_manager.QUEUE_ERROR_DIR', Path('/errors')), \
             patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', Path('/no_reply')):
            
            # Create a directory that doesn't match any of the known ones
            unknown_dir = Mock(spec=Path)
            unknown_dir.exists.return_value = True
            unknown_dir.glob.return_value = []
            
            with patch('utils.queue_manager.Path') as mock_path:
                mock_path.return_value = unknown_dir
                
                result = utils.queue_manager.list_notifications()
                
                # Should return None when no notifications found
                assert result is None

    def test_count_by_handle_nonexistent_directory(self):
        """Test count_by_handle with nonexistent directories."""
        import utils.queue_manager
        from unittest.mock import patch, Mock
        from pathlib import Path
        
        # Mock directories that don't exist
        mock_dir = Mock(spec=Path)
        mock_dir.exists.return_value = False
        
        with patch('utils.queue_manager.QUEUE_DIR', mock_dir), \
             patch('utils.queue_manager.QUEUE_ERROR_DIR', mock_dir), \
             patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', mock_dir):
            
            result = utils.queue_manager.count_by_handle()
            
            # Should return None when no directories exist
            assert result is None

    def test_count_by_handle_subdirectory_skip(self):
        """Test count_by_handle skipping subdirectories."""
        import utils.queue_manager
        from unittest.mock import patch, Mock
        from pathlib import Path
        
        # Create a mock directory with a subdirectory
        mock_dir = Mock(spec=Path)
        mock_dir.exists.return_value = True
        
        # Create a mock filepath that is a directory
        mock_filepath = Mock(spec=Path)
        mock_filepath.is_dir.return_value = True
        mock_filepath.name = "subdir"
        
        mock_dir.glob.return_value = [mock_filepath]
        
        with patch('utils.queue_manager.QUEUE_DIR', mock_dir), \
             patch('utils.queue_manager.QUEUE_ERROR_DIR', mock_dir), \
             patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', mock_dir):
            
            result = utils.queue_manager.count_by_handle()
            
            # Should return None when only subdirectories are found
            assert result is None
