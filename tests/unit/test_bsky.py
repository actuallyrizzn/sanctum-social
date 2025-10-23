import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
from pathlib import Path
from datetime import datetime
import os

# Mock the config loading before importing bsky
with patch('core.config.get_config') as mock_get_config:
    mock_loader = mock_get_config.return_value
    mock_loader.get_required.side_effect = lambda key: {
        'letta.api_key': 'test-api-key',
        'letta.agent_id': 'test-agent-id'
    }.get(key)
    mock_loader.get.side_effect = lambda key, default=None: {
        'letta.timeout': 30,
        'letta.base_url': None
    }.get(key, default)
    
    from platforms.bluesky.orchestrator import (
        extract_handles_from_data,
        log_with_panel,
        export_agent_state,
        initialize_agent,
        notification_to_dict,
        load_processed_notifications,
        save_processed_notifications,
        save_notification_to_queue,
        FETCH_NOTIFICATIONS_DELAY_SEC,
        CHECK_NEW_NOTIFICATIONS_EVERY_N_ITEMS
    )


class TestExtractHandlesFromData:
    def test_extract_handles_simple_dict(self):
        """Test extracting handles from a simple dictionary."""
        data = {
            "author": {"handle": "test.user.bsky.social"},
            "post": {"text": "Hello world"}
        }
        handles = extract_handles_from_data(data)
        assert handles == ["test.user.bsky.social"]

    def test_extract_handles_nested_structure(self):
        """Test extracting handles from nested data structure."""
        data = {
            "notifications": [
                {
                    "author": {"handle": "user1.bsky.social"},
                    "parent": {
                        "author": {"handle": "user2.bsky.social"}
                    }
                },
                {
                    "author": {"handle": "user3.bsky.social"}
                }
            ]
        }
        handles = extract_handles_from_data(data)
        assert set(handles) == {"user1.bsky.social", "user2.bsky.social", "user3.bsky.social"}

    def test_extract_handles_no_handles(self):
        """Test extracting handles when no handles are present."""
        data = {"text": "Hello world", "timestamp": "2025-01-01T00:00:00Z"}
        handles = extract_handles_from_data(data)
        assert handles == []

    def test_extract_handles_empty_data(self):
        """Test extracting handles from empty data."""
        handles = extract_handles_from_data({})
        assert handles == []

    def test_extract_handles_list_of_dicts(self):
        """Test extracting handles from a list of dictionaries."""
        data = [
            {"author": {"handle": "user1.bsky.social"}},
            {"author": {"handle": "user2.bsky.social"}},
            {"text": "No handle here"}
        ]
        handles = extract_handles_from_data(data)
        assert set(handles) == {"user1.bsky.social", "user2.bsky.social"}


class TestLogWithPanel:
    def test_log_with_panel_title_and_message(self, capsys):
        """Test logging with title and message."""
        log_with_panel("Test message", "Test Title", "blue")
        captured = capsys.readouterr()
        assert "⚙ Test Title" in captured.out
        assert "Test message" in captured.out

    def test_log_with_panel_no_title(self, capsys):
        """Test logging without title."""
        log_with_panel("Simple message")
        captured = capsys.readouterr()
        assert "Simple message" in captured.out

    def test_log_with_panel_multiline_message(self, capsys):
        """Test logging with multiline message."""
        message = "Line 1\nLine 2\nLine 3"
        log_with_panel(message, "Multiline", "green")
        captured = capsys.readouterr()
        assert "✓ Multiline" in captured.out
        assert "Line 1" in captured.out
        assert "Line 2" in captured.out
        assert "Line 3" in captured.out

    def test_log_with_panel_color_symbols(self, capsys):
        """Test different color symbols."""
        colors = ["blue", "green", "yellow", "red", "white", "cyan"]
        expected_symbols = ["⚙", "✓", "◆", "✗", "▶", "✎"]
        
        for color, symbol in zip(colors, expected_symbols):
            log_with_panel("Test", "Title", color)
            captured = capsys.readouterr()
            assert f"{symbol} Title" in captured.out

    def test_log_with_panel_unknown_color(self, capsys):
        """Test logging with unknown color defaults to default symbol."""
        log_with_panel("Test", "Title", "unknown")
        captured = capsys.readouterr()
        assert "▶ Title" in captured.out


class TestExportAgentState:
    def test_export_agent_state_success(self, temp_dir):
        """Test successful agent state export."""
        mock_client = Mock()
        mock_agent = Mock()
        mock_agent.id = "test-agent-id"
        mock_agent.name = "test-agent"
        
        # Mock the agent data
        mock_client.agents.get.return_value = mock_agent
        mock_client.agents.list_blocks.return_value = []
        mock_client.agents.list_tools.return_value = []
        mock_client.agents.export_file.return_value = {"agent": "data"}
        
        with patch('platforms.bluesky.orchestrator.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_agent_data_dir.return_value = "data/agent"
            mock_config.get_file_paths_config.return_value = {"archive_dir": "data/agent/archive"}
            mock_config.get_archive_file_path.return_value = "data/agent/archive/test-agent_20240101_120000.af"
            mock_config.get_current_agent_file_path.return_value = "data/agent/current.af"
            mock_get_config.return_value = mock_config
            
            with patch('platforms.bluesky.orchestrator.logger') as mock_logger:
                mock_logger.info = Mock()
                mock_logger.error = Mock()
                
                with patch('platforms.bluesky.orchestrator.Path') as mock_path:
                    mock_path.return_value.exists.return_value = False
                    mock_path.return_value.mkdir.return_value = None
                    
                    with patch('builtins.open', mock_open()) as mock_file:
                        result = export_agent_state(mock_client, mock_agent, skip_git=True)
                        
                        assert result is None  # Function doesn't return anything
                        mock_client.agents.export_file.assert_called_once_with(agent_id="test-agent-id")

    def test_export_agent_state_agent_not_found(self):
        """Test export when agent is not found."""
        mock_client = Mock()
        mock_agent = Mock()
        mock_agent.id = "test-agent-id"
        
        mock_client.agents.get.side_effect = Exception("Agent not found")
        
        with patch('platforms.bluesky.orchestrator.logger') as mock_logger:
            mock_logger.info = Mock()
            mock_logger.error = Mock()
            
            result = export_agent_state(mock_client, mock_agent, skip_git=True)
            assert result is None  # Function doesn't return anything

    def test_export_agent_state_blocks_error(self):
        """Test export when listing blocks fails."""
        mock_client = Mock()
        mock_agent = Mock()
        mock_agent.id = "test-agent-id"
        
        mock_client.agents.get.return_value = mock_agent
        mock_client.agents.list_blocks.side_effect = Exception("Blocks error")
        
        with patch('platforms.bluesky.orchestrator.logger') as mock_logger:
            mock_logger.info = Mock()
            mock_logger.error = Mock()
            
            result = export_agent_state(mock_client, mock_agent, skip_git=True)
            assert result is None  # Function doesn't return anything


class TestInitializeAgent:
    def test_initialize_agent_success(self):
        """Test successful agent initialization."""
        mock_client = Mock()
        mock_agent = Mock()
        mock_agent.id = "test-agent-id"
        mock_agent.name = "test-agent"
        mock_agent.tools = []  # Add tools attribute with length
        mock_client.agents.retrieve.return_value = mock_agent
        
        with patch('platforms.bluesky.orchestrator.logger') as mock_logger, \
             patch('platforms.bluesky.orchestrator.get_letta_config', return_value={'api_key': 'test-key', 'agent_id': 'test-agent-id', 'timeout': 30}):
            mock_logger.info = Mock()
            mock_logger.error = Mock()
            
            with patch('platforms.bluesky.orchestrator.Letta', return_value=mock_client):
                result = initialize_agent()
                assert result == mock_agent
                mock_client.agents.retrieve.assert_called_once()

    def test_initialize_agent_agent_not_found(self):
        """Test initialization when agent is not found."""
        mock_client = Mock()
        mock_client.agents.retrieve.side_effect = Exception("Agent not found")
        
        with patch('platforms.bluesky.orchestrator.logger') as mock_logger, \
             patch('platforms.bluesky.orchestrator.get_letta_config', return_value={'api_key': 'test-key', 'agent_id': 'test-agent-id', 'timeout': 30}):
            mock_logger.info = Mock()
            mock_logger.error = Mock()
            
            with patch('platforms.bluesky.orchestrator.Letta', return_value=mock_client):
                with pytest.raises(Exception, match="Agent not found"):
                    initialize_agent()


class TestNotificationToDict:
    def test_notification_to_dict_complete(self):
        """Test converting complete notification to dictionary."""
        notification = Mock()
        notification.uri = "at://did:plc:test/app.bsky.notification.record/test"
        notification.cid = "test-cid"
        notification.reason = "mention"
        notification.is_read = False
        notification.indexed_at = "2025-01-01T00:00:00.000Z"
        notification.author.handle = "test.user.bsky.social"
        notification.author.display_name = "Test User"
        notification.author.did = "did:plc:test-author"
        notification.record.text = "Test notification"
        
        result = notification_to_dict(notification)
        
        assert result["uri"] == "at://did:plc:test/app.bsky.notification.record/test"
        assert result["cid"] == "test-cid"
        assert result["reason"] == "mention"
        assert result["is_read"] == False
        assert result["indexed_at"] == "2025-01-01T00:00:00.000Z"
        assert result["author"]["handle"] == "test.user.bsky.social"
        assert result["author"]["display_name"] == "Test User"
        assert result["author"]["did"] == "did:plc:test-author"
        assert result["record"]["text"] == "Test notification"

    def test_notification_to_dict_minimal(self):
        """Test converting minimal notification to dictionary."""
        notification = Mock()
        notification.uri = "at://did:plc:test/app.bsky.notification.record/test"
        notification.cid = "test-cid"
        notification.reason = "mention"
        notification.is_read = False
        notification.indexed_at = "2025-01-01T00:00:00.000Z"
        notification.author.handle = "test.user.bsky.social"
        notification.author.display_name = "Test User"
        notification.author.did = "did:plc:test-author"
        notification.record.text = "Test"
        
        result = notification_to_dict(notification)
        
        assert result["uri"] == "at://did:plc:test/app.bsky.notification.record/test"
        assert result["record"]["text"] == "Test"


class TestProcessedNotifications:
    def test_load_processed_notifications_file_exists(self, temp_dir):
        """Test loading processed notifications from database."""
        processed_data = {"uri1", "uri2", "uri3"}
        
        mock_db = Mock()
        mock_db.get_processed_uris.return_value = processed_data
        
        with patch('platforms.bluesky.orchestrator.NOTIFICATION_DB', mock_db):
            result = load_processed_notifications()
            assert result == processed_data
            mock_db.get_processed_uris.assert_called_once()

    def test_load_processed_notifications_file_not_exists(self, temp_dir):
        """Test loading processed notifications when database is None."""
        with patch('platforms.bluesky.orchestrator.NOTIFICATION_DB', None):
            result = load_processed_notifications()
            assert result == set()

    def test_save_processed_notifications(self, temp_dir):
        """Test saving processed notifications (no-op function)."""
        processed_data = {"uri1", "uri2", "uri3"}
        
        # This function is now a no-op, so we just test it doesn't raise an exception
        save_processed_notifications(processed_data)


class TestSaveNotificationToQueue:
    def test_save_notification_to_queue_success(self, temp_dir):
        """Test successfully saving notification to queue."""
        notification_data = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social"},
            "text": "Test notification",
            "reason": "mention"
        }
        
        queue_dir = temp_dir / "queue"
        queue_dir.mkdir()
        
        mock_db = Mock()
        mock_db.is_processed.return_value = False
        mock_db.add_notification.return_value = True
        
        with patch('platforms.bluesky.orchestrator.logger') as mock_logger:
            mock_logger.info = Mock()
            mock_logger.error = Mock()
            mock_logger.debug = Mock()
            mock_logger.warning = Mock()
            
            with patch('platforms.bluesky.orchestrator.QUEUE_DIR', queue_dir):
                with patch('platforms.bluesky.orchestrator.NOTIFICATION_DB', mock_db):
                    result = save_notification_to_queue(notification_data)
                    
                    assert result is True
                    # Check that a queue file was created
                    queue_files = list(queue_dir.glob("*.json"))
                    assert len(queue_files) == 1
                    
                    # Verify file contents
                    with open(queue_files[0], 'r') as f:
                        saved_data = json.load(f)
                        assert saved_data["uri"] == notification_data["uri"]

    def test_save_notification_to_queue_priority(self, temp_dir):
        """Test saving priority notification to queue."""
        notification_data = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "cameron.pfiffer.org"},  # This should be high priority
            "text": "Priority notification",
            "reason": "mention"
        }
        
        queue_dir = temp_dir / "queue"
        queue_dir.mkdir()
        
        mock_db = Mock()
        mock_db.is_processed.return_value = False
        mock_db.add_notification.return_value = True
        
        with patch('platforms.bluesky.orchestrator.logger') as mock_logger:
            mock_logger.info = Mock()
            mock_logger.error = Mock()
            mock_logger.debug = Mock()
            mock_logger.warning = Mock()
            
            with patch('platforms.bluesky.orchestrator.QUEUE_DIR', queue_dir):
                with patch('platforms.bluesky.orchestrator.NOTIFICATION_DB', mock_db):
                    result = save_notification_to_queue(notification_data, is_priority=True)
                    
                    assert result is True
                    # Check that a priority queue file was created (starts with 0_)
                    queue_files = list(queue_dir.glob("0_*.json"))
                    assert len(queue_files) == 1

    def test_save_notification_to_queue_error(self, temp_dir):
        """Test saving notification when queue directory doesn't exist."""
        notification_data = {
            "uri": "at://did:plc:test/app.bsky.notification.record/test",
            "indexed_at": "2025-01-01T00:00:00.000Z",
            "author": {"handle": "test.user.bsky.social"},
            "text": "Test notification",
            "reason": "mention"
        }
        
        # Use a non-existent directory
        queue_dir = temp_dir / "nonexistent_queue"
        
        mock_db = Mock()
        mock_db.is_processed.return_value = False
        mock_db.add_notification.return_value = True
        
        with patch('platforms.bluesky.orchestrator.logger') as mock_logger:
            mock_logger.info = Mock()
            mock_logger.error = Mock()
            mock_logger.debug = Mock()
            mock_logger.warning = Mock()
            
            with patch('platforms.bluesky.orchestrator.QUEUE_DIR', queue_dir):
                with patch('platforms.bluesky.orchestrator.NOTIFICATION_DB', mock_db):
                    result = save_notification_to_queue(notification_data)
                    
                    assert result is False


class TestConstants:
    def test_fetch_notifications_delay(self):
        """Test that fetch notifications delay is set correctly."""
        assert FETCH_NOTIFICATIONS_DELAY_SEC == 10

    def test_check_new_notifications_every_n_items(self):
        """Test that check new notifications frequency is set correctly."""
        assert CHECK_NEW_NOTIFICATIONS_EVERY_N_ITEMS == 2


# Helper function for mocking file operations
def mock_open():
    """Create a mock for file operations."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open()
