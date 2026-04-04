# Phase 3: Advanced Features Guide

jmAgent Phase 3 adds four powerful features to make code generation faster, more interactive, and more versatile. All features work together seamlessly.

---

## 1. Prompt Caching

### How It Works
When you specify a project with `--project`, jmAgent loads the project context (README, file structure, dependencies) and caches it. Subsequent requests with the same project reuse this cached context, reducing token usage by ~90%.

### Benefits
- **90% token reduction** on repeated context
- **Lower costs** - fewer tokens = less expensive API calls
- **Faster responses** - Bedrock uses cached context without reprocessing
- **Automatic** - works transparently when `--project` is specified

### Usage
```bash
# First request - context is cached
jm --project . generate --prompt "Create a function to parse JSON"

# Second request - reuses cached context (90% fewer tokens)
jm --project . generate --prompt "Create a function to validate JSON"
```

---

## 2. Streaming Responses

### How It Works
Instead of waiting for the complete response, streaming displays tokens as they're generated in real-time. This reduces perceived latency and gives immediate feedback.

### Benefits
- **Improved UX** - See code appearing in real-time
- **Faster feedback** - Don't wait for complete response
- **Better for long responses** - See progress for large code blocks
- **Interactive feeling** - More responsive than batch processing

### Usage
```bash
# Streaming enabled - see output in real-time
jm generate --prompt "Write a function to parse JSON" --stream
```

---

## 3. Code Auto-formatting

### How It Works
Generated code is automatically formatted using language-specific formatters. This ensures consistent style with your project standards.

### Supported Languages
- **Python** - Black
- **JavaScript/TypeScript** - Prettier
- **SQL** - sqlformat
- **Go** - gofmt
- **Rust** - rustfmt

### Benefits
- **Consistent style** - All generated code matches formatting rules
- **Project standard compliance** - Uses your project's formatter
- **Automatic** - No manual reformatting needed
- **Graceful degradation** - Returns original code if formatter unavailable

### Usage
```bash
# Auto-format generated code
jm generate --prompt "Sort an array" --language python --format

# Auto-format refactored code
jm refactor --file src/main.py --requirements "Add type hints" --format
```

---

## 4. Multi-file Support

### How It Works
Instead of working with one file at a time, you can specify multiple files using comma-separated lists or glob patterns. The tool analyzes them as a unit and generates changes that work across all files.

### Supported Patterns
- **Comma-separated**: `file1.py,file2.py,utils.py`
- **Glob patterns**: `src/**/*.py`, `src/handlers/*.ts`
- **Single file**: `main.py` (existing behavior)

### Benefits
- **Batch operations** - Refactor multiple files consistently
- **Cross-file consistency** - Changes work together
- **Less repetition** - Handle related files in one request
- **Better context** - Tool understands file relationships

### Usage
```bash
# Refactor multiple Python files with consistent style
jm refactor --files "src/**/*.py" --requirements "Add type hints"

# Generate tests for multiple files
jm test --files "auth.py,utils.py,models.py" --framework pytest --coverage 0.9

# Mix and match: multi-file + formatting + streaming
jm refactor --files "handlers/*.ts" --requirements "Simplify" --format --stream
```

---

## Feature Combinations

### Real-world Workflows

**Scenario 1: Fast Iteration with Caching + Streaming**
```bash
# Set project for caching
export JM_PROJECT_ROOT=~/my-project

# First request: slower but cached
jm generate --prompt "Create user model" --stream

# Second request: much faster due to cache + streaming
jm generate --prompt "Create auth service" --stream
```

**Scenario 2: Batch Refactoring with Formatting**
```bash
# Refactor all handlers with auto-formatting
jm --project . refactor --files "src/handlers/**/*.py" \
  --requirements "Add error handling" --format
```

**Scenario 3: All Features Together**
```bash
# Leverage all Phase 3 features:
jm --project . refactor \
  --files "src/api/**/*.ts" \
  --requirements "Optimize performance" \
  --format --stream
```

---

## Quick Reference

```bash
# Prompt caching (automatic with --project)
jm --project . generate --prompt "..."

# Streaming
jm generate --prompt "..." --stream

# Auto-formatting
jm generate --prompt "..." --format

# Multi-file refactoring
jm refactor --files "src/**/*.py" --requirements "..."

# Multi-file testing
jm test --files "main.py,utils.py" --framework pytest

# All together
jm --project . refactor --files "src/**/*.py" \
  --requirements "..." --format --stream
```

---

For more information, see [README.md](../README.md) and [CLAUDE.md](../CLAUDE.md).
