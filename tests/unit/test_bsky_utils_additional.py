"""Additional tests for platforms/bluesky/utils.py to improve coverage."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import os
import time
import json

from platforms.bluesky.utils import (
    cleanup_old_sessions,
    validate_session,
    get_session_config,
    reply_to_post,
    get_post_thread,
    reply_to_notification,
    create_synthesis_ack,
    acknowledge_post,
    create_tool_call_record,
    create_reasoning_record,
    strip_fields,
    flatten_thread_structure,
    init_client,
    default_login,
    remove_outside_quotes,
    get_session_with_retry,
    save_session_with_retry
)


class TestSessionManagement:
    """Test session management functions."""
    
    @patch('platforms.bluesky.utils.get_session_config')
    def test_cleanup_old_sessions_no_directory(self, mock_get_config):
        """Test cleanup_old_sessions when directory doesn't exist."""
        mock_get_config.return_value = {
            'max_age_days': 30,
            'directory': '/nonexistent',
            'validate_sessions': True
        }
        
        result = cleanup_old_sessions()
        
        assert result == 0
    
    @patch('platforms.bluesky.utils.get_session_config')
    @patch('platforms.bluesky.utils.Path')
    def test_cleanup_old_sessions_error_accessing_directory(self, mock_path, mock_get_config):
        """Test cleanup_old_sessions when there's an error accessing directory."""
        mock_get_config.return_value = {
            'max_age_days': 30,
            'directory': '/test',
            'validate_sessions': True
        }
        mock_path.side_effect = Exception("Permission denied")
        
        result = cleanup_old_sessions()
        
        assert result == 0
    
    @patch('platforms.bluesky.utils.get_session_config')
    @patch('platforms.bluesky.utils.Path')
    @patch('platforms.bluesky.utils.time.time')
    def test_cleanup_old_sessions_removes_old_files(self, mock_time, mock_path, mock_get_config):
        """Test cleanup_old_sessions removes old session files."""
        mock_get_config.return_value = {
            'max_age_days': 30,
            'directory': '/test',
            'validate_sessions': True
        }
        mock_time.return_value = 1000000  # Current time
        
        # Mock Path and file operations
        mock_session_path = MagicMock()
        mock_session_path.exists.return_value = True
        mock_session_path.glob.return_value = [
            MagicMock(stat=lambda: MagicMock(st_mtime=900000))  # Old file
        ]
        mock_path.return_value = mock_session_path
        
        # Mock file operations
        with patch('builtins.open', mock_open(read_data="valid session data")):
            with patch('platforms.bluesky.utils.validate_session', return_value=True):
                result = cleanup_old_sessions()
        
        assert result == 1
        mock_session_path.glob.return_value[0].unlink.assert_called_once()
    
    @patch('platforms.bluesky.utils.get_session_config')
    @patch('platforms.bluesky.utils.Path')
    @patch('platforms.bluesky.utils.time.time')
    def test_cleanup_old_sessions_removes_corrupted_files(self, mock_time, mock_path, mock_get_config):
        """Test cleanup_old_sessions removes corrupted session files."""
        mock_get_config.return_value = {
            'max_age_days': 30,
            'directory': '/test',
            'validate_sessions': True
        }
        mock_time.return_value = 1000000  # Current time
        
        # Mock Path and file operations
        mock_session_path = MagicMock()
        mock_session_path.exists.return_value = True
        mock_session_path.glob.return_value = [
            MagicMock(stat=lambda: MagicMock(st_mtime=999000))  # Recent file
        ]
        mock_path.return_value = mock_session_path
        
        # Mock file operations
        with patch('builtins.open', mock_open(read_data="corrupted session data")):
            with patch('platforms.bluesky.utils.validate_session', return_value=False):
                result = cleanup_old_sessions()
        
        assert result == 1
        mock_session_path.glob.return_value[0].unlink.assert_called_once()
    
    @patch('platforms.bluesky.utils.get_session_config')
    @patch('platforms.bluesky.utils.Path')
    @patch('platforms.bluesky.utils.time.time')
    def test_cleanup_old_sessions_removes_unreadable_files(self, mock_time, mock_path, mock_get_config):
        """Test cleanup_old_sessions removes unreadable session files."""
        mock_get_config.return_value = {
            'max_age_days': 30,
            'directory': '/test',
            'validate_sessions': True
        }
        mock_time.return_value = 1000000  # Current time
        
        # Mock Path and file operations
        mock_session_path = MagicMock()
        mock_session_path.exists.return_value = True
        mock_session_path.glob.return_value = [
            MagicMock(stat=lambda: MagicMock(st_mtime=999000))  # Recent file
        ]
        mock_path.return_value = mock_session_path
        
        # Mock file operations to raise exception
        with patch('builtins.open', side_effect=Exception("Cannot read file")):
            result = cleanup_old_sessions()
        
        assert result == 1
        mock_session_path.glob.return_value[0].unlink.assert_called_once()
    
    def test_validate_session_valid(self):
        """Test validate_session with valid session data."""
        valid_session = '{"accessJwt": "token", "refreshJwt": "refresh", "handle": "user", "did": "did:plc:example"}'
        
        result = validate_session(valid_session)
        
        assert result is True
    
    def test_validate_session_invalid(self):
        """Test validate_session with invalid session data."""
        invalid_session = ""
        
        result = validate_session(invalid_session)
        
        assert result is False
    
    def test_get_session_config(self):
        """Test get_session_config returns default configuration."""
        config = get_session_config()
        
        assert 'directory' in config
        assert 'max_age_days' in config
        assert 'validate_sessions' in config
        assert isinstance(config['max_age_days'], int)
        assert isinstance(config['validate_sessions'], bool)


class TestClientInitialization:
    """Test client initialization functions."""
    
    @patch('platforms.bluesky.utils.Client')
    def test_init_client_success(self, mock_client_class):
        """Test init_client with successful initialization."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        result = init_client("testuser", "testpass")
        
        assert result == mock_client
        mock_client_class.assert_called_once()
    
    @patch('platforms.bluesky.utils.Client')
    def test_init_client_error(self, mock_client_class):
        """Test init_client with initialization error."""
        mock_client_class.side_effect = Exception("Connection error")
        
        result = init_client("testuser", "testpass")
        
        assert result is None
    
    @patch('platforms.bluesky.utils.get_config')
    def test_default_login_success(self, mock_get_config):
        """Test default_login with successful login."""
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default: {
            'platforms.bluesky.username': 'testuser',
            'platforms.bluesky.password': 'testpass'
        }.get(key, default)
        mock_get_config.return_value = mock_config

        with patch('platforms.bluesky.utils.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            result = default_login()

            assert result == mock_client
            mock_client_class.assert_called_once()
    
    @patch('platforms.bluesky.utils.get_config')
    def test_default_login_missing_credentials(self, mock_get_config):
        """Test default_login with missing credentials."""
        mock_config = MagicMock()
        mock_config.get.return_value = None
        mock_get_config.return_value = mock_config

        with pytest.raises(SystemExit):
            result = default_login()


class TestTextProcessing:
    """Test text processing functions."""
    
    def test_remove_outside_quotes_single_quotes(self):
        """Test remove_outside_quotes with single quotes."""
        text = "'Hello world'"
        result = remove_outside_quotes(text)
        assert result == "'Hello world'"  # Function only removes double quotes
    
    def test_remove_outside_quotes_double_quotes(self):
        """Test remove_outside_quotes with double quotes."""
        text = '"Hello world"'
        result = remove_outside_quotes(text)
        assert result == "Hello world"
    
    def test_remove_outside_quotes_no_quotes(self):
        """Test remove_outside_quotes with no quotes."""
        text = "Hello world"
        result = remove_outside_quotes(text)
        assert result == "Hello world"
    
    def test_remove_outside_quotes_mixed_quotes(self):
        """Test remove_outside_quotes with mixed quotes."""
        text = "'Hello \"world\"'"
        result = remove_outside_quotes(text)
        assert result == "'Hello \"world\"'"  # Function only removes double quotes
    
    def test_remove_outside_quotes_unmatched_quotes(self):
        """Test remove_outside_quotes with unmatched quotes."""
        text = "'Hello world"
        result = remove_outside_quotes(text)
        assert result == "'Hello world"
    
    def test_remove_outside_quotes_empty_string(self):
        """Test remove_outside_quotes with empty string."""
        text = ""
        result = remove_outside_quotes(text)
        assert result == ""


class TestSessionRetry:
    """Test session retry functions."""
    
    @patch('platforms.bluesky.utils.get_session_path')
    @patch('platforms.bluesky.utils.get_session_config')
    def test_get_session_with_retry_success(self, mock_get_config, mock_get_path):
        """Test get_session_with_retry with successful retry."""
        mock_config = {
            'retry_attempts': 3,
            'validate_sessions': False
        }
        mock_get_config.return_value = mock_config
        
        mock_path = MagicMock()
        mock_path.exists.side_effect = [False, True]  # First attempt fails, second succeeds
        mock_get_path.return_value = mock_path
        
        with patch('builtins.open', mock_open(read_data="session_data")):
            result = get_session_with_retry("testuser", max_retries=2)
        
        assert result == "session_data"
    
    @patch('platforms.bluesky.utils.get_session_path')
    @patch('platforms.bluesky.utils.get_session_config')
    def test_get_session_with_retry_max_retries(self, mock_get_config, mock_get_path):
        """Test get_session_with_retry with max retries exceeded."""
        mock_config = {
            'retry_attempts': 3,
            'validate_sessions': False
        }
        mock_get_config.return_value = mock_config
        
        mock_path = MagicMock()
        mock_path.exists.return_value = False  # File never exists
        mock_get_path.return_value = mock_path
        
        result = get_session_with_retry("testuser", max_retries=2)
        
        assert result is None
    
    @patch('platforms.bluesky.utils.get_session_path')
    @patch('platforms.bluesky.utils.get_session_config')
    def test_save_session_with_retry_success(self, mock_get_config, mock_get_path):
        """Test save_session_with_retry with successful retry."""
        mock_config = {
            'retry_attempts': 3,
            'validate_sessions': False
        }
        mock_get_config.return_value = mock_config
        
        mock_path = MagicMock()
        mock_get_path.return_value = mock_path
        
        with patch('builtins.open', mock_open()):
            result = save_session_with_retry("testuser", "session_data", max_retries=2, validate=False)
        
        assert result is True
    
    @patch('platforms.bluesky.utils.get_session_path')
    @patch('platforms.bluesky.utils.get_session_config')
    def test_save_session_with_retry_max_retries(self, mock_get_config, mock_get_path):
        """Test save_session_with_retry with max retries exceeded."""
        mock_config = {
            'retry_attempts': 3,
            'validate_sessions': False
        }
        mock_get_config.return_value = mock_config
        
        mock_path = MagicMock()
        mock_get_path.return_value = mock_path
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = save_session_with_retry("testuser", "session_data", max_retries=2, validate=False)
        
        assert result is False


class TestThreadOperations:
    """Test thread operation functions."""
    
    @patch('platforms.bluesky.utils.Client')
    def test_get_post_thread_success(self, mock_client_class):
        """Test get_post_thread with successful API call."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_thread_data = MagicMock()
        mock_client.app.bsky.feed.get_post_thread.return_value = mock_thread_data
        
        result = get_post_thread(mock_client, "at://test")
        
        assert result == mock_thread_data
        mock_client.app.bsky.feed.get_post_thread.assert_called_once()
    
    @patch('platforms.bluesky.utils.Client')
    def test_get_post_thread_api_error(self, mock_client_class):
        """Test get_post_thread with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.app.bsky.feed.get_post_thread.side_effect = Exception("API error")
        
        result = get_post_thread(mock_client, "at://test")
        
        assert result is None
    
    @patch('platforms.bluesky.utils.create_post_with_facets')
    @patch('platforms.bluesky.utils.Client')
    def test_reply_to_post_success(self, mock_client_class, mock_create_post):
        """Test reply_to_post with successful reply."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_create_post.return_value = MagicMock()
        mock_client.app.bsky.feed.create_post.return_value = MagicMock()
        
        result = reply_to_post("Hello world", "at://test", mock_client, "test_correlation")
        
        assert result is not None
        mock_create_post.assert_called_once()
        mock_client.app.bsky.feed.create_post.assert_called_once()
    
    @patch('platforms.bluesky.utils.create_post_with_facets')
    @patch('platforms.bluesky.utils.Client')
    def test_reply_to_post_api_error(self, mock_client_class, mock_create_post):
        """Test reply_to_post with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_create_post.return_value = MagicMock()
        mock_client.app.bsky.feed.create_post.side_effect = Exception("API error")
        
        result = reply_to_post("Hello world", "at://test", mock_client, "test_correlation")
        
        assert result is None
    
    @patch('platforms.bluesky.utils.create_post_with_facets')
    @patch('platforms.bluesky.utils.Client')
    def test_reply_to_notification_success(self, mock_client_class, mock_create_post):
        """Test reply_to_notification with successful reply."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_create_post.return_value = MagicMock()
        mock_client.app.bsky.feed.create_post.return_value = MagicMock()
        
        notification_data = {
            'uri': 'at://test',
            'author': {'handle': 'testuser'}
        }
        
        result = reply_to_notification("Hello world", notification_data, mock_client, "test_correlation")
        
        assert result is not None
        mock_create_post.assert_called_once()
        mock_client.app.bsky.feed.create_post.assert_called_once()
    
    @patch('platforms.bluesky.utils.create_post_with_facets')
    @patch('platforms.bluesky.utils.Client')
    def test_reply_to_notification_api_error(self, mock_client_class, mock_create_post):
        """Test reply_to_notification with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_create_post.return_value = MagicMock()
        mock_client.app.bsky.feed.create_post.side_effect = Exception("API error")
        
        notification_data = {
            'uri': 'at://test',
            'author': {'handle': 'testuser'}
        }
        
        result = reply_to_notification("Hello world", notification_data, mock_client, "test_correlation")
        
        assert result is None


class TestAcknowledgmentFunctions:
    """Test acknowledgment functions."""
    
    @patch('core.config.get_bluesky_config')
    @patch('platforms.bluesky.utils.Client')
    def test_create_synthesis_ack_success(self, mock_client_class, mock_get_bluesky_config):
        """Test create_synthesis_ack with successful creation."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock the client session
        mock_session = MagicMock()
        mock_session.access_jwt = "test_token"
        mock_session.did = "test_did"
        mock_client._session = mock_session
        
        # Mock the bluesky config
        mock_get_bluesky_config.return_value = {
            'pds_uri': 'https://bsky.social'
        }
        
        # Mock the requests.post call
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"uri": "test_uri", "cid": "test_cid"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = create_synthesis_ack(mock_client, "Synthesis complete")
        
        assert result is not None
        assert result["uri"] == "test_uri"
        assert result["cid"] == "test_cid"
    
    @patch('core.config.get_config')
    @patch('platforms.bluesky.utils.Client')
    def test_create_synthesis_ack_api_error(self, mock_client_class, mock_get_config):
        """Test create_synthesis_ack with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default: {
            'platforms.bluesky.username': 'testuser',
            'platforms.bluesky.password': 'testpass'
        }.get(key, default)
        mock_get_config.return_value = mock_config
        
        mock_client.app.bsky.feed.post.create.side_effect = Exception("API error")
        
        result = create_synthesis_ack(mock_client, "Synthesis complete")
        
        assert result is None
    
    @patch('core.config.get_config')
    @patch('platforms.bluesky.utils.Client')
    def test_acknowledge_post_success(self, mock_client_class, mock_get_config):
        """Test acknowledge_post with successful acknowledgment."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default: {
            'platforms.bluesky.username': 'testuser',
            'platforms.bluesky.password': 'testpass'
        }.get(key, default)
        mock_get_config.return_value = mock_config
        
        mock_client.app.bsky.feed.post.create.return_value = {"uri": "test_uri", "cid": "test_cid"}
        
        result = acknowledge_post(mock_client, "at://test", "test_cid", "Acknowledged")
        
        assert result is not None
        assert result["uri"] == "test_uri"
        assert result["cid"] == "test_cid"
    
    @patch('platforms.bluesky.utils.Client')
    def test_acknowledge_post_api_error(self, mock_client_class):
        """Test acknowledge_post with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.app.bsky.feed.create_post.side_effect = Exception("API error")
        
        result = acknowledge_post(mock_client, "at://test", "test_cid", "Acknowledged")
        
        assert result is None
    
    @patch('core.config.get_config')
    @patch('platforms.bluesky.utils.Client')
    def test_create_tool_call_record_success(self, mock_client_class, mock_get_config):
        """Test create_tool_call_record with successful creation."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default: {
            'platforms.bluesky.username': 'testuser',
            'platforms.bluesky.password': 'testpass'
        }.get(key, default)
        mock_get_config.return_value = mock_config
        
        mock_client.app.bsky.feed.post.create.return_value = {"uri": "test_uri", "cid": "test_cid"}
        
        result = create_tool_call_record(mock_client, "test_tool", "test_args", "test_correlation")
        
        assert result is not None
        assert result["uri"] == "test_uri"
        assert result["cid"] == "test_cid"
    
    @patch('platforms.bluesky.utils.Client')
    def test_create_tool_call_record_api_error(self, mock_client_class):
        """Test create_tool_call_record with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_client.app.bsky.feed.create_post.side_effect = Exception("API error")
        
        result = create_tool_call_record(mock_client, "test_tool", "test_args", "test_correlation")
        
        assert result is None
    
    @patch('core.config.get_config')
    @patch('platforms.bluesky.utils.Client')
    def test_create_reasoning_record_success(self, mock_client_class, mock_get_config):
        """Test create_reasoning_record with successful creation."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default: {
            'platforms.bluesky.username': 'testuser',
            'platforms.bluesky.password': 'testpass'
        }.get(key, default)
        mock_get_config.return_value = mock_config
        
        mock_client.app.bsky.feed.post.create.return_value = {"uri": "test_uri", "cid": "test_cid"}
        
        result = create_reasoning_record(mock_client, "test_reasoning")
        
        assert result is not None
        assert result["uri"] == "test_uri"
        assert result["cid"] == "test_cid"
    
    @patch('core.config.get_config')
    @patch('platforms.bluesky.utils.Client')
    def test_create_reasoning_record_api_error(self, mock_client_class, mock_get_config):
        """Test create_reasoning_record with API error."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default: {
            'platforms.bluesky.username': 'testuser',
            'platforms.bluesky.password': 'testpass'
        }.get(key, default)
        mock_get_config.return_value = mock_config
        
        mock_client.app.bsky.feed.post.create.side_effect = Exception("API error")
        
        result = create_reasoning_record(mock_client, "test_reasoning")
        
        assert result is None


class TestStripFields:
    """Test strip_fields function edge cases."""
    
    def test_strip_fields_with_none_values(self):
        """Test strip_fields removes None values."""
        data = {
            'keep': 'value',
            'remove': None,
            'empty_dict': {},
            'empty_list': [],
            'empty_string': ''
        }
        
        result = strip_fields(data, ['remove'])
        
        assert 'keep' in result
        assert 'remove' not in result
        assert 'empty_dict' not in result
        assert 'empty_list' not in result
        assert 'empty_string' not in result
    
    def test_strip_fields_with_pydantic_metadata(self):
        """Test strip_fields removes pydantic metadata."""
        data = {
            'keep': 'value',
            '__pydantic_metadata__': 'metadata',
            '__private__': 'private'
        }
        
        result = strip_fields(data, [])
        
        assert 'keep' in result
        assert '__pydantic_metadata__' not in result
        assert '__private__' not in result
    
    def test_strip_fields_with_nested_none_values(self):
        """Test strip_fields removes nested None values."""
        data = {
            'level1': {
                'level2': {
                    'keep': 'value',
                    'remove': None
                }
            }
        }
        
        result = strip_fields(data, ['remove'])
        
        assert 'level1' in result
        assert 'level2' in result['level1']
        assert 'keep' in result['level1']['level2']
        assert 'remove' not in result['level1']['level2']


class TestFlattenThreadStructure:
    """Test flatten_thread_structure function edge cases."""
    
    def test_flatten_thread_structure_with_dict_parent(self):
        """Test flatten_thread_structure with dict-based parent."""
        thread_data = {
            'thread': {
                'parent': {
                    'post': {'text': 'Parent post'}
                },
                'post': {'text': 'Main post'},
                'replies': [
                    {
                        'post': {'text': 'Reply 1'}
                    }
                ]
            }
        }
        
        result = flatten_thread_structure(thread_data)
        
        assert 'posts' in result
        assert len(result['posts']) == 3
        assert result['posts'][0]['text'] == 'Parent post'
        assert result['posts'][1]['text'] == 'Main post'
        assert result['posts'][2]['text'] == 'Reply 1'
    
    def test_flatten_thread_structure_with_object_parent(self):
        """Test flatten_thread_structure with object-based parent."""
        class MockPost:
            def __init__(self, text):
                self.text = text
        
        class MockThread:
            def __init__(self):
                self.parent = MockPost('Parent post')
                self.post = MockPost('Main post')
                self.replies = [MockPost('Reply 1')]
        
        thread_data = MagicMock()
        thread_data.thread = MockThread()
        
        result = flatten_thread_structure(thread_data)
        
        assert 'posts' in result
        assert len(result['posts']) == 3
    
    def test_flatten_thread_structure_empty_thread(self):
        """Test flatten_thread_structure with empty thread."""
        thread_data = {}
        
        result = flatten_thread_structure(thread_data)
        
        assert 'posts' in result
        assert len(result['posts']) == 0
    
    def test_flatten_thread_structure_none_node(self):
        """Test flatten_thread_structure with None node."""
        thread_data = {
            'thread': None
        }
        
        result = flatten_thread_structure(thread_data)
        
        assert 'posts' in result
        assert len(result['posts']) == 0
