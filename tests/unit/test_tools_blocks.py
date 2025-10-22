import pytest
from unittest.mock import Mock, patch, mock_open
from pydantic_core import ValidationError
from tools.blocks import (
    get_letta_client,
    get_x_letta_client,
    get_platform_letta_client,
    attach_user_blocks,
    detach_user_blocks,
    user_note_append,
    user_note_replace,
    user_note_set,
    user_note_view,
    attach_x_user_blocks,
    detach_x_user_blocks,
    x_user_note_append,
    x_user_note_replace,
    x_user_note_set,
    x_user_note_view,
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
        with patch('config_loader.get_letta_config') as mock_config:
            mock_config.return_value = {
                'api_key': 'test-api-key',
                'timeout': 30,
                'base_url': 'https://api.example.com'
            }
            
            with patch('letta_client.Letta') as mock_letta:
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
        with patch('config_loader.get_letta_config') as mock_config:
            mock_config.return_value = {
                'api_key': 'test-api-key',
                'timeout': 30
            }
            
            with patch('letta_client.Letta') as mock_letta:
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
        with patch('config_loader.get_letta_config') as mock_config:
            mock_config.side_effect = FileNotFoundError("Config not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'env-api-key'}):
                with patch('letta_client.Letta') as mock_letta:
                    mock_client = Mock()
                    mock_letta.return_value = mock_client
                    
                    result = get_letta_client()
                    
                    assert result == mock_client
                    mock_letta.assert_called_once_with(token='env-api-key')


class TestGetXLettaClient:
    def test_get_x_letta_client_with_config(self):
        """Test getting X Letta client with x_config.yaml."""
        with patch('pathlib.Path') as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path_class.return_value = mock_path
            
            with patch('builtins.open', mock_open(read_data='letta:\n  api_key: x-api-key\n  timeout: 600\n  base_url: https://x-api.example.com')):
                with patch('yaml.safe_load') as mock_yaml:
                    mock_yaml.return_value = {
                        'letta': {
                            'api_key': 'x-api-key',
                            'timeout': 600,
                            'base_url': 'https://x-api.example.com'
                        }
                    }
                    
                    with patch('letta_client.Letta') as mock_letta:
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
        with patch('pathlib.Path') as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = False
            mock_path_class.return_value = mock_path
            
            with patch('tools.blocks.get_letta_client') as mock_get_client:
                mock_client = Mock()
                mock_get_client.return_value = mock_client
                
                result = get_x_letta_client()
                
                assert result == mock_client
                mock_get_client.assert_called_once()

    def test_get_x_letta_client_yaml_error(self):
        """Test getting X Letta client with YAML error."""
        with patch('pathlib.Path') as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path_class.return_value = mock_path
            
            with patch('builtins.open', mock_open(read_data='invalid yaml')):
                with patch('yaml.safe_load') as mock_yaml:
                    import yaml
                    mock_yaml.side_effect = yaml.YAMLError("YAML error")
                    
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
    def test_valid_handles(self):
        """Test valid handles list."""
        args = AttachUserBlocksArgs(handles=['user1.bsky.social', 'user2.bsky.social'])
        assert args.handles == ['user1.bsky.social', 'user2.bsky.social']

    def test_missing_handles(self):
        """Test missing handles field."""
        with pytest.raises(ValidationError):
            AttachUserBlocksArgs()

    def test_invalid_handles_type(self):
        """Test invalid handles type."""
        with pytest.raises(ValidationError):
            AttachUserBlocksArgs(handles="not_a_list")


class TestDetachUserBlocksArgs:
    def test_valid_handles(self):
        """Test valid handles list."""
        args = DetachUserBlocksArgs(handles=['user1.bsky.social', 'user2.bsky.social'])
        assert args.handles == ['user1.bsky.social', 'user2.bsky.social']

    def test_missing_handles(self):
        """Test missing handles field."""
        with pytest.raises(ValidationError):
            DetachUserBlocksArgs()


class TestUserNoteAppendArgs:
    def test_valid_args(self):
        """Test valid arguments."""
        args = UserNoteAppendArgs(
            handle='user.bsky.social',
            note='This is a note'
        )
        assert args.handle == 'user.bsky.social'
        assert args.note == 'This is a note'

    def test_missing_handle(self):
        """Test missing handle field."""
        with pytest.raises(ValidationError):
            UserNoteAppendArgs(note='This is a note')

    def test_missing_note(self):
        """Test missing note field."""
        with pytest.raises(ValidationError):
            UserNoteAppendArgs(handle='user.bsky.social')


class TestUserNoteReplaceArgs:
    def test_valid_args(self):
        """Test valid arguments."""
        args = UserNoteReplaceArgs(
            handle='user.bsky.social',
            old_text='old text',
            new_text='new text'
        )
        assert args.handle == 'user.bsky.social'
        assert args.old_text == 'old text'
        assert args.new_text == 'new text'

    def test_missing_fields(self):
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            UserNoteReplaceArgs(handle='user.bsky.social')


class TestUserNoteSetArgs:
    def test_valid_args(self):
        """Test valid arguments."""
        args = UserNoteSetArgs(
            handle='user.bsky.social',
            content='Complete content'
        )
        assert args.handle == 'user.bsky.social'
        assert args.content == 'Complete content'

    def test_missing_fields(self):
        """Test missing required fields."""
        with pytest.raises(ValidationError):
            UserNoteSetArgs(handle='user.bsky.social')


class TestUserNoteViewArgs:
    def test_valid_args(self):
        """Test valid arguments."""
        args = UserNoteViewArgs(handle='user.bsky.social')
        assert args.handle == 'user.bsky.social'

    def test_missing_handle(self):
        """Test missing handle field."""
        with pytest.raises(ValidationError):
            UserNoteViewArgs()


class TestAttachXUserBlocksArgs:
    def test_valid_user_ids(self):
        """Test valid user IDs list."""
        args = AttachXUserBlocksArgs(user_ids=['1232326955652931584', '1950680610282094592'])
        assert args.user_ids == ['1232326955652931584', '1950680610282094592']

    def test_missing_user_ids(self):
        """Test missing user_ids field."""
        with pytest.raises(ValidationError):
            AttachXUserBlocksArgs()


class TestDetachXUserBlocksArgs:
    def test_valid_user_ids(self):
        """Test valid user IDs list."""
        args = DetachXUserBlocksArgs(user_ids=['1232326955652931584', '1950680610282094592'])
        assert args.user_ids == ['1232326955652931584', '1950680610282094592']

    def test_missing_user_ids(self):
        """Test missing user_ids field."""
        with pytest.raises(ValidationError):
            DetachXUserBlocksArgs()


class TestXUserNoteAppendArgs:
    def test_valid_args(self):
        """Test valid arguments."""
        args = XUserNoteAppendArgs(
            user_id='1232326955652931584',
            note='This is a note'
        )
        assert args.user_id == '1232326955652931584'
        assert args.note == 'This is a note'

    def test_missing_user_id(self):
        """Test missing user_id field."""
        with pytest.raises(ValidationError):
            XUserNoteAppendArgs(note='This is a note')

    def test_missing_note(self):
        """Test missing note field."""
        with pytest.raises(ValidationError):
            XUserNoteAppendArgs(user_id='1232326955652931584')


class TestAttachUserBlocks:
    def test_attach_user_blocks_success(self):
        """Test successful attachment of user blocks."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and blocks
        mock_client = Mock()
        mock_block = Mock()
        mock_block.id = "block-id"
        mock_block.label = "user_test_handle"
        
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock current blocks (empty)
            mock_client.agents.blocks.list.return_value = []
            
            # Mock block creation - return empty list for blocks.list, then create block
            mock_client.blocks.list.return_value = []
            mock_client.blocks.create.return_value = mock_block
            
            # Mock agent block attachment
            mock_client.agents.blocks.attach.return_value = Mock()
            
            result = attach_user_blocks(['test.handle'], mock_agent_state)
            
            assert "✓ test.handle: Block attached" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_called_once()

    def test_attach_user_blocks_already_attached(self):
        """Test attachment when blocks are already attached."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock current blocks (already attached)
            mock_client.agents.blocks.list.return_value = [mock_existing_block]
            
            result = attach_user_blocks(['test.handle'], mock_agent_state)
            
            assert "✓ test.handle: Already attached" in result
            mock_client.blocks.create.assert_not_called()
            mock_client.agents.blocks.attach.assert_not_called()

    def test_attach_user_blocks_fallback_to_env(self):
        """Test attachment with environment variable fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'env-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    # Mock current blocks (empty)
                    mock_client.agents.blocks.list.return_value = []
                    
                    # Mock block creation
                    mock_client.blocks.list.return_value = []
                    mock_client.blocks.create.return_value = Mock()
                    
                    # Mock agent block attachment
                    mock_client.agents.blocks.attach.return_value = Mock()
                    
                    result = attach_user_blocks(['test.handle'], mock_agent_state)
                    
                    assert "✓ test.handle: Block attached" in result
                    mock_letta_class.assert_called_once_with(token='env-key')


class TestDetachUserBlocks:
    def test_detach_user_blocks_success(self):
        """Test successful detachment of user blocks."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock current blocks (attached)
            mock_client.agents.blocks.list.return_value = [mock_existing_block]
            
            # Mock detachment
            mock_client.agents.blocks.detach.return_value = Mock()
            
            result = detach_user_blocks(['test.handle'], mock_agent_state)
            
            assert "✓ test.handle: Detached" in result
            mock_client.agents.blocks.detach.assert_called_once()

    def test_detach_user_blocks_not_attached(self):
        """Test detachment when blocks are not attached."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock current blocks (empty)
            mock_client.agents.blocks.list.return_value = []
            
            result = detach_user_blocks(['test.handle'], mock_agent_state)
            
            assert "✗ test.handle: Not attached" in result
            mock_client.agents.blocks.detach.assert_not_called()

    def test_detach_user_blocks_import_error(self):
        """Test detach user blocks with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_client.agents.blocks.list.return_value = []

        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = detach_user_blocks(['test.handle'], mock_agent_state)
                    
                    assert "✗ test.handle: Not attached" in result
                    mock_letta_class.assert_called_once_with(token='test-key')

    def test_detach_user_blocks_detachment_error(self):
        """Test detach user blocks with detachment error."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"

        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            # Mock current blocks (attached)
            mock_client.agents.blocks.list.return_value = [mock_existing_block]

            # Mock detachment error
            mock_client.agents.blocks.detach.side_effect = Exception("Detachment failed")

            result = detach_user_blocks(['test.handle'], mock_agent_state)

            assert "Error during detachment - Detachment failed" in result
            assert "test.handle" in result

    def test_detach_user_blocks_outer_exception(self):
        """Test detach user blocks outer exception handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client that raises exception on agents.blocks.list
        mock_client = Mock()
        mock_client.agents.blocks.list.side_effect = Exception("Outer error")

        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                detach_user_blocks(['test.user'], mock_agent_state)

            assert "Error detaching user blocks" in str(exc_info.value)
            assert "Outer error" in str(exc_info.value)


class TestUserNoteAppend:
    def test_user_note_append_success(self):
        """Test successful note append."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        mock_existing_block.value = "Existing content"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            # Mock block update
            mock_client.blocks.modify.return_value = Mock()
            
            result = user_note_append('test.handle', 'New note', mock_agent_state)
            
            assert "✓ Appended note to test.handle's memory block" in result
            mock_client.blocks.modify.assert_called_once()

    def test_user_note_append_not_attached(self):
        """Test note append when block is not attached."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (no existing block)
            mock_client.blocks.list.return_value = []
            
            # Mock block creation
            mock_new_block = Mock()
            mock_new_block.id = "new-block-id"
            mock_new_block.label = "user_test_handle"
            mock_client.blocks.create.return_value = mock_new_block
            
            # Mock current blocks (empty)
            mock_client.agents.blocks.list.return_value = []
            
            # Mock agent block attachment
            mock_client.agents.blocks.attach.return_value = Mock()
            
            result = user_note_append('test.handle', 'New note', mock_agent_state)
            
            assert "✓ Created and attached test.handle's memory block with note" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_called_once()

    def test_user_note_append_import_error(self):
        """Test user note append with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_client.blocks.list.return_value = []
        mock_client.agents.blocks.list.return_value = []

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = user_note_append('test.handle', 'New note', mock_agent_state)
                    
                    assert "✓ Created and attached test.handle's memory block with note" in result
                    mock_letta_class.assert_called_once_with(token='test-key')


class TestUserNoteReplace:
    def test_user_note_replace_success(self):
        """Test successful note replace."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        mock_existing_block.value = "Old text content"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            # Mock block update
            mock_client.blocks.modify.return_value = Mock()
            
            result = user_note_replace('test.handle', 'Old text', 'New text', mock_agent_state)
            
            assert "✓ Replaced text in test.handle's memory block" in result
            mock_client.blocks.modify.assert_called_once()

    def test_user_note_replace_text_not_found(self):
        """Test note replace when old text is not found."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        mock_existing_block.value = "Different content"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            with pytest.raises(Exception) as exc_info:
                user_note_replace('test.handle', 'Old text', 'New text', mock_agent_state)
            
            assert "Error replacing text in user block" in str(exc_info.value)
            assert "Text 'Old text' not found in test.handle's memory block" in str(exc_info.value)
            mock_client.blocks.modify.assert_not_called()

    def test_user_note_replace_import_error(self):
        """Test user note replace with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        mock_existing_block.value = "Old text content"
        mock_client.blocks.list.return_value = [mock_existing_block]
        mock_client.blocks.modify.return_value = Mock()

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = user_note_replace('test.handle', 'Old text', 'New text', mock_agent_state)
                    
                    assert "✓ Replaced text in test.handle's memory block" in result
                    mock_letta_class.assert_called_once_with(token='test-key')

    def test_user_note_replace_no_block_found(self):
        """Test user note replace when no block is found."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()

        # Mock block list (no blocks found)
        mock_client.blocks.list.return_value = []

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                user_note_replace('test.handle', 'Old text', 'New text', mock_agent_state)

            assert "Error replacing text in user block" in str(exc_info.value)
            assert "No memory block found for user: test.handle" in str(exc_info.value)


class TestUserNoteSet:
    def test_user_note_set_success(self):
        """Test successful note set."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            # Mock block update
            mock_client.blocks.modify.return_value = Mock()
            
            result = user_note_set('test.handle', 'New content', mock_agent_state)
            
            assert "✓ Set content for test.handle's memory block" in result
            mock_client.blocks.modify.assert_called_once()

    def test_user_note_set_import_error(self):
        """Test user note set with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        mock_client.blocks.list.return_value = [mock_existing_block]
        mock_client.blocks.modify.return_value = Mock()

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = user_note_set('test.handle', 'New content', mock_agent_state)
                    
                    assert "✓ Set content for test.handle's memory block" in result
                    mock_letta_class.assert_called_once_with(token='test-key')


class TestUserNoteView:
    def test_user_note_view_success(self):
        """Test successful note view."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        mock_existing_block.value = "Block content"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            result = user_note_view('test.handle', mock_agent_state)
            
            assert "Block content" in result
            assert "test.handle" in result


class TestAttachXUserBlocks:
    def test_attach_x_user_blocks_success(self):
        """Test successful attachment of X user blocks."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and blocks
        mock_client = Mock()
        mock_block = Mock()
        mock_block.id = "block-id"
        mock_block.label = "x_user_123456789"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock current blocks (empty)
            mock_client.agents.blocks.list.return_value = []
            
            # Mock block creation
            mock_client.blocks.list.return_value = []
            mock_client.blocks.create.return_value = mock_block
            
            # Mock agent block attachment
            mock_client.agents.blocks.attach.return_value = Mock()
            
            result = attach_x_user_blocks(['123456789'], mock_agent_state)
            
            assert "✓ 123456789: Block attached" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_called_once()

    def test_attach_x_user_blocks_import_error(self):
        """Test attach X user blocks with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_client.agents.blocks.list.return_value = []
        mock_client.blocks.list.return_value = []
        
        mock_block = Mock()
        mock_block.id = "block-id"
        mock_block.label = "x_user_123456789"
        mock_client.blocks.create.return_value = mock_block
        mock_client.agents.blocks.attach.return_value = Mock()

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = attach_x_user_blocks(['123456789'], mock_agent_state)
                    
                    assert "✓ 123456789: Block attached" in result
                    mock_letta_class.assert_called_once_with(token='test-key')

    def test_attach_x_user_blocks_block_creation_error(self):
        """Test attach X user blocks with block creation error."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_client.agents.blocks.list.return_value = []
        mock_client.blocks.list.return_value = []
        mock_client.blocks.create.side_effect = Exception("Block creation failed")

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            result = attach_x_user_blocks(['123456789'], mock_agent_state)

            assert "Error - Block creation failed" in result
            assert "123456789" in result

    def test_attach_x_user_blocks_outer_exception(self):
        """Test attach X user blocks outer exception handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client that raises exception on agents.blocks.list
        mock_client = Mock()
        mock_client.agents.blocks.list.side_effect = Exception("Outer error")

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                attach_x_user_blocks(['123456789'], mock_agent_state)

            assert "Error attaching X user blocks" in str(exc_info.value)
            assert "Outer error" in str(exc_info.value)


class TestDetachXUserBlocks:
    def test_detach_x_user_blocks_success(self):
        """Test successful detachment of X user blocks."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock current blocks (attached)
            mock_client.agents.blocks.list.return_value = [mock_existing_block]
            
            # Mock detachment
            mock_client.agents.blocks.detach.return_value = Mock()
            
            result = detach_x_user_blocks(['123456789'], mock_agent_state)
            
            assert "✓ 123456789: Detached" in result
            mock_client.agents.blocks.detach.assert_called_once()

    def test_detach_x_user_blocks_import_error(self):
        """Test detach X user blocks with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_client.agents.blocks.list.return_value = []

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = detach_x_user_blocks(['123456789'], mock_agent_state)
                    
                    assert "✗ 123456789: Not attached" in result
                    mock_letta_class.assert_called_once_with(token='test-key')

    def test_detach_x_user_blocks_detachment_error(self):
        """Test detach X user blocks with detachment error."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            # Mock current blocks (attached)
            mock_client.agents.blocks.list.return_value = [mock_existing_block]

            # Mock detachment error
            mock_client.agents.blocks.detach.side_effect = Exception("Detachment failed")

            result = detach_x_user_blocks(['123456789'], mock_agent_state)

            assert "Error during detachment - Detachment failed" in result
            assert "123456789" in result

    def test_detach_x_user_blocks_outer_exception(self):
        """Test detach X user blocks outer exception handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client that raises exception on agents.blocks.list
        mock_client = Mock()
        mock_client.agents.blocks.list.side_effect = Exception("Outer error")

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                detach_x_user_blocks(['123456789'], mock_agent_state)

            assert "Error detaching X user blocks" in str(exc_info.value)
            assert "Outer error" in str(exc_info.value)


class TestXUserNoteAppend:
    def test_x_user_note_append_success(self):
        """Test successful X user note append."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        mock_existing_block.value = "Existing content"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            # Mock block update
            mock_client.blocks.modify.return_value = Mock()
            
            result = x_user_note_append('123456789', 'New note', mock_agent_state)
            
            assert "✓ Appended note to X user 123456789's memory block" in result
            mock_client.blocks.modify.assert_called_once()

    def test_x_user_note_append_import_error(self):
        """Test X user note append with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        mock_existing_block.value = "Existing content"
        mock_client.blocks.list.return_value = [mock_existing_block]
        mock_client.blocks.modify.return_value = Mock()

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = x_user_note_append('123456789', 'New note', mock_agent_state)
                    
                    assert "✓ Appended note to X user 123456789's memory block" in result
                    mock_letta_class.assert_called_once_with(token='test-key')

    def test_x_user_note_append_block_creation_and_attachment(self):
        """Test X user note append with block creation and attachment."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()

        # Mock block list (no existing block)
        mock_client.blocks.list.return_value = []

        # Mock block creation
        mock_new_block = Mock()
        mock_new_block.id = "new-block-id"
        mock_new_block.label = "x_user_123456789"
        mock_client.blocks.create.return_value = mock_new_block

        # Mock current blocks (empty)
        mock_client.agents.blocks.list.return_value = []

        # Mock agent block attachment
        mock_client.agents.blocks.attach.return_value = Mock()

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            result = x_user_note_append('123456789', 'New note', mock_agent_state)

            assert "✓ Created and attached X user 123456789's memory block with note" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_called_once()

    def test_x_user_note_append_block_already_attached(self):
        """Test X user note append when block is already attached."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()

        # Mock block list (no existing block)
        mock_client.blocks.list.return_value = []

        # Mock block creation
        mock_new_block = Mock()
        mock_new_block.id = "new-block-id"
        mock_new_block.label = "x_user_123456789"
        mock_client.blocks.create.return_value = mock_new_block

        # Mock current blocks (already attached)
        mock_attached_block = Mock()
        mock_attached_block.label = "x_user_123456789"
        mock_client.agents.blocks.list.return_value = [mock_attached_block]

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            result = x_user_note_append('123456789', 'New note', mock_agent_state)

            assert "✓ Created X user 123456789's memory block with note" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_not_called()

    def test_x_user_note_append_outer_exception(self):
        """Test X user note append outer exception handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client that raises exception on blocks.list
        mock_client = Mock()
        mock_client.blocks.list.side_effect = Exception("Outer error")

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                x_user_note_append('123456789', 'New note', mock_agent_state)

            assert "Error appending note to X user block" in str(exc_info.value)
            assert "Outer error" in str(exc_info.value)


class TestAttachUserBlocksErrorHandling:
    def test_attach_user_blocks_block_already_attached_by_id(self):
        """Test attachment when block is already attached by ID."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_handle"
        
        # Mock current blocks (block already attached by ID)
        mock_attached_block = Mock()
        mock_attached_block.id = "existing-block-id"  # Same ID as the existing block
        mock_attached_block.label = "user_different_user"
        mock_client.agents.blocks.list.return_value = [mock_attached_block]
        
        # Mock block list (existing block found)
        mock_client.blocks.list.return_value = [mock_existing_block]
        
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = attach_user_blocks(['test.handle'], mock_agent_state)
            
            assert "✓ test.handle: Already attached (by ID)" in result
            mock_client.blocks.create.assert_not_called()
            mock_client.agents.blocks.attach.assert_not_called()

    def test_attach_user_blocks_outer_exception(self):
        """Test attach user blocks outer exception handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client that raises exception on agents.blocks.list
        mock_client = Mock()
        mock_client.agents.blocks.list.side_effect = Exception("Outer error")

        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            with pytest.raises(Exception) as exc_info:
                attach_user_blocks(['test.user'], mock_agent_state)

            assert "Error attaching user blocks" in str(exc_info.value)
            assert "Outer error" in str(exc_info.value)

    def test_attach_user_blocks_duplicate_constraint_error(self):
        """Test attachment with duplicate constraint error handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock current blocks (empty)
        mock_client.agents.blocks.list.return_value = []
        
        # Mock block creation
        mock_new_block = Mock()
        mock_new_block.id = "new-block-id"
        mock_client.blocks.list.return_value = []
        mock_client.blocks.create.return_value = mock_new_block
        
        # Mock duplicate constraint error
        mock_client.agents.blocks.attach.side_effect = Exception("duplicate key value violates unique constraint unique_label_per_agent")
        
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = attach_user_blocks(['test.handle'], mock_agent_state)
            
            assert "✓ test.handle: Already attached (verified)" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_called_once()

    def test_attach_user_blocks_other_attach_error(self):
        """Test attachment with other attach error."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock current blocks (empty)
        mock_client.agents.blocks.list.return_value = []
        
        # Mock block creation
        mock_new_block = Mock()
        mock_new_block.id = "new-block-id"
        mock_client.blocks.list.return_value = []
        mock_client.blocks.create.return_value = mock_new_block
        
        # Mock other attach error
        mock_client.agents.blocks.attach.side_effect = Exception("Network error")
        
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = attach_user_blocks(['test.handle'], mock_agent_state)
            
            assert "✗ test.handle: Error - Network error" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_called_once()

    def test_attach_user_blocks_block_creation_error(self):
        """Test attachment with block creation error."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock current blocks (empty)
        mock_client.agents.blocks.list.return_value = []
        
        # Mock block creation error
        mock_client.blocks.list.return_value = []
        mock_client.blocks.create.side_effect = Exception("Block creation failed")
        
        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = attach_user_blocks(['test.handle'], mock_agent_state)
            
            assert "✗ test.handle: Error - Block creation failed" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_not_called()

    def test_attach_user_blocks_existing_block_not_attached_by_id(self):
        """Test attach user blocks when block exists but is not attached by ID."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "user_test_user"

        # Mock current blocks (different block attached)
        mock_attached_block = Mock()
        mock_attached_block.id = "different-block-id"
        mock_attached_block.label = "user_different_user"
        mock_client.agents.blocks.list.return_value = [mock_attached_block]

        # Mock block list (existing block found)
        mock_client.blocks.list.return_value = [mock_existing_block]

        # Mock agent block attachment
        mock_client.agents.blocks.attach.return_value = Mock()

        with patch('tools.blocks.get_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client

            result = attach_user_blocks(['test.user'], mock_agent_state)

            # Verify result contains "Block attached"
            assert "Block attached" in result
            assert "test.user" in result

            # Verify attachment was attempted
            mock_client.agents.blocks.attach.assert_called_once()


class TestUserNoteAppendErrorHandling:
    def test_user_note_append_block_already_attached(self):
        """Test note append when block is already attached to agent."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list (no existing block)
        mock_client.blocks.list.return_value = []
        
        # Mock block creation
        mock_new_block = Mock()
        mock_new_block.id = "new-block-id"
        mock_new_block.label = "user_test_handle"
        mock_client.blocks.create.return_value = mock_new_block
        
        # Mock current blocks (already attached)
        mock_attached_block = Mock()
        mock_attached_block.label = "user_test_handle"
        mock_client.agents.blocks.list.return_value = [mock_attached_block]
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = user_note_append('test.handle', 'New note', mock_agent_state)
            
            assert "✓ Created test.handle's memory block with note" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_not_called()

    def test_user_note_append_error_handling(self):
        """Test note append error handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list error
        mock_client.blocks.list.side_effect = Exception("Database error")
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                user_note_append('test.handle', 'New note', mock_agent_state)
            
            assert "Error appending note to user block" in str(exc_info.value)
            assert "Database error" in str(exc_info.value)


class TestUserNoteSetErrorHandling:
    def test_user_note_set_block_creation_and_attachment(self):
        """Test note set with block creation and attachment."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list (no existing block)
        mock_client.blocks.list.return_value = []
        
        # Mock block creation
        mock_new_block = Mock()
        mock_new_block.id = "new-block-id"
        mock_new_block.label = "user_test_handle"
        mock_client.blocks.create.return_value = mock_new_block
        
        # Mock current blocks (empty)
        mock_client.agents.blocks.list.return_value = []
        
        # Mock agent block attachment
        mock_client.agents.blocks.attach.return_value = Mock()
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = user_note_set('test.handle', 'New content', mock_agent_state)
            
            assert "✓ Created and attached test.handle's memory block" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_called_once()

    def test_user_note_set_block_already_attached(self):
        """Test note set when block is already attached."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list (no existing block)
        mock_client.blocks.list.return_value = []
        
        # Mock block creation
        mock_new_block = Mock()
        mock_new_block.id = "new-block-id"
        mock_new_block.label = "user_test_handle"
        mock_client.blocks.create.return_value = mock_new_block
        
        # Mock current blocks (already attached)
        mock_attached_block = Mock()
        mock_attached_block.label = "user_test_handle"
        mock_client.agents.blocks.list.return_value = [mock_attached_block]
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = user_note_set('test.handle', 'New content', mock_agent_state)
            
            assert "✓ Created test.handle's memory block" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_not_called()

    def test_user_note_set_error_handling(self):
        """Test note set error handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list error
        mock_client.blocks.list.side_effect = Exception("Database error")
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                user_note_set('test.handle', 'New content', mock_agent_state)
            
            assert "Error setting user block content" in str(exc_info.value)
            assert "Database error" in str(exc_info.value)


class TestUserNoteViewErrorHandling:
    def test_user_note_view_no_block_found(self):
        """Test note view when no block is found."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list (no blocks found)
        mock_client.blocks.list.return_value = []
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = user_note_view('test.handle', mock_agent_state)
            
            assert "No memory block found for user: test.handle" in result

    def test_user_note_view_error_handling(self):
        """Test note view error handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list error
        mock_client.blocks.list.side_effect = Exception("Database error")
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                user_note_view('test.handle', mock_agent_state)
            
            assert "Error viewing user block" in str(exc_info.value)
            assert "Database error" in str(exc_info.value)


class TestXUserNoteReplace:
    def test_x_user_note_replace_success(self):
        """Test successful X user note replace."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        mock_existing_block.value = "Old text content"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            # Mock block update
            mock_client.blocks.modify.return_value = Mock()
            
            result = x_user_note_replace('123456789', 'Old text', 'New text', mock_agent_state)
            
            assert "✓ Replaced text in X user 123456789's memory block" in result
            mock_client.blocks.modify.assert_called_once()

    def test_x_user_note_replace_text_not_found(self):
        """Test X user note replace when old text is not found."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        mock_existing_block.value = "Different content"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            with pytest.raises(Exception) as exc_info:
                x_user_note_replace('123456789', 'Old text', 'New text', mock_agent_state)
            
            assert "Error replacing text in X user block" in str(exc_info.value)
            assert "Text 'Old text' not found in X user 123456789's memory block" in str(exc_info.value)
            mock_client.blocks.modify.assert_not_called()

    def test_x_user_note_replace_no_block_found(self):
        """Test X user note replace when no block is found."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list (no blocks found)
        mock_client.blocks.list.return_value = []
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                x_user_note_replace('123456789', 'Old text', 'New text', mock_agent_state)
            
            assert "Error replacing text in X user block" in str(exc_info.value)
            assert "No memory block found for X user: 123456789" in str(exc_info.value)

    def test_x_user_note_replace_error_handling(self):
        """Test X user note replace error handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list error
        mock_client.blocks.list.side_effect = Exception("Database error")
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                x_user_note_replace('123456789', 'Old text', 'New text', mock_agent_state)
            
            assert "Error replacing text in X user block" in str(exc_info.value)
            assert "Database error" in str(exc_info.value)

    def test_x_user_note_replace_import_error(self):
        """Test X user note replace with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        mock_existing_block.value = "Old text content"
        mock_client.blocks.list.return_value = [mock_existing_block]
        mock_client.blocks.modify.return_value = Mock()

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = x_user_note_replace('123456789', 'Old text', 'New text', mock_agent_state)
                    
                    assert "✓ Replaced text in X user 123456789's memory block" in result
                    mock_letta_class.assert_called_once_with(token='test-key')


class TestXUserNoteSet:
    def test_x_user_note_set_success(self):
        """Test successful X user note set."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            # Mock block update
            mock_client.blocks.modify.return_value = Mock()
            
            result = x_user_note_set('123456789', 'New content', mock_agent_state)
            
            assert "✓ Set content for X user 123456789's memory block" in result
            mock_client.blocks.modify.assert_called_once()

    def test_x_user_note_set_block_creation_and_attachment(self):
        """Test X user note set with block creation and attachment."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list (no existing block)
        mock_client.blocks.list.return_value = []
        
        # Mock block creation
        mock_new_block = Mock()
        mock_new_block.id = "new-block-id"
        mock_new_block.label = "x_user_123456789"
        mock_client.blocks.create.return_value = mock_new_block
        
        # Mock current blocks (empty)
        mock_client.agents.blocks.list.return_value = []
        
        # Mock agent block attachment
        mock_client.agents.blocks.attach.return_value = Mock()
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = x_user_note_set('123456789', 'New content', mock_agent_state)
            
            assert "✓ Created and attached X user 123456789's memory block" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_called_once()

    def test_x_user_note_set_block_already_attached(self):
        """Test X user note set when block is already attached."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list (no existing block)
        mock_client.blocks.list.return_value = []
        
        # Mock block creation
        mock_new_block = Mock()
        mock_new_block.id = "new-block-id"
        mock_new_block.label = "x_user_123456789"
        mock_client.blocks.create.return_value = mock_new_block
        
        # Mock current blocks (already attached)
        mock_attached_block = Mock()
        mock_attached_block.label = "x_user_123456789"
        mock_client.agents.blocks.list.return_value = [mock_attached_block]
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = x_user_note_set('123456789', 'New content', mock_agent_state)
            
            assert "✓ Created X user 123456789's memory block" in result
            mock_client.blocks.create.assert_called_once()
            mock_client.agents.blocks.attach.assert_not_called()

    def test_x_user_note_set_error_handling(self):
        """Test X user note set error handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list error
        mock_client.blocks.list.side_effect = Exception("Database error")
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                x_user_note_set('123456789', 'New content', mock_agent_state)
            
            assert "Error setting X user block content" in str(exc_info.value)
            assert "Database error" in str(exc_info.value)

    def test_x_user_note_set_import_error(self):
        """Test X user note set with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        mock_client.blocks.list.return_value = [mock_existing_block]
        mock_client.blocks.modify.return_value = Mock()

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = x_user_note_set('123456789', 'New content', mock_agent_state)
                    
                    assert "✓ Set content for X user 123456789's memory block" in result
                    mock_letta_class.assert_called_once_with(token='test-key')


class TestXUserNoteView:
    def test_x_user_note_view_success(self):
        """Test successful X user note view."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client and existing block
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        mock_existing_block.value = "Block content"
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            # Mock block list (existing block found)
            mock_client.blocks.list.return_value = [mock_existing_block]
            
            result = x_user_note_view('123456789', mock_agent_state)
            
            assert "Block content" in result
            assert "123456789" in result

    def test_x_user_note_view_no_block_found(self):
        """Test X user note view when no block is found."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list (no blocks found)
        mock_client.blocks.list.return_value = []
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            result = x_user_note_view('123456789', mock_agent_state)
            
            assert "No memory block found for X user: 123456789" in result

    def test_x_user_note_view_error_handling(self):
        """Test X user note view error handling."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"
        
        # Mock client
        mock_client = Mock()
        
        # Mock block list error
        mock_client.blocks.list.side_effect = Exception("Database error")
        
        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                x_user_note_view('123456789', mock_agent_state)
            
            assert "Error viewing X user block" in str(exc_info.value)
            assert "Database error" in str(exc_info.value)

    def test_x_user_note_view_import_error(self):
        """Test X user note view with ImportError fallback."""
        # Mock agent state
        mock_agent_state = Mock()
        mock_agent_state.id = "test-agent-id"

        # Mock client
        mock_client = Mock()
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "x_user_123456789"
        mock_existing_block.value = "Block content"
        mock_client.blocks.list.return_value = [mock_existing_block]

        with patch('tools.blocks.get_x_letta_client') as mock_get_client:
            mock_get_client.side_effect = ImportError("Module not found")
            
            with patch.dict('os.environ', {'LETTA_API_KEY': 'test-key'}):
                with patch('letta_client.Letta') as mock_letta_class:
                    mock_letta_class.return_value = mock_client
                    
                    result = x_user_note_view('123456789', mock_agent_state)
                    
                    assert "Block content" in result
                    assert "123456789" in result
                    mock_letta_class.assert_called_once_with(token='test-key')