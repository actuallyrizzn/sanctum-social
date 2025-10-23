"""Tests for the Whitewind blog post creation tool."""
import pytest
import os
import requests
from unittest.mock import patch, MagicMock
from tools.whitewind import WhitewindPostArgs, create_whitewind_blog_post


class TestWhitewindPostArgs:
    """Test the WhitewindPostArgs Pydantic model."""
    
    def test_valid_args(self):
        """Test valid WhitewindPostArgs creation."""
        args = WhitewindPostArgs(title="Test Post", content="Test content")
        assert args.title == "Test Post"
        assert args.content == "Test content"
        assert args.subtitle is None
    
    def test_args_with_subtitle(self):
        """Test WhitewindPostArgs with subtitle."""
        args = WhitewindPostArgs(
            title="Test Post", 
            content="Test content",
            subtitle="Test subtitle"
        )
        assert args.title == "Test Post"
        assert args.content == "Test content"
        assert args.subtitle == "Test subtitle"
    
    def test_args_with_empty_title(self):
        """Test WhitewindPostArgs with empty title."""
        args = WhitewindPostArgs(title="", content="Test content")
        assert args.title == ""
        assert args.content == "Test content"
    
    def test_args_with_empty_content(self):
        """Test WhitewindPostArgs with empty content."""
        args = WhitewindPostArgs(title="Test Post", content="")
        assert args.title == "Test Post"
        assert args.content == ""
    
    def test_args_with_long_content(self):
        """Test WhitewindPostArgs with long content."""
        long_content = "This is a very long content " * 100
        args = WhitewindPostArgs(title="Test Post", content=long_content)
        assert args.title == "Test Post"
        assert args.content == long_content
    
    def test_args_with_special_characters(self):
        """Test WhitewindPostArgs with special characters."""
        args = WhitewindPostArgs(
            title="Test Post with émojis 🚀",
            content="Content with special chars: @#$%^&*()",
            subtitle="Subtitle with unicode: ñáéíóú"
        )
        assert args.title == "Test Post with émojis 🚀"
        assert args.content == "Content with special chars: @#$%^&*()"
        assert args.subtitle == "Subtitle with unicode: ñáéíóú"


class TestCreateWhitewindBlogPost:
    """Test the create_whitewind_blog_post function."""
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_success(self, mock_post):
        """Test successful Whitewind blog post creation."""
        # Mock session response
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.return_value = {
            "accessJwt": "test_access_token",
            "did": "did:plc:test123",
            "handle": "testuser"
        }
        
        # Mock post creation response
        post_response = MagicMock()
        post_response.status_code = 200
        post_response.json.return_value = {
            "uri": "at://did:plc:test123/com.whtwnd.blog.entry/test123"
        }
        
        mock_post.side_effect = [session_response, post_response]
        
        result = create_whitewind_blog_post("Test Post", "Test content")
        
        assert "Successfully created Whitewind blog post!" in result
        assert "Title: Test Post" in result
        assert "URL: https://whtwnd.com/testuser/test123" in result
        assert "Theme: github-light" in result
        assert "Visibility: public" in result
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_with_subtitle(self, mock_post):
        """Test Whitewind blog post creation with subtitle."""
        # Mock session response
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.return_value = {
            "accessJwt": "test_access_token",
            "did": "did:plc:test123",
            "handle": "testuser"
        }
        
        # Mock post creation response
        post_response = MagicMock()
        post_response.status_code = 200
        post_response.json.return_value = {
            "uri": "at://did:plc:test123/com.whtwnd.blog.entry/test123"
        }
        
        mock_post.side_effect = [session_response, post_response]
        
        result = create_whitewind_blog_post("Test Post", "Test content", "Test subtitle")
        
        assert "Successfully created Whitewind blog post!" in result
        assert "Title: Test Post" in result
        assert "Subtitle: Test subtitle" in result
        assert "URL: https://whtwnd.com/testuser/test123" in result
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_without_uri(self, mock_post):
        """Test Whitewind blog post creation without URI in response."""
        # Mock session response
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.return_value = {
            "accessJwt": "test_access_token",
            "did": "did:plc:test123",
            "handle": "testuser"
        }
        
        # Mock post creation response without URI
        post_response = MagicMock()
        post_response.status_code = 200
        post_response.json.return_value = {}
        
        mock_post.side_effect = [session_response, post_response]
        
        result = create_whitewind_blog_post("Test Post", "Test content")
        
        assert "Successfully created Whitewind blog post!" in result
        assert "Title: Test Post" in result
        assert "URL: URL generation failed" in result
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_without_handle(self, mock_post):
        """Test Whitewind blog post creation without handle in session."""
        # Mock session response without handle
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.return_value = {
            "accessJwt": "test_access_token",
            "did": "did:plc:test123"
        }
        
        # Mock post creation response
        post_response = MagicMock()
        post_response.status_code = 200
        post_response.json.return_value = {
            "uri": "at://did:plc:test123/com.whtwnd.blog.entry/test123"
        }
        
        mock_post.side_effect = [session_response, post_response]
        
        result = create_whitewind_blog_post("Test Post", "Test content")
        
        assert "Successfully created Whitewind blog post!" in result
        assert "URL: https://whtwnd.com/testuser/test123" in result
    
    def test_create_whitewind_blog_post_missing_username(self):
        """Test Whitewind blog post creation with missing username."""
        with patch.dict(os.environ, {
            'BSKY_PASSWORD': 'testpass',
            'PDS_URI': 'https://bsky.social'
        }, clear=True):
            with pytest.raises(Exception, match="BSKY_USERNAME and BSKY_PASSWORD environment variables must be set"):
                create_whitewind_blog_post("Test Post", "Test content")
    
    def test_create_whitewind_blog_post_missing_password(self):
        """Test Whitewind blog post creation with missing password."""
        with patch.dict(os.environ, {
            'BSKY_USERNAME': 'testuser',
            'PDS_URI': 'https://bsky.social'
        }, clear=True):
            with pytest.raises(Exception, match="BSKY_USERNAME and BSKY_PASSWORD environment variables must be set"):
                create_whitewind_blog_post("Test Post", "Test content")
    
    def test_create_whitewind_blog_post_missing_credentials(self):
        """Test Whitewind blog post creation with missing credentials."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception, match="BSKY_USERNAME and BSKY_PASSWORD environment variables must be set"):
                create_whitewind_blog_post("Test Post", "Test content")
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_session_error(self, mock_post):
        """Test Whitewind blog post creation with session error."""
        # Mock session response with error
        session_response = MagicMock()
        session_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        
        mock_post.return_value = session_response
        
        with pytest.raises(Exception, match="Error creating Whitewind blog post: 401 Unauthorized"):
            create_whitewind_blog_post("Test Post", "Test content")
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_session_missing_token(self, mock_post):
        """Test Whitewind blog post creation with missing access token."""
        # Mock session response without access token
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.return_value = {
            "did": "did:plc:test123",
            "handle": "testuser"
        }
        
        mock_post.return_value = session_response
        
        with pytest.raises(Exception, match="Failed to get access token or DID from session"):
            create_whitewind_blog_post("Test Post", "Test content")
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_session_missing_did(self, mock_post):
        """Test Whitewind blog post creation with missing DID."""
        # Mock session response without DID
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.return_value = {
            "accessJwt": "test_access_token",
            "handle": "testuser"
        }
        
        mock_post.return_value = session_response
        
        with pytest.raises(Exception, match="Failed to get access token or DID from session"):
            create_whitewind_blog_post("Test Post", "Test content")
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_creation_error(self, mock_post):
        """Test Whitewind blog post creation with post creation error."""
        # Mock session response
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.return_value = {
            "accessJwt": "test_access_token",
            "did": "did:plc:test123",
            "handle": "testuser"
        }
        
        # Mock post creation response with error
        post_response = MagicMock()
        post_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        
        mock_post.side_effect = [session_response, post_response]
        
        with pytest.raises(Exception, match="Error creating Whitewind blog post: 403 Forbidden"):
            create_whitewind_blog_post("Test Post", "Test content")
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_network_error(self, mock_post):
        """Test Whitewind blog post creation with network error."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        with pytest.raises(Exception, match="Error creating Whitewind blog post: Network error"):
            create_whitewind_blog_post("Test Post", "Test content")
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_timeout_error(self, mock_post):
        """Test Whitewind blog post creation with timeout error."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        with pytest.raises(Exception, match="Error creating Whitewind blog post: Request timeout"):
            create_whitewind_blog_post("Test Post", "Test content")
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_json_error(self, mock_post):
        """Test Whitewind blog post creation with JSON decode error."""
        # Mock session response
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.side_effect = ValueError("Invalid JSON")
        
        mock_post.return_value = session_response
        
        with pytest.raises(Exception, match="Error creating Whitewind blog post: Invalid JSON"):
            create_whitewind_blog_post("Test Post", "Test content")
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass'
        # No PDS_URI - should use default
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_default_pds(self, mock_post):
        """Test Whitewind blog post creation with default PDS URI."""
        # Mock session response
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.return_value = {
            "accessJwt": "test_access_token",
            "did": "did:plc:test123",
            "handle": "testuser"
        }
        
        # Mock post creation response
        post_response = MagicMock()
        post_response.status_code = 200
        post_response.json.return_value = {
            "uri": "at://did:plc:test123/com.whtwnd.blog.entry/test123"
        }
        
        mock_post.side_effect = [session_response, post_response]
        
        result = create_whitewind_blog_post("Test Post", "Test content")
        
        assert "Successfully created Whitewind blog post!" in result
        # Verify the default PDS URI was used
        session_call = mock_post.call_args_list[0]
        assert "https://bsky.social" in session_call[0][0]
    
    @patch.dict(os.environ, {
        'BSKY_USERNAME': 'testuser',
        'BSKY_PASSWORD': 'testpass',
        'PDS_URI': 'https://bsky.social'
    })
    @patch('requests.post')
    def test_create_whitewind_blog_post_request_parameters(self, mock_post):
        """Test Whitewind blog post creation request parameters."""
        # Mock session response
        session_response = MagicMock()
        session_response.status_code = 200
        session_response.json.return_value = {
            "accessJwt": "test_access_token",
            "did": "did:plc:test123",
            "handle": "testuser"
        }
        
        # Mock post creation response
        post_response = MagicMock()
        post_response.status_code = 200
        post_response.json.return_value = {
            "uri": "at://did:plc:test123/com.whtwnd.blog.entry/test123"
        }
        
        mock_post.side_effect = [session_response, post_response]
        
        create_whitewind_blog_post("Test Post", "Test content", "Test subtitle")
        
        # Verify session request
        session_call = mock_post.call_args_list[0]
        assert "com.atproto.server.createSession" in session_call[0][0]
        assert session_call[1]["json"]["identifier"] == "testuser"
        assert session_call[1]["json"]["password"] == "testpass"
        assert session_call[1]["timeout"] == 10
        
        # Verify post creation request
        post_call = mock_post.call_args_list[1]
        assert "com.atproto.repo.createRecord" in post_call[0][0]
        assert post_call[1]["headers"]["Authorization"] == "Bearer test_access_token"
        assert post_call[1]["json"]["repo"] == "did:plc:test123"
        assert post_call[1]["json"]["collection"] == "com.whtwnd.blog.entry"
        assert post_call[1]["json"]["record"]["title"] == "Test Post"
        assert post_call[1]["json"]["record"]["content"] == "Test content"
        assert post_call[1]["json"]["record"]["subtitle"] == "Test subtitle"
        assert post_call[1]["json"]["record"]["theme"] == "github-light"
        assert post_call[1]["json"]["record"]["visibility"] == "public"
        assert post_call[1]["timeout"] == 10


class TestWhitewindIntegration:
    """Integration tests for Whitewind functionality."""
    
    def test_whitewind_post_args_with_create_whitewind_blog_post(self):
        """Test using WhitewindPostArgs with create_whitewind_blog_post."""
        args = WhitewindPostArgs(
            title="Test Post",
            content="Test content",
            subtitle="Test subtitle"
        )
        
        with patch.dict(os.environ, {
            'BSKY_USERNAME': 'testuser',
            'BSKY_PASSWORD': 'testpass',
            'PDS_URI': 'https://bsky.social'
        }):
            with patch('requests.post') as mock_post:
                # Mock session response
                session_response = MagicMock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    "accessJwt": "test_access_token",
                    "did": "did:plc:test123",
                    "handle": "testuser"
                }
                
                # Mock post creation response
                post_response = MagicMock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    "uri": "at://did:plc:test123/com.whtwnd.blog.entry/test123"
                }
                
                mock_post.side_effect = [session_response, post_response]
                
                result = create_whitewind_blog_post(args.title, args.content, args.subtitle)
                
                assert "Successfully created Whitewind blog post!" in result
                assert "Title: Test Post" in result
                assert "Subtitle: Test subtitle" in result
    
    def test_whitewind_error_handling_flow(self):
        """Test complete error handling flow."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception, match="BSKY_USERNAME and BSKY_PASSWORD environment variables must be set"):
                create_whitewind_blog_post("Test Post", "Test content")
    
    def test_whitewind_success_flow(self):
        """Test complete success flow."""
        with patch.dict(os.environ, {
            'BSKY_USERNAME': 'testuser',
            'BSKY_PASSWORD': 'testpass',
            'PDS_URI': 'https://bsky.social'
        }):
            with patch('requests.post') as mock_post:
                # Mock session response
                session_response = MagicMock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    "accessJwt": "test_access_token",
                    "did": "did:plc:test123",
                    "handle": "testuser"
                }
                
                # Mock post creation response
                post_response = MagicMock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    "uri": "at://did:plc:test123/com.whtwnd.blog.entry/test123"
                }
                
                mock_post.side_effect = [session_response, post_response]
                
                result = create_whitewind_blog_post("Test Post", "Test content")
                
                assert "Successfully created Whitewind blog post!" in result
                assert "Title: Test Post" in result
                assert "URL: https://whtwnd.com/testuser/test123" in result
                assert "Theme: github-light" in result
                assert "Visibility: public" in result
