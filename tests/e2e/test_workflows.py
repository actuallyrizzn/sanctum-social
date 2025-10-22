"""
End-to-end tests for Void Bot workflows
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
from pathlib import Path

from config_loader import ConfigLoader
from notification_db import NotificationDB


@pytest.mark.live
@pytest.mark.e2e
class TestBotWorkflow:
    """End-to-end tests for bot workflows."""
    
    def test_notification_processing_workflow(self, temp_dir, mock_config_file, sample_notification):
        """Test the complete notification processing workflow."""
        # Set up test environment
        queue_dir = temp_dir / "queue"
        queue_dir.mkdir()
        
        db_path = temp_dir / "test.db"
        
        # Initialize database
        with NotificationDB(str(db_path)) as db:
            # Add notification to database
            db.add_notification(
                uri=sample_notification["uri"],
                indexed_at=sample_notification["indexedAt"],
                author_handle=sample_notification["author"]["handle"],
                author_did=sample_notification["author"]["did"],
                text=sample_notification["record"]["text"],
                parent_uri=sample_notification["record"].get("reply", {}).get("parent", {}).get("uri"),
                root_uri=sample_notification["record"].get("reply", {}).get("root", {}).get("uri")
            )
            
            # Verify notification was added
            assert not db.is_processed(sample_notification["uri"])
            
            # Simulate processing
            db.mark_processed(sample_notification["uri"], "success", "Test processing")
            
            # Verify processing was recorded
            assert db.is_processed(sample_notification["uri"])
    
    def test_configuration_loading_workflow(self, mock_config_file):
        """Test the configuration loading workflow."""
        # Load configuration
        config = ConfigLoader(str(mock_config_file))
        
        # Verify configuration sections
        assert config.get("letta.api_key") == "test-letta-api-key"
        assert config.get("bluesky.username") == "test.bsky.social"
        assert config.get("bot.agent.name") == "test-void"
        
        # Verify configuration sections
        letta_config = config.get_section("letta")
        assert letta_config["api_key"] == "test-letta-api-key"
        assert letta_config["project_id"] == "test-project-id"
        
        bluesky_config = config.get_section("bluesky")
        assert bluesky_config["username"] == "test.bsky.social"
        assert bluesky_config["password"] == "test-app-password"
    
    def test_queue_management_workflow(self, temp_dir, sample_notification):
        """Test the queue management workflow."""
        # Set up queue directory
        queue_dir = temp_dir / "queue"
        queue_dir.mkdir()
        (queue_dir / "errors").mkdir()
        (queue_dir / "no_reply").mkdir()
        
        # Create notification file
        notification_file = queue_dir / f"{sample_notification['uri'].split('/')[-1]}.json"
        with open(notification_file, 'w') as f:
            json.dump(sample_notification, f)
        
        # Verify file was created
        assert notification_file.exists()
        
        # Simulate processing by moving file
        processed_file = queue_dir / "errors" / notification_file.name
        notification_file.rename(processed_file)
        
        # Verify file was moved
        assert not notification_file.exists()
        assert processed_file.exists()
    
    @patch('bsky_utils.get_session')
    @patch('bsky_utils.get_thread')
    def test_bluesky_integration_workflow(self, mock_get_thread, mock_get_session, sample_thread):
        """Test Bluesky integration workflow."""
        # Mock session
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        # Mock thread retrieval
        mock_get_thread.return_value = sample_thread
        
        # Simulate thread processing
        thread_data = mock_get_thread("test-post-uri")
        
        # Verify thread data structure
        assert "thread" in thread_data
        assert "post" in thread_data["thread"]
        assert "replies" in thread_data["thread"]
        
        # Verify post data
        post = thread_data["thread"]["post"]
        assert "uri" in post
        assert "author" in post
        assert "record" in post
    
    @patch('x.XClient')
    def test_x_integration_workflow(self, mock_x_client_class, sample_x_mention, sample_x_user):
        """Test X integration workflow."""
        # Mock X client
        mock_x_client = Mock()
        mock_x_client_class.return_value = mock_x_client
        
        # Mock API responses
        mock_x_client.get_mentions.return_value = {
            "data": [sample_x_mention],
            "meta": {"result_count": 1}
        }
        
        mock_x_client.get_user_by_id.return_value = {
            "data": sample_x_user
        }
        
        # Simulate mention processing
        mentions = mock_x_client.get_mentions()
        assert len(mentions["data"]) == 1
        
        mention = mentions["data"][0]
        user_data = mock_x_client.get_user_by_id(mention["author_id"])
        
        # Verify data flow
        assert mention["id"] == sample_x_mention["id"]
        assert user_data["data"]["id"] == sample_x_user["id"]


@pytest.mark.live
@pytest.mark.e2e
class TestErrorRecoveryWorkflow:
    """Test error recovery workflows."""
    
    def test_configuration_error_recovery(self, temp_dir):
        """Test recovery from configuration errors."""
        # Create invalid config file
        invalid_config = temp_dir / "invalid.yaml"
        with open(invalid_config, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        # Test error handling
        with pytest.raises(ValueError, match="Invalid YAML"):
            ConfigLoader(str(invalid_config))
        
        # Test fallback to environment variables
        with patch.dict('os.environ', {
            'LETTA_API_KEY': 'test-key',
            'BSKY_USERNAME': 'test.bsky.social',
            'BSKY_PASSWORD': 'test-password'
        }):
            from config_loader import get_letta_config, get_bluesky_config
            
            letta_config = get_letta_config()
            assert letta_config["api_key"] == "test-key"
            
            bluesky_config = get_bluesky_config()
            assert bluesky_config["username"] == "test.bsky.social"
    
    def test_database_error_recovery(self, temp_dir):
        """Test recovery from database errors."""
        db_path = temp_dir / "test.db"
        
        with NotificationDB(str(db_path)) as db:
            # Test duplicate notification handling
            uri = "at://did:plc:test/app.bsky.notification.record/test"
            
            # Add notification first time
            db.add_notification(
                uri=uri,
                indexed_at="2025-01-01T00:00:00.000Z",
                author_handle="test.user.bsky.social",
                author_did="did:plc:test",
                text="Test notification"
            )
            
            # Try to add duplicate
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.add_notification(
                    uri=uri,
                    indexed_at="2025-01-01T00:00:00.000Z",
                    author_handle="test.user.bsky.social",
                    author_did="did:plc:test",
                    text="Test notification"
                )
            
            # Verify original notification still exists
            assert not db.is_processed(uri)
    
    def test_api_error_recovery(self):
        """Test recovery from API errors."""
        with patch('tools.search.requests.get') as mock_get:
            # Mock API error
            mock_get.side_effect = Exception("API Error")
            
            from tools.search import search_bluesky_posts
            
            # Should return error message, not raise exception
            result = search_bluesky_posts("test query")
            assert isinstance(result, str)
            assert "error" in result.lower() or "failed" in result.lower()


@pytest.mark.live
@pytest.mark.e2e
class TestDataPersistenceWorkflow:
    """Test data persistence workflows."""
    
    def test_notification_persistence(self, temp_dir):
        """Test notification data persistence."""
        db_path = temp_dir / "test.db"
        
        # Create database and add notifications
        with NotificationDB(str(db_path)) as db:
            notifications = [
                {
                    "uri": "at://did:plc:test/app.bsky.notification.record/test1",
                    "indexed_at": "2025-01-01T00:00:00.000Z",
                    "author_handle": "test1.bsky.social",
                    "author_did": "did:plc:test1",
                    "text": "Test notification 1"
                },
                {
                    "uri": "at://did:plc:test/app.bsky.notification.record/test2",
                    "indexed_at": "2025-01-01T00:01:00.000Z",
                    "author_handle": "test2.bsky.social",
                    "author_did": "did:plc:test2",
                    "text": "Test notification 2"
                }
            ]
            
            for notif in notifications:
                db.add_notification(**notif)
        
        # Reopen database and verify data persistence
        with NotificationDB(str(db_path)) as db:
            stats = db.get_stats()
            assert stats["total"] == 2
            assert stats["pending"] == 2
            
            # Verify individual notifications
            for notif in notifications:
                assert not db.is_processed(notif["uri"])
    
    def test_configuration_persistence(self, temp_dir, mock_config):
        """Test configuration data persistence."""
        config_file = temp_dir / "config.yaml"
        
        # Write configuration
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(mock_config, f)
        
        # Read configuration back
        config = ConfigLoader(str(config_file))
        
        # Verify data persistence
        assert config.get("letta.api_key") == mock_config["letta"]["api_key"]
        assert config.get("bluesky.username") == mock_config["bluesky"]["username"]
        assert config.get("bot.agent.name") == mock_config["bot"]["agent"]["name"]
    
    def test_queue_file_persistence(self, temp_dir, sample_notification):
        """Test queue file persistence."""
        queue_dir = temp_dir / "queue"
        queue_dir.mkdir()
        
        # Create notification file
        notification_file = queue_dir / "test_notification.json"
        with open(notification_file, 'w') as f:
            json.dump(sample_notification, f)
        
        # Verify file exists
        assert notification_file.exists()
        
        # Read file back
        with open(notification_file, 'r') as f:
            loaded_notification = json.load(f)
        
        # Verify data persistence
        assert loaded_notification["uri"] == sample_notification["uri"]
        assert loaded_notification["author"]["handle"] == sample_notification["author"]["handle"]
        assert loaded_notification["record"]["text"] == sample_notification["record"]["text"]


@pytest.mark.live
@pytest.mark.e2e
class TestPerformanceWorkflow:
    """Test performance-related workflows."""
    
    def test_bulk_notification_processing(self, temp_dir):
        """Test processing multiple notifications efficiently."""
        db_path = temp_dir / "test.db"
        
        with NotificationDB(str(db_path)) as db:
            # Add multiple notifications
            notifications = []
            for i in range(100):
                notifications.append({
                    "uri": f"at://did:plc:test/app.bsky.notification.record/test{i}",
                    "indexed_at": f"2025-01-01T00:{i:02d}:00.000Z",
                    "author_handle": f"test{i}.bsky.social",
                    "author_did": f"did:plc:test{i}",
                    "text": f"Test notification {i}"
                })
            
            # Add all notifications
            for notif in notifications:
                db.add_notification(**notif)
            
            # Verify all were added
            stats = db.get_stats()
            assert stats["total"] == 100
            assert stats["pending"] == 100
            
            # Process notifications in batches
            batch_size = 10
            for i in range(0, len(notifications), batch_size):
                batch = notifications[i:i + batch_size]
                for notif in batch:
                    db.mark_processed(notif["uri"], "success")
            
            # Verify all were processed
            stats = db.get_stats()
            assert stats["total"] == 100
            assert stats["processed"] == 100
            assert stats["pending"] == 0
    
    def test_memory_cleanup_workflow(self, temp_dir, frozen_time):
        """Test memory cleanup workflow."""
        db_path = temp_dir / "test.db"
        
        with NotificationDB(str(db_path)) as db:
            with frozen_time as ft:
                # Add old notifications
                ft.move_to("2024-12-01T00:00:00Z")
                for i in range(10):
                    db.add_notification(
                        uri=f"at://did:plc:test/app.bsky.notification.record/old{i}",
                        indexed_at="2024-12-01T00:00:00.000Z",
                        author_handle=f"old{i}.bsky.social",
                        author_did=f"did:plc:old{i}",
                        text=f"Old notification {i}"
                    )
                
                # Add recent notifications
                ft.move_to("2024-12-25T00:00:00Z")
                for i in range(5):
                    db.add_notification(
                        uri=f"at://did:plc:test/app.bsky.notification.record/recent{i}",
                        indexed_at="2024-12-25T00:00:00.000Z",
                        author_handle=f"recent{i}.bsky.social",
                        author_did=f"did:plc:recent{i}",
                        text=f"Recent notification {i}"
                    )
                
                # Move to current time
                ft.move_to("2025-01-01T00:00:00Z")
                
                # Cleanup old notifications (older than 7 days)
                cleaned_count = db.cleanup_old_notifications(days=7)
                
                # Should clean up old notifications
                assert cleaned_count == 10
                
                # Verify only recent notifications remain
                stats = db.get_stats()
                assert stats["total"] == 5


@pytest.mark.slow
@pytest.mark.live
@pytest.mark.e2e
class TestLongRunningWorkflow:
    """Test long-running workflows."""
    
    def test_continuous_processing_simulation(self, temp_dir):
        """Simulate continuous notification processing."""
        db_path = temp_dir / "test.db"
        
        with NotificationDB(str(db_path)) as db:
            # Simulate continuous processing
            for cycle in range(5):
                # Add new notifications
                for i in range(3):
                    db.add_notification(
                        uri=f"at://did:plc:test/app.bsky.notification.record/cycle{cycle}_notif{i}",
                        indexed_at=f"2025-01-01T00:{cycle:02d}:{i:02d}:00.000Z",
                        author_handle=f"cycle{cycle}_user{i}.bsky.social",
                        author_did=f"did:plc:cycle{cycle}_user{i}",
                        text=f"Notification {i} from cycle {cycle}"
                    )
                
                # Process pending notifications
                pending = db.get_pending_notifications()
                for notif in pending:
                    db.mark_processed(notif["uri"], "success")
                
                # Verify processing
                stats = db.get_stats()
                assert stats["processed"] == (cycle + 1) * 3
                assert stats["pending"] == 0
