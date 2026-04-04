# Phase 2: Project Context Support - Quick Start Guide

## Overview

Phase 2 adds project context awareness to jmAgent. When you specify a project directory, jmAgent automatically analyzes the project structure and includes that context in all prompts, resulting in more accurate code generation that matches your project's style and patterns.

---

## Basic Usage

### Method 1: CLI `--project` Option

```bash
# Generate code with project context
jm --project . generate --prompt "Create a function to parse JSON"

# Refactor code with project understanding
jm --project /path/to/myapp refactor --file src/main.py --requirements "add type hints"

# Generate tests for project code
jm --project ~/my-project test --file app.py --framework pytest

# Explain code with project context
jm --project . explain --file src/agent.py

# Fix bugs with project awareness
jm --project . fix --file src/cli.py --error "TypeError: missing required argument"

# Interactive chat with project context
jm --project . chat
```

### Method 2: Environment Variable

```bash
# Set project root for all commands
export JM_PROJECT_ROOT=~/my-project

# Now all commands use this project context
jm generate --prompt "Create a data model"
jm refactor --file services/auth.py --requirements "optimize performance"
jm chat
```

### Method 3: Home Directory (Recommended)

```bash
# In your project directory
export JM_PROJECT_ROOT=.

# Or use absolute path
export JM_PROJECT_ROOT="$(pwd)"
```

---

## Supported Project Types

jmAgent automatically detects project types from these markers:

| Type | Detection Markers |
|------|-------------------|
| **Python** | `pyproject.toml`, `setup.py`, `requirements.txt` |
| **Node.js** | `package.json` |
| **Java** | `pom.xml` |
| **Go** | `go.mod` |
| **Rust** | `Cargo.toml` |
| **Generic** | Directory with source files |

---

## What Gets Included in Context

When you specify `--project`, jmAgent includes:

1. **Project Type**: Detected from project markers
2. **Project Name**: Extracted from directory or package name
3. **Description**: First 1000 chars of README.md
4. **Package Info**: Content from package.json, pyproject.toml, etc.
5. **File Tree**: Structure of project (up to 50 lines, 3 levels deep)
6. **Key Files**: Important source files in the project

**Example context for jmAgent project**:
```
# Project: jmAgent
Type: python
Description: jmAgent is a personal coding assistant powered by AWS Bedrock...
Package Info: Python 3.10+, async support, boto3 integration...
File Tree:
  jmAgent/
    src/
      ├── agent.py (JmAgent class)
      ├── cli.py (CLI interface)
      └── auth/ (authentication)
    tests/ (comprehensive test suite)
    docs/ (documentation)
Key Files: 10 Python files analyzed
```

---

## Real-World Examples

### Example 1: Generate Code for Your Project

```bash
# Project context helps generate code that fits your patterns
$ jm --project . generate --prompt "Create a new async API handler"

Generated:
```python
import asyncio
from src.agent import JmAgent
from src.models.request import BedrockRequest

class APIHandler:
    def __init__(self, agent: JmAgent):
        self.agent = agent
    
    async def handle_request(self, prompt: str) -> str:
        """Handle API request with project patterns."""
        return await self.agent.generate(prompt)
```

### Example 2: Refactor with Style Consistency

```bash
# Without context: Code might not match your patterns
$ jm refactor --file src/old_module.py --requirements "add async support"

# With context: Code follows jmAgent's async patterns
$ jm --project . refactor --file src/old_module.py --requirements "add async support"

# Result respects:
# - Async/await patterns
# - Bedrock API integration style
# - Type hints
# - Project structure
```

### Example 3: Generate Tests for Your Code

```bash
# Tests generated understand your project structure
$ jm --project . test --file src/agent.py --framework pytest

# Generated tests include:
# - Project-specific imports
# - Matching test patterns
# - Appropriate assertions for your code style
```

### Example 4: Interactive Chat with Context

```bash
$ jm --project . chat

> What does the JmAgent class do?
# Responds with specific knowledge about YOUR JmAgent

> How should I add a new CLI command?
# Responds based on YOUR project patterns

> Explain the auth module
# References YOUR project's auth implementation
```

---

## Tips & Best Practices

### 1. Use Relative Paths
```bash
# Good - works from anywhere
jm --project ~/my-project generate --prompt "..."

# Also good - when in project directory
jm --project . generate --prompt "..."
```

### 2. Set Environment Variable for Frequent Use
```bash
# Add to ~/.zshrc or ~/.bashrc
export JM_PROJECT_ROOT=~/my-project

# Then use jmAgent without --project flag
jm generate --prompt "..."
jm refactor --file src/main.py --requirements "..."
```

### 3. Different Projects in Same Session
```bash
# Switch projects with --project flag
jm --project ~/project-a generate --prompt "..."
jm --project ~/project-b generate --prompt "..."

# Useful when working across multiple repos
```

### 4. Context Size Optimization
- README limited to 1000 characters
- File tree limited to 50 lines
- Keeps token usage reasonable (~685 tokens per request)

### 5. Without Context (When Needed)
```bash
# Sometimes you want generic code
jm generate --prompt "Write a generic utility function"

# Or reset environment variable
unset JM_PROJECT_ROOT
```

---

## Token Usage & Costs

### Cost Comparison

| Scenario | Tokens | Cost |
|----------|--------|------|
| Without context | 53 input | ~$0.0002 |
| With context | 738 input | ~$0.0022 |
| Difference | 685 tokens | ~$0.002 |

**Haiku 4.5 pricing**: $0.003 per 1000 input tokens

---

## Troubleshooting

### Project not detected
```bash
# Check if project type is detected
python3 -c "
from src.prompts.context_loader import detect_project_type
print(detect_project_type('/path/to/project'))
"

# Supported: python, node, java, go, rust, generic
```

### Context not appearing in response
- Context is injected silently; no indication in output
- Verify with token count (738 vs 53 input tokens)
- Content influences quality, not visibility

### Wrong project being used
```bash
# Clear environment variable
unset JM_PROJECT_ROOT

# Use explicit --project flag
jm --project /correct/path generate --prompt "..."
```

---

## Next Steps

- Use `--project .` with your projects
- Monitor generated code quality improvement
- Set `JM_PROJECT_ROOT` for your primary project
- Provide feedback on context usefulness

---

## Related Documentation

- [Phase 2 Implementation Plan](./superpowers/plans/2026-04-03-phase2-project-context.md)
- [Phase 2 Test Results](./PHASE2_TEST_RESULTS.md)
- [README.md](../README.md) - Main documentation
