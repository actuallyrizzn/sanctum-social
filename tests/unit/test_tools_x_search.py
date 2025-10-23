"""Tests for the X search tool."""
import pytest
import os
import yaml
import requests
from unittest.mock import patch, MagicMock
from platforms.x.tools.search import SearchXArgs, search_x_posts


class TestSearchXArgs:
    """Test the SearchXArgs Pydantic model."""
    
    def test_valid_args(self):
        """Test valid SearchXArgs creation."""
        args = SearchXArgs(username="testuser")
        assert args.username == "testuser"
        assert args.max_results == 10
        assert args.exclude_replies is False
        assert args.exclude_retweets is False
    
    def test_args_with_custom_values(self):
        """Test SearchXArgs with custom values."""
        args = SearchXArgs(
            username="testuser",
            max_results=25,
            exclude_replies=True,
            exclude_retweets=True
        )
        assert args.username == "testuser"
        assert args.max_results == 25
        assert args.exclude_replies is True
        assert args.exclude_retweets is True
    
    def test_args_with_max_results_boundary(self):
        """Test SearchXArgs with max_results at boundary."""
        args = SearchXArgs(username="testuser", max_results=100)
        assert args.max_results == 100
    
    def test_args_with_max_results_over_limit(self):
        """Test SearchXArgs with max_results over limit."""
        args = SearchXArgs(username="testuser", max_results=150)
        assert args.max_results == 150  # Pydantic doesn't enforce max by default
    
    def test_args_with_empty_username(self):
        """Test SearchXArgs with empty username."""
        args = SearchXArgs(username="")
        assert args.username == ""
    
    def test_args_with_special_characters_username(self):
        """Test SearchXArgs with special characters in username."""
        args = SearchXArgs(username="test_user123")
        assert args.username == "test_user123"


class TestSearchXPosts:
    """Test the search_x_posts function."""
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_success(self, mock_get):
        """Test successful X posts search."""
        # Mock user lookup response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456789",
                "username": "testuser",
                "name": "Test User",
                "description": "Test description"
            }
        }
        
        # Mock tweets response
        tweets_response = MagicMock()
        tweets_response.status_code = 200
        tweets_response.json.return_value = {
            "data": [
                {
                    "id": "tweet123",
                    "text": "Hello world!",
                    "created_at": "2024-01-01T12:00:00Z",
                    "author_id": "123456789"
                }
            ]
        }
        
        mock_get.side_effect = [user_response, tweets_response]
        
        result = search_x_posts("testuser")
        
        # Parse YAML result
        parsed_result = yaml.safe_load(result)
        assert "x_user_posts" in parsed_result
        assert parsed_result["x_user_posts"]["user"]["username"] == "testuser"
        assert parsed_result["x_user_posts"]["post_count"] == 1
        assert len(parsed_result["x_user_posts"]["posts"]) == 1
        assert parsed_result["x_user_posts"]["posts"][0]["text"] == "Hello world!"
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_with_exclusions(self, mock_get):
        """Test X posts search with exclusions."""
        # Mock user lookup response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456789",
                "username": "testuser",
                "name": "Test User",
                "description": "Test description"
            }
        }
        
        # Mock tweets response
        tweets_response = MagicMock()
        tweets_response.status_code = 200
        tweets_response.json.return_value = {
            "data": [
                {
                    "id": "tweet123",
                    "text": "Hello world!",
                    "created_at": "2024-01-01T12:00:00Z",
                    "author_id": "123456789"
                }
            ]
        }
        
        mock_get.side_effect = [user_response, tweets_response]
        
        result = search_x_posts("testuser", max_results=5, exclude_replies=True, exclude_retweets=True)
        
        # Verify the request parameters included exclusions
        tweets_call = mock_get.call_args_list[1]
        assert "exclude" in tweets_call[1]["params"]
        assert tweets_call[1]["params"]["exclude"] == "replies,retweets"
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_with_retweets(self, mock_get):
        """Test X posts search with retweets."""
        # Mock user lookup response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456789",
                "username": "testuser",
                "name": "Test User",
                "description": "Test description"
            }
        }
        
        # Mock tweets response with retweet
        tweets_response = MagicMock()
        tweets_response.status_code = 200
        tweets_response.json.return_value = {
            "data": [
                {
                    "id": "tweet123",
                    "text": "RT @otheruser: Original tweet",
                    "created_at": "2024-01-01T12:00:00Z",
                    "author_id": "123456789",
                    "referenced_tweets": [
                        {
                            "type": "retweeted",
                            "id": "original123"
                        }
                    ]
                }
            ]
        }
        
        mock_get.side_effect = [user_response, tweets_response]
        
        result = search_x_posts("testuser")
        
        # Parse YAML result
        parsed_result = yaml.safe_load(result)
        assert parsed_result["x_user_posts"]["posts"][0]["is_retweet"] is True
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_with_replies(self, mock_get):
        """Test X posts search with replies."""
        # Mock user lookup response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456789",
                "username": "testuser",
                "name": "Test User",
                "description": "Test description"
            }
        }
        
        # Mock tweets response with reply
        tweets_response = MagicMock()
        tweets_response.status_code = 200
        tweets_response.json.return_value = {
            "data": [
                {
                    "id": "tweet123",
                    "text": "This is a reply",
                    "created_at": "2024-01-01T12:00:00Z",
                    "author_id": "123456789",
                    "conversation_id": "conversation123"
                }
            ]
        }
        
        mock_get.side_effect = [user_response, tweets_response]
        
        result = search_x_posts("testuser")
        
        # Parse YAML result
        parsed_result = yaml.safe_load(result)
        assert parsed_result["x_user_posts"]["posts"][0]["conversation_id"] == "conversation123"
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_max_results_capped(self, mock_get):
        """Test X posts search with max_results capped at 100."""
        # Mock user lookup response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456789",
                "username": "testuser",
                "name": "Test User",
                "description": "Test description"
            }
        }
        
        # Mock tweets response
        tweets_response = MagicMock()
        tweets_response.status_code = 200
        tweets_response.json.return_value = {"data": []}
        
        mock_get.side_effect = [user_response, tweets_response]
        
        result = search_x_posts("testuser", max_results=150)
        
        # Verify max_results was capped at 100
        tweets_call = mock_get.call_args_list[1]
        assert tweets_call[1]["params"]["max_results"] == 100
    
    def test_search_x_posts_missing_credentials(self):
        """Test search_x_posts with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception, match="X API credentials not found"):
                search_x_posts("testuser")
    
    def test_search_x_posts_partial_credentials(self):
        """Test search_x_posts with partial credentials."""
        with patch.dict(os.environ, {
            'X_CONSUMER_KEY': 'test_key',
            'X_CONSUMER_SECRET': 'test_secret',
            # Missing access tokens
        }):
            with pytest.raises(Exception, match="X API credentials not found"):
                search_x_posts("testuser")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    def test_search_x_posts_oauth_credentials_but_no_bearer(self):
        """Test search_x_posts with OAuth credentials but no bearer token."""
        with pytest.raises(Exception, match="Bearer token required"):
            search_x_posts("testuser")
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_user_not_found(self, mock_get):
        """Test search_x_posts with user not found."""
        # Mock user lookup response with 404
        user_response = MagicMock()
        user_response.status_code = 404
        user_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        mock_get.return_value = user_response
        
        with pytest.raises(Exception, match="User @testuser not found"):
            search_x_posts("testuser")
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_user_lookup_error(self, mock_get):
        """Test search_x_posts with user lookup error."""
        # Mock user lookup response with error
        user_response = MagicMock()
        user_response.status_code = 500
        user_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Internal Server Error")
        
        mock_get.return_value = user_response
        
        with pytest.raises(Exception, match="Failed to look up user @testuser"):
            search_x_posts("testuser")
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_user_data_missing(self, mock_get):
        """Test search_x_posts with missing user data."""
        # Mock user lookup response without data
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "errors": [{"message": "User not found"}]
        }
        
        mock_get.return_value = user_response
        
        with pytest.raises(Exception, match="User @testuser not found"):
            search_x_posts("testuser")
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_tweets_error(self, mock_get):
        """Test search_x_posts with tweets fetch error."""
        # Mock user lookup response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456789",
                "username": "testuser",
                "name": "Test User",
                "description": "Test description"
            }
        }
        
        # Mock tweets response with error
        tweets_response = MagicMock()
        tweets_response.raise_for_status.side_effect = Exception("API Error")
        
        mock_get.side_effect = [user_response, tweets_response]
        
        with pytest.raises(Exception, match="Failed to fetch posts from @testuser"):
            search_x_posts("testuser")
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_empty_tweets(self, mock_get):
        """Test search_x_posts with empty tweets."""
        # Mock user lookup response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456789",
                "username": "testuser",
                "name": "Test User",
                "description": "Test description"
            }
        }
        
        # Mock tweets response with empty data
        tweets_response = MagicMock()
        tweets_response.status_code = 200
        tweets_response.json.return_value = {"data": []}
        
        mock_get.side_effect = [user_response, tweets_response]
        
        result = search_x_posts("testuser")
        
        # Parse YAML result
        parsed_result = yaml.safe_load(result)
        assert parsed_result["x_user_posts"]["post_count"] == 0
        assert len(parsed_result["x_user_posts"]["posts"]) == 0
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_multiple_tweets(self, mock_get):
        """Test search_x_posts with multiple tweets."""
        # Mock user lookup response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456789",
                "username": "testuser",
                "name": "Test User",
                "description": "Test description"
            }
        }
        
        # Mock tweets response with multiple tweets
        tweets_response = MagicMock()
        tweets_response.status_code = 200
        tweets_response.json.return_value = {
            "data": [
                {
                    "id": "tweet1",
                    "text": "First tweet",
                    "created_at": "2024-01-01T12:00:00Z",
                    "author_id": "123456789"
                },
                {
                    "id": "tweet2",
                    "text": "Second tweet",
                    "created_at": "2024-01-01T13:00:00Z",
                    "author_id": "123456789"
                }
            ]
        }
        
        mock_get.side_effect = [user_response, tweets_response]
        
        result = search_x_posts("testuser")
        
        # Parse YAML result
        parsed_result = yaml.safe_load(result)
        assert parsed_result["x_user_posts"]["post_count"] == 2
        assert len(parsed_result["x_user_posts"]["posts"]) == 2
        assert parsed_result["x_user_posts"]["posts"][0]["text"] == "First tweet"
        assert parsed_result["x_user_posts"]["posts"][1]["text"] == "Second tweet"
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_network_error(self, mock_get):
        """Test search_x_posts with network error."""
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception, match="Error searching X posts: Network error"):
            search_x_posts("testuser")
    
    @patch.dict(os.environ, {
        'X_BEARER_TOKEN': 'test_bearer_token'
    })
    @patch('requests.get')
    def test_search_x_posts_request_parameters(self, mock_get):
        """Test search_x_posts request parameters."""
        # Mock user lookup response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "data": {
                "id": "123456789",
                "username": "testuser",
                "name": "Test User",
                "description": "Test description"
            }
        }
        
        # Mock tweets response
        tweets_response = MagicMock()
        tweets_response.status_code = 200
        tweets_response.json.return_value = {"data": []}
        
        mock_get.side_effect = [user_response, tweets_response]
        
        search_x_posts("testuser", max_results=25)
        
        # Verify user lookup request
        user_call = mock_get.call_args_list[0]
        assert "testuser" in user_call[0][0]
        assert user_call[1]["headers"]["Authorization"] == "Bearer test_bearer_token"
        
        # Verify tweets request
        tweets_call = mock_get.call_args_list[1]
        assert "123456789" in tweets_call[0][0]
        assert tweets_call[1]["params"]["max_results"] == 25


class TestSearchXPostsIntegration:
    """Integration tests for X search functionality."""
    
    def test_search_x_args_with_search_x_posts(self):
        """Test using SearchXArgs with search_x_posts."""
        args = SearchXArgs(username="testuser", max_results=5)
        
        with patch.dict(os.environ, {
            'X_BEARER_TOKEN': 'test_bearer_token'
        }):
            with patch('requests.get') as mock_get:
                # Mock user lookup response
                user_response = MagicMock()
                user_response.status_code = 200
                user_response.json.return_value = {
                    "data": {
                        "id": "123456789",
                        "username": "testuser",
                        "name": "Test User",
                        "description": "Test description"
                    }
                }
                
                # Mock tweets response
                tweets_response = MagicMock()
                tweets_response.status_code = 200
                tweets_response.json.return_value = {"data": []}
                
                mock_get.side_effect = [user_response, tweets_response]
                
                result = search_x_posts(args.username, args.max_results, args.exclude_replies, args.exclude_retweets)
                
                # Parse YAML result
                parsed_result = yaml.safe_load(result)
                assert parsed_result["x_user_posts"]["user"]["username"] == "testuser"
    
    def test_search_x_posts_error_handling_flow(self):
        """Test complete error handling flow."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception, match="X API credentials not found"):
                search_x_posts("testuser")
    
    def test_search_x_posts_success_flow(self):
        """Test complete success flow."""
        with patch.dict(os.environ, {
            'X_BEARER_TOKEN': 'test_bearer_token'
        }):
            with patch('requests.get') as mock_get:
                # Mock user lookup response
                user_response = MagicMock()
                user_response.status_code = 200
                user_response.json.return_value = {
                    "data": {
                        "id": "123456789",
                        "username": "testuser",
                        "name": "Test User",
                        "description": "Test description"
                    }
                }
                
                # Mock tweets response
                tweets_response = MagicMock()
                tweets_response.status_code = 200
                tweets_response.json.return_value = {
                    "data": [
                        {
                            "id": "tweet123",
                            "text": "Hello world!",
                            "created_at": "2024-01-01T12:00:00Z",
                            "author_id": "123456789"
                        }
                    ]
                }
                
                mock_get.side_effect = [user_response, tweets_response]
                
                result = search_x_posts("testuser")
                
                # Parse YAML result
                parsed_result = yaml.safe_load(result)
                assert parsed_result["x_user_posts"]["user"]["username"] == "testuser"
                assert parsed_result["x_user_posts"]["post_count"] == 1
                assert parsed_result["x_user_posts"]["posts"][0]["text"] == "Hello world!"
