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
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

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
                                },
                                'likeCount': 5,
                                'repostCount': 2,
                                'replyCount': 1
                            }
                        }
                    ]
                }
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("home")
                
                assert "feed:" in result
                assert "Home timeline post" in result
                assert "test.user.bsky.social" in result
                assert "type: home" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_discover_feed(self):
        """Test getting discover feed."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

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
                                },
                                'likeCount': 10,
                                'repostCount': 5,
                                'replyCount': 3
                            }
                        }
                    ]
                }
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("discover")
                
                assert "feed:" in result
                assert "Discover feed post" in result
                assert "popular.user.bsky.social" in result
                assert "type: custom" in result
                assert "name: discover" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_ai_feed(self):
        """Test getting AI for grownups feed."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("ai-for-grownups")
                
                assert "feed:" in result
                assert "type: custom" in result
                assert "name: ai-for-grownups" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_atmosphere_feed(self):
        """Test getting atmosphere feed."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("atmosphere")
                
                assert "feed:" in result
                assert "type: custom" in result
                assert "name: atmosphere" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_void_cafe_feed(self):
        """Test getting void cafe feed."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("void-cafe")
                
                assert "feed:" in result
                assert "type: custom" in result
                assert "name: void-cafe" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_with_feedname_prefix(self):
        """Test getting feed with FeedName prefix."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("FeedName.discover")
                
                assert "feed:" in result
                assert "type: custom" in result
                assert "name: discover" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_invalid_feed_name(self):
        """Test getting feed with invalid feed name."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with pytest.raises(Exception, match="Invalid feed name 'invalid-feed'"):
                get_bluesky_feed("invalid-feed")

    def test_get_bluesky_feed_max_posts_capped_at_100(self):
        """Test that max_posts is capped at 100."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("home", max_posts=150)
                
                assert "feed:" in result
                # Verify that the limit is capped at 100
                feed_call = mock_get.call_args
                feed_params = feed_call[1]['params']
                assert feed_params['limit'] == 100
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_missing_credentials(self):
        """Test getting feed with missing credentials."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            with pytest.raises(Exception, match="BSKY_USERNAME and BSKY_PASSWORD environment variables must be set"):
                get_bluesky_feed("home")

    def test_get_bluesky_feed_session_error(self):
        """Test getting feed when session creation fails."""
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
                
                with pytest.raises(Exception, match="Authentication failed"):
                    get_bluesky_feed("home")

    def test_get_bluesky_feed_missing_access_token(self):
        """Test getting feed when session response is missing access token."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post:
                # Mock session creation without accessJwt
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                    # Missing 'accessJwt'
                }
                mock_post.return_value = mock_session_response
                
                with pytest.raises(Exception, match="Failed to get access token from session"):
                    get_bluesky_feed("home")

    def test_get_bluesky_feed_api_error(self):
        """Test getting feed when API fails."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock successful session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock failed feed request
                mock_feed_response = Mock()
                mock_feed_response.status_code = 400
                mock_feed_response.raise_for_status.side_effect = Exception("Bad Request")
                mock_get.return_value = mock_feed_response
                
                with pytest.raises(Exception, match="Failed to get feed"):
                    get_bluesky_feed("home")

    def test_get_bluesky_feed_empty_results(self):
        """Test getting feed with empty results."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock empty feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("home")
                
                assert "feed:" in result
                assert "post_count: 0" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_default_no_feed_name(self):
        """Test getting feed with no feed name (defaults to home)."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock feed response
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {'feed': []}
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed()
                
                assert "feed:" in result
                assert "type: home" in result
                assert "name: home" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_with_repost_info(self):
        """Test getting feed with repost information."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock feed response with repost info
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {
                    'feed': [
                        {
                            'post': {
                                'uri': 'at://did:plc:test/post/1',
                                'cid': 'test_cid',
                                'record': {
                                    'text': 'Reposted content',
                                    'createdAt': '2025-01-01T00:00:00.000Z'
                                },
                                'author': {
                                    'handle': 'original.user.bsky.social',
                                    'displayName': 'Original User'
                                },
                                'likeCount': 5,
                                'repostCount': 2,
                                'replyCount': 1
                            },
                            'reason': {
                                '$type': 'app.bsky.feed.defs#reasonRepost',
                                'by': {
                                    'handle': 'reposter.user.bsky.social',
                                    'displayName': 'Reposter User'
                                }
                            }
                        }
                    ]
                }
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("home")
                
                assert "feed:" in result
                assert "Reposted content" in result
                assert "reposted_by:" in result
                assert "reposter.user.bsky.social" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_with_reply_info(self):
        """Test getting feed with reply information."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock feed response with reply info
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {
                    'feed': [
                        {
                            'post': {
                                'uri': 'at://did:plc:test/post/1',
                                'cid': 'test_cid',
                                'record': {
                                    'text': 'Reply content',
                                    'createdAt': '2025-01-01T00:00:00.000Z',
                                    'reply': {
                                        'parent': {
                                            'uri': 'at://did:plc:test/parent/1',
                                            'cid': 'parent_cid'
                                        }
                                    }
                                },
                                'author': {
                                    'handle': 'replier.user.bsky.social',
                                    'displayName': 'Replier User'
                                },
                                'likeCount': 3,
                                'repostCount': 1,
                                'replyCount': 0
                            }
                        }
                    ]
                }
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("home")
                
                assert "feed:" in result
                assert "Reply content" in result
                assert "reply_to:" in result
                assert "at://did:plc:test/parent/1" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_get_bluesky_feed_multiple_posts(self):
        """Test getting feed with multiple posts."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get:
                
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                mock_post.return_value = mock_session_response

                # Mock feed response with multiple posts
                mock_feed_response = Mock()
                mock_feed_response.status_code = 200
                mock_feed_response.json.return_value = {
                    'feed': [
                        {
                            'post': {
                                'uri': 'at://did:plc:test/post/1',
                                'cid': 'test_cid_1',
                                'record': {
                                    'text': 'First post',
                                    'createdAt': '2025-01-01T00:00:00.000Z'
                                },
                                'author': {
                                    'handle': 'user1.bsky.social',
                                    'displayName': 'User One'
                                },
                                'likeCount': 5,
                                'repostCount': 2,
                                'replyCount': 1
                            }
                        },
                        {
                            'post': {
                                'uri': 'at://did:plc:test/post/2',
                                'cid': 'test_cid_2',
                                'record': {
                                    'text': 'Second post',
                                    'createdAt': '2025-01-01T01:00:00.000Z'
                                },
                                'author': {
                                    'handle': 'user2.bsky.social',
                                    'displayName': 'User Two'
                                },
                                'likeCount': 10,
                                'repostCount': 5,
                                'replyCount': 3
                            }
                        }
                    ]
                }
                mock_get.return_value = mock_feed_response

                result = get_bluesky_feed("home")
                
                assert "feed:" in result
                assert "post_count: 2" in result
                assert "First post" in result
                assert "Second post" in result
                assert "user1.bsky.social" in result
                assert "user2.bsky.social" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()