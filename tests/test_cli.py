import pytest
from unittest.mock import patch
from src.cli import create_parser

def test_create_parser():
    """Test parser creation."""
    parser = create_parser()
    assert parser is not None

def test_parser_generate_command():
    """Test generate command parsing."""
    parser = create_parser()
    args = parser.parse_args([
        "generate",
        "--prompt", "Create a function",
        "--language", "python"
    ])

    assert args.action == "generate"
    assert args.prompt == "Create a function"
    assert args.language == "python"

def test_parser_refactor_command():
    """Test refactor command parsing."""
    parser = create_parser()
    args = parser.parse_args([
        "refactor",
        "--file", "main.py",
        "--requirements", "Add type hints"
    ])

    assert args.action == "refactor"
    assert args.file == "main.py"
    assert args.requirements == "Add type hints"

def test_parser_test_command():
    """Test test command parsing."""
    parser = create_parser()
    args = parser.parse_args([
        "test",
        "--file", "utils.py",
        "--framework", "pytest",
        "--coverage", "0.9"
    ])

    assert args.action == "test"
    assert args.file == "utils.py"
    assert args.framework == "pytest"
    assert args.coverage == 0.9

def test_parser_model_option():
    """Test global model option."""
    parser = create_parser()
    args = parser.parse_args([
        "--model", "sonnet",
        "generate",
        "--prompt", "test"
    ])

    assert args.model == "sonnet"

def test_parser_temperature_option():
    """Test global temperature option."""
    parser = create_parser()
    args = parser.parse_args([
        "--temperature", "0.5",
        "generate",
        "--prompt", "test"
    ])

    assert args.temperature == 0.5

def test_parser_chat_command():
    """Test chat command parsing."""
    parser = create_parser()
    args = parser.parse_args(["chat"])

    assert args.action == "chat"


def test_parser_generate_with_format_flag():
    """Test generate command with --format flag."""
    parser = create_parser()
    args = parser.parse_args([
        "generate",
        "--prompt", "Create a function",
        "--format"
    ])

    assert args.action == "generate"
    assert args.prompt == "Create a function"
    assert args.format is True


def test_parser_generate_without_format_flag():
    """Test generate command without --format flag."""
    parser = create_parser()
    args = parser.parse_args([
        "generate",
        "--prompt", "Create a function"
    ])

    assert args.action == "generate"
    assert args.format is False


def test_parser_refactor_with_format_flag():
    """Test refactor command with --format flag."""
    parser = create_parser()
    args = parser.parse_args([
        "refactor",
        "--file", "main.py",
        "--requirements", "Add type hints",
        "--format"
    ])

    assert args.action == "refactor"
    assert args.file == "main.py"
    assert args.format is True


def test_parser_refactor_without_format_flag():
    """Test refactor command without --format flag."""
    parser = create_parser()
    args = parser.parse_args([
        "refactor",
        "--file", "main.py",
        "--requirements", "Add type hints"
    ])

    assert args.action == "refactor"
    assert args.format is False


# Phase 4: Config command tests
def test_parser_config_show_command():
    """Test config show command parsing."""
    parser = create_parser()
    args = parser.parse_args(["config", "show"])

    assert args.action == "config"
    assert args.config_action == "show"


def test_parser_config_show_with_key():
    """Test config show command with specific key."""
    parser = create_parser()
    args = parser.parse_args(["config", "show", "--key", "jm_default_model"])

    assert args.action == "config"
    assert args.config_action == "show"
    assert args.key == "jm_default_model"


def test_parser_config_set_command():
    """Test config set command parsing."""
    parser = create_parser()
    args = parser.parse_args(["config", "set", "--key", "jm_default_model", "--value", "sonnet"])

    assert args.action == "config"
    assert args.config_action == "set"
    assert args.key == "jm_default_model"
    assert args.value == "sonnet"


def test_parser_config_reset_command():
    """Test config reset command parsing."""
    parser = create_parser()
    args = parser.parse_args(["config", "reset"])

    assert args.action == "config"
    assert args.config_action == "reset"


# Phase 4: Metrics command tests
def test_parser_metrics_summary_command():
    """Test metrics summary command parsing."""
    parser = create_parser()
    args = parser.parse_args(["metrics", "summary"])

    assert args.action == "metrics"
    assert args.metrics_action == "summary"


def test_parser_metrics_summary_with_action_filter():
    """Test metrics summary command with action filter."""
    parser = create_parser()
    args = parser.parse_args(["metrics", "summary", "--action", "generate"])

    assert args.action == "metrics"
    assert args.metrics_action == "summary"
    assert args.action_filter == "generate"


def test_parser_metrics_cost_command():
    """Test metrics cost command parsing."""
    parser = create_parser()
    args = parser.parse_args(["metrics", "cost"])

    assert args.action == "metrics"
    assert args.metrics_action == "cost"


def test_parser_metrics_reset_command():
    """Test metrics reset command parsing."""
    parser = create_parser()
    args = parser.parse_args(["metrics", "reset"])

    assert args.action == "metrics"
    assert args.metrics_action == "reset"


# Phase 4: Audit command tests
def test_parser_audit_log_command():
    """Test audit log command parsing."""
    parser = create_parser()
    args = parser.parse_args(["audit", "log"])

    assert args.action == "audit"
    assert args.audit_action == "log"


def test_parser_audit_log_with_limit():
    """Test audit log command with limit."""
    parser = create_parser()
    args = parser.parse_args(["audit", "log", "--limit", "20"])

    assert args.action == "audit"
    assert args.audit_action == "log"
    assert args.limit == 20


def test_parser_audit_search_command():
    """Test audit search command parsing."""
    parser = create_parser()
    args = parser.parse_args(["audit", "search", "--action", "generate"])

    assert args.action == "audit"
    assert args.audit_action == "search"
    assert args.search_action == "generate"


def test_parser_audit_search_with_multiple_filters():
    """Test audit search command with multiple filters."""
    parser = create_parser()
    args = parser.parse_args([
        "audit", "search",
        "--action", "refactor",
        "--user", "alice",
        "--status", "success"
    ])

    assert args.action == "audit"
    assert args.audit_action == "search"
    assert args.search_action == "refactor"
    assert args.search_user == "alice"
    assert args.search_status == "success"


# Phase 4: Plugin command tests
def test_parser_plugin_list_command():
    """Test plugin list command parsing."""
    parser = create_parser()
    args = parser.parse_args(["plugin", "list"])

    assert args.action == "plugin"
    assert args.plugin_action == "list"


def test_parser_plugin_list_enabled_only():
    """Test plugin list command with enabled filter."""
    parser = create_parser()
    args = parser.parse_args(["plugin", "list", "--enabled"])

    assert args.action == "plugin"
    assert args.plugin_action == "list"
    assert args.enabled is True


def test_parser_plugin_enable_command():
    """Test plugin enable command parsing."""
    parser = create_parser()
    args = parser.parse_args(["plugin", "enable", "--name", "github_integration"])

    assert args.action == "plugin"
    assert args.plugin_action == "enable"
    assert args.name == "github_integration"


def test_parser_plugin_disable_command():
    """Test plugin disable command parsing."""
    parser = create_parser()
    args = parser.parse_args(["plugin", "disable", "--name", "github_integration"])

    assert args.action == "plugin"
    assert args.plugin_action == "disable"
    assert args.name == "github_integration"


# Phase 4: Template command tests
def test_parser_template_list_command():
    """Test template list command parsing."""
    parser = create_parser()
    args = parser.parse_args(["template", "list"])

    assert args.action == "template"
    assert args.template_action == "list"


def test_parser_template_list_for_action():
    """Test template list command for specific action."""
    parser = create_parser()
    args = parser.parse_args(["template", "list", "--action", "generate"])

    assert args.action == "template"
    assert args.template_action == "list"
    assert args.template_action_filter == "generate"


def test_parser_template_use_command():
    """Test template use command parsing."""
    parser = create_parser()
    args = parser.parse_args([
        "template", "use",
        "--action", "generate",
        "--name", "custom_gen"
    ])

    assert args.action == "template"
    assert args.template_action == "use"
    assert args.template_action_name == "generate"
    assert args.template_name == "custom_gen"
