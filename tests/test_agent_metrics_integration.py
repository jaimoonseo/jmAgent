"""Integration tests for metrics collection in JmAgent."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.agent import JmAgent
from src.models.response import BedrockResponse


@pytest.fixture
def agent():
    """Create a JmAgent instance with mocked Bedrock client."""
    with patch("src.agent.build_bedrock_runtime"):
        return JmAgent(model="haiku")


class TestJmAgentMetricsIntegration:
    """Tests for metrics collection in JmAgent."""

    def test_agent_has_metrics_collector(self, agent):
        """Test that JmAgent has a metrics collector."""
        assert agent.metrics is not None
        from src.monitoring.metrics import MetricsCollector
        assert isinstance(agent.metrics, MetricsCollector)

    def test_agent_metrics_initially_empty(self, agent):
        """Test that metrics are empty on initialization."""
        assert len(agent.metrics.metrics) == 0

    @pytest.mark.asyncio
    async def test_metrics_recorded_on_successful_bedrock_call(self, agent):
        """Test that metrics are recorded on successful Bedrock call."""
        # Mock the actual Bedrock invocation
        with patch("src.agent.invoke_bedrock") as mock_invoke:
            mock_invoke.return_value = {
                "content": "def hello():\n    return 'world'",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 50, "output_tokens": 20}
            }

            response = await agent._call_bedrock("generate", "Create a hello function")

            # Verify metrics were recorded
            assert len(agent.metrics.metrics) == 1
            metric = agent.metrics.metrics[0]
            assert metric.action_type == "generate"
            assert metric.success is True
            assert metric.input_tokens == 50
            assert metric.output_tokens == 20
            assert metric.total_tokens == 70

    @pytest.mark.asyncio
    async def test_metrics_recorded_on_failed_bedrock_call(self, agent):
        """Test that metrics are recorded on failed Bedrock call."""
        # Mock Bedrock invocation that raises an exception
        with patch("src.agent.invoke_bedrock") as mock_invoke:
            mock_invoke.side_effect = Exception("API error")

            with pytest.raises(Exception):
                await agent._call_bedrock("generate", "Create a hello function")

            # Metrics should still be recorded with failure
            assert len(agent.metrics.metrics) == 1
            metric = agent.metrics.metrics[0]
            assert metric.success is False
            assert metric.error == "API error"

    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, agent):
        """Test getting metrics summary."""
        # Record some metrics
        agent.metrics.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        agent.metrics.record_metric(
            action_type="refactor",
            response_time=1.5,
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        summary = agent.get_metrics_summary()
        assert "generate" in summary
        assert "refactor" in summary
        assert summary["generate"]["count"] == 1
        assert summary["refactor"]["count"] == 1

    def test_clear_metrics(self, agent):
        """Test clearing metrics."""
        agent.metrics.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        assert len(agent.metrics.metrics) == 1

        agent.clear_metrics()
        assert len(agent.metrics.metrics) == 0

    def test_get_metrics_collector(self, agent):
        """Test getting the metrics collector instance."""
        collector = agent.get_metrics()
        assert collector is agent.metrics


class TestMetricsWithMultipleActions:
    """Tests for metrics across multiple actions."""

    @pytest.fixture
    def agent_with_metrics(self):
        """Create agent and record various metrics."""
        with patch("src.agent.build_bedrock_runtime"):
            agent = JmAgent(model="haiku")

            # Record metrics for different actions
            for action in ["generate", "refactor", "test"]:
                agent.metrics.record_metric(
                    action_type=action,
                    response_time=1.0,
                    input_tokens=100,
                    output_tokens=50,
                    success=True
                )

            return agent

    def test_metrics_separate_by_action(self, agent_with_metrics):
        """Test that metrics are separated by action type."""
        stats = agent_with_metrics.get_metrics_summary()
        assert len(stats) == 3
        assert all(action in stats for action in ["generate", "refactor", "test"])

    def test_metrics_count_across_actions(self, agent_with_metrics):
        """Test total metric count."""
        assert len(agent_with_metrics.metrics.metrics) == 3

    def test_metrics_success_rate(self, agent_with_metrics):
        """Test success rate calculation."""
        stats = agent_with_metrics.get_metrics_summary()
        for action, action_stats in stats.items():
            assert action_stats["success_rate"] == 1.0


class TestMetricsWithAnalytics:
    """Tests for analytics engine with JmAgent metrics."""

    @pytest.fixture
    def agent_with_analytics(self):
        """Create agent with recorded metrics."""
        with patch("src.agent.build_bedrock_runtime"):
            agent = JmAgent(model="haiku")

            # Record various metrics
            for i in range(5):
                agent.metrics.record_metric(
                    action_type="generate",
                    response_time=1.0 + i*0.1,
                    input_tokens=100,
                    output_tokens=50,
                    success=True if i < 4 else False,
                    error=None if i < 4 else "Test failure"
                )

            return agent

    def test_analytics_engine_creation(self, agent_with_analytics):
        """Test creating analytics engine from agent metrics."""
        from src.monitoring.analytics import AnalyticsEngine
        engine = AnalyticsEngine(agent_with_analytics.metrics)
        assert engine.collector is agent_with_analytics.metrics

    def test_analytics_summary_report(self, agent_with_analytics):
        """Test generating summary report from agent metrics."""
        from src.monitoring.analytics import AnalyticsEngine
        engine = AnalyticsEngine(agent_with_analytics.metrics)
        report = engine.get_summary_report()

        assert report["total_requests"] == 5
        assert report["total_success"] == 4
        assert report["total_failures"] == 1
        assert report["overall_success_rate"] == 0.8

    def test_analytics_token_breakdown(self, agent_with_analytics):
        """Test token usage breakdown from agent metrics."""
        from src.monitoring.analytics import AnalyticsEngine
        engine = AnalyticsEngine(agent_with_analytics.metrics)
        breakdown = engine.get_token_usage_breakdown()

        assert "generate" in breakdown
        assert breakdown["total_tokens"] == 750  # 5 * (100+50)

    def test_analytics_cost_estimation(self, agent_with_analytics):
        """Test cost estimation from agent metrics."""
        from src.monitoring.analytics import AnalyticsEngine
        engine = AnalyticsEngine(agent_with_analytics.metrics)
        cost = engine.estimate_cost()

        # Should be a positive number
        assert isinstance(cost, (int, float))
        assert cost > 0
