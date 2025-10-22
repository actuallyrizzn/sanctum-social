#!/usr/bin/env python3
"""Register all Void tools with a Letta agent."""
import os
import sys
import logging
from typing import List
from letta_client import Letta
from rich.console import Console
from rich.table import Table
from config_loader import get_letta_config

# Import standalone functions and their schemas
from tools.search import search_bluesky_posts, SearchArgs
from tools.post import create_new_bluesky_post, PostArgs
from tools.feed import get_bluesky_feed, FeedArgs
from tools.blocks import attach_user_blocks, detach_user_blocks, user_note_append, user_note_replace, user_note_set, user_note_view, AttachUserBlocksArgs, DetachUserBlocksArgs, UserNoteAppendArgs, UserNoteReplaceArgs, UserNoteSetArgs, UserNoteViewArgs
from tools.halt import halt_activity, HaltArgs
from tools.thread import add_post_to_bluesky_reply_thread, ReplyThreadPostArgs
from tools.ignore import ignore_notification, IgnoreNotificationArgs
from tools.whitewind import create_whitewind_blog_post, WhitewindPostArgs
from tools.ack import annotate_ack, AnnotateAckArgs
from tools.webpage import fetch_webpage, WebpageArgs

letta_config = get_letta_config()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


# Tool configurations: function paired with its args_schema and metadata
TOOL_CONFIGS = [
    {
        "func": search_bluesky_posts,
        "args_schema": SearchArgs,
        "description": "Search for posts on Bluesky matching the given criteria",
        "tags": ["bluesky", "search", "posts"]
    },
    {
        "func": create_new_bluesky_post,
        "args_schema": PostArgs,
        "description": "Create a new Bluesky post or thread",
        "tags": ["bluesky", "post", "create", "thread"]
    },
    {
        "func": get_bluesky_feed,
        "args_schema": FeedArgs,
        "description": "Retrieve a Bluesky feed (home timeline or custom feed)",
        "tags": ["bluesky", "feed", "timeline"]
    },
    # Note: attach_user_blocks is available on the server but not exposed to the agent
    # to prevent the agent from managing its own memory blocks
    {
        "func": detach_user_blocks,
        "args_schema": DetachUserBlocksArgs,
        "description": "Detach user-specific memory blocks from the agent. Blocks are preserved for later use.",
        "tags": ["memory", "blocks", "user"]
    },
    {
        "func": user_note_append,
        "args_schema": UserNoteAppendArgs,
        "description": "Append a note to a user's memory block. Creates the block if it doesn't exist.",
        "tags": ["memory", "blocks", "user", "append"]
    },
    {
        "func": user_note_replace,
        "args_schema": UserNoteReplaceArgs,
        "description": "Replace text in a user's memory block.",
        "tags": ["memory", "blocks", "user", "replace"]
    },
    {
        "func": user_note_set,
        "args_schema": UserNoteSetArgs,
        "description": "Set the complete content of a user's memory block.",
        "tags": ["memory", "blocks", "user", "set"]
    },
    {
        "func": user_note_view,
        "args_schema": UserNoteViewArgs,
        "description": "View the content of a user's memory block.",
        "tags": ["memory", "blocks", "user", "view"]
    },
    {
        "func": halt_activity,
        "args_schema": HaltArgs,
        "description": "Signal to halt all bot activity and terminate bsky.py",
        "tags": ["control", "halt", "terminate"]
    },
    {
        "func": add_post_to_bluesky_reply_thread,
        "args_schema": ReplyThreadPostArgs,
        "description": "Add a single post to the current Bluesky reply thread atomically",
        "tags": ["bluesky", "reply", "thread", "atomic"]
    },
    {
        "func": ignore_notification,
        "args_schema": IgnoreNotificationArgs,
        "description": "Explicitly ignore a notification without replying (useful for ignoring bot interactions)",
        "tags": ["notification", "ignore", "control", "bot"]
    },
    {
        "func": create_whitewind_blog_post,
        "args_schema": WhitewindPostArgs,
        "description": "Create a blog post on Whitewind with markdown support",
        "tags": ["whitewind", "blog", "post", "markdown"]
    },
    {
        "func": annotate_ack,
        "args_schema": AnnotateAckArgs,
        "description": "Add a note to the acknowledgment record for the current post interaction",
        "tags": ["acknowledgment", "note", "annotation", "metadata"]
    },
    {
        "func": fetch_webpage,
        "args_schema": WebpageArgs,
        "description": "Fetch a webpage and convert it to markdown/text format using Jina AI reader",
        "tags": ["web", "fetch", "webpage", "markdown", "jina"]
    },
]


def register_tools(agent_id: str = None, tools: List[str] = None):
    """Register tools with a Letta agent.

    Args:
        agent_id: ID of the agent to attach tools to. If None, uses config default.
        tools: List of tool names to register. If None, registers all tools.
    """
    # Use agent ID from config if not provided
    if agent_id is None:
        agent_id = letta_config['agent_id']
    
    try:
        # Initialize Letta client with API key and base_url from config
        client_params = {
            'token': letta_config['api_key'],
            'timeout': letta_config['timeout']
        }
        if letta_config.get('base_url'):
            client_params['base_url'] = letta_config['base_url']
        client = Letta(**client_params)

        # Get the agent by ID
        try:
            agent = client.agents.retrieve(agent_id=agent_id)
        except Exception as e:
            console.print(f"[red]Error: Agent '{agent_id}' not found[/red]")
            console.print(f"Error details: {e}")
            return

        # Filter tools if specific ones requested
        tools_to_register = TOOL_CONFIGS
        if tools:
            tools_to_register = [t for t in TOOL_CONFIGS if t["func"].__name__ in tools]
            if len(tools_to_register) != len(tools):
                missing = set(tools) - {t["func"].__name__ for t in tools_to_register}
                console.print(f"[yellow]Warning: Unknown tools: {missing}[/yellow]")

        # Create results table
        table = Table(title=f"Tool Registration for Agent '{agent.name}' ({agent_id})")
        table.add_column("Tool", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Description")

        # Register each tool
        for tool_config in tools_to_register:
            func = tool_config["func"]
            tool_name = func.__name__

            try:
                # Create or update the tool using the standalone function
                created_tool = client.tools.upsert_from_function(
                    func=func,
                    args_schema=tool_config["args_schema"],
                    tags=tool_config["tags"]
                )

                # Get current agent tools
                current_tools = client.agents.tools.list(agent_id=str(agent.id))
                tool_names = [t.name for t in current_tools]

                # Check if already attached
                if created_tool.name in tool_names:
                    table.add_row(tool_name, "Already Attached", tool_config["description"])
                else:
                    # Attach to agent
                    client.agents.tools.attach(
                        agent_id=str(agent.id),
                        tool_id=str(created_tool.id)
                    )
                    table.add_row(tool_name, "✓ Attached", tool_config["description"])

            except Exception as e:
                table.add_row(tool_name, f"✗ Error: {str(e)}", tool_config["description"])
                logger.error(f"Error registering tool {tool_name}: {e}")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        logger.error(f"Fatal error: {e}")


def list_available_tools():
    """List all available tools."""
    table = Table(title="Available Void Tools")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Description")
    table.add_column("Tags", style="dim")

    for tool_config in TOOL_CONFIGS:
        table.add_row(
            tool_config["func"].__name__,
            tool_config["description"],
            ", ".join(tool_config["tags"])
        )

    console.print(table)


def main():
    """Main CLI function for register tools."""
    import argparse

    parser = argparse.ArgumentParser(description="Register Void tools with a Letta agent")
    parser.add_argument("--agent-id", help=f"Agent ID (default: from config)")
    parser.add_argument("--tools", nargs="+", help="Specific tools to register (default: all)")
    parser.add_argument("--list", action="store_true", help="List available tools")

    args = parser.parse_args()

    if args.list:
        list_available_tools()
    else:
        # Use config default if no agent specified
        agent_id = args.agent_id if args.agent_id else letta_config['agent_id']
        console.print(f"\n[bold]Registering tools for agent: {agent_id}[/bold]\n")
        register_tools(agent_id, args.tools)


if __name__ == "__main__":
    main()
