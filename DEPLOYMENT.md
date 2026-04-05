# Deployment & Setup Guide for jmAgent v1.0.0

This guide covers installation, configuration, and initial setup of jmAgent for production use.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [First-Time Setup](#first-time-setup)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Getting Help](#getting-help)

## System Requirements

### Minimum Requirements
- **Python**: 3.10, 3.11, or 3.12
- **OS**: Linux, macOS, or Windows (WSL2)
- **RAM**: 512MB (2GB recommended)
- **Disk Space**: 500MB
- **Network**: Internet connection for AWS Bedrock API

### AWS Requirements
- **AWS Account** with access to Bedrock
- **Bedrock Region**: us-east-1 (or your preferred region)
- **Authentication**: Either API Key (ABSK) or IAM credentials

## Installation

### Step 1: Clone or Download jmAgent

```bash
# Option A: Clone from repository
git clone https://github.com/yourusername/jmAgent.git
cd jmAgent

# Option B: Download release
wget https://github.com/yourusername/jmAgent/releases/download/v1.0.0/jmAgent-1.0.0.tar.gz
tar xzf jmAgent-1.0.0.tar.gz
cd jmAgent-1.0.0
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (cmd):
venv\Scripts\activate.bat
```

### Step 3: Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Install jmAgent in development mode
pip install -e .
```

### Step 4: Verify Installation

```bash
# Check jm command is available
jm --version

# Check Python version
python --version  # Should be 3.10+

# Verify all dependencies
pip list | grep -E "boto3|pydantic|PyGithub|PyYAML"
```

## Configuration

### Step 1: Create .env File

```bash
# Copy example configuration
cp .env.example .env

# Edit with your credentials
# On macOS/Linux:
nano .env

# On Windows:
notepad .env
```

### Step 2: Add AWS Credentials

Choose ONE of the following authentication methods:

#### Option A: Bedrock API Key (Recommended)

```bash
# Edit .env
AWS_BEARER_TOKEN_BEDROCK=ABSK-xxxxx...
AWS_BEDROCK_REGION=us-east-1
```

To obtain an API key:
1. Go to AWS Console: https://console.aws.amazon.com/bedrock/
2. Navigate to API Keys (left sidebar)
3. Create new API key
4. Copy the ABSK token
5. Paste into .env file

#### Option B: IAM Credentials

```bash
# Edit .env
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_BEDROCK_REGION=us-east-1
```

To create IAM credentials:
1. Go to AWS IAM: https://console.aws.amazon.com/iam/
2. Create new user with Bedrock permissions
3. Generate access keys
4. Add to .env file

### Step 3: Configure Optional Settings

```bash
# Edit .env to add optional settings
JM_DEFAULT_MODEL=haiku              # haiku, sonnet, or opus
JM_TEMPERATURE=0.2                  # 0.0 (consistent) to 1.0 (creative)
JM_MAX_TOKENS=4096                  # Max output tokens
JM_PROJECT_ROOT=.                   # Default project directory
```

### Step 4: Verify Configuration

```bash
# Test AWS authentication
python3 -c "from src.auth.bedrock_auth import BedrockAuth; print('Auth OK')"

# Or use the test script if available
python3 src/auth/bedrock_auth.py
```

## First-Time Setup

### 1. Test Basic Connectivity

```bash
# Simple test to verify everything works
jm --help
```

### 2. Test Code Generation

```bash
# Generate simple code to verify Bedrock connectivity
jm generate --prompt "Create a simple Python hello world function"
```

Expected output: Python function definition

### 3. Check Configuration

```bash
# View current configuration (if available)
jm config show

# View specific setting
jm config show --key jm_default_model
```

### 4. Run Quick Test Suite

```bash
# Run unit tests to verify installation
python3 -m pytest tests/test_auth.py -v

# Run all tests (optional, takes longer)
python3 -m pytest tests/ -v --tb=short
```

## Verification

### Complete Verification Checklist

```bash
# 1. Python version
python3 --version
# Expected: Python 3.10.x, 3.11.x, or 3.12.x

# 2. Virtual environment active
which python | grep venv
# Expected: Path containing 'venv'

# 3. jm command available
which jm
# Expected: Path to jm executable

# 4. Dependencies installed
pip list
# Expected: boto3, pydantic, PyGithub, PyYAML listed

# 5. AWS authentication
python3 << 'EOF'
import os
from src.auth.bedrock_auth import BedrockAuth
auth = BedrockAuth()
print("Authentication mode:", auth.auth_mode)
print("Region:", auth.region)
EOF

# 6. Basic CLI test
jm --help
# Expected: Help output with commands

# 7. Generate code test
jm generate --prompt "Hello world"
# Expected: Generated Python code

# 8. Optional: Run tests
python3 -m pytest tests/test_auth.py::TestBedrockAuth::test_detect_api_key -v
# Expected: Test passes
```

## Troubleshooting

### Issue: "AWS_BEARER_TOKEN_BEDROCK not found"

**Solution:**
1. Verify .env file exists: `ls -la .env`
2. Check file is not empty: `cat .env`
3. Ensure variables are set: `echo $AWS_BEARER_TOKEN_BEDROCK`
4. Reload shell: `source venv/bin/activate`

### Issue: "ModuleNotFoundError: No module named 'boto3'"

**Solution:**
1. Verify virtual environment is active: `which python | grep venv`
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Verify installation: `pip list | grep boto3`

### Issue: "Command 'jm' not found"

**Solution:**
1. Verify installation: `pip install -e .`
2. Check entry point: `python -c "from src.cli import main; print(main)"`
3. Reinstall: `pip uninstall jmAgent && pip install -e .`

### Issue: "BLOCKED" response from Bedrock

**Solution:**
1. This indicates content policy violation
2. Rephrase your prompt to be more specific
3. Avoid ambiguous or potentially sensitive requests
4. Try with different model: `jm --model sonnet generate --prompt "..."`

### Issue: "Connection timeout" or "Service unavailable"

**Solution:**
1. Check AWS region: `echo $AWS_BEDROCK_REGION`
2. Verify internet connectivity: `ping aws.amazon.com`
3. Try different region: `AWS_BEDROCK_REGION=us-west-2 jm generate --prompt "..."`
4. Check AWS service status: https://health.aws.amazon.com/

### Issue: "jm: command not found" on Windows

**Solution:**
1. Use Python module execution: `python -m src.cli --help`
2. Create batch file wrapper:
```batch
@echo off
python -m src.cli %*
```
3. Save as `jm.bat` in project directory

### Issue: Tests fail with "yaml" module not found

**Solution:**
1. Install optional dependencies: `pip install PyYAML`
2. Or install all dependencies: `pip install -r requirements.txt`

## Advanced Configuration

### Project Context Support

```bash
# Use project analysis for better code generation
jm --project /path/to/your/project generate --prompt "..."

# Or set environment variable
export JM_PROJECT_ROOT=/path/to/your/project
jm generate --prompt "..."
```

### Custom Model Selection

```bash
# Use Sonnet for complex tasks
jm --model sonnet generate --prompt "Complex algorithm"

# Use Opus for highest quality
jm --model opus refactor --file src/main.py --requirements "..."
```

### Streaming Responses

```bash
# See output in real-time
jm --stream generate --prompt "Large code example"
```

### Code Auto-formatting

```bash
# Auto-format generated code
jm --format generate --prompt "Python script"

# Works with all actions
jm refactor --file src/main.py --requirements "..." --format
```

## Installation Verification Script

```bash
#!/bin/bash
# save as verify_install.sh

echo "jmAgent Installation Verification"
echo "=================================="
echo ""

# Check Python
echo -n "Python version: "
python3 --version || echo "FAILED"

# Check venv
echo -n "Virtual environment: "
if [[ "$VIRTUAL_ENV" != "" ]]; then echo "ACTIVE"; else echo "NOT ACTIVE"; fi

# Check jm command
echo -n "jm command: "
which jm > /dev/null && echo "AVAILABLE" || echo "NOT FOUND"

# Check dependencies
echo -n "boto3: "
pip list | grep boto3 > /dev/null && echo "INSTALLED" || echo "MISSING"

echo -n "pydantic: "
pip list | grep pydantic > /dev/null && echo "INSTALLED" || echo "MISSING"

echo -n "PyYAML: "
pip list | grep PyYAML > /dev/null && echo "INSTALLED" || echo "MISSING"

# Check AWS auth
echo -n "AWS credentials: "
[[ -n "$AWS_BEARER_TOKEN_BEDROCK" ]] || [[ -n "$AWS_ACCESS_KEY_ID" ]] && echo "SET" || echo "NOT SET"

echo ""
echo "To complete setup:"
echo "1. Create .env file: cp .env.example .env"
echo "2. Edit .env with AWS credentials"
echo "3. Test: jm generate --prompt \"hello\""
```

## Getting Help

### Documentation
- **README.md** - Quick start and usage guide
- **RELEASE_NOTES.md** - Version history and features
- **docs/PHASE4_FEATURES.md** - Detailed feature documentation

### Troubleshooting Resources
1. Check CLAUDE.md for development info
2. Review test files: `tests/` directory
3. Examine example usage: See README.md examples

### Support Contacts
- For AWS Bedrock issues: https://aws.amazon.com/support/
- For jmAgent issues: Check PLAN.md and CLAUDE.md
- For feature requests: See roadmap in RELEASE_NOTES.md

## Next Steps

1. **Complete Configuration** - Ensure .env is properly set up
2. **Run Verification** - Execute the verification checklist
3. **Read Documentation** - Review README.md and docs/
4. **Try Examples** - Run example commands from README.md
5. **Explore Features** - Test different actions (generate, refactor, test, etc.)

## Uninstallation

To completely remove jmAgent:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Optionally remove installed package
pip uninstall jmAgent

# Remove configuration (if desired)
rm .env
```

---

**Version**: 1.0.0  
**Last Updated**: April 2026  
**Status**: Production Ready
