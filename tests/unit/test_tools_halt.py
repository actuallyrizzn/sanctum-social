"""
Unit tests for tools/halt.py
"""
import pytest
from platforms.bluesky.tools.halt import halt_activity, HaltArgs


class TestHaltTool:
    """Test cases for halt tool."""
    
    def test_halt_activity_default_reason(self):
        """Test halt activity with default reason."""
        result = halt_activity()
        
        assert result == "Halting activity: User requested halt"
    
    def test_halt_activity_custom_reason(self):
        """Test halt activity with custom reason."""
        custom_reason = "Emergency stop requested"
        result = halt_activity(custom_reason)
        
        assert result == f"Halting activity: {custom_reason}"
    
    def test_halt_activity_empty_reason(self):
        """Test halt activity with empty reason."""
        result = halt_activity("")
        
        assert result == "Halting activity: "
    
    def test_halt_args_model(self):
        """Test HaltArgs Pydantic model."""
        # Test default values
        args = HaltArgs()
        assert args.reason == "User requested halt"
        
        # Test custom values
        custom_args = HaltArgs(reason="Custom halt reason")
        assert custom_args.reason == "Custom halt reason"
    
    def test_halt_args_validation(self):
        """Test HaltArgs validation."""
        # Test with valid data
        args = HaltArgs(reason="Valid reason")
        assert args.reason == "Valid reason"
        
        # Test with different data types
        args = HaltArgs(reason="123")
        assert args.reason == "123"
    
    def test_halt_activity_with_args_model(self):
        """Test halt activity using HaltArgs model."""
        args = HaltArgs(reason="Model-based halt")
        result = halt_activity(args.reason)
        
        assert result == "Halting activity: Model-based halt"
    
    def test_halt_activity_multiple_calls(self):
        """Test multiple halt activity calls."""
        reasons = ["Reason 1", "Reason 2", "Reason 3"]
        results = [halt_activity(reason) for reason in reasons]
        
        for i, result in enumerate(results):
            assert result == f"Halting activity: {reasons[i]}"
    
    def test_halt_activity_special_characters(self):
        """Test halt activity with special characters."""
        special_reason = "Halt! @#$%^&*()_+-=[]{}|;':\",./<>?"
        result = halt_activity(special_reason)
        
        assert result == f"Halting activity: {special_reason}"
    
    def test_halt_activity_unicode(self):
        """Test halt activity with unicode characters."""
        unicode_reason = "Halt with unicode: 🛑 ⚠️ 🚨"
        result = halt_activity(unicode_reason)
        
        assert result == f"Halting activity: {unicode_reason}"
    
    def test_halt_activity_long_reason(self):
        """Test halt activity with very long reason."""
        long_reason = "A" * 1000  # 1000 character reason
        result = halt_activity(long_reason)
        
        assert result == f"Halting activity: {long_reason}"
        assert len(result) == len(long_reason) + len("Halting activity: ")
