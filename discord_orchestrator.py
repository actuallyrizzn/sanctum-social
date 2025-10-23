import os
import logging
import json
import hashlib
import time
from typing import Optional, Dict, Any, List, Set
from datetime import datetime
from pathlib import Path
import discord
from discord.ext import commands

import bsky_utils
from config_loader import get_letta_config
from utils import upsert_block, upsert_agent
from tools.blocks import attach_user_blocks, detach_user_blocks

# Initialize logging early to prevent NoneType errors
logger = logging.getLogger("void_bot")
logger.setLevel(logging.INFO)

# Create a simple handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

prompt_logger = logging.getLogger("void_bot.prompts")
prompt_logger.setLevel(logging.WARNING)

# Discord-specific file paths
DISCORD_QUEUE_DIR = Path("discord_queue")
DISCORD_CACHE_DIR = Path("discord_cache")
DISCORD_PROCESSED_MENTIONS_FILE = DISCORD_QUEUE_DIR / "processed_mentions.json"
DISCORD_LAST_SEEN_FILE = DISCORD_QUEUE_DIR / "last_seen_id.json"
DISCORD_DOWNRANK_USERS_FILE = Path("discord_downrank_users.txt")

class DiscordRateLimitError(Exception):
    """Exception raised when Discord API rate limit is exceeded"""
    pass

class DiscordClient:
    """Discord client wrapper following X/Bluesky patterns"""
    
    def __init__(self, bot_token: str, guild_id: str = None):
        """Initialize Discord client with bot token and optional guild ID"""
        self.bot_token = bot_token
        self.guild_id = guild_id
        self.client = None
        self.last_response_time = 0
        self.response_count = 0
        self.rate_limit_window = 60  # 1 minute window
        self.max_responses_per_minute = 10
        
    async def initialize(self):
        """Initialize the Discord client"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        self.client = commands.Bot(command_prefix='!', intents=intents)
        
        @self.client.event
        async def on_ready():
            logger.info(f'Discord bot logged in as {self.client.user}')
            
        @self.client.event
        async def on_message(message):
            # Ignore messages from the bot itself
            if message.author == self.client.user:
                return
                
            # Only respond to mentions of the bot
            if self.client.user in message.mentions:
                await self._handle_mention(message)
        
        await self.client.start(self.bot_token)
    
    async def _handle_mention(self, message):
        """Handle mention of the bot"""
        try:
            # Check rate limiting
            if not self._check_rate_limit():
                logger.warning("Rate limit exceeded, skipping response")
                return
                
            # Get context (last 10 messages)
            context_messages = await self._get_context_messages(message.channel, message.id, limit=10)
            
            # Process the mention (this would integrate with Letta)
            logger.info(f"Processing Discord mention from {message.author} in {message.channel}")
            
            # For now, just send a simple response
            await message.reply("Hello! I'm Void, your AI assistant. How can I help you?")
            
        except Exception as e:
            logger.error(f"Error handling Discord mention: {e}")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self.last_response_time > self.rate_limit_window:
            self.response_count = 0
            self.last_response_time = current_time
        
        # Check if we've exceeded the limit
        if self.response_count >= self.max_responses_per_minute:
            return False
            
        self.response_count += 1
        return True
    
    async def _get_context_messages(self, channel, message_id: int, limit: int = 10) -> List[dict]:
        """Get context messages before the target message"""
        try:
            messages = []
            async for message in channel.history(limit=limit, before=discord.Object(id=message_id)):
                messages.append({
                    'id': message.id,
                    'content': message.content,
                    'author': {
                        'id': message.author.id,
                        'name': message.author.name,
                        'display_name': message.author.display_name
                    },
                    'created_at': message.created_at.isoformat(),
                    'channel_id': message.channel.id
                })
            return messages
        except Exception as e:
            logger.error(f"Error getting context messages: {e}")
            return []
    
    async def get_mentions(self, limit: int = 50) -> List[dict]:
        """Get mentions directed at the bot"""
        try:
            mentions = []
            for guild in self.client.guilds:
                for channel in guild.text_channels:
                    async for message in channel.history(limit=limit):
                        if self.client.user in message.mentions:
                            mentions.append({
                                'id': message.id,
                                'content': message.content,
                                'author': {
                                    'id': message.author.id,
                                    'name': message.author.name,
                                    'display_name': message.author.display_name
                                },
                                'created_at': message.created_at.isoformat(),
                                'channel_id': message.channel.id,
                                'guild_id': guild.id
                            })
            return mentions
        except Exception as e:
            logger.error(f"Error getting Discord mentions: {e}")
            return []
    
    async def send_message(self, channel_id: str, content: str) -> dict:
        """Send message to Discord channel"""
        try:
            channel = self.client.get_channel(int(channel_id))
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")
                
            message = await channel.send(content)
            return {
                'id': message.id,
                'content': message.content,
                'channel_id': message.channel.id,
                'created_at': message.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            raise
    
    async def send_reply(self, channel_id: str, message_id: str, content: str) -> dict:
        """Reply to specific Discord message"""
        try:
            channel = self.client.get_channel(int(channel_id))
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")
                
            message = await channel.fetch_message(int(message_id))
            reply = await message.reply(content)
            
            return {
                'id': reply.id,
                'content': reply.content,
                'channel_id': reply.channel.id,
                'reply_to': message_id,
                'created_at': reply.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error sending Discord reply: {e}")
            raise
    
    async def get_user_info(self, user_id: str) -> dict:
        """Get Discord user information"""
        try:
            user = await self.client.fetch_user(int(user_id))
            return {
                'id': user.id,
                'name': user.name,
                'display_name': user.display_name,
                'avatar_url': str(user.avatar.url) if user.avatar else None,
                'created_at': user.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting Discord user info: {e}")
            raise
    
    async def get_channel_info(self, channel_id: str) -> dict:
        """Get Discord channel information"""
        try:
            channel = self.client.get_channel(int(channel_id))
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")
                
            return {
                'id': channel.id,
                'name': channel.name,
                'type': str(channel.type),
                'guild_id': channel.guild.id if hasattr(channel, 'guild') else None,
                'created_at': channel.created_at.isoformat() if hasattr(channel, 'created_at') else None
            }
        except Exception as e:
            logger.error(f"Error getting Discord channel info: {e}")
            raise

def load_discord_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load Discord configuration from config file"""
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('discord', {})
    except FileNotFoundError:
        logger.error(f"Config file {config_path} not found")
        return {}
    except Exception as e:
        logger.error(f"Error loading Discord config: {e}")
        return {}

def save_mention_to_queue(mention: dict) -> bool:
    """Save Discord mention to queue for processing"""
    try:
        DISCORD_QUEUE_DIR.mkdir(exist_ok=True)
        
        # Create filename based on mention ID and timestamp
        mention_id = str(mention['id'])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{mention_id}_{timestamp}.json"
        filepath = DISCORD_QUEUE_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(mention, f, indent=2)
            
        logger.info(f"Saved Discord mention {mention_id} to queue")
        return True
    except Exception as e:
        logger.error(f"Error saving Discord mention to queue: {e}")
        return False

def load_processed_mentions() -> Set[str]:
    """Load processed Discord mention IDs"""
    try:
        if DISCORD_PROCESSED_MENTIONS_FILE.exists():
            with open(DISCORD_PROCESSED_MENTIONS_FILE, 'r') as f:
                return set(json.load(f))
        return set()
    except Exception as e:
        logger.error(f"Error loading processed Discord mentions: {e}")
        return set()

def save_processed_mentions(processed_ids: Set[str]) -> None:
    """Save processed Discord mention IDs"""
    try:
        DISCORD_QUEUE_DIR.mkdir(exist_ok=True)
        with open(DISCORD_PROCESSED_MENTIONS_FILE, 'w') as f:
            json.dump(list(processed_ids), f, indent=2)
    except Exception as e:
        logger.error(f"Error saving processed Discord mentions: {e}")

def load_downrank_users() -> Set[str]:
    """Load Discord downrank users list"""
    try:
        if DISCORD_DOWNRANK_USERS_FILE.exists():
            with open(DISCORD_DOWNRANK_USERS_FILE, 'r') as f:
                return {line.strip() for line in f if line.strip() and not line.startswith('#')}
        return set()
    except Exception as e:
        logger.error(f"Error loading Discord downrank users: {e}")
        return set()

def should_respond_to_downranked_user(user_id: str, downrank_users: Set[str]) -> bool:
    """Check if we should respond to a downranked Discord user"""
    if user_id not in downrank_users:
        return True
    
    # 10% chance for downranked users
    import random
    should_respond = random.random() < 0.1
    logger.info(f"Downranked Discord user {user_id}: {'responding' if should_respond else 'skipping'} (10% chance)")
    return should_respond

async def main():
    """Main Discord bot function"""
    try:
        # Load configuration
        config = load_discord_config()
        bot_token = config.get('bot_token')
        
        if not bot_token:
            logger.error("Discord bot token not found in config")
            return
        
        # Create Discord client
        client = DiscordClient(bot_token)
        
        # Initialize and run
        await client.initialize()
        
    except Exception as e:
        logger.error(f"Error in Discord main: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
