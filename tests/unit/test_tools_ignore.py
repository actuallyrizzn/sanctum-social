"""
Unit tests for tools/ignore.py
"""
import pytest
from platforms.bluesky.tools.ignore import ignore_notification, IgnoreNotificationArgs


class TestIgnoreTool:
    """Test cases for ignore notification tool."""
    
    def test_ignore_notification_default_category(self):
        """Test ignore notification with default category."""
        reason = "Bot detected"
        result = ignore_notification(reason)
        
        assert result == f"IGNORED_NOTIFICATION::bot::{reason}"
    
    def test_ignore_notification_custom_category(self):
        """Test ignore notification with custom category."""
        reason = "Spam detected"
        category = "spam"
        result = ignore_notification(reason, category)
        
        assert result == f"IGNORED_NOTIFICATION::{category}::{reason}"
    
    def test_ignore_notification_different_categories(self):
        """Test ignore notification with different categories."""
        test_cases = [
            ("Bot detected", "bot"),
            ("Spam content", "spam"),
            ("Not relevant", "not_relevant"),
            ("Handled elsewhere", "handled_elsewhere"),
            ("Custom category", "custom")
        ]
        
        for reason, category in test_cases:
            result = ignore_notification(reason, category)
            assert result == f"IGNORED_NOTIFICATION::{category}::{reason}"
    
    def test_ignore_notification_args_model(self):
        """Test IgnoreNotificationArgs Pydantic model."""
        # Test with required reason only
        args = IgnoreNotificationArgs(reason="Test reason")
        assert args.reason == "Test reason"
        assert args.category == "bot"  # Default value
        
        # Test with both reason and category
        args = IgnoreNotificationArgs(reason="Test reason", category="spam")
        assert args.reason == "Test reason"
        assert args.category == "spam"
    
    def test_ignore_notification_args_validation(self):
        """Test IgnoreNotificationArgs validation."""
        # Test with valid data
        args = IgnoreNotificationArgs(reason="Valid reason")
        assert args.reason == "Valid reason"
        
        # Test with empty reason (should be valid)
        args = IgnoreNotificationArgs(reason="")
        assert args.reason == ""
        
        # Test with None category (should use default)
        args = IgnoreNotificationArgs(reason="Test", category=None)
        assert args.category is None
    
    def test_ignore_notification_with_args_model(self):
        """Test ignore notification using IgnoreNotificationArgs model."""
        args = IgnoreNotificationArgs(reason="Model-based ignore", category="test")
        result = ignore_notification(args.reason, args.category)
        
        assert result == "IGNORED_NOTIFICATION::test::Model-based ignore"
    
    def test_ignore_notification_special_characters(self):
        """Test ignore notification with special characters."""
        special_reason = "Ignore! @#$%^&*()_+-=[]{}|;':\",./<>?"
        result = ignore_notification(special_reason)
        
        assert result == f"IGNORED_NOTIFICATION::bot::{special_reason}"
    
    def test_ignore_notification_unicode(self):
        """Test ignore notification with unicode characters."""
        unicode_reason = "Ignore with unicode: 🚫 ❌ ⛔"
        result = ignore_notification(unicode_reason)
        
        assert result == f"IGNORED_NOTIFICATION::bot::{unicode_reason}"
    
    def test_ignore_notification_long_reason(self):
        """Test ignore notification with very long reason."""
        long_reason = "A" * 1000  # 1000 character reason
        result = ignore_notification(long_reason)
        
        expected = f"IGNORED_NOTIFICATION::bot::{long_reason}"
        assert result == expected
        assert len(result) == len(expected)
    
    def test_ignore_notification_empty_reason(self):
        """Test ignore notification with empty reason."""
        result = ignore_notification("")
        
        assert result == "IGNORED_NOTIFICATION::bot::"
    
    def test_ignore_notification_empty_category(self):
        """Test ignore notification with empty category."""
        result = ignore_notification("Test reason", "")
        
        assert result == "IGNORED_NOTIFICATION::::Test reason"
    
    def test_ignore_notification_format_consistency(self):
        """Test that the output format is consistent."""
        reasons = ["Reason 1", "Reason 2", "Reason 3"]
        categories = ["bot", "spam", "not_relevant"]
        
        for reason in reasons:
            for category in categories:
                result = ignore_notification(reason, category)
                assert result.startswith("IGNORED_NOTIFICATION::")
                assert result.endswith(f"::{reason}")
                assert f"::{category}::" in result
    
    def test_ignore_notification_multiple_calls(self):
        """Test multiple ignore notification calls."""
        test_data = [
            ("Bot detected", "bot"),
            ("Spam content", "spam"),
            ("Not relevant", "not_relevant")
        ]
        
        results = [ignore_notification(reason, category) for reason, category in test_data]
        
        for i, (reason, category) in enumerate(test_data):
            assert results[i] == f"IGNORED_NOTIFICATION::{category}::{reason}"
