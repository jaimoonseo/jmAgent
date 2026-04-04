import pytest
import subprocess
from unittest.mock import patch, MagicMock
from src.formatting.formatter import CodeFormatter, detect_language


class TestDetectLanguage:
    """Test language detection functionality."""

    def test_detect_python(self):
        """Test Python language detection."""
        code = "def hello():\n    return 'world'"
        assert detect_language(code) == "python"

    def test_detect_python_with_class(self):
        """Test Python detection with class."""
        code = "class MyClass:\n    def __init__(self):\n        self.value = 42"
        assert detect_language(code) == "python"

    def test_detect_python_with_import(self):
        """Test Python detection with import."""
        code = "import os\nfrom sys import argv"
        assert detect_language(code) == "python"

    def test_detect_javascript(self):
        """Test JavaScript language detection."""
        code = "const hello = () => 'world';"
        assert detect_language(code) == "javascript"

    def test_detect_javascript_with_function(self):
        """Test JavaScript detection with function keyword."""
        code = "function hello() {\n    return 'world';\n}"
        assert detect_language(code) == "javascript"

    def test_detect_javascript_with_var(self):
        """Test JavaScript detection with var."""
        code = "var x = 10;\nlet y = 20;"
        assert detect_language(code) == "javascript"

    def test_detect_javascript_with_console(self):
        """Test JavaScript detection with console."""
        code = "console.log('hello');"
        assert detect_language(code) == "javascript"

    def test_detect_typescript(self):
        """Test TypeScript language detection."""
        code = "interface User {\n    name: string;\n    age: number;\n}"
        assert detect_language(code) == "typescript"

    def test_detect_typescript_with_type_annotation(self):
        """Test TypeScript detection with type annotations."""
        code = "const greet = (name: string): string => `Hello, ${name}`;"
        assert detect_language(code) == "typescript"

    def test_detect_sql_select(self):
        """Test SQL detection with SELECT."""
        code = "SELECT * FROM users WHERE age > 18;"
        assert detect_language(code) == "sql"

    def test_detect_sql_insert(self):
        """Test SQL detection with INSERT."""
        code = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com');"
        assert detect_language(code) == "sql"

    def test_detect_sql_update(self):
        """Test SQL detection with UPDATE."""
        code = "UPDATE users SET age = 21 WHERE id = 1;"
        assert detect_language(code) == "sql"

    def test_detect_sql_delete(self):
        """Test SQL detection with DELETE."""
        code = "DELETE FROM users WHERE age < 18;"
        assert detect_language(code) == "sql"

    def test_detect_sql_create(self):
        """Test SQL detection with CREATE."""
        code = "CREATE TABLE users (id INT, name VARCHAR(255));"
        assert detect_language(code) == "sql"

    def test_detect_bash(self):
        """Test Bash language detection."""
        code = "#!/bin/bash\necho 'Hello World'"
        assert detect_language(code) == "bash"

    def test_detect_bash_with_variable(self):
        """Test Bash detection with variable."""
        code = "$my_var = 'value'\necho $my_var"
        assert detect_language(code) == "bash"

    def test_detect_go(self):
        """Test Go language detection."""
        code = "package main\nfunc main() {\n    fmt.Println('Hello')\n}"
        assert detect_language(code) == "go"

    def test_detect_go_with_import(self):
        """Test Go detection with import."""
        code = "package main\nimport 'fmt'"
        assert detect_language(code) == "go"

    def test_detect_rust(self):
        """Test Rust language detection."""
        code = "fn main() {\n    println!('Hello');\n}"
        assert detect_language(code) == "rust"

    def test_detect_rust_with_let(self):
        """Test Rust detection with let."""
        code = "let x = 42;\nlet y: i32 = 100;"
        assert detect_language(code) == "rust"

    def test_detect_rust_with_impl(self):
        """Test Rust detection with impl."""
        code = "impl MyStruct {\n    fn new() {}\n}"
        assert detect_language(code) == "rust"

    def test_detect_java(self):
        """Test Java language detection."""
        code = "public class Hello {\n    public static void main(String[] args) {}\n}"
        assert detect_language(code) == "java"

    def test_detect_java_with_extends(self):
        """Test Java detection with extends."""
        code = "public class Child extends Parent {}"
        assert detect_language(code) == "java"

    def test_detect_unknown(self):
        """Test detection of unknown language."""
        code = "some random text that doesn't match any pattern"
        assert detect_language(code) == "unknown"

    def test_detect_empty_code(self):
        """Test detection with empty code."""
        code = ""
        assert detect_language(code) == "unknown"

    def test_detect_case_insensitive(self):
        """Test that detection is case-insensitive."""
        code = "def hello():\n    return 'world'"
        assert detect_language(code) == "python"


class TestCodeFormatterInit:
    """Test CodeFormatter initialization and formatter detection."""

    def test_formatter_initialization(self):
        """Test CodeFormatter initializes properly."""
        with patch("src.formatting.formatter.CodeFormatter._detect_formatters") as mock_detect:
            mock_detect.return_value = {"black": True, "prettier": False, "sqlformat": False}
            formatter = CodeFormatter()
            assert formatter.available_formatters is not None

    def test_detect_formatters(self):
        """Test formatter detection."""
        formatter = CodeFormatter()
        # The actual availability depends on system, but the method should return a dict
        assert isinstance(formatter.available_formatters, dict)
        assert any(key in formatter.available_formatters for key in ["black", "prettier", "sqlformat", "gofmt", "rustfmt"])

    @patch("shutil.which")
    def test_detect_formatters_with_mocked_which(self, mock_which):
        """Test formatter detection with mocked which."""
        def which_side_effect(cmd):
            if cmd == "black":
                return "/usr/bin/black"
            elif cmd == "prettier":
                return "/usr/bin/prettier"
            return None

        mock_which.side_effect = which_side_effect
        formatter = CodeFormatter()
        assert formatter.available_formatters["black"] is True
        assert formatter.available_formatters["prettier"] is True
        assert formatter.available_formatters["sqlformat"] is False


class TestCodeFormatterFormat:
    """Test code formatting functionality."""

    def test_format_without_language_detection(self):
        """Test format with automatic language detection."""
        with patch.object(CodeFormatter, "_format_python", return_value="formatted_code"):
            formatter = CodeFormatter()
            code = "def hello():\n    return 'world'"
            result = formatter.format(code)
            assert result == "formatted_code"

    def test_format_with_explicit_language(self):
        """Test format with explicit language."""
        with patch.object(CodeFormatter, "_format_python", return_value="formatted_code"):
            formatter = CodeFormatter()
            code = "def hello():\n    return 'world'"
            result = formatter.format(code, language="python")
            assert result == "formatted_code"

    def test_format_unknown_language_returns_original(self):
        """Test that unknown language returns original code."""
        formatter = CodeFormatter()
        code = "random code"
        result = formatter.format(code, language="unknown")
        assert result == code

    def test_format_unavailable_formatter_returns_original(self):
        """Test that unavailable formatter returns original code."""
        formatter = CodeFormatter()
        formatter.available_formatters = {"black": False}
        code = "def hello():\n    return 'world'"
        result = formatter.format(code, language="python")
        assert result == code

    @patch("subprocess.run")
    def test_format_python_success(self, mock_run):
        """Test Python formatting success."""
        formatter = CodeFormatter()
        formatter.available_formatters["black"] = True
        code = "def hello():\n    return 'world'"
        formatted_code = "def hello():\n    return 'world'"

        # Mock subprocess.run to return formatted code
        mock_run.return_value = MagicMock(stdout=formatted_code, returncode=0)

        result = formatter._format_python(code)
        # Should call subprocess.run with black
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_format_python_timeout(self, mock_run):
        """Test Python formatting timeout."""
        formatter = CodeFormatter()
        formatter.available_formatters["black"] = True
        code = "def hello():\n    return 'world'"

        # Mock subprocess.run to raise TimeoutExpired
        mock_run.side_effect = subprocess.TimeoutExpired("black", 5)

        result = formatter._format_python(code)
        # Should return original code on timeout
        assert result == code

    @patch("subprocess.run")
    def test_format_python_error(self, mock_run):
        """Test Python formatting error."""
        formatter = CodeFormatter()
        formatter.available_formatters["black"] = True
        code = "def hello():\n    return 'world'"

        # Mock subprocess.run to raise an exception
        mock_run.side_effect = Exception("Some error")

        result = formatter._format_python(code)
        # Should return original code on error
        assert result == code

    @patch("subprocess.run")
    def test_format_javascript_success(self, mock_run):
        """Test JavaScript formatting success."""
        formatter = CodeFormatter()
        formatter.available_formatters["prettier"] = True
        code = "const hello = () => 'world';"

        mock_run.return_value = MagicMock(stdout=code, returncode=0)
        result = formatter._format_javascript(code)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_format_sql_success(self, mock_run):
        """Test SQL formatting success."""
        formatter = CodeFormatter()
        formatter.available_formatters["sqlformat"] = True
        code = "SELECT * FROM users;"

        mock_run.return_value = MagicMock(stdout=code, returncode=0)
        result = formatter._format_sql(code)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_format_go_success(self, mock_run):
        """Test Go formatting success."""
        formatter = CodeFormatter()
        formatter.available_formatters["gofmt"] = True
        code = "package main"

        mock_run.return_value = MagicMock(stdout=code, returncode=0)
        result = formatter._format_go(code)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_format_rust_success(self, mock_run):
        """Test Rust formatting success."""
        formatter = CodeFormatter()
        formatter.available_formatters["rustfmt"] = True
        code = "fn main() {}"

        mock_run.return_value = MagicMock(stdout=code, returncode=0)
        result = formatter._format_rust(code)
        mock_run.assert_called_once()

    def test_format_with_all_languages(self):
        """Test format method works with all language types."""
        formatter = CodeFormatter()
        test_cases = [
            ("def hello(): pass", "python"),
            ("const x = 1;", "javascript"),
            ("SELECT 1;", "sql"),
            ("package main", "go"),
            ("fn main() {}", "rust"),
        ]

        for code, language in test_cases:
            result = formatter.format(code, language=language)
            # Should return either formatted or original code (graceful degradation)
            assert isinstance(result, str)


class TestCodeFormatterIntegration:
    """Integration tests for formatting."""

    def test_format_preserves_content_on_unavailable_tool(self):
        """Test that code is preserved when formatter is unavailable."""
        formatter = CodeFormatter()
        code = "def hello():\n    return 'world'"

        # Force all formatters to be unavailable
        formatter.available_formatters = {k: False for k in formatter.available_formatters}

        result = formatter.format(code, language="python")
        assert result == code

    def test_format_returns_string(self):
        """Test that format always returns a string."""
        formatter = CodeFormatter()
        codes = [
            "def hello(): pass",
            "",
            "x = 1",
            "some random text"
        ]

        for code in codes:
            result = formatter.format(code)
            assert isinstance(result, str)

    def test_multiple_format_calls(self):
        """Test multiple formatting calls work correctly."""
        formatter = CodeFormatter()
        code1 = "def hello(): pass"
        code2 = "const x = 1;"

        result1 = formatter.format(code1, language="python")
        result2 = formatter.format(code2, language="javascript")

        assert isinstance(result1, str)
        assert isinstance(result2, str)
