"""
Test environment configuration and utilities for comprehensive test coverage.

This module provides:
1. Test environment setup with mocked credentials
2. Missing utility functions for integration tests
3. Reusable mock fixtures and patterns
"""

import os
import json
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional


def setup_test_environment() -> Dict[str, str]:
    """
    Set up test environment with mocked credentials.
    
    Returns:
        Dictionary of test environment variables
    """
    test_env = {
        'LETTA_API_KEY': 'test_letta_key_12345',
        'BSKY_USERNAME': 'test_user.bsky.social',
        'BSKY_PASSWORD': 'test_password_12345',
        'X_API_KEY': 'test_x_api_key_12345',
        'X_API_SECRET': 'test_x_api_secret_12345',
        'X_ACCESS_TOKEN': 'test_x_access_token_12345',
        'X_ACCESS_TOKEN_SECRET': 'test_x_token_secret_12345',
        'BSKY_APP_PASSWORD': 'test_app_password_12345'
    }
    return test_env


def get_agent_config() -> Dict[str, Any]:
    """
    Mock agent configuration for tests.
    
    Returns:
        Mock agent configuration dictionary
    """
    return {
        'agent_id': 'test-agent-id-12345',
        'platform': 'bluesky',
        'tools': ['post', 'reply', 'search', 'feed', 'blocks'],
        'memory_blocks': ['system_information', 'conversation_summary'],
        'settings': {
            'polling_interval': 30,
            'max_retries': 3,
            'timeout': 30
        }
    }


def get_thread(uri: str) -> Dict[str, Any]:
    """
    Mock thread retrieval for tests.
    
    Args:
        uri: Thread URI to retrieve
        
    Returns:
        Mock thread data dictionary
    """
    return {
        'uri': uri,
        'posts': [
            {
                'uri': f'{uri}/post1',
                'text': 'Test post content',
                'author': 'test.user.bsky.social',
                'created_at': '2025-01-01T00:00:00Z'
            }
        ],
        'replies': [
            {
                'uri': f'{uri}/reply1',
                'text': 'Test reply content',
                'author': 'reply.user.bsky.social',
                'created_at': '2025-01-01T00:01:00Z'
            }
        ],
        'thread_length': 1,
        'reply_count': 1
    }


def register_tools() -> Dict[str, Any]:
    """
    Mock tool registration for tests.
    
    Returns:
        Mock registration result dictionary
    """
    return {
        'status': 'success',
        'tools_registered': 5,
        'registered_tools': [
            'post', 'reply', 'search', 'feed', 'blocks'
        ],
        'errors': [],
        'warnings': []
    }


def get_bluesky_session() -> Dict[str, str]:
    """
    Mock Bluesky session for tests.
    
    Returns:
        Mock session data dictionary
    """
    return {
        'accessJwt': 'test_access_jwt_12345',
        'refreshJwt': 'test_refresh_jwt_12345',
        'handle': 'test.user.bsky.social',
        'did': 'did:plc:test123456789',
        'email': 'test@example.com'
    }


def get_x_credentials() -> Dict[str, str]:
    """
    Mock X (Twitter) credentials for tests.
    
    Returns:
        Mock X credentials dictionary
    """
    return {
        'api_key': 'test_x_api_key_12345',
        'api_secret': 'test_x_api_secret_12345',
        'access_token': 'test_x_access_token_12345',
        'access_token_secret': 'test_x_token_secret_12345',
        'user_id': '123456789',
        'screen_name': 'test_user'
    }


def create_mock_notification(platform: str = 'bluesky', 
                            handle: str = 'test.user.bsky.social') -> Dict[str, Any]:
    """
    Create a mock notification for tests.
    
    Args:
        platform: Platform type ('bluesky' or 'x')
        handle: User handle
        
    Returns:
        Mock notification dictionary
    """
    if platform == 'bluesky':
        return {
            'uri': f'at://did:plc:test123456789/app.bsky.feed.post/test123',
            'cid': 'test_cid_12345',
            'author': {
                'did': 'did:plc:test123456789',
                'handle': handle,
                'displayName': 'Test User'
            },
            'record': {
                'text': 'Test notification content',
                'createdAt': '2025-01-01T00:00:00Z'
            },
            'replyCount': 0,
            'repostCount': 0,
            'likeCount': 0,
            'indexedAt': '2025-01-01T00:00:00Z'
        }
    else:  # X platform
        return {
            'id': '1234567890123456789',
            'text': 'Test X notification content',
            'author_id': '123456789',
            'author_username': handle.replace('.bsky.social', ''),
            'created_at': '2025-01-01T00:00:00Z',
            'public_metrics': {
                'retweet_count': 0,
                'like_count': 0,
                'reply_count': 0
            }
        }


def create_mock_queue_file(filepath: str, notification: Dict[str, Any]) -> None:
    """
    Create a mock queue file for tests.
    
    Args:
        filepath: Path to create the file
        notification: Notification data to write
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(notification, f, indent=2)


def mock_letta_client():
    """
    Create a mock Letta client for tests.
    
    Returns:
        Mock Letta client object
    """
    mock_client = MagicMock()
    
    # Mock agent operations
    mock_client.agents = MagicMock()
    mock_client.agents.blocks = MagicMock()
    
    # Mock block operations
    mock_client.agents.blocks.list.return_value = [
        MagicMock(label='system_information'),
        MagicMock(label='conversation_summary')
    ]
    
    mock_client.agents.blocks.attach.return_value = MagicMock()
    mock_client.agents.blocks.detach.return_value = MagicMock()
    mock_client.agents.blocks.retrieve.return_value = MagicMock(
        value='Mock block content'
    )
    
    return mock_client


def mock_bluesky_client():
    """
    Create a mock Bluesky client for tests.
    
    Returns:
        Mock Bluesky client object
    """
    mock_client = MagicMock()
    
    # Mock session operations
    mock_client.login.return_value = get_bluesky_session()
    
    # Mock feed operations
    mock_client.get_timeline.return_value = {
        'feed': [create_mock_notification()]
    }
    
    # Mock post operations
    mock_client.post.return_value = {
        'uri': 'at://did:plc:test123456789/app.bsky.feed.post/test123',
        'cid': 'test_cid_12345'
    }
    
    return mock_client


def mock_x_client():
    """
    Create a mock X (Twitter) client for tests.
    
    Returns:
        Mock X client object
    """
    mock_client = MagicMock()
    
    # Mock tweet operations
    mock_client.create_tweet.return_value = {
        'data': {
            'id': '1234567890123456789',
            'text': 'Test tweet content'
        }
    }
    
    # Mock timeline operations
    mock_client.get_home_timeline.return_value = {
        'data': [create_mock_notification('x')]
    }
    
    return mock_client


class TestEnvironmentManager:
    """
    Context manager for test environment setup.
    
    Usage:
        with TestEnvironmentManager() as env:
            # Test code here
            pass
    """
    
    def __init__(self):
        self.test_env = setup_test_environment()
        self.original_env = {}
    
    def __enter__(self):
        # Store original environment variables
        for key in self.test_env:
            self.original_env[key] = os.environ.get(key)
        
        # Set test environment variables
        os.environ.update(self.test_env)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original environment variables
        for key in self.test_env:
            if key in self.original_env:
                os.environ[key] = self.original_env[key]
            else:
                os.environ.pop(key, None)


# Convenience functions for common test patterns
def with_test_environment(func):
    """
    Decorator to automatically set up test environment for a test function.
    
    Args:
        func: Test function to decorate
        
    Returns:
        Decorated test function
    """
    def wrapper(*args, **kwargs):
        with TestEnvironmentManager():
            return func(*args, **kwargs)
    return wrapper


def create_test_notification_db():
    """
    Create a mock notification database for tests.
    
    Returns:
        Mock notification database object
    """
    mock_db = MagicMock()
    mock_db.add_notification.return_value = True
    mock_db.get_notifications.return_value = []
    mock_db.count_notifications.return_value = 0
    mock_db.delete_notification.return_value = True
    return mock_db
