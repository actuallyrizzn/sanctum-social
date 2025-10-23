"""
Unit tests for utils.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from utils.utils import upsert_block, upsert_agent


class TestUpsertBlock:
    """Test cases for upsert_block function."""
    
    def test_create_new_block(self, mock_letta_client):
        """Test creating a new block when none exists."""
        # Mock empty blocks list
        mock_letta_client.blocks.list.return_value = []
        
        # Mock block creation
        mock_block = Mock()
        mock_block.id = "test-block-id"
        mock_letta_client.blocks.create.return_value = mock_block
        
        result = upsert_block(
            mock_letta_client,
            "test-label",
            "test-value",
            description="Test block"
        )
        
        # Verify block creation was called
        mock_letta_client.blocks.create.assert_called_once_with(
            label="test-label",
            value="test-value",
            description="Test block"
        )
        assert result == mock_block
    
    def test_return_existing_block(self, mock_letta_client):
        """Test returning existing block when one exists."""
        # Mock existing block
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_existing_block.label = "test-label"
        mock_letta_client.blocks.list.return_value = [mock_existing_block]
        
        result = upsert_block(
            mock_letta_client,
            "test-label",
            "test-value"
        )
        
        # Verify no creation was called
        mock_letta_client.blocks.create.assert_not_called()
        assert result == mock_existing_block
    
    def test_multiple_blocks_error(self, mock_letta_client):
        """Test error when multiple blocks with same label exist."""
        # Mock multiple blocks with same label
        mock_block1 = Mock()
        mock_block1.label = "test-label"
        mock_block2 = Mock()
        mock_block2.label = "test-label"
        mock_letta_client.blocks.list.return_value = [mock_block1, mock_block2]
        
        with pytest.raises(Exception, match="2 blocks by the label 'test-label' retrieved"):
            upsert_block(mock_letta_client, "test-label", "test-value")
    
    def test_update_existing_block(self, mock_letta_client):
        """Test updating existing block when update=True."""
        # Mock existing block
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_letta_client.blocks.list.return_value = [mock_existing_block]
        
        # Mock block modification
        mock_updated_block = Mock()
        mock_letta_client.blocks.modify.return_value = mock_updated_block
        
        result = upsert_block(
            mock_letta_client,
            "test-label",
            "new-value",
            description="Updated description",
            update=True
        )
        
        # Verify block modification was called
        mock_letta_client.blocks.modify.assert_called_once_with(
            block_id="existing-block-id",
            label="test-label",
            value="new-value",
            description="Updated description"
        )
        assert result == mock_updated_block
    
    def test_update_existing_block_without_update_flag(self, mock_letta_client):
        """Test that existing block is returned when update=False."""
        # Mock existing block
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_letta_client.blocks.list.return_value = [mock_existing_block]
        
        result = upsert_block(
            mock_letta_client,
            "test-label",
            "new-value",
            description="Updated description",
            update=False
        )
        
        # Verify no modification was called
        mock_letta_client.blocks.modify.assert_not_called()
        assert result == mock_existing_block
    
    def test_kwargs_passed_to_create(self, mock_letta_client):
        """Test that additional kwargs are passed to block creation."""
        mock_letta_client.blocks.list.return_value = []
        
        mock_block = Mock()
        mock_letta_client.blocks.create.return_value = mock_block
        
        upsert_block(
            mock_letta_client,
            "test-label",
            "test-value",
            description="Test description",
            custom_field="custom_value"
        )
        
        mock_letta_client.blocks.create.assert_called_once_with(
            label="test-label",
            value="test-value",
            description="Test description",
            custom_field="custom_value"
        )
    
    def test_update_kwargs_exclude_update_flag(self, mock_letta_client):
        """Test that update flag is excluded from modification kwargs."""
        mock_existing_block = Mock()
        mock_existing_block.id = "existing-block-id"
        mock_letta_client.blocks.list.return_value = [mock_existing_block]
        
        mock_updated_block = Mock()
        mock_letta_client.blocks.modify.return_value = mock_updated_block
        
        upsert_block(
            mock_letta_client,
            "test-label",
            "new-value",
            description="Updated description",
            update=True,
            custom_field="custom_value"
        )
        
        # Verify update flag is not passed to modify
        call_args = mock_letta_client.blocks.modify.call_args[1]
        assert "update" not in call_args
        assert call_args["custom_field"] == "custom_value"


class TestUpsertAgent:
    """Test cases for upsert_agent function."""
    
    def test_create_new_agent(self, mock_letta_client):
        """Test creating a new agent when none exists."""
        # Mock empty agents list
        mock_letta_client.agents.list.return_value = []
        
        # Mock agent creation
        mock_agent = Mock()
        mock_agent.id = "test-agent-id"
        mock_letta_client.agents.create.return_value = mock_agent
        
        result = upsert_agent(
            mock_letta_client,
            "test-agent",
            model="openai/gpt-4o-mini",
            description="Test agent"
        )
        
        # Verify agent creation was called
        mock_letta_client.agents.create.assert_called_once_with(
            name="test-agent",
            model="openai/gpt-4o-mini",
            description="Test agent"
        )
        assert result == mock_agent
    
    def test_return_existing_agent(self, mock_letta_client):
        """Test returning existing agent when one exists."""
        # Mock existing agent
        mock_existing_agent = Mock()
        mock_existing_agent.id = "existing-agent-id"
        mock_existing_agent.name = "test-agent"
        mock_letta_client.agents.list.return_value = [mock_existing_agent]
        
        result = upsert_agent(
            mock_letta_client,
            "test-agent",
            model="openai/gpt-4o-mini"
        )
        
        # Verify no creation was called
        mock_letta_client.agents.create.assert_not_called()
        assert result == mock_existing_agent
    
    def test_multiple_agents_error(self, mock_letta_client):
        """Test error when multiple agents with same name exist."""
        # Mock multiple agents with same name
        mock_agent1 = Mock()
        mock_agent1.name = "test-agent"
        mock_agent2 = Mock()
        mock_agent2.name = "test-agent"
        mock_letta_client.agents.list.return_value = [mock_agent1, mock_agent2]
        
        with pytest.raises(Exception, match="2 agents by the name 'test-agent' retrieved"):
            upsert_agent(mock_letta_client, "test-agent", model="openai/gpt-4o-mini")
    
    def test_update_existing_agent(self, mock_letta_client):
        """Test updating existing agent."""
        # Mock existing agent
        mock_existing_agent = Mock()
        mock_existing_agent.id = "existing-agent-id"
        mock_letta_client.agents.list.return_value = [mock_existing_agent]
        
        # Mock agent modification
        mock_updated_agent = Mock()
        mock_letta_client.agents.modify.return_value = mock_updated_agent
        
        result = upsert_agent(
            mock_letta_client,
            "test-agent",
            model="openai/gpt-4o-mini",
            description="Updated description",
            update=True
        )
        
        # Verify agent modification was called
        mock_letta_client.agents.modify.assert_called_once_with(
            agent_id="existing-agent-id",
            model="openai/gpt-4o-mini",
            description="Updated description"
        )
        assert result == mock_updated_agent
    
    def test_kwargs_passed_to_create(self, mock_letta_client):
        """Test that additional kwargs are passed to agent creation."""
        mock_letta_client.agents.list.return_value = []
        
        mock_agent = Mock()
        mock_letta_client.agents.create.return_value = mock_agent
        
        upsert_agent(
            mock_letta_client,
            "test-agent",
            model="openai/gpt-4o-mini",
            description="Test agent",
            custom_field="custom_value"
        )
        
        mock_letta_client.agents.create.assert_called_once_with(
            name="test-agent",
            model="openai/gpt-4o-mini",
            description="Test agent",
            custom_field="custom_value"
        )
    
    def test_update_kwargs_exclude_update_flag(self, mock_letta_client):
        """Test that update flag is excluded from modification kwargs."""
        mock_existing_agent = Mock()
        mock_existing_agent.id = "existing-agent-id"
        mock_letta_client.agents.list.return_value = [mock_existing_agent]
        
        mock_updated_agent = Mock()
        mock_letta_client.agents.modify.return_value = mock_updated_agent
        
        upsert_agent(
            mock_letta_client,
            "test-agent",
            model="openai/gpt-4o-mini",
            description="Updated description",
            update=True,
            custom_field="custom_value"
        )
        
        # Verify update flag is not passed to modify
        call_args = mock_letta_client.agents.modify.call_args[1]
        assert "update" not in call_args
        assert call_args["custom_field"] == "custom_value"


class TestUtilsIntegration:
    """Integration tests for utils functions."""
    
    def test_upsert_block_with_real_client_structure(self):
        """Test upsert_block with a more realistic client structure."""
        # Create a more realistic mock client
        mock_client = Mock()
        mock_client.blocks = Mock()
        
        # Mock empty blocks list
        mock_client.blocks.list.return_value = []
        
        # Mock block creation
        mock_block = Mock()
        mock_block.id = "test-block-id"
        mock_block.label = "test-label"
        mock_client.blocks.create.return_value = mock_block
        
        result = upsert_block(
            mock_client,
            "test-label",
            "test-value",
            description="Test block"
        )
        
        # Verify the correct methods were called
        mock_client.blocks.list.assert_called_once_with(label="test-label")
        mock_client.blocks.create.assert_called_once()
        assert result == mock_block
    
    def test_upsert_agent_with_real_client_structure(self):
        """Test upsert_agent with a more realistic client structure."""
        # Create a more realistic mock client
        mock_client = Mock()
        mock_client.agents = Mock()
        
        # Mock empty agents list
        mock_client.agents.list.return_value = []
        
        # Mock agent creation
        mock_agent = Mock()
        mock_agent.id = "test-agent-id"
        mock_agent.name = "test-agent"
        mock_client.agents.create.return_value = mock_agent
        
        result = upsert_agent(
            mock_client,
            "test-agent",
            model="openai/gpt-4o-mini",
            description="Test agent"
        )
        
        # Verify the correct methods were called
        mock_client.agents.list.assert_called_once_with(name="test-agent")
        mock_client.agents.create.assert_called_once()
        assert result == mock_agent


@pytest.mark.parametrize("label,value,description", [
    ("test-label-1", "test-value-1", "Test description 1"),
    ("zeitgeist", "Current social environment", "Zeitgeist block"),
    ("void-persona", "My name is Void", "Persona block"),
    ("user_test.bsky.social", "User information", "User block"),
])
def test_upsert_block_with_different_labels(mock_letta_client, label, value, description):
    """Test upsert_block with different label types."""
    mock_letta_client.blocks.list.return_value = []
    
    mock_block = Mock()
    mock_letta_client.blocks.create.return_value = mock_block
    
    result = upsert_block(mock_letta_client, label, value, description=description)
    
    mock_letta_client.blocks.create.assert_called_once_with(
        label=label,
        value=value,
        description=description
    )
    assert result == mock_block


@pytest.mark.parametrize("name,model,description", [
    ("void", "openai/gpt-4o-mini", "Void agent"),
    ("test-agent", "openai/gpt-4o", "Test agent"),
    ("custom-agent", "anthropic/claude-3", "Custom agent"),
])
def test_upsert_agent_with_different_configs(mock_letta_client, name, model, description):
    """Test upsert_agent with different agent configurations."""
    mock_letta_client.agents.list.return_value = []
    
    mock_agent = Mock()
    mock_letta_client.agents.create.return_value = mock_agent
    
    result = upsert_agent(mock_letta_client, name, model=model, description=description)
    
    mock_letta_client.agents.create.assert_called_once_with(
        name=name,
        model=model,
        description=description
    )
    assert result == mock_agent
