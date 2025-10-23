"""
Unit tests for enhanced session management functionality.

Tests the robust session management logic without requiring live API keys or real systems.
"""
import pytest
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import Dict, Any

# Import the functions we're testing
from platforms.bluesky.utils import (
    get_session_config,
    get_session_path,
    validate_session,
    get_session_with_retry,
    save_session_with_retry,
    cleanup_old_sessions,
    get_session,
    save_session
)


class TestSessionConfig:
    """Test session configuration management."""
    
    def test_get_session_config_defaults(self):
        """Test default configuration when no config file exists."""
        with patch('core.config.get_config', side_effect=Exception("No config")):
            config = get_session_config()
            
            assert config['directory'] == 'sessions'
            assert config['max_age_days'] == 30
            assert config['retry_attempts'] == 3
            assert config['retry_delay'] == 1.0
            assert config['validate_sessions'] == True
    
    def test_get_session_config_from_file(self):
        """Test configuration loaded from config file."""
        mock_config = {
            'session_management': {
                'directory': 'custom_sessions',
                'max_age_days': 7,
                'retry_attempts': 5,
                'retry_delay': 2.0,
                'validate_sessions': False
            }
        }
        
        with patch('core.config.get_config', return_value=mock_config):
            config = get_session_config()
            
            assert config['directory'] == 'custom_sessions'
            assert config['max_age_days'] == 7
            assert config['retry_attempts'] == 5
            assert config['retry_delay'] == 2.0
            assert config['validate_sessions'] == False


class TestSessionPath:
    """Test session path handling."""
    
    def test_get_session_path_default_directory(self):
        """Test session path with default directory."""
        with patch('os.getcwd', return_value='/test/dir'):
            path = get_session_path('test_user')
            
            assert path.name == 'session_test_user.txt'
            assert path.parent.name == 'dir'  # Current working directory name
    
    def test_get_session_path_custom_directory(self):
        """Test session path with custom directory."""
        path = get_session_path('test_user', 'custom_dir')
        
        assert path.name == 'session_test_user.txt'
        assert path.parent.name == 'custom_dir'
    
    def test_get_session_path_creates_directory(self, temp_dir):
        """Test that session path creates directory if it doesn't exist."""
        custom_dir = temp_dir / 'new_sessions'
        assert not custom_dir.exists()
        
        path = get_session_path('test_user', str(custom_dir))
        
        assert custom_dir.exists()
        assert path.parent == custom_dir


class TestSessionValidation:
    """Test session data validation."""
    
    def test_validate_session_valid_data(self):
        """Test validation with valid session data."""
        valid_session = {
            'accessJwt': 'valid_jwt_token',
            'refreshJwt': 'valid_refresh_token',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        }
        session_string = json.dumps(valid_session)
        
        assert validate_session(session_string) == True
    
    def test_validate_session_missing_fields(self):
        """Test validation with missing required fields."""
        invalid_session = {
            'accessJwt': 'valid_jwt_token',
            'handle': 'test.bsky.social'
            # Missing refreshJwt and did
        }
        session_string = json.dumps(invalid_session)
        
        assert validate_session(session_string) == False
    
    def test_validate_session_invalid_jwt(self):
        """Test validation with invalid JWT."""
        invalid_session = {
            'accessJwt': '',  # Empty JWT
            'refreshJwt': 'valid_refresh_token',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        }
        session_string = json.dumps(invalid_session)
        
        assert validate_session(session_string) == False
    
    def test_validate_session_invalid_json(self):
        """Test validation with invalid JSON."""
        invalid_json = "{ invalid json }"
        
        assert validate_session(invalid_json) == False
    
    def test_validate_session_empty_string(self):
        """Test validation with empty string."""
        assert validate_session('') == False
        assert validate_session(None) == False


class TestSessionRetryLogic:
    """Test session operations with retry logic."""
    
    def test_get_session_with_retry_success(self, temp_dir):
        """Test successful session retrieval with retry."""
        session_data = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        session_file = temp_dir / 'session_test_user.txt'
        session_file.write_text(session_data)
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'retry_attempts': 3, 'validate_sessions': True}):
            result = get_session_with_retry('test_user', session_dir=str(temp_dir))
            
            assert result == session_data
    
    def test_get_session_with_retry_file_not_found(self, temp_dir):
        """Test session retrieval when file doesn't exist."""
        with patch('platforms.bluesky.utils.get_session_config', return_value={'retry_attempts': 3, 'validate_sessions': True}):
            result = get_session_with_retry('nonexistent_user', session_dir=str(temp_dir))
            
            assert result is None
    
    def test_get_session_with_retry_permission_error(self, temp_dir):
        """Test session retrieval with permission errors."""
        session_file = temp_dir / 'session_test_user.txt'
        session_file.write_text('test_data')
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'retry_attempts': 2, 'retry_delay': 0.1, 'validate_sessions': True}):
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                result = get_session_with_retry('test_user', session_dir=str(temp_dir))
                
                assert result is None
    
    def test_save_session_with_retry_success(self, temp_dir):
        """Test successful session saving with retry."""
        session_data = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'retry_attempts': 3, 'validate_sessions': True}):
            result = save_session_with_retry('test_user', session_data, session_dir=str(temp_dir))
            
            assert result == True
            
            # Verify file was created
            session_file = temp_dir / 'session_test_user.txt'
            assert session_file.exists()
            assert session_file.read_text() == session_data
    
    def test_save_session_with_retry_permission_error(self, temp_dir):
        """Test session saving with permission errors."""
        session_data = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'retry_attempts': 2, 'retry_delay': 0.1, 'validate_sessions': True}):
            with patch('builtins.open', side_effect=PermissionError("Permission denied")):
                result = save_session_with_retry('test_user', session_data, session_dir=str(temp_dir))
                
                assert result == False
    
    def test_save_session_with_retry_invalid_data(self, temp_dir):
        """Test session saving with invalid session data."""
        invalid_session = "invalid session data"
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'retry_attempts': 3, 'validate_sessions': True}):
            result = save_session_with_retry('test_user', invalid_session, session_dir=str(temp_dir))
            
            assert result == False


class TestSessionCleanup:
    """Test session cleanup functionality."""
    
    def test_cleanup_old_sessions_no_files(self, temp_dir):
        """Test cleanup when no session files exist."""
        with patch('platforms.bluesky.utils.get_session_config', return_value={'max_age_days': 30, 'validate_sessions': True}):
            cleaned = cleanup_old_sessions(session_dir=str(temp_dir))
            
            assert cleaned == 0
    
    def test_cleanup_old_sessions_remove_old(self, temp_dir):
        """Test cleanup removes old session files."""
        # Create old session file
        old_session = temp_dir / 'session_old_user.txt'
        old_session.write_text('old_session_data')
        
        # Make file old by setting modification time using os.utime
        import os
        old_time = time.time() - (31 * 24 * 60 * 60)  # 31 days ago
        os.utime(old_session, (old_time, old_time))
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'max_age_days': 30, 'validate_sessions': True}):
            cleaned = cleanup_old_sessions(session_dir=str(temp_dir))
            
            assert cleaned == 1
            assert not old_session.exists()
    
    def test_cleanup_old_sessions_keep_recent(self, temp_dir):
        """Test cleanup keeps recent session files."""
        # Create recent session file with valid JSON
        recent_session = temp_dir / 'session_recent_user.txt'
        valid_session = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        recent_session.write_text(valid_session)
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'max_age_days': 30, 'validate_sessions': True}):
            cleaned = cleanup_old_sessions(session_dir=str(temp_dir))
            
            assert cleaned == 0
            assert recent_session.exists()
    
    def test_cleanup_old_sessions_remove_corrupted(self, temp_dir):
        """Test cleanup removes corrupted session files."""
        # Create corrupted session file
        corrupted_session = temp_dir / 'session_corrupted_user.txt'
        corrupted_session.write_text('corrupted_data')
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'max_age_days': 30, 'validate_sessions': True}):
            cleaned = cleanup_old_sessions(session_dir=str(temp_dir))
            
            assert cleaned == 1
            assert not corrupted_session.exists()
    
    def test_cleanup_old_sessions_mixed_files(self, temp_dir):
        """Test cleanup with mix of old, recent, and corrupted files."""
        # Create old file
        old_session = temp_dir / 'session_old_user.txt'
        old_session.write_text('old_session_data')
        import os
        old_time = time.time() - (31 * 24 * 60 * 60)
        os.utime(old_session, (old_time, old_time))
        
        # Create recent valid file
        recent_session = temp_dir / 'session_recent_user.txt'
        valid_session = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        recent_session.write_text(valid_session)
        
        # Create corrupted file
        corrupted_session = temp_dir / 'session_corrupted_user.txt'
        corrupted_session.write_text('corrupted_data')
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'max_age_days': 30, 'validate_sessions': True}):
            cleaned = cleanup_old_sessions(session_dir=str(temp_dir))
            
            assert cleaned == 2  # Old + corrupted
            assert not old_session.exists()
            assert not corrupted_session.exists()
            assert recent_session.exists()


class TestLegacySessionFunctions:
    """Test legacy session functions with enhanced error handling."""
    
    def test_get_session_legacy_success(self, temp_dir):
        """Test legacy get_session function with success."""
        session_data = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        session_file = temp_dir / 'session_test_user.txt'
        session_file.write_text(session_data)
        
        with patch('platforms.bluesky.utils.get_session_with_retry', return_value=session_data):
            result = get_session('test_user')
            
            assert result == session_data
    
    def test_get_session_legacy_error(self, temp_dir):
        """Test legacy get_session function with error."""
        with patch('platforms.bluesky.utils.get_session_with_retry', side_effect=Exception("Test error")):
            with patch('os.getcwd', return_value=str(temp_dir)):
                # Create a file to test fallback
                session_file = temp_dir / 'session_test_user.txt'
                session_file.write_text('test_session_data')
                
                result = get_session('test_user')
                assert result == 'test_session_data'
    
    def test_save_session_legacy_success(self, temp_dir):
        """Test legacy save_session function with success."""
        session_data = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        with patch('platforms.bluesky.utils.save_session_with_retry', return_value=True):
            # Should not raise exception
            save_session('test_user', session_data)
    
    def test_save_session_legacy_failure(self, temp_dir):
        """Test legacy save_session function with failure."""
        session_data = 'test_data'
        
        with patch('platforms.bluesky.utils.save_session_with_retry', return_value=False):
            with patch('os.getcwd', return_value=str(temp_dir)):
                # Should not raise exception because legacy fallback will work
                save_session('test_user', session_data)
                
                # Verify file was created by legacy method
                session_file = temp_dir / 'session_test_user.txt'
                assert session_file.exists()


class TestSessionErrorHandling:
    """Test comprehensive error handling scenarios."""
    
    def test_session_operations_with_various_errors(self, temp_dir):
        """Test session operations with various error conditions."""
        session_data = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        # Test OSError handling
        with patch('platforms.bluesky.utils.get_session_config', return_value={'retry_attempts': 2, 'retry_delay': 0.1, 'validate_sessions': True}):
            with patch('builtins.open', side_effect=OSError("Disk full")):
                result = save_session_with_retry('test_user', session_data, session_dir=str(temp_dir))
                assert result == False
        
        # Test UnicodeEncodeError handling
        with patch('platforms.bluesky.utils.get_session_config', return_value={'retry_attempts': 2, 'retry_delay': 0.1, 'validate_sessions': True}):
            with patch('builtins.open', side_effect=UnicodeEncodeError('utf-8', 'test', 0, 1, 'invalid')):
                result = save_session_with_retry('test_user', session_data, session_dir=str(temp_dir))
                assert result == False
    
    def test_session_cleanup_error_handling(self, temp_dir):
        """Test session cleanup error handling."""
        # Create a file that will cause errors during processing
        problematic_file = temp_dir / 'session_problematic_user.txt'
        problematic_file.write_text('test_data')
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'max_age_days': 30, 'validate_sessions': True}):
            # Mock the Path.exists() method to raise an error
            with patch('pathlib.Path.exists', side_effect=OSError("Permission denied")):
                cleaned = cleanup_old_sessions(session_dir=str(temp_dir))
                
                # Should handle error gracefully and return 0
                assert cleaned == 0


class TestSessionIntegration:
    """Integration tests for session management."""
    
    def test_full_session_lifecycle(self, temp_dir):
        """Test complete session lifecycle: create, validate, save, load, cleanup."""
        session_data = json.dumps({
            'accessJwt': 'valid_jwt_token',
            'refreshJwt': 'valid_refresh_token',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={
            'directory': str(temp_dir),
            'retry_attempts': 3,
            'validate_sessions': True,
            'max_age_days': 30
        }):
            with patch('os.getcwd', return_value=str(temp_dir)):
                # 1. Validate session data
                assert validate_session(session_data) == True
                
                # 2. Save session
                success = save_session_with_retry('test_user', session_data)
                assert success == True
                
                # 3. Load session
                loaded_data = get_session_with_retry('test_user')
                assert loaded_data == session_data
                
                # 4. Verify file exists
                session_file = temp_dir / 'session_test_user.txt'
                assert session_file.exists()
                
                # 5. Test cleanup (should not remove recent file)
                cleaned = cleanup_old_sessions()
                assert cleaned == 0
                assert session_file.exists()
    
    def test_session_retry_exponential_backoff(self, temp_dir):
        """Test that retry logic uses exponential backoff."""
        session_data = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        with patch('platforms.bluesky.utils.get_session_config', return_value={'retry_attempts': 3, 'retry_delay': 0.1, 'validate_sessions': True}):
            with patch('time.sleep') as mock_sleep:
                with patch('builtins.open', side_effect=OSError("Test error")):
                    result = save_session_with_retry('test_user', session_data, session_dir=str(temp_dir))
                    
                    assert result == False
                    # Should sleep with exponential backoff: 0.1, 0.2, 0.4
                    assert mock_sleep.call_count == 2  # 3 attempts = 2 sleeps
                    mock_sleep.assert_any_call(0.1)  # First retry
                    mock_sleep.assert_any_call(0.2)  # Second retry
