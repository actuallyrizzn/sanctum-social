import pytest
from unittest.mock import Mock, patch
from tools.feed import FeedArgs, get_bluesky_feed


class TestFeedArgs:
    def test_feed_args_valid(self):
        """Test FeedArgs with valid data."""
        args = FeedArgs(
            feed_name="discover",
            max_posts=50
        )
        assert args.feed_name == "discover"
        assert args.max_posts == 50

    def test_feed_args_defaults(self):
        """Test FeedArgs with default values."""
        args = FeedArgs()
        assert args.feed_name is None
        assert args.max_posts == 25

    def test_feed_args_home_feed(self):
        """Test FeedArgs with home feed."""
        args = FeedArgs(feed_name="home")
        assert args.feed_name == "home"
        assert args.max_posts == 25

    def test_feed_args_ai_feed(self):
        """Test FeedArgs with AI feed."""
        args = FeedArgs(feed_name="ai-for-grownups", max_posts=10)
        assert args.feed_name == "ai-for-grownups"
        assert args.max_posts == 10


class TestGetBlueskyFeed:
    def test_get_bluesky_feed_home_timeline(self):
        """Test getting home timeline feed."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {
                    'feed': [
                        {
                            'post': {
                                'uri': 'at://did:plc:test/post/1',
                                'cid': 'test_cid',
                                'record': {
                                    'text': 'Home timeline post',
                                    'createdAt': '2025-01-01T00:00:00.000Z'
                                },
                                'author': {
                                    'handle': 'test.user.bsky.social',
                                    'displayName': 'Test User'
                                }
                            }
                        }
                    ]
                }
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed("home")
                
                assert "Feed Results" in result
                assert "Home timeline post" in result
                assert "test.user.bsky.social" in result
                assert mock_post.call_count == 2

    def test_get_bluesky_feed_discover_feed(self):
        """Test getting discover feed."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {
                    'feed': [
                        {
                            'post': {
                                'uri': 'at://did:plc:test/post/1',
                                'cid': 'test_cid',
                                'record': {
                                    'text': 'Discover feed post',
                                    'createdAt': '2025-01-01T00:00:00.000Z'
                                },
                                'author': {
                                    'handle': 'popular.user.bsky.social',
                                    'displayName': 'Popular User'
                                }
                            }
                        }
                    ]
                }
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed("discover")
                
                assert "Feed Results" in result
                assert "Discover feed post" in result
                assert "popular.user.bsky.social" in result
                # Verify that the correct feed URI was used
                feed_call = mock_post.call_args_list[1]
                feed_params = feed_call[1]['params']
                assert 'at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.generator/whats-hot' in feed_params['feed']

    def test_get_bluesky_feed_ai_feed(self):
        """Test getting AI for grownups feed."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed("ai-for-grownups")
                
                assert "Feed Results" in result
                # Verify that the correct feed URI was used
                feed_call = mock_post.call_args_list[1]
                feed_params = feed_call[1]['params']
                assert 'at://did:plc:gfrmhdmjvxn2sjedzboeudef/app.bsky.feed.generator/ai-for-grownups' in feed_params['feed']

    def test_get_bluesky_feed_atmosphere_feed(self):
        """Test getting atmosphere feed."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed("atmosphere")
                
                assert "Feed Results" in result
                # Verify that the correct feed URI was used
                feed_call = mock_post.call_args_list[1]
                feed_params = feed_call[1]['params']
                assert 'at://did:plc:gfrmhdmjvxn2sjedzboeudef/app.bsky.feed.generator/the-atmosphere' in feed_params['feed']

    def test_get_bluesky_feed_void_cafe_feed(self):
        """Test getting void cafe feed."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed("void-cafe")
                
                assert "Feed Results" in result
                # Verify that the correct feed URI was used
                feed_call = mock_post.call_args_list[1]
                feed_params = feed_call[1]['params']
                assert 'at://did:plc:gfrmhdmjvxn2sjedzboeudef/app.bsky.feed.generator/void-cafe' in feed_params['feed']

    def test_get_bluesky_feed_with_feedname_prefix(self):
        """Test getting feed with FeedName prefix."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed("FeedName.discover")
                
                assert "Feed Results" in result
                # Verify that the FeedName prefix was stripped
                feed_call = mock_post.call_args_list[1]
                feed_params = feed_call[1]['params']
                assert 'at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.generator/whats-hot' in feed_params['feed']

    def test_get_bluesky_feed_invalid_feed_name(self):
        """Test getting feed with invalid feed name."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            result = get_bluesky_feed("invalid-feed")
            
            assert "Error: Invalid feed name" in result
            assert "invalid-feed" in result
            assert "Available feeds:" in result

    def test_get_bluesky_feed_max_posts_capped_at_100(self):
        """Test that max_posts is capped at 100."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed("home", max_posts=150)
                
                assert "Feed Results" in result
                # Verify that the limit is capped at 100
                feed_call = mock_post.call_args_list[1]
                feed_params = feed_call[1]['params']
                assert feed_params['limit'] == 100

    def test_get_bluesky_feed_missing_credentials(self):
        """Test getting feed with missing credentials."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            result = get_bluesky_feed("home")
            
            assert "Error: Missing Bluesky credentials" in result

    def test_get_bluesky_feed_session_error(self):
        """Test getting feed when session creation fails."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                mock_post.side_effect = Exception("Session error")
                
                result = get_bluesky_feed("home")
                
                assert "Error retrieving Bluesky feed" in result
                assert "Session error" in result

    def test_get_bluesky_feed_api_error(self):
        """Test getting feed when API fails."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock successful session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock failed feed request
                mock_feed_response = Mock()
                mock_feed_response.status_code = 400
                mock_feed_response.text = "Bad Request"
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed("home")
                
                assert "Error retrieving Bluesky feed" in result
                assert "400" in result

    def test_get_bluesky_feed_empty_results(self):
        """Test getting feed with empty results."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock empty feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed("home")
                
                assert "Feed Results" in result
                assert "No posts found" in result

    def test_get_bluesky_feed_default_no_feed_name(self):
        """Test getting feed with no feed name (defaults to home)."""
        with patch('tools.feed.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.feed.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                
                mock_post.side_effect = [mock_session_response, mock_feed_response]
                
                result = get_bluesky_feed()
                
                assert "Feed Results" in result
                # Verify that home timeline was requested (no feed parameter)
                feed_call = mock_post.call_args_list[1]
                feed_params = feed_call[1]['params']
                assert 'feed' not in feed_params or feed_params['feed'] is None
