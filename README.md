# jmAgent - Personal Claude Coding Assistant

jmAgent is a personal coding assistant powered by AWS Bedrock Claude models. It supports code generation, refactoring, testing, explanation, debugging, and interactive chat.

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

Test summary (44 total):
- Logger utility: 3 tests
- Data models: 4 tests
- Bedrock auth: 8 tests
- Agent class: 8 tests
- CLI: 7 tests
- Integration: 14 tests

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
~/Documents/jmAgent/
├── src/
│   ├── __init__.py
│   ├── agent.py                    # Core JmAgent class
│   ├── cli.py                      # CLI entry point
│   ├── auth/
│   │   ├── __init__.py
│   │   └── bedrock_auth.py         # AWS Bedrock authentication
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py              # Request data classes
│   │   └── response.py             # Response data classes
│   └── utils/
│       ├── __init__.py
│       └── logger.py               # Logging utility
├── tests/
│   ├── __init__.py
│   ├── test_logger.py
│   ├── test_models.py
│   ├── test_auth.py
│   ├── test_agent.py
│   ├── test_cli.py
│   └── test_integration.py
├── docs/
│   └── superpowers/
│       └── plans/
│           └── 2026-04-02-phase1-foundation.md
├── .env.example
├── PLAN.md
├── CLAUDE.md
├── README.md
├── requirements.txt
├── setup.py
└── .gitignore
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

## License

Personal project - use at your own risk.

## Contact & Support

For issues or suggestions, refer to the project PLAN.md and CLAUDE.md files.
