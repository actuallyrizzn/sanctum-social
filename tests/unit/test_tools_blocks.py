import pytest
from unittest.mock import Mock, patch
from tools.blocks import (
    get_letta_client,
    get_x_letta_client,
    get_platform_letta_client,
    AttachUserBlocksArgs,
    DetachUserBlocksArgs,
    UserNoteAppendArgs,
    UserNoteReplaceArgs,
    UserNoteSetArgs,
    UserNoteViewArgs,
    AttachXUserBlocksArgs,
    DetachXUserBlocksArgs,
    XUserNoteAppendArgs
)


class TestGetLettaClient:
    def test_get_letta_client_with_config(self):
        """Test getting Letta client with config file."""
        with patch('tools.blocks.get_letta_config') as mock_config:
            mock_config.return_value = {
                'api_key': 'test-api-key',
                'timeout': 30,
                'base_url': 'https://api.example.com'
            }
            
            with patch('tools.blocks.Letta') as mock_letta:
                mock_client = Mock()
                mock_letta.return_value = mock_client
                
                result = get_letta_client()
                
                assert result == mock_client
                mock_letta.assert_called_once_with(
                    token='test-api-key',
                    timeout=30,
                    base_url='https://api.example.com'
                )

    def test_get_letta_client_without_base_url(self):
        """Test getting Letta client without base_url."""
        with patch('tools.blocks.get_letta_config') as mock_config:
            mock_config.return_value = {
                'api_key': 'test-api-key',
                'timeout': 30
            }
            
            with patch('tools.blocks.Letta') as mock_letta:
                mock_client = Mock()
                mock_letta.return_value = mock_client
                
                result = get_letta_client()
                
                assert result == mock_client
                mock_letta.assert_called_once_with(
                    token='test-api-key',
                    timeout=30
                )

    def test_get_letta_client_fallback_to_env(self):
        """Test getting Letta client falling back to environment variable."""
        with patch('tools.blocks.get_letta_config') as mock_config:
            mock_config.side_effect = FileNotFoundError("Config not found")
            
            with patch('tools.blocks.os.environ', {'LETTA_API_KEY': 'env-api-key'}):
                with patch('tools.blocks.Letta') as mock_letta:
                    mock_client = Mock()
                    mock_letta.return_value = mock_client
                    
                    result = get_letta_client()
                    
                    assert result == mock_client
                    mock_letta.assert_called_once_with(token='env-api-key')


class TestGetXLettaClient:
    def test_get_x_letta_client_with_config(self):
        """Test getting X Letta client with x_config.yaml."""
        with patch('tools.blocks.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            with patch('builtins.open', mock_open('letta:\n  api_key: x-api-key\n  timeout: 600\n  base_url: https://x-api.example.com')):
                with patch('tools.blocks.yaml.safe_load') as mock_yaml:
                    mock_yaml.return_value = {
                        'letta': {
                            'api_key': 'x-api-key',
                            'timeout': 600,
                            'base_url': 'https://x-api.example.com'
                        }
                    }
                    
                    with patch('tools.blocks.Letta') as mock_letta:
                        mock_client = Mock()
                        mock_letta.return_value = mock_client
                        
                        result = get_x_letta_client()
                        
                        assert result == mock_client
                        mock_letta.assert_called_once_with(
                            token='x-api-key',
                            timeout=600,
                            base_url='https://x-api.example.com'
                        )

    def test_get_x_letta_client_config_not_exists(self):
        """Test getting X Letta client when config doesn't exist."""
        with patch('tools.blocks.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            
            with patch('tools.blocks.get_letta_client') as mock_get_client:
                mock_client = Mock()
                mock_get_client.return_value = mock_client
                
                result = get_x_letta_client()
                
                assert result == mock_client
                mock_get_client.assert_called_once()

    def test_get_x_letta_client_yaml_error(self):
        """Test getting X Letta client with YAML error."""
        with patch('tools.blocks.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            
            with patch('builtins.open', mock_open('invalid yaml')):
                with patch('tools.blocks.yaml.safe_load') as mock_yaml:
                    mock_yaml.side_effect = Exception("YAML error")
                    
                    with patch('tools.blocks.get_letta_client') as mock_get_client:
                        mock_client = Mock()
                        mock_get_client.return_value = mock_client
                        
                        result = get_x_letta_client()
                        
                        assert result == mock_client
                        mock_get_client.assert_called_once()


class TestGetPlatformLettaClient:
    def test_get_platform_letta_client_bluesky(self):
        """Test getting platform client for Bluesky."""
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            
            result = get_platform_letta_client(is_x_function=False)
            
            assert result == mock_client
            mock_get_client.assert_called_once()

    def test_get_platform_letta_client_x(self):
        """Test getting platform client for X."""
        with patch('tools.blocks.get_x_letta_client') as mock_get_x_client:
            mock_client = Mock()
            mock_get_x_client.return_value = mock_client
            
            result = get_platform_letta_client(is_x_function=True)
            
            assert result == mock_client
            mock_get_x_client.assert_called_once()


class TestAttachUserBlocksArgs:
    def test_attach_user_blocks_args_valid(self):
        """Test AttachUserBlocksArgs with valid handles."""
        args = AttachUserBlocksArgs(handles=["user1.bsky.social", "user2.bsky.social"])
        assert args.handles == ["user1.bsky.social", "user2.bsky.social"]

    def test_attach_user_blocks_args_single_handle(self):
        """Test AttachUserBlocksArgs with single handle."""
        args = AttachUserBlocksArgs(handles=["cameron.pfiffer.org"])
        assert args.handles == ["cameron.pfiffer.org"]

    def test_attach_user_blocks_args_empty_handles(self):
        """Test AttachUserBlocksArgs with empty handles list."""
        with pytest.raises(ValueError, match="field required"):
            AttachUserBlocksArgs(handles=[])


class TestDetachUserBlocksArgs:
    def test_detach_user_blocks_args_valid(self):
        """Test DetachUserBlocksArgs with valid handles."""
        args = DetachUserBlocksArgs(handles=["user1.bsky.social", "user2.bsky.social"])
        assert args.handles == ["user1.bsky.social", "user2.bsky.social"]

    def test_detach_user_blocks_args_single_handle(self):
        """Test DetachUserBlocksArgs with single handle."""
        args = DetachUserBlocksArgs(handles=["cameron.pfiffer.org"])
        assert args.handles == ["cameron.pfiffer.org"]


class TestUserNoteAppendArgs:
    def test_user_note_append_args_valid(self):
        """Test UserNoteAppendArgs with valid data."""
        args = UserNoteAppendArgs(
            handle="cameron.pfiffer.org",
            note="\n- Cameron is a person"
        )
        assert args.handle == "cameron.pfiffer.org"
        assert args.note == "\n- Cameron is a person"

    def test_user_note_append_args_missing_handle(self):
        """Test UserNoteAppendArgs with missing handle."""
        with pytest.raises(ValueError, match="field required"):
            UserNoteAppendArgs(note="Some note")

    def test_user_note_append_args_missing_note(self):
        """Test UserNoteAppendArgs with missing note."""
        with pytest.raises(ValueError, match="field required"):
            UserNoteAppendArgs(handle="cameron.pfiffer.org")


class TestUserNoteReplaceArgs:
    def test_user_note_replace_args_valid(self):
        """Test UserNoteReplaceArgs with valid data."""
        args = UserNoteReplaceArgs(
            handle="cameron.pfiffer.org",
            old_text="old content",
            new_text="new content"
        )
        assert args.handle == "cameron.pfiffer.org"
        assert args.old_text == "old content"
        assert args.new_text == "new content"

    def test_user_note_replace_args_missing_fields(self):
        """Test UserNoteReplaceArgs with missing fields."""
        with pytest.raises(ValueError, match="field required"):
            UserNoteReplaceArgs(handle="cameron.pfiffer.org")


class TestUserNoteSetArgs:
    def test_user_note_set_args_valid(self):
        """Test UserNoteSetArgs with valid data."""
        args = UserNoteSetArgs(
            handle="cameron.pfiffer.org",
            content="Complete user information"
        )
        assert args.handle == "cameron.pfiffer.org"
        assert args.content == "Complete user information"

    def test_user_note_set_args_missing_fields(self):
        """Test UserNoteSetArgs with missing fields."""
        with pytest.raises(ValueError, match="field required"):
            UserNoteSetArgs(handle="cameron.pfiffer.org")


class TestUserNoteViewArgs:
    def test_user_note_view_args_valid(self):
        """Test UserNoteViewArgs with valid handle."""
        args = UserNoteViewArgs(handle="cameron.pfiffer.org")
        assert args.handle == "cameron.pfiffer.org"

    def test_user_note_view_args_missing_handle(self):
        """Test UserNoteViewArgs with missing handle."""
        with pytest.raises(ValueError, match="field required"):
            UserNoteViewArgs()


class TestAttachXUserBlocksArgs:
    def test_attach_x_user_blocks_args_valid(self):
        """Test AttachXUserBlocksArgs with valid user IDs."""
        args = AttachXUserBlocksArgs(user_ids=["1232326955652931584", "1950680610282094592"])
        assert args.user_ids == ["1232326955652931584", "1950680610282094592"]

    def test_attach_x_user_blocks_args_single_id(self):
        """Test AttachXUserBlocksArgs with single user ID."""
        args = AttachXUserBlocksArgs(user_ids=["1232326955652931584"])
        assert args.user_ids == ["1232326955652931584"]

    def test_attach_x_user_blocks_args_empty_ids(self):
        """Test AttachXUserBlocksArgs with empty user IDs list."""
        with pytest.raises(ValueError, match="field required"):
            AttachXUserBlocksArgs(user_ids=[])


class TestDetachXUserBlocksArgs:
    def test_detach_x_user_blocks_args_valid(self):
        """Test DetachXUserBlocksArgs with valid user IDs."""
        args = DetachXUserBlocksArgs(user_ids=["1232326955652931584", "1950680610282094592"])
        assert args.user_ids == ["1232326955652931584", "1950680610282094592"]

    def test_detach_x_user_blocks_args_single_id(self):
        """Test DetachXUserBlocksArgs with single user ID."""
        args = DetachXUserBlocksArgs(user_ids=["1232326955652931584"])
        assert args.user_ids == ["1232326955652931584"]


class TestXUserNoteAppendArgs:
    def test_x_user_note_append_args_valid(self):
        """Test XUserNoteAppendArgs with valid data."""
        args = XUserNoteAppendArgs(
            user_id="1232326955652931584",
            note="\\n- Cameron is a person"
        )
        assert args.user_id == "1232326955652931584"
        assert args.note == "\\n- Cameron is a person"

    def test_x_user_note_append_args_missing_user_id(self):
        """Test XUserNoteAppendArgs with missing user ID."""
        with pytest.raises(ValueError, match="field required"):
            XUserNoteAppendArgs(note="Some note")

    def test_x_user_note_append_args_missing_note(self):
        """Test XUserNoteAppendArgs with missing note."""
        with pytest.raises(ValueError, match="field required"):
            XUserNoteAppendArgs(user_id="1232326955652931584")


# Helper function for mocking file operations
def mock_open(content=""):
    """Create a mock for file operations."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=content)
