"""Tests for platforms.bluesky.tools.thread module."""

import pytest
from pydantic import ValidationError

from platforms.bluesky.tools.thread import ReplyThreadPostArgs, add_post_to_bluesky_reply_thread


class TestReplyThreadPostArgs:
    """Test ReplyThreadPostArgs model validation."""

    def test_valid_args(self):
        """Test valid arguments."""
        args = ReplyThreadPostArgs(text="Hello world", lang="en-US")
        assert args.text == "Hello world"
        assert args.lang == "en-US"

    def test_default_language(self):
        """Test default language is applied."""
        args = ReplyThreadPostArgs(text="Hello world")
        assert args.text == "Hello world"
        assert args.lang == "en-US"

    def test_text_length_validation_valid(self):
        """Test text length validation with valid length."""
        args = ReplyThreadPostArgs(text="A" * 300)
        assert args.text == "A" * 300

    def test_text_length_validation_invalid(self):
        """Test text length validation with invalid length."""
        with pytest.raises(ValidationError) as exc_info:
            ReplyThreadPostArgs(text="A" * 301)
        
        assert "Text exceeds 300 character limit" in str(exc_info.value)

    def test_text_length_validation_exact_limit(self):
        """Test text length validation at exact limit."""
        args = ReplyThreadPostArgs(text="A" * 300)
        assert len(args.text) == 300

    def test_different_languages(self):
        """Test different language codes."""
        languages = ["en-US", "es", "ja", "th", "fr-FR"]
        for lang in languages:
            args = ReplyThreadPostArgs(text="Hello", lang=lang)
            assert args.lang == lang

    def test_empty_text(self):
        """Test empty text is allowed."""
        args = ReplyThreadPostArgs(text="")
        assert args.text == ""

    def test_unicode_text(self):
        """Test unicode text handling."""
        args = ReplyThreadPostArgs(text="Hello 世界 🌍", lang="en-US")
        assert args.text == "Hello 世界 🌍"

    def test_special_characters(self):
        """Test special characters in text."""
        args = ReplyThreadPostArgs(text="Hello @user #hashtag $money", lang="en-US")
        assert args.text == "Hello @user #hashtag $money"


class TestAddPostToBlueskyReplyThread:
    """Test add_post_to_bluesky_reply_thread function."""

    def test_add_post_success(self):
        """Test successful post addition."""
        result = add_post_to_bluesky_reply_thread("Hello world", "en-US")
        assert "Post queued for reply thread" in result
        assert "Hello world" in result
        assert "Language: en-US" in result

    def test_add_post_default_language(self):
        """Test post addition with default language."""
        result = add_post_to_bluesky_reply_thread("Hello world")
        assert "Post queued for reply thread" in result
        assert "Hello world" in result
        assert "Language: en-US" in result

    def test_add_post_long_text_truncation(self):
        """Test post addition with long text shows truncation."""
        long_text = "A" * 100
        result = add_post_to_bluesky_reply_thread(long_text, "en-US")
        assert "Post queued for reply thread" in result
        assert long_text[:50] in result
        assert "..." in result

    def test_add_post_short_text_no_truncation(self):
        """Test post addition with short text shows no truncation."""
        short_text = "Hello"
        result = add_post_to_bluesky_reply_thread(short_text, "en-US")
        assert "Post queued for reply thread" in result
        assert short_text in result
        assert "..." not in result

    def test_add_post_text_too_long_raises_exception(self):
        """Test post addition with text exceeding limit raises exception."""
        with pytest.raises(Exception) as exc_info:
            add_post_to_bluesky_reply_thread("A" * 301, "en-US")
        
        assert "Text exceeds 300 character limit" in str(exc_info.value)
        assert "This post will be omitted from the thread" in str(exc_info.value)

    def test_add_post_exact_limit(self):
        """Test post addition at exact character limit."""
        text = "A" * 300
        result = add_post_to_bluesky_reply_thread(text, "en-US")
        assert "Post queued for reply thread" in result
        assert text[:50] in result

    def test_add_post_different_languages(self):
        """Test post addition with different languages."""
        languages = ["es", "ja", "th", "fr-FR"]
        for lang in languages:
            result = add_post_to_bluesky_reply_thread("Hello", lang)
            assert f"Language: {lang}" in result

    def test_add_post_empty_text(self):
        """Test post addition with empty text."""
        result = add_post_to_bluesky_reply_thread("", "en-US")
        assert "Post queued for reply thread" in result
        assert "Language: en-US" in result

    def test_add_post_unicode_text(self):
        """Test post addition with unicode text."""
        text = "Hello 世界 🌍"
        result = add_post_to_bluesky_reply_thread(text, "en-US")
        assert "Post queued for reply thread" in result
        assert text in result

    def test_add_post_special_characters(self):
        """Test post addition with special characters."""
        text = "Hello @user #hashtag $money"
        result = add_post_to_bluesky_reply_thread(text, "en-US")
        assert "Post queued for reply thread" in result
        assert text in result

    def test_add_post_multiline_text(self):
        """Test post addition with multiline text."""
        text = "Line 1\nLine 2\nLine 3"
        result = add_post_to_bluesky_reply_thread(text, "en-US")
        assert "Post queued for reply thread" in result
        assert "Line 1" in result

    def test_add_post_whitespace_text(self):
        """Test post addition with whitespace text."""
        text = "   Hello   "
        result = add_post_to_bluesky_reply_thread(text, "en-US")
        assert "Post queued for reply thread" in result
        assert text in result
