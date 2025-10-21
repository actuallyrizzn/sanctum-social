import pytest
from unittest.mock import Mock, patch
from tools.post import PostArgs, create_new_bluesky_post


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
        with pytest.raises(ValueError, match="Text list cannot be empty"):
            PostArgs(text=None)


class TestCreateNewBlueskyPost:
    def test_create_new_bluesky_post_single_text(self):
        """Test creating a single Bluesky post."""
        with patch('tools.post.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BLUESKY_USERNAME': 'test.user.bsky.social',
                'BLUESKY_PASSWORD': 'test_password',
                'BLUESKY_SERVICE': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.post.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                mock_post.return_value = mock_response
                
                result = create_new_bluesky_post(["Hello from Void!"])
                
                assert "Post created successfully" in result
                assert "Hello from Void!" in result
                mock_post.assert_called_once()

    def test_create_new_bluesky_post_thread(self):
        """Test creating a Bluesky thread."""
        with patch('tools.post.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BLUESKY_USERNAME': 'test.user.bsky.social',
                'BLUESKY_PASSWORD': 'test_password',
                'BLUESKY_SERVICE': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.post.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                mock_post.return_value = mock_response
                
                result = create_new_bluesky_post(["Part 1", "Part 2", "Part 3"])
                
                assert "Thread created successfully" in result
                assert "3 posts" in result
                assert mock_post.call_count == 3  # One call per post

    def test_create_new_bluesky_post_custom_language(self):
        """Test creating a post with custom language."""
        with patch('tools.post.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BLUESKY_USERNAME': 'test.user.bsky.social',
                'BLUESKY_PASSWORD': 'test_password',
                'BLUESKY_SERVICE': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.post.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                mock_post.return_value = mock_response
                
                result = create_new_bluesky_post(["Hola mundo!"], lang="es")
                
                assert "Post created successfully" in result
                assert "Hola mundo!" in result
                # Verify language was passed in the request
                call_args = mock_post.call_args
                assert call_args[1]['json']['langs'] == ["es"]

    def test_create_new_bluesky_post_empty_text_raises_exception(self):
        """Test creating a post with empty text list raises exception."""
        with pytest.raises(Exception, match="Text list cannot be empty"):
            create_new_bluesky_post([])

    def test_create_new_bluesky_post_text_too_long_raises_exception(self):
        """Test creating a post with text exceeding 300 characters raises exception."""
        long_text = "a" * 301
        with pytest.raises(Exception, match="Text cannot be longer than 300 characters"):
            create_new_bluesky_post([long_text])

    def test_create_new_bluesky_post_missing_credentials(self):
        """Test creating a post with missing credentials."""
        with patch('tools.post.os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            result = create_new_bluesky_post(["Test post"])
            
            assert "Error: Missing Bluesky credentials" in result

    def test_create_new_bluesky_post_api_error(self):
        """Test creating a post when API returns error."""
        with patch('tools.post.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BLUESKY_USERNAME': 'test.user.bsky.social',
                'BLUESKY_PASSWORD': 'test_password',
                'BLUESKY_SERVICE': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.post.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 400
                mock_response.text = "Bad Request"
                mock_post.return_value = mock_response
                
                result = create_new_bluesky_post(["Test post"])
                
                assert "Error creating post" in result
                assert "400" in result

    def test_create_new_bluesky_post_network_error(self):
        """Test creating a post when network request fails."""
        with patch('tools.post.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BLUESKY_USERNAME': 'test.user.bsky.social',
                'BLUESKY_PASSWORD': 'test_password',
                'BLUESKY_SERVICE': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.post.requests.post') as mock_post:
                mock_post.side_effect = Exception("Network error")
                
                result = create_new_bluesky_post(["Test post"])
                
                assert "Error creating post" in result
                assert "Network error" in result

    def test_create_new_bluesky_post_thread_too_many_posts(self):
        """Test creating a thread with too many posts."""
        texts = [f"Post {i}" for i in range(6)]  # 6 posts, max is 5
        
        with patch('tools.post.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BLUESKY_USERNAME': 'test.user.bsky.social',
                'BLUESKY_PASSWORD': 'test_password',
                'BLUESKY_SERVICE': 'https://bsky.social'
            }.get(key, default)
            
            with pytest.raises(Exception, match="Cannot create more than 5 posts in a thread"):
                create_new_bluesky_post(texts)

    def test_create_new_bluesky_post_thread_with_reply_to(self):
        """Test creating a thread with reply_to context."""
        with patch('tools.post.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BLUESKY_USERNAME': 'test.user.bsky.social',
                'BLUESKY_PASSWORD': 'test_password',
                'BLUESKY_SERVICE': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.post.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'uri': 'at://did:plc:test/app.bsky.feed.post/test',
                    'cid': 'test_cid'
                }
                mock_post.return_value = mock_response
                
                result = create_new_bluesky_post(["Part 1", "Part 2"])
                
                assert "Thread created successfully" in result
                # Verify that subsequent posts have reply_to context
                assert mock_post.call_count == 2
                
                # Check that second call has reply_to
                second_call = mock_post.call_args_list[1]
                assert 'reply' in second_call[1]['json']
