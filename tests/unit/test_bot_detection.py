"""
Unit tests for bot detection functionality.

Tests the bot detection logic without requiring live API keys or real data.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import the functions we're testing
from tools.bot_detection import (
    check_known_bots,
    should_respond_to_bot_thread,
    extract_handles_from_thread,
    CheckKnownBotsArgs,
    normalize_handle,
    parse_bot_handles
)


class TestHandleNormalization:
    """Test handle normalization logic."""
    
    def test_normalize_handle_basic(self):
        """Test basic handle normalization."""
        assert normalize_handle("user.bsky.social") == "user.bsky.social"
        assert normalize_handle("  user.bsky.social  ") == "user.bsky.social"
    
    def test_normalize_handle_with_at_symbol(self):
        """Test handles with @ symbol."""
        assert normalize_handle("@user.bsky.social") == "user.bsky.social"
        assert normalize_handle("  @user.bsky.social  ") == "user.bsky.social"
    
    def test_normalize_handle_case_sensitivity(self):
        """Test case insensitive normalization."""
        assert normalize_handle("User.bsky.social") == "user.bsky.social"
        assert normalize_handle("USER.bsky.social") == "user.bsky.social"
        assert normalize_handle("@User.bsky.social") == "user.bsky.social"
    
    def test_normalize_handle_whitespace(self):
        """Test whitespace handling."""
        assert normalize_handle("  user.bsky.social  ") == "user.bsky.social"
        assert normalize_handle("\tuser.bsky.social\t") == "user.bsky.social"
        assert normalize_handle("\nuser.bsky.social\n") == "user.bsky.social"


class TestBotListParsing:
    """Test parsing of bot list content."""
    
    def test_parse_bot_list_standard_format(self):
        """Test parsing standard bot list format."""
        bot_list_content = """
# Known bots list
- @bot1.bsky.social
- @bot2.bsky.social: This is a bot
- @bot3.bsky.social

# More bots
- @bot4.bsky.social: Another bot description
"""
        handles = parse_bot_handles(bot_list_content)
        expected = ['bot1.bsky.social', 'bot2.bsky.social', 'bot3.bsky.social', 'bot4.bsky.social']
        assert handles == expected
    
    def test_parse_bot_list_various_formats(self):
        """Test parsing various bot list formats."""
        bot_list_content = """
- @bot1.bsky.social
- bot2.bsky.social
@bot3.bsky.social
bot4.bsky.social: description
- @bot5.bsky.social: description with colon
"""
        handles = parse_bot_handles(bot_list_content)
        expected = ['bot1.bsky.social', 'bot2.bsky.social', 'bot3.bsky.social', 'bot4.bsky.social', 'bot5.bsky.social']
        assert handles == expected
    
    def test_parse_bot_list_with_comments(self):
        """Test parsing with comments and empty lines."""
        bot_list_content = """
# This is a comment
- @bot1.bsky.social

# Another comment
- @bot2.bsky.social: description

# Empty line above
"""
        handles = parse_bot_handles(bot_list_content)
        expected = ['bot1.bsky.social', 'bot2.bsky.social']
        assert handles == expected
    
    def test_parse_bot_list_malformed_entries(self):
        """Test parsing malformed entries."""
        bot_list_content = """
- @bot1.bsky.social
- malformed entry without proper format
- @bot2.bsky.social: proper entry
- 
- @bot3.bsky.social
"""
        handles = parse_bot_handles(bot_list_content)
        expected = ['bot1.bsky.social', 'malformed entry without proper format', 'bot2.bsky.social', 'bot3.bsky.social']
        assert handles == expected
    
    def test_parse_bot_list_case_insensitive(self):
        """Test parsing handles with different cases."""
        bot_list_content = """
- @Bot1.bsky.social
- @BOT2.bsky.social: description
- @bot3.bsky.social
"""
        handles = parse_bot_handles(bot_list_content)
        expected = ['bot1.bsky.social', 'bot2.bsky.social', 'bot3.bsky.social']
        assert handles == expected


class TestThreadHandleExtraction:
    """Test handle extraction from thread data."""
    
    def test_extract_handles_simple_thread(self):
        """Test extracting handles from simple thread."""
        thread_data = {
            'thread': {
                'post': {
                    'author': {'handle': 'user1.bsky.social'}
                },
                'replies': [
                    {
                        'post': {
                            'author': {'handle': 'user2.bsky.social'}
                        }
                    }
                ]
            }
        }
        handles = extract_handles_from_thread(thread_data)
        assert 'user1.bsky.social' in handles
        assert 'user2.bsky.social' in handles
        assert len(handles) == 2
    
    def test_extract_handles_nested_replies(self):
        """Test extracting handles from nested replies."""
        thread_data = {
            'thread': {
                'post': {
                    'author': {'handle': 'user1.bsky.social'}
                },
                'replies': [
                    {
                        'post': {
                            'author': {'handle': 'user2.bsky.social'}
                        },
                        'replies': [
                            {
                                'post': {
                                    'author': {'handle': 'user3.bsky.social'}
                                }
                            }
                        ]
                    }
                ]
            }
        }
        handles = extract_handles_from_thread(thread_data)
        assert 'user1.bsky.social' in handles
        assert 'user2.bsky.social' in handles
        assert 'user3.bsky.social' in handles
        assert len(handles) == 3
    
    def test_extract_handles_with_parent(self):
        """Test extracting handles with parent posts."""
        thread_data = {
            'thread': {
                'post': {
                    'author': {'handle': 'user1.bsky.social'}
                },
                'parent': {
                    'post': {
                        'author': {'handle': 'user0.bsky.social'}
                    }
                }
            }
        }
        handles = extract_handles_from_thread(thread_data)
        assert 'user0.bsky.social' in handles
        assert 'user1.bsky.social' in handles
        assert len(handles) == 2
    
    def test_extract_handles_different_structures(self):
        """Test extracting handles from different thread structures."""
        # Test direct post structure
        thread_data = {
            'post': {
                'author': {'handle': 'user1.bsky.social'}
            }
        }
        handles = extract_handles_from_thread(thread_data)
        assert 'user1.bsky.social' in handles
        assert len(handles) == 1
    
    def test_extract_handles_missing_handles(self):
        """Test extracting handles when some are missing."""
        thread_data = {
            'thread': {
                'post': {
                    'author': {'handle': 'user1.bsky.social'}
                },
                'replies': [
                    {
                        'post': {
                            'author': {}  # Missing handle
                        }
                    },
                    {
                        'post': {
                            'author': {'handle': 'user2.bsky.social'}
                        }
                    }
                ]
            }
        }
        handles = extract_handles_from_thread(thread_data)
        assert 'user1.bsky.social' in handles
        assert 'user2.bsky.social' in handles
        assert len(handles) == 2


class TestBotDetectionLogic:
    """Test the main bot detection logic."""
    
    def create_mock_agent_state(self, agent_id: str = "test-agent-123"):
        """Create a mock agent state object."""
        mock_agent_state = Mock()
        mock_agent_state.id = agent_id
        return mock_agent_state
    
    def create_mock_letta_client(self, bot_list_content: str = ""):
        """Create a mock Letta client."""
        mock_client = Mock()
        
        # Mock blocks.list() to return known_bots block
        mock_block = Mock()
        mock_block.label = "known_bots"
        mock_client.agents.blocks.list.return_value = [mock_block]
        
        # Mock blocks.retrieve() to return bot list content
        mock_bot_block = Mock()
        mock_bot_block.value = bot_list_content
        mock_client.agents.blocks.retrieve.return_value = mock_bot_block
        
        return mock_client
    
    @patch('tools.bot_detection.Letta')
    @patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'})
    def test_check_known_bots_no_bot_detected(self, mock_letta_class):
        """Test bot detection when no bots are detected."""
        # Setup mock
        bot_list_content = """
- @bot1.bsky.social
- @bot2.bsky.social
"""
        mock_client = self.create_mock_letta_client(bot_list_content)
        mock_letta_class.return_value = mock_client
        
        agent_state = self.create_mock_agent_state()
        handles = ['user1.bsky.social', 'user2.bsky.social']
        
        # Test
        result = check_known_bots(handles, agent_state)
        result_data = json.loads(result)
        
        # Assertions
        assert result_data['bot_detected'] == False
        assert result_data['detected_bots'] == []
        assert result_data['total_known_bots'] == 2
        assert 'user1.bsky.social' in result_data['checked_handles']
        assert 'user2.bsky.social' in result_data['checked_handles']
    
    @patch('tools.bot_detection.Letta')
    @patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'})
    def test_check_known_bots_bot_detected(self, mock_letta_class):
        """Test bot detection when bots are detected."""
        # Setup mock
        bot_list_content = """
- @bot1.bsky.social
- @bot2.bsky.social
"""
        mock_client = self.create_mock_letta_client(bot_list_content)
        mock_letta_class.return_value = mock_client
        
        agent_state = self.create_mock_agent_state()
        handles = ['user1.bsky.social', 'bot1.bsky.social', 'user2.bsky.social']
        
        # Test
        result = check_known_bots(handles, agent_state)
        result_data = json.loads(result)
        
        # Assertions
        assert result_data['bot_detected'] == True
        assert 'bot1.bsky.social' in result_data['detected_bots']
        assert len(result_data['detected_bots']) == 1
    
    @patch('tools.bot_detection.Letta')
    @patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'})
    def test_check_known_bots_case_insensitive(self, mock_letta_class):
        """Test bot detection with case insensitive matching."""
        # Setup mock
        bot_list_content = """
- @Bot1.bsky.social
- @BOT2.bsky.social
"""
        mock_client = self.create_mock_letta_client(bot_list_content)
        mock_letta_class.return_value = mock_client
        
        agent_state = self.create_mock_agent_state()
        handles = ['bot1.bsky.social', 'BOT2.bsky.social']
        
        # Test
        result = check_known_bots(handles, agent_state)
        result_data = json.loads(result)
        
        # This test will fail with current implementation due to case sensitivity
        # Will pass after implementing case-insensitive comparison
        assert result_data['bot_detected'] == True
        assert len(result_data['detected_bots']) == 2
    
    @patch('tools.bot_detection.Letta')
    @patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'})
    def test_check_known_bots_with_at_symbols(self, mock_letta_class):
        """Test bot detection with @ symbols in handles."""
        # Setup mock
        bot_list_content = """
- @bot1.bsky.social
- bot2.bsky.social
"""
        mock_client = self.create_mock_letta_client(bot_list_content)
        mock_letta_class.return_value = mock_client
        
        agent_state = self.create_mock_agent_state()
        handles = ['@bot1.bsky.social', '@bot2.bsky.social']
        
        # Test
        result = check_known_bots(handles, agent_state)
        result_data = json.loads(result)
        
        # This test will fail with current implementation due to @ symbol handling
        # Will pass after implementing consistent normalization
        assert result_data['bot_detected'] == True
        assert len(result_data['detected_bots']) == 2
    
    @patch('tools.bot_detection.Letta')
    @patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'})
    def test_check_known_bots_missing_block(self, mock_letta_class):
        """Test bot detection when known_bots block is not mounted."""
        # Setup mock
        mock_client = Mock()
        mock_client.agents.blocks.list.return_value = []  # No blocks
        
        mock_letta_class.return_value = mock_client
        
        agent_state = self.create_mock_agent_state()
        handles = ['user1.bsky.social']
        
        # Test
        result = check_known_bots(handles, agent_state)
        result_data = json.loads(result)
        
        # Assertions
        assert result_data['bot_detected'] == False
        assert 'error' in result_data
        assert 'not mounted' in result_data['error']
    
    @patch('tools.bot_detection.Letta')
    @patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'})
    def test_check_known_bots_api_error(self, mock_letta_class):
        """Test bot detection when API call fails."""
        # Setup mock
        mock_client = Mock()
        mock_client.agents.blocks.list.side_effect = Exception("API Error")
        
        mock_letta_class.return_value = mock_client
        
        agent_state = self.create_mock_agent_state()
        handles = ['user1.bsky.social']
        
        # Test
        result = check_known_bots(handles, agent_state)
        result_data = json.loads(result)
        
        # Assertions
        assert result_data['bot_detected'] == False
        assert 'error' in result_data


class TestBotResponseLogic:
    """Test bot response probability logic."""
    
    def test_should_respond_to_bot_thread_probability(self):
        """Test that response probability is approximately 10%."""
        # Run multiple times to test probability
        responses = []
        for _ in range(1000):
            responses.append(should_respond_to_bot_thread())
        
        # Should be approximately 10% (allowing for randomness)
        response_rate = sum(responses) / len(responses)
        assert 0.05 <= response_rate <= 0.15  # Allow some variance


class TestBotDetectionArgs:
    """Test the Pydantic model for bot detection arguments."""
    
    def test_check_known_bots_args_valid(self):
        """Test valid arguments."""
        args = CheckKnownBotsArgs(handles=['user1.bsky.social', 'user2.bsky.social'])
        assert args.handles == ['user1.bsky.social', 'user2.bsky.social']
    
    def test_check_known_bots_args_empty_list(self):
        """Test empty handles list."""
        args = CheckKnownBotsArgs(handles=[])
        assert args.handles == []
    
    def test_check_known_bots_args_single_handle(self):
        """Test single handle."""
        args = CheckKnownBotsArgs(handles=['user1.bsky.social'])
        assert args.handles == ['user1.bsky.social']


# Integration tests that will be implemented after refactoring
class TestBotDetectionIntegration:
    """Integration tests for the complete bot detection flow."""
    
    def test_full_bot_detection_flow(self):
        """Test the complete bot detection flow with mock data."""
        # This will be implemented after refactoring the main function
        pass
    
    def test_bot_detection_with_real_world_scenarios(self):
        """Test bot detection with real-world-like scenarios."""
        # This will be implemented after refactoring
        pass
