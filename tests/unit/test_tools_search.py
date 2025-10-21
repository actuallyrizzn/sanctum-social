import pytest
from unittest.mock import Mock, patch
from tools.search import SearchArgs, search_bluesky_posts


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
        with pytest.raises(ValueError, match="Field required"):
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
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
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
                
                mock_post.side_effect = [mock_session_response, mock_search_response]
                
                result = search_bluesky_posts("test query")
                
                assert "Search Results" in result
                assert "Test post content" in result
                assert "test.user.bsky.social" in result
                assert mock_post.call_count == 2

    def test_search_bluesky_posts_with_author_filter(self):
        """Test search with author filter."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                
                mock_post.side_effect = [mock_session_response, mock_search_response]
                
                result = search_bluesky_posts("test query", author="specific.user.bsky.social")
                
                assert "Search Results" in result
                # Verify that the search query includes the author filter
                search_call = mock_post.call_args_list[1]
                search_params = search_call[1]['params']
                assert 'from:specific.user.bsky.social test query' in search_params['q']

    def test_search_bluesky_posts_with_custom_max_results(self):
        """Test search with custom max_results."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                
                mock_post.side_effect = [mock_session_response, mock_search_response]
                
                result = search_bluesky_posts("test query", max_results=50)
                
                assert "Search Results" in result
                # Verify that the search params include the correct limit
                search_call = mock_post.call_args_list[1]
                search_params = search_call[1]['params']
                assert search_params['limit'] == 50

    def test_search_bluesky_posts_max_results_capped_at_100(self):
        """Test that max_results is capped at 100."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                
                mock_post.side_effect = [mock_session_response, mock_search_response]
                
                result = search_bluesky_posts("test query", max_results=150)
                
                assert "Search Results" in result
                # Verify that the search params are capped at 100
                search_call = mock_post.call_args_list[1]
                search_params = search_call[1]['params']
                assert search_params['limit'] == 100

    def test_search_bluesky_posts_with_sort_order(self):
        """Test search with different sort orders."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                
                mock_post.side_effect = [mock_session_response, mock_search_response]
                
                result = search_bluesky_posts("test query", sort="top")
                
                assert "Search Results" in result
                # Verify that the search params include the correct sort
                search_call = mock_post.call_args_list[1]
                search_params = search_call[1]['params']
                assert search_params['sort'] == 'top'

    def test_search_bluesky_posts_invalid_sort_defaults_to_latest(self):
        """Test that invalid sort order defaults to 'latest'."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                
                mock_post.side_effect = [mock_session_response, mock_search_response]
                
                result = search_bluesky_posts("test query", sort="invalid")
                
                assert "Search Results" in result
                # Verify that the search params default to 'latest'
                search_call = mock_post.call_args_list[1]
                search_params = search_call[1]['params']
                assert search_params['sort'] == 'latest'

    def test_search_bluesky_posts_missing_credentials(self):
        """Test search with missing credentials."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            result = search_bluesky_posts("test query")
            
            assert "Error: Missing Bluesky credentials" in result

    def test_search_bluesky_posts_session_error(self):
        """Test search when session creation fails."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                mock_post.side_effect = Exception("Session error")
                
                result = search_bluesky_posts("test query")
                
                assert "Error searching Bluesky" in result
                assert "Session error" in result

    def test_search_bluesky_posts_search_api_error(self):
        """Test search when search API fails."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                # Mock successful session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock failed search
                mock_search_response = Mock()
                mock_search_response.status_code = 400
                mock_search_response.text = "Bad Request"
                
                mock_post.side_effect = [mock_session_response, mock_search_response]
                
                result = search_bluesky_posts("test query")
                
                assert "Error searching Bluesky" in result
                assert "400" in result

    def test_search_bluesky_posts_empty_results(self):
        """Test search with empty results."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock empty search response
                mock_search_response = Mock()
                mock_search_response.status_code = 200
                mock_search_response.json.return_value = {'posts': []}
                
                mock_post.side_effect = [mock_session_response, mock_search_response]
                
                result = search_bluesky_posts("nonexistent query")
                
                assert "Search Results" in result
                assert "No posts found" in result

    def test_search_bluesky_posts_multiple_results(self):
        """Test search with multiple results."""
        with patch('tools.search.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'BSKY_USERNAME': 'test.user.bsky.social',
                'BSKY_PASSWORD': 'test_password',
                'PDS_URI': 'https://bsky.social'
            }.get(key, default)
            
            with patch('tools.search.requests.post') as mock_post:
                # Mock session creation
                mock_session_response = Mock()
                mock_session_response.status_code = 200
                mock_session_response.json.return_value = {
                    'accessJwt': 'test_token',
                    'did': 'test_did',
                    'handle': 'test.user.bsky.social'
                }
                
                # Mock search response with multiple posts
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
                
                mock_post.side_effect = [mock_session_response, mock_search_response]
                
                result = search_bluesky_posts("test query")
                
                assert "Search Results" in result
                assert "First post" in result
                assert "Second post" in result
                assert "user1.bsky.social" in result
                assert "user2.bsky.social" in result
