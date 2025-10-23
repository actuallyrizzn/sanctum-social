import pytest
from unittest.mock import MagicMock, patch, mock_open
import json
import yaml
from pathlib import Path
import os

# Import Discord modules
from platforms.discord.utils import (
    mention_to_yaml_string,
    thread_to_yaml_string,
    convert_to_basic_types,
    strip_fields,
    flatten_thread_structure,
    remove_outside_quotes,
    create_discord_ack,
    create_discord_tool_call_record,
    create_discord_reasoning_record
)

# Import Discord tools
from platforms.discord.tools.post import create_new_discord_post, DiscordPostArgs
from platforms.discord.tools.reply import discord_reply, DiscordReplyArgs
from platforms.discord.tools.search import search_discord_messages, DiscordSearchArgs
from platforms.discord.tools.blocks import ignore_discord_users, unignore_discord_users, DiscordIgnoreArgs
from platforms.discord.tools.feed import get_discord_feed, DiscordFeedArgs

class TestDiscordUtils:
    """Test Discord utility functions"""
    
    def test_mention_to_yaml_string(self):
        """Test converting Discord mention to YAML string"""
        mention = {
            'id': '123456789',
            'content': 'Hello @void',
            'author': {
                'id': '987654321',
                'name': 'testuser',
                'display_name': 'Test User'
            },
            'channel_id': '111222333',
            'guild_id': '444555666',
            'created_at': '2025-01-01T00:00:00Z'
        }
        
        yaml_string = mention_to_yaml_string(mention)
        
        assert 'platform: discord' in yaml_string
        assert "mention_id: '123456789'" in yaml_string
        assert 'Hello @void' in yaml_string
        assert 'testuser' in yaml_string
    
    def test_thread_to_yaml_string(self):
        """Test converting Discord thread to YAML string"""
        thread_data = {
            'conversation_id': 'conv_123',
            'messages': [
                {
                    'id': 'msg_1',
                    'content': 'First message',
                    'author': {'id': 'user_1', 'name': 'User 1'}
                },
                {
                    'id': 'msg_2',
                    'content': 'Second message',
                    'author': {'id': 'user_2', 'name': 'User 2'}
                }
            ],
            'users': {
                'user_1': {'id': 'user_1', 'name': 'User 1'},
                'user_2': {'id': 'user_2', 'name': 'User 2'}
            },
            'channel_id': 'channel_123',
            'guild_id': 'guild_123'
        }
        
        yaml_string = thread_to_yaml_string(thread_data)
        
        assert 'platform: discord' in yaml_string
        assert 'conversation_id: conv_123' in yaml_string
        assert 'First message' in yaml_string
        assert 'Second message' in yaml_string
    
    def test_convert_to_basic_types(self):
        """Test converting Discord data to basic types"""
        from datetime import datetime
        
        data = {
            'id': '123',
            'created_at': datetime(2025, 1, 1, 12, 0, 0),
            'nested': {
                'value': 'test',
                'timestamp': datetime(2025, 1, 1, 12, 0, 0)
            }
        }
        
        result = convert_to_basic_types(data)
        
        assert result['id'] == '123'
        assert result['created_at'] == '2025-01-01T12:00:00'
        assert result['nested']['value'] == 'test'
        assert result['nested']['timestamp'] == '2025-01-01T12:00:00'
    
    def test_strip_fields(self):
        """Test stripping fields from Discord data"""
        data = {
            'id': '123',
            'content': 'Hello',
            'avatar': 'avatar_url',
            'banner': 'banner_url',
            'nested': {
                'value': 'test',
                'avatar': 'nested_avatar'
            }
        }
        
        fields_to_strip = ['avatar', 'banner']
        result = strip_fields(data, fields_to_strip)
        
        assert 'id' in result
        assert 'content' in result
        assert 'avatar' not in result
        assert 'banner' not in result
        assert 'nested' in result
        assert 'avatar' not in result['nested']
    
    def test_flatten_thread_structure(self):
        """Test flattening Discord thread structure"""
        thread_data = {
            'conversation_id': 'conv_123',
            'messages': [
                {
                    'id': 'msg_1',
                    'content': 'First message',
                    'author': {'id': 'user_1', 'name': 'User 1'},
                    'created_at': '2025-01-01T00:00:00Z',
                    'channel_id': 'channel_123'
                }
            ]
        }
        
        result = flatten_thread_structure(thread_data)
        
        assert result['platform'] == 'discord'
        assert result['conversation_id'] == 'conv_123'
        assert len(result['messages']) == 1
        assert result['messages'][0]['id'] == 'msg_1'
        assert 'user_1' in result['users']
    
    def test_remove_outside_quotes(self):
        """Test removing quotes from outside of strings"""
        assert remove_outside_quotes('"hello"') == 'hello'
        assert remove_outside_quotes("'world'") == 'world'
        assert remove_outside_quotes('no quotes') == 'no quotes'
        assert remove_outside_quotes('"mixed\'quotes"') == 'mixed\'quotes'
        assert remove_outside_quotes('') == ''
    
    def test_create_discord_ack(self):
        """Test creating Discord acknowledgment"""
        ack = create_discord_ack('123456789', 'Test note')
        
        assert '✅ Discord mention 123456789 acknowledged' in ack
        assert 'Test note' in ack
    
    def test_create_discord_tool_call_record(self):
        """Test creating Discord tool call record"""
        args = {'text': ['Hello']}
        result = 'Success'
        
        record = create_discord_tool_call_record('test_tool', args, result)
        
        assert 'Discord Tool Call Record' in record
        assert 'test_tool' in record
        assert 'Hello' in record
        assert 'Success' in record
    
    def test_create_discord_reasoning_record(self):
        """Test creating Discord reasoning record"""
        reasoning = 'User asked for help'
        
        record = create_discord_reasoning_record(reasoning)
        
        assert 'Discord Reasoning Record' in record
        assert 'User asked for help' in record

class TestDiscordPostTool:
    """Test Discord post tool"""
    
    def test_create_new_discord_post_single_message(self):
        """Test creating single Discord message"""
        result = create_new_discord_post(['Hello Discord!'])
        assert result == 'Discord message sent'
    
    def test_create_new_discord_post_multiple_messages(self):
        """Test creating multiple Discord messages"""
        result = create_new_discord_post(['First message', 'Second message'])
        assert result == 'Discord thread with 2 messages sent'
    
    def test_create_new_discord_post_empty_list(self):
        """Test creating Discord post with empty list"""
        with pytest.raises(ValueError, match="Text list cannot be empty"):
            create_new_discord_post([])
    
    def test_create_new_discord_post_message_too_long(self):
        """Test creating Discord post with message too long"""
        long_message = 'x' * 2001
        with pytest.raises(ValueError, match="Message 1 cannot be longer than 2000 characters"):
            create_new_discord_post([long_message])
    
    def test_discord_post_args_validation(self):
        """Test Discord post args validation"""
        # Valid args
        args = DiscordPostArgs(text=['Hello'])
        assert args.text == ['Hello']
        
        # Invalid args
        with pytest.raises(ValueError):
            DiscordPostArgs(text=[])

class TestDiscordReplyTool:
    """Test Discord reply tool"""
    
    def test_discord_reply_single_message(self):
        """Test single Discord reply"""
        result = discord_reply(['Hello!'])
        assert result == 'Discord reply sent'
    
    def test_discord_reply_multiple_messages(self):
        """Test multiple Discord replies"""
        result = discord_reply(['First reply', 'Second reply'])
        assert result == 'Discord reply thread with 2 messages sent'
    
    def test_discord_reply_empty_messages(self):
        """Test Discord reply with empty messages"""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            discord_reply([])
    
    def test_discord_reply_too_many_messages(self):
        """Test Discord reply with too many messages"""
        messages = ['msg1', 'msg2', 'msg3', 'msg4', 'msg5']
        with pytest.raises(ValueError, match="Cannot send more than 4 reply messages"):
            discord_reply(messages)
    
    def test_discord_reply_message_too_long(self):
        """Test Discord reply with message too long"""
        long_message = 'x' * 2001
        with pytest.raises(ValueError, match="Message 1 cannot be longer than 2000 characters"):
            discord_reply([long_message])
    
    def test_discord_reply_args_validation(self):
        """Test Discord reply args validation"""
        # Valid args
        args = DiscordReplyArgs(messages=['Hello'])
        assert args.messages == ['Hello']
        
        # Invalid args
        with pytest.raises(ValueError):
            DiscordReplyArgs(messages=[])

class TestDiscordSearchTool:
    """Test Discord search tool"""
    
    def test_search_discord_messages(self):
        """Test searching Discord messages"""
        result = search_discord_messages('hello', max_results=5)
        assert 'Discord search for "hello"' in result
        assert '5 results' in result
    
    def test_search_discord_messages_with_channel(self):
        """Test searching Discord messages in specific channel"""
        result = search_discord_messages('hello', max_results=5, channel_id='123456')
        assert 'in channel 123456' in result
    
    def test_search_discord_messages_empty_query(self):
        """Test searching Discord messages with empty query"""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            search_discord_messages('')
    
    def test_search_discord_messages_max_results_too_high(self):
        """Test searching Discord messages with max_results too high"""
        with pytest.raises(ValueError, match="max_results cannot exceed 100"):
            search_discord_messages('hello', max_results=101)
    
    def test_discord_search_args_validation(self):
        """Test Discord search args validation"""
        # Valid args
        args = DiscordSearchArgs(query='hello', max_results=10)
        assert args.query == 'hello'
        assert args.max_results == 10
        
        # Invalid args
        with pytest.raises(ValueError):
            DiscordSearchArgs(query='hello', max_results=101)

class TestDiscordBlocksTool:
    """Test Discord blocks tool"""
    
    def test_ignore_discord_users(self):
        """Test ignoring Discord users"""
        result = ignore_discord_users(['123456', '789012'], 'Spam users')
        assert 'Ignored 2 Discord users' in result
        assert 'Spam users' in result
    
    def test_ignore_discord_users_empty_list(self):
        """Test ignoring Discord users with empty list"""
        with pytest.raises(ValueError, match="User IDs list cannot be empty"):
            ignore_discord_users([])
    
    def test_unignore_discord_users(self):
        """Test unignoring Discord users"""
        result = unignore_discord_users(['123456', '789012'])
        assert 'Removed 2 Discord users from ignore list' in result
    
    def test_unignore_discord_users_empty_list(self):
        """Test unignoring Discord users with empty list"""
        with pytest.raises(ValueError, match="User IDs list cannot be empty"):
            unignore_discord_users([])
    
    def test_discord_ignore_args_validation(self):
        """Test Discord ignore args validation"""
        # Valid args
        args = DiscordIgnoreArgs(user_ids=['123456'], reason='Spam')
        assert args.user_ids == ['123456']
        assert args.reason == 'Spam'
        
        # Invalid args
        with pytest.raises(ValueError):
            DiscordIgnoreArgs(user_ids=[])

class TestDiscordFeedTool:
    """Test Discord feed tool"""
    
    def test_get_discord_feed(self):
        """Test getting Discord feed"""
        result = get_discord_feed('123456', max_posts=5)
        assert 'Retrieved Discord feed from channel 123456' in result
        assert '5 messages' in result
    
    def test_get_discord_feed_empty_channel_id(self):
        """Test getting Discord feed with empty channel ID"""
        with pytest.raises(ValueError, match="Channel ID cannot be empty"):
            get_discord_feed('')
    
    def test_get_discord_feed_max_posts_too_high(self):
        """Test getting Discord feed with max_posts too high"""
        with pytest.raises(ValueError, match="max_posts cannot exceed 100"):
            get_discord_feed('123456', max_posts=101)
    
    def test_discord_feed_args_validation(self):
        """Test Discord feed args validation"""
        # Valid args
        args = DiscordFeedArgs(channel_id='123456', max_posts=10)
        assert args.channel_id == '123456'
        assert args.max_posts == 10
        
        # Invalid args
        with pytest.raises(ValueError):
            DiscordFeedArgs(channel_id='123456', max_posts=101)
