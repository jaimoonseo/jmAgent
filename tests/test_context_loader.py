import pytest
from pathlib import Path
from src.prompts.context_loader import (
    ProjectContext, detect_project_type, load_project_context
)

@pytest.fixture
def temp_python_project(tmp_path):
    """Create a temporary Python project structure."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test-project'\n")
    (tmp_path / "README.md").write_text("# Test Project\nA test project for testing.")
    return tmp_path

@pytest.fixture
def temp_node_project(tmp_path):
    """Create a temporary Node.js project structure."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "index.js").write_text("console.log('hello')")
    (tmp_path / "package.json").write_text('{"name": "test-app", "description": "A test app"}')
    (tmp_path / "README.md").write_text("# Test App\nA test Node app.")
    return tmp_path

def test_detect_project_type_python(temp_python_project):
    """Test Python project detection."""
    project_type = detect_project_type(temp_python_project)
    assert project_type == "python"

def test_detect_project_type_node(temp_node_project):
    """Test Node.js project detection."""
    project_type = detect_project_type(temp_node_project)
    assert project_type == "node"

def test_load_project_context_python(temp_python_project):
    """Test loading Python project context."""
    context = load_project_context(temp_python_project)

    assert context.project_type == "python"
    assert context.project_name == temp_python_project.name
    assert context.readme_content is not None
    assert "A test project" in context.readme_content

def test_project_context_to_string(temp_python_project):
    """Test context string generation."""
    context = load_project_context(temp_python_project)
    context_str = context.to_context_string()

    assert context.project_name in context_str
    assert "python" in context_str
    assert "Project Structure" in context_str

def test_load_nonexistent_project():
    """Test error handling for nonexistent project."""
    with pytest.raises(ValueError):
        load_project_context(Path("/nonexistent/project"))
