# jmAgent Quick Start Guide

Welcome to **jmAgent** - your personal AI-powered coding assistant! This guide will get you up and running in 5-10 minutes.

## Table of Contents
1. [What is jmAgent?](#what-is-jmagent)
2. [Prerequisites](#prerequisites)
3. [Installation (3 minutes)](#installation-3-minutes)
4. [Configuration (2 minutes)](#configuration-2-minutes)
5. [Your First Command](#your-first-command)
6. [Essential Commands](#essential-commands)
7. [Real-World Examples](#real-world-examples)
8. [Tips & Tricks](#tips--tricks)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## What is jmAgent?

jmAgent is a personal coding assistant powered by AWS Bedrock Claude models. It helps you:

- **Generate code** from natural language descriptions
- **Refactor code** to improve quality and add features
- **Write tests** automatically for your code
- **Explain code** in plain English (or other languages)
- **Fix bugs** by analyzing error messages
- **Chat interactively** with an AI coding assistant

Think of it as having a expert programmer available 24/7 right in your terminal.

### Why Use jmAgent?

- **Fast**: Get working code in seconds
- **Smart**: Understands your project structure for better suggestions
- **Flexible**: Supports Python, TypeScript, JavaScript, SQL, Bash, and more
- **Affordable**: Uses fast Haiku model (~$0.01 per request)
- **Private**: Runs with your own AWS credentials

---

## Prerequisites

Before you start, make sure you have:

- **Python 3.10 or higher** - Check with: `python3 --version`
- **AWS Account** with Bedrock access (bedrock-runtime API)
- **AWS Credentials** (either API key or IAM credentials)
- **Terminal/Shell** - macOS (zsh/bash), Linux, or Windows (WSL2)

### AWS Bedrock Setup (2 minutes)

If you haven't set up Bedrock yet:

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Search for "Bedrock" and open it
3. Click "Get Started" or go to Models in the left sidebar
4. Request access to **Claude models** (if you see "Request model access")
5. You're ready! (Usually available immediately or within minutes)

For credentials, you can use either:
- **Bedrock API Key** (easiest for personal projects)
- **IAM credentials** (AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY)

---

## Installation (3 minutes)

### Step 1: Clone or Navigate to jmAgent

```bash
# If you haven't cloned it yet
git clone <your-repo-url>
cd jmAgent

# Or just navigate if you already have it
cd ~/Documents/jmAgent
```

### Step 2: Create Virtual Environment

```bash
# Create a Python virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### Step 4: Verify Installation

```bash
# This should show help text
python src/cli.py --help
```

Great! You're installed. Now let's configure it.

---

## Configuration (2 minutes)

### Step 1: Get Your AWS Credentials

You have two options:

**Option A: Bedrock API Key (Recommended for Quick Start)**

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Search for "Bedrock"
3. Go to "Organization settings" → "API Keys"
4. Create a new API key
5. Copy the key (it looks like `ABSK-xxxxxxxxx`)

**Option B: IAM Credentials**

1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Create access keys or use existing ones
3. Copy your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

### Step 2: Create .env File

```bash
# Copy the example file
cp .env.example .env

# Open .env in your editor
nano .env  # or vi, code, etc.
```

### Step 3: Add Credentials to .env

Paste **ONE** of these blocks into your `.env` file:

**If using Bedrock API Key:**
```env
JMAGENT_AWS_BEARER_TOKEN_BEDROCK=ABSK-your-key-here
JMAGENT_AWS_BEDROCK_REGION=us-east-1
```

**If using IAM Credentials:**
```env
JMAGENT_AWS_ACCESS_KEY_ID=AKIA...
JMAGENT_AWS_SECRET_ACCESS_KEY=...
JMAGENT_AWS_BEDROCK_REGION=us-east-1
```

### Step 4: Test Your Configuration

```bash
# This should show "Authentication successful!"
python src/auth/bedrock_auth.py
```

**Got an error?** See [Troubleshooting](#troubleshooting) below.

---

## Your First Command

Let's generate some code! Run this:

```bash
python src/cli.py generate --prompt "Create a Python function that checks if a string is a palindrome"
```

### What to Expect

You'll see:
```
Generating code...

def is_palindrome(s: str) -> bool:
    """
    Check if a string is a palindrome.
    
    Args:
        s: Input string
        
    Returns:
        True if palindrome, False otherwise
    """
    s = s.lower().replace(" ", "")
    return s == s[::-1]
```

**Success!** You just generated your first piece of code with jmAgent.

---

## Essential Commands

Here are the 6 commands you'll use most:

### 1. Generate Code

Create code from a description:

```bash
python src/cli.py generate --prompt "Create a function that finds the largest prime number below N"

# With language specified
python src/cli.py generate --prompt "Hello world REST API" --language javascript

# From existing file context
python src/cli.py generate --prompt "Add a GET endpoint for users" --file src/app.py
```

### 2. Refactor Code

Improve existing code:

```bash
# Add type hints to a file
python src/cli.py refactor --file src/utils.py --requirements "Add type hints and docstrings"

# Refactor multiple files
python src/cli.py refactor --files "src/**/*.py" --requirements "Use more descriptive variable names"

# Auto-format after refactoring
python src/cli.py refactor --file src/main.py --requirements "Improve error handling" --format
```

### 3. Generate Tests

Create automated tests:

```bash
# Generate pytest tests for a file
python src/cli.py test --file src/utils.py --framework pytest

# Generate Jest tests for JavaScript
python src/cli.py test --file src/helpers.js --framework jest

# Multiple files
python src/cli.py test --files "src/**/*.py" --framework pytest --coverage 0.9
```

### 4. Explain Code

Understand what code does:

```bash
# Explain a file
python src/cli.py explain --file src/complex.py

# Explain in Korean (or other language)
python src/cli.py explain --file src/model.py --language korean
```

### 5. Fix Bugs

Get help debugging:

```bash
# Provide an error message
python src/cli.py fix --file src/api.py --error "TypeError: 'NoneType' object is not subscriptable at line 45"

# It will analyze your code and the error, then suggest fixes
```

### 6. Interactive Chat

Have a conversation with the assistant:

```bash
# Start interactive mode
python src/cli.py chat

# You can now type questions and have back-and-forth conversation
# Type 'exit' or 'quit' to end
```

---

## Real-World Examples

### Example 1: Generate a FastAPI Endpoint

```bash
python src/cli.py generate --prompt "FastAPI endpoint that returns a list of users from a database, with filtering by name and role"
```

**Output:**
```python
from fastapi import FastAPI, Query
from typing import List
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    role: str

# Mock database
USERS = [
    {"id": 1, "name": "Alice", "role": "admin"},
    {"id": 2, "name": "Bob", "role": "user"},
]

@app.get("/users", response_model=List[User])
async def get_users(
    name: str = Query(None),
    role: str = Query(None)
):
    """Get users with optional filtering."""
    users = USERS
    if name:
        users = [u for u in users if name.lower() in u["name"].lower()]
    if role:
        users = [u for u in users if u["role"] == role]
    return users
```

### Example 2: Refactor Existing Code

You have a messy file `src/calculator.py`:

```bash
python src/cli.py refactor --file src/calculator.py --requirements "Add type hints, improve variable names, add docstrings" --format
```

jmAgent will:
- Add type hints to all functions
- Rename vague variables to be more descriptive
- Add comprehensive docstrings
- Format the code automatically

### Example 3: Generate Tests

You just wrote a utils module:

```bash
python src/cli.py test --file src/utils.py --framework pytest --coverage 0.85
```

jmAgent creates tests covering:
- Happy path scenarios
- Edge cases
- Error conditions
- ~85% code coverage

### Example 4: Explain Complex Code

You inherited a codebase and found a complex function:

```bash
python src/cli.py explain --file src/algorithms.py
```

Gets an explanation like:
```
This file contains three sorting algorithms:

1. bubble_sort(): Simple comparison sort, O(n²) complexity
   - Iterates through array multiple times
   - Swaps adjacent elements if they're in wrong order
   - Good for learning, bad for large datasets

2. merge_sort(): Divide-and-conquer sort, O(n log n) complexity
   - Splits array in half recursively
   - Merges sorted halves back together
   - More efficient than bubble sort

3. quick_sort(): Another O(n log n) algorithm using pivot
   ...
```

### Example 5: Fix a Bug

You get an error in production:

```bash
python src/cli.py fix --file src/payment.py --error "KeyError: 'amount' in /src/payment.py line 23 - dictionary doesn't have 'amount' key"
```

jmAgent analyzes your code and the error, then:
- Identifies the root cause
- Shows the problematic code
- Suggests fixes with explanations
- Shows corrected code

---

## Tips & Tricks

### 🚀 Tip 1: Use Project Context

For better results, tell jmAgent about your project:

```bash
# Single command with project context
python src/cli.py --project . generate --prompt "Add a new endpoint that fits our project structure"

# Or set it in .env (use once, forget about it)
# JMAGENT_PROJECT_ROOT=/path/to/project
```

jmAgent will analyze your project structure and generate more fitting code.

### 🎯 Tip 2: Choose the Right Model

By default, jmAgent uses **Haiku** (fast, cheap). But you can pick:

```bash
# Fast and cheap (default) - best for most tasks
python src/cli.py --model haiku generate --prompt "..."

# Balanced quality/speed
python src/cli.py --model sonnet generate --prompt "..."

# Best quality, slower/more expensive
python src/cli.py --model opus generate --prompt "..."
```

**When to use each:**
- **Haiku**: Daily coding tasks, quick solutions, learning
- **Sonnet**: Complex refactoring, architecture decisions
- **Opus**: Critical code, security-sensitive features

### 📺 Tip 3: Stream Output for Long Responses

For large code generation, see output as it's generated:

```bash
python src/cli.py generate --prompt "..." --stream
```

### 🔧 Tip 4: Auto-Format Generated Code

Automatically format code after generation:

```bash
python src/cli.py generate --prompt "..." --format

# Works with refactor too
python src/cli.py refactor --file src/main.py --requirements "..." --format
```

### 📚 Tip 5: Batch Multiple Files

Process multiple files at once:

```bash
# Using glob pattern
python src/cli.py refactor --files "src/**/*.py" --requirements "Add type hints"

# Using comma-separated list
python src/cli.py refactor --files "src/a.py,src/b.py,src/c.py" --requirements "..."
```

### 💰 Tip 6: Control Output Size

Limit the number of tokens to save cost:

```bash
python src/cli.py --max-tokens 2000 generate --prompt "..."
```

### 🌡️ Tip 7: Adjust Creativity (Temperature)

```bash
# More deterministic/consistent (default)
python src/cli.py --temperature 0.2 generate --prompt "..."

# More creative/varied
python src/cli.py --temperature 0.8 generate --prompt "..."
```

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'src'"

**Solution:** Make sure you're in the jmAgent directory and virtual env is activated:

```bash
cd ~/Documents/jmAgent
source venv/bin/activate
pip install -e .
```

### Error: "Authentication failed" or "Invalid credentials"

**Solution:** Check your `.env` file:

```bash
# Verify .env exists and has credentials
cat .env

# Test authentication
python src/auth/bedrock_auth.py

# If using API Key, make sure it starts with ABSK-
# If using IAM, make sure you have both ACCESS_KEY_ID and SECRET_ACCESS_KEY
```

### Error: "Model access not available"

**Solution:** You need to request model access in AWS Bedrock:

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Click "Model access" in the sidebar
3. Find "Claude 3" models
4. Click "Request model access"
5. Wait for approval (usually instant)

### Error: "Rate limit exceeded"

**Solution:** You've hit the API rate limit. Just wait a minute and try again.

### Command not found: "jm"

**Solution:** The `jm` alias isn't set up yet. Use full command:

```bash
python src/cli.py generate --prompt "..."

# Or create an alias in ~/.zshrc or ~/.bashrc:
echo "alias jm='python ~/Documents/jmAgent/src/cli.py'" >> ~/.zshrc
source ~/.zshrc
```

### Getting empty or poor quality output

**Solutions:**
- Be more specific in your prompt
- Provide context with `--file` or `--project`
- Use a more capable model (`--model sonnet`)
- Check that your AWS region matches where you set up Bedrock

---

## Next Steps

Now that you're up and running, here's what to explore:

### 1. **Read the Full README**
   - More detailed feature explanations
   - Advanced configuration options
   - Performance benchmarks

   ```bash
   cat README.md
   ```

### 2. **Explore Advanced Features**
   - Prompt caching (reduce token usage by ~90%)
   - Streaming responses (real-time output)
   - Code formatting (Black, Prettier, etc.)
   - Multi-file operations (batch refactoring)

   ```bash
   cat docs/PHASE3_FEATURES.md
   cat docs/PHASE4_FEATURES.md
   ```

### 3. **Learn about Enterprise Features**
   - Configuration management
   - Metrics and audit logging
   - Plugin system
   - Custom templates

   ```bash
   cat docs/PHASE4_HANDOFF.md
   ```

### 4. **Set Up for Your Project**
   - Copy jmAgent to your project directory (or symlink)
   - Configure it with your project root
   - Create custom templates for your codebase style

### 5. **Create an Alias**
   ```bash
   echo "alias jm='python ~/Documents/jmAgent/src/cli.py'" >> ~/.zshrc
   source ~/.zshrc
   
   # Now you can just use: jm generate --prompt "..."
   ```

### 6. **Explore the Codebase**
   - `src/agent.py` - Core JmAgent class
   - `src/actions/` - Individual action implementations
   - `src/prompts/` - System prompts and templates
   - `tests/` - Test examples

---

## Quick Reference Card

Print this out or keep it handy:

```
COMMANDS:
  generate   [--prompt TEXT] [--language LANG] [--file PATH]
  refactor   [--file/--files PATH] --requirements TEXT
  test       [--file/--files PATH] [--framework pytest|jest|vitest]
  explain    --file PATH [--language LANG]
  fix        --file PATH --error TEXT
  chat       (interactive mode)

GLOBAL OPTIONS:
  --model            haiku | sonnet | opus (default: haiku)
  --temperature      0.0-1.0 (default: 0.2)
  --max-tokens       integer (default: 4096)
  --project          path/to/project (for context)

FLAGS:
  --stream           Real-time output streaming
  --format           Auto-format generated code
  --coverage N       Target test coverage (0.0-1.0)

EXAMPLES:
  python src/cli.py generate --prompt "FastAPI endpoint"
  python src/cli.py refactor --file src/main.py --requirements "Add type hints"
  python src/cli.py test --file src/utils.py --framework pytest
  python src/cli.py explain --file src/complex.py
  python src/cli.py fix --file src/app.py --error "TypeError: NoneType..."
  python src/cli.py --model sonnet generate --prompt "Complex feature"
```

---

## Getting Help

- **Documentation**: Check the docs/ folder
- **Issues**: If you find a bug, check CONTRIBUTING.md
- **Examples**: Look in the tests/ folder for usage examples
- **API Docs**: Check the docstrings in src/

---

## Success Checklist

Before you move on to advanced features:

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] AWS credentials configured in `.env`
- [ ] Authentication test passed (`python src/auth/bedrock_auth.py`)
- [ ] First command works (`jm generate --prompt "hello world"`)
- [ ] Able to run all 6 basic commands (generate, refactor, test, explain, fix, chat)

**You're ready to be productive with jmAgent!**

---

## Common Questions

**Q: Will jmAgent make me a better programmer?**  
A: It's a tool - like any tool, you get out what you put in. Use it to learn, experiment, and speed up repetitive tasks.

**Q: Is my code private?**  
A: Your code is sent to AWS Bedrock (Claude). For sensitive code, use on-premise solutions or check AWS data retention policies.

**Q: How much will this cost?**  
A: Haiku costs ~$0.01 per typical request. Most developers spend $5-20/month.

**Q: Can I use it for production code?**  
A: Yes, but always review and test generated code. Use it for scaffolding, not as the only quality check.

**Q: Does it work offline?**  
A: No, it requires AWS Bedrock API access. You can't use it without internet.

**Q: Can I modify the system prompts?**  
A: Yes! Check `src/prompts/` for template files and customize them for your needs.

---

Happy coding with jmAgent! 🚀

For more details, check the [README.md](../README.md) and other documentation in the [docs/](.) folder.
