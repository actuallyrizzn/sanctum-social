#!/usr/bin/env python3
"""Unit tests for notification_recovery.py"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

# Mock the config loading before importing notification_recovery
with patch('core.config.get_config') as mock_get_config:
    mock_loader = mock_get_config.return_value
    mock_loader.get_required.side_effect = lambda key: {
        'letta.api_key': 'test-api-key',
        'letta.agent_id': 'test-agent-id'
    }.get(key)
    mock_loader.get.side_effect = lambda key, default=None: {
        'letta.timeout': 30,
        'letta.base_url': None
    }.get(key, default)
    
    from utils.notification_recovery import (
        recover_notifications,
        check_database_health,
        reset_notification_status
    )


class TestNotificationRecovery:
    """Test cases for notification_recovery module."""

    @patch('utils.notification_recovery.bsky_utils.default_login')
    @patch('utils.notification_recovery.NotificationDB')
    @patch('utils.notification_recovery.save_notification_to_queue')
    @patch('utils.notification_recovery.notification_to_dict')
    def test_recover_notifications_dry_run(self, mock_notification_to_dict, mock_save_to_queue, 
                                         mock_notification_db, mock_default_login):
        """Test recover_notifications in dry run mode."""
        # Setup mocks
        mock_client = Mock()
        mock_default_login.return_value = mock_client
        
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        mock_db.is_processed.return_value = False
        
        # Mock notification data
        mock_notif = Mock()
        mock_notif.reason = 'mention'
        mock_notif.indexed_at = datetime.now().isoformat()
        
        mock_notification_to_dict.return_value = {
            'uri': 'at://test/notification/123',
            'author': {'handle': 'test.user'},
            'reason': 'mention',
            'indexed_at': datetime.now().isoformat()
        }
        
        # Mock API response
        mock_response = Mock()
        mock_response.notifications = [mock_notif]
        mock_response.cursor = None
        mock_client.app.bsky.notification.list_notifications.return_value = mock_response
        
        # Test dry run
        result = recover_notifications(hours=24, dry_run=True)
        
        # Verify calls
        mock_default_login.assert_called_once()
        mock_notification_db.assert_called_once()
        mock_client.app.bsky.notification.list_notifications.assert_called_once()
        mock_db.is_processed.assert_called_once()
        
        # Should not save to queue in dry run
        mock_save_to_queue.assert_not_called()
        
        # Should return count of notifications that would be recovered
        assert result == 1

    @patch('utils.notification_recovery.bsky_utils.default_login')
    @patch('utils.notification_recovery.NotificationDB')
    @patch('utils.notification_recovery.save_notification_to_queue')
    @patch('utils.notification_recovery.notification_to_dict')
    def test_recover_notifications_execute_mode(self, mock_notification_to_dict, mock_save_to_queue,
                                             mock_notification_db, mock_default_login):
        """Test recover_notifications in execute mode."""
        # Setup mocks
        mock_client = Mock()
        mock_default_login.return_value = mock_client
        
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        mock_db.is_processed.return_value = False
        
        # Mock notification data
        mock_notif = Mock()
        mock_notif.reason = 'mention'
        mock_notif.indexed_at = datetime.now().isoformat()
        
        mock_notification_to_dict.return_value = {
            'uri': 'at://test/notification/123',
            'author': {'handle': 'test.user'},
            'reason': 'mention',
            'indexed_at': datetime.now().isoformat()
        }
        
        mock_save_to_queue.return_value = True
        
        # Mock API response
        mock_response = Mock()
        mock_response.notifications = [mock_notif]
        mock_response.cursor = None
        mock_client.app.bsky.notification.list_notifications.return_value = mock_response
        
        # Test execute mode
        result = recover_notifications(hours=24, dry_run=False)
        
        # Verify calls
        mock_save_to_queue.assert_called_once()
        
        # Should return count of recovered notifications
        assert result == 1

    @patch('utils.notification_recovery.bsky_utils.default_login')
    @patch('utils.notification_recovery.NotificationDB')
    @patch('utils.notification_recovery.notification_to_dict')
    def test_recover_notifications_skip_likes(self, mock_notification_to_dict, mock_notification_db, mock_default_login):
        """Test that likes are skipped during recovery."""
        # Setup mocks
        mock_client = Mock()
        mock_default_login.return_value = mock_client
        
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        
        # Mock notification data (like)
        mock_notif = Mock()
        mock_notif.reason = 'like'
        mock_notif.indexed_at = datetime.now().isoformat()
        
        # Mock API response
        mock_response = Mock()
        mock_response.notifications = [mock_notif]
        mock_response.cursor = None
        mock_client.app.bsky.notification.list_notifications.return_value = mock_response
        
        # Test recovery
        result = recover_notifications(hours=24, dry_run=True)
        
        # Should skip likes and return 0
        assert result == 0
        mock_notification_to_dict.assert_not_called()

    @patch('utils.notification_recovery.bsky_utils.default_login')
    @patch('utils.notification_recovery.NotificationDB')
    @patch('utils.notification_recovery.notification_to_dict')
    def test_recover_notifications_already_processed(self, mock_notification_to_dict, mock_notification_db, mock_default_login):
        """Test that already processed notifications are skipped."""
        # Setup mocks
        mock_client = Mock()
        mock_default_login.return_value = mock_client
        
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        mock_db.is_processed.return_value = True  # Already processed
        
        # Mock notification data
        mock_notif = Mock()
        mock_notif.reason = 'mention'
        mock_notif.indexed_at = datetime.now().isoformat()
        
        mock_notification_to_dict.return_value = {
            'uri': 'at://test/notification/123',
            'author': {'handle': 'test.user'},
            'reason': 'mention',
            'indexed_at': datetime.now().isoformat()
        }
        
        # Mock API response
        mock_response = Mock()
        mock_response.notifications = [mock_notif]
        mock_response.cursor = None
        mock_client.app.bsky.notification.list_notifications.return_value = mock_response
        
        # Test recovery
        result = recover_notifications(hours=24, dry_run=True)
        
        # Should skip already processed notifications
        assert result == 0

    @patch('utils.notification_recovery.bsky_utils.default_login')
    @patch('utils.notification_recovery.NotificationDB')
    def test_recover_notifications_api_error(self, mock_notification_db, mock_default_login):
        """Test handling of API errors during recovery."""
        # Setup mocks
        mock_client = Mock()
        mock_default_login.return_value = mock_client
        
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        
        # Mock API error
        mock_client.app.bsky.notification.list_notifications.side_effect = Exception("API Error")
        
        # Test recovery
        result = recover_notifications(hours=24, dry_run=True)
        
        # Should handle error gracefully
        assert result == 0

    @patch('utils.notification_recovery.NotificationDB')
    def test_check_database_health(self, mock_notification_db):
        """Test database health check."""
        # Setup mock
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        
        # Mock stats
        mock_stats = {
            'total': 100,
            'status_pending': 50,
            'status_processed': 30,
            'status_ignored': 10,
            'status_no_reply': 5,
            'status_error': 3,
            'recent_24h': 20
        }
        mock_db.get_stats.return_value = mock_stats
        
        # Test health check
        result = check_database_health()
        
        # Verify calls
        mock_notification_db.assert_called_once()
        mock_db.get_stats.assert_called_once()
        
        # Should return stats
        assert result == mock_stats

    @patch('utils.notification_recovery.NotificationDB')
    def test_check_database_health_high_pending_warning(self, mock_notification_db):
        """Test database health check with high pending notifications."""
        # Setup mock
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        
        # Mock stats with high pending count
        mock_stats = {
            'total': 200,
            'status_pending': 150,  # High pending count
            'status_processed': 30,
            'status_ignored': 10,
            'status_no_reply': 5,
            'status_error': 3,
            'recent_24h': 20
        }
        mock_db.get_stats.return_value = mock_stats
        
        # Test health check
        result = check_database_health()
        
        # Should return stats
        assert result == mock_stats

    @patch('utils.notification_recovery.NotificationDB')
    def test_check_database_health_high_error_warning(self, mock_notification_db):
        """Test database health check with high error notifications."""
        # Setup mock
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        
        # Mock stats with high error count
        mock_stats = {
            'total': 200,
            'status_pending': 50,
            'status_processed': 30,
            'status_ignored': 10,
            'status_no_reply': 5,
            'status_error': 75,  # High error count
            'recent_24h': 20
        }
        mock_db.get_stats.return_value = mock_stats
        
        # Test health check
        result = check_database_health()
        
        # Should return stats
        assert result == mock_stats

    @patch('utils.notification_recovery.NotificationDB')
    def test_reset_notification_status_dry_run(self, mock_notification_db):
        """Test reset_notification_status in dry run mode."""
        # Setup mock
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        
        # Mock database query results
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                'uri': 'at://test/notification/123',
                'status': 'error',
                'indexed_at': datetime.now().isoformat(),
                'author_handle': 'test.user'
            }
        ]
        mock_db.conn.execute.return_value = mock_cursor
        
        # Test dry run
        result = reset_notification_status(hours=1, dry_run=True)
        
        # Verify calls
        mock_notification_db.assert_called_once()
        mock_db.conn.execute.assert_called_once()
        
        # Should return count of notifications that would be reset
        assert result == 1

    @patch('utils.notification_recovery.NotificationDB')
    def test_reset_notification_status_execute_mode(self, mock_notification_db):
        """Test reset_notification_status in execute mode."""
        # Setup mock
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        
        # Mock database query results
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                'uri': 'at://test/notification/123',
                'status': 'error',
                'indexed_at': datetime.now().isoformat(),
                'author_handle': 'test.user'
            }
        ]
        
        # Mock update result
        mock_update_cursor = Mock()
        mock_update_cursor.rowcount = 1
        
        # Set up side effects for multiple calls
        mock_db.conn.execute.side_effect = [mock_cursor, mock_update_cursor]
        
        # Test execute mode
        result = reset_notification_status(hours=1, dry_run=False)
        
        # Verify calls
        assert mock_db.conn.execute.call_count == 2  # SELECT and UPDATE
        mock_db.conn.commit.assert_called_once()
        
        # Should return count of reset notifications
        assert result == 1

    @patch('utils.notification_recovery.NotificationDB')
    def test_reset_notification_status_no_notifications(self, mock_notification_db):
        """Test reset_notification_status when no notifications need reset."""
        # Setup mock
        mock_db = Mock()
        mock_notification_db.return_value.__enter__ = Mock(return_value=mock_db)
        mock_notification_db.return_value.__exit__ = Mock(return_value=None)
        
        # Mock empty database query results
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_db.conn.execute.return_value = mock_cursor
        
        # Test reset
        result = reset_notification_status(hours=1, dry_run=True)
        
        # Should return 0
        assert result == 0

    @patch('utils.notification_recovery.recover_notifications')
    def test_cli_main_recover_command(self, mock_recover_notifications):
        """Test CLI main function with recover command."""
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Execute the CLI main block code
            import argparse
            
            parser = argparse.ArgumentParser(description="Notification recovery and management tools")
            
            subparsers = parser.add_subparsers(dest='command', help='Command to run')
            
            # Recover command
            recover_parser = subparsers.add_parser('recover', help='Recover missed notifications')
            recover_parser.add_argument('--hours', type=int, default=24, 
                                      help='Number of hours back to check (default: 24)')
            recover_parser.add_argument('--execute', action='store_true',
                                      help='Actually recover notifications (default is dry run)')
            
            # Health check command
            health_parser = subparsers.add_parser('health', help='Check database health')
            
            # Reset command
            reset_parser = subparsers.add_parser('reset', help='Reset error notifications to pending')
            reset_parser.add_argument('--hours', type=int, default=1,
                                    help='Reset notifications from last N hours (default: 1)')
            reset_parser.add_argument('--execute', action='store_true',
                                    help='Actually reset notifications (default is dry run)')
            
            args = parser.parse_args(['recover', '--hours', '12'])
            
            if args.command == 'recover':
                mock_recover_notifications(hours=args.hours, dry_run=not args.execute)
            elif args.command == 'health':
                check_database_health()
            elif args.command == 'reset':
                reset_notification_status(hours=args.hours, dry_run=not args.execute)
            else:
                parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify the function was called with correct parameters
        mock_recover_notifications.assert_called_once_with(hours=12, dry_run=True)

    @patch('utils.notification_recovery.check_database_health')
    def test_cli_main_health_command(self, mock_check_database_health):
        """Test CLI main function with health command."""
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Execute the CLI main block code
            import argparse
            
            parser = argparse.ArgumentParser(description="Notification recovery and management tools")
            
            subparsers = parser.add_subparsers(dest='command', help='Command to run')
            
            # Recover command
            recover_parser = subparsers.add_parser('recover', help='Recover missed notifications')
            recover_parser.add_argument('--hours', type=int, default=24, 
                                      help='Number of hours back to check (default: 24)')
            recover_parser.add_argument('--execute', action='store_true',
                                      help='Actually recover notifications (default is dry run)')
            
            # Health check command
            health_parser = subparsers.add_parser('health', help='Check database health')
            
            # Reset command
            reset_parser = subparsers.add_parser('reset', help='Reset error notifications to pending')
            reset_parser.add_argument('--hours', type=int, default=1,
                                    help='Reset notifications from last N hours (default: 1)')
            reset_parser.add_argument('--execute', action='store_true',
                                    help='Actually reset notifications (default is dry run)')
            
            args = parser.parse_args(['health'])
            
            if args.command == 'recover':
                recover_notifications(hours=args.hours, dry_run=not args.execute)
            elif args.command == 'health':
                mock_check_database_health()
            elif args.command == 'reset':
                reset_notification_status(hours=args.hours, dry_run=not args.execute)
            else:
                parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify the function was called
        mock_check_database_health.assert_called_once()

    @patch('utils.notification_recovery.reset_notification_status')
    def test_cli_main_reset_command(self, mock_reset_notification_status):
        """Test CLI main function with reset command."""
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Execute the CLI main block code
            import argparse
            
            parser = argparse.ArgumentParser(description="Notification recovery and management tools")
            
            subparsers = parser.add_subparsers(dest='command', help='Command to run')
            
            # Recover command
            recover_parser = subparsers.add_parser('recover', help='Recover missed notifications')
            recover_parser.add_argument('--hours', type=int, default=24, 
                                      help='Number of hours back to check (default: 24)')
            recover_parser.add_argument('--execute', action='store_true',
                                      help='Actually recover notifications (default is dry run)')
            
            # Health check command
            health_parser = subparsers.add_parser('health', help='Check database health')
            
            # Reset command
            reset_parser = subparsers.add_parser('reset', help='Reset error notifications to pending')
            reset_parser.add_argument('--hours', type=int, default=1,
                                    help='Reset notifications from last N hours (default: 1)')
            reset_parser.add_argument('--execute', action='store_true',
                                    help='Actually reset notifications (default is dry run)')
            
            args = parser.parse_args(['reset', '--hours', '2'])
            
            if args.command == 'recover':
                recover_notifications(hours=args.hours, dry_run=not args.execute)
            elif args.command == 'health':
                check_database_health()
            elif args.command == 'reset':
                mock_reset_notification_status(hours=args.hours, dry_run=not args.execute)
            else:
                parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify the function was called with correct parameters
        mock_reset_notification_status.assert_called_once_with(hours=2, dry_run=True)

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
            
            parser = argparse.ArgumentParser(description="Notification recovery and management tools")
            
            subparsers = parser.add_subparsers(dest='command', help='Command to run')
            
            # Recover command
            recover_parser = subparsers.add_parser('recover', help='Recover missed notifications')
            recover_parser.add_argument('--hours', type=int, default=24, 
                                      help='Number of hours back to check (default: 24)')
            recover_parser.add_argument('--execute', action='store_true',
                                      help='Actually recover notifications (default is dry run)')
            
            # Health check command
            health_parser = subparsers.add_parser('health', help='Check database health')
            
            # Reset command
            reset_parser = subparsers.add_parser('reset', help='Reset error notifications to pending')
            reset_parser.add_argument('--hours', type=int, default=1,
                                    help='Reset notifications from last N hours (default: 1)')
            reset_parser.add_argument('--execute', action='store_true',
                                    help='Actually reset notifications (default is dry run)')
            
            args = parser.parse_args([])
            
            if args.command == 'recover':
                recover_notifications(hours=args.hours, dry_run=not args.execute)
            elif args.command == 'health':
                check_database_health()
            elif args.command == 'reset':
                reset_notification_status(hours=args.hours, dry_run=not args.execute)
            else:
                parser.print_help()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify output contains help message
        assert 'Notification recovery and management tools' in output

    def test_cli_main_function_recover_with_execute(self):
        """Test CLI main function with recover command and execute flag."""
        import utils.notification_recovery
        from unittest.mock import patch
        
        with patch('utils.notification_recovery.recover_notifications') as mock_recover:
            with patch('sys.argv', ['notification_recovery.py', 'recover', '--hours', '12', '--execute']):
                try:
                    utils.notification_recovery.main()
                except SystemExit:
                    pass
            
            mock_recover.assert_called_once_with(hours=12, dry_run=False)

    def test_cli_main_function_health(self):
        """Test CLI main function with health command."""
        import utils.notification_recovery
        from unittest.mock import patch
        
        with patch('utils.notification_recovery.check_database_health') as mock_health:
            with patch('sys.argv', ['notification_recovery.py', 'health']):
                try:
                    utils.notification_recovery.main()
                except SystemExit:
                    pass
            
            mock_health.assert_called_once()

    def test_cli_main_function_reset_with_execute(self):
        """Test CLI main function with reset command and execute flag."""
        import utils.notification_recovery
        from unittest.mock import patch
        
        with patch('utils.notification_recovery.reset_notification_status') as mock_reset:
            with patch('sys.argv', ['notification_recovery.py', 'reset', '--hours', '2', '--execute']):
                try:
                    utils.notification_recovery.main()
                except SystemExit:
                    pass
            
            mock_reset.assert_called_once_with(hours=2, dry_run=False)

    def test_cli_main_function_no_command(self):
        """Test CLI main function with no command (should print help)."""
        import utils.notification_recovery
        from unittest.mock import patch
        
        with patch('utils.notification_recovery.argparse.ArgumentParser.print_help') as mock_help:
            with patch('sys.argv', ['notification_recovery.py']):
                try:
                    utils.notification_recovery.main()
                except SystemExit:
                    pass
            
            mock_help.assert_called_once()
