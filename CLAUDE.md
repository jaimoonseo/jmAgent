# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**jmAgent v1.0.0** - Production Ready  
**Status**: All phases complete (Phase 1-4 ✅)  
**Tests**: 520+ passing  
**Release**: April 2026

This is a mature, production-ready personal Claude coding assistant using AWS Bedrock (Haiku 4.5). The project includes enterprise features, comprehensive testing, and full documentation.

## Architecture Overview

The project follows a modular architecture with clear separation of concerns:

- **`src/auth/bedrock_auth.py`** - AWS Bedrock authentication (API Key or IAM), reusing patterns from FeedOPS
- **`src/agent.py`** - Core `JmAgent` class with async methods for code generation, refactoring, testing, explanation, bug fixing, and chat
- **`src/cli.py`** - argparse-based CLI entry point
- **`src/prompts/`** - System prompts and action-specific templates
- **`src/actions/`** - Individual action modules (generate, refactor, test, explain, fix)
- **`src/models/`** - Request/response data classes
- **`src/utils/`** - Token counting, code formatting, file handling, logging

The JmAgent is designed to be language/framework-agnostic, supporting Python, TypeScript/JavaScript, SQL, Bash, and more.

## Key Design Decisions

1. **Authentication Flexibility** - Auto-detect between API Key (ABSK) and IAM credentials (from FeedOPS patterns)
2. **Conversation History as List** - Manage multi-turn conversations using message lists
3. **Temperature: 0.2** - Consistency over creativity for code generation
4. **Max Tokens: 4096** - Default output limit; configurable per action
5. **Model Selection** - Haiku 4.5 (default/fast), Sonnet 4.6 (balanced), Opus 4.6 (high-quality)
6. **Async Methods** - All agent methods are async for non-blocking I/O
7. **Project Context Support** - jmAgent analyzes project structure (README, metadata, file tree) and injects this into prompts for project-aware code generation
8. **Prompt Caching** - Cache project context to reduce token usage by ~90% on repeated requests (Phase 3)
9. **Streaming Responses** - Real-time token delivery via Bedrock streaming API for improved UX (Phase 3)
10. **Code Auto-formatting** - Language-specific formatters (Black, Prettier, etc.) for consistent output (Phase 3)
11. **Multi-file Operations** - Analyze and refactor multiple files as a cohesive unit with batch operations (Phase 3)
12. **Structured JSON Logging** - StructuredLogger outputs JSON format with timestamp, level, logger name, message, extra fields (Phase 4 Task 1)
13. **Resilience Patterns** - Retry with exponential backoff, circuit breaker for API protection, custom exception hierarchy (Phase 4 Task 2)
14. **Performance Monitoring** - MetricsCollector tracks per-action statistics, token usage, response times; AnalyticsEngine provides reports and cost estimation (Phase 4 Task 3)

## Common Development Commands

Once Phase 1 is complete, these commands will be available:

```bash
# Virtual environment setup
python3.10+ -m venv venv && source venv/bin/activate

# Install dependencies
pip install boto3 python-dotenv

# Test authentication
python src/auth/bedrock_auth.py

# Run unit tests (after tests are written)
python -m pytest tests/

# Run single test
python -m pytest tests/test_agent.py::TestJmAgent::test_generate

# Run CLI
python src/cli.py generate --prompt "FastAPI GET endpoint"
python src/cli.py refactor --file src/main.py --requirements "add type hints"
python src/cli.py test --file src/utils.py --framework pytest
python src/cli.py explain --file src/complex.py
python src/cli.py fix --file src/app.py --error "TypeError: 'NoneType'..."
python src/cli.py chat  # Interactive mode

# Optional: Install CLI alias
alias jm='python ~/Documents/jmAgent/src/cli.py'
```

## Implementation Roadmap

### Phase 1: Foundation (Current)
- [ ] `bedrock_auth.py` - FeedOPS-based authentication
- [ ] `agent.py` - JmAgent class with core methods
- [ ] `cli.py` - argparse CLI entry point
- **Output**: Basic code generation working

### Phase 2: Project Context Support (Current)
- [x] Context loader for project structure analysis
- [x] Context enhancer for prompt improvement
- [x] --project CLI option
- [x] JM_PROJECT_ROOT environment variable support
- [x] Integration into JmAgent and CLI
- [x] Full test coverage (57+ tests passing)

### Phase 3: Advanced Features ✅
- [x] Prompt caching for reduced token usage (~90% savings)
- [x] Streaming responses for real-time output
- [x] Multi-file support for batch operations
- [x] Code auto-formatting (Black, Prettier, etc.)
- [x] Full test coverage (226 tests passing)
- **Output**: Production-ready advanced features

### Phase 4: Enterprise-Ready Features ✅ COMPLETE & RELEASED
**v1.0.0 Production Release - All 9 Tasks Finished**
- [x] Task 1: Structured JSON Logging (StructuredLogger with JSON output)
- [x] Task 2: Error Handling & Resilience (Custom exceptions, retry with backoff, circuit breaker)
- [x] Task 3: Performance Monitoring & Analytics (MetricsCollector, AnalyticsEngine, cost estimation)
- [x] Task 4: Configuration Management (Pydantic settings, dynamic configuration)
- [x] Task 5: Audit Logging System (comprehensive audit trail with SQLite persistence)
- [x] Task 6: GitHub Integration (GitHub API support, PR/issue operations)
- [x] Task 7: Custom Prompt Templates (user templates with Jinja2 support)
- [x] Task 8: Plugin Architecture (extensible plugins with lifecycle management)
- [x] Task 9: CLI Commands & Documentation (config/metrics/audit/plugin/template commands)
- **Production Status**: 520+ tests passing, zero regressions, fully documented, ready for deployment

### Release Artifacts (v1.0.0)
- ✅ LICENSE (MIT)
- ✅ RELEASE_NOTES.md (comprehensive)
- ✅ DEPLOYMENT.md (installation and setup)
- ✅ CONTRIBUTING.md (contribution guidelines)
- ✅ .gitignore (Python-specific)
- ✅ requirements.txt (pinned versions)
- ✅ setup.py (complete metadata)

## Configuration

Environment variables (`.env` or system):

```
AWS_BEARER_TOKEN_BEDROCK=<ABSK-...>    # OR IAM credentials
AWS_BEDROCK_REGION=us-east-1

# Optional
JM_DEFAULT_MODEL=haiku                  # haiku, sonnet, opus
JM_TEMPERATURE=0.2
JM_MAX_TOKENS=4096
JM_PROJECT_ROOT=.
```

## FeedOPS Patterns to Reuse

1. **Auth Detection** - `_detect_auth_mode()` checks for API Key or IAM
2. **Client Creation** - `_build_bedrock_runtime()` with flexible auth
3. **Model Invocation** - `invoke_model()` with Bedrock JSON format
4. **Conversation Management** - List of message dicts with role/content
5. **Token Estimation** - Pre-validate before API calls

## Testing Strategy

- Unit tests for auth, prompts, and utilities
- Integration tests with mock Bedrock responses (optional: real Bedrock for CI)
- CLI smoke tests for each action

## Cost Optimization

- Haiku 4.5: ~$0.01 per typical request
- Token estimation to avoid unnecessary API calls
- Prompt caching for repeated system prompts
- User controls over model selection and max_tokens

## Important Notes

- This is a **personal project** independent of FeedOPS (no cross-dependencies)
- All core methods in JmAgent should be **async**
- File handling should use `src/utils/file_handler.py` for consistency
- Prompts are crucial for quality—invest time in templates
- Temperature of 0.2 prioritizes consistency; adjust for specific actions if needed
