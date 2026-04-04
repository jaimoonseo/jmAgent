"""Benchmarking utilities for performance testing."""

import json
import time
from typing import Callable, Dict, Any


class BenchmarkRunner:
    """Runs benchmarks on operations and collects results."""

    def __init__(self):
        """Initialize the benchmark runner."""
        self.results: Dict[str, Dict[str, Any]] = {}

    def run_benchmark(
        self,
        name: str,
        operation: Callable,
        iterations: int = 10,
    ) -> None:
        """
        Run a benchmark on an operation.

        Args:
            name: Name of the benchmark
            operation: Callable to benchmark
            iterations: Number of iterations to run
        """
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            try:
                operation()
            finally:
                end = time.perf_counter()
                times.append(end - start)

        total_time = sum(times)
        avg_time = total_time / iterations
        min_time = min(times)
        max_time = max(times)

        self.results[name] = {
            "iterations": iterations,
            "total_time": total_time,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
        }

    def get_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Get benchmark results.

        Returns:
            Dictionary of benchmark results
        """
        return self.results

    def get_results_as_json(self) -> str:
        """
        Get benchmark results as JSON.

        Returns:
            JSON string of benchmark results
        """
        return json.dumps(self.results, indent=2)

    def clear(self) -> None:
        """Clear all benchmark results."""
        self.results.clear()
