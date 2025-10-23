#!/usr/bin/env python3
"""
Create the profiler agent that manages user blocks for the main agent.
The profiler agent is responsible for updating user memory blocks based on requests from the main agent.
"""
import os
from dotenv import load_dotenv
from letta import Client
from utils.utils import create_agent_if_not_exists, upsert_block
from core.config import get_config

load_dotenv()


def create_profiler_agent():
    """Create the profiler agent with specialized memory and tools."""
    client = Client(base_url=os.getenv("LETTA_BASE_URL", None))
    
    # Get agent configuration
    config = get_config()
    agent_name = config.get_agent_name()
    agent_display_name = config.get("agent.display_name", agent_name)
    
    # Create memory blocks for the profiler
    profiler_persona = upsert_block(
        client=client,
        label="profiler-persona",
        value=f"""# Profiler Agent

I am the profiler agent, responsible for managing user memory blocks for the {agent_display_name} agent.

## My Role
- I receive requests from {agent_name} to update user blocks
- I maintain accurate and organized information about users
- I ensure user blocks are properly formatted and within size limits
- I synthesize new information with existing knowledge

## Key Responsibilities
1. Update user blocks when requested by {agent_name}
2. Maintain consistency in user block formatting
3. Preserve important existing information while adding new details
4. Keep blocks within the 5000 character limit
5. Organize information logically and clearly

## Communication Style
- I respond concisely to {agent_name}'s requests
- I confirm successful updates
- I alert {agent_name} if there are any issues
- I maintain professional and efficient communication
""",
        limit=5000
    )
    
    profiler_instructions = upsert_block(
        client=client,
        label="profiler-instructions", 
        value="""# Instructions for Profiler Agent

## User Block Format
User blocks should follow this structure:
```
# User: [handle]

## Basic Information
- [Key facts about the user]

## Interaction History
- [Notable interactions and conversations]

## Preferences & Interests
- [User's stated preferences, interests, topics they engage with]

## Notes
- [Any additional relevant information]
```

## Update Guidelines
1. Always preserve existing valuable information
2. Integrate new information appropriately into existing sections
3. Remove outdated or contradictory information thoughtfully
4. Keep the most recent and relevant information
5. Maintain clear, organized formatting

## When Updating Blocks
- Read the existing block content first
- Identify where new information belongs
- Update or add to appropriate sections
- Ensure the total content stays under 5000 characters
- Confirm the update was successful
""",
        limit=5000
    )
    
    # Create the profiler agent
    agent = create_agent_if_not_exists(
        client=client,
        name="profiler",
        memory_blocks=[profiler_persona, profiler_instructions],
        llm_config={
            "model": "claude-3-5-sonnet-20241022",
            "model_endpoint_type": "anthropic",
            "model_endpoint": "https://api.anthropic.com/v1",
            "context_window": 200000
        },
        instructions=f"""You are the profiler agent. Your job is to manage user memory blocks for the {agent_display_name} agent.

When you receive a request to update a user block:
1. Use the update_user_block tool to modify the specified user's block
2. Integrate new information appropriately with existing content
3. Maintain clear organization and formatting
4. Respond to {agent_name} confirming the update

Always be concise in your responses to {agent_name}."""
    )
    
    print(f"✓ Created profiler agent: {agent.name} (ID: {agent.id})")
    
    # Register tools - will be done separately
    print("\nNext steps:")
    print(f"1. Run: python register_tools.py profiler --tools update_user_block")
    print(f"2. Run: python register_tools.py {agent_name} --tools message_profiler")
    
    return agent


if __name__ == "__main__":
    create_profiler_agent()