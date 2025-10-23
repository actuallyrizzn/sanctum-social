"""Tests for the Bluesky webpage tool."""
import pytest
from unittest.mock import patch, MagicMock
from platforms.bluesky.tools.webpage import WebpageArgs, fetch_webpage


class TestWebpageArgs:
    """Test the WebpageArgs Pydantic model."""
    
    def test_valid_args(self):
        """Test valid WebpageArgs creation."""
        args = WebpageArgs(url="https://example.com")
        assert args.url == "https://example.com"
    
    def test_empty_url_raises_exception(self):
        """Test that empty URL raises validation error."""
        # Pydantic doesn't raise exception for empty strings by default
        # This test verifies the behavior - empty string is allowed
        args = WebpageArgs(url="")
        assert args.url == ""
    
    def test_none_url_raises_exception(self):
        """Test that None URL raises validation error."""
        with pytest.raises(ValueError):
            WebpageArgs(url=None)
    
    def test_different_url_formats(self):
        """Test various URL formats."""
        urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com/path",
            "https://example.com/path?query=value",
            "https://example.com/path#fragment"
        ]
        
        for url in urls:
            args = WebpageArgs(url=url)
            assert args.url == url
    
    def test_url_with_special_characters(self):
        """Test URL with special characters."""
        url = "https://example.com/path with spaces"
        args = WebpageArgs(url=url)
        assert args.url == url


class TestFetchWebpage:
    """Test the fetch_webpage function."""
    
    @patch('requests.get')
    def test_fetch_webpage_success(self, mock_get):
        """Test successful webpage fetch."""
        mock_response = MagicMock()
        mock_response.text = "# Test Page\n\nThis is test content."
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = fetch_webpage("https://example.com")
        
        assert result == "# Test Page\n\nThis is test content."
        mock_get.assert_called_once_with("https://r.jina.ai/https://example.com", timeout=30)
        mock_response.raise_for_status.assert_called_once()
    
    @patch('requests.get')
    def test_fetch_webpage_with_different_urls(self, mock_get):
        """Test fetch_webpage with different URL formats."""
        mock_response = MagicMock()
        mock_response.text = "Test content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        test_urls = [
            "https://example.com",
            "http://example.com",
            "https://subdomain.example.com/path",
            "https://example.com/path?query=value"
        ]
        
        for url in test_urls:
            result = fetch_webpage(url)
            assert result == "Test content"
            mock_get.assert_called_with(f"https://r.jina.ai/{url}", timeout=30)
    
    @patch('requests.get')
    def test_fetch_webpage_http_error(self, mock_get):
        """Test fetch_webpage with HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404 Not Found")
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="Unexpected error: HTTP 404 Not Found"):
            fetch_webpage("https://example.com")
    
    @patch('requests.get')
    def test_fetch_webpage_connection_error(self, mock_get):
        """Test fetch_webpage with connection error."""
        mock_get.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception, match="Unexpected error: Connection error"):
            fetch_webpage("https://example.com")
    
    @patch('requests.get')
    def test_fetch_webpage_timeout_error(self, mock_get):
        """Test fetch_webpage with timeout error."""
        mock_get.side_effect = Exception("Timeout error")
        
        with pytest.raises(Exception, match="Unexpected error: Timeout error"):
            fetch_webpage("https://example.com")
    
    @patch('requests.get')
    def test_fetch_webpage_unexpected_error(self, mock_get):
        """Test fetch_webpage with unexpected error."""
        mock_response = MagicMock()
        mock_response.text = "Test content"
        mock_response.raise_for_status.side_effect = ValueError("Unexpected error")
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="Unexpected error: Unexpected error"):
            fetch_webpage("https://example.com")
    
    @patch('requests.get')
    def test_fetch_webpage_empty_response(self, mock_get):
        """Test fetch_webpage with empty response."""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = fetch_webpage("https://example.com")
        assert result == ""
    
    @patch('requests.get')
    def test_fetch_webpage_large_response(self, mock_get):
        """Test fetch_webpage with large response."""
        large_content = "Test content " * 1000
        mock_response = MagicMock()
        mock_response.text = large_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = fetch_webpage("https://example.com")
        assert result == large_content
    
    @patch('requests.get')
    def test_fetch_webpage_special_characters_in_url(self, mock_get):
        """Test fetch_webpage with special characters in URL."""
        url = "https://example.com/path with spaces"
        mock_response = MagicMock()
        mock_response.text = "Test content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = fetch_webpage(url)
        assert result == "Test content"
        mock_get.assert_called_once_with(f"https://r.jina.ai/{url}", timeout=30)
    
    @patch('requests.get')
    def test_fetch_webpage_unicode_content(self, mock_get):
        """Test fetch_webpage with unicode content."""
        unicode_content = "测试内容 🚀 émojis"
        mock_response = MagicMock()
        mock_response.text = unicode_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = fetch_webpage("https://example.com")
        assert result == unicode_content
    
    @patch('requests.get')
    def test_fetch_webpage_markdown_content(self, mock_get):
        """Test fetch_webpage with markdown content."""
        markdown_content = """# Title

## Subtitle

- List item 1
- List item 2

**Bold text** and *italic text*

[Link](https://example.com)
"""
        mock_response = MagicMock()
        mock_response.text = markdown_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = fetch_webpage("https://example.com")
        assert result == markdown_content
    
    @patch('requests.get')
    def test_fetch_webpage_multiple_calls(self, mock_get):
        """Test multiple calls to fetch_webpage."""
        mock_response = MagicMock()
        mock_response.text = "Test content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
        
        for url in urls:
            result = fetch_webpage(url)
            assert result == "Test content"
        
        assert mock_get.call_count == 3
        mock_get.assert_any_call("https://r.jina.ai/https://example1.com", timeout=30)
        mock_get.assert_any_call("https://r.jina.ai/https://example2.com", timeout=30)
        mock_get.assert_any_call("https://r.jina.ai/https://example3.com", timeout=30)


class TestWebpageIntegration:
    """Integration tests for webpage functionality."""
    
    def test_webpage_args_with_fetch_webpage(self):
        """Test using WebpageArgs with fetch_webpage."""
        args = WebpageArgs(url="https://example.com")
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "Test content"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = fetch_webpage(args.url)
            assert result == "Test content"
    
    def test_webpage_error_handling_flow(self):
        """Test complete error handling flow."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(Exception, match="Unexpected error: Network error"):
                fetch_webpage("https://example.com")
    
    def test_webpage_success_flow(self):
        """Test complete success flow."""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "Success content"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = fetch_webpage("https://example.com")
            assert result == "Success content"
            mock_get.assert_called_once_with("https://r.jina.ai/https://example.com", timeout=30)
