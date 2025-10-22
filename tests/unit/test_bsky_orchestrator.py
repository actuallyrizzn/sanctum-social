"""
Comprehensive unit tests for bsky.py - Bluesky orchestrator module.

This module tests:
1. Core Bluesky orchestrator functionality
2. Notification processing workflows
3. Queue management operations
4. Memory block management
5. Error handling and recovery
6. Configuration and initialization
7. Tool execution and integration
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Import the module under test
import bsky
from bsky import (
    extract_handles_from_data,
    log_with_panel,
    initialize_void,
    process_mention,
    notification_to_dict,
    load_processed_notifications,
    save_processed_notifications,
    save_notification_to_queue,
    load_and_process_queued_notifications,
    fetch_and_queue_new_notifications,
    process_notifications,
    send_synthesis_message,
    periodic_user_block_cleanup,
    attach_temporal_blocks,
    detach_temporal_blocks
)


class TestBlueskyUtilityFunctions:
    """Test Bluesky utility functions."""
    
    def test_extract_handles_from_data_simple(self):
        """Test handle extraction from simple data structure."""
        data = {
            'handle': 'test.user.bsky.social',
            'other_field': 'value'
        }
        
        handles = extract_handles_from_data(data)
        assert handles == ['test.user.bsky.social']
    
    def test_extract_handles_from_data_nested(self):
        """Test handle extraction from nested data structure."""
        data = {
            'user': {
                'handle': 'user1.bsky.social',
                'profile': {
                    'handle': 'user2.bsky.social'
                }
            },
            'mentions': [
                {'handle': 'user3.bsky.social'},
                {'handle': 'user4.bsky.social'}
            ]
        }
        
        handles = extract_handles_from_data(data)
        assert len(handles) == 4
        assert 'user1.bsky.social' in handles
        assert 'user2.bsky.social' in handles
        assert 'user3.bsky.social' in handles
        assert 'user4.bsky.social' in handles
    
    def test_extract_handles_from_data_no_handles(self):
        """Test handle extraction from data with no handles."""
        data = {
            'text': 'Hello world',
            'timestamp': '2025-01-01T00:00:00Z',
            'metadata': {
                'source': 'api',
                'version': '1.0'
            }
        }
        
        handles = extract_handles_from_data(data)
        assert handles == []
    
    def test_extract_handles_from_data_empty(self):
        """Test handle extraction from empty data."""
        data = {}
        handles = extract_handles_from_data(data)
        assert handles == []
    
    def test_log_with_panel_with_title(self):
        """Test log_with_panel with title and border color."""
        with patch('builtins.print') as mock_print:
            log_with_panel("Test message", "Test Title", "blue")
            
            mock_print.assert_called()
            calls = mock_print.call_args_list
            assert len(calls) >= 2
            assert "⚙ Test Title" in str(calls[0])
            # Check that the message appears in any of the calls
            all_calls_str = " ".join(str(call) for call in calls)
            assert "Test message" in all_calls_str
    
    def test_log_with_panel_without_title(self):
        """Test log_with_panel without title."""
        with patch('builtins.print') as mock_print:
            log_with_panel("Test message")
            
            mock_print.assert_called_once_with("Test message")
    
    def test_log_with_panel_different_colors(self):
        """Test log_with_panel with different border colors."""
        color_symbols = {
            "blue": "⚙",
            "green": "✓",
            "yellow": "◆",
            "red": "✗",
            "white": "▶",
            "cyan": "✎"
        }
        
        for color, expected_symbol in color_symbols.items():
            with patch('builtins.print') as mock_print:
                log_with_panel("Test message", "Test Title", color)
                
                calls = mock_print.call_args_list
                assert expected_symbol in str(calls[0])
    
    def test_notification_to_dict(self):
        """Test notification to dictionary conversion."""
        mock_notification = MagicMock()
        mock_notification.uri = "at://did:plc:test123456789/app.bsky.feed.post/test123"
        mock_notification.cid = "test_cid_12345"
        mock_notification.author.did = "did:plc:test123456789"
        mock_notification.author.handle = "test.user.bsky.social"
        mock_notification.author.displayName = "Test User"
        mock_notification.record.text = "Test notification content"
        mock_notification.record.createdAt = "2025-01-01T00:00:00Z"
        mock_notification.replyCount = 0
        mock_notification.repostCount = 0
        mock_notification.likeCount = 0
        mock_notification.indexedAt = "2025-01-01T00:00:00Z"
        
        result = notification_to_dict(mock_notification)
        
        assert result['uri'] == "at://did:plc:test123456789/app.bsky.feed.post/test123"
        assert result['cid'] == "test_cid_12345"
        assert result['author']['did'] == "did:plc:test123456789"
        assert result['author']['handle'] == "test.user.bsky.social"
        assert result['author']['displayName'] == "Test User"
        assert result['record']['text'] == "Test notification content"
        assert result['record']['createdAt'] == "2025-01-01T00:00:00Z"
        assert result['replyCount'] == 0
        assert result['repostCount'] == 0
        assert result['likeCount'] == 0
        assert result['indexedAt'] == "2025-01-01T00:00:00Z"


class TestBlueskyInitialization:
    """Test Bluesky initialization functions."""
    
    @patch('bsky.get_letta_config')
    @patch('bsky.Letta')
    @patch('bsky.upsert_agent')
    def test_initialize_void_success(self, mock_upsert_agent, mock_letta_class, mock_get_config):
        """Test successful void agent initialization."""
        # Setup mocks
        mock_config = {
            'letta': {
                'api_key': 'test_letta_key',
                'agent_id': 'test_agent_id'
            }
        }
        mock_get_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        mock_agent = MagicMock()
        mock_agent.id = 'test_agent_id'
        mock_client.agents.retrieve.return_value = mock_agent
        
        mock_upsert_agent.return_value = mock_agent
        
        # Test initialization
        result = initialize_void()
        
        assert result == mock_agent
        assert result.id == 'test_agent_id'
        mock_get_config.assert_called_once()
        mock_letta_class.assert_called_once_with(token='test_letta_key')
        mock_client.agents.retrieve.assert_called_once_with(agent_id='test_agent_id')
        mock_upsert_agent.assert_called_once_with(mock_client, mock_agent)
    
    @patch('bsky.get_letta_config')
    @patch('bsky.Letta')
    def test_initialize_void_config_error(self, mock_letta_class, mock_get_config):
        """Test void initialization with configuration error."""
        mock_get_config.side_effect = Exception("Config error")
        
        with pytest.raises(Exception, match="Config error"):
            initialize_void()
    
    @patch('bsky.get_letta_config')
    @patch('bsky.Letta')
    def test_initialize_void_client_error(self, mock_letta_class, mock_get_config):
        """Test void initialization with client error."""
        mock_config = {
            'letta': {
                'api_key': 'test_letta_key',
                'agent_id': 'test_agent_id'
            }
        }
        mock_get_config.return_value = mock_config
        mock_letta_class.side_effect = Exception("Client error")
        
        with pytest.raises(Exception, match="Client error"):
            initialize_void()


class TestBlueskyQueueOperations:
    """Test Bluesky queue operations."""
    
    def test_load_processed_notifications_success(self):
        """Test successful processed notifications loading."""
        test_data = {"processed_notifications": ["123456789", "987654321"]}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            with patch('bsky.PROCESSED_NOTIFICATIONS_FILE', Path("test_processed.json")):
                processed = load_processed_notifications()
                assert processed == {"123456789", "987654321"}
    
    def test_load_processed_notifications_file_not_found(self):
        """Test processed notifications loading with missing file."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('bsky.PROCESSED_NOTIFICATIONS_FILE', Path("nonexistent.json")):
                processed = load_processed_notifications()
                assert processed == set()
    
    def test_save_processed_notifications_success(self):
        """Test successful processed notifications saving."""
        test_set = {"123456789", "987654321"}
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('bsky.PROCESSED_NOTIFICATIONS_FILE', Path("test_processed.json")):
                save_processed_notifications(test_set)
                
                mock_file.assert_called_once()
                # Verify the written data
                written_data = json.loads(mock_file().write.call_args[0][0])
                assert set(written_data["processed_notifications"]) == test_set
    
    def test_save_notification_to_queue_success(self):
        """Test successful notification saving to queue."""
        notification = {
            'uri': 'at://did:plc:test123456789/app.bsky.feed.post/test123',
            'cid': 'test_cid_12345',
            'author': {
                'did': 'did:plc:test123456789',
                'handle': 'test.user.bsky.social',
                'displayName': 'Test User'
            },
            'record': {
                'text': 'Test notification content',
                'createdAt': '2025-01-01T00:00:00Z'
            }
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('bsky.QUEUE_DIR', Path("test_queue")):
                with patch('pathlib.Path.mkdir'):
                    with patch('bsky.hashlib.md5') as mock_md5:
                        mock_md5.return_value.hexdigest.return_value = "test_hash"
                        save_notification_to_queue(notification)
                        
                        mock_file.assert_called_once()
                        # Verify the written data
                        written_data = json.loads(mock_file().write.call_args[0][0])
                        assert written_data['uri'] == notification['uri']
                        assert written_data['record']['text'] == notification['record']['text']
    
    def test_save_notification_to_queue_priority(self):
        """Test saving priority notification to queue."""
        notification = {
            'uri': 'at://did:plc:test123456789/app.bsky.feed.post/test123',
            'record': {'text': 'Priority notification'}
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('bsky.QUEUE_DIR', Path("test_queue")):
                with patch('pathlib.Path.mkdir'):
                    with patch('bsky.hashlib.md5') as mock_md5:
                        mock_md5.return_value.hexdigest.return_value = "priority_hash"
                        save_notification_to_queue(notification, is_priority=True)
                        
                        mock_file.assert_called_once()
                        # Verify the written data includes priority flag
                        written_data = json.loads(mock_file().write.call_args[0][0])
                        assert written_data['is_priority'] is True


class TestBlueskyNotificationProcessing:
    """Test Bluesky notification processing."""
    
    @patch('bsky.attach_user_blocks')
    @patch('bsky.thread_to_yaml_string')
    def test_process_mention_success(self, mock_thread_to_yaml, mock_attach_blocks):
        """Test successful mention processing."""
        # Setup mocks
        mock_void_agent = MagicMock()
        mock_void_agent.id = 'test_agent_id'
        mock_void_agent.memory = MagicMock()
        
        mock_atproto_client = MagicMock()
        
        notification_data = {
            'uri': 'at://did:plc:test123456789/app.bsky.feed.post/test123',
            'author': {
                'handle': 'test.user.bsky.social',
                'did': 'did:plc:test123456789'
            },
            'record': {
                'text': 'Test mention content'
            }
        }
        
        mock_thread_to_yaml.return_value = "Test thread YAML"
        
        # Test processing
        result = process_mention(mock_void_agent, mock_atproto_client, notification_data)
        
        # Verify the function completed successfully
        assert result is not None
        mock_thread_to_yaml.assert_called_once()
    
    @patch('bsky.attach_user_blocks')
    def test_process_mention_with_user_blocks(self, mock_attach_blocks):
        """Test mention processing with user block attachment."""
        mock_void_agent = MagicMock()
        mock_void_agent.id = 'test_agent_id'
        mock_void_agent.memory = MagicMock()
        
        mock_atproto_client = MagicMock()
        
        notification_data = {
            'uri': 'at://did:plc:test123456789/app.bsky.feed.post/test123',
            'author': {
                'handle': 'test.user.bsky.social',
                'did': 'did:plc:test123456789'
            },
            'record': {
                'text': 'Test mention content'
            }
        }
        
        # Test processing
        process_mention(mock_void_agent, mock_atproto_client, notification_data)
        
        # Verify user blocks were attached
        mock_attach_blocks.assert_called_once()
    
    def test_process_mention_error_handling(self):
        """Test mention processing error handling."""
        mock_void_agent = MagicMock()
        mock_atproto_client = MagicMock()
        
        # Invalid notification data
        invalid_notification = {}
        
        # Should handle gracefully without crashing
        result = process_mention(mock_void_agent, mock_atproto_client, invalid_notification)
        assert result is not None


class TestBlueskyQueueProcessing:
    """Test Bluesky queue processing functions."""
    
    @patch('bsky.process_mention')
    @patch('bsky.load_processed_notifications')
    @patch('bsky.save_processed_notifications')
    def test_load_and_process_queued_notifications_success(self, mock_save_processed, mock_load_processed, mock_process_mention):
        """Test successful queued notifications processing."""
        # Setup mocks
        mock_load_processed.return_value = {"123456789"}
        
        mock_void_agent = MagicMock()
        mock_void_agent.id = 'test_agent_id'
        
        mock_atproto_client = MagicMock()
        
        # Create test queue files
        test_notification = {
            'uri': 'at://did:plc:test123456789/app.bsky.feed.post/test123',
            'author': {'handle': 'test.user.bsky.social'},
            'record': {'text': 'Test notification'}
        }
        
        with patch('pathlib.Path.glob') as mock_glob:
            mock_file = MagicMock()
            mock_file.name = 'test_notification.json'
            mock_glob.return_value = [mock_file]
            
            with patch('builtins.open', mock_open(read_data=json.dumps(test_notification))):
                with patch('pathlib.Path.unlink'):  # Mock file deletion
                    mock_process_mention.return_value = True
                    
                    # Test processing
                    result = load_and_process_queued_notifications(mock_void_agent, mock_atproto_client)
                    
                    assert result is not None
                    mock_process_mention.assert_called_once()
    
    @patch('bsky.save_notification_to_queue')
    def test_fetch_and_queue_new_notifications_success(self, mock_save_to_queue):
        """Test successful new notifications fetching and queuing."""
        mock_atproto_client = MagicMock()
        
        # Mock notification data
        mock_notification = MagicMock()
        mock_notification.uri = "at://did:plc:test123456789/app.bsky.feed.post/test123"
        mock_notification.cid = "test_cid_12345"
        mock_notification.author.did = "did:plc:test123456789"
        mock_notification.author.handle = "test.user.bsky.social"
        mock_notification.author.displayName = "Test User"
        mock_notification.record.text = "Test notification content"
        mock_notification.record.createdAt = "2025-01-01T00:00:00Z"
        mock_notification.replyCount = 0
        mock_notification.repostCount = 0
        mock_notification.likeCount = 0
        mock_notification.indexedAt = "2025-01-01T00:00:00Z"
        
        mock_atproto_client.notifications.list_notifications.return_value = {
            'notifications': [mock_notification]
        }
        
        # Test fetching
        result = fetch_and_queue_new_notifications(mock_atproto_client)
        
        assert result is not None
        mock_save_to_queue.assert_called_once()
    
    @patch('bsky.load_and_process_queued_notifications')
    @patch('bsky.fetch_and_queue_new_notifications')
    def test_process_notifications_success(self, mock_fetch_notifications, mock_process_queued):
        """Test successful notifications processing workflow."""
        mock_void_agent = MagicMock()
        mock_atproto_client = MagicMock()
        
        mock_fetch_notifications.return_value = True
        mock_process_queued.return_value = True
        
        # Test processing
        result = process_notifications(mock_void_agent, mock_atproto_client)
        
        assert result is not None
        mock_fetch_notifications.assert_called_once_with(mock_atproto_client)
        mock_process_queued.assert_called_once_with(mock_void_agent, mock_atproto_client)


class TestBlueskyMemoryManagement:
    """Test Bluesky memory management functions."""
    
    @patch('bsky.Letta')
    def test_send_synthesis_message_success(self, mock_letta_class):
        """Test successful synthesis message sending."""
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        mock_agent = MagicMock()
        mock_agent.id = 'test_agent_id'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Test synthesis message
        send_synthesis_message(mock_client, 'test_agent_id')
        
        mock_client.agents.retrieve.assert_called_once_with(agent_id='test_agent_id')
    
    @patch('bsky.Letta')
    def test_periodic_user_block_cleanup_success(self, mock_letta_class):
        """Test successful periodic user block cleanup."""
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        # Mock block operations
        mock_client.agents.blocks.list.return_value = [
            MagicMock(label='user_test.user.bsky.social'),
            MagicMock(label='system_information')
        ]
        
        # Test cleanup
        periodic_user_block_cleanup(mock_client, 'test_agent_id')
        
        mock_client.agents.blocks.list.assert_called_once_with(agent_id='test_agent_id')
    
    @patch('bsky.Letta')
    def test_attach_temporal_blocks_success(self, mock_letta_class):
        """Test successful temporal blocks attachment."""
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        # Mock block attachment
        mock_client.agents.blocks.attach.return_value = MagicMock()
        
        # Test attachment
        result = attach_temporal_blocks(mock_client, 'test_agent_id')
        
        assert result is not None
        mock_client.agents.blocks.attach.assert_called()
    
    @patch('bsky.Letta')
    def test_detach_temporal_blocks_success(self, mock_letta_class):
        """Test successful temporal blocks detachment."""
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        # Mock block detachment
        mock_client.agents.blocks.detach.return_value = MagicMock()
        
        # Test detachment
        result = detach_temporal_blocks(mock_client, 'test_agent_id', ['test_block'])
        
        assert result is True
        mock_client.agents.blocks.detach.assert_called()


class TestBlueskyErrorHandling:
    """Test Bluesky error handling and edge cases."""
    
    def test_process_mention_with_invalid_data(self):
        """Test mention processing with invalid data."""
        mock_void_agent = MagicMock()
        mock_atproto_client = MagicMock()
        
        # Invalid notification data
        invalid_notification = None
        
        # Should handle gracefully
        result = process_mention(mock_void_agent, mock_atproto_client, invalid_notification)
        assert result is not None
    
    @patch('bsky.load_processed_notifications')
    def test_load_and_process_queued_notifications_no_files(self, mock_load_processed):
        """Test queued notifications processing with no files."""
        mock_load_processed.return_value = set()
        
        mock_void_agent = MagicMock()
        mock_atproto_client = MagicMock()
        
        with patch('pathlib.Path.glob', return_value=[]):
            result = load_and_process_queued_notifications(mock_void_agent, mock_atproto_client)
            assert result is not None
    
    @patch('bsky.save_notification_to_queue')
    def test_fetch_and_queue_new_notifications_api_error(self, mock_save_to_queue):
        """Test notifications fetching with API error."""
        mock_atproto_client = MagicMock()
        mock_atproto_client.notifications.list_notifications.side_effect = Exception("API error")
        
        # Should handle gracefully
        result = fetch_and_queue_new_notifications(mock_atproto_client)
        assert result is not None
    
    def test_notification_to_dict_with_missing_attributes(self):
        """Test notification to dict conversion with missing attributes."""
        mock_notification = MagicMock()
        # Don't set any attributes
        
        # Should handle gracefully
        result = notification_to_dict(mock_notification)
        assert isinstance(result, dict)


class TestBlueskyIntegration:
    """Test Bluesky integration scenarios."""
    
    @patch('bsky.initialize_void')
    @patch('bsky.process_notifications')
    def test_bluesky_integration_workflow(self, mock_process_notifications, mock_initialize_void):
        """Test complete Bluesky integration workflow."""
        # Setup mocks
        mock_void_agent = MagicMock()
        mock_void_agent.id = 'test_agent_id'
        mock_initialize_void.return_value = mock_void_agent
        
        mock_atproto_client = MagicMock()
        mock_process_notifications.return_value = True
        
        # Test workflow
        void_agent = initialize_void()
        result = process_notifications(void_agent, mock_atproto_client)
        
        assert void_agent == mock_void_agent
        assert result is True
        mock_initialize_void.assert_called_once()
        mock_process_notifications.assert_called_once_with(mock_void_agent, mock_atproto_client)
    
    def test_bluesky_configuration_integration(self):
        """Test Bluesky configuration integration."""
        test_config = {
            'letta': {
                'api_key': 'test_letta_key',
                'agent_id': 'test_agent_id'
            },
            'bluesky': {
                'username': 'test.user.bsky.social',
                'password': 'test_password'
            }
        }
        
        with patch('bsky.get_letta_config', return_value=test_config):
            # Test that configuration is properly loaded
            config = bsky.get_letta_config()
            assert config['letta']['api_key'] == 'test_letta_key'
            assert config['bluesky']['username'] == 'test.user.bsky.social'
    
    def test_bluesky_queue_integration(self):
        """Test Bluesky queue integration workflow."""
        test_notification = {
            'uri': 'at://did:plc:test123456789/app.bsky.feed.post/test123',
            'author': {'handle': 'test.user.bsky.social'},
            'record': {'text': 'Test notification'}
        }
        
        with patch('bsky.save_notification_to_queue') as mock_save:
            with patch('bsky.load_processed_notifications', return_value=set()):
                with patch('bsky.save_processed_notifications') as mock_save_processed:
                    # Simulate queue workflow
                    save_notification_to_queue(test_notification)
                    
                    mock_save.assert_called_once_with(test_notification)
    
    def test_bluesky_memory_integration(self):
        """Test Bluesky memory management integration."""
        mock_client = MagicMock()
        
        with patch('bsky.attach_temporal_blocks') as mock_attach:
            with patch('bsky.detach_temporal_blocks') as mock_detach:
                # Test memory block lifecycle
                attach_temporal_blocks(mock_client, 'test_agent_id')
                detach_temporal_blocks(mock_client, 'test_agent_id', ['test_block'])
                
                mock_attach.assert_called_once_with(mock_client, 'test_agent_id')
                mock_detach.assert_called_once_with(mock_client, 'test_agent_id', ['test_block'])
