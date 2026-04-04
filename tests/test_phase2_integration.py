import pytest
from pathlib import Path
from unittest.mock import patch
from src.agent import JmAgent
from src.prompts.context_loader import load_project_context


@pytest.fixture
def temp_project(tmp_path):
    """Create a test project with realistic structure."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main():\n    pass\n")
    (tmp_path / "src" / "utils.py").write_text("def helper():\n    pass\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_main():\n    pass\n")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'test-project'\n"
        "dependencies = ['pytest']\n"
    )
    (tmp_path / "README.md").write_text(
        "# Test Project\nA sample Python project.\n"
    )
    return tmp_path


def test_agent_with_project_context(temp_project):
    """Test agent initialization with project context."""
    context = load_project_context(temp_project)
    with patch("src.agent.build_bedrock_runtime"):
        agent = JmAgent(project_context=context)

    assert agent.project_context is not None
    assert agent.project_context.project_type == "python"


def test_project_context_structure(temp_project):
    """Test project context correctly identifies structure."""
    context = load_project_context(temp_project)

    assert context.project_type == "python"
    assert "src" in context.file_tree
    assert len(context.key_files) > 0


def test_context_enhancer_modifies_prompt(temp_project):
    """Test that context enhancer modifies prompts."""
    from src.prompts.context_enhancer import ContextEnhancer

    context = load_project_context(temp_project)
    enhancer = ContextEnhancer(context)

    original = "Generate a utility function"
    enhanced = enhancer.enhance_generate_prompt(original)

    assert len(enhanced) > len(original)
    assert "Project Context" in enhanced
