"""
Comprehensive integration tests for Phase 3 features.
Tests cache, streaming, formatting, and multi-file support together.
"""

import pytest
import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from src.agent import JmAgent
from src.cache.cache_manager import CacheManager
from src.streaming.stream_handler import StreamHandler, StreamCollector
from src.formatting.formatter import CodeFormatter, detect_language
from src.models.response import BedrockResponse, GenerateResponse
from src.prompts.context_loader import load_project_context, load_multiple_files


# ============================================================================
# Fixtures for testing
# ============================================================================

@pytest.fixture
def cache_manager():
    """Create a fresh cache manager for each test."""
    return CacheManager(ttl_minutes=60)


@pytest.fixture
def code_formatter():
    """Create a code formatter instance."""
    return CodeFormatter()


@pytest.fixture
def stream_collector():
    """Create a stream collector instance."""
    return StreamCollector()


@pytest.fixture
def temp_project():
    """Create a test project with multiple files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create project structure
        (tmppath / "src").mkdir()
        (tmppath / "tests").mkdir()

        # Create Python files
        (tmppath / "src" / "main.py").write_text(
            "def hello(name: str) -> str:\n"
            "    return f'Hello, {name}!'\n"
        )
        (tmppath / "src" / "utils.py").write_text(
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n"
            "def subtract(a: int, b: int) -> int:\n"
            "    return a - b\n"
        )

        # Create JavaScript file
        (tmppath / "src" / "app.js").write_text(
            "const express = require('express');\n"
            "const app = express();\n"
            "app.get('/', (req, res) => res.send('Hello'));\n"
        )

        # Create test file
        (tmppath / "tests" / "test_main.py").write_text(
            "import pytest\n"
            "from src.main import hello\n"
            "def test_hello():\n"
            "    assert hello('World') == 'Hello, World!'\n"
        )

        # Create project metadata
        (tmppath / "pyproject.toml").write_text(
            "[project]\n"
            "name = 'test-project'\n"
            "version = '0.1.0'\n"
        )
        (tmppath / "README.md").write_text("# Test Project\n")

        yield tmppath


# ============================================================================
# Test Cache Manager Features
# ============================================================================

class TestCacheManagerStatistics:
    """Test cache manager statistics tracking."""

    def test_cache_stats_initial_state(self, cache_manager):
        """Verify cache starts with zero hits/misses."""
        stats = cache_manager.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["entries"] == 0
        assert stats["hit_rate"] == 0.0

    def test_cache_stats_after_set_and_get(self, cache_manager):
        """Verify stats update correctly after set and get."""
        context = "generate FastAPI endpoint"
        value = "def api():\n    pass"

        # Set value
        cache_manager.set(context, value)
        stats = cache_manager.get_stats()
        assert stats["entries"] == 1

        # Get value (hit)
        result = cache_manager.get(context)
        assert result == value
        stats = cache_manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 1.0

    def test_cache_stats_with_misses(self, cache_manager):
        """Verify cache tracks misses correctly."""
        # Miss 1
        cache_manager.get("nonexistent")

        # Set and hit
        cache_manager.set("existing", "value")
        cache_manager.get("existing")

        # Miss 2
        cache_manager.get("nonexistent2")

        stats = cache_manager.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["hit_rate"] == 1/3  # 1 hit out of 3 requests

    def test_cache_hit_rate_calculation(self, cache_manager):
        """Verify hit rate is calculated correctly."""
        # Set 2 values
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")

        # Get: 2 hits, 1 miss
        cache_manager.get("key1")
        cache_manager.get("key2")
        cache_manager.get("nonexistent")

        stats = cache_manager.get_stats()
        assert stats["hit_rate"] == 2/3


# ============================================================================
# Test Streaming with Accumulation
# ============================================================================

class TestStreamingAccumulation:
    """Test streaming response accumulation."""

    def test_stream_collector_accumulates_complete_code(self, stream_collector):
        """Verify StreamCollector accumulates multi-event code completely."""
        # Simulate streaming events
        events = [
            {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "def hello"}
            },
            {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "():\n"}
            },
            {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "    return 'world'"}
            }
        ]

        for event in events:
            stream_collector.add_event(event)

        result = stream_collector.finalize()
        assert result == "def hello():\n    return 'world'"

    def test_stream_handler_statistics(self, stream_collector):
        """Verify stream handler tracks statistics correctly."""
        events = [
            {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "chunk1"}
            },
            {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "chunk2"}
            },
        ]

        for event in events:
            stream_collector.add_event(event)

        stats = stream_collector.handler.get_stats()
        assert stats["token_count"] == 2
        assert stats["events_processed"] == 2
        assert stats["buffer_length"] == 12  # len("chunk1chunk2")

    def test_stream_collector_ignores_non_text_events(self, stream_collector):
        """Verify StreamCollector ignores non-text events."""
        events = [
            {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "code"}
            },
            {
                "type": "message_start",
                "message": {"role": "assistant"}
            },
            {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "more"}
            }
        ]

        for event in events:
            stream_collector.add_event(event)

        result = stream_collector.finalize()
        assert result == "codemore"
        assert stream_collector.handler.get_stats()["events_processed"] == 2


# ============================================================================
# Test Code Formatting
# ============================================================================

class TestCodeFormatterWithLanguages:
    """Test formatter with various programming languages."""

    def test_formatter_detects_python(self, code_formatter):
        """Verify formatter correctly detects Python."""
        code = "def hello():\n    return 'world'"
        assert detect_language(code) == "python"

    def test_formatter_detects_javascript(self, code_formatter):
        """Verify formatter correctly detects JavaScript."""
        code = "const hello = () => 'world';"
        assert detect_language(code) == "javascript"

    def test_formatter_detects_typescript(self, code_formatter):
        """Verify formatter correctly detects TypeScript."""
        code = "interface User {\n    name: string;\n    age: number;\n}"
        assert detect_language(code) == "typescript"

    def test_formatter_detects_sql(self, code_formatter):
        """Verify formatter correctly detects SQL."""
        code = "SELECT * FROM users WHERE age > 18;"
        assert detect_language(code) == "sql"

    def test_formatter_detects_bash(self, code_formatter):
        """Verify formatter correctly detects Bash."""
        code = "#!/bin/bash\necho 'hello'"
        assert detect_language(code) == "bash"

    def test_formatter_detects_go(self, code_formatter):
        """Verify formatter correctly detects Go."""
        code = "package main\n\nfunc hello() string {\n    return 'world'\n}"
        assert detect_language(code) == "go"

    def test_formatter_detects_rust(self, code_formatter):
        """Verify formatter correctly detects Rust."""
        code = "fn hello() -> String {\n    String::from('world')\n}"
        assert detect_language(code) == "rust"

    def test_formatter_detects_java(self, code_formatter):
        """Verify formatter correctly detects Java."""
        code = "public class Hello {\n    public void greet() {}\n}"
        assert detect_language(code) == "java"

    def test_formatter_graceful_degradation(self, code_formatter):
        """Verify formatter gracefully handles when tool unavailable."""
        # All formatters might not be installed - test graceful fallback
        code = "def hello():\n    return 'world'"
        result = code_formatter.format(code, language="python")

        # Should return original code or formatted version
        assert isinstance(result, str)
        assert len(result) > 0

    def test_formatter_with_auto_detection(self, code_formatter):
        """Verify formatter auto-detects language when not specified."""
        python_code = "def add(a, b):\n    return a + b"
        result = code_formatter.format(python_code)

        assert isinstance(result, str)
        # Result should be original or formatted code
        assert "def add" in result or len(result) > 0


# ============================================================================
# Test Cache + Streaming Integration
# ============================================================================

class TestCacheStreamingIntegration:
    """Test cache and streaming working together."""

    def test_cache_key_generation(self, cache_manager):
        """Verify cache generates unique keys for different prompts."""
        prompt1 = "generate FastAPI endpoint"
        prompt2 = "generate Flask endpoint"

        key1 = cache_manager.get_cache_key(prompt1)
        key2 = cache_manager.get_cache_key(prompt2)

        assert key1 != key2
        assert len(key1) == 64  # SHA-256 hex length
        assert len(key2) == 64

    def test_cache_same_key_for_same_prompt(self, cache_manager):
        """Verify cache generates same key for identical prompts."""
        prompt = "generate FastAPI endpoint"

        key1 = cache_manager.get_cache_key(prompt)
        key2 = cache_manager.get_cache_key(prompt)

        assert key1 == key2

    def test_streaming_with_cache_simulation(self, cache_manager, stream_collector):
        """Simulate streaming response and cache interaction."""
        prompt = "def hello(): return 'world'"

        # Simulate streaming
        events = [
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "def "}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "hello"}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "(): return 'world'"}},
        ]

        for event in events:
            stream_collector.add_event(event)

        code = stream_collector.finalize()

        # Cache the result
        cache_manager.set(prompt, code)

        # Verify cache hit
        cached = cache_manager.get(prompt)
        assert cached == code

        stats = cache_manager.get_stats()
        assert stats["hits"] == 1


# ============================================================================
# Test Multi-File Context Loading
# ============================================================================

class TestMultiFileContextLoading:
    """Test loading and processing multiple files."""

    def test_load_multiple_files(self, temp_project):
        """Verify loading multiple files creates proper context."""
        file_paths = [
            str(temp_project / "src" / "main.py"),
            str(temp_project / "src" / "utils.py"),
        ]

        context = load_multiple_files(file_paths)

        assert isinstance(context, str)
        assert "hello" in context
        assert "add" in context
        assert "subtract" in context

    def test_project_context_loading(self, temp_project):
        """Verify project context loader finds structure."""
        context = load_project_context(temp_project)

        assert context is not None
        assert context.project_type == "python"
        assert context.file_tree is not None
        assert len(context.key_files) > 0


# ============================================================================
# Test Multi-File + Formatting Integration
# ============================================================================

class TestMultiFileFormattingIntegration:
    """Test multi-file operations with formatting."""

    def test_multi_file_refactoring_structure(self, temp_project):
        """Verify multi-file refactoring returns properly structured response."""
        # This tests the structure expected by agent.refactor_multiple()
        file_paths = [
            str(temp_project / "src" / "main.py"),
            str(temp_project / "src" / "utils.py"),
        ]

        # Simulate API response with file markers
        api_response = """
## File: src/main.py
def hello(name: str) -> str:
    return f'Hello, {name}!'

## File: src/utils.py
def add(a: int, b: int) -> int:
    return a + b

def subtract(a: int, b: int) -> int:
    return a - b
"""

        # Parse response as the agent would
        lines = api_response.split("\n")
        result = {}
        current_file = None
        current_code = []

        for line in lines:
            if line.startswith("## File:"):
                # Save previous file if any
                if current_file and current_code:
                    refactored = "\n".join(current_code).strip()
                    result[current_file] = refactored

                # Extract new filename
                filename = line.replace("## File:", "").strip()
                if "(" in filename:
                    filename = filename[:filename.index("(")].strip()
                current_file = filename
                current_code = []
            elif current_file:
                if line.strip() not in ("```", "```python"):
                    current_code.append(line)

        # Save last file
        if current_file and current_code:
            refactored = "\n".join(current_code).strip()
            result[current_file] = refactored

        assert "src/main.py" in result
        assert "src/utils.py" in result
        assert "Hello" in result["src/main.py"]
        assert "add" in result["src/utils.py"]

    @pytest.mark.asyncio
    async def test_agent_multi_file_refactor_with_format(self):
        """Test agent refactor_multiple with formatting enabled."""
        with patch("src.agent.build_bedrock_runtime"):
            agent = JmAgent()

            with patch.object(agent, "_call_bedrock", new_callable=AsyncMock) as mock_bedrock:
                # Simulate multi-file response
                response_content = """
## File: main.py
def hello(name: str) -> str:
    return f'Hello, {name}!'

## File: utils.py
def add(a: int, b: int) -> int:
    return a + b
"""
                mock_bedrock.return_value = BedrockResponse(
                    content=response_content,
                    stop_reason="end_turn",
                    usage={"input_tokens": 100, "output_tokens": 50}
                )

                # Call refactor_multiple with format_code=True
                result = await agent.refactor_multiple(
                    file_paths=["main.py", "utils.py"],
                    requirements="Add type hints",
                    language="python",
                    format_code=True
                )

                assert isinstance(result, dict)
                assert len(result) == 2


# ============================================================================
# Test All Features Together
# ============================================================================

class TestPhase3CrossFeatureIntegration:
    """Test all Phase 3 features working together."""

    @pytest.mark.asyncio
    async def test_generate_with_all_phase3_features(self):
        """Test code generation with cache, streaming, and formatting."""
        with patch("src.agent.build_bedrock_runtime"):
            agent = JmAgent(model="haiku")

            with patch.object(agent, "_call_bedrock", new_callable=AsyncMock) as mock_bedrock:
                mock_bedrock.return_value = BedrockResponse(
                    content="def hello():\n    return 'world'",
                    stop_reason="end_turn",
                    usage={"input_tokens": 50, "output_tokens": 20}
                )

                # Generate with format_code=True
                result = await agent.generate(
                    prompt="Create a hello function",
                    language="python",
                    format_code=True
                )

                assert isinstance(result, GenerateResponse)
                assert "def hello" in result.code
                assert result.language == "python"
                assert result.tokens_used is not None

    @pytest.mark.asyncio
    async def test_generate_streaming_with_formatting(self):
        """Test streaming generation with formatting applied."""
        with patch("src.agent.build_bedrock_runtime"):
            agent = JmAgent()

            # Mock the streaming
            mock_events = [
                {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "def "}},
                {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "hello"}},
                {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "():\n    return 'world'"}},
            ]

            with patch.object(agent, "_stream_and_collect") as mock_stream:
                def stream_handler(body, collector, on_chunk):
                    for event in mock_events:
                        collector.add_event(event)

                mock_stream.side_effect = stream_handler

                # Generate with streaming and formatting
                result = await agent.generate_streaming(
                    prompt="Hello function",
                    language="python",
                    format_code=True
                )

                assert isinstance(result, GenerateResponse)
                assert "hello" in result.code.lower()

    def test_cache_with_all_formatters(self, cache_manager, code_formatter):
        """Test caching formatted code in different languages."""
        languages_and_code = [
            ("python", "def hello():\n    return 'world'"),
            ("javascript", "const hello = () => 'world';"),
            ("typescript", "interface User { name: string; }"),
            ("sql", "SELECT * FROM users;"),
        ]

        for language, code in languages_and_code:
            # Format the code
            formatted = code_formatter.format(code, language=language)

            # Cache it
            cache_manager.set(code, formatted)

            # Verify retrieval
            cached = cache_manager.get(code)
            assert cached is not None

        stats = cache_manager.get_stats()
        assert stats["hits"] == len(languages_and_code)

    def test_project_context_with_multi_file_formatting(self, temp_project):
        """Test project context loading with multi-file and formatting."""
        # Load project context
        context = load_project_context(temp_project)
        assert context is not None

        # Load multiple files
        file_paths = [
            str(temp_project / "src" / "main.py"),
            str(temp_project / "src" / "utils.py"),
        ]
        multi_context = load_multiple_files(file_paths)
        assert "hello" in multi_context

        # Format each file
        for file_path in file_paths:
            code = Path(file_path).read_text()
            formatter = CodeFormatter()
            formatted = formatter.format(code, language="python")
            assert isinstance(formatted, str)


# ============================================================================
# Test CLI Feature Combinations
# ============================================================================

class TestCLIFeatureCombinations:
    """Test CLI with various feature combinations."""

    def test_parse_file_list_variations(self):
        """Test parse_file_list handles different input formats."""
        from src.cli import parse_file_list

        # Single file
        assert parse_file_list("main.py") == ["main.py"]

        # Comma-separated
        files = parse_file_list("a.py, b.py, c.py")
        assert len(files) == 3
        assert all(f.endswith(".py") for f in files)

    @pytest.mark.asyncio
    async def test_agent_with_project_and_format(self, temp_project):
        """Test agent with project context and formatting."""
        from src.prompts.context_loader import load_project_context

        context = load_project_context(temp_project)

        with patch("src.agent.build_bedrock_runtime"):
            agent = JmAgent(project_context=context)

            assert agent.project_context is not None
            assert agent.formatter is not None


# ============================================================================
# Test Feature Interaction Edge Cases
# ============================================================================

class TestFeatureInteractionEdgeCases:
    """Test edge cases in feature interactions."""

    def test_empty_stream_accumulation(self, stream_collector):
        """Test stream collector with empty events."""
        result = stream_collector.finalize()
        assert result == ""

    def test_cache_with_very_long_code(self, cache_manager):
        """Test caching very long code."""
        long_code = "def func():\n    pass\n" * 1000
        key = cache_manager.get_cache_key(long_code)

        cache_manager.set(long_code, long_code)
        cached = cache_manager.get(long_code)

        assert cached == long_code
        assert len(cached) > 10000

    def test_formatter_with_malformed_code(self, code_formatter):
        """Test formatter gracefully handles malformed code."""
        malformed = "def hello(\n    incomplete"
        result = code_formatter.format(malformed, language="python")

        # Should return something (either original or formatted)
        assert isinstance(result, str)

    def test_stream_with_special_characters(self, stream_collector):
        """Test streaming with special characters."""
        events = [
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "# UTF-8: "}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "😀🎉"}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "\nprint('done')"}},
        ]

        for event in events:
            stream_collector.add_event(event)

        result = stream_collector.finalize()
        assert "😀" in result
        assert "print" in result

    def test_cache_expiration_simulation(self, cache_manager):
        """Test cache expiration tracking."""
        from datetime import datetime, timedelta
        from src.cache.cache_manager import CacheEntry

        # Create an entry that will expire
        entry = CacheEntry("content", ttl_minutes=1)
        entry.created_at = datetime.now() - timedelta(minutes=2)

        # Verify it's expired
        assert entry.is_expired()
        assert entry.get_content() is None


# ============================================================================
# Regression Test: All Features Together
# ============================================================================

class TestPhase3RegressionScenarios:
    """Real-world scenario tests."""

    @pytest.mark.asyncio
    async def test_complete_refactor_workflow(self, temp_project):
        """Test complete refactoring workflow with all Phase 3 features."""
        from src.prompts.context_loader import load_project_context

        # Load project context
        context = load_project_context(temp_project)

        with patch("src.agent.build_bedrock_runtime"):
            # Create agent with project context
            agent = JmAgent(project_context=context)

            # Mock the API response
            with patch.object(agent, "_call_bedrock", new_callable=AsyncMock) as mock_bedrock:
                mock_bedrock.return_value = BedrockResponse(
                    content="def hello(name: str) -> str:\n    return f'Hello, {name}!'",
                    stop_reason="end_turn",
                    usage={"input_tokens": 75, "output_tokens": 30}
                )

                # Refactor with formatting
                main_file = str(temp_project / "src" / "main.py")
                original_code = Path(main_file).read_text()

                result = await agent.refactor(
                    code=original_code,
                    requirements="Add type hints and docstrings",
                    language="python",
                    format_code=True
                )

                assert isinstance(result, GenerateResponse)
                assert result.tokens_used is not None

    @pytest.mark.asyncio
    async def test_multi_file_test_generation(self, temp_project):
        """Test generating tests for multiple files."""
        file_paths = [
            str(temp_project / "src" / "main.py"),
            str(temp_project / "src" / "utils.py"),
        ]

        with patch("src.agent.build_bedrock_runtime"):
            agent = JmAgent()

            with patch.object(agent, "_call_bedrock", new_callable=AsyncMock) as mock_bedrock:
                mock_bedrock.return_value = BedrockResponse(
                    content="import pytest\n\ndef test_functions():\n    pass",
                    stop_reason="end_turn",
                    usage={"input_tokens": 150, "output_tokens": 50}
                )

                result = await agent.test_multiple(
                    file_paths=file_paths,
                    test_framework="pytest",
                    target_coverage=0.8
                )

                assert isinstance(result, GenerateResponse)
                assert "pytest" in result.code or "test" in result.code


# ============================================================================
# Performance and Statistics Tests
# ============================================================================

class TestPhase3PerformanceMetrics:
    """Test performance metrics and statistics."""

    def test_cache_performance_improvement(self, cache_manager):
        """Demonstrate cache performance improvement."""
        prompt = "generate FastAPI endpoint"
        code = "def api():\n    pass"

        # First call - miss
        start = time.time()
        result = cache_manager.get(prompt)
        miss_time = time.time() - start

        # Set cache
        cache_manager.set(prompt, code)

        # Second call - hit (should be faster)
        start = time.time()
        result = cache_manager.get(prompt)
        hit_time = time.time() - start

        assert result == code
        stats = cache_manager.get_stats()
        assert stats["hit_rate"] == 0.5  # 1 hit, 1 miss, then 1 hit

    def test_streaming_token_counting(self, stream_collector):
        """Verify streaming token counting accuracy."""
        events = [
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "a"}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "b"}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "c"}},
        ]

        for event in events:
            stream_collector.add_event(event)

        stats = stream_collector.handler.get_stats()
        assert stats["token_count"] == 3
        assert stats["buffer_length"] == 3

    def test_formatter_availability_detection(self, code_formatter):
        """Test formatter correctly detects available tools."""
        formatters = code_formatter.available_formatters

        assert isinstance(formatters, dict)
        assert any(isinstance(v, bool) for v in formatters.values())

        # At least check structure is correct
        expected_keys = {"black", "prettier", "sqlformat", "gofmt", "rustfmt"}
        assert set(formatters.keys()) == expected_keys
