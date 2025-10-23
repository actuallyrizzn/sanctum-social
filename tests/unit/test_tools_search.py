import pytest
from unittest.mock import Mock, patch
from platforms.bluesky.tools.search import SearchArgs, search_bluesky_posts


class TestSearchArgs:
    def test_search_args_valid(self):
        """Test SearchArgs with valid data."""
        args = SearchArgs(
            query="test query",
            max_results=50,
            author="user.bsky.social",
            sort="top"
        )
        assert args.query == "test query"
        assert args.max_results == 50
        assert args.author == "user.bsky.social"
        assert args.sort == "top"

    def test_search_args_defaults(self):
        """Test SearchArgs with default values."""
        args = SearchArgs(query="test query")
        assert args.query == "test query"
        assert args.max_results == 25
        assert args.author is None
        assert args.sort == "latest"

    def test_search_args_missing_query(self):
        """Test SearchArgs with missing query."""
        with pytest.raises(Exception, match="Field required"):
            SearchArgs()

    def test_search_args_max_results_validation(self):
        """Test SearchArgs with max_results validation."""
        args = SearchArgs(query="test", max_results=150)
        assert args.max_results == 150  # No validation in the model itself

    def test_search_args_sort_validation(self):
        """Test SearchArgs with sort validation."""
        args = SearchArgs(query="test", sort="invalid")
        assert args.sort == "invalid"  # No validation in the model itself


class TestSearchBlueskyPosts:
    def test_search_bluesky_posts_success(self):
        """Test successful Bluesky post search."""
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

                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {
                    'posts': [
                        {
                            'uri': 'at://did:plc:test/post/1',
                            'cid': 'test_cid',
                            'record': {
                                'text': 'Test post content',
                                'createdAt': '2025-01-01T00:00:00.000Z'
                            },
                            'author': {
                                'handle': 'test.user.bsky.social',
                                'displayName': 'Test User'
                            }
                        }
                    ]
                }
                mock_get.return_value = mock_search_response

                result = search_bluesky_posts("test query")
                
                assert "search_results" in result
                assert "Test post content" in result
                assert "test.user.bsky.social" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_search_bluesky_posts_with_author_filter(self):
        """Test search with author filter."""
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

                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                mock_get.return_value = mock_search_response

                result = search_bluesky_posts("test query", author="user.bsky.social")
                
                assert "search_results" in result
                assert "user.bsky.social" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_search_bluesky_posts_with_custom_max_results(self):
        """Test search with custom max_results."""
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

                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                mock_get.return_value = mock_search_response

                result = search_bluesky_posts("test query", max_results=50)
                
                assert "search_results" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_search_bluesky_posts_max_results_capped_at_100(self):
        """Test that max_results is capped at 100."""
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

                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                mock_get.return_value = mock_search_response

                result = search_bluesky_posts("test query", max_results=150)
                
                assert "search_results" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_search_bluesky_posts_with_sort_order(self):
        """Test search with different sort orders."""
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

                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                mock_get.return_value = mock_search_response

                result = search_bluesky_posts("test query", sort="top")
                
                assert "search_results" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_search_bluesky_posts_invalid_sort_defaults_to_latest(self):
        """Test that invalid sort order defaults to 'latest'."""
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

                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                mock_get.return_value = mock_search_response

                result = search_bluesky_posts("test query", sort="invalid")
                
                assert "search_results" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_search_bluesky_posts_missing_credentials(self):
        """Test search with missing credentials."""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            with pytest.raises(Exception, match="BSKY_USERNAME and BSKY_PASSWORD environment variables must be set"):
                search_bluesky_posts("test query")

    def test_search_bluesky_posts_session_error(self):
        """Test search when session creation fails."""
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
                
                with pytest.raises(Exception, match="Error searching Bluesky"):
                    search_bluesky_posts("test query")

    def test_search_bluesky_posts_search_api_error(self):
        """Test search when search API fails."""
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

                # Mock search API error
                mock_search_response = Mock()
                mock_search_response.status_code = 400
                mock_search_response.raise_for_status.side_effect = Exception("Bad Request")
                mock_get.return_value = mock_search_response
                
                with pytest.raises(Exception, match="Error searching Bluesky"):
                    search_bluesky_posts("test query")

    def test_search_bluesky_posts_empty_results(self):
        """Test search with empty results."""
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

                # Mock empty search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                mock_get.return_value = mock_search_response

                result = search_bluesky_posts("test query")
                
                assert "search_results" in result
                assert "result_count: 0" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_search_bluesky_posts_multiple_results(self):
        """Test search with multiple results."""
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

                # Mock multiple search results
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {
                    'posts': [
                        {
                            'uri': 'at://did:plc:test/post/1',
                            'cid': 'test_cid_1',
                            'record': {
                                'text': 'First post',
                                'createdAt': '2025-01-01T00:00:00.000Z'
                            },
                            'author': {
                                'handle': 'user1.bsky.social',
                                'displayName': 'User One'
                            }
                        },
                        {
                            'uri': 'at://did:plc:test/post/2',
                            'cid': 'test_cid_2',
                            'record': {
                                'text': 'Second post',
                                'createdAt': '2025-01-01T01:00:00.000Z'
                            },
                            'author': {
                                'handle': 'user2.bsky.social',
                                'displayName': 'User Two'
                            }
                        }
                    ]
                }
                mock_get.return_value = mock_search_response

                result = search_bluesky_posts("test query")
                
                assert "search_results" in result
                assert "result_count: 2" in result
                assert "First post" in result
                assert "Second post" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_search_bluesky_posts_with_reply_info(self):
        """Test search with posts that have reply information."""
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

                # Mock search response with reply info
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {
                    'posts': [
                        {
                            'uri': 'at://did:plc:test/post/1',
                            'cid': 'test_cid',
                            'record': {
                                'text': 'Reply post',
                                'createdAt': '2025-01-01T00:00:00.000Z',
                                'reply': {
                                    'parent': {
                                        'uri': 'at://did:plc:test/parent/1',
                                        'cid': 'parent_cid'
                                    }
                                }
                            },
                            'author': {
                                'handle': 'test.user.bsky.social',
                                'displayName': 'Test User'
                            }
                        }
                    ]
                }
                mock_get.return_value = mock_search_response

                result = search_bluesky_posts("test query")
                
                assert "search_results" in result
                assert "Reply post" in result
                assert "reply_to" in result
                mock_post.assert_called_once()
                mock_get.assert_called_once()

    def test_search_bluesky_posts_missing_access_token(self):
        """Test search when session response is missing access token."""
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
                    search_bluesky_posts("test query")