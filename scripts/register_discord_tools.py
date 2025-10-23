import os
import yaml
from letta_client import Letta
from core.config import get_letta_config, get_config, get_logger_names_config
import logging

# Get logger names from configuration
config = get_config()
logger_names = get_logger_names_config(config._config)
main_logger_name = logger_names.get("main", "agent_bot")

logger = logging.getLogger(main_logger_name)

def register_discord_tools():
    """Register Discord tools with Letta agent"""
    try:
        # Load configuration
        config = get_letta_config()
        api_key = config.get('api_key')
        agent_id = config.get('agent_id')
        timeout = config.get('timeout', 30)
        base_url = config.get('base_url')
        
        if not api_key or not agent_id:
            logger.error("Missing required Letta configuration (api_key, agent_id)")
            return False
        
        # Create Letta client
        client_kwargs = {'token': api_key, 'timeout': timeout}
        if base_url:
            client_kwargs['base_url'] = base_url
            
        client = Letta(**client_kwargs)
        
        # Import Discord tools
        from platforms.discord.tools.post import create_new_discord_post
        from platforms.discord.tools.reply import discord_reply
        from platforms.discord.tools.search import search_discord_messages
        from platforms.discord.tools.blocks import ignore_discord_users, unignore_discord_users
        from platforms.discord.tools.feed import get_discord_feed
        
        # Register tools
        tools_to_register = [
            create_new_discord_post,
            discord_reply,
            search_discord_messages,
            ignore_discord_users,
            unignore_discord_users,
            get_discord_feed
        ]
        
        registered_count = 0
        for tool in tools_to_register:
            try:
                result = client.tools.upsert_from_function(tool)
                logger.info(f"Registered Discord tool: {tool.__name__}")
                registered_count += 1
            except Exception as e:
                logger.error(f"Failed to register Discord tool {tool.__name__}: {e}")
        
        logger.info(f"Successfully registered {registered_count}/{len(tools_to_register)} Discord tools")
        return registered_count == len(tools_to_register)
        
    except Exception as e:
        logger.error(f"Error registering Discord tools: {e}")
        return False

if __name__ == "__main__":
    success = register_discord_tools()
    if success:
        print("Discord tools registered successfully")
    else:
        print("Failed to register Discord tools")
