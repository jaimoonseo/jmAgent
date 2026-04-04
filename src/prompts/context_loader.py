from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import json

# Configuration constants
MAX_README_CHARS = 1000
MAX_TREE_LINES = 50
MAX_MULTIPLE_FILES_SIZE = 50000  # 50KB default limit for multiple files

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
                return readme_path.read_text(encoding="utf-8")[:MAX_README_CHARS]
            except Exception:
                pass
    return None

def read_package_info(project_root: Path, project_type: str) -> Optional[dict]:
    """Read package metadata based on project type.

    Args:
        project_root: Root directory path
        project_type: Project type ('python', 'node', etc.)

    Returns:
        Dictionary with package metadata (structure varies by type),
        or None if file not found or parse fails.
        For Python: parsed pyproject.toml content.
        For Node: parsed package.json content.
    """
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
    """Generate a simple file tree string.

    Args:
        project_root: Root directory path
        max_depth: Maximum depth to traverse (default: 3)
        current_depth: Current recursion depth (internal use)
        prefix: Tree prefix for formatting (internal use)

    Returns:
        Formatted file tree string (limited to MAX_TREE_LINES lines)
    """
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

    return "\n".join(tree_lines[:MAX_TREE_LINES])

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
        lines = readme_content.split("\n")
        for line in lines:
            if line.strip() and not line.startswith("#"):
                description = line.strip()
                break

    package_info = read_package_info(project_root, project_type)
    if package_info and "description" in package_info:
        description = package_info.get("description", description)

    file_tree = generate_file_tree(project_root)

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


def load_multiple_files(file_paths: List[str], max_size: int = MAX_MULTIPLE_FILES_SIZE) -> str:
    """
    Load multiple files and format as context.

    Args:
        file_paths: List of file paths to load
        max_size: Maximum total size in bytes (default: 50KB)

    Returns:
        Formatted context string with:
        - File count
        - Each file preceded by "## File: <filename>"
        - File size for each file
        - File contents in code blocks
        - Stops loading when max_size reached

    Example output:
        File count: 2
        Total size: 1024 bytes

        ## File: main.py (512 bytes)
        ```python
        def hello():
            return "world"
        ```

        ## File: utils.py (512 bytes)
        ```python
        def add(a, b):
            return a + b
        ```
    """
    if not file_paths:
        return "File count: 0\nTotal size: 0 bytes\n"

    parts = []
    total_size = 0
    files_loaded = 0
    file_details = []

    for file_path in file_paths:
        # Check if we've exceeded size limit
        if total_size >= max_size:
            parts.append(f"\n(Stopped loading at size limit of {max_size} bytes)")
            break

        try:
            path = Path(file_path)

            if not path.exists():
                continue

            # Read file content
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue

            file_size = len(content.encode("utf-8"))

            # Check if adding this file would exceed limit
            if total_size + file_size > max_size:
                # Try to truncate the file content to fit
                available = max_size - total_size
                if available > 100:  # Only include if we have at least 100 bytes
                    content = content[:available // 2]  # Rough estimate
                    file_size = available
                else:
                    # Skip this file
                    parts.append(f"\n(Stopped loading at size limit of {max_size} bytes)")
                    break

            total_size += file_size
            files_loaded += 1

            # Format file entry
            filename = path.name
            file_details.append((filename, file_size))
            parts.append(f"## File: {filename} ({file_size} bytes)")
            parts.append("```")
            parts.append(content)
            parts.append("```")

        except Exception:
            # Skip problematic files
            continue

    # Build result
    result_parts = [
        f"File count: {files_loaded}",
        f"Total size: {total_size} bytes",
        ""
    ]

    if file_details:
        result_parts.extend(parts)

    return "\n".join(result_parts)
