# jmAgent - Personal Claude Coding Assistant

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-520%2B%20passing-brightgreen)](tests/)
[![Status](https://img.shields.io/badge/status-Production%20Ready-success)](RELEASE_NOTES.md)

**jmAgent v1.0.0** - Production-ready personal coding assistant powered by AWS Bedrock Claude models.

A comprehensive AI-powered development tool that supports code generation, refactoring, testing, explanation, debugging, interactive chat, and enterprise features including configuration management, metrics tracking, audit logging, plugin system, and custom templates.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Advanced Features](#advanced-features)
- [Configuration](#configuration)
- [Testing](#testing)
- [Architecture](#architecture)
- [Cost & Performance](#cost--performance)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **Code Generation** - Generate code in any language from natural language prompts
- **Project-Aware** - Analyzes your project structure for context-aware generation
- **Advanced Features** - Prompt caching, streaming, code formatting, multi-file support
- **Enterprise Ready** - Configuration management, metrics, audit logging, plugins, templates
- **Multiple Models** - Haiku (fast), Sonnet (balanced), Opus (high-quality)
- **Interactive Chat** - Multi-turn conversation with history
- **Language Support** - Python, TypeScript, JavaScript, SQL, Bash, and more

## Quick Start

### Installation

```bash
cd ~/Documents/jmAgent
python3.10+ -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Configuration

Create a `.env` file with your AWS credentials:

```bash
cp .env.example .env
# Edit .env with your AWS_BEARER_TOKEN_BEDROCK or IAM credentials
```

### Usage

```bash
# Generate code
jm generate --prompt "Create a FastAPI endpoint"

# Generate with language specification
jm generate --prompt "Create a todo app" --language typescript

# Refactor code
jm refactor --file src/main.py --requirements "Add type hints"

# Generate tests
jm test --file src/utils.py --framework pytest

# Explain code
jm explain --file src/complex.py

# Fix bug
jm fix --file src/app.py --error "TypeError: 'NoneType' object is not subscriptable"

# Interactive chat
jm chat

# Use different model
jm --model sonnet generate --prompt "Complex problem"
```

## Commands

### generate
Generate code from a prompt.

```bash
jm generate --prompt "description" [--language LANG] [--file PATH]
```

Options:
- `--prompt TEXT` (required) - Code generation prompt
- `--language TEXT` - Programming language (e.g., python, javascript, typescript)
- `--file PATH` - File path for context

### refactor
Refactor existing code.

```bash
jm refactor --file PATH --requirements "description"
```

Options:
- `--file PATH` (required) - File to refactor
- `--requirements TEXT` (required) - Refactoring requirements
- `--language TEXT` - Programming language

### test
Generate unit tests.

```bash
jm test --file PATH [--framework pytest|jest|vitest] [--coverage 0.0-1.0]
```

Options:
- `--file PATH` (required) - File to test
- `--framework {pytest,jest,vitest}` - Test framework (default: pytest)
- `--coverage FLOAT` - Target code coverage (default: 0.8)

### explain
Explain code.

```bash
jm explain --file PATH [--language LANG]
```

Options:
- `--file PATH` (required) - File to explain
- `--language TEXT` - Programming language

### fix
Fix bugs in code.

```bash
jm fix --file PATH --error "message" [--context TEXT]
```

Options:
- `--file PATH` (required) - File with bug
- `--error TEXT` (required) - Error message
- `--context TEXT` - Additional context

### chat
Interactive chat mode.

```bash
jm chat
```

Start an interactive conversation with the assistant. Type `exit` or `quit` to end.

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

## Phase 3: Advanced Features

jmAgent now includes powerful Phase 3 features to make code generation faster and more versatile.

### Prompt Caching
Cache project context to reduce token usage by ~90% on repeated requests.
```bash
jm --project . generate --prompt "Create a model"  # Context cached
jm --project . generate --prompt "Create a view"   # Reuses cached context
```

### Streaming Responses
See generated code appear in real-time as tokens are generated.
```bash
jm generate --prompt "Write a parser" --stream
```

### Code Auto-formatting
Automatically format generated code using Black, Prettier, and other language-specific formatters.
```bash
jm generate --prompt "Sort array" --language python --format
jm refactor --file src/main.py --requirements "Add types" --format
```

### Multi-file Support
Refactor and test multiple files together as a cohesive unit.
```bash
jm refactor --files "src/**/*.py" --requirements "Add type hints"
jm test --files "auth.py,utils.py" --framework pytest --coverage 0.9
```

For detailed information, see [docs/PHASE3_FEATURES.md](docs/PHASE3_FEATURES.md).

## Phase 4: Configuration, Monitoring & Management

Phase 4 introduces enterprise-grade management and monitoring capabilities including configuration management, metrics tracking, audit logging, plugin system, and template customization.

### Key Features

- **Configuration Management** - View, update, and reset settings via CLI
- **Metrics & Monitoring** - Track performance metrics and estimated costs
- **Audit Logging** - Complete audit trail of all actions with SQLite persistence
- **Plugin System** - Extend functionality with custom plugins
- **Template System** - Customize prompts for each action type

### Quick Examples

```bash
# Configuration Management
jm config show                          # View all settings
jm config set --key jm_default_model --value sonnet  # Change default model
jm config show --key jm_temperature     # View specific setting

# Metrics & Monitoring
jm metrics summary                      # View performance metrics
jm metrics summary --action generate    # Filter by action type
jm metrics cost                         # Show cost breakdown
jm metrics reset                        # Clear all metrics

# Audit Logging
jm audit log                            # Show recent audit logs
jm audit log --limit 20                 # Show last 20 logs
jm audit search --action generate       # Search by action
jm audit search --user alice --status success  # Search with filters

# Plugin Management
jm plugin list                          # List all plugins
jm plugin list --enabled                # Show only enabled plugins
jm plugin enable --name github_integration  # Enable a plugin

# Template Management
jm template list                        # List available templates
jm template list --action generate      # Templates for specific action
jm template use --action generate --name custom_gen  # Use custom template
```

For comprehensive details, see [docs/PHASE4_FEATURES.md](docs/PHASE4_FEATURES.md).

## Phase 5: REST API Server

A production-ready FastAPI-based REST API server providing programmatic access to all jmAgent features.

### Quick Start

```bash
# Start the API server
uvicorn src.api.main:app --reload

# Access API documentation
open http://localhost:8000/api/docs
```

### Features

- **40+ REST Endpoints** for all jmAgent operations
- **OpenAPI Documentation** at `/api/docs` and `/api/redoc`
- **JWT & API Key Authentication** for secure access
- **Rate Limiting** (100 requests/minute per IP)
- **Comprehensive Audit Logging** for compliance
- **Metrics & Analytics** for monitoring usage

### Documentation

- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete endpoint reference
- **[API Examples](docs/API_EXAMPLES.md)** - Curl and Python examples
- **[Deployment Guide](docs/DEPLOYMENT_REST_API.md)** - Installation and configuration
- **[Production Checklist](docs/PRODUCTION_CHECKLIST.md)** - Pre-deployment verification

### Example: Generate Code via API

```bash
curl -X POST http://localhost:8000/api/v1/actions/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world in Python"}'
```

For more examples, see [API Examples](docs/API_EXAMPLES.md).

## Global Options

- `--model {haiku,sonnet,opus}` - LLM model (default: haiku)
- `--temperature FLOAT` - Sampling temperature 0.0-1.0 (default: 0.2)
- `--max-tokens INT` - Maximum output tokens (default: 4096)
- `--project PATH` - Project directory for context analysis
- `--stream` - Stream responses in real-time
- `--format` - Auto-format generated code
- `--files PATTERN` - Multiple files (comma-separated or glob)

Example:
```bash
jm --model sonnet --temperature 0.5 generate --prompt "Creative code"
jm --project . refactor --files "src/**/*.py" --requirements "..." --format --stream
```

## Architecture

The project is organized into the following modules:

- **auth/** - AWS Bedrock authentication (API Key or IAM)
- **models/** - Request and response data classes
- **utils/** - Logging and utility functions
- **agent.py** - Core JmAgent class with async methods
- **cli.py** - Command-line interface

## Testing

Run all tests:
```bash
python -m pytest tests/ -v
```

Run specific test file:
```bash
python -m pytest tests/test_agent.py -v
```

Run single test:
```bash
python -m pytest tests/test_agent.py::test_agent_initialization -v
```

Run tests by Phase:
```bash
python -m pytest tests/ -k "test_phase2" -v  # Phase 2 tests
python -m pytest tests/ -k "test_phase3" -v  # Phase 3 tests
python -m pytest tests/ -k "test_phase4" -v  # Phase 4 tests
```

Test Summary (520+ tests):
- **Phase 1 Foundation**: 44 tests (auth, models, CLI, agent basics)
- **Phase 2 Context**: 57 tests (project context, file analysis)
- **Phase 3 Advanced**: 115+ tests (caching, streaming, formatting, multi-file)
- **Phase 4 Enterprise**: 300+ tests (config, metrics, audit, plugins, templates, integrations)
- **Total Coverage**: 100% of core functionality

## Environment Variables

- `AWS_BEARER_TOKEN_BEDROCK` - Bedrock API key (ABSK-...)
- `AWS_ACCESS_KEY_ID` - AWS access key (for IAM auth)
- `AWS_SECRET_ACCESS_KEY` - AWS secret key (for IAM auth)
- `AWS_BEDROCK_REGION` - AWS region (default: us-east-1)
- `JM_DEFAULT_MODEL` - Default model (haiku, sonnet, opus)

## Examples

### Generate a FastAPI application

```bash
jm generate --prompt "Create a FastAPI app with GET /api/users endpoint" --language python
```

### Refactor with type hints

```bash
jm refactor --file main.py --requirements "Add comprehensive type hints and docstrings"
```

### Generate tests with high coverage

```bash
jm test --file utils.py --framework pytest --coverage 0.95
```

### Debug an error

```bash
jm fix --file app.py --error "AttributeError: 'NoneType' object has no attribute 'id'"
```

### Interactive development

```bash
$ jm chat
Starting interactive chat (type 'exit' to quit)
============================================================

> Can you help me design a REST API?
Assistant: I'd be happy to help design a REST API...

> Here's the data model: User { id, name, email }
Assistant: Great! Based on that model, here's a suggested REST API design...

> Can you generate the FastAPI code for this?
Assistant: [Generates complete FastAPI implementation]

> exit
Goodbye!
```

## Project Structure

```
jmAgent/
├── src/
│   ├── __init__.py                 # Version and exports
│   ├── agent.py                    # Core JmAgent class
│   ├── cli.py                      # CLI entry point
│   ├── auth/                       # AWS authentication
│   ├── models/                     # Data classes
│   ├── prompts/                    # System prompts
│   ├── actions/                    # Action implementations
│   ├── config/                     # Configuration management
│   ├── monitoring/                 # Metrics and analytics
│   ├── audit/                      # Audit logging
│   ├── plugins/                    # Plugin system
│   ├── integrations/               # GitHub and other integrations
│   ├── errors/                     # Custom exceptions
│   ├── formatting/                 # Code formatters
│   ├── cache/                      # Prompt caching
│   ├── resilience/                 # Retry and circuit breaker
│   └── logging/                    # Structured logging
├── tests/
│   ├── test_*.py                   # 30+ test modules
│   └── ...                         # 520+ total tests
├── docs/
│   ├── PHASE2_FEATURES.md
│   ├── PHASE3_FEATURES.md
│   ├── PHASE4_FEATURES.md
│   └── templates/                  # Template examples
├── .env.example                    # Configuration template
├── .gitignore                      # Git exclusions
├── CLAUDE.md                       # Development guide
├── CONTRIBUTING.md                 # Contribution guidelines
├── DEPLOYMENT.md                   # Setup instructions
├── RELEASE_NOTES.md                # v1.0.0 release notes
├── LICENSE                         # MIT License
├── README.md                       # This file
├── requirements.txt                # Python dependencies
└── setup.py                        # Package configuration
```

## Cost & Performance

### Token Usage
- Simple code generation: ~500-1000 input tokens, ~1000 output tokens (~$0.005)
- With file context: ~2000 input tokens, ~2000 output tokens (~$0.01)
- Refactoring: ~3000 input tokens, ~1500 output tokens (~$0.01)

### Model Selection
- **Haiku 4.5** (default): Fast, cheap, good for most tasks
- **Sonnet 4.6**: Balanced quality and speed for complex tasks
- **Opus 4.6**: Highest quality for very complex problems

## Troubleshooting

### "File not found" error
Ensure the file path is correct and relative to where you run the `jm` command.

### "IAM authentication requires" error
Make sure `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set in your `.env` file.

### Slow responses
Try using a shorter prompt or reducing `--max-tokens` to speed up responses.

### "BLOCKED" response
The Bedrock API may be blocking the request due to content policy. Try rephrasing your prompt.

## Development

The project uses:
- **Python 3.10+** for async/await support
- **boto3** for AWS Bedrock API
- **pytest** for testing
- **argparse** for CLI
- **asyncio** for concurrent I/O

To develop locally:
```bash
cd ~/Documents/jmAgent
source venv/bin/activate
pip install -e .
pytest tests/
```

## Future Enhancements (Phase 2+)

- [ ] Multi-file refactoring
- [ ] Streaming responses
- [ ] Code auto-formatting
- [ ] Interactive prompt suggestions
- [ ] Session management (save/load chat history)
- [ ] Plugin system for custom actions
- [ ] Web UI
- [ ] API server mode

## Additional Resources

- **[RELEASE_NOTES.md](RELEASE_NOTES.md)** - v1.0.0 release information and roadmap
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Installation, configuration, and troubleshooting
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute to jmAgent
- **[CLAUDE.md](CLAUDE.md)** - Development guidance for Claude Code
- **[docs/PHASE4_FEATURES.md](docs/PHASE4_FEATURES.md)** - Enterprise feature details
- **[docs/PHASE3_FEATURES.md](docs/PHASE3_FEATURES.md)** - Advanced feature guide

## License

jmAgent is released under the MIT License. See [LICENSE](LICENSE) file for details.

## Support

- **Documentation** - See README.md and docs/ directory
- **Issues** - Check [PLAN.md](PLAN.md) and [CLAUDE.md](CLAUDE.md)
- **Setup Help** - See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Contributing** - See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Version**: 1.0.0 | **Status**: Production Ready | **Tests**: 520+ passing | **License**: MIT
