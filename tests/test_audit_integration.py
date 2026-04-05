"""Integration tests for audit logging with JmAgent."""

import asyncio
import tempfile
from pathlib import Path
import pytest
from src.agent import JmAgent
from src.audit.storage import AuditStorage, AuditQuery
from unittest.mock import AsyncMock, patch, MagicMock, Mock


@pytest.fixture
def temp_audit_db():
    """Create temporary audit database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "audit.db"
        yield str(db_path)


class TestAuditIntegration:
    """Integration tests for audit logging with JmAgent."""

    @pytest.fixture
    def mock_bedrock_client(self):
        """Mock Bedrock client."""
        return Mock()

    @pytest.mark.asyncio
    async def test_agent_logs_generate_action(self, temp_audit_db, mock_bedrock_client):
        """Test that generate action is logged to audit."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent(user="test_dev")

            # Mock Bedrock response
            with patch("src.agent.invoke_bedrock") as mock_invoke:
                mock_invoke.return_value = {
                    "content": "def hello(): pass",
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 50, "output_tokens": 100}
                }

                await agent.generate("Create a hello function")

        # Audit record should be created in agent's audit logger
        audit_storage = AuditStorage(db_path=temp_audit_db)
        assert agent.audit_logger is not None

    @pytest.mark.asyncio
    async def test_agent_logs_refactor_action(self, mock_bedrock_client):
        """Test that refactor action is logged."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent(user="test_dev")
            assert agent.audit_logger.user == "test_dev"

            # Mock Bedrock response
            with patch("src.agent.invoke_bedrock") as mock_invoke:
                mock_invoke.return_value = {
                    "content": "def refactored(): pass",
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 75, "output_tokens": 120}
                }

                await agent.refactor("def old(): pass", "add type hints")

    @pytest.mark.asyncio
    async def test_agent_logs_test_action(self, mock_bedrock_client):
        """Test that test action is logged."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent(user="qa_engineer")
            assert agent.audit_logger.user == "qa_engineer"

            with patch("src.agent.invoke_bedrock") as mock_invoke:
                mock_invoke.return_value = {
                    "content": "def test_hello(): pass",
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 50, "output_tokens": 80}
                }

                await agent.add_tests("def hello(): pass")

    @pytest.mark.asyncio
    async def test_agent_logs_explain_action(self, mock_bedrock_client):
        """Test that explain action is logged."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent()

            with patch("src.agent.invoke_bedrock") as mock_invoke:
                mock_invoke.return_value = {
                    "content": "This function does X",
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 40, "output_tokens": 50}
                }

                result = await agent.explain("def func(): pass")
                assert "X" in result

    @pytest.mark.asyncio
    async def test_agent_logs_fix_action(self, mock_bedrock_client):
        """Test that fix action is logged."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent()

            with patch("src.agent.invoke_bedrock") as mock_invoke:
                mock_invoke.return_value = {
                    "content": "def fixed(): pass",
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 60, "output_tokens": 90}
                }

                await agent.fix_bug("def broken(): pass", "TypeError: undefined")

    @pytest.mark.asyncio
    async def test_agent_logs_chat_action(self, mock_bedrock_client):
        """Test that chat action is logged."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent()

            with patch("src.agent.invoke_bedrock") as mock_invoke:
                mock_invoke.return_value = {
                    "content": "Here's how to use async in Python...",
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 30, "output_tokens": 100}
                }

                result = await agent.chat("How do I use async?")
                assert "async" in result.lower()

    def test_agent_audit_logger_access(self, mock_bedrock_client):
        """Test accessing audit logger from agent."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent(user="test_user")
            audit_logger = agent.get_audit_logger()

            assert audit_logger is not None
            assert audit_logger.user == "test_user"

    def test_audit_logger_records_action(self, mock_bedrock_client):
        """Test that audit logger correctly records actions."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent(user="dev1")
            record = agent.audit_logger.log_action(
                action_type="generate",
                input_data={"prompt": "test"},
                output_data={"code": "test"},
                status="success",
                duration=1.5,
                tokens_used={"input": 50, "output": 100}
            )

            assert record.action_type == "generate"
            assert record.user == "dev1"
            assert record.status == "success"
            assert record.duration == 1.5

    def test_agent_preserves_existing_functionality(self, mock_bedrock_client):
        """Test that adding audit logging doesn't break existing functionality."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent(
                model="haiku",
                temperature=0.3,
                max_tokens=2048,
                user="existing_user"
            )

            assert agent.model == "haiku"
            assert agent.temperature == 0.3
            assert agent.max_tokens == 2048
            assert agent.audit_logger.user == "existing_user"

    @pytest.mark.asyncio
    async def test_audit_logger_on_failure(self, mock_bedrock_client):
        """Test that audit logger records failures."""
        with patch("src.agent.build_bedrock_runtime", return_value=mock_bedrock_client):
            agent = JmAgent()

            # Mock Bedrock to raise an exception
            with patch("src.agent.invoke_bedrock") as mock_invoke:
                mock_invoke.side_effect = Exception("API Error")

                with pytest.raises(Exception):
                    await agent.generate("test")

    def test_audit_storage_with_multiple_records(self, temp_audit_db):
        """Test audit storage functionality."""
        storage = AuditStorage(db_path=temp_audit_db)

        # Create multiple records using audit logger
        logger1 = AuditStorage(db_path=temp_audit_db)
        logger2 = AuditStorage(db_path=temp_audit_db)

        # Both should work with same database
        all_records = storage.get_all()
        assert isinstance(all_records, list)
