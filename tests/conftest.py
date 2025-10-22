"""
Shared pytest configuration and fixtures for Void Bot testing.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any, Generator

import pytest
from faker import Faker
from freezegun import freeze_time

try:
    import yaml
except ImportError:
    yaml = None

try:
    from factory import Factory
except ImportError:
    Factory = None

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Initialize faker for test data generation
fake = Faker()


@pytest.fixture(scope="session")
def project_root_path():
    """Return the project root path."""
    return project_root


@pytest.fixture(scope="session")
def test_data_dir():
    """Return the test data directory."""
    return project_root / "tests" / "data"


@pytest.fixture(scope="session")
def fixtures_dir():
    """Return the fixtures directory."""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test isolation."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Enhanced cleanup for Windows compatibility
    import gc
    import time
    
    # Force garbage collection to close any open file handles
    gc.collect()
    
    # Retry logic for Windows file cleanup
    max_retries = 3
    for attempt in range(max_retries):
        try:
            shutil.rmtree(temp_path)
            break
        except PermissionError as e:
            if attempt < max_retries - 1:
                # Wait a bit and try again
                time.sleep(0.1 * (attempt + 1))
                gc.collect()  # Force another garbage collection
                continue
            else:
                # On final attempt, just log the warning and continue
                print(f"Warning: Could not clean up temporary directory {temp_path}: {e}")
                break
        except Exception as e:
            # For other exceptions, just log and continue
            print(f"Warning: Unexpected error cleaning up {temp_path}: {e}")
            break


@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    return {
        "letta": {
            "api_key": "test-letta-api-key",
            "project_id": "test-project-id",
            "agent_id": "test-agent-id",
            "timeout": 30,
            "base_url": None
        },
        "bluesky": {
            "username": "test.bsky.social",
            "password": "test-app-password",
            "pds_uri": "https://bsky.social"
        },
        "x": {
            "api_key": "test-x-api-key",
            "consumer_key": "test-consumer-key",
            "consumer_secret": "test-consumer-secret",
            "access_token": "test-access-token",
            "access_token_secret": "test-access-token-secret",
            "user_id": "1234567890"
        },
        "bot": {
            "fetch_notifications_delay": 5,
            "max_processed_notifications": 100,
            "max_notification_pages": 5,
            "agent": {
                "name": "test-void",
                "model": "openai/gpt-4o-mini",
                "embedding": "openai/text-embedding-3-small",
                "description": "Test void agent",
                "max_steps": 10,
                "blocks": {
                    "zeitgeist": {
                        "label": "zeitgeist",
                        "value": "Test zeitgeist",
                        "description": "Test zeitgeist block"
                    },
                    "persona": {
                        "label": "void-persona",
                        "value": "Test persona",
                        "description": "Test persona block"
                    }
                }
            }
        },
        "queue": {
            "priority_users": ["test.user.bsky.social"],
            "base_dir": "test_queue",
            "error_dir": "test_queue/errors",
            "no_reply_dir": "test_queue/no_reply",
            "processed_file": "test_queue/processed_notifications.json"
        },
        "threading": {
            "parent_height": 10,
            "depth": 5,
            "max_post_characters": 300
        },
        "logging": {
            "level": "DEBUG",
            "loggers": {
                "void_bot": "DEBUG",
                "void_bot_prompts": "DEBUG",
                "httpx": "CRITICAL"
            }
        }
    }


@pytest.fixture
def mock_config_file(temp_dir, mock_config):
    """Create a temporary config.yaml file for testing."""
    config_path = temp_dir / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(mock_config, f)
    return config_path


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for testing."""
    env_vars = {
        "LETTA_API_KEY": "test-letta-api-key",
        "BSKY_USERNAME": "test.bsky.social",
        "BSKY_PASSWORD": "test-app-password",
        "PDS_URI": "https://bsky.social",
        "X_API_KEY": "test-x-api-key",
        "X_CONSUMER_KEY": "test-consumer-key",
        "X_CONSUMER_SECRET": "test-consumer-secret",
        "X_ACCESS_TOKEN": "test-access-token",
        "X_ACCESS_TOKEN_SECRET": "test-access-token-secret",
        "X_USER_ID": "1234567890"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_letta_client():
    """Provide a mock Letta client for testing."""
    client = Mock()
    client.agents = Mock()
    client.agents.list.return_value = []
    client.agents.get.return_value = Mock()
    client.agents.create.return_value = Mock()
    client.agents.modify.return_value = Mock()
    client.agents.delete.return_value = Mock()
    
    client.blocks = Mock()
    client.blocks.list.return_value = []
    client.blocks.create.return_value = Mock()
    client.blocks.modify.return_value = Mock()
    client.blocks.delete.return_value = Mock()
    client.blocks.attach.return_value = Mock()
    client.blocks.detach.return_value = Mock()
    
    client.messages = Mock()
    client.messages.send.return_value = Mock()
    
    return client


@pytest.fixture
def mock_bluesky_client():
    """Provide a mock Bluesky client for testing."""
    client = Mock()
    client.login.return_value = Mock()
    client.get_notifications.return_value = Mock()
    client.get_post_thread.return_value = Mock()
    client.create_post.return_value = Mock()
    client.create_reply.return_value = Mock()
    client.get_profile.return_value = Mock()
    return client


@pytest.fixture
def mock_x_client():
    """Provide a mock X client for testing."""
    client = Mock()
    client.get_mentions.return_value = Mock()
    client.get_tweet.return_value = Mock()
    client.search_tweets.return_value = Mock()
    client.post_tweet.return_value = Mock()
    client.post_reply.return_value = Mock()
    client.get_user_by_id.return_value = Mock()
    return client


@pytest.fixture
def sample_notification():
    """Provide a sample notification for testing."""
    return {
        "uri": "at://did:plc:test/app.bsky.notification.record/test-notification",
        "cid": "test-cid",
        "author": {
            "did": "did:plc:test-author",
            "handle": "test.author.bsky.social",
            "displayName": "Test Author",
            "avatar": "https://example.com/avatar.jpg"
        },
        "reason": "mention",
        "reasonSubject": "at://did:plc:test/app.bsky.feed.post/test-post",
        "record": {
            "text": "Hello @test.bsky.social, how are you?",
            "createdAt": "2025-01-01T00:00:00.000Z",
            "reply": {
                "root": {
                    "uri": "at://did:plc:test/app.bsky.feed.post/root-post",
                    "cid": "root-cid"
                },
                "parent": {
                    "uri": "at://did:plc:test/app.bsky.feed.post/parent-post",
                    "cid": "parent-cid"
                }
            }
        },
        "isRead": False,
        "indexedAt": "2025-01-01T00:00:00.000Z"
    }


@pytest.fixture
def sample_thread():
    """Provide a sample thread for testing."""
    return {
        "thread": {
            "post": {
                "uri": "at://did:plc:test/app.bsky.feed.post/test-post",
                "cid": "test-cid",
                "author": {
                    "did": "did:plc:test-author",
                    "handle": "test.author.bsky.social",
                    "displayName": "Test Author"
                },
                "record": {
                    "text": "This is a test post",
                    "createdAt": "2025-01-01T00:00:00.000Z"
                },
                "replyCount": 2,
                "repostCount": 1,
                "likeCount": 5
            },
            "replies": [
                {
                    "post": {
                        "uri": "at://did:plc:test/app.bsky.feed.post/reply-1",
                        "cid": "reply-1-cid",
                        "author": {
                            "did": "did:plc:test-reply-author",
                            "handle": "test.reply.bsky.social",
                            "displayName": "Test Reply Author"
                        },
                        "record": {
                            "text": "This is a reply",
                            "createdAt": "2025-01-01T00:01:00.000Z"
                        }
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_x_mention():
    """Provide a sample X mention for testing."""
    return {
        "id": "1234567890",
        "text": "Hello @testbot, how are you?",
        "author_id": "9876543210",
        "created_at": "2025-01-01T00:00:00.000Z",
        "conversation_id": "1234567890",
        "in_reply_to_user_id": "1111111111",
        "referenced_tweets": [
            {
                "type": "replied_to",
                "id": "0987654321"
            }
        ],
        "public_metrics": {
            "retweet_count": 0,
            "reply_count": 0,
            "like_count": 0,
            "quote_count": 0
        }
    }


@pytest.fixture
def sample_x_user():
    """Provide a sample X user for testing."""
    return {
        "id": "9876543210",
        "username": "testuser",
        "name": "Test User",
        "created_at": "2020-01-01T00:00:00.000Z",
        "description": "Test user description",
        "public_metrics": {
            "followers_count": 100,
            "following_count": 50,
            "tweet_count": 500,
            "listed_count": 10
        },
        "verified": False,
        "protected": False
    }


@pytest.fixture
def mock_queue_dir(temp_dir):
    """Create a mock queue directory structure."""
    queue_dir = temp_dir / "queue"
    queue_dir.mkdir()
    (queue_dir / "errors").mkdir()
    (queue_dir / "no_reply").mkdir()
    return queue_dir


@pytest.fixture
def mock_x_queue_dir(temp_dir):
    """Create a mock X queue directory structure."""
    x_queue_dir = temp_dir / "x_queue"
    x_queue_dir.mkdir()
    (x_queue_dir / "acknowledgments").mkdir()
    (x_queue_dir / "debug").mkdir()
    return x_queue_dir


@pytest.fixture
def mock_x_cache_dir(temp_dir):
    """Create a mock X cache directory."""
    x_cache_dir = temp_dir / "x_cache"
    x_cache_dir.mkdir()
    return x_cache_dir


@pytest.fixture
def frozen_time():
    """Freeze time for consistent testing."""
    with freeze_time("2025-01-01T00:00:00Z") as frozen_time:
        yield frozen_time


@pytest.fixture
def notification_db(temp_dir):
    """Create a NotificationDB instance with proper cleanup."""
    from notification_db import NotificationDB
    db_path = temp_dir / "test.db"
    with NotificationDB(str(db_path)) as db:
        yield db


# Test data factories
class NotificationFactory(Factory):
    """Factory for creating test notifications."""
    
    class Meta:
        model = dict
    
    uri = fake.uri()
    cid = fake.sha256()
    author = {
        "did": f"did:plc:{fake.word()}",
        "handle": f"{fake.word()}.bsky.social",
        "displayName": fake.name(),
        "avatar": fake.image_url()
    }
    reason = fake.random_element(elements=("mention", "reply", "quote", "repost", "like"))
    isRead = False
    indexedAt = fake.iso8601()


class ThreadFactory(Factory):
    """Factory for creating test threads."""
    
    class Meta:
        model = dict
    
    post = {
        "uri": fake.uri(),
        "cid": fake.sha256(),
        "author": {
            "did": f"did:plc:{fake.word()}",
            "handle": f"{fake.word()}.bsky.social",
            "displayName": fake.name()
        },
        "record": {
            "text": fake.text(max_nb_chars=300),
            "createdAt": fake.iso8601()
        },
        "replyCount": fake.random_int(min=0, max=10),
        "repostCount": fake.random_int(min=0, max=5),
        "likeCount": fake.random_int(min=0, max=20)
    }
    replies = []


# Pytest hooks
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Create reports directory
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add slow marker for tests that might take longer
        if "slow" in item.name or "benchmark" in item.name:
            item.add_marker(pytest.mark.slow)


def pytest_runtest_setup(item):
    """Set up test environment before each test."""
    # Ensure we're in the project root
    os.chdir(project_root)


def pytest_runtest_teardown(item):
    """Clean up after each test."""
    # Clean up any temporary files or state
    pass
