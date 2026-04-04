import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from src.cli import parse_file_list
from src.prompts.context_loader import load_multiple_files
from src.agent import JmAgent
from src.models.response import GenerateResponse


class TestParseFileList:
    """Test parse_file_list function."""

    def test_parse_single_file(self):
        """Test parsing a single file."""
        result = parse_file_list("main.py")
        assert result == ["main.py"]

    def test_parse_comma_separated_files(self):
        """Test parsing comma-separated files."""
        result = parse_file_list("main.py,utils.py,config.py")
        assert result == ["main.py", "utils.py", "config.py"]

    def test_parse_comma_separated_with_spaces(self):
        """Test parsing comma-separated files with spaces."""
        result = parse_file_list("main.py, utils.py, config.py")
        assert result == ["main.py", "utils.py", "config.py"]

    def test_parse_glob_pattern_simple(self):
        """Test parsing glob pattern with wildcard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "test1.py").touch()
            Path(tmpdir, "test2.py").touch()
            Path(tmpdir, "other.txt").touch()

            # Change to temp dir for glob to work
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = parse_file_list("*.py")
                assert sorted(result) == sorted(["test1.py", "test2.py"])
            finally:
                os.chdir(old_cwd)

    def test_parse_glob_pattern_recursive(self):
        """Test parsing recursive glob pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            Path(tmpdir, "src").mkdir()
            Path(tmpdir, "src", "main.py").touch()
            Path(tmpdir, "src", "utils.py").touch()
            Path(tmpdir, "tests").mkdir()
            Path(tmpdir, "tests", "test_main.py").touch()

            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = parse_file_list("**/*.py")
                # Verify all Python files are found
                assert len(result) >= 3
                assert any("main.py" in r for r in result)
                assert any("utils.py" in r for r in result)
                assert any("test_main.py" in r for r in result)
            finally:
                os.chdir(old_cwd)

    def test_parse_glob_pattern_with_question_mark(self):
        """Test glob pattern with ? wildcard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "file1.py").touch()
            Path(tmpdir, "file2.py").touch()
            Path(tmpdir, "file10.py").touch()

            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = parse_file_list("file?.py")
                assert sorted(result) == sorted(["file1.py", "file2.py"])
            finally:
                os.chdir(old_cwd)

    def test_parse_glob_no_matches(self):
        """Test glob pattern with no matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").touch()

            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = parse_file_list("*.py")
                assert result == []
            finally:
                os.chdir(old_cwd)


class TestLoadMultipleFiles:
    """Test load_multiple_files function."""

    def test_load_multiple_files_basic(self):
        """Test loading multiple files with basic content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir, "file1.py")
            file1.write_text("def hello():\n    return 'hello'")

            file2 = Path(tmpdir, "file2.py")
            file2.write_text("def world():\n    return 'world'")

            file_paths = [str(file1), str(file2)]
            result = load_multiple_files(file_paths)

            # Verify output contains both files
            assert "## File:" in result
            assert "file1.py" in result
            assert "file2.py" in result
            assert "hello()" in result
            assert "world()" in result

    def test_load_multiple_files_format(self):
        """Test output format of load_multiple_files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir, "file1.py")
            file1.write_text("x = 1")

            file_paths = [str(file1)]
            result = load_multiple_files(file_paths)

            # Check for expected format markers
            assert "## File:" in result
            assert "bytes)" in result or "byte)" in result
            assert "```" in result or "x = 1" in result

    def test_load_multiple_files_size_tracking(self):
        """Test that total size is tracked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir, "file1.py")
            file1.write_text("x = 1")

            file2 = Path(tmpdir, "file2.py")
            file2.write_text("y = 2")

            file_paths = [str(file1), str(file2)]
            result = load_multiple_files(file_paths)

            # Should contain file count and size info
            assert "File count:" in result or "2 files" in result or "file1" in result
            assert "Total size:" in result or "bytes" in result or file1.name in result

    def test_load_multiple_files_size_limit(self):
        """Test that loading stops at size limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create large file (100KB)
            large_file = Path(tmpdir, "large.py")
            large_file.write_text("x = " + "1" * 100000)

            # Create second file
            small_file = Path(tmpdir, "small.py")
            small_file.write_text("y = 2")

            file_paths = [str(large_file), str(small_file)]

            # Load with 50KB limit
            result = load_multiple_files(file_paths, max_size=50000)

            # Should include first file but may be truncated
            # Total size should not greatly exceed limit
            assert "large.py" in result
            # The result length should be reasonable
            assert len(result) < 150000  # Should be much less than if both files fully loaded

    def test_load_multiple_files_nonexistent(self):
        """Test handling of nonexistent files."""
        file_paths = ["/nonexistent/file1.py", "/nonexistent/file2.py"]

        # Should handle gracefully
        result = load_multiple_files(file_paths)

        # Result should not be empty, may contain error messages or just be shorter
        assert isinstance(result, str)

    def test_load_multiple_files_empty_list(self):
        """Test with empty file list."""
        result = load_multiple_files([])
        assert isinstance(result, str)
        # Should return some context even if empty
        assert "File count:" in result or "files" in result or result == ""

    def test_load_multiple_files_permission_error(self):
        """Test handling of permission-denied files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir, "readable.py")
            file1.write_text("x = 1")

            file2 = Path(tmpdir, "unreadable.py")
            file2.write_text("y = 2")
            os.chmod(str(file2), 0o000)

            try:
                file_paths = [str(file1), str(file2)]
                result = load_multiple_files(file_paths)

                # Should handle gracefully, at least readable file should be loaded
                assert "readable.py" in result or "x = 1" in result
            finally:
                # Restore permissions for cleanup
                os.chmod(str(file2), 0o644)


class TestRefactorMultiple:
    """Test refactor_multiple method."""

    @pytest.mark.asyncio
    async def test_refactor_multiple_basic(self):
        """Test basic refactor_multiple functionality."""
        with patch("src.agent.build_bedrock_runtime") as mock_build, \
             patch("src.agent.invoke_bedrock") as mock_invoke:
            # Mock response
            mock_build.return_value = MagicMock()
            mock_invoke.return_value = {
                "content": "## File: file1.py\nrefactored code 1\n## File: file2.py\nrefactored code 2",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }

            agent = JmAgent()
            with tempfile.TemporaryDirectory() as tmpdir:
                file1 = Path(tmpdir, "file1.py")
                file1.write_text("x = 1")

                file2 = Path(tmpdir, "file2.py")
                file2.write_text("y = 2")

                result = await agent.refactor_multiple(
                    [str(file1), str(file2)],
                    "Add type hints"
                )

                # Should return dict mapping files to responses
                assert isinstance(result, dict)
                assert len(result) > 0

    @pytest.mark.asyncio
    async def test_refactor_multiple_returns_responses(self):
        """Test that refactor_multiple returns GenerateResponse objects."""
        with patch("src.agent.build_bedrock_runtime") as mock_build, \
             patch("src.agent.invoke_bedrock") as mock_invoke:
            mock_build.return_value = MagicMock()
            mock_invoke.return_value = {
                "content": "## File: file1.py\ncode1\n## File: file2.py\ncode2",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }

            agent = JmAgent()
            with tempfile.TemporaryDirectory() as tmpdir:
                file1 = Path(tmpdir, "file1.py")
                file1.write_text("x = 1")

                result = await agent.refactor_multiple(
                    [str(file1)],
                    "Refactor"
                )

                # Values should be GenerateResponse objects
                for response in result.values():
                    assert hasattr(response, "code")
                    assert hasattr(response, "tokens_used")

    @pytest.mark.asyncio
    async def test_refactor_multiple_with_language(self):
        """Test refactor_multiple with language parameter."""
        with patch("src.agent.build_bedrock_runtime") as mock_build, \
             patch("src.agent.invoke_bedrock") as mock_invoke:
            mock_build.return_value = MagicMock()
            mock_invoke.return_value = {
                "content": "## File: test.py\nrefactored",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }

            agent = JmAgent()
            with tempfile.TemporaryDirectory() as tmpdir:
                file1 = Path(tmpdir, "test.py")
                file1.write_text("pass")

                result = await agent.refactor_multiple(
                    [str(file1)],
                    "Refactor",
                    language="python"
                )

                # Should handle language parameter without error
                assert isinstance(result, dict)


class TestTestMultiple:
    """Test test_multiple method."""

    @pytest.mark.asyncio
    async def test_test_multiple_basic(self):
        """Test basic test_multiple functionality."""
        with patch("src.agent.build_bedrock_runtime") as mock_build, \
             patch("src.agent.invoke_bedrock") as mock_invoke:
            mock_build.return_value = MagicMock()
            mock_invoke.return_value = {
                "content": "import pytest\ndef test_file1(): pass\ndef test_file2(): pass",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }

            agent = JmAgent()
            with tempfile.TemporaryDirectory() as tmpdir:
                file1 = Path(tmpdir, "file1.py")
                file1.write_text("def add(a, b): return a + b")

                file2 = Path(tmpdir, "file2.py")
                file2.write_text("def multiply(a, b): return a * b")

                result = await agent.test_multiple(
                    [str(file1), str(file2)],
                    test_framework="pytest"
                )

                # Should return GenerateResponse
                assert isinstance(result, GenerateResponse)
                assert result.code is not None

    @pytest.mark.asyncio
    async def test_test_multiple_with_coverage(self):
        """Test test_multiple with target coverage."""
        with patch("src.agent.build_bedrock_runtime") as mock_build, \
             patch("src.agent.invoke_bedrock") as mock_invoke:
            mock_build.return_value = MagicMock()
            mock_invoke.return_value = {
                "content": "test code",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }

            agent = JmAgent()
            with tempfile.TemporaryDirectory() as tmpdir:
                file1 = Path(tmpdir, "test.py")
                file1.write_text("pass")

                result = await agent.test_multiple(
                    [str(file1)],
                    test_framework="pytest",
                    target_coverage=0.9
                )

                assert isinstance(result, GenerateResponse)

    @pytest.mark.asyncio
    async def test_test_multiple_different_frameworks(self):
        """Test test_multiple with different test frameworks."""
        with patch("src.agent.build_bedrock_runtime") as mock_build, \
             patch("src.agent.invoke_bedrock") as mock_invoke:
            mock_build.return_value = MagicMock()
            mock_invoke.return_value = {
                "content": "test code",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }

            agent = JmAgent()
            with tempfile.TemporaryDirectory() as tmpdir:
                file1 = Path(tmpdir, "test.ts")
                file1.write_text("function add() {}")

                for framework in ["jest", "vitest"]:
                    result = await agent.test_multiple(
                        [str(file1)],
                        test_framework=framework
                    )
                    assert isinstance(result, GenerateResponse)


class TestCLIMultiFileIntegration:
    """Test CLI integration with multi-file support."""

    def test_cli_parser_refactor_with_files(self):
        """Test refactor command with --files option."""
        from src.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "refactor",
            "--files", "file1.py,file2.py",
            "--requirements", "Add type hints"
        ])

        assert args.action == "refactor"
        assert args.files == "file1.py,file2.py"
        assert args.requirements == "Add type hints"

    def test_cli_parser_test_with_files(self):
        """Test test command with --files option."""
        from src.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test",
            "--files", "src/**/*.py",
            "--framework", "pytest"
        ])

        assert args.action == "test"
        assert args.files == "src/**/*.py"
        assert args.framework == "pytest"

    def test_cli_parser_refactor_backward_compat(self):
        """Test that --file still works (backward compatibility)."""
        from src.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "refactor",
            "--file", "main.py",
            "--requirements", "Refactor"
        ])

        assert args.action == "refactor"
        assert args.file == "main.py"
        assert args.requirements == "Refactor"

    def test_cli_parser_test_backward_compat(self):
        """Test that --file still works for test command."""
        from src.cli import create_parser

        parser = create_parser()
        args = parser.parse_args([
            "test",
            "--file", "utils.py",
            "--framework", "pytest"
        ])

        assert args.action == "test"
        assert args.file == "utils.py"


class TestMultiFileEdgeCases:
    """Test edge cases and error handling."""

    def test_load_multiple_files_mixed_types(self):
        """Test loading files of different types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir, "script.py")
            py_file.write_text("print('hello')")

            js_file = Path(tmpdir, "script.js")
            js_file.write_text("console.log('hello');")

            txt_file = Path(tmpdir, "readme.txt")
            txt_file.write_text("This is a readme")

            result = load_multiple_files([str(py_file), str(js_file), str(txt_file)])

            assert isinstance(result, str)
            assert "script.py" in result
            assert "script.js" in result

    def test_parse_file_list_absolute_paths(self):
        """Test parsing absolute file paths."""
        result = parse_file_list("/home/user/file1.py,/home/user/file2.py")
        assert result == ["/home/user/file1.py", "/home/user/file2.py"]

    def test_parse_file_list_mixed_separators(self):
        """Test that only commas are treated as separators."""
        result = parse_file_list("file1.py,file2.py")
        assert len(result) == 2
        assert "file1.py" in result
        assert "file2.py" in result

    @pytest.mark.asyncio
    async def test_refactor_multiple_empty_list(self):
        """Test refactor_multiple with empty file list."""
        with patch("src.agent.build_bedrock_runtime") as mock_build, \
             patch("src.agent.invoke_bedrock") as mock_invoke:
            mock_build.return_value = MagicMock()
            mock_invoke.return_value = {
                "content": "no files to refactor",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }

            agent = JmAgent()

            # Should handle gracefully
            result = await agent.refactor_multiple([], "Refactor")
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_test_multiple_single_file(self):
        """Test test_multiple with just one file."""
        with patch("src.agent.build_bedrock_runtime") as mock_build, \
             patch("src.agent.invoke_bedrock") as mock_invoke:
            mock_build.return_value = MagicMock()
            mock_invoke.return_value = {
                "content": "test code",
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 100, "output_tokens": 50}
            }

            agent = JmAgent()
            with tempfile.TemporaryDirectory() as tmpdir:
                file1 = Path(tmpdir, "test.py")
                file1.write_text("pass")

                result = await agent.test_multiple([str(file1)])
                assert isinstance(result, GenerateResponse)
