import json
import pytest
import asyncio
from datetime import datetime, timedelta
from src.monitoring.metrics import MetricsCollector, ActionMetric
from src.monitoring.analytics import AnalyticsEngine
from src.monitoring.benchmarks import BenchmarkRunner


class TestActionMetric:
    """Tests for ActionMetric data class."""

    def test_action_metric_creation(self):
        """Test creating an ActionMetric."""
        metric = ActionMetric(
            action_type="generate",
            response_time=1.5,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            success=True,
            error=None,
            timestamp=datetime.now()
        )
        assert metric.action_type == "generate"
        assert metric.response_time == 1.5
        assert metric.input_tokens == 100
        assert metric.output_tokens == 50
        assert metric.total_tokens == 150
        assert metric.success is True
        assert metric.error is None

    def test_action_metric_with_error(self):
        """Test ActionMetric with error."""
        metric = ActionMetric(
            action_type="refactor",
            response_time=0.5,
            input_tokens=50,
            output_tokens=0,
            total_tokens=50,
            success=False,
            error="API rate limit exceeded"
        )
        assert metric.success is False
        assert metric.error == "API rate limit exceeded"


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_metrics_collector_initialization(self):
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()
        assert len(collector.metrics) == 0

    def test_record_metric(self):
        """Test recording a metric."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.5,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]
        assert metric.action_type == "generate"
        assert metric.response_time == 1.5
        assert metric.total_tokens == 150

    def test_record_metric_with_error(self):
        """Test recording a metric with error."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="test",
            response_time=0.2,
            input_tokens=50,
            output_tokens=0,
            success=False,
            error="Timeout"
        )
        assert len(collector.metrics) == 1
        assert collector.metrics[0].success is False
        assert collector.metrics[0].error == "Timeout"

    def test_record_multiple_metrics(self):
        """Test recording multiple metrics."""
        collector = MetricsCollector()
        for i in range(5):
            collector.record_metric(
                action_type="generate",
                response_time=1.0 + i*0.1,
                input_tokens=100,
                output_tokens=50,
                success=True
            )
        assert len(collector.metrics) == 5

    def test_get_action_stats_single_action(self):
        """Test getting stats for a single action."""
        collector = MetricsCollector()
        for i in range(3):
            collector.record_metric(
                action_type="generate",
                response_time=1.0 + i*0.1,
                input_tokens=100,
                output_tokens=50,
                success=True
            )

        stats = collector.get_action_stats("generate")
        assert stats["action_type"] == "generate"
        assert stats["count"] == 3
        assert "avg_response_time" in stats
        assert "min_response_time" in stats
        assert "max_response_time" in stats
        assert stats["success_count"] == 3
        assert stats["failure_count"] == 0

    def test_get_action_stats_with_failures(self):
        """Test action stats with failures."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="refactor",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        collector.record_metric(
            action_type="refactor",
            response_time=0.5,
            input_tokens=100,
            output_tokens=0,
            success=False,
            error="API error"
        )

        stats = collector.get_action_stats("refactor")
        assert stats["count"] == 2
        assert stats["success_count"] == 1
        assert stats["failure_count"] == 1
        assert stats["success_rate"] == 0.5

    def test_get_action_stats_nonexistent_action(self):
        """Test getting stats for non-existent action."""
        collector = MetricsCollector()
        stats = collector.get_action_stats("nonexistent")
        assert stats is None

    def test_get_all_stats(self):
        """Test getting stats for all actions."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        collector.record_metric(
            action_type="refactor",
            response_time=1.5,
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        all_stats = collector.get_all_stats()
        assert "generate" in all_stats
        assert "refactor" in all_stats
        assert len(all_stats) == 2

    def test_metrics_response_time_calculation(self):
        """Test response time calculation."""
        collector = MetricsCollector()
        response_times = [1.0, 1.2, 0.8, 1.5, 0.9]
        for rt in response_times:
            collector.record_metric(
                action_type="generate",
                response_time=rt,
                input_tokens=100,
                output_tokens=50,
                success=True
            )

        stats = collector.get_action_stats("generate")
        assert abs(stats["avg_response_time"] - 1.08) < 0.01
        assert stats["min_response_time"] == 0.8
        assert stats["max_response_time"] == 1.5

    def test_metrics_token_calculation(self):
        """Test token calculation."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=150,
            output_tokens=75,
            success=True
        )

        stats = collector.get_action_stats("generate")
        assert stats["total_tokens"] == 375  # (100+50) + (150+75)
        assert stats["total_input_tokens"] == 250
        assert stats["total_output_tokens"] == 125

    def test_clear_metrics(self):
        """Test clearing metrics."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        assert len(collector.metrics) == 1

        collector.clear()
        assert len(collector.metrics) == 0

    def test_metrics_to_json(self):
        """Test converting metrics to JSON."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        json_str = collector.to_json()
        data = json.loads(json_str)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["action_type"] == "generate"

    def test_get_action_stats_empty_collector(self):
        """Test stats on empty collector."""
        collector = MetricsCollector()
        stats = collector.get_all_stats()
        assert stats == {}

    def test_record_metric_calculates_total_tokens(self):
        """Test that total tokens are calculated correctly."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        metric = collector.metrics[0]
        assert metric.total_tokens == 150


class TestAnalyticsEngine:
    """Tests for AnalyticsEngine class."""

    def test_analytics_engine_initialization(self):
        """Test AnalyticsEngine initialization."""
        collector = MetricsCollector()
        engine = AnalyticsEngine(collector)
        assert engine.collector is collector

    def test_get_summary_report(self):
        """Test generating a summary report."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        collector.record_metric(
            action_type="refactor",
            response_time=1.5,
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        engine = AnalyticsEngine(collector)
        report = engine.get_summary_report()

        assert "total_requests" in report
        assert report["total_requests"] == 2
        assert "actions" in report
        assert "generate" in report["actions"]
        assert "refactor" in report["actions"]

    def test_get_token_usage_breakdown(self):
        """Test token usage breakdown."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        collector.record_metric(
            action_type="refactor",
            response_time=1.0,
            input_tokens=80,
            output_tokens=40,
            success=True
        )

        engine = AnalyticsEngine(collector)
        breakdown = engine.get_token_usage_breakdown()

        assert "total_tokens" in breakdown
        assert breakdown["total_tokens"] == 270  # (100+50) + (80+40)
        assert "generate" in breakdown
        assert "refactor" in breakdown
        assert breakdown["generate"]["total"] == 150
        assert breakdown["refactor"]["total"] == 120

    def test_estimate_cost(self):
        """Test cost estimation."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        engine = AnalyticsEngine(collector)
        cost = engine.estimate_cost()

        assert isinstance(cost, (int, float))
        assert cost >= 0

    def test_estimate_cost_by_action(self):
        """Test cost estimation by action."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=1000,
            output_tokens=500,
            success=True
        )

        engine = AnalyticsEngine(collector)
        cost_by_action = engine.estimate_cost_by_action()

        assert "generate" in cost_by_action
        assert cost_by_action["generate"] >= 0

    def test_get_response_time_distribution(self):
        """Test response time distribution."""
        collector = MetricsCollector()
        for i in range(10):
            collector.record_metric(
                action_type="generate",
                response_time=0.5 + i*0.1,
                input_tokens=100,
                output_tokens=50,
                success=True
            )

        engine = AnalyticsEngine(collector)
        distribution = engine.get_response_time_distribution()

        assert "min" in distribution
        assert "max" in distribution
        assert "mean" in distribution
        assert "median" in distribution

    def test_get_success_rate(self):
        """Test success rate calculation."""
        collector = MetricsCollector()
        for i in range(8):
            collector.record_metric(
                action_type="generate",
                response_time=1.0,
                input_tokens=100,
                output_tokens=50,
                success=True
            )
        for i in range(2):
            collector.record_metric(
                action_type="generate",
                response_time=1.0,
                input_tokens=100,
                output_tokens=0,
                success=False,
                error="API error"
            )

        engine = AnalyticsEngine(collector)
        rate = engine.get_success_rate()

        assert rate == 0.8

    def test_get_success_rate_by_action(self):
        """Test success rate by action."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=0,
            success=False,
            error="API error"
        )

        engine = AnalyticsEngine(collector)
        rates = engine.get_success_rate_by_action()

        assert "generate" in rates
        assert rates["generate"] == 0.5

    def test_get_report_as_json(self):
        """Test getting report as JSON."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        engine = AnalyticsEngine(collector)
        json_str = engine.get_report_as_json()
        report = json.loads(json_str)

        assert "summary" in report
        assert "token_breakdown" in report
        assert "success_rates" in report


class TestBenchmarkRunner:
    """Tests for BenchmarkRunner class."""

    def test_benchmark_runner_initialization(self):
        """Test BenchmarkRunner initialization."""
        runner = BenchmarkRunner()
        assert runner.results == {}

    def test_run_benchmark(self):
        """Test running a benchmark."""
        def dummy_operation():
            return "result"

        runner = BenchmarkRunner()
        runner.run_benchmark("dummy", dummy_operation, iterations=5)

        assert "dummy" in runner.results
        result = runner.results["dummy"]
        assert result["iterations"] == 5
        assert "total_time" in result
        assert "avg_time" in result

    def test_benchmark_multiple_operations(self):
        """Test benchmarking multiple operations."""
        def op1():
            return 1

        def op2():
            return 2

        runner = BenchmarkRunner()
        runner.run_benchmark("op1", op1, iterations=3)
        runner.run_benchmark("op2", op2, iterations=3)

        assert len(runner.results) == 2
        assert "op1" in runner.results
        assert "op2" in runner.results

    def test_benchmark_comparison(self):
        """Test benchmark comparison."""
        def slow_op():
            import time
            time.sleep(0.01)

        def fast_op():
            pass

        runner = BenchmarkRunner()
        runner.run_benchmark("slow", slow_op, iterations=2)
        runner.run_benchmark("fast", fast_op, iterations=2)

        assert runner.results["slow"]["avg_time"] > runner.results["fast"]["avg_time"]

    def test_benchmark_results_as_dict(self):
        """Test getting benchmark results as dict."""
        def dummy():
            return 1

        runner = BenchmarkRunner()
        runner.run_benchmark("test", dummy, iterations=2)

        results_dict = runner.get_results()
        assert isinstance(results_dict, dict)
        assert "test" in results_dict

    def test_benchmark_results_as_json(self):
        """Test getting benchmark results as JSON."""
        def dummy():
            return 1

        runner = BenchmarkRunner()
        runner.run_benchmark("test", dummy, iterations=2)

        json_str = runner.get_results_as_json()
        data = json.loads(json_str)
        assert "test" in data


class TestMetricsIntegration:
    """Integration tests for metrics system."""

    def test_metrics_workflow(self):
        """Test complete metrics workflow."""
        collector = MetricsCollector()

        # Simulate multiple actions
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        collector.record_metric(
            action_type="generate",
            response_time=1.1,
            input_tokens=120,
            output_tokens=60,
            success=True
        )
        collector.record_metric(
            action_type="refactor",
            response_time=1.5,
            input_tokens=100,
            output_tokens=50,
            success=True
        )
        collector.record_metric(
            action_type="refactor",
            response_time=0.5,
            input_tokens=50,
            output_tokens=0,
            success=False,
            error="Timeout"
        )

        # Analyze metrics
        engine = AnalyticsEngine(collector)
        report = engine.get_summary_report()

        assert report["total_requests"] == 4
        assert len(report["actions"]) == 2
        assert report["overall_success_rate"] == 0.75

    def test_metrics_with_different_actions(self):
        """Test metrics with all action types."""
        collector = MetricsCollector()

        actions = ["generate", "refactor", "test", "explain", "fix", "chat"]
        for action in actions:
            collector.record_metric(
                action_type=action,
                response_time=1.0,
                input_tokens=100,
                output_tokens=50,
                success=True
            )

        all_stats = collector.get_all_stats()
        assert len(all_stats) == 6
        for action in actions:
            assert action in all_stats

    def test_analytics_with_empty_metrics(self):
        """Test analytics with empty metrics."""
        collector = MetricsCollector()
        engine = AnalyticsEngine(collector)

        report = engine.get_summary_report()
        assert report["total_requests"] == 0
        assert report["overall_success_rate"] == 0


class TestMetricsJSONSerialization:
    """Tests for JSON serialization of metrics."""

    def test_action_metric_to_dict(self):
        """Test converting ActionMetric to dict."""
        metric = ActionMetric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            success=True,
            error=None
        )

        # Convert to dict manually (ActionMetric is a dataclass)
        metric_dict = {
            "action_type": metric.action_type,
            "response_time": metric.response_time,
            "input_tokens": metric.input_tokens,
            "output_tokens": metric.output_tokens,
            "total_tokens": metric.total_tokens,
            "success": metric.success,
            "error": metric.error,
        }

        assert metric_dict["action_type"] == "generate"
        assert metric_dict["total_tokens"] == 150

    def test_metrics_collector_json_has_timestamp(self):
        """Test that metrics JSON includes timestamp."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.0,
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        json_str = collector.to_json()
        data = json.loads(json_str)

        assert "timestamp" in data[0]

    def test_metrics_json_structure(self):
        """Test metrics JSON structure."""
        collector = MetricsCollector()
        collector.record_metric(
            action_type="generate",
            response_time=1.5,
            input_tokens=100,
            output_tokens=50,
            success=True
        )

        json_str = collector.to_json()
        data = json.loads(json_str)

        metric = data[0]
        assert metric["action_type"] == "generate"
        assert metric["response_time"] == 1.5
        assert metric["input_tokens"] == 100
        assert metric["output_tokens"] == 50
        assert metric["total_tokens"] == 150
        assert metric["success"] is True
        assert metric["error"] is None
