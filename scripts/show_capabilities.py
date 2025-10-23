#!/usr/bin/env python3
"""
Show the current capabilities of both agents.
"""

import os
from letta_client import Letta
from core.config import get_config

def show_agent_capabilities():
    """Display the capabilities of both agents."""
    
    client = Letta(token=os.environ["LETTA_API_KEY"])
    
    # Get agent configuration
    config = get_config()
    agent_name = config.get_agent_name()
    agent_display_name = config.get("agent.display_name", agent_name)
    
    print("🤖 LETTA AGENT CAPABILITIES")
    print("=" * 50)
    
    # Profile Researcher Agent
    researchers = client.agents.list(name="profile-researcher")
    if researchers:
        researcher = researchers[0]
        print(f"\n📊 PROFILE RESEARCHER AGENT")
        print(f"   ID: {researcher.id}")
        print(f"   Name: {researcher.name}")
        
        researcher_tools = client.agents.tools.list(agent_id=researcher.id)
        print(f"   Tools ({len(researcher_tools)}):")
        for tool in researcher_tools:
            print(f"     - {tool.name}")
        
        researcher_blocks = client.agents.blocks.list(agent_id=researcher.id)
        print(f"   Memory Blocks ({len(researcher_blocks)}):")
        for block in researcher_blocks:
            print(f"     - {block.label}")
    
    # Main Agent
    agents = client.agents.list(name=agent_name)
    if agents:
        agent = agents[0]
        print(f"\n🌌 {agent_display_name.upper()} AGENT")
        print(f"   ID: {agent.id}")
        print(f"   Name: {agent.name}")
        
        agent_tools = client.agents.tools.list(agent_id=agent.id)
        print(f"   Tools ({len(agent_tools)}):")
        for tool in agent_tools:
            print(f"     - {tool.name}")
        
        agent_blocks = client.agents.blocks.list(agent_id=agent.id)
        print(f"   Memory Blocks ({len(agent_blocks)}):")
        for block in agent_blocks:
            print(f"     - {block.label}")
    
    print(f"\n🔄 WORKFLOW")
    print(f"   1. Profile Researcher: attach_user_block → research_bluesky_profile → update_user_block → detach_user_block")
    print(f"   2. {agent_display_name} Agent: Can attach/detach same user blocks for personalized interactions")
    print(f"   3. Shared Memory: Both agents can access the same user-specific blocks")
    
    print(f"\n💡 USAGE EXAMPLES")
    print(f"   Profile Researcher: 'Research @cameron.pfiffer.org and store findings'")
    print(f"   {agent_display_name} Agent: 'Attach user block for cameron.pfiffer.org before responding'")

if __name__ == "__main__":
    show_agent_capabilities()