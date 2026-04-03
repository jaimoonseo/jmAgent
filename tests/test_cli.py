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
