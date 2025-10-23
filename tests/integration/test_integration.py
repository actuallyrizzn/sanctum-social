"""
Simplified integration tests for the Void project.

These tests verify that different components work together correctly,
focusing on components that don't have module-level config dependencies.
"""
import pytest
import tempfile
import shutil
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the modules we want to test integration between
from tool_manager import ensure_platform_tools, get_attached_tools
from utils.queue_manager import load_notification, list_notifications, delete_by_handle, count_by_handle, stats
from utils.notification_db import NotificationDB
from platforms.bluesky.tools.blocks import attach_user_blocks, detach_user_blocks, user_note_append
from platforms.bluesky.tools.post import create_new_bluesky_post
from platforms.bluesky.tools.search import search_bluesky_posts
from platforms.bluesky.tools.feed import get_bluesky_feed


@pytest.mark.live
@pytest.mark.integration
class TestQueueManagementIntegration:
    """Test integration between queue management and notification processing."""
    
    def test_notification_lifecycle_integration(self):
        """Test the complete lifecycle of a notification through the queue system."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test environment
            queue_dir = Path(temp_dir) / "queue"
            error_dir = Path(temp_dir) / "error"
            no_reply_dir = Path(temp_dir) / "no_reply"
            
            queue_dir.mkdir()
            error_dir.mkdir()
            no_reply_dir.mkdir()
            
            # Create a test notification file
            test_notification = {
                "uri": "at://did:plc:test/post/1",
                "cid": "test_cid",
                "record": {
                    "text": "Test notification",
                    "createdAt": "2025-01-01T00:00:00.000Z"
                },
                "author": {
                    "handle": "test.user.bsky.social",
                    "displayName": "Test User"
                }
            }
            
            notification_file = queue_dir / "test_notification.json"
            with open(notification_file, 'w') as f:
                json.dump(test_notification, f)
            
            # Test loading the notification
            with patch('queue_manager.QUEUE_DIR', queue_dir):
                loaded_notification = load_notification("test_notification")
                assert loaded_notification is not None
                assert loaded_notification['uri'] == "at://did:plc:test/post/1"
            
            # Test listing notifications
            with patch('queue_manager.QUEUE_DIR', queue_dir), \
                 patch('queue_manager.QUEUE_ERROR_DIR', error_dir), \
                 patch('queue_manager.QUEUE_NO_REPLY_DIR', no_reply_dir):
                
                notifications = list_notifications(show_all=True)
                assert notifications is not None
                assert len(notifications) > 0
                assert any(n['uri'] == "at://did:plc:test/post/1" for n in notifications)
            
            # Test counting by handle
            with patch('queue_manager.QUEUE_DIR', queue_dir), \
                 patch('queue_manager.QUEUE_ERROR_DIR', error_dir), \
                 patch('queue_manager.QUEUE_NO_REPLY_DIR', no_reply_dir):
                
                count = count_by_handle("test.user.bsky.social")
                assert count >= 1
            
            # Test stats
            with patch('queue_manager.QUEUE_DIR', queue_dir), \
                 patch('queue_manager.QUEUE_ERROR_DIR', error_dir), \
                 patch('queue_manager.QUEUE_NO_REPLY_DIR', no_reply_dir):
                
                stats_result = stats()
                assert "Total notifications" in stats_result
                assert "Queue: 1" in stats_result

    def test_notification_deletion_integration(self):
        """Test notification deletion and its effects on queue statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test environment
            queue_dir = Path(temp_dir) / "queue"
            queue_dir.mkdir()
            
            # Create multiple test notification files
            for i in range(3):
                test_notification = {
                    "uri": f"at://did:plc:test/post/{i}",
                    "cid": f"test_cid_{i}",
                    "record": {
                        "text": f"Test notification {i}",
                        "createdAt": "2025-01-01T00:00:00.000Z"
                    },
                    "author": {
                        "handle": "test.user.bsky.social",
                        "displayName": "Test User"
                    }
                }
                
                notification_file = queue_dir / f"test_notification_{i}.json"
                with open(notification_file, 'w') as f:
                    json.dump(test_notification, f)
            
            # Test initial count
            with patch('queue_manager.QUEUE_DIR', queue_dir), \
                 patch('queue_manager.QUEUE_ERROR_DIR', Path(temp_dir) / "error"), \
                 patch('queue_manager.QUEUE_NO_REPLY_DIR', Path(temp_dir) / "no_reply"):
                
                initial_count = count_by_handle("test.user.bsky.social")
                assert initial_count == 3
                
                # Delete notifications
                result = delete_by_handle("test.user.bsky.social")
                assert "Deleted 3 notifications" in result
                
                # Verify count is now 0
                final_count = count_by_handle("test.user.bsky.social")
                assert final_count == 0


@pytest.mark.live
@pytest.mark.integration
class TestToolsIntegration:
    """Test integration between different tools."""
    
    def test_blocks_tools_integration(self):
        """Test integration between different block management tools."""
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            
            # Mock existing blocks
            mock_existing_block = Mock()
            mock_existing_block.id = 'existing-block-id'
            mock_existing_block.name = 'test.handle'
            mock_client.agents.blocks.list.return_value = [mock_existing_block]
            
            # Mock block operations
            mock_client.agents.blocks.create.return_value = Mock(id='new-block-id')
            mock_client.agents.blocks.attach.return_value = Mock()
            mock_client.agents.blocks.modify.return_value = Mock()
            
            # Test attaching user blocks
            result = attach_user_blocks(['test.handle'])
            assert "test.handle: Already attached" in result
            
            # Test appending to user notes
            result = user_note_append('test.handle', 'New note')
            assert "test.handle: Note appended" in result
            
            # Test detaching user blocks
            mock_client.agents.blocks.detach.return_value = Mock()
            result = detach_user_blocks(['test.handle'])
            assert "test.handle: Detached" in result

    def test_bluesky_tools_integration(self):
        """Test integration between Bluesky tools (post, search, feed)."""
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
                            'text': 'Test post',
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
                            'uri': 'at://did:plc:test/post/1',
                            'cid': 'test_cid',
                            'record': {
                                'text': 'Feed post',
                                'createdAt': '2025-01-01T00:00:00.000Z'
                            },
                            'author': {
                                'handle': 'test.user.bsky.social',
                                'displayName': 'Test User'
                            },
                            'likeCount': 5,
                            'repostCount': 2,
                            'replyCount': 1
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
            
            # Test search functionality
            search_result = search_bluesky_posts("test query")
            assert "search_results" in search_result
            assert "Test post" in search_result
            
            # Test feed functionality
            feed_result = get_bluesky_feed("home")
            assert "feed:" in feed_result
            assert "Feed post" in feed_result
            
            # Test post creation
            post_result = create_new_bluesky_post(["New post content"])
            assert "Post created successfully" in post_result


@pytest.mark.live
@pytest.mark.integration
class TestCrossPlatformIntegration:
    """Test integration between Bluesky and X platform tools."""
    
    def test_platform_tool_switching(self):
        """Test switching between Bluesky and X platform tools."""
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
            
            # Test Bluesky platform tools
            result = ensure_platform_tools('bluesky', 'test-agent-id')
            assert "bluesky" in result.lower()
            
            # Test X platform tools
            result = ensure_platform_tools('x', 'test-agent-id')
            assert "x" in result.lower()
            
            # Verify the client was used for both platforms
            assert mock_client.agents.retrieve.call_count >= 2

    def test_tool_consistency_across_platforms(self):
        """Test that tools behave consistently across platforms."""
        with patch('tools.blocks.get_letta_client') as mock_get_bluesky_client, \
             patch('tools.blocks.get_x_letta_client') as mock_get_x_client:
            
            # Mock clients
            mock_bluesky_client = Mock()
            mock_x_client = Mock()
            mock_get_bluesky_client.return_value = mock_bluesky_client
            mock_get_x_client.return_value = mock_x_client
            
            # Mock block operations
            mock_bluesky_client.agents.blocks.list.return_value = []
            mock_x_client.agents.blocks.list.return_value = []
            
            mock_bluesky_client.agents.blocks.create.return_value = Mock(id='bluesky-block-id')
            mock_x_client.agents.blocks.create.return_value = Mock(id='x-block-id')
            
            mock_bluesky_client.agents.blocks.attach.return_value = Mock()
            mock_x_client.agents.blocks.attach.return_value = Mock()
            
            # Test Bluesky user blocks
            result = attach_user_blocks(['test.handle'])
            assert "test.handle: Attached" in result
            
            # Test X user blocks
            result = attach_user_blocks(['123456789'])  # X user ID
            assert "123456789: Attached" in result
            
            # Verify both clients were used
            mock_bluesky_client.agents.blocks.create.assert_called()
            mock_x_client.agents.blocks.create.assert_called()


@pytest.mark.live
@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test integration error handling across components."""
    
    def test_tool_registration_failure_recovery(self):
        """Test recovery from tool registration failures."""
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
            
            # Mock Letta client that raises an exception
            mock_client = Mock()
            mock_client.agents.retrieve.side_effect = Exception("Agent not found")
            mock_letta_class.return_value = mock_client
            
            # Test that tool management handles the error gracefully
            result = ensure_platform_tools('bluesky', 'test-agent-id')
            assert "Error: Agent not found" in result

    def test_queue_management_error_recovery(self):
        """Test error recovery in queue management."""
        with tempfile.TemporaryDirectory() as temp_dir:
            queue_dir = Path(temp_dir) / "queue"
            queue_dir.mkdir()
            
            # Create a malformed JSON file
            malformed_file = queue_dir / "malformed.json"
            with open(malformed_file, 'w') as f:
                f.write("{ invalid json")
            
            # Test that list_notifications handles malformed files gracefully
            with patch('queue_manager.QUEUE_DIR', queue_dir), \
                 patch('queue_manager.QUEUE_ERROR_DIR', Path(temp_dir) / "error"), \
                 patch('queue_manager.QUEUE_NO_REPLY_DIR', Path(temp_dir) / "no_reply"):
                
                notifications = list_notifications(show_all=True)
                # Should not crash, may return None or empty list
                assert notifications is None or isinstance(notifications, list)

    def test_database_connection_error_handling(self):
        """Test database connection error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Test that NotificationDB handles connection errors gracefully
            with patch('notification_db.sqlite3.connect') as mock_connect:
                mock_connect.side_effect = Exception("Database connection failed")
                
                with pytest.raises(Exception, match="Database connection failed"):
                    NotificationDB(str(db_path))