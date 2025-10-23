"""
Unit tests for tools/ack.py
"""
import pytest
from platforms.bluesky.tools.ack import annotate_ack, AnnotateAckArgs


class TestAckTool:
    """Test cases for annotate ack tool."""
    
    def test_annotate_ack_basic(self):
        """Test basic annotate ack functionality."""
        note = "This is a test note"
        result = annotate_ack(note)
        
        assert result == f'Your note will be added to the acknowledgment: "{note}"'
    
    def test_annotate_ack_empty_note(self):
        """Test annotate ack with empty note."""
        result = annotate_ack("")
        
        assert result == 'Your note will be added to the acknowledgment: ""'
    
    def test_annotate_ack_args_model(self):
        """Test AnnotateAckArgs Pydantic model."""
        # Test with valid note
        args = AnnotateAckArgs(note="Test note")
        assert args.note == "Test note"
        
        # Test with empty note
        args = AnnotateAckArgs(note="")
        assert args.note == ""
    
    def test_annotate_ack_args_validation(self):
        """Test AnnotateAckArgs validation."""
        # Test with valid data
        args = AnnotateAckArgs(note="Valid note")
        assert args.note == "Valid note"
        
        # Test with different data types
        args = AnnotateAckArgs(note="123")
        assert args.note == "123"
    
    def test_annotate_ack_with_args_model(self):
        """Test annotate ack using AnnotateAckArgs model."""
        args = AnnotateAckArgs(note="Model-based note")
        result = annotate_ack(args.note)
        
        assert result == 'Your note will be added to the acknowledgment: "Model-based note"'
    
    def test_annotate_ack_special_characters(self):
        """Test annotate ack with special characters."""
        special_note = "Note with @#$%^&*()_+-=[]{}|;':\",./<>?"
        result = annotate_ack(special_note)
        
        assert result == f'Your note will be added to the acknowledgment: "{special_note}"'
    
    def test_annotate_ack_unicode(self):
        """Test annotate ack with unicode characters."""
        unicode_note = "Note with unicode: 📝 ✅ 💯"
        result = annotate_ack(unicode_note)
        
        assert result == f'Your note will be added to the acknowledgment: "{unicode_note}"'
    
    def test_annotate_ack_long_note(self):
        """Test annotate ack with very long note."""
        long_note = "A" * 1000  # 1000 character note
        result = annotate_ack(long_note)
        
        expected = f'Your note will be added to the acknowledgment: "{long_note}"'
        assert result == expected
        assert len(result) == len(expected)
    
    def test_annotate_ack_multiple_calls(self):
        """Test multiple annotate ack calls."""
        notes = ["Note 1", "Note 2", "Note 3"]
        results = [annotate_ack(note) for note in notes]
        
        for i, result in enumerate(results):
            assert result == f'Your note will be added to the acknowledgment: "{notes[i]}"'
    
    def test_annotate_ack_format_consistency(self):
        """Test that the output format is consistent."""
        test_notes = [
            "Simple note",
            "Note with spaces",
            "Note-with-hyphens",
            "Note_with_underscores",
            "Note.with.dots",
            "Note,with,commas"
        ]
        
        for note in test_notes:
            result = annotate_ack(note)
            assert result.startswith('Your note will be added to the acknowledgment: "')
            assert result.endswith('"')
            assert f'"{note}"' in result
    
    def test_annotate_ack_quotes_in_note(self):
        """Test annotate ack with quotes in the note."""
        note_with_quotes = 'Note with "quotes" inside'
        result = annotate_ack(note_with_quotes)
        
        assert result == f'Your note will be added to the acknowledgment: "{note_with_quotes}"'
    
    def test_annotate_ack_newlines_in_note(self):
        """Test annotate ack with newlines in the note."""
        note_with_newlines = "Note with\nnewlines\ninside"
        result = annotate_ack(note_with_newlines)
        
        assert result == f'Your note will be added to the acknowledgment: "{note_with_newlines}"'
    
    def test_annotate_ack_tabs_in_note(self):
        """Test annotate ack with tabs in the note."""
        note_with_tabs = "Note with\ttabs\tinside"
        result = annotate_ack(note_with_tabs)
        
        assert result == f'Your note will be added to the acknowledgment: "{note_with_tabs}"'
    
    def test_annotate_ack_whitespace_note(self):
        """Test annotate ack with whitespace-only note."""
        whitespace_note = "   \t\n   "
        result = annotate_ack(whitespace_note)
        
        assert result == f'Your note will be added to the acknowledgment: "{whitespace_note}"'
    
    def test_annotate_ack_numeric_note(self):
        """Test annotate ack with numeric note."""
        numeric_note = "12345"
        result = annotate_ack(numeric_note)
        
        assert result == f'Your note will be added to the acknowledgment: "{numeric_note}"'
    
    def test_annotate_ack_boolean_note(self):
        """Test annotate ack with boolean-like note."""
        boolean_note = "True"
        result = annotate_ack(boolean_note)
        
        assert result == f'Your note will be added to the acknowledgment: "{boolean_note}"'
