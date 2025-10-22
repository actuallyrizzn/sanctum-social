"""
Unit tests for enhanced queue management error handling functionality.

Tests the robust queue management logic without requiring live API keys or real systems.
"""
import pytest
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any

# Import the functions we're testing
from queue_manager import (
    QueueError,
    TransientQueueError,
    PermanentQueueError,
    QueueHealthError,
    retry_with_exponential_backoff,
    is_transient_error,
    classify_queue_error,
    log_queue_error,
    load_notification,
    save_notification,
    QueueMetrics,
    QueueHealthMonitor,
    repair_corrupted_queue_files,
    QUEUE_DIR,
    QUEUE_ERROR_DIR,
    QUEUE_NO_REPLY_DIR
)


class TestErrorClassification:
    """Test error classification system."""
    
    def test_queue_error_creation(self):
        """Test basic QueueError creation."""
        error = QueueError("Test error", Path("test.json"), "test_operation")
        
        assert error.message == "Test error"
        assert error.filepath == Path("test.json")
        assert error.operation == "test_operation"
        assert isinstance(error.timestamp, type(error.timestamp))
    
    def test_transient_queue_error(self):
        """Test TransientQueueError creation."""
        error = TransientQueueError("Transient error", Path("test.json"), "test_operation")
        
        assert isinstance(error, QueueError)
        assert error.message == "Transient error"
    
    def test_permanent_queue_error(self):
        """Test PermanentQueueError creation."""
        error = PermanentQueueError("Permanent error", Path("test.json"), "test_operation")
        
        assert isinstance(error, QueueError)
        assert error.message == "Permanent error"
    
    def test_queue_health_error(self):
        """Test QueueHealthError creation."""
        error = QueueHealthError("Health error", Path("test.json"), "test_operation")
        
        assert isinstance(error, QueueError)
        assert error.message == "Health error"


class TestErrorClassificationLogic:
    """Test error classification logic."""
    
    def test_classify_permission_error(self):
        """Test classification of permission errors."""
        error = PermissionError("Permission denied")
        classified = classify_queue_error(error, Path("test.json"), "test_op")
        
        assert isinstance(classified, TransientQueueError)
        assert "Permission error" in classified.message
    
    def test_classify_disk_full_error(self):
        """Test classification of disk full errors."""
        error = OSError("No space left on device")
        classified = classify_queue_error(error, Path("test.json"), "test_op")
        
        assert isinstance(classified, QueueHealthError)
        assert "Disk full" in classified.message
    
    def test_classify_json_decode_error(self):
        """Test classification of JSON decode errors."""
        error = json.JSONDecodeError("Invalid JSON", "doc", 0)
        classified = classify_queue_error(error, Path("test.json"), "test_op")
        
        assert isinstance(classified, PermanentQueueError)
        assert "Corrupted JSON" in classified.message
    
    def test_classify_connection_error(self):
        """Test classification of connection errors."""
        error = ConnectionError("Connection failed")
        classified = classify_queue_error(error, Path("test.json"), "test_op")
        
        assert isinstance(classified, TransientQueueError)
        assert "Network error" in classified.message
    
    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        error = TimeoutError("Operation timed out")
        classified = classify_queue_error(error, Path("test.json"), "test_op")
        
        assert isinstance(classified, TransientQueueError)
        assert "Network error" in classified.message
    
    def test_classify_unknown_error(self):
        """Test classification of unknown errors."""
        error = ValueError("Unknown error")
        classified = classify_queue_error(error, Path("test.json"), "test_op")
        
        assert isinstance(classified, QueueError)
        assert "Unknown error" in classified.message


class TestTransientErrorDetection:
    """Test transient error detection logic."""
    
    def test_is_transient_error_permission(self):
        """Test permission error detection."""
        error = PermissionError("Permission denied")
        assert is_transient_error(error) == True
    
    def test_is_transient_error_os_error(self):
        """Test OSError detection."""
        error = OSError("File system error")
        assert is_transient_error(error) == True
    
    def test_is_transient_error_json_decode(self):
        """Test JSON decode error detection."""
        error = json.JSONDecodeError("Invalid JSON", "doc", 0)
        assert is_transient_error(error) == True
    
    def test_is_transient_error_connection(self):
        """Test connection error detection."""
        error = ConnectionError("Connection failed")
        assert is_transient_error(error) == True
    
    def test_is_transient_error_timeout(self):
        """Test timeout error detection."""
        error = TimeoutError("Operation timed out")
        assert is_transient_error(error) == True
    
    def test_is_not_transient_error_value(self):
        """Test that ValueError is not transient."""
        error = ValueError("Invalid value")
        assert is_transient_error(error) == False
    
    def test_is_not_transient_error_key(self):
        """Test that KeyError is not transient."""
        error = KeyError("Missing key")
        assert is_transient_error(error) == False


class TestRetryLogic:
    """Test retry logic with exponential backoff."""
    
    def test_retry_success_first_attempt(self):
        """Test retry logic when function succeeds on first attempt."""
        @retry_with_exponential_backoff(max_retries=3)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_retry_success_after_failures(self):
        """Test retry logic when function succeeds after failures."""
        call_count = 0
        
        @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise PermissionError("Temporary failure")
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_max_attempts_exceeded(self):
        """Test retry logic when max attempts are exceeded."""
        @retry_with_exponential_backoff(max_retries=2, base_delay=0.01)
        def test_func():
            raise PermissionError("Persistent failure")
        
        with pytest.raises(PermissionError, match="Persistent failure"):
            test_func()
    
    def test_retry_permanent_error_no_retry(self):
        """Test that permanent errors are not retried."""
        call_count = 0
        
        @retry_with_exponential_backoff(max_retries=3, base_delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError, match="Permanent error"):
            test_func()
        
        assert call_count == 1  # Should not retry permanent errors
    
    def test_retry_exponential_backoff_timing(self):
        """Test that retry delays follow exponential backoff."""
        call_times = []
        
        @retry_with_exponential_backoff(max_retries=3, base_delay=0.1)
        def test_func():
            call_times.append(time.time())
            raise PermissionError("Temporary failure")
        
        start_time = time.time()
        with pytest.raises(PermissionError):
            test_func()
        
        # Check that delays increase exponentially
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            
            # Allow some tolerance for timing
            assert delay1 >= 0.05  # Should be around 0.1
            assert delay2 >= 0.15  # Should be around 0.2


class TestQueueOperations:
    """Test enhanced queue operations."""
    
    def test_load_notification_success(self, temp_dir):
        """Test successful notification loading."""
        notification_data = {
            "uri": "at://test.bsky.social/post/123",
            "text": "Test notification",
            "author": {"handle": "test.user.bsky.social"}
        }
        
        notification_file = temp_dir / "test_notification.json"
        with open(notification_file, 'w', encoding='utf-8') as f:
            json.dump(notification_data, f)
        
        result = load_notification(notification_file)
        assert result == notification_data
    
    def test_load_notification_file_not_found(self, temp_dir):
        """Test loading notification from non-existent file."""
        non_existent_file = temp_dir / "non_existent.json"
        
        with pytest.raises(QueueError):
            load_notification(non_existent_file)
    
    def test_load_notification_corrupted_json(self, temp_dir):
        """Test loading corrupted JSON file."""
        corrupted_file = temp_dir / "corrupted.json"
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(PermanentQueueError):
            load_notification(corrupted_file)
    
    def test_save_notification_success(self, temp_dir):
        """Test successful notification saving."""
        notification_data = {
            "uri": "at://test.bsky.social/post/123",
            "text": "Test notification",
            "author": {"handle": "test.user.bsky.social"}
        }
        
        notification_file = temp_dir / "test_notification.json"
        result = save_notification(notification_data, notification_file)
        
        assert result == True
        assert notification_file.exists()
        
        with open(notification_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        assert loaded_data == notification_data
    
    def test_save_notification_permission_error(self, temp_dir):
        """Test saving notification with permission error."""
        notification_data = {"test": "data"}
        notification_file = temp_dir / "test_notification.json"
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(TransientQueueError):
                save_notification(notification_data, notification_file)
    
    def test_save_notification_disk_full(self, temp_dir):
        """Test saving notification with disk full error."""
        notification_data = {"test": "data"}
        notification_file = temp_dir / "test_notification.json"
        
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            with pytest.raises(QueueHealthError):
                save_notification(notification_data, notification_file)


class TestQueueHealthMonitoring:
    """Test queue health monitoring system."""
    
    def test_queue_metrics_creation(self):
        """Test QueueMetrics creation."""
        metrics = QueueMetrics()
        
        assert metrics.queue_size == 0
        assert metrics.error_size == 0
        assert metrics.no_reply_size == 0
        assert metrics.total_size == 0
        assert metrics.unique_handles == 0
        assert metrics.error_rate == 0.0
        assert metrics.processing_rate == 0.0
        assert isinstance(metrics.timestamp, type(metrics.timestamp))
    
    def test_queue_health_monitor_creation(self):
        """Test QueueHealthMonitor creation."""
        monitor = QueueHealthMonitor()
        
        assert monitor.metrics_history == []
        assert monitor.max_history == 100
    
    def test_get_queue_metrics_empty_queue(self, temp_dir):
        """Test getting metrics from empty queue."""
        with patch('queue_manager.QUEUE_DIR', temp_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', temp_dir / "errors"), \
             patch('queue_manager.QUEUE_NO_REPLY_DIR', temp_dir / "no_reply"):
            
            monitor = QueueHealthMonitor()
            metrics = monitor.get_queue_metrics()
            
            assert metrics.queue_size == 0
            assert metrics.error_size == 0
            assert metrics.no_reply_size == 0
            assert metrics.total_size == 0
            assert metrics.error_rate == 0.0
    
    def test_get_queue_metrics_with_files(self, temp_dir):
        """Test getting metrics with queue files."""
        # Create test files
        queue_dir = temp_dir / "queue"
        error_dir = temp_dir / "errors"
        no_reply_dir = temp_dir / "no_reply"
        
        queue_dir.mkdir()
        error_dir.mkdir()
        no_reply_dir.mkdir()
        
        # Create test notifications
        for i in range(3):
            notification = {
                "uri": f"at://test.bsky.social/post/{i}",
                "author": {"handle": f"user{i}.bsky.social"},
                "text": f"Test notification {i}"
            }
            
            with open(queue_dir / f"notif_{i}.json", 'w', encoding='utf-8') as f:
                json.dump(notification, f)
        
        # Create error file
        error_notification = {
            "uri": "at://test.bsky.social/post/error",
            "author": {"handle": "error.user.bsky.social"},
            "text": "Error notification"
        }
        
        with open(error_dir / "error.json", 'w', encoding='utf-8') as f:
            json.dump(error_notification, f)
        
        with patch('queue_manager.QUEUE_DIR', queue_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', error_dir), \
             patch('queue_manager.QUEUE_NO_REPLY_DIR', no_reply_dir):
            
            monitor = QueueHealthMonitor()
            metrics = monitor.get_queue_metrics()
            
            assert metrics.queue_size == 3
            assert metrics.error_size == 1
            assert metrics.no_reply_size == 0
            assert metrics.total_size == 4
            assert metrics.error_rate == 0.25  # 1/4 = 25%
    
    def test_check_queue_health_healthy(self, temp_dir):
        """Test queue health check for healthy queue."""
        with patch('queue_manager.QUEUE_DIR', temp_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', temp_dir / "errors"), \
             patch('queue_manager.QUEUE_NO_REPLY_DIR', temp_dir / "no_reply"):
            
            monitor = QueueHealthMonitor()
            health = monitor.check_queue_health()
            
            assert health == "HEALTHY"
    
    def test_check_queue_health_critical(self, temp_dir):
        """Test queue health check for critical queue."""
        error_dir = temp_dir / "errors"
        error_dir.mkdir()
        
        # Create error files to simulate critical state
        for i in range(10):
            notification = {
                "uri": f"at://test.bsky.social/post/{i}",
                "author": {"handle": f"user{i}.bsky.social"},
                "text": f"Error notification {i}"
            }
            
            with open(error_dir / f"error_{i}.json", 'w', encoding='utf-8') as f:
                json.dump(notification, f)
        
        with patch('queue_manager.QUEUE_DIR', temp_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', error_dir), \
             patch('queue_manager.QUEUE_NO_REPLY_DIR', temp_dir / "no_reply"):
            
            monitor = QueueHealthMonitor()
            health = monitor.check_queue_health()
            
            assert health == "CRITICAL"
    
    def test_detect_queue_backlog(self, temp_dir):
        """Test queue backlog detection."""
        with patch('queue_manager.QUEUE_DIR', temp_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', temp_dir / "errors"), \
             patch('queue_manager.QUEUE_NO_REPLY_DIR', temp_dir / "no_reply"):
            
            monitor = QueueHealthMonitor()
            
            # Add metrics with increasing queue size
            for i in range(5):
                metrics = QueueMetrics()
                metrics.queue_size = i * 10
                monitor.metrics_history.append(metrics)
            
            backlog = monitor.detect_queue_backlog()
            assert backlog == True
    
    def test_get_queue_size_trend(self, temp_dir):
        """Test queue size trend detection."""
        with patch('queue_manager.QUEUE_DIR', temp_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', temp_dir / "errors"), \
             patch('queue_manager.QUEUE_NO_REPLY_DIR', temp_dir / "no_reply"):
            
            monitor = QueueHealthMonitor()
            
            # Add metrics with increasing size
            metrics1 = QueueMetrics()
            metrics1.queue_size = 100
            monitor.metrics_history.append(metrics1)
            
            metrics2 = QueueMetrics()
            metrics2.queue_size = 120  # 20% increase
            monitor.metrics_history.append(metrics2)
            
            trend = monitor.get_queue_size_trend()
            assert trend == "increasing"


class TestQueueRepair:
    """Test queue repair functionality."""
    
    def test_repair_corrupted_files_none_found(self, temp_dir):
        """Test repair when no corrupted files are found."""
        # Create valid JSON files
        for i in range(3):
            notification = {
                "uri": f"at://test.bsky.social/post/{i}",
                "author": {"handle": f"user{i}.bsky.social"},
                "text": f"Valid notification {i}"
            }
            
            with open(temp_dir / f"valid_{i}.json", 'w', encoding='utf-8') as f:
                json.dump(notification, f)
        
        with patch('queue_manager.QUEUE_DIR', temp_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', temp_dir / "errors"):
            
            stats = repair_corrupted_queue_files()
            
            assert stats["scanned"] == 3
            assert stats["corrupted"] == 0
            assert stats["repaired"] == 0
            assert stats["moved_to_errors"] == 0
    
    def test_repair_corrupted_files_success(self, temp_dir):
        """Test repair of corrupted files."""
        # Create a corrupted JSON file
        corrupted_file = temp_dir / "corrupted.json"
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write('{"uri": "at://test.bsky.social/post/123", "text": "Test notification"}')  # Valid JSON
        
        # Corrupt it by adding invalid characters
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write('{"uri": "at://test.bsky.social/post/123", "text": "Test notification"\x00}')  # Invalid JSON
        
        with patch('queue_manager.QUEUE_DIR', temp_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', temp_dir / "errors"):
            
            stats = repair_corrupted_queue_files()
            
            assert stats["scanned"] == 1
            assert stats["corrupted"] == 1
            assert stats["repaired"] == 1
            assert stats["moved_to_errors"] == 0
    
    def test_repair_corrupted_files_unrecoverable(self, temp_dir):
        """Test repair of unrecoverable corrupted files."""
        # Create an unrecoverable corrupted file
        corrupted_file = temp_dir / "unrecoverable.json"
        with open(corrupted_file, 'w', encoding='utf-8') as f:
            f.write('completely invalid json content')
        
        with patch('queue_manager.QUEUE_DIR', temp_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', temp_dir / "errors"):
            
            stats = repair_corrupted_queue_files()
            
            assert stats["scanned"] == 1
            assert stats["corrupted"] == 1
            assert stats["repaired"] == 0
            assert stats["moved_to_errors"] == 1


class TestErrorLogging:
    """Test error logging functionality."""
    
    def test_log_queue_error_transient(self, caplog):
        """Test logging transient queue errors."""
        error = TransientQueueError("Test transient error", Path("test.json"), "test_op")
        
        log_queue_error(error, {"context": "test"})
        
        assert "Transient queue error" in caplog.text
        assert "Test transient error" in caplog.text
    
    def test_log_queue_error_permanent(self, caplog):
        """Test logging permanent queue errors."""
        error = PermanentQueueError("Test permanent error", Path("test.json"), "test_op")
        
        log_queue_error(error, {"context": "test"})
        
        assert "Permanent queue error" in caplog.text
        assert "Test permanent error" in caplog.text
    
    def test_log_queue_error_health(self, caplog):
        """Test logging queue health errors."""
        error = QueueHealthError("Test health error", Path("test.json"), "test_op")
        
        log_queue_error(error, {"context": "test"})
        
        assert "Queue health error" in caplog.text
        assert "Test health error" in caplog.text


class TestIntegration:
    """Integration tests for queue management."""
    
    def test_full_queue_lifecycle(self, temp_dir):
        """Test complete queue lifecycle with error handling."""
        queue_dir = temp_dir / "queue"
        queue_dir.mkdir()
        
        with patch('queue_manager.QUEUE_DIR', queue_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', temp_dir / "errors"), \
             patch('queue_manager.QUEUE_NO_REPLY_DIR', temp_dir / "no_reply"):
            
            # 1. Save notification
            notification = {
                "uri": "at://test.bsky.social/post/123",
                "text": "Test notification",
                "author": {"handle": "test.user.bsky.social"}
            }
            
            notification_file = queue_dir / "test_notification.json"
            result = save_notification(notification, notification_file)
            assert result == True
            assert notification_file.exists()
            
            # 2. Load notification
            loaded_notification = load_notification(notification_file)
            assert loaded_notification == notification
            
            # 3. Check queue health
            monitor = QueueHealthMonitor()
            metrics = monitor.get_queue_metrics()
            assert metrics.queue_size == 1
            assert metrics.total_size == 1
            assert metrics.error_rate == 0.0
            
            health = monitor.check_queue_health()
            assert health == "HEALTHY"
    
    def test_error_recovery_workflow(self, temp_dir):
        """Test error recovery workflow."""
        queue_dir = temp_dir / "queue"
        error_dir = temp_dir / "errors"
        queue_dir.mkdir()
        error_dir.mkdir()
        
        with patch('queue_manager.QUEUE_DIR', queue_dir), \
             patch('queue_manager.QUEUE_ERROR_DIR', error_dir), \
             patch('queue_manager.QUEUE_NO_REPLY_DIR', temp_dir / "no_reply"):
            
            # 1. Create corrupted file
            corrupted_file = queue_dir / "corrupted.json"
            with open(corrupted_file, 'w', encoding='utf-8') as f:
                f.write('{"uri": "at://test.bsky.social/post/123", "text": "Test notification"\x00}')
            
            # 2. Try to load corrupted file (should move to error directory)
            with pytest.raises(PermanentQueueError):
                load_notification(corrupted_file)
            
            # 3. Check that file was moved to error directory
            error_file = error_dir / "corrupted.json"
            assert error_file.exists()
            assert not corrupted_file.exists()
            
            # 4. Check queue health
            monitor = QueueHealthMonitor()
            metrics = monitor.get_queue_metrics()
            assert metrics.queue_size == 0
            assert metrics.error_size == 1
            assert metrics.error_rate == 1.0
            
            health = monitor.check_queue_health()
            assert health == "CRITICAL"
            
            # 5. Repair corrupted file (now in error directory)
            stats = repair_corrupted_queue_files(error_dir)
            assert stats["scanned"] == 1
            assert stats["corrupted"] == 1
            assert stats["repaired"] == 1
