import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import yaml
from datetime import datetime

# Mock the dotenv loading before importing bsky_utils
with patch('platforms.bluesky.utils.dotenv.load_dotenv'):
    from platforms.bluesky.utils import (
        convert_to_basic_types,
        strip_fields,
        flatten_thread_structure,
        thread_to_yaml_string,
        get_session,
        save_session,
        on_session_change,
        init_client,
        default_login,
        remove_outside_quotes,
        reply_to_post,
        get_post_thread,
        reply_to_notification,
        reply_with_thread_to_notification,
        create_synthesis_ack,
        acknowledge_post,
        create_tool_call_record,
        create_reasoning_record,
        STRIP_FIELDS
    )
    from atproto_client import SessionEvent


class TestConvertToBasicTypes:
    def test_convert_simple_types(self):
        """Test converting simple types."""
        assert convert_to_basic_types("string") == "string"
        assert convert_to_basic_types(123) == 123
        assert convert_to_basic_types(True) == True
        assert convert_to_basic_types(None) == None

    def test_convert_list(self):
        """Test converting list with mixed types."""
        data = ["string", 123, True, None]
        result = convert_to_basic_types(data)
        assert result == ["string", 123, True, None]

    def test_convert_dict(self):
        """Test converting dictionary."""
        data = {"key1": "value1", "key2": 123, "key3": True}
        result = convert_to_basic_types(data)
        assert result == {"key1": "value1", "key2": 123, "key3": True}

    def test_convert_nested_structure(self):
        """Test converting nested data structure."""
        data = {
            "level1": {
                "level2": ["item1", "item2"],
                "level2_dict": {"nested": "value"}
            },
            "simple_list": [1, 2, 3]
        }
        result = convert_to_basic_types(data)
        assert result == data

    def test_convert_with_custom_objects(self):
        """Test converting objects with custom attributes."""
        class CustomObject:
            def __init__(self):
                self.attr1 = "value1"
                self.attr2 = 123
        
        obj = CustomObject()
        result = convert_to_basic_types(obj)
        assert result == {"attr1": "value1", "attr2": 123}


class TestStripFields:
    def test_strip_fields_from_dict(self):
        """Test stripping fields from dictionary."""
        data = {
            "keep_this": "value1",
            "cid": "remove_this",
            "rev": "remove_this_too",
            "other_field": "keep_this_too"
        }
        fields_to_strip = ["cid", "rev"]
        result = strip_fields(data, fields_to_strip)
        
        assert "keep_this" in result
        assert "other_field" in result
        assert "cid" not in result
        assert "rev" not in result

    def test_strip_fields_from_nested_dict(self):
        """Test stripping fields from nested dictionary."""
        data = {
            "level1": {
                "keep_this": "value1",
                "cid": "remove_this"
            },
            "level1_list": [
                {"keep_this": "value2", "rev": "remove_this"}
            ]
        }
        fields_to_strip = ["cid", "rev"]
        result = strip_fields(data, fields_to_strip)
        
        assert "keep_this" in result["level1"]
        assert "cid" not in result["level1"]
        assert "keep_this" in result["level1_list"][0]
        assert "rev" not in result["level1_list"][0]

    def test_strip_fields_from_list(self):
        """Test stripping fields from list of dictionaries."""
        data = [
            {"keep_this": "value1", "cid": "remove_this"},
            {"keep_this": "value2", "rev": "remove_this"}
        ]
        fields_to_strip = ["cid", "rev"]
        result = strip_fields(data, fields_to_strip)
        
        assert len(result) == 2
        assert "keep_this" in result[0]
        assert "cid" not in result[0]
        assert "keep_this" in result[1]
        assert "rev" not in result[1]

    def test_strip_fields_empty_data(self):
        """Test stripping fields from empty data."""
        result = strip_fields({}, ["cid", "rev"])
        assert result == {}
        
        result = strip_fields([], ["cid", "rev"])
        assert result == []


class TestFlattenThreadStructure:
    def test_flatten_simple_thread(self):
        """Test flattening a simple thread structure."""
        # Create a proper thread structure without Mock objects to avoid recursion
        thread_data = {
            'thread': {
                'post': {
                    "uri": "at://did:plc:test/post/1",
                    "text": "Original post"
                },
                'replies': [
                    {
                        'post': {
                            "uri": "at://did:plc:test/post/2",
                            "text": "Reply 1"
                        }
                    }
                ]
            }
        }
        
        result = flatten_thread_structure(thread_data)
        
        assert "posts" in result
        assert len(result["posts"]) == 2
        assert result["posts"][0]["uri"] == "at://did:plc:test/post/1"
        assert result["posts"][0]["text"] == "Original post"
        assert result["posts"][1]["uri"] == "at://did:plc:test/post/2"
        assert result["posts"][1]["text"] == "Reply 1"

    def test_flatten_nested_replies(self):
        """Test flattening thread with nested replies."""
        thread_data = {
            'thread': {
                "post": {
                    "uri": "at://did:plc:test/post/1",
                    "text": "Original post"
                },
                "replies": [
                    {
                        "post": {
                            "uri": "at://did:plc:test/post/2",
                            "text": "Reply 1"
                        },
                        "replies": [
                            {
                                "post": {
                                    "uri": "at://did:plc:test/post/3",
                                    "text": "Reply to reply"
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        result = flatten_thread_structure(thread_data)
        
        assert "posts" in result
        assert len(result["posts"]) == 3
        assert result["posts"][0]["uri"] == "at://did:plc:test/post/1"
        assert result["posts"][1]["uri"] == "at://did:plc:test/post/2"
        assert result["posts"][2]["uri"] == "at://did:plc:test/post/3"

    def test_flatten_empty_thread(self):
        """Test flattening empty thread structure."""
        thread_data = {}
        result = flatten_thread_structure(thread_data)
        
        assert "posts" in result
        assert len(result["posts"]) == 0


class TestThreadToYamlString:
    def test_thread_to_yaml_string_basic(self):
        """Test converting thread to YAML string."""
        thread_data = {
            "thread": {
                "post": {
                    "uri": "at://did:plc:test/post/1",
                    "text": "Original post",
                    "author": {"handle": "test.user.bsky.social"}
                },
                "replies": []
            }
        }
        
        result = thread_to_yaml_string(thread_data)
        
        assert isinstance(result, str)
        assert "Original post" in result
        assert "test.user.bsky.social" in result

    def test_thread_to_yaml_string_with_stripping(self):
        """Test converting thread to YAML with metadata stripping."""
        thread_data = {
            "thread": {
                "post": {
                    "uri": "at://did:plc:test/post/1",
                    "text": "Original post",
                    "cid": "should_be_stripped",
                    "indexed_at": "2025-01-01T00:00:00Z"
                },
                "replies": []
            }
        }
        
        result = thread_to_yaml_string(thread_data, strip_metadata=True)
        
        assert "Original post" in result
        assert "should_be_stripped" not in result
        assert "2025-01-01T00:00:00Z" not in result

    def test_thread_to_yaml_string_without_stripping(self):
        """Test converting thread to YAML without metadata stripping."""
        thread_data = {
            "thread": {
                "post": {
                    "uri": "at://did:plc:test/post/1",
                    "text": "Original post",
                    "cid": "should_be_kept",
                    "indexed_at": "2025-01-01T00:00:00Z"
                },
                "replies": []
            }
        }
        
        result = thread_to_yaml_string(thread_data, strip_metadata=False)
        
        assert "Original post" in result
        assert "should_be_kept" in result
        assert "2025-01-01T00:00:00Z" in result


class TestSessionManagement:
    def test_get_session_existing_file(self, temp_dir):
        """Test getting session from existing file."""
        session_file = temp_dir / "session_test_user.txt"
        session_data = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        with open(session_file, 'w') as f:
            f.write(session_data)
        
        with patch('os.getcwd', return_value=str(temp_dir)):
            result = get_session("test_user")
            assert result == session_data

    def test_get_session_no_file(self, temp_dir):
        """Test getting session when file doesn't exist."""
        with patch('os.getcwd', return_value=str(temp_dir)):
            result = get_session("nonexistent_user")
            assert result is None

    def test_save_session(self, temp_dir):
        """Test saving session to file."""
        session_data = json.dumps({
            'accessJwt': 'valid_jwt',
            'refreshJwt': 'valid_refresh',
            'handle': 'test.bsky.social',
            'did': 'did:plc:test123'
        })
        
        with patch('os.getcwd', return_value=str(temp_dir)):
            save_session("test_user", session_data)
            
            session_file = temp_dir / "session_test_user.txt"
            assert session_file.exists()
            
            with open(session_file, 'r') as f:
                content = f.read()
                assert content == session_data

    def test_on_session_change(self, temp_dir):
        """Test session change handler."""
        with patch('os.getcwd', return_value=str(temp_dir)):
            mock_session = Mock()
            mock_session.export.return_value = json.dumps({
                'accessJwt': 'valid_jwt',
                'refreshJwt': 'valid_refresh',
                'handle': 'test.bsky.social',
                'did': 'did:plc:test123'
            })
            
            # Mock SessionEvent.CREATE
            mock_event = Mock()
            mock_event.__eq__ = lambda self, other: other == SessionEvent.CREATE
            
            on_session_change("test_user", mock_event, mock_session)
            
            session_file = temp_dir / "session_test_user.txt"
            assert session_file.exists()
            
            with open(session_file, 'r') as f:
                content = f.read()
                assert 'valid_jwt' in content


class TestRemoveOutsideQuotes:
    def test_remove_outside_quotes_single_quotes(self):
        """Test that single quotes are preserved (function only handles double quotes)."""
        assert remove_outside_quotes("'hello world'") == "'hello world'"  # Single quotes preserved
        assert remove_outside_quotes("'test'") == "'test'"

    def test_remove_outside_quotes_double_quotes(self):
        """Test removing outside double quotes."""
        assert remove_outside_quotes('"hello world"') == "hello world"
        assert remove_outside_quotes('"test"') == "test"

    def test_remove_outside_quotes_no_quotes(self):
        """Test text without outside quotes."""
        assert remove_outside_quotes("hello world") == "hello world"
        assert remove_outside_quotes("test") == "test"

    def test_remove_outside_quotes_mixed_quotes(self):
        """Test text with mixed quotes inside."""
        assert remove_outside_quotes('"He said \'hello\'"') == "He said 'hello'"
        assert remove_outside_quotes("'She said \"hi\"'") == "'She said \"hi\"'"  # Single quotes preserved

    def test_remove_outside_quotes_unmatched_quotes(self):
        """Test text with unmatched quotes."""
        assert remove_outside_quotes("'unmatched") == "'unmatched"
        assert remove_outside_quotes('"unmatched') == '"unmatched'
        assert remove_outside_quotes("unmatched'") == "unmatched'"

    def test_remove_outside_quotes_empty_string(self):
        """Test empty string."""
        assert remove_outside_quotes("") == ""
        assert remove_outside_quotes("''") == "''"  # Single quotes preserved
        assert remove_outside_quotes('""') == ""


class TestReplyToPost:
    def test_reply_to_post_success(self):
        """Test successful reply to post."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.uri = "at://did:plc:test/reply/1"
        mock_response.cid = "test_cid"
        mock_client.send_post.return_value = mock_response
        
        result = reply_to_post(
            mock_client,
            "Test reply",
            "at://did:plc:test/post/1",
            "test_cid"
        )
        
        assert result.uri == "at://did:plc:test/reply/1"
        assert result.cid == "test_cid"
        mock_client.send_post.assert_called_once()

    def test_reply_to_post_with_root(self):
        """Test reply to post with root context."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.uri = "at://did:plc:test/reply/1"
        mock_response.cid = "test_cid"
        mock_client.send_post.return_value = mock_response
        
        result = reply_to_post(
            mock_client,
            "Test reply",
            "at://did:plc:test/post/1",
            "test_cid",
            root_uri="at://did:plc:test/root/1",
            root_cid="root_cid"
        )
        
        assert result.uri == "at://did:plc:test/reply/1"
        assert result.cid == "test_cid"

    def test_reply_to_post_error(self):
        """Test reply to post with error."""
        mock_client = Mock()
        mock_client.send_post.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            reply_to_post(
                mock_client,
                "Test reply",
                "at://did:plc:test/post/1",
                "test_cid"
            )


class TestGetPostThread:
    def test_get_post_thread_success(self):
        """Test successful thread retrieval."""
        mock_client = Mock()
        mock_thread = {
            "thread": {
                "post": {"uri": "at://did:plc:test/post/1", "text": "Original post"},
                "replies": []
            }
        }
        mock_client.app.bsky.feed.get_post_thread.return_value = mock_thread
        
        result = get_post_thread(mock_client, "at://did:plc:test/post/1")
        
        assert result == mock_thread
        mock_client.app.bsky.feed.get_post_thread.assert_called_once()

    def test_get_post_thread_error(self):
        """Test thread retrieval with error."""
        mock_client = Mock()
        mock_client.app.bsky.feed.get_post_thread.side_effect = Exception("API Error")
        
        result = get_post_thread(mock_client, "at://did:plc:test/post/1")
        
        assert result is None


class TestReplyToNotification:
    def test_reply_to_notification_success(self):
        """Test successful reply to notification."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.uri = "at://did:plc:test/reply/1"
        mock_response.cid = "test_cid"
        mock_client.send_post.return_value = mock_response
        
        # Create a proper mock notification with the expected structure
        mock_notification = Mock()
        mock_notification.uri = "at://did:plc:test/notification/1"
        mock_notification.cid = "notification_cid"
        
        # Mock the record structure properly
        mock_record = Mock()
        mock_record.reply = None  # No reply info, so this post is the root
        mock_notification.record = mock_record
        
        result = reply_to_notification(
            mock_client,
            mock_notification,
            "Test reply"
        )
        
        assert result.uri == "at://did:plc:test/reply/1"
        assert result.cid == "test_cid"

    def test_reply_to_notification_error(self):
        """Test reply to notification with error."""
        mock_client = Mock()
        mock_client.send_post.side_effect = Exception("API Error")
        
        mock_notification = Mock()
        mock_notification.uri = "at://did:plc:test/notification/1"
        mock_notification.cid = "notification_cid"
        
        result = reply_to_notification(
            mock_client,
            mock_notification,
            "Test reply"
        )
        
        assert result is None


class TestCreateSynthesisAck:
    @patch('core.config.get_bluesky_config')
    def test_create_synthesis_ack_success(self, mock_get_bluesky_config):
        """Test successful synthesis acknowledgment creation."""
        # Mock bluesky config to return proper PDS URI
        mock_bluesky_config = {'pds_uri': 'https://bsky.social'}
        mock_get_bluesky_config.return_value = mock_bluesky_config
        
        # Create a mock client with proper session structure
        mock_client = Mock()
        mock_session = Mock()
        mock_session.access_jwt = "test_access_token"
        mock_session.did = "did:plc:test"
        mock_client._session = mock_session
        
        # Mock the requests.post call
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "uri": "at://did:plc:test/ack/1",
                "cid": "test_cid"
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = create_synthesis_ack(mock_client, "Test note")
            
            assert result["uri"] == "at://did:plc:test/ack/1"
            assert result["cid"] == "test_cid"
            mock_post.assert_called_once()

    def test_create_synthesis_ack_error(self):
        """Test synthesis acknowledgment creation with error."""
        mock_client = Mock()
        mock_client.send_post.side_effect = Exception("API Error")
        
        result = create_synthesis_ack(mock_client, "Test note")
        
        assert result is None


class TestAcknowledgePost:
    @patch('core.config.get_bluesky_config')
    def test_acknowledge_post_success(self, mock_get_bluesky_config):
        """Test successful post acknowledgment."""
        # Mock bluesky config to return proper PDS URI
        mock_bluesky_config = {'pds_uri': 'https://bsky.social'}
        mock_get_bluesky_config.return_value = mock_bluesky_config
        
        # Create a mock client with proper session structure
        mock_client = Mock()
        mock_session = Mock()
        mock_session.access_jwt = "test_access_token"
        mock_session.did = "did:plc:test"
        mock_client._session = mock_session
        
        # Mock the requests.post call
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "uri": "at://did:plc:test/ack/1",
                "cid": "test_cid"
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = acknowledge_post(
                mock_client,
                "at://did:plc:test/post/1",
                "post_cid",
                "Test note"
            )
            
            assert result["uri"] == "at://did:plc:test/ack/1"
            assert result["cid"] == "test_cid"
            mock_post.assert_called_once()

    @patch('core.config.get_bluesky_config')
    def test_acknowledge_post_no_note(self, mock_get_bluesky_config):
        """Test post acknowledgment without note."""
        # Mock bluesky config to return proper PDS URI
        mock_bluesky_config = {'pds_uri': 'https://bsky.social'}
        mock_get_bluesky_config.return_value = mock_bluesky_config
        
        # Create a mock client with proper session structure
        mock_client = Mock()
        mock_session = Mock()
        mock_session.access_jwt = "test_access_token"
        mock_session.did = "did:plc:test"
        mock_client._session = mock_session
        
        # Mock the requests.post call
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "uri": "at://did:plc:test/ack/1",
                "cid": "test_cid"
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = acknowledge_post(
                mock_client,
                "at://did:plc:test/post/1",
                "post_cid"
            )
            
            assert result["uri"] == "at://did:plc:test/ack/1"
            assert result["cid"] == "test_cid"
            mock_post.assert_called_once()

    def test_acknowledge_post_error(self):
        """Test post acknowledgment with error."""
        mock_client = Mock()
        mock_client.send_post.side_effect = Exception("API Error")
        
        result = acknowledge_post(
            mock_client,
            "at://did:plc:test/post/1",
            "post_cid",
            "Test note"
        )
        
        assert result is None


class TestCreateToolCallRecord:
    @patch('core.config.get_bluesky_config')
    def test_create_tool_call_record_success(self, mock_get_bluesky_config):
        """Test successful tool call record creation."""
        # Mock bluesky config to return proper PDS URI
        mock_bluesky_config = {'pds_uri': 'https://bsky.social'}
        mock_get_bluesky_config.return_value = mock_bluesky_config
        
        # Create a mock client with proper session structure
        mock_client = Mock()
        mock_session = Mock()
        mock_session.access_jwt = "test_access_token"
        mock_session.did = "did:plc:test"
        mock_client._session = mock_session
        
        # Mock the requests.post call
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "uri": "at://did:plc:test/tool/1",
                "cid": "test_cid"
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = create_tool_call_record(
                mock_client,
                "test_tool",
                '{"arg1": "value1"}',
                "tool_call_123"
            )
            
            assert result["uri"] == "at://did:plc:test/tool/1"
            assert result["cid"] == "test_cid"
            mock_post.assert_called_once()

    def test_create_tool_call_record_error(self):
        """Test tool call record creation with error."""
        mock_client = Mock()
        mock_client.send_post.side_effect = Exception("API Error")
        
        result = create_tool_call_record(
            mock_client,
            "test_tool",
            '{"arg1": "value1"}',
            "tool_call_123"
        )
        
        assert result is None


class TestCreateReasoningRecord:
    @patch('core.config.get_bluesky_config')
    def test_create_reasoning_record_success(self, mock_get_bluesky_config):
        """Test successful reasoning record creation."""
        # Mock bluesky config to return proper PDS URI
        mock_bluesky_config = {'pds_uri': 'https://bsky.social'}
        mock_get_bluesky_config.return_value = mock_bluesky_config
        
        # Create a mock client with proper session structure
        mock_client = Mock()
        mock_session = Mock()
        mock_session.access_jwt = "test_access_token"
        mock_session.did = "did:plc:test"
        mock_client._session = mock_session
        
        # Mock the requests.post call
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "uri": "at://did:plc:test/reasoning/1",
                "cid": "test_cid"
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = create_reasoning_record(mock_client, "Test reasoning text")
            
            assert result["uri"] == "at://did:plc:test/reasoning/1"
            assert result["cid"] == "test_cid"
            mock_post.assert_called_once()

    def test_create_reasoning_record_error(self):
        """Test reasoning record creation with error."""
        mock_client = Mock()
        mock_client.send_post.side_effect = Exception("API Error")
        
        result = create_reasoning_record(mock_client, "Test reasoning text")
        
        assert result is None


class TestConstants:
    def test_strip_fields_constant(self):
        """Test that STRIP_FIELDS constant is properly defined."""
        assert isinstance(STRIP_FIELDS, list)
        assert len(STRIP_FIELDS) > 0
        assert "cid" in STRIP_FIELDS
        assert "rev" in STRIP_FIELDS
        assert "did" in STRIP_FIELDS
