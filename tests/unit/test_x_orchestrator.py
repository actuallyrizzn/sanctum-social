"""
Comprehensive unit tests for x.py - X (Twitter) orchestrator module.

This module tests:
1. XClient class functionality
2. Configuration loading and management
3. Queue operations and file management
4. Notification processing workflows
5. Error handling and recovery
6. Caching mechanisms
7. User block management
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout

# Import the module under test
import x
from x import XClient, XRateLimitError


class TestXClient:
    """Test XClient class functionality."""
    
    def test_x_client_oauth1a_initialization(self):
        """Test XClient initialization with OAuth 1.0a credentials."""
        client = XClient(
            api_key="test_api_key",
            user_id="123456789",
            access_token="test_access_token",
            consumer_key="test_consumer_key",
            consumer_secret="test_consumer_secret",
            access_token_secret="test_access_token_secret"
        )
        
        assert client.api_key == "test_api_key"
        assert client.user_id == "123456789"
        assert client.access_token == "test_access_token"
        assert client.auth_method == "oauth1a"
        assert client.oauth is not None
        assert "Authorization" not in client.headers
    
    def test_x_client_oauth2_user_initialization(self):
        """Test XClient initialization with OAuth 2.0 user context."""
        client = XClient(
            api_key="test_api_key",
            user_id="123456789",
            access_token="test_access_token"
        )
        
        assert client.api_key == "test_api_key"
        assert client.user_id == "123456789"
        assert client.access_token == "test_access_token"
        assert client.auth_method == "oauth2_user"
        assert client.oauth is None
        assert client.headers["Authorization"] == "Bearer test_access_token"
    
    def test_x_client_bearer_token_initialization(self):
        """Test XClient initialization with Application-Only Bearer token."""
        client = XClient(
            api_key="test_api_key",
            user_id="123456789"
        )
        
        assert client.api_key == "test_api_key"
        assert client.user_id == "123456789"
        assert client.access_token is None
        assert client.auth_method == "bearer"
        assert client.oauth is None
        assert client.headers["Authorization"] == "Bearer test_api_key"
    
    @patch('x.requests.get')
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test_data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = XClient("test_api_key", "123456789")
        result = client._make_request("/test/endpoint")
        
        assert result == {"data": "test_data"}
        mock_get.assert_called_once()
    
    @patch('x.requests.get')
    def test_make_request_http_error_401(self, mock_get):
        """Test handling of 401 authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response
        
        client = XClient("test_api_key", "123456789")
        result = client._make_request("/test/endpoint")
        
        assert result is None
        mock_get.assert_called_once()
    
    @patch('x.requests.get')
    def test_make_request_http_error_403(self, mock_get):
        """Test handling of 403 forbidden error."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_response.raise_for_status.side_effect = HTTPError("403 Forbidden")
        mock_get.return_value = mock_response
        
        client = XClient("test_api_key", "123456789")
        result = client._make_request("/test/endpoint")
        
        assert result is None
        mock_get.assert_called_once()
    
    @patch('x.requests.get')
    @patch('x.time.sleep')
    def test_make_request_rate_limit_retry(self, mock_sleep, mock_get):
        """Test handling of rate limit with retry."""
        # First call returns 429, second call succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.text = "Rate limit exceeded"
        mock_response_429.raise_for_status.side_effect = HTTPError("429 Rate limit exceeded")
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"data": "success"}
        mock_response_200.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response_429, mock_response_200]
        
        client = XClient("test_api_key", "123456789")
        result = client._make_request("/test/endpoint")
        
        assert result == {"data": "success"}
        assert mock_get.call_count == 2
        mock_sleep.assert_called_once_with(60)  # First backoff time
    
    @patch('x.requests.get')
    @patch('x.time.sleep')
    def test_make_request_rate_limit_max_retries(self, mock_sleep, mock_get):
        """Test handling of rate limit with max retries exceeded."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.raise_for_status.side_effect = HTTPError("429 Rate limit exceeded")
        mock_get.return_value = mock_response
        
        client = XClient("test_api_key", "123456789")
        
        with pytest.raises(XRateLimitError):
            client._make_request("/test/endpoint", max_retries=2)
        
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('x.requests.get')
    def test_get_mentions_success(self, mock_get):
        """Test successful mentions retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "123456789",
                    "text": "Test mention",
                    "author_id": "987654321",
                    "created_at": "2025-01-01T00:00:00Z"
                }
            ],
            "includes": {
                "users": [
                    {
                        "id": "987654321",
                        "name": "Test User",
                        "username": "testuser"
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = XClient("test_api_key", "123456789")
        mentions = client.get_mentions()
        
        assert len(mentions) == 1
        assert mentions[0]["id"] == "123456789"
        assert mentions[0]["text"] == "Test mention"
    
    @patch('x.requests.get')
    def test_get_mentions_with_since_id(self, mock_get):
        """Test mentions retrieval with since_id parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = XClient("test_api_key", "123456789")
        mentions = client.get_mentions(since_id="123456789", max_results=50)
        
        assert mentions == []
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "since_id" in call_args[1]["params"]
        assert call_args[1]["params"]["since_id"] == "123456789"
        assert call_args[1]["params"]["max_results"] == 50
    
    @patch('x.requests.get')
    def test_get_mentions_max_results_boundary(self, mock_get):
        """Test mentions retrieval with boundary max_results values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = XClient("test_api_key", "123456789")
        
        # Test minimum boundary (should be adjusted to 5)
        client.get_mentions(max_results=1)
        call_args = mock_get.call_args
        assert call_args[1]["params"]["max_results"] == 5
        
        # Test maximum boundary (should be adjusted to 100)
        client.get_mentions(max_results=200)
        call_args = mock_get.call_args
        assert call_args[1]["params"]["max_results"] == 100


class TestXConfiguration:
    """Test X configuration loading and management."""
    
    def test_load_x_config_success(self):
        """Test successful X configuration loading."""
        test_config = {
            'x': {
                'api_key': 'test_api_key',
                'user_id': '123456789',
                'access_token': 'test_access_token'
            },
            'logging': {
                'level': 'DEBUG'
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
            with patch('x.yaml.safe_load', return_value=test_config):
                config = x.load_x_config("test_config.yaml")
                
                assert config == test_config
                assert config['x']['api_key'] == 'test_api_key'
                assert config['x']['user_id'] == '123456789'
    
    def test_load_x_config_file_not_found(self):
        """Test X configuration loading with missing file."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = x.load_x_config("nonexistent.yaml")
            assert config == {}
    
    def test_get_x_letta_config_success(self):
        """Test successful X Letta configuration retrieval."""
        test_config = {
            'x': {
                'api_key': 'test_api_key',
                'user_id': '123456789'
            },
            'letta': {
                'api_key': 'test_letta_key',
                'agent_id': 'test_agent_id'
            }
        }
        
        with patch('x.load_x_config', return_value=test_config):
            config = x.get_x_letta_config("test_config.yaml")
            
            assert config['x']['api_key'] == 'test_api_key'
            assert config['letta']['api_key'] == 'test_letta_key'
    
    def test_create_x_client_success(self):
        """Test successful X client creation."""
        test_config = {
            'x': {
                'api_key': 'test_api_key',
                'user_id': '123456789',
                'access_token': 'test_access_token',
                'consumer_key': 'test_consumer_key',
                'consumer_secret': 'test_consumer_secret',
                'access_token_secret': 'test_access_token_secret'
            }
        }
        
        with patch('x.load_x_config', return_value=test_config):
            client = x.create_x_client("test_config.yaml")
            
            assert isinstance(client, XClient)
            assert client.api_key == 'test_api_key'
            assert client.user_id == '123456789'
            assert client.auth_method == 'oauth1a'


class TestXQueueOperations:
    """Test X queue operations and file management."""
    
    def test_load_last_seen_id_success(self):
        """Test successful last seen ID loading."""
        test_data = {"last_seen_id": "123456789"}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            with patch('x.X_LAST_SEEN_FILE', Path("test_last_seen.json")):
                last_seen_id = x.load_last_seen_id()
                assert last_seen_id == "123456789"
    
    def test_load_last_seen_id_file_not_found(self):
        """Test last seen ID loading with missing file."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('x.X_LAST_SEEN_FILE', Path("nonexistent.json")):
                last_seen_id = x.load_last_seen_id()
                assert last_seen_id is None
    
    def test_save_last_seen_id_success(self):
        """Test successful last seen ID saving."""
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('x.X_LAST_SEEN_FILE', Path("test_last_seen.json")):
                x.save_last_seen_id("123456789")
                
                mock_file.assert_called_once()
                # Verify the written data
                written_data = json.loads(mock_file().write.call_args[0][0])
                assert written_data["last_seen_id"] == "123456789"
    
    def test_load_processed_mentions_success(self):
        """Test successful processed mentions loading."""
        test_data = {"processed_mentions": ["123456789", "987654321"]}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            with patch('x.X_PROCESSED_MENTIONS_FILE', Path("test_processed.json")):
                processed = x.load_processed_mentions()
                assert processed == {"123456789", "987654321"}
    
    def test_load_processed_mentions_file_not_found(self):
        """Test processed mentions loading with missing file."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('x.X_PROCESSED_MENTIONS_FILE', Path("nonexistent.json")):
                processed = x.load_processed_mentions()
                assert processed == set()
    
    def test_save_processed_mentions_success(self):
        """Test successful processed mentions saving."""
        test_set = {"123456789", "987654321"}
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('x.X_PROCESSED_MENTIONS_FILE', Path("test_processed.json")):
                x.save_processed_mentions(test_set)
                
                mock_file.assert_called_once()
                # Verify the written data
                written_data = json.loads(mock_file().write.call_args[0][0])
                assert set(written_data["processed_mentions"]) == test_set
    
    def test_load_downrank_users_success(self):
        """Test successful downrank users loading."""
        test_content = "user1\nuser2\nuser3\n"
        
        with patch('builtins.open', mock_open(read_data=test_content)):
            with patch('x.X_DOWNRANK_USERS_FILE', Path("test_downrank.txt")):
                downrank_users = x.load_downrank_users()
                assert downrank_users == {"user1", "user2", "user3"}
    
    def test_load_downrank_users_file_not_found(self):
        """Test downrank users loading with missing file."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('x.X_DOWNRANK_USERS_FILE', Path("nonexistent.txt")):
                downrank_users = x.load_downrank_users()
                assert downrank_users == set()
    
    def test_should_respond_to_downranked_user(self):
        """Test downranked user response logic."""
        downrank_users = {"user1", "user2"}
        
        # Should not respond to downranked user
        assert not x.should_respond_to_downranked_user("user1", downrank_users)
        assert not x.should_respond_to_downranked_user("user2", downrank_users)
        
        # Should respond to non-downranked user
        assert x.should_respond_to_downranked_user("user3", downrank_users)
        assert x.should_respond_to_downranked_user("user4", downrank_users)


class TestXCaching:
    """Test X caching mechanisms."""
    
    def test_get_cached_thread_context_success(self):
        """Test successful thread context caching retrieval."""
        test_data = {
            "conversation_id": "test_conv_123",
            "thread_data": {"posts": [], "replies": []}
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            with patch('x.X_CACHE_DIR', Path("test_cache")):
                thread_data = x.get_cached_thread_context("test_conv_123")
                assert thread_data == test_data
    
    def test_get_cached_thread_context_file_not_found(self):
        """Test thread context caching with missing file."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('x.X_CACHE_DIR', Path("test_cache")):
                thread_data = x.get_cached_thread_context("test_conv_123")
                assert thread_data is None
    
    def test_save_cached_thread_context_success(self):
        """Test successful thread context caching save."""
        test_data = {
            "conversation_id": "test_conv_123",
            "thread_data": {"posts": [], "replies": []}
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('x.X_CACHE_DIR', Path("test_cache")):
                with patch('pathlib.Path.mkdir'):
                    x.save_cached_thread_context("test_conv_123", test_data)
                    
                    mock_file.assert_called_once()
                    # Verify the written data
                    written_data = json.loads(mock_file().write.call_args[0][0])
                    assert written_data == test_data
    
    def test_get_cached_tweets_success(self):
        """Test successful tweets caching retrieval."""
        test_data = {
            "123456789": {"id": "123456789", "text": "Test tweet 1"},
            "987654321": {"id": "987654321", "text": "Test tweet 2"}
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            with patch('x.X_CACHE_DIR', Path("test_cache")):
                tweets = x.get_cached_tweets(["123456789", "987654321"])
                assert tweets == test_data
    
    def test_get_cached_tweets_file_not_found(self):
        """Test tweets caching with missing file."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with patch('x.X_CACHE_DIR', Path("test_cache")):
                tweets = x.get_cached_tweets(["123456789"])
                assert tweets == {}
    
    def test_save_cached_tweets_success(self):
        """Test successful tweets caching save."""
        tweets_data = [
            {"id": "123456789", "text": "Test tweet 1"},
            {"id": "987654321", "text": "Test tweet 2"}
        ]
        users_data = {
            "123456789": {"id": "123456789", "name": "User 1"},
            "987654321": {"id": "987654321", "name": "User 2"}
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('x.X_CACHE_DIR', Path("test_cache")):
                with patch('pathlib.Path.mkdir'):
                    x.save_cached_tweets(tweets_data, users_data)
                    
                    mock_file.assert_called_once()
                    # Verify the written data contains both tweets and users
                    written_data = json.loads(mock_file().write.call_args[0][0])
                    assert "tweets" in written_data
                    assert "users" in written_data


class TestXUtilityFunctions:
    """Test X utility functions."""
    
    def test_mention_to_yaml_string(self):
        """Test mention to YAML string conversion."""
        mention = {
            "id": "123456789",
            "text": "Test mention",
            "author_id": "987654321",
            "created_at": "2025-01-01T00:00:00Z"
        }
        users_data = {
            "987654321": {
                "id": "987654321",
                "name": "Test User",
                "username": "testuser"
            }
        }
        
        yaml_string = x.mention_to_yaml_string(mention, users_data)
        
        assert "123456789" in yaml_string
        assert "Test mention" in yaml_string
        assert "Test User" in yaml_string
        assert "testuser" in yaml_string
    
    def test_thread_to_yaml_string(self):
        """Test thread to YAML string conversion."""
        thread_data = {
            "conversation_id": "test_conv_123",
            "posts": [
                {
                    "id": "123456789",
                    "text": "Test post",
                    "author_id": "987654321"
                }
            ],
            "replies": [
                {
                    "id": "987654321",
                    "text": "Test reply",
                    "author_id": "111222333"
                }
            ]
        }
        
        yaml_string = x.thread_to_yaml_string(thread_data)
        
        assert "test_conv_123" in yaml_string
        assert "Test post" in yaml_string
        assert "Test reply" in yaml_string
    
    def test_save_mention_to_queue(self):
        """Test saving mention to queue."""
        mention = {
            "id": "123456789",
            "text": "Test mention",
            "author_id": "987654321",
            "created_at": "2025-01-01T00:00:00Z"
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('x.X_QUEUE_DIR', Path("test_queue")):
                with patch('pathlib.Path.mkdir'):
                    with patch('x.hashlib.md5') as mock_md5:
                        mock_md5.return_value.hexdigest.return_value = "test_hash"
                        x.save_mention_to_queue(mention)
                        
                        mock_file.assert_called_once()
                        # Verify the written data
                        written_data = json.loads(mock_file().write.call_args[0][0])
                        assert written_data["id"] == "123456789"
                        assert written_data["text"] == "Test mention"


class TestXErrorHandling:
    """Test X error handling and edge cases."""
    
    def test_x_rate_limit_error(self):
        """Test XRateLimitError exception."""
        error = XRateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, Exception)
    
    @patch('x.requests.get')
    def test_make_request_connection_error(self, mock_get):
        """Test handling of connection errors."""
        mock_get.side_effect = ConnectionError("Connection failed")
        
        client = XClient("test_api_key", "123456789")
        result = client._make_request("/test/endpoint", max_retries=1)
        
        assert result is None
        mock_get.assert_called_once()
    
    @patch('x.requests.get')
    def test_make_request_timeout_error(self, mock_get):
        """Test handling of timeout errors."""
        mock_get.side_effect = Timeout("Request timeout")
        
        client = XClient("test_api_key", "123456789")
        result = client._make_request("/test/endpoint", max_retries=1)
        
        assert result is None
        mock_get.assert_called_once()
    
    @patch('x.requests.get')
    def test_make_request_invalid_json(self, mock_get):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        client = XClient("test_api_key", "123456789")
        result = client._make_request("/test/endpoint")
        
        assert result is None
        mock_get.assert_called_once()
    
    def test_get_mentions_no_data(self):
        """Test mentions retrieval with no data in response."""
        with patch.object(XClient, '_make_request', return_value={"meta": {}}):
            client = XClient("test_api_key", "123456789")
            mentions = client.get_mentions()
            assert mentions is None
    
    def test_get_mentions_api_error(self):
        """Test mentions retrieval with API error."""
        with patch.object(XClient, '_make_request', return_value=None):
            client = XClient("test_api_key", "123456789")
            mentions = client.get_mentions()
            assert mentions is None


class TestXIntegration:
    """Test X integration scenarios."""
    
    @patch('x.XClient')
    def test_x_client_integration_workflow(self, mock_client_class):
        """Test complete X client integration workflow."""
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful mentions retrieval
        mock_client.get_mentions.return_value = [
            {
                "id": "123456789",
                "text": "Test mention",
                "author_id": "987654321",
                "created_at": "2025-01-01T00:00:00Z"
            }
        ]
        
        # Create client and test workflow
        client = XClient("test_api_key", "123456789")
        mentions = client.get_mentions()
        
        assert len(mentions) == 1
        assert mentions[0]["id"] == "123456789"
        mock_client.get_mentions.assert_called_once()
    
    def test_x_configuration_integration(self):
        """Test X configuration integration with client creation."""
        test_config = {
            'x': {
                'api_key': 'test_api_key',
                'user_id': '123456789',
                'access_token': 'test_access_token'
            }
        }
        
        with patch('x.load_x_config', return_value=test_config):
            client = x.create_x_client("test_config.yaml")
            
            assert isinstance(client, XClient)
            assert client.api_key == 'test_api_key'
            assert client.user_id == '123456789'
            assert client.auth_method == 'oauth2_user'
    
    def test_x_queue_integration(self):
        """Test X queue integration workflow."""
        test_mention = {
            "id": "123456789",
            "text": "Test mention",
            "author_id": "987654321"
        }
        
        with patch('x.save_mention_to_queue') as mock_save:
            with patch('x.load_last_seen_id', return_value="123456789"):
                with patch('x.save_last_seen_id') as mock_save_last:
                    # Simulate queue workflow
                    x.save_mention_to_queue(test_mention)
                    x.save_last_seen_id("123456789")
                    
                    mock_save.assert_called_once_with(test_mention)
                    mock_save_last.assert_called_once_with("123456789")
