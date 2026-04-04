# jmAgent Phase 2: Project Context Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable jmAgent to analyze and understand project structure, automatically including project context and coding style patterns in code generation for improved accuracy and consistency.

**Architecture:** Three-layer approach:
1. **Context Loader** (`context_loader.py`) - Analyzes project structure, reads metadata files (README, package.json, pyproject.toml), builds file tree
2. **Context Enhancer** (`context_enhancer.py`) - Enriches system prompts with project context, injects coding patterns
3. **CLI Integration** (modified `cli.py`) - Accepts `--project` option and `JM_PROJECT_ROOT` environment variable

**Tech Stack:** Python 3.10+, pathlib, JSON parsing, regex for code style analysis

---

## File Structure

```
~/Documents/jmAgent/
├── src/
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── context_loader.py      # NEW: Project structure analysis
│   │   ├── context_enhancer.py    # NEW: Prompt enrichment
│   │   └── (existing files)
│   ├── cli.py                     # MODIFY: Add --project option
│   ├── agent.py                   # MODIFY: Accept project context
│   └── (existing files)
├── tests/
│   ├── test_context_loader.py    # NEW: Context loader tests
│   ├── test_context_enhancer.py  # NEW: Context enhancer tests
│   └── (existing tests)
└── (existing files)
```

---

## Task 1: Create Context Loader (context_loader.py)

**Files:**
- Create: `src/prompts/context_loader.py`
- Test: `tests/test_context_loader.py`

**Context Loader Responsibilities:**
- Read project metadata (README.md, package.json, pyproject.toml)
- Generate project file tree (respecting .gitignore)
- Extract project type (Python, Node.js, Java, etc.)
- Identify key directories (src, lib, test, etc.)

- [ ] **Step 1: Create context_loader.py with ProjectContext dataclass**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/src/prompts/context_loader.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import json
import re

@dataclass
class ProjectContext:
    """Represents project metadata and structure."""
    root_path: Path
    project_type: str  # "python", "node", "java", "rust", etc.
    project_name: str
    description: str
    readme_content: Optional[str] = None
    package_info: Optional[dict] = None
    file_tree: Optional[str] = None
    key_files: List[str] = None
    
    def __post_init__(self):
        if self.key_files is None:
            self.key_files = []
    
    def to_context_string(self) -> str:
        """Convert context to string for prompts."""
        parts = [
            f"# Project: {self.project_name}",
            f"Type: {self.project_type}",
        ]
        
        if self.description:
            parts.append(f"Description: {self.description}")
        
        if self.file_tree:
            parts.append(f"\n## Project Structure:\n{self.file_tree}")
        
        if self.key_files:
            parts.append(f"\n## Key Files:\n" + "\n".join(f"- {f}" for f in self.key_files))
        
        return "\n".join(parts)

def detect_project_type(project_root: Path) -> str:
    """Detect project type based on files present."""
    file_checks = {
        "python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"],
        "node": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
        "java": ["pom.xml", "build.gradle", "mvnw"],
        "rust": ["Cargo.toml"],
        "go": ["go.mod", "go.sum"],
        "csharp": ["*.csproj", "*.sln"],
        "ruby": ["Gemfile", "Rakefile"],
        "php": ["composer.json", "Artisan"],
    }
    
    for project_type, markers in file_checks.items():
        for marker in markers:
            if list(project_root.glob(marker)):
                return project_type
    
    return "unknown"

def read_readme(project_root: Path) -> Optional[str]:
    """Read README.md content."""
    for readme_name in ["README.md", "README.txt", "README"]:
        readme_path = project_root / readme_name
        if readme_path.exists():
            try:
                return readme_path.read_text(encoding="utf-8")[:1000]  # First 1000 chars
            except Exception:
                pass
    return None

def read_package_info(project_root: Path, project_type: str) -> Optional[dict]:
    """Read package metadata based on project type."""
    if project_type == "python":
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                import toml
                return toml.loads(pyproject.read_text())
            except Exception:
                pass
    elif project_type == "node":
        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                return json.loads(package_json.read_text())
            except Exception:
                pass
    return None

def generate_file_tree(project_root: Path, max_depth: int = 3, current_depth: int = 0, prefix: str = "") -> str:
    """Generate a simple file tree string."""
    if current_depth >= max_depth:
        return ""
    
    tree_lines = []
    ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".pytest_cache"}
    
    try:
        items = sorted(project_root.iterdir(), key=lambda x: (not x.is_dir(), x.name))
    except PermissionError:
        return ""
    
    for item in items:
        if item.name.startswith(".") and item.name not in {".env", ".gitignore"}:
            continue
        if item.name in ignore_dirs:
            continue
        
        if item.is_dir():
            tree_lines.append(f"{prefix}├── {item.name}/")
            subtree = generate_file_tree(item, max_depth, current_depth + 1, prefix + "│   ")
            if subtree:
                tree_lines.append(subtree)
        else:
            tree_lines.append(f"{prefix}├── {item.name}")
    
    return "\n".join(tree_lines[:50])  # Limit to 50 lines

def load_project_context(project_root: Path) -> ProjectContext:
    """Load complete project context."""
    project_root = Path(project_root).resolve()
    
    if not project_root.exists():
        raise ValueError(f"Project root does not exist: {project_root}")
    
    project_type = detect_project_type(project_root)
    project_name = project_root.name
    
    readme_content = read_readme(project_root)
    description = ""
    if readme_content:
        # Extract first line or description
        lines = readme_content.split("\n")
        for line in lines:
            if line.strip() and not line.startswith("#"):
                description = line.strip()
                break
    
    package_info = read_package_info(project_root, project_type)
    if package_info and "description" in package_info:
        description = package_info.get("description", description)
    
    file_tree = generate_file_tree(project_root)
    
    # Find key source files
    key_files = []
    if project_type == "python":
        key_files = [str(p.relative_to(project_root)) for p in project_root.glob("src/**/*.py")][:10]
    elif project_type == "node":
        key_files = [str(p.relative_to(project_root)) for p in project_root.glob("src/**/*.{js,ts}")][:10]
    
    return ProjectContext(
        root_path=project_root,
        project_type=project_type,
        project_name=project_name,
        description=description,
        readme_content=readme_content,
        package_info=package_info,
        file_tree=file_tree,
        key_files=key_files
    )
```

- [ ] **Step 2: Create test_context_loader.py with 5 test cases**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/tests/test_context_loader.py
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
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_context_loader.py -v
```

Expected: Tests fail with "No module named 'src.prompts.context_loader'"

- [ ] **Step 4: Implement context_loader.py (code shown in Step 1)**

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_context_loader.py -v
```

Expected: All 5 tests pass

- [ ] **Step 6: Commit**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
git add src/prompts/context_loader.py tests/test_context_loader.py
git commit -m "feat: add project context loader for structure analysis"
```

---

## Task 2: Create Context Enhancer (context_enhancer.py)

**Files:**
- Create: `src/prompts/context_enhancer.py`
- Test: `tests/test_context_enhancer.py`

- [ ] **Step 1: Create context_enhancer.py**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/src/prompts/context_enhancer.py
from src.prompts.context_loader import ProjectContext
from typing import Optional

class ContextEnhancer:
    """Enhances prompts with project context and coding patterns."""
    
    def __init__(self, project_context: Optional[ProjectContext] = None):
        self.context = project_context
    
    def get_project_context_prefix(self) -> str:
        """Get context prefix to prepend to prompts."""
        if not self.context:
            return ""
        
        return f"""## Project Context
{self.context.to_context_string()}

## Instructions
- Follow the project's existing code structure and style
- Use the same naming conventions as existing code
- Match the indentation and formatting style of the project
- Consider existing dependencies and frameworks
"""
    
    def enhance_generate_prompt(self, prompt: str) -> str:
        """Enhance code generation prompt with context."""
        prefix = self.get_project_context_prefix()
        if prefix:
            return f"{prefix}\n## Request\n{prompt}"
        return prompt
    
    def enhance_refactor_prompt(self, prompt: str) -> str:
        """Enhance refactoring prompt with context."""
        prefix = self.get_project_context_prefix()
        if prefix:
            return f"{prefix}\n## Refactoring Request\n{prompt}"
        return prompt
    
    def enhance_test_prompt(self, prompt: str) -> str:
        """Enhance test generation prompt with context."""
        prefix = self.get_project_context_prefix()
        if prefix:
            return f"{prefix}\n## Test Request\n{prompt}"
        return prompt
    
    def enhance_explain_prompt(self, prompt: str) -> str:
        """Enhance code explanation prompt with context."""
        prefix = self.get_project_context_prefix()
        if prefix:
            return f"{prefix}\n## Explanation Request\n{prompt}"
        return prompt
    
    def enhance_fix_prompt(self, prompt: str) -> str:
        """Enhance bug fix prompt with context."""
        prefix = self.get_project_context_prefix()
        if prefix:
            return f"{prefix}\n## Bug Fix Request\n{prompt}"
        return prompt
```

- [ ] **Step 2: Create test_context_enhancer.py**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/tests/test_context_enhancer.py
import pytest
from pathlib import Path
from src.prompts.context_loader import load_project_context, ProjectContext
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
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_context_enhancer.py -v
```

Expected: Tests fail (module not found)

- [ ] **Step 4: Implement context_enhancer.py (code shown in Step 1)**

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_context_enhancer.py -v
```

Expected: All 5 tests pass

- [ ] **Step 6: Commit**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
git add src/prompts/context_enhancer.py tests/test_context_enhancer.py
git commit -m "feat: add context enhancer for prompt improvement"
```

---

## Task 3: Add --project Option to CLI

**Files:**
- Modify: `src/cli.py`

- [ ] **Step 1: Read current cli.py to understand structure**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
head -50 src/cli.py
```

- [ ] **Step 2: Add project option to argument parser**

After line 16 (after global options section), add:

```python
parser.add_argument(
    "--project",
    type=str,
    default=None,
    help="Project root directory for context analysis"
)
```

Also add environment variable support after load_dotenv():

```python
import os

def main() -> None:
    """Entry point."""
    load_dotenv()
    
    # Check for JM_PROJECT_ROOT environment variable
    default_project = os.getenv("JM_PROJECT_ROOT")
    
    parser = create_parser()
    # If default_project exists, use it as default for --project argument
    if default_project:
        parser.set_defaults(project=default_project)
    
    args = parser.parse_args()
    ...
```

- [ ] **Step 3: Verify parser accepts --project option**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
source venv/bin/activate
python -m src.cli --help | grep -A 2 "project"
```

Expected: `--project` option shown in help

- [ ] **Step 4: Test with --project flag**

```bash
python -m src.cli --project /tmp --help | grep project
```

Expected: No error, help displays successfully

- [ ] **Step 5: Commit**

```bash
git add src/cli.py
git commit -m "feat: add --project option to CLI"
```

---

## Task 4: Integrate Context into JmAgent

**Files:**
- Modify: `src/agent.py`

- [ ] **Step 1: Update JmAgent.__init__ to accept project_context**

Find `__init__` method and update:

```python
def __init__(
    self,
    model: str = "haiku",
    region: str = "us-east-1",
    temperature: float = 0.2,
    max_tokens: int = 4096,
    project_context: Optional[ProjectContext] = None,  # ADD THIS
):
    """
    Initialize JmAgent.
    
    Args:
        model: Model name ('haiku', 'sonnet', 'opus')
        region: AWS region
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum output tokens
        project_context: Optional project context for improved code generation
    """
    self.model = model
    self.model_id = MODELS.get(model, MODELS["haiku"])
    self.region = region
    self.temperature = temperature
    self.max_tokens = max_tokens
    self.client = build_bedrock_runtime(region)
    self.conversation_history: List[dict] = []
    self.project_context = project_context  # ADD THIS
    
    logger.info(f"Initialized JmAgent with model: {self.model}")
```

- [ ] **Step 2: Add imports at top of agent.py**

```python
from pathlib import Path
from src.prompts.context_loader import ProjectContext, load_project_context
from src.prompts.context_enhancer import ContextEnhancer
```

- [ ] **Step 3: Update _call_bedrock to use context-enhanced prompts**

In `_call_bedrock` method, add context enhancement:

```python
async def _call_bedrock(
    self,
    action: str,
    prompt: str,
    use_history: bool = False
) -> BedrockResponse:
    """Call Bedrock API with given action and prompt."""
    
    # Enhance prompt with project context if available
    if self.project_context:
        enhancer = ContextEnhancer(self.project_context)
        if action == "generate":
            prompt = enhancer.enhance_generate_prompt(prompt)
        elif action == "refactor":
            prompt = enhancer.enhance_refactor_prompt(prompt)
        elif action == "test":
            prompt = enhancer.enhance_test_prompt(prompt)
        elif action == "explain":
            prompt = enhancer.enhance_explain_prompt(prompt)
        elif action == "fix":
            prompt = enhancer.enhance_fix_prompt(prompt)
    
    system_prompt = SYSTEM_PROMPTS.get(action, SYSTEM_PROMPTS["chat"])
    # ... rest of method unchanged
```

- [ ] **Step 4: Test updated agent initialization**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
source venv/bin/activate
python -c "
from src.agent import JmAgent
from src.prompts.context_loader import ProjectContext
from pathlib import Path

# Test without context
agent1 = JmAgent()
print('✓ Agent initialized without context')

# Test with context (will fail if context_loader not working)
try:
    context = ProjectContext(
        root_path=Path('.'),
        project_type='python',
        project_name='jmAgent',
        description='Test'
    )
    agent2 = JmAgent(project_context=context)
    print('✓ Agent initialized with context')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

Expected: Both initializations succeed

- [ ] **Step 5: Commit**

```bash
git add src/agent.py
git commit -m "feat: integrate project context into JmAgent"
```

---

## Task 5: Integrate Context into CLI Commands

**Files:**
- Modify: `src/cli.py`

- [ ] **Step 1: Update main_async to load and pass project context**

Replace the `main_async` function:

```python
async def main_async(args) -> None:
    """Main async function."""
    # Load project context if --project specified
    project_context = None
    if args.project:
        try:
            from src.prompts.context_loader import load_project_context
            project_context = load_project_context(args.project)
            logger.info(f"Loaded project context from {args.project}")
        except Exception as e:
            logger.warning(f"Could not load project context: {str(e)}")
    
    agent = JmAgent(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        project_context=project_context  # ADD THIS
    )
    
    if args.action == "generate":
        await cmd_generate(args, agent)
    elif args.action == "refactor":
        await cmd_refactor(args, agent)
    elif args.action == "test":
        await cmd_test(args, agent)
    elif args.action == "explain":
        await cmd_explain(args, agent)
    elif args.action == "fix":
        await cmd_fix(args, agent)
    elif args.action == "chat":
        await cmd_chat(args, agent)
    else:
        print("No action specified. Use --help for usage.")
```

- [ ] **Step 2: Test CLI with --project option**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
source venv/bin/activate
python -m src.cli --project . --help | grep -A 1 "project"
```

Expected: No errors, help displays with project option

- [ ] **Step 3: Test project loading with real project**

```bash
source venv/bin/activate
python -c "
from src.prompts.context_loader import load_project_context
from pathlib import Path
context = load_project_context(Path('.'))
print(f'Project: {context.project_name}')
print(f'Type: {context.project_type}')
print(f'Files: {len(context.key_files)} key files found')
"
```

Expected: Project loaded successfully

- [ ] **Step 4: Commit**

```bash
git add src/cli.py
git commit -m "feat: integrate project context loading into CLI"
```

---

## Task 6: Test Project Context with Real Usage

**Files:**
- Test manually with actual jmAgent project

- [ ] **Step 1: Generate code without project context**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
source venv/bin/activate
python -m src.cli generate --prompt "Create a utility function" 2>&1 | head -30
```

- [ ] **Step 2: Generate code with project context**

```bash
python -m src.cli --project . generate --prompt "Create a utility function for project analysis" 2>&1 | head -30
```

Expected: Response includes project-aware suggestions

- [ ] **Step 3: Test with environment variable**

```bash
export JM_PROJECT_ROOT=/Users/jaimoonseo/Documents/jmAgent
python -m src.cli generate --prompt "Add a new CLI command" 2>&1 | head -30
```

Expected: Context loaded from environment variable

- [ ] **Step 4: Test with non-existent project**

```bash
python -m src.cli --project /nonexistent generate --prompt "test" 2>&1
```

Expected: Warning logged, agent continues without context

- [ ] **Step 5: Verify all tests still pass**

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```

Expected: 49+ tests pass (44 original + 5 new)

- [ ] **Step 6: Commit test results**

```bash
git add -A
git commit -m "test: verify project context integration with real usage"
```

---

## Task 7: Integration Testing and Documentation

**Files:**
- Create: `tests/test_phase2_integration.py`
- Modify: `README.md`

- [ ] **Step 1: Create integration test file**

```python
# Create /Users/jaimoonseo/Documents/jmAgent/tests/test_phase2_integration.py
import pytest
from pathlib import Path
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
    agent = JmAgent(project_context=context)
    
    assert agent.project_context is not None
    assert agent.project_context.project_type == "python"

def test_project_context_structure(temp_project):
    """Test project context correctly identifies structure."""
    context = load_project_context(temp_project)
    
    assert context.project_type == "python"
    assert "src" in context.file_tree
    assert "main.py" in context.file_tree or len(context.key_files) > 0

def test_context_enhancer_modifies_prompt(temp_project):
    """Test that context enhancer modifies prompts."""
    from src.prompts.context_enhancer import ContextEnhancer
    
    context = load_project_context(temp_project)
    enhancer = ContextEnhancer(context)
    
    original = "Generate a utility function"
    enhanced = enhancer.enhance_generate_prompt(original)
    
    assert len(enhanced) > len(original)
    assert "Project Context" in enhanced
```

- [ ] **Step 2: Run integration tests**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
python -m pytest tests/test_phase2_integration.py -v
```

Expected: All 3 tests pass

- [ ] **Step 3: Update README.md with project context section**

Add new section after "Commands" section:

```markdown
## Project Context Support

jmAgent can analyze your project structure and use that information to generate more accurate and consistent code.

### Usage

```bash
# Specify project directory
jm --project /path/to/project generate --prompt "your request"

# Use environment variable
export JM_PROJECT_ROOT=/path/to/project
jm generate --prompt "your request"

# Analyze current directory
jm --project . chat
```

### How It Works

When you specify a project with `--project`:
1. jmAgent analyzes the project structure (README, package.json, pyproject.toml)
2. Identifies the project type (Python, Node.js, Java, etc.)
3. Reads project metadata and key files
4. Automatically includes this context in all prompts
5. Generated code follows the project's existing style and patterns

### Examples

```bash
# Generate code for a Python project
jm --project ~/my-python-app generate --prompt "Add a database utility class"

# Refactor with project awareness
jm --project ~/my-react-app refactor --file src/App.tsx --requirements "Use React hooks"

# Generate tests matching project style
jm --project . test --file src/utils.py --framework pytest
```

### Benefits

- Generated code matches your project's style and conventions
- Dependencies and frameworks are considered
- Naming patterns are respected
- Directory structure is understood
```

- [ ] **Step 4: Update CLAUDE.md with Phase 2 info**

Add to "Implementation Roadmap" section:

```markdown
### Phase 2: Project Context Support (Current)
- [x] Context loader for project structure analysis
- [x] Context enhancer for prompt improvement
- [x] --project CLI option
- [x] JM_PROJECT_ROOT environment variable
- [ ] Auto-detect project from current directory (nice-to-have)
- [ ] Cache project context for performance
- [ ] Support more project types (Ruby, PHP, Go, etc.)
```

- [ ] **Step 5: Run all tests to verify nothing broke**

```bash
python -m pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: 49+ tests pass

- [ ] **Step 6: Final commits**

```bash
git add tests/test_phase2_integration.py README.md CLAUDE.md
git commit -m "docs: add project context documentation"
```

---

## Task 8: Final Verification and Cleanup

**Files:**
- Verify all components working together

- [ ] **Step 1: Full test suite run**

```bash
cd /Users/jaimoonseo/Documents/jmAgent
source venv/bin/activate
python -m pytest tests/ -v 2>&1 | tee test_results_phase2.txt
```

Verify: All tests pass, count should be 49+

- [ ] **Step 2: Test all CLI commands with --project**

```bash
# Test generate
python -m src.cli --project . generate --prompt "utility" 2>&1 | head -20

# Test help
python -m src.cli --help | grep project

# Test environment variable
export JM_PROJECT_ROOT=.
python -m src.cli generate --prompt "test" 2>&1 | head -20
```

Expected: All commands work, context is loaded

- [ ] **Step 3: Verify git log for Phase 2 commits**

```bash
git log --oneline | head -15
```

Expected: Shows 8 commits for Phase 2 tasks

- [ ] **Step 4: Create Phase 2 completion summary**

```bash
git log --oneline --grep="feat:" | wc -l
```

- [ ] **Step 5: Final commit**

```bash
git add test_results_phase2.txt
git commit -m "test: add Phase 2 test results"
```

---

## Spec Coverage Checklist

✅ **Add --project global option** - Task 3  
✅ **Create context_loader.py** - Task 1  
✅ **Analyze project structure** - Task 1  
✅ **Create context_enhancer.py** - Task 2  
✅ **Enhance prompts with context** - Task 2  
✅ **Integrate into JmAgent** - Task 4  
✅ **Support JM_PROJECT_ROOT env var** - Task 5  
✅ **Apply coding style patterns** - Task 2 (via context)  
✅ **Full testing** - Task 6, 7, 8  
✅ **Documentation** - Task 7  

---

**Plan Status:** Ready for execution

**Recommended Execution:** Use superpowers:subagent-driven-development for task-by-task implementation with review checkpoints between tasks.

**Estimated Duration:** 3-4 hours with subagent-driven development

**Deliverable:** jmAgent Phase 2 - Project-aware code generation with context analysis and prompt enhancement
