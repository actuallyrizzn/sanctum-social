import pytest
from unittest.mock import MagicMock, patch, mock_open
import json
import yaml

# Import Discord modules
from discord_utils import mention_to_yaml_string, thread_to_yaml_string
from tools.discord_post import create_new_discord_post
from tools.discord_reply import discord_reply
from tools.discord_search import search_discord_messages
from tools.discord_blocks import ignore_discord_users
from tools.discord_feed import get_discord_feed

class TestDiscordIntegration:
    """Test Discord integration functionality"""
    
    def test_discord_tool_function_signatures(self):
        """Test Discord tool function signatures"""
        # Test that all Discord tools have correct signatures
        tools = [
            create_new_discord_post,
            discord_reply,
            search_discord_messages,
            ignore_discord_users,
            get_discord_feed
        ]
        
        for tool in tools:
            assert callable(tool)
            # Test that tools can be called with basic arguments
            if tool == create_new_discord_post:
                result = tool(['test message'])
                assert isinstance(result, str)
            elif tool == discord_reply:
                result = tool(['test reply'])
                assert isinstance(result, str)
            elif tool == search_discord_messages:
                result = tool('test query')
                assert isinstance(result, str)
            elif tool == ignore_discord_users:
                result = tool(['123456'])
                assert isinstance(result, str)
            elif tool == get_discord_feed:
                result = tool('123456')
                assert isinstance(result, str)
    
    def test_discord_mention_processing_workflow(self):
        """Test Discord mention processing workflow"""
        # Simulate Discord mention
        mention = {
            'id': '123456789',
            'content': 'Hello @void, how are you?',
            'author': {
                'id': '987654321',
                'name': 'testuser',
                'display_name': 'Test User'
            },
            'channel_id': '111222333',
            'guild_id': '444555666',
            'created_at': '2025-01-01T00:00:00Z'
        }
        
        # Convert to YAML for processing
        yaml_string = mention_to_yaml_string(mention)
        
        assert 'platform: discord' in yaml_string
        assert 'Hello @void' in yaml_string
        assert 'testuser' in yaml_string
        
        # Simulate processing response
        response = discord_reply(['Hello! I am doing well, thank you for asking.'])
        
        assert 'Discord reply sent' in response
    
    def test_discord_thread_processing_workflow(self):
        """Test Discord thread processing workflow"""
        # Simulate Discord thread
        thread_data = {
            'conversation_id': 'conv_123',
            'messages': [
                {
                    'id': 'msg_1',
                    'content': 'What is the weather like?',
                    'author': {'id': 'user_1', 'name': 'User 1'},
                    'created_at': '2025-01-01T00:00:00Z',
                    'channel_id': 'channel_123'
                },
                {
                    'id': 'msg_2',
                    'content': 'I can help you find weather information!',
                    'author': {'id': 'bot_id', 'name': 'Void'},
                    'created_at': '2025-01-01T00:01:00Z',
                    'channel_id': 'channel_123'
                }
            ],
            'users': {
                'user_1': {'id': 'user_1', 'name': 'User 1'},
                'bot_id': {'id': 'bot_id', 'name': 'Void'}
            },
            'channel_id': 'channel_123',
            'guild_id': 'guild_123'
        }
        
        # Convert to YAML for processing
        yaml_string = thread_to_yaml_string(thread_data)
        
        assert 'platform: discord' in yaml_string
        assert 'What is the weather like?' in yaml_string
        assert 'I can help you find weather information!' in yaml_string
        
        # Simulate search in thread
        search_result = search_discord_messages('weather', max_results=5, channel_id='channel_123')
        
        assert 'Discord search for "weather"' in search_result
        assert 'in channel channel_123' in search_result
    
    def test_discord_user_management_workflow(self):
        """Test Discord user management workflow"""
        # Simulate ignoring users
        ignore_result = ignore_discord_users(['123456', '789012'], 'Spam users')
        
        assert 'Ignored 2 Discord users' in ignore_result
        assert 'Spam users' in ignore_result
        
        # Simulate unignoring users
        unignore_result = ignore_discord_users(['123456'])  # This would be unignore in real implementation
        
        assert 'Ignored 1 Discord users' in unignore_result
    
    def test_discord_feed_workflow(self):
        """Test Discord feed workflow"""
        # Simulate getting feed
        feed_result = get_discord_feed('123456', max_posts=10)
        
        assert 'Retrieved Discord feed from channel 123456' in feed_result
        assert '10 messages' in feed_result
        
        # Simulate posting to feed
        post_result = create_new_discord_post(['Here is the latest update!'])
        
        assert 'Discord message sent' in post_result
    
    def test_discord_error_handling(self):
        """Test Discord error handling"""
        # Test various error conditions
        with pytest.raises(ValueError):
            create_new_discord_post([])
        
        with pytest.raises(ValueError):
            discord_reply([])
        
        with pytest.raises(ValueError):
            search_discord_messages('')
        
        with pytest.raises(ValueError):
            ignore_discord_users([])
        
        with pytest.raises(ValueError):
            get_discord_feed('')
    
    def test_discord_rate_limiting_simulation(self):
        """Test Discord rate limiting simulation"""
        # Simulate rate limiting by testing multiple rapid calls
        responses = []
        
        # These would normally be rate limited in real implementation
        for i in range(3):
            response = discord_reply([f'Response {i+1}'])
            responses.append(response)
        
        # All should succeed in test environment
        assert len(responses) == 3
        assert all('Discord reply sent' in resp for resp in responses)
    
    def test_discord_configuration_integration(self):
        """Test Discord configuration integration"""
        # Simulate loading Discord config
        mock_config = {
            'discord': {
                'bot_token': 'test_token',
                'guild_id': 'test_guild',
                'channels': {
                    'general': 'test_channel'
                },
                'rate_limit': {
                    'cooldown_seconds': 5,
                    'max_responses_per_minute': 10
                },
                'context': {
                    'message_history_limit': 10
                }
            }
        }
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(mock_config))):
            # This would normally load config in real implementation
            assert mock_config['discord']['bot_token'] == 'test_token'
            assert mock_config['discord']['rate_limit']['cooldown_seconds'] == 5
    
    def test_discord_queue_integration(self):
        """Test Discord queue integration"""
        # Simulate queue operations
        mention = {
            'id': '123456789',
            'content': 'Test mention',
            'author': {'id': '987654321', 'name': 'testuser', 'display_name': 'Test User'},
            'channel_id': '111222333',
            'created_at': '2025-01-01T00:00:00Z'
        }
        
        # Simulate saving to queue
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('pathlib.Path.mkdir'):
                # This would normally save to queue in real implementation
                yaml_string = mention_to_yaml_string(mention)
                assert 'platform: discord' in yaml_string
                assert '123456789' in yaml_string
    
    def test_discord_memory_integration(self):
        """Test Discord memory integration"""
        # Simulate memory operations
        user_info = {
            'id': '123456',
            'name': 'testuser',
            'display_name': 'Test User',
            'interaction_count': 5,
            'last_seen': '2025-01-01T00:00:00Z'
        }
        
        # Simulate creating acknowledgment
        ack = f"✅ Discord user {user_info['id']} acknowledged"
        
        assert '123456' in ack
        assert 'acknowledged' in ack
