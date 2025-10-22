"""
Integration tests for tool system
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os

from tools.blocks import attach_user_blocks, detach_user_blocks
from tools.reply import bluesky_reply
from tools.post import create_new_bluesky_post
from tools.search import search_bluesky_posts


@pytest.mark.live
@pytest.mark.integration
class TestToolIntegration:
    """Integration tests for tool system."""
    
    def test_attach_user_blocks_integration(self, mock_letta_client):
        """Test attaching user blocks with real tool integration."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock block creation
        mock_block = Mock()
        mock_block.id = "test-block-id"
        mock_block.label = "user_test.user.bsky.social"
        mock_letta_client.blocks.create.return_value = mock_block
        mock_letta_client.blocks.list.return_value = []
        
        # Mock block attachment
        mock_letta_client.agents.blocks.attach.return_value = Mock()
        
        # Test attaching user blocks
        handles = ["test.user.bsky.social"]
        result = attach_user_blocks(handles, mock_agent_state)
        
        # Verify block was created
        mock_letta_client.blocks.create.assert_called_once()
        
        # Verify block was attached
        mock_letta_client.agents.blocks.attach.assert_called_once_with(
            agent_id="test-agent-id",
            block_id="test-block-id"
        )
        
        # Verify result message
        assert "test.user.bsky.social" in result
        assert "attached" in result.lower()
    
    def test_detach_user_blocks_integration(self, mock_letta_client):
        """Test detaching user blocks with real tool integration."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock existing block
        mock_block = Mock()
        mock_block.id = "test-block-id"
        mock_block.label = "user_test.user.bsky.social"
        mock_letta_client.blocks.list.return_value = [mock_block]
        
        # Mock block detachment
        mock_letta_client.agents.blocks.detach.return_value = Mock()
        
        # Test detaching user blocks
        handles = ["test.user.bsky.social"]
        result = detach_user_blocks(handles, mock_agent_state)
        
        # Verify block was detached
        mock_letta_client.agents.blocks.detach.assert_called_once_with(
            agent_id="test-agent-id",
            block_id="test-block-id"
        )
        
        # Verify result message
        assert "test.user.bsky.social" in result
        assert "detached" in result.lower()
    
    def test_bluesky_reply_tool_integration(self):
        """Test Bluesky reply tool integration."""
        # Test single reply
        messages = ["Hello, this is a test reply!"]
        result = bluesky_reply(messages)
        
        assert "queued" in result.lower()
        assert "bluesky" in result.lower()
        assert "reply" in result.lower()
        
        # Test threaded reply
        messages = [
            "First reply",
            "Second reply",
            "Third reply"
        ]
        result = bluesky_reply(messages)
        
        assert "queued" in result.lower()
        assert len(messages) == 3
    
    def test_create_new_bluesky_post_integration(self):
        """Test creating new Bluesky post tool integration."""
        # Test valid post
        text = "This is a test post for Bluesky!"
        result = create_new_bluesky_post(text)
        
        assert "queued" in result.lower()
        assert "bluesky" in result.lower()
        assert "post" in result.lower()
        
        # Test post with language
        result = create_new_bluesky_post(text, language="en-US")
        assert "queued" in result.lower()
    
    def test_search_bluesky_posts_integration(self):
        """Test searching Bluesky posts tool integration."""
        # Test basic search
        query = "test search"
        result = search_bluesky_posts(query)
        
        assert "search" in result.lower()
        assert "bluesky" in result.lower()
        
        # Test search with limit
        result = search_bluesky_posts(query, limit=10)
        assert "search" in result.lower()


@pytest.mark.live
@pytest.mark.integration
class TestToolErrorHandling:
    """Test error handling in tool system."""
    
    def test_attach_user_blocks_error_handling(self, mock_letta_client):
        """Test error handling in attach_user_blocks."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock API error
        mock_letta_client.blocks.create.side_effect = Exception("API Error")
        
        # Test error handling
        handles = ["test.user.bsky.social"]
        result = attach_user_blocks(handles, mock_agent_state)
        
        # Should return error message, not raise exception
        assert "error" in result.lower() or "failed" in result.lower()
    
    def test_bluesky_reply_validation(self):
        """Test validation in Bluesky reply tool."""
        # Test empty messages
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            bluesky_reply([])
        
        # Test too many messages
        messages = ["msg1", "msg2", "msg3", "msg4", "msg5"]
        with pytest.raises(ValueError, match="Cannot send more than 4 reply messages"):
            bluesky_reply(messages)
        
        # Test message too long
        long_message = "x" * 301
        with pytest.raises(ValueError, match="cannot be longer than 300 characters"):
            bluesky_reply([long_message])
    
    def test_create_post_validation(self):
        """Test validation in create post tool."""
        # Test empty text
        with pytest.raises(ValueError, match="Text cannot be empty"):
            create_new_bluesky_post("")
        
        # Test text too long
        long_text = "x" * 301
        with pytest.raises(ValueError, match="exceeds 300 character limit"):
            create_new_bluesky_post(long_text)


@pytest.mark.live
@pytest.mark.integration
class TestToolWithMockedAPIs:
    """Test tools with mocked external APIs."""
    
    @patch('tools.search.requests.get')
    def test_search_bluesky_posts_with_mock_api(self, mock_get):
        """Test search tool with mocked API response."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "posts": [
                {
                    "uri": "at://did:plc:test/app.bsky.feed.post/test1",
                    "record": {
                        "text": "Test post 1"
                    },
                    "author": {
                        "handle": "test1.bsky.social"
                    }
                },
                {
                    "uri": "at://did:plc:test/app.bsky.feed.post/test2",
                    "record": {
                        "text": "Test post 2"
                    },
                    "author": {
                        "handle": "test2.bsky.social"
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Test search
        result = search_bluesky_posts("test query")
        
        # Verify API was called
        mock_get.assert_called_once()
        
        # Verify result contains search information
        assert "search" in result.lower()
        assert "bluesky" in result.lower()
    
    @patch('tools.search.requests.get')
    def test_search_bluesky_posts_api_error(self, mock_get):
        """Test search tool with API error."""
        # Mock API error
        mock_get.side_effect = Exception("API Error")
        
        # Test error handling
        result = search_bluesky_posts("test query")
        
        # Should return error message, not raise exception
        assert "error" in result.lower() or "failed" in result.lower()


@pytest.mark.live
@pytest.mark.integration
class TestToolConfiguration:
    """Test tool configuration and setup."""
    
    def test_tool_client_creation(self):
        """Test that tools can create their own clients."""
        # Test that tools can import and create clients
        from tools.blocks import get_letta_client
        
        # Should not raise import error
        assert callable(get_letta_client)
    
    def test_tool_environment_fallback(self):
        """Test that tools fall back to environment variables."""
        with patch.dict(os.environ, {"LETTA_API_KEY": "test-key"}):
            from tools.blocks import get_letta_client
            
            # Should be able to create client with env var
            client = get_letta_client()
            assert client is not None
    
    def test_tool_configuration_loading(self, mock_config_file):
        """Test that tools can load configuration."""
        with patch('tools.blocks.get_letta_config') as mock_config:
            mock_config.return_value = {
                "api_key": "test-key",
                "timeout": 30
            }
            
            from tools.blocks import get_letta_client
            
            # Should be able to create client with config
            client = get_letta_client()
            assert client is not None


@pytest.mark.live
@pytest.mark.integration
class TestToolDataFlow:
    """Test data flow through tool system."""
    
    def test_tool_input_validation(self):
        """Test that tools validate their inputs properly."""
        # Test reply tool input validation
        with pytest.raises(ValueError):
            bluesky_reply([])  # Empty list
        
        with pytest.raises(ValueError):
            bluesky_reply(["x" * 301])  # Too long
        
        # Test post tool input validation
        with pytest.raises(ValueError):
            create_new_bluesky_post("")  # Empty text
        
        with pytest.raises(ValueError):
            create_new_bluesky_post("x" * 301)  # Too long
    
    def test_tool_output_format(self):
        """Test that tools return properly formatted output."""
        # Test reply tool output
        result = bluesky_reply(["Test reply"])
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Test post tool output
        result = create_new_bluesky_post("Test post")
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Test search tool output
        result = search_bluesky_posts("test")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_tool_error_propagation(self):
        """Test that tool errors are properly handled."""
        # Test that validation errors are raised
        with pytest.raises(ValueError):
            bluesky_reply([])
        
        # Test that API errors are caught and returned as strings
        with patch('tools.search.requests.get') as mock_get:
            mock_get.side_effect = Exception("API Error")
            result = search_bluesky_posts("test")
            assert isinstance(result, str)
            assert "error" in result.lower() or "failed" in result.lower()


@pytest.mark.parametrize("tool_name,tool_function", [
    ("bluesky_reply", bluesky_reply),
    ("create_new_bluesky_post", create_new_bluesky_post),
    ("search_bluesky_posts", search_bluesky_posts),
])
def test_tool_function_signatures(tool_name, tool_function):
    """Test that tool functions have proper signatures."""
    import inspect
    
    # Get function signature
    sig = inspect.signature(tool_function)
    
    # All tools should return strings
    assert sig.return_annotation == str or sig.return_annotation == inspect.Signature.empty
    
    # All tools should be callable
    assert callable(tool_function)


@pytest.mark.parametrize("messages,expected_valid", [
    (["Hello"], True),
    (["Hello", "World"], True),
    (["Hello", "World", "Test"], True),
    (["Hello", "World", "Test", "Final"], True),
    ([], False),
    (["x" * 301], False),
    (["msg1", "msg2", "msg3", "msg4", "msg5"], False),
])
def test_bluesky_reply_validation_parametrized(messages, expected_valid):
    """Parametrized test for Bluesky reply validation."""
    if expected_valid:
        result = bluesky_reply(messages)
        assert isinstance(result, str)
        assert len(result) > 0
    else:
        with pytest.raises(ValueError):
            bluesky_reply(messages)
