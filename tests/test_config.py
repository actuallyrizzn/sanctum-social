#!/usr/bin/env python3
"""
Configuration validation test script for Void Bot.
Run this to verify your config.yaml setup is working correctly.
"""


def test_config_loading():
    """Test that configuration can be loaded successfully."""
    try:
        from core.config import (
            get_config,
            get_letta_config,
            get_bluesky_config,
            get_bot_config,
            get_agent_config,
            get_threading_config,
            get_queue_config
        )

        print("Testing Configuration...")
        print("=" * 50)

        # Test basic config loading
        config = get_config()
        print("Configuration file loaded successfully")

        # Test individual config sections
        print("\nConfiguration Sections:")
        print("-" * 30)

        # Letta Configuration
        try:
            letta_config = get_letta_config()
            print(
                f"Letta API: project_id={letta_config.get('project_id', 'N/A')[:20]}...")
            print(f"   - Timeout: {letta_config.get('timeout')}s")
            api_key = letta_config.get('api_key', 'Not configured')
            if api_key != 'Not configured':
                print(f"   - API Key: ***{api_key[-8:]} (configured)")
            else:
                print("   - API Key: Not configured (required)")
        except Exception as e:
            print(f"Letta config: {e}")

        # Bluesky Configuration
        try:
            bluesky_config = get_bluesky_config()
            username = bluesky_config.get('username', 'Not configured')
            password = bluesky_config.get('password', 'Not configured')
            pds_uri = bluesky_config.get('pds_uri', 'Not configured')

            if username != 'Not configured':
                print(f"Bluesky: username={username}")
            else:
                print("Bluesky username: Not configured (required)")

            if password != 'Not configured':
                print(f"   - Password: ***{password[-4:]} (configured)")
            else:
                print("   - Password: Not configured (required)")

            print(f"   - PDS URI: {pds_uri}")
        except Exception as e:
            print(f"Bluesky config: {e}")

        # Bot Configuration
        try:
            bot_config = get_bot_config()
            print(f"Bot behavior:")
            print(
                f"   - Notification delay: {bot_config.get('fetch_notifications_delay')}s")
            print(
                f"   - Max notifications: {bot_config.get('max_processed_notifications')}")
            print(
                f"   - Max pages: {bot_config.get('max_notification_pages')}")
        except Exception as e:
            print(f"Bot config: {e}")

        # Agent Configuration
        try:
            agent_config = get_agent_config()
            print(f"Agent settings:")
            print(f"   - Name: {agent_config.get('name')}")
            print(f"   - Model: {agent_config.get('model')}")
            print(f"   - Embedding: {agent_config.get('embedding')}")
            print(f"   - Max steps: {agent_config.get('max_steps')}")
            blocks = agent_config.get('blocks', {})
            print(f"   - Memory blocks: {len(blocks)} configured")
        except Exception as e:
            print(f"Agent config: {e}")

        # Threading Configuration
        try:
            threading_config = get_threading_config()
            print(f"Threading:")
            print(
                f"   - Parent height: {threading_config.get('parent_height')}")
            print(f"   - Depth: {threading_config.get('depth')}")
            print(
                f"   - Max chars/post: {threading_config.get('max_post_characters')}")
        except Exception as e:
            print(f"Threading config: {e}")

        # Queue Configuration
        try:
            queue_config = get_queue_config()
            priority_users = queue_config.get('priority_users', [])
            print(f"Queue settings:")
            print(
                f"   - Priority users: {len(priority_users)} ({', '.join(priority_users[:3])}{'...' if len(priority_users) > 3 else ''})")
            print(f"   - Base dir: {queue_config.get('base_dir')}")
            print(f"   - Error dir: {queue_config.get('error_dir')}")
        except Exception as e:
            print(f"Queue config: {e}")

        print("\n" + "=" * 50)
        print("Configuration test completed!")

        # Check for common issues
        print("\nConfiguration Status:")
        has_letta_key = False
        has_bluesky_creds = False

        try:
            letta_config = get_letta_config()
            has_letta_key = True
        except:
            print("Missing Letta API key - bot cannot connect to Letta")

        try:
            bluesky_config = get_bluesky_config()
            has_bluesky_creds = True
        except:
            print("Missing Bluesky credentials - bot cannot connect to Bluesky")

        if has_letta_key and has_bluesky_creds:
            print("All required credentials configured - bot should work!")
        elif not has_letta_key and not has_bluesky_creds:
            print("Missing both Letta and Bluesky credentials")
            print("   Add them to config.yaml or set environment variables")
        else:
            print("Partial configuration - some features may not work")

        print("\nNext steps:")
        if not has_letta_key:
            print("   - Add your Letta API key to config.yaml under letta.api_key")
            print("   - Or set LETTA_API_KEY environment variable")
        if not has_bluesky_creds:
            print(
                "   - Add your Bluesky credentials to config.yaml under bluesky section")
            print("   - Or set BSKY_USERNAME and BSKY_PASSWORD environment variables")
        if has_letta_key and has_bluesky_creds:
            print("   - Run: python bsky.py")
            print("   - Or run with testing mode: python bsky.py --test")

    except FileNotFoundError as e:
        print("Configuration file not found!")
        print(f"   {e}")
        print("\nTo set up configuration:")
        print("   1. Copy config.yaml.example to config.yaml")
        print("   2. Edit config.yaml with your credentials")
        print("   3. Run this test again")
    except Exception as e:
        print(f"Configuration loading failed: {e}")
        print("\nTroubleshooting:")
        print("   - Check that config.yaml has valid YAML syntax")
        print("   - Ensure required fields are not commented out")
        print("   - See docs/CONFIG.md for detailed setup instructions")


if __name__ == "__main__":
    test_config_loading()
