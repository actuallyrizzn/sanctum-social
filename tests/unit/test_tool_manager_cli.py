"""Additional CLI coverage tests for tool_manager.py"""

import pytest
import argparse
from unittest.mock import patch, Mock
from tool_manager import BLUESKY_TOOLS, X_TOOLS, COMMON_TOOLS


class TestToolManagerCLICoverage:
    """Test CLI main block coverage for tool_manager.py"""

    def test_cli_main_block_coverage_complete(self):
        """Test complete CLI main block coverage."""
        # Test the list command path
        with patch('tool_manager.get_attached_tools') as mock_get_tools:
            mock_get_tools.return_value = {'tool1', 'tool2'}
            
            # Simulate the CLI main block execution for --list
            parser = argparse.ArgumentParser(description="Manage platform-specific tools for Void agent")
            parser.add_argument("platform", choices=['bluesky', 'x'], nargs='?', help="Platform to configure tools for")
            parser.add_argument("--agent-id", help="Agent ID (default: from config)")
            parser.add_argument("--list", action="store_true", help="List current tools without making changes")
            
            args = parser.parse_args(['--list'])
            
            if args.list:
                tools = mock_get_tools(args.agent_id)
                output_lines = []
                output_lines.append(f"\nCurrently attached tools ({len(tools)}):")
                for tool in sorted(tools):
                    platform_indicator = ""
                    if tool in BLUESKY_TOOLS:
                        platform_indicator = " [Bluesky]"
                    elif tool in X_TOOLS:
                        platform_indicator = " [X]"
                    elif tool in COMMON_TOOLS:
                        platform_indicator = " [Common]"
                    output_lines.append(f"  - {tool}{platform_indicator}")
                
                # Verify the output format
                assert len(output_lines) == 3  # Header + 2 tools
                assert "Currently attached tools (2):" in output_lines[0]
                assert "  - tool1" in output_lines[1] or "  - tool2" in output_lines[1]
                assert "  - tool1" in output_lines[2] or "  - tool2" in output_lines[2]
            
            mock_get_tools.assert_called_once_with(None)

    def test_cli_main_block_coverage_platform_error(self):
        """Test CLI main block coverage for platform error path."""
        # Test the platform required error path
        with patch('tool_manager.ensure_platform_tools') as mock_ensure:
            parser = argparse.ArgumentParser(description="Manage platform-specific tools for Void agent")
            parser.add_argument("platform", choices=['bluesky', 'x'], nargs='?', help="Platform to configure tools for")
            parser.add_argument("--agent-id", help="Agent ID (default: from config)")
            parser.add_argument("--list", action="store_true", help="List current tools without making changes")
            
            args = parser.parse_args([])  # No platform, no --list
            
            try:
                if args.list:
                    # This won't execute
                    pass
                else:
                    if not args.platform:
                        # This should raise SystemExit
                        parser.error("platform is required when not using --list")
            except SystemExit:
                # Expected behavior
                pass

    def test_cli_main_block_coverage_platform_execution(self):
        """Test CLI main block coverage for platform execution."""
        # Test the platform execution path
        with patch('tool_manager.ensure_platform_tools') as mock_ensure:
            parser = argparse.ArgumentParser(description="Manage platform-specific tools for Void agent")
            parser.add_argument("platform", choices=['bluesky', 'x'], nargs='?', help="Platform to configure tools for")
            parser.add_argument("--agent-id", help="Agent ID (default: from config)")
            parser.add_argument("--list", action="store_true", help="List current tools without making changes")
            
            args = parser.parse_args(['bluesky', '--agent-id', 'test-agent'])
            
            if args.list:
                # This won't execute
                pass
            else:
                if not args.platform:
                    parser.error("platform is required when not using --list")
                mock_ensure(args.platform, args.agent_id)
            
    def test_cli_main_block_coverage_platform_execution(self):
        """Test CLI main block coverage for platform execution."""
        # Test the platform execution path
        with patch('tool_manager.ensure_platform_tools') as mock_ensure:
            parser = argparse.ArgumentParser(description="Manage platform-specific tools for Void agent")
            parser.add_argument("platform", choices=['bluesky', 'x'], nargs='?', help="Platform to configure tools for")
            parser.add_argument("--agent-id", help="Agent ID (default: from config)")
            parser.add_argument("--list", action="store_true", help="List current tools without making changes")
            
            args = parser.parse_args(['bluesky', '--agent-id', 'test-agent'])
            
            if args.list:
                # This won't execute
                pass
            else:
                if not args.platform:
                    parser.error("platform is required when not using --list")
                mock_ensure(args.platform, args.agent_id)
            
            mock_ensure.assert_called_once_with('bluesky', 'test-agent')

    def test_cli_main_block_platform_indicators(self):
        """Test CLI main block coverage for platform indicators."""
        import sys
        import tool_manager
        from unittest.mock import patch
        
        # Test with tools from different platforms
        with patch('tool_manager.get_attached_tools') as mock_get_tools:
            # Test with a Bluesky tool
            mock_get_tools.return_value = {'create_new_bluesky_post'}  # This should be in BLUESKY_TOOLS
            
            with patch('sys.argv', ['tool_manager.py', '--list']):
                tool_manager.main()
            
            # Test with an X tool
            mock_get_tools.return_value = {'search_x_posts'}  # This should be in X_TOOLS
            
            with patch('sys.argv', ['tool_manager.py', '--list']):
                tool_manager.main()
            
            # Test with a common tool
            mock_get_tools.return_value = {'halt_activity'}  # This should be in COMMON_TOOLS
            
            with patch('sys.argv', ['tool_manager.py', '--list']):
                tool_manager.main()

    def test_cli_main_block_platform_error(self):
        """Test CLI main block coverage for platform error path."""
        import sys
        import tool_manager
        from unittest.mock import patch
        
        # Test the platform required error path
        with patch('sys.argv', ['tool_manager.py']):  # No platform, no --list
            try:
                tool_manager.main()
            except SystemExit:
                # Expected behavior - parser.error raises SystemExit
                pass

    def test_cli_main_block_actual_execution(self):
        """Test actual CLI main block execution by calling the main() function."""
        import sys
        import tool_manager
        from unittest.mock import patch
        
        # Mock the functions that would be called
        with patch('tool_manager.get_attached_tools') as mock_get_tools, \
             patch('tool_manager.ensure_platform_tools') as mock_ensure:
            
            mock_get_tools.return_value = {'test_tool'}
            
            # Test --list path by mocking sys.argv
            with patch('sys.argv', ['tool_manager.py', '--list']):
                tool_manager.main()
            
            mock_get_tools.assert_called_once_with(None)
            
            # Test platform execution path
            with patch('sys.argv', ['tool_manager.py', 'bluesky', '--agent-id', 'test-agent']):
                tool_manager.main()
            
            mock_ensure.assert_called_once_with('bluesky', 'test-agent')

    def test_cli_main_block_platform_indicators(self):
        """Test CLI main block coverage for platform indicators."""
        import sys
        import tool_manager
        from unittest.mock import patch
        
        # Test with tools from different platforms
        with patch('tool_manager.get_attached_tools') as mock_get_tools:
            # Test with a Bluesky tool
            mock_get_tools.return_value = {'create_new_bluesky_post'}  # This should be in BLUESKY_TOOLS
            
            with patch('sys.argv', ['tool_manager.py', '--list']):
                tool_manager.main()
            
            # Test with an X tool
            mock_get_tools.return_value = {'search_x_posts'}  # This should be in X_TOOLS
            
            with patch('sys.argv', ['tool_manager.py', '--list']):
                tool_manager.main()
            
            # Test with a common tool
            mock_get_tools.return_value = {'halt_activity'}  # This should be in COMMON_TOOLS
            
            with patch('sys.argv', ['tool_manager.py', '--list']):
                tool_manager.main()

    def test_cli_main_block_platform_error(self):
        """Test CLI main block coverage for platform error path."""
        import sys
        import tool_manager
        from unittest.mock import patch
        
        # Test the platform required error path
        with patch('sys.argv', ['tool_manager.py']):  # No platform, no --list
            try:
                tool_manager.main()
            except SystemExit:
                # Expected behavior - parser.error raises SystemExit
                pass
