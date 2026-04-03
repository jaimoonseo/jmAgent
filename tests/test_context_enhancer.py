import pytest
from pathlib import Path
from src.prompts.context_loader import load_project_context
from src.prompts.context_enhancer import ContextEnhancer


@pytest.fixture
def mock_project_context(tmp_path):
    """Create a mock project context."""
    (tmp_path / "src").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
    return load_project_context(tmp_path)


def test_enhancer_without_context():
    """Test enhancer with no project context."""
    enhancer = ContextEnhancer()
    prompt = "Generate a hello function"
    enhanced = enhancer.enhance_generate_prompt(prompt)

    assert enhanced == prompt


def test_enhancer_with_context(mock_project_context):
    """Test enhancer with project context."""
    enhancer = ContextEnhancer(mock_project_context)
    prompt = "Generate a hello function"
    enhanced = enhancer.enhance_generate_prompt(prompt)

    assert "Project Context" in enhanced
    assert "Request" in enhanced
    assert prompt in enhanced


def test_enhance_refactor_prompt(mock_project_context):
    """Test refactoring prompt enhancement."""
    enhancer = ContextEnhancer(mock_project_context)
    prompt = "Add type hints"
    enhanced = enhancer.enhance_refactor_prompt(prompt)

    assert "Refactoring Request" in enhanced
    assert prompt in enhanced


def test_enhance_test_prompt(mock_project_context):
    """Test test generation prompt enhancement."""
    enhancer = ContextEnhancer(mock_project_context)
    prompt = "Generate tests"
    enhanced = enhancer.enhance_test_prompt(prompt)

    assert "Test Request" in enhanced
    assert prompt in enhanced


def test_context_prefix_content(mock_project_context):
    """Test context prefix content."""
    enhancer = ContextEnhancer(mock_project_context)
    prefix = enhancer.get_project_context_prefix()

    assert "Project Context" in prefix
    assert "Instructions" in prefix
    assert "existing code structure" in prefix
