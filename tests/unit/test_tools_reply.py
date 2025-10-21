"""
Unit tests for tools/reply.py
"""
import pytest
from tools.reply import bluesky_reply, ReplyArgs


class TestReplyTool:
    """Test cases for reply tool."""
    
    def test_bluesky_reply_single_message(self):
        """Test reply with single message."""
        messages = ["Hello, this is a test reply"]
        result = bluesky_reply(messages)
        
        assert result == "Reply sent (language: en-US)"
    
    def test_bluesky_reply_multiple_messages(self):
        """Test reply with multiple messages."""
        messages = ["First message", "Second message", "Third message"]
        result = bluesky_reply(messages)
        
        assert result == "Reply thread with 3 messages sent (language: en-US)"
    
    def test_bluesky_reply_custom_language(self):
        """Test reply with custom language."""
        messages = ["Hola, este es un mensaje de prueba"]
        result = bluesky_reply(messages, lang="es")
        
        assert result == "Reply sent (language: es)"
    
    def test_bluesky_reply_max_messages(self):
        """Test reply with maximum allowed messages."""
        messages = ["Message 1", "Message 2", "Message 3", "Message 4"]
        result = bluesky_reply(messages)
        
        assert result == "Reply thread with 4 messages sent (language: en-US)"
    
    def test_bluesky_reply_empty_messages(self):
        """Test reply with empty messages list."""
        with pytest.raises(Exception, match="Messages list cannot be empty"):
            bluesky_reply([])
    
    def test_bluesky_reply_too_many_messages(self):
        """Test reply with too many messages."""
        messages = ["Message 1", "Message 2", "Message 3", "Message 4", "Message 5"]
        with pytest.raises(Exception, match="Cannot send more than 4 reply messages"):
            bluesky_reply(messages)
    
    def test_bluesky_reply_message_too_long(self):
        """Test reply with message that's too long."""
        long_message = "A" * 301  # 301 characters
        messages = [long_message]
        with pytest.raises(Exception, match="Message 1 cannot be longer than 300 characters"):
            bluesky_reply(messages)
    
    def test_bluesky_reply_max_length_message(self):
        """Test reply with maximum length message."""
        max_message = "A" * 300  # Exactly 300 characters
        messages = [max_message]
        result = bluesky_reply(messages)
        
        assert result == "Reply sent (language: en-US)"
    
    def test_bluesky_reply_multiple_long_messages(self):
        """Test reply with multiple messages, one too long."""
        messages = ["Short message", "A" * 301, "Another short message"]
        with pytest.raises(Exception, match="Message 2 cannot be longer than 300 characters"):
            bluesky_reply(messages)
    
    def test_reply_args_model_valid(self):
        """Test ReplyArgs model with valid data."""
        args = ReplyArgs(messages=["Test message"])
        assert args.messages == ["Test message"]
        assert args.lang == "en-US"
        
        args = ReplyArgs(messages=["Message 1", "Message 2"], lang="es")
        assert args.messages == ["Message 1", "Message 2"]
        assert args.lang == "es"
    
    def test_reply_args_model_empty_messages(self):
        """Test ReplyArgs model with empty messages."""
        with pytest.raises(ValueError, match="Messages list cannot be empty"):
            ReplyArgs(messages=[])
    
    def test_reply_args_model_too_many_messages(self):
        """Test ReplyArgs model with too many messages."""
        messages = ["Message 1", "Message 2", "Message 3", "Message 4", "Message 5"]
        with pytest.raises(ValueError, match="Cannot send more than 4 reply messages"):
            ReplyArgs(messages=messages)
    
    def test_reply_args_model_message_too_long(self):
        """Test ReplyArgs model with message too long."""
        long_message = "A" * 301
        with pytest.raises(ValueError, match="Message 1 cannot be longer than 300 characters"):
            ReplyArgs(messages=[long_message])
    
    def test_reply_args_model_multiple_long_messages(self):
        """Test ReplyArgs model with multiple messages, one too long."""
        messages = ["Short message", "A" * 301, "Another short message"]
        with pytest.raises(ValueError, match="Message 2 cannot be longer than 300 characters"):
            ReplyArgs(messages=messages)
    
    def test_bluesky_reply_with_args_model(self):
        """Test bluesky_reply using ReplyArgs model."""
        args = ReplyArgs(messages=["Model-based message"], lang="ja")
        result = bluesky_reply(args.messages, args.lang)
        
        assert result == "Reply sent (language: ja)"
    
    def test_bluesky_reply_different_languages(self):
        """Test reply with different language codes."""
        languages = ["en-US", "es", "ja", "th", "fr", "de"]
        messages = ["Test message"]
        
        for lang in languages:
            result = bluesky_reply(messages, lang)
            assert result == f"Reply sent (language: {lang})"
    
    def test_bluesky_reply_special_characters(self):
        """Test reply with special characters."""
        messages = ["Message with @#$%^&*()_+-=[]{}|;':\",./<>?"]
        result = bluesky_reply(messages)
        
        assert result == "Reply sent (language: en-US)"
    
    def test_bluesky_reply_unicode(self):
        """Test reply with unicode characters."""
        messages = ["Message with unicode: 🌟 ✨ 💫"]
        result = bluesky_reply(messages)
        
        assert result == "Reply sent (language: en-US)"
    
    def test_bluesky_reply_whitespace_messages(self):
        """Test reply with whitespace-only messages."""
        messages = ["   ", "\t", "\n"]
        result = bluesky_reply(messages)
        
        assert result == "Reply thread with 3 messages sent (language: en-US)"
    
    def test_bluesky_reply_mixed_length_messages(self):
        """Test reply with messages of different lengths."""
        messages = [
            "Short",
            "A" * 100,
            "A" * 200,
            "A" * 300
        ]
        result = bluesky_reply(messages)
        
        assert result == "Reply thread with 4 messages sent (language: en-US)"
    
    def test_bluesky_reply_none_messages(self):
        """Test reply with None messages."""
        with pytest.raises(Exception, match="Messages list cannot be empty"):
            bluesky_reply(None)
    
    def test_bluesky_reply_empty_string_messages(self):
        """Test reply with empty string messages."""
        messages = ["", "", ""]
        result = bluesky_reply(messages)
        
        assert result == "Reply thread with 3 messages sent (language: en-US)"
    
    def test_bluesky_reply_edge_case_lengths(self):
        """Test reply with edge case message lengths."""
        # Test exactly at limits
        messages = ["A" * 300, "B" * 300, "C" * 300, "D" * 300]
        result = bluesky_reply(messages)
        
        assert result == "Reply thread with 4 messages sent (language: en-US)"
    
    def test_bluesky_reply_single_character_messages(self):
        """Test reply with single character messages."""
        messages = ["A", "B", "C"]
        result = bluesky_reply(messages)
        
        assert result == "Reply thread with 3 messages sent (language: en-US)"
    
    def test_bluesky_reply_language_case_sensitivity(self):
        """Test reply with different language code cases."""
        messages = ["Test message"]
        
        # Test different cases
        result1 = bluesky_reply(messages, "en-us")
        result2 = bluesky_reply(messages, "EN-US")
        result3 = bluesky_reply(messages, "En-Us")
        
        assert result1 == "Reply sent (language: en-us)"
        assert result2 == "Reply sent (language: EN-US)"
        assert result3 == "Reply sent (language: En-Us)"
