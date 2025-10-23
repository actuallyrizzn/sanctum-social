"""
End-to-end tests for the Void project.

These tests simulate real-world usage scenarios, testing the complete
workflow from notification processing to tool execution and response generation.
"""
import pytest
import tempfile
import shutil
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import main modules for E2E testing
from tool_manager import ensure_platform_tools, get_attached_tools
from utils.queue_manager import load_notification, list_notifications, delete_by_handle
from utils.notification_recovery import recover_notifications, check_database_health
from utils.notification_db import NotificationDB
from platforms.bluesky.tools.blocks import attach_user_blocks, user_note_append, user_note_view
from platforms.bluesky.tools.post import create_new_bluesky_post
from platforms.bluesky.tools.search import search_bluesky_posts
from platforms.bluesky.tools.feed import get_bluesky_feed


@pytest.mark.live
@pytest.mark.e2e
class TestBlueskyE2EWorkflow:
    """End-to-end tests for Bluesky workflow."""
    
    def test_complete_bluesky_notification_processing_workflow(self):
        """Test the complete workflow from notification to response."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test environment
            queue_dir = Path(temp_dir) / "queue"
            error_dir = Path(temp_dir) / "error"
            no_reply_dir = Path(temp_dir) / "no_reply"
            db_path = Path(temp_dir) / "test.db"
            
            queue_dir.mkdir()
            error_dir.mkdir()
            no_reply_dir.mkdir()
            
            # Mock the main bsky module components
            with patch('bsky.Letta') as mock_letta_class, \
                 patch('bsky.get_letta_config') as mock_get_config, \
                 patch('bsky.get_agent_config') as mock_get_agent_config, \
                 patch('bsky.NotificationDB') as mock_db_class, \
                 patch('bsky.QUEUE_DIR', queue_dir), \
                 patch('bsky.QUEUE_ERROR_DIR', error_dir), \
                 patch('bsky.QUEUE_NO_REPLY_DIR', no_reply_dir), \
                 patch('bsky.PROCESSED_NOTIFICATIONS_FILE', Path(temp_dir) / "processed.txt"):
                
                # Mock configuration
                mock_config = {
                    'api_key': 'test-api-key',
                    'base_url': 'https://test.letta.com',
                    'timeout': 30,
                    'agent_id': 'test-agent-id'
                }
                mock_get_config.return_value = mock_config
                mock_get_agent_config.return_value = {'agent_id': 'test-agent-id'}
                
                # Mock Letta client
                mock_client = Mock()
                mock_letta_class.return_value = mock_client
                
                # Mock agent retrieval
                mock_agent = Mock()
                mock_agent.id = 'test-agent-id'
                mock_client.agents.retrieve.return_value = mock_agent
                
                # Mock notification processing
                mock_notification = {
                    'uri': 'at://did:plc:test/post/1',
                    'cid': 'test_cid',
                    'record': {
                        'text': '@testbot hello there!',
                        'createdAt': '2025-01-01T00:00:00.000Z'
                    },
                    'author': {
                        'handle': 'test.user.bsky.social',
                        'displayName': 'Test User'
                    }
                }
                
                # Mock database
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                mock_db.add_notification.return_value = True
                
                # Mock tool execution
                mock_client.agents.run.return_value = {
                    'response': 'Hello! Thanks for mentioning me.',
                    'tools_used': ['user_note_append']
                }
                
                # Test the workflow
                # 1. Initialize the system
                result = bsky.initialize_void()
                assert "Void initialized" in result
                
                # 2. Process a notification
                result = bsky.process_notification(mock_notification)
                assert "Notification processed" in result
                
                # 3. Verify notification was saved to queue
                notifications = list_notifications(show_all=True)
                assert notifications is not None
                assert len(notifications) > 0

    def test_bluesky_tool_execution_e2e(self):
        """Test end-to-end tool execution for Bluesky."""
        with patch('os.getenv') as mock_getenv, \
             patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get:
            
            # Mock environment variables
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            # Mock session creation
            mock_session_response = Mock()
            mock_session_response.status_code = 200
            mock_session_response.json.return_value = {
                'accessJwt': 'test_token',
                'did': 'test_did',
                'handle': 'test.user.bsky.social'
            }
            mock_post.return_value = mock_session_response
            
            # Mock API responses
            mock_search_response = Mock()
            mock_search_response.status_code = 200
            mock_search_response.json.return_value = {
                'posts': [
                    {
                        'uri': 'at://did:plc:test/post/1',
                        'cid': 'test_cid',
                        'record': {
                            'text': 'Test post about AI',
                            'createdAt': '2025-01-01T00:00:00.000Z'
                        },
                        'author': {
                            'handle': 'test.user.bsky.social',
                            'displayName': 'Test User'
                        }
                    }
                ]
            }
            
            mock_feed_response = Mock()
            mock_feed_response.status_code = 200
            mock_feed_response.json.return_value = {
                'feed': [
                    {
                        'post': {
                            'uri': 'at://did:plc:test/post/2',
                            'cid': 'test_cid_2',
                            'record': {
                                'text': 'Interesting post',
                                'createdAt': '2025-01-01T01:00:00.000Z'
                            },
                            'author': {
                                'handle': 'another.user.bsky.social',
                                'displayName': 'Another User'
                            },
                            'likeCount': 10,
                            'repostCount': 5,
                            'replyCount': 3
                        }
                    }
                ]
            }
            
            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                'uri': 'at://did:plc:test/new_post/1',
                'cid': 'new_post_cid'
            }
            
            # Set up side effects for different API calls
            mock_post.side_effect = [mock_session_response, mock_post_response]
            mock_get.side_effect = [mock_search_response, mock_feed_response]
            
            # Test complete workflow
            # 1. Search for posts
            search_result = search_bluesky_posts("AI")
            assert "search_results" in search_result
            assert "Test post about AI" in search_result
            
            # 2. Get feed
            feed_result = get_bluesky_feed("home")
            assert "feed:" in feed_result
            assert "Interesting post" in feed_result
            
            # 3. Create a post
            post_result = create_new_bluesky_post(["Thanks for the interesting content!"])
            assert "Post created successfully" in post_result

    def test_bluesky_memory_management_e2e(self):
        """Test end-to-end memory management for Bluesky."""
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            
            # Mock block operations
            mock_client.agents.blocks.list.return_value = []
            mock_client.agents.blocks.create.return_value = Mock(id='new-block-id')
            mock_client.agents.blocks.attach.return_value = Mock()
            mock_client.agents.blocks.modify.return_value = Mock()
            
            # Test complete memory workflow
            # 1. Attach user blocks
            result = attach_user_blocks(['test.user.bsky.social'])
            assert "test.user.bsky.social: Attached" in result
            
            # 2. Add notes to user
            result = user_note_append('test.user.bsky.social', 'Likes AI content')
            assert "test.user.bsky.social: Note appended" in result
            
            result = user_note_append('test.user.bsky.social', 'Active in tech discussions')
            assert "test.user.bsky.social: Note appended" in result
            
            # 3. View user notes
            result = user_note_view('test.user.bsky.social')
            assert "test.user.bsky.social" in result
            assert "Likes AI content" in result
            assert "Active in tech discussions" in result


@pytest.mark.live
@pytest.mark.e2e
class TestXE2EWorkflow:
    """End-to-end tests for X (Twitter) workflow."""
    
    def test_complete_x_notification_processing_workflow(self):
        """Test the complete workflow from X notification to response."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test environment
            queue_dir = Path(temp_dir) / "queue"
            error_dir = Path(temp_dir) / "error"
            no_reply_dir = Path(temp_dir) / "no_reply"
            
            queue_dir.mkdir()
            error_dir.mkdir()
            no_reply_dir.mkdir()
            
            # Mock the main x module components
            with patch('x.Letta') as mock_letta_class, \
                 patch('x.get_letta_config') as mock_get_config, \
                 patch('x.get_agent_config') as mock_get_agent_config, \
                 patch('x.NotificationDB') as mock_db_class, \
                 patch('x.QUEUE_DIR', queue_dir), \
                 patch('x.QUEUE_ERROR_DIR', error_dir), \
                 patch('x.QUEUE_NO_REPLY_DIR', no_reply_dir), \
                 patch('x.PROCESSED_NOTIFICATIONS_FILE', Path(temp_dir) / "processed.txt"):
                
                # Mock configuration
                mock_config = {
                    'api_key': 'test-api-key',
                    'base_url': 'https://test.letta.com',
                    'timeout': 30,
                    'agent_id': 'test-agent-id'
                }
                mock_get_config.return_value = mock_config
                mock_get_agent_config.return_value = {'agent_id': 'test-agent-id'}
                
                # Mock Letta client
                mock_client = Mock()
                mock_letta_class.return_value = mock_client
                
                # Mock agent retrieval
                mock_agent = Mock()
                mock_agent.id = 'test-agent-id'
                mock_client.agents.retrieve.return_value = mock_agent
                
                # Mock X notification processing
                mock_notification = {
                    'id': '1234567890',
                    'text': '@testbot hello there!',
                    'created_at': '2025-01-01T00:00:00.000Z',
                    'user': {
                        'id': '123456789',
                        'screen_name': 'testuser',
                        'name': 'Test User'
                    }
                }
                
                # Mock database
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                mock_db.add_notification.return_value = True
                
                # Mock tool execution
                mock_client.agents.run.return_value = {
                    'response': 'Hello! Thanks for mentioning me.',
                    'tools_used': ['x_user_note_append']
                }
                
                # Test the workflow
                # 1. Initialize the system
                result = x.initialize_void()
                assert "Void initialized" in result
                
                # 2. Process a notification
                result = x.process_notification(mock_notification)
                assert "Notification processed" in result

    def test_x_memory_management_e2e(self):
        """Test end-to-end memory management for X."""
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            
            # Mock block operations
            mock_client.agents.blocks.list.return_value = []
            mock_client.agents.blocks.create.return_value = Mock(id='new-block-id')
            mock_client.agents.blocks.attach.return_value = Mock()
            mock_client.agents.blocks.modify.return_value = Mock()
            
            # Test complete memory workflow for X
            # 1. Attach X user blocks
            result = attach_user_blocks(['123456789'])  # X user ID
            assert "123456789: Attached" in result
            
            # 2. Add notes to X user
            result = user_note_append('123456789', 'Likes tech content')
            assert "123456789: Note appended" in result
            
            result = user_note_append('123456789', 'Frequent poster')
            assert "123456789: Note appended" in result
            
            # 3. View X user notes
            result = user_note_view('123456789')
            assert "123456789" in result
            assert "Likes tech content" in result
            assert "Frequent poster" in result


@pytest.mark.live
@pytest.mark.e2e
class TestCrossPlatformE2E:
    """End-to-end tests for cross-platform functionality."""
    
    def test_platform_switching_e2e(self):
        """Test switching between platforms in a complete workflow."""
        with patch('tool_manager.Letta') as mock_letta_class, \
             patch('tool_manager.get_letta_config') as mock_get_config, \
             patch('tool_manager.get_agent_config') as mock_get_agent_config:
            
            # Mock configuration
            mock_config = {
                'api_key': 'test-api-key',
                'base_url': 'https://test.letta.com',
                'timeout': 30,
                'agent_id': 'test-agent-id'
            }
            mock_get_config.return_value = mock_config
            mock_get_agent_config.return_value = {'agent_id': 'test-agent-id'}
            
            # Mock Letta client
            mock_client = Mock()
            mock_letta_class.return_value = mock_client
            
            # Mock agent retrieval
            mock_agent = Mock()
            mock_agent.id = 'test-agent-id'
            mock_client.agents.retrieve.return_value = mock_agent
            
            # Mock tool operations
            mock_client.agents.blocks.list.return_value = []
            mock_client.agents.blocks.create.return_value = Mock(id='new-tool-id')
            mock_client.agents.blocks.attach.return_value = Mock()
            
            # Test complete platform switching workflow
            # 1. Set up Bluesky tools
            result = ensure_platform_tools('bluesky', 'test-agent-id')
            assert "bluesky" in result.lower()
            
            # 2. Set up X tools
            result = ensure_platform_tools('x', 'test-agent-id')
            assert "x" in result.lower()
            
            # 3. Verify tools are attached
            result = get_attached_tools('test-agent-id')
            assert isinstance(result, set)
            assert len(result) > 0

    def test_tool_registration_and_management_e2e(self):
        """Test complete tool registration and management workflow."""
        with patch('register_tools.Letta') as mock_letta_class, \
             patch('register_tools.get_letta_config') as mock_get_config, \
             patch('tool_manager.Letta') as mock_tool_manager_letta_class, \
             patch('tool_manager.get_letta_config') as mock_tool_manager_config, \
             patch('tool_manager.get_agent_config') as mock_get_agent_config:
            
            # Mock configuration
            mock_config = {
                'api_key': 'test-api-key',
                'base_url': 'https://test.letta.com',
                'timeout': 30,
                'agent_id': 'test-agent-id'
            }
            mock_get_config.return_value = mock_config
            mock_tool_manager_config.return_value = mock_config
            mock_get_agent_config.return_value = {'agent_id': 'test-agent-id'}
            
            # Mock Letta client
            mock_client = Mock()
            mock_letta_class.return_value = mock_client
            mock_tool_manager_letta_class.return_value = mock_client
            
            # Mock agent retrieval
            mock_agent = Mock()
            mock_agent.id = 'test-agent-id'
            mock_client.agents.retrieve.return_value = mock_agent
            
            # Mock tool operations
            mock_client.agents.blocks.list.return_value = []
            mock_client.agents.blocks.create.return_value = Mock(id='new-tool-id')
            mock_client.agents.blocks.attach.return_value = Mock()
            
            # Test complete workflow
            # 1. Register tools
            result = register_tools()
            assert "Successfully registered" in result
            
            # 2. Ensure platform tools
            result = ensure_platform_tools('bluesky', 'test-agent-id')
            assert "bluesky" in result.lower()
            
            # 3. Get attached tools
            result = get_attached_tools('test-agent-id')
            assert isinstance(result, set)


@pytest.mark.live
@pytest.mark.e2e
class TestRecoveryAndMaintenanceE2E:
    """End-to-end tests for recovery and maintenance operations."""
    
    def test_notification_recovery_e2e(self):
        """Test complete notification recovery workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test environment
            queue_dir = Path(temp_dir) / "queue"
            error_dir = Path(temp_dir) / "error"
            no_reply_dir = Path(temp_dir) / "no_reply"
            db_path = Path(temp_dir) / "test.db"
            
            queue_dir.mkdir()
            error_dir.mkdir()
            no_reply_dir.mkdir()
            
            # Create test notification files
            test_notifications = [
                {
                    'uri': 'at://did:plc:test/post/1',
                    'cid': 'test_cid_1',
                    'record': {
                        'text': 'Test notification 1',
                        'createdAt': '2025-01-01T00:00:00.000Z'
                    },
                    'author': {
                        'handle': 'test.user.bsky.social',
                        'displayName': 'Test User'
                    }
                },
                {
                    'uri': 'at://did:plc:test/post/2',
                    'cid': 'test_cid_2',
                    'record': {
                        'text': 'Test notification 2',
                        'createdAt': '2025-01-01T01:00:00.000Z'
                    },
                    'author': {
                        'handle': 'another.user.bsky.social',
                        'displayName': 'Another User'
                    }
                }
            ]
            
            for i, notification in enumerate(test_notifications):
                notification_file = queue_dir / f"notification_{i}.json"
                with open(notification_file, 'w') as f:
                    json.dump(notification, f)
            
            # Mock database operations
            with patch('notification_recovery.NotificationDB') as mock_db_class, \
                 patch('notification_recovery.QUEUE_DIR', queue_dir):
                
                mock_db = Mock()
                mock_db_class.return_value = mock_db
                
                # Mock database queries
                mock_cursor = Mock()
                mock_cursor.fetchall.return_value = [
                    ('at://did:plc:test/post/1', 'pending'),
                    ('at://did:plc:test/post/2', 'pending')
                ]
                mock_db.conn.execute.return_value = mock_cursor
                
                # Test complete recovery workflow
                # 1. Check database health
                health_result = check_database_health()
                assert "Database health check completed" in health_result
                
                # 2. Recover notifications (dry run)
                recovery_result = recover_notifications(dry_run=True)
                assert "Found 2 notifications to recover" in recovery_result
                
                # 3. Recover notifications (execute)
                recovery_result = recover_notifications(dry_run=False)
                assert "Recovered 2 notifications" in recovery_result

    def test_queue_maintenance_e2e(self):
        """Test complete queue maintenance workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test environment
            queue_dir = Path(temp_dir) / "queue"
            error_dir = Path(temp_dir) / "error"
            no_reply_dir = Path(temp_dir) / "no_reply"
            
            queue_dir.mkdir()
            error_dir.mkdir()
            no_reply_dir.mkdir()
            
            # Create test notification files
            test_notifications = [
                {
                    'uri': 'at://did:plc:test/post/1',
                    'cid': 'test_cid_1',
                    'record': {
                        'text': 'Test notification 1',
                        'createdAt': '2025-01-01T00:00:00.000Z'
                    },
                    'author': {
                        'handle': 'test.user.bsky.social',
                        'displayName': 'Test User'
                    }
                },
                {
                    'uri': 'at://did:plc:test/post/2',
                    'cid': 'test_cid_2',
                    'record': {
                        'text': 'Test notification 2',
                        'createdAt': '2025-01-01T01:00:00.000Z'
                    },
                    'author': {
                        'handle': 'test.user.bsky.social',
                        'displayName': 'Test User'
                    }
                }
            ]
            
            for i, notification in enumerate(test_notifications):
                notification_file = queue_dir / f"notification_{i}.json"
                with open(notification_file, 'w') as f:
                    json.dump(notification, f)
            
            # Test complete queue maintenance workflow
            with patch('utils.queue_manager.QUEUE_DIR', queue_dir), \
                 patch('queue_manager.QUEUE_ERROR_DIR', error_dir), \
                 patch('queue_manager.QUEUE_NO_REPLY_DIR', no_reply_dir):
                
                # 1. List all notifications
                notifications = list_notifications(show_all=True)
                assert notifications is not None
                assert len(notifications) == 2
                
                # 2. Count by handle
                count = count_by_handle("test.user.bsky.social")
                assert count == 2
                
                # 3. Delete by handle
                result = delete_by_handle("test.user.bsky.social")
                assert "Deleted 2 notifications" in result
                
                # 4. Verify deletion
                notifications = list_notifications(show_all=True)
                assert notifications is None or len(notifications) == 0


class TestErrorRecoveryE2E:
    """End-to-end tests for error recovery scenarios."""
    
    def test_api_failure_recovery_e2e(self):
        """Test recovery from API failures."""
        with patch('os.getenv') as mock_getenv, \
             patch('requests.post') as mock_post, \
             patch('requests.get') as mock_get:
            
            # Mock environment variables
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            # Mock API failure
            mock_post.side_effect = Exception("API connection failed")
            
            # Test that tools handle API failures gracefully
            with pytest.raises(Exception, match="Error"):
                search_bluesky_posts("test query")
            
            with pytest.raises(Exception, match="Error"):
                get_bluesky_feed("home")
            
            with pytest.raises(Exception, match="Error"):
                create_new_bluesky_post(["Test post"])

    def test_database_corruption_recovery_e2e(self):
        """Test recovery from database corruption."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "corrupted.db"
            
            # Create a corrupted database file
            with open(db_path, 'w') as f:
                f.write("corrupted database content")
            
            # Test that the system handles database corruption gracefully
            with patch('utils.notification_recovery.NotificationDB') as mock_db_class:
                mock_db_class.side_effect = Exception("Database corruption detected")
                
                with pytest.raises(Exception, match="Database corruption detected"):
                    check_database_health()

    def test_file_system_error_recovery_e2e(self):
        """Test recovery from file system errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_dir = Path(temp_dir) / "queue"
            queue_dir.mkdir()
            
            # Create a file with permission issues
            restricted_file = queue_dir / "restricted.json"
            with open(restricted_file, 'w') as f:
                json.dump({"test": "data"}, f)
            
            # Make file read-only (simulate permission error)
            restricted_file.chmod(0o444)
            
            # Test that the system handles file permission errors gracefully
            with patch('utils.queue_manager.QUEUE_DIR', queue_dir), \
                 patch('utils.queue_manager.QUEUE_ERROR_DIR', Path(temp_dir) / "error"), \
                 patch('utils.queue_manager.QUEUE_NO_REPLY_DIR', Path(temp_dir) / "no_reply"):
                
                # Should handle permission errors gracefully
                notifications = list_notifications(show_all=True)
                # May return None or partial results, but shouldn't crash
                assert notifications is None or isinstance(notifications, list)
