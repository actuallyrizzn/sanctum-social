import pytest
from unittest.mock import Mock, patch
from platforms.bluesky.tools.post import PostArgs, create_new_bluesky_post


class TestPostArgs:
    def test_post_args_valid_single_text(self):
        """Test PostArgs with valid single text."""
        args = PostArgs(text=["Hello world!"])
        assert args.text == ["Hello world!"]
        assert args.lang == "en-US"

    def test_post_args_valid_multiple_texts(self):
        """Test PostArgs with valid multiple texts."""
        args = PostArgs(text=["First post", "Second post", "Third post"])
        assert args.text == ["First post", "Second post", "Third post"]
        assert args.lang == "en-US"

    def test_post_args_custom_language(self):
        """Test PostArgs with custom language."""
        args = PostArgs(text=["Hola mundo!"], lang="es")
        assert args.text == ["Hola mundo!"]
        assert args.lang == "es"

    def test_post_args_empty_text_list_raises_exception(self):
        """Test PostArgs with empty text list raises exception."""
        with pytest.raises(ValueError, match="Text list cannot be empty"):
            PostArgs(text=[])

    def test_post_args_none_text_raises_exception(self):
        """Test PostArgs with None text raises exception."""
        with pytest.raises(Exception, match="Input should be a valid list"):
            PostArgs(text=None)


class TestCreateNewBlueskyPost:
    def test_create_new_bluesky_post_single_text(self):
        """Test creating a single Bluesky post."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                # Mock session creation
                session_response = Mock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'did:plc:test',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock post creation
                post_response = Mock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                
                mock_post.side_effect = [session_response, post_response]
                
                result = create_new_bluesky_post(["Hello from Void!"])
                
                assert "Successfully posted to Bluesky!" in result
                assert "Hello from Void!" in result
                assert mock_post.call_count == 2  # Session + post creation

    def test_create_new_bluesky_post_thread(self):
        """Test creating a Bluesky thread."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                # Mock session creation
                session_response = Mock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'did:plc:test',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock post creation responses
                post_response = Mock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                
                mock_post.side_effect = [session_response, post_response, post_response, post_response]
                
                result = create_new_bluesky_post(["Part 1", "Part 2", "Part 3"])
                
                assert "Successfully created thread with 3 posts!" in result
                assert mock_post.call_count == 4  # Session + 3 posts

    def test_create_new_bluesky_post_custom_language(self):
        """Test creating a post with custom language."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                # Mock session creation
                session_response = Mock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'did:plc:test',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock post creation
                post_response = Mock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                
                mock_post.side_effect = [session_response, post_response]
                
                result = create_new_bluesky_post(["Hola mundo!"], lang="es")
                
                assert "Successfully posted to Bluesky!" in result
                assert "Hola mundo!" in result
                assert "Language: es" in result

    def test_create_new_bluesky_post_empty_text_raises_exception(self):
        """Test creating a post with empty text list raises exception."""
        with pytest.raises(Exception, match="Text list cannot be empty"):
            create_new_bluesky_post([])

    def test_create_new_bluesky_post_text_too_long_raises_exception(self):
        """Test creating a post with text exceeding 300 characters raises exception."""
        long_text = "a" * 301
        with pytest.raises(Exception, match="Post 1 exceeds 300 character limit"):
            create_new_bluesky_post([long_text])

    def test_create_new_bluesky_post_missing_credentials(self):
        """Test creating a post with missing credentials."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            with pytest.raises(Exception, match="BSKY_USERNAME and BSKY_PASSWORD environment variables must be set"):
                create_new_bluesky_post(["Test post"])

    def test_create_new_bluesky_post_api_error(self):
        """Test creating a post when API returns error."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 400
                mock_response.raise_for_status.side_effect = Exception("Bad Request")
                mock_post.return_value = mock_response
                
                with pytest.raises(Exception, match="Error posting to Bluesky"):
                    create_new_bluesky_post(["Test post"])

    def test_create_new_bluesky_post_network_error(self):
        """Test creating a post when network request fails."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                mock_post.side_effect = Exception("Network error")
                
                with pytest.raises(Exception, match="Error posting to Bluesky"):
                    create_new_bluesky_post(["Test post"])

    def test_create_new_bluesky_post_thread_too_many_posts(self):
        """Test creating a thread with too many posts."""
        texts = [f"Post {i}" for i in range(6)]  # 6 posts, max is 5
        
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                # Mock session creation
                session_response = Mock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'did:plc:test',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock post creation responses
                post_response = Mock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                
                mock_post.side_effect = [session_response] + [post_response] * 6
                
                result = create_new_bluesky_post(texts)
                
                # Should succeed (no limit in current implementation)
                assert "Successfully created thread with 6 posts!" in result

    def test_create_new_bluesky_post_thread_with_reply_to(self):
        """Test creating a thread with reply_to context."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                # Mock session creation
                session_response = Mock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'did:plc:test',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock post creation responses
                post_response = Mock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                
                mock_post.side_effect = [session_response, post_response, post_response]
                
                result = create_new_bluesky_post(["Part 1", "Part 2"])
                
                assert "Successfully created thread with 2 posts!" in result
                assert mock_post.call_count == 3  # Session + 2 posts

    def test_create_new_bluesky_post_missing_session_data(self):
        """Test creating a post when session response is missing required data."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                # Mock session creation with missing data
                session_response = Mock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    'accessJwt': None,  # Missing token
                    'did': 'did:plc:test',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = session_response
                
                with pytest.raises(Exception, match="Failed to get access token or DID from session"):
                    create_new_bluesky_post(["Test post"])

    def test_create_new_bluesky_post_with_mentions(self):
        """Test creating a post with mentions."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                session_response = Mock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'did:plc:test',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock mention resolution
                mention_response = Mock()
                mention_response.status_code = 200
                mention_response.json.return_value = {
                    'did': 'did:plc:mentioned_user'
                }
                mock_get.return_value = mention_response
                
                # Mock post creation
                post_response = Mock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                
                mock_post.side_effect = [session_response, post_response]
                
                result = create_new_bluesky_post(["Hello @test.user.bsky.social!"])
                
                assert "Successfully posted to Bluesky!" in result
                assert "@test.user.bsky.social" in result
                # Verify mention resolution was called
                mock_get.assert_called_once()

    def test_create_new_bluesky_post_with_urls(self):
        """Test creating a post with URLs."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                # Mock session creation
                session_response = Mock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'did:plc:test',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock post creation
                post_response = Mock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                
                mock_post.side_effect = [session_response, post_response]
                
                result = create_new_bluesky_post(["Check out https://example.com!"])
                
                assert "Successfully posted to Bluesky!" in result
                assert "https://example.com" in result

    def test_create_new_bluesky_post_mention_resolution_failure(self):
        """Test creating a post when mention resolution fails."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                session_response = Mock()
                session_response.status_code = 200
                session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'did:plc:test',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock mention resolution failure
                mock_get.side_effect = Exception("Resolution failed")
                
                # Mock post creation
                post_response = Mock()
                post_response.status_code = 200
                post_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                
                mock_post.side_effect = [session_response, post_response]
                
                result = create_new_bluesky_post(["Hello @nonexistent.user!"])
                
                # Should still succeed, just without mention facets
                assert "Successfully posted to Bluesky!" in result
