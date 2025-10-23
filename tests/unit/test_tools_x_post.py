"""Tests for the X post tool."""
import pytest
import os
from unittest.mock import patch, MagicMock
from platforms.x.tools.post import PostToXArgs, post_to_x


class TestPostToXArgs:
    """Test the PostToXArgs Pydantic model."""
    
    def test_valid_args(self):
        """Test valid PostToXArgs creation."""
        args = PostToXArgs(text="Hello, X!")
        assert args.text == "Hello, X!"
    
    def test_text_length_validation_valid(self):
        """Test text length validation with valid length."""
        args = PostToXArgs(text="A" * 280)  # Exactly 280 characters
        assert args.text == "A" * 280
    
    def test_text_length_validation_invalid(self):
        """Test text length validation with invalid length."""
        with pytest.raises(ValueError, match="Text exceeds 280 character limit"):
            PostToXArgs(text="A" * 281)  # 281 characters
    
    def test_text_length_validation_exact_limit(self):
        """Test text length validation at exact limit."""
        text = "A" * 280
        args = PostToXArgs(text=text)
        assert args.text == text
    
    def test_empty_text(self):
        """Test empty text."""
        args = PostToXArgs(text="")
        assert args.text == ""
    
    def test_unicode_text(self):
        """Test unicode text."""
        text = "Hello 世界! 🌍"
        args = PostToXArgs(text=text)
        assert args.text == text
    
    def test_special_characters(self):
        """Test special characters."""
        text = "Hello @user #hashtag $money & more!"
        args = PostToXArgs(text=text)
        assert args.text == text
    
    def test_multiline_text(self):
        """Test multiline text."""
        text = "Line 1\nLine 2\nLine 3"
        args = PostToXArgs(text=text)
        assert args.text == text


class TestPostToX:
    """Test the post_to_x function."""
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_success(self, mock_post):
        """Test successful X post creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {
                'id': '1234567890',
                'text': 'Hello, X!'
            }
        }
        mock_post.return_value = mock_response
        
        result = post_to_x("Hello, X!")
        
        assert "Successfully posted to X" in result
        assert "Tweet ID: 1234567890" in result
        assert "URL: https://x.com/i/status/1234567890" in result
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_success_unknown_id(self, mock_post):
        """Test successful X post creation with unknown ID."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {
                'text': 'Hello, X!'
            }
        }
        mock_post.return_value = mock_response
        
        result = post_to_x("Hello, X!")
        
        assert "Successfully posted to X" in result
        assert "Tweet ID: unknown" in result
        assert "URL: https://x.com/i/status/unknown" in result
    
    def test_post_to_x_text_too_long(self):
        """Test post_to_x with text exceeding character limit."""
        long_text = "A" * 281
        with pytest.raises(Exception, match="Text exceeds 280 character limit"):
            post_to_x(long_text)
    
    def test_post_to_x_text_exact_limit(self):
        """Test post_to_x with text at exact character limit."""
        text = "A" * 280
        
        with patch.dict(os.environ, {
            'X_CONSUMER_KEY': 'test_consumer_key',
            'X_CONSUMER_SECRET': 'test_consumer_secret',
            'X_ACCESS_TOKEN': 'test_access_token',
            'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
        }):
            with patch('platforms.x.tools.post.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {
                    'data': {'id': '1234567890'}
                }
                mock_post.return_value = mock_response
                
                result = post_to_x(text)
                assert "Successfully posted to X" in result
    
    def test_post_to_x_missing_credentials(self):
        """Test post_to_x with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception, match="Missing X API credentials"):
                post_to_x("Hello, X!")
    
    def test_post_to_x_partial_credentials(self):
        """Test post_to_x with partial credentials."""
        with patch.dict(os.environ, {
            'X_CONSUMER_KEY': 'test_consumer_key',
            'X_CONSUMER_SECRET': 'test_consumer_secret',
            # Missing access tokens
        }):
            with pytest.raises(Exception, match="Missing X API credentials"):
                post_to_x("Hello, X!")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_api_error_400(self, mock_post):
        """Test post_to_x with API error 400."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="X API error: 400 - Bad Request"):
            post_to_x("Hello, X!")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_api_error_401(self, mock_post):
        """Test post_to_x with API error 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="X API error: 401 - Unauthorized"):
            post_to_x("Hello, X!")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_api_error_403(self, mock_post):
        """Test post_to_x with API error 403."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="X API error: 403 - Forbidden"):
            post_to_x("Hello, X!")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_api_error_429(self, mock_post):
        """Test post_to_x with API error 429 (rate limit)."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="X API error: 429 - Too Many Requests"):
            post_to_x("Hello, X!")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_unexpected_response_format(self, mock_post):
        """Test post_to_x with unexpected response format."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'unexpected': 'format'
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="Unexpected response format"):
            post_to_x("Hello, X!")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_network_error(self, mock_post):
        """Test post_to_x with network error."""
        mock_post.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception, match="Unexpected error posting to X: Connection error"):
            post_to_x("Hello, X!")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_timeout_error(self, mock_post):
        """Test post_to_x with timeout error."""
        mock_post.side_effect = Exception("Timeout error")
        
        with pytest.raises(Exception, match="Unexpected error posting to X: Timeout error"):
            post_to_x("Hello, X!")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_unexpected_error(self, mock_post):
        """Test post_to_x with unexpected error."""
        mock_post.side_effect = ValueError("Unexpected error")
        
        with pytest.raises(Exception, match="Unexpected error posting to X: Unexpected error"):
            post_to_x("Hello, X!")
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_empty_text(self, mock_post):
        """Test post_to_x with empty text."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {'id': '1234567890'}
        }
        mock_post.return_value = mock_response
        
        result = post_to_x("")
        assert "Successfully posted to X" in result
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_unicode_text(self, mock_post):
        """Test post_to_x with unicode text."""
        unicode_text = "Hello 世界! 🌍"
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {'id': '1234567890'}
        }
        mock_post.return_value = mock_response
        
        result = post_to_x(unicode_text)
        assert "Successfully posted to X" in result
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_special_characters(self, mock_post):
        """Test post_to_x with special characters."""
        special_text = "Hello @user #hashtag $money & more!"
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {'id': '1234567890'}
        }
        mock_post.return_value = mock_response
        
        result = post_to_x(special_text)
        assert "Successfully posted to X" in result
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_multiline_text(self, mock_post):
        """Test post_to_x with multiline text."""
        multiline_text = "Line 1\nLine 2\nLine 3"
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {'id': '1234567890'}
        }
        mock_post.return_value = mock_response
        
        result = post_to_x(multiline_text)
        assert "Successfully posted to X" in result
    
    @patch.dict(os.environ, {
        'X_CONSUMER_KEY': 'test_consumer_key',
        'X_CONSUMER_SECRET': 'test_consumer_secret',
        'X_ACCESS_TOKEN': 'test_access_token',
        'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
    })
    @patch('platforms.x.tools.post.requests.post')
    def test_post_to_x_request_parameters(self, mock_post):
        """Test post_to_x request parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'data': {'id': '1234567890'}
        }
        mock_post.return_value = mock_response
        
        post_to_x("Hello, X!")
        
        # Verify request parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        assert call_args[0][0] == "https://api.x.com/2/tweets"
        assert call_args[1]['headers'] == {"Content-Type": "application/json"}
        assert call_args[1]['json'] == {"text": "Hello, X!"}
        assert 'auth' in call_args[1]


class TestPostToXIntegration:
    """Integration tests for X post functionality."""
    
    def test_post_to_x_args_with_post_to_x(self):
        """Test using PostToXArgs with post_to_x."""
        args = PostToXArgs(text="Hello, X!")
        
        with patch.dict(os.environ, {
            'X_CONSUMER_KEY': 'test_consumer_key',
            'X_CONSUMER_SECRET': 'test_consumer_secret',
            'X_ACCESS_TOKEN': 'test_access_token',
            'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
        }):
            with patch('platforms.x.tools.post.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {
                    'data': {'id': '1234567890'}
                }
                mock_post.return_value = mock_response
                
                result = post_to_x(args.text)
                assert "Successfully posted to X" in result
    
    def test_post_to_x_error_handling_flow(self):
        """Test complete error handling flow."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception, match="Missing X API credentials"):
                post_to_x("Hello, X!")
    
    def test_post_to_x_success_flow(self):
        """Test complete success flow."""
        with patch.dict(os.environ, {
            'X_CONSUMER_KEY': 'test_consumer_key',
            'X_CONSUMER_SECRET': 'test_consumer_secret',
            'X_ACCESS_TOKEN': 'test_access_token',
            'X_ACCESS_TOKEN_SECRET': 'test_access_token_secret'
        }):
            with patch('platforms.x.tools.post.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {
                    'data': {'id': '1234567890'}
                }
                mock_post.return_value = mock_response
                
                result = post_to_x("Hello, X!")
                assert "Successfully posted to X" in result
                assert "Tweet ID: 1234567890" in result
                assert "URL: https://x.com/i/status/1234567890" in result
