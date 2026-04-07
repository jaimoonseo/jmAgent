# jmAgent API Examples

Complete examples of how to use the jmAgent REST API with curl, Python, and other tools.

## Table of Contents

1. [Curl Examples](#curl-examples)
2. [Python Examples](#python-examples)
3. [Common Use Cases](#common-use-cases)
4. [Error Handling](#error-handling)

## Curl Examples

### Setup

First, set up environment variables:

```bash
export API_URL="http://localhost:8000/api/v1"
export TOKEN="your-jwt-token-here"
```

### 1. Health Check

No authentication required:

```bash
curl $API_URL/health
```

Response:
```json
{
  "success": true,
  "data": {
    "status": "healthy"
  }
}
```

### 2. Generate Code

Generate a Python function to calculate Fibonacci:

```bash
curl -X POST $API_URL/actions/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python function to calculate Fibonacci numbers up to n",
    "language": "python",
    "temperature": 0.2
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "code": "def fibonacci(n: int) -> list:\n    if n <= 0:\n        return []\n    elif n == 1:\n        return [0]\n    \n    fib = [0, 1]\n    for i in range(2, n):\n        fib.append(fib[i-1] + fib[i-2])\n    return fib\n",
    "language": "python",
    "tokens_used": 78,
    "model_used": "haiku"
  }
}
```

### 3. Refactor Code

Refactor an existing file:

```bash
curl -X POST $API_URL/actions/refactor \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/old_code.py",
    "requirements": "Add type hints and improve variable names"
  }'
```

### 4. Generate Tests

Generate pytest tests:

```bash
curl -X POST $API_URL/actions/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/math_utils.py",
    "framework": "pytest"
  }'
```

### 5. Explain Code

Get Korean explanation of code:

```bash
curl -X POST $API_URL/actions/explain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/complex.py",
    "language": "korean",
    "focus_area": "algorithm"
  }'
```

### 6. Fix a Bug

Fix code with a known error:

```bash
curl -X POST $API_URL/actions/fix \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/buggy.py",
    "error_message": "TypeError: list indices must be integers or slices, not str"
  }'
```

### 7. Interactive Chat

Start a conversation:

```bash
curl -X POST $API_URL/actions/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I write a decorator in Python?"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "response": "A decorator in Python is a function that...",
    "conversation_id": "conv_abc123xyz",
    "turn_number": 1
  }
}
```

Continue conversation with ID:

```bash
curl -X POST $API_URL/actions/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you show me a concrete example?",
    "conversation_id": "conv_abc123xyz"
  }'
```

### 8. Configuration Management

Get current configuration:

```bash
curl $API_URL/config \
  -H "Authorization: Bearer $TOKEN"
```

Update a setting:

```bash
curl -X POST $API_URL/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "port",
    "value": 9000
  }'
```

Delete (reset) a setting:

```bash
curl -X DELETE $API_URL/config/debug \
  -H "Authorization: Bearer $TOKEN"
```

### 9. Metrics

Get metrics summary:

```bash
curl $API_URL/metrics/summary \
  -H "Authorization: Bearer $TOKEN"
```

Get metrics by action:

```bash
curl $API_URL/metrics/by-action \
  -H "Authorization: Bearer $TOKEN"
```

Get metrics by model:

```bash
curl $API_URL/metrics/by-model \
  -H "Authorization: Bearer $TOKEN"
```

### 10. Audit Logs

Get recent audit logs:

```bash
curl "$API_URL/audit/logs?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

Search audit logs:

```bash
curl "$API_URL/audit/search?action=generate&status=success" \
  -H "Authorization: Bearer $TOKEN"
```

Export audit logs as CSV:

```bash
curl "$API_URL/audit/export?format=csv&start_date=2026-04-01&end_date=2026-04-06" \
  -H "Authorization: Bearer $TOKEN" \
  -o audit_logs.csv
```

Export as JSON:

```bash
curl "$API_URL/audit/export?format=json" \
  -H "Authorization: Bearer $TOKEN" > audit_logs.json
```

Get audit summary:

```bash
curl $API_URL/audit/summary \
  -H "Authorization: Bearer $TOKEN"
```

### 11. Templates

List all templates:

```bash
curl $API_URL/templates \
  -H "Authorization: Bearer $TOKEN"
```

List templates for a specific action:

```bash
curl "$API_URL/templates?action=generate" \
  -H "Authorization: Bearer $TOKEN"
```

Get template details:

```bash
curl "$API_URL/templates/custom_1" \
  -H "Authorization: Bearer $TOKEN"
```

Create custom template:

```bash
curl -X POST $API_URL/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FastAPI Template",
    "action": "generate",
    "content": "Create a FastAPI endpoint for {{ resource_name }} with {{ methods }} methods",
    "description": "Template for FastAPI endpoints"
  }'
```

Update template:

```bash
curl -X PUT "$API_URL/templates/custom_1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated content with new variables"
  }'
```

Preview template:

```bash
curl -X POST "$API_URL/templates/custom_1/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_name": "users",
    "methods": "GET, POST, PUT, DELETE"
  }'
```

Use template for generation:

```bash
curl -X POST "$API_URL/templates/custom_1/use" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_name": "products",
    "methods": "GET, POST",
    "model": "sonnet"
  }'
```

Delete template:

```bash
curl -X DELETE "$API_URL/templates/custom_1" \
  -H "Authorization: Bearer $TOKEN"
```

### 12. Plugins

List plugins:

```bash
curl $API_URL/plugins \
  -H "Authorization: Bearer $TOKEN"
```

Get plugin details:

```bash
curl "$API_URL/plugins/code_formatter" \
  -H "Authorization: Bearer $TOKEN"
```

Enable plugin:

```bash
curl -X POST "$API_URL/plugins/code_formatter/enable" \
  -H "Authorization: Bearer $TOKEN"
```

Disable plugin:

```bash
curl -X POST "$API_URL/plugins/code_formatter/disable" \
  -H "Authorization: Bearer $TOKEN"
```

Get plugin configuration:

```bash
curl "$API_URL/plugins/code_formatter/config" \
  -H "Authorization: Bearer $TOKEN"
```

Update plugin configuration:

```bash
curl -X POST "$API_URL/plugins/code_formatter/config" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "line_length": 100,
    "use_tabs": false
  }'
```

## Python Examples

### Setup

Install required package:

```bash
pip install requests
```

### Example 1: Simple Code Generation

```python
import requests

# Configuration
API_URL = "http://localhost:8000/api/v1"
TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Generate code
response = requests.post(
    f"{API_URL}/actions/generate",
    json={
        "prompt": "Create a Python function to validate credit card numbers",
        "language": "python"
    },
    headers=headers
)

if response.status_code == 200:
    data = response.json()["data"]
    print("Generated Code:")
    print(data["code"])
    print(f"\nTokens used: {data['tokens_used']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### Example 2: Async Generation with AIOHTTP

```python
import asyncio
import aiohttp

async def generate_code():
    API_URL = "http://localhost:8000/api/v1"
    TOKEN = "your-jwt-token-here"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_URL}/actions/generate",
            json={
                "prompt": "Create a sorting algorithm in TypeScript",
                "language": "typescript"
            },
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(data["data"]["code"])
            else:
                print(f"Error: {response.status}")

# Run
asyncio.run(generate_code())
```

### Example 3: Batch Code Generation

```python
import requests
import json

API_URL = "http://localhost:8000/api/v1"
TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# List of tasks to generate code for
tasks = [
    "Create a function to validate email addresses",
    "Create a function to hash passwords securely",
    "Create a function to parse JSON files"
]

results = []

for task in tasks:
    response = requests.post(
        f"{API_URL}/actions/generate",
        json={"prompt": task},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()["data"]
        results.append({
            "task": task,
            "code": data["code"],
            "tokens_used": data["tokens_used"]
        })
    else:
        print(f"Failed: {task}")

# Save results
with open("generated_code.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"Generated {len(results)} code snippets")
```

### Example 4: Metrics Analysis

```python
import requests
import json

API_URL = "http://localhost:8000/api/v1"
TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Get metrics
response = requests.get(
    f"{API_URL}/metrics/summary",
    headers=headers
)

if response.status_code == 200:
    metrics = response.json()["data"]
    
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Total tokens: {metrics['total_tokens']}")
    
    print("\nMetrics by action:")
    for action, stats in metrics["by_action"].items():
        success_rate = stats.get("success_rate", 0)
        print(f"  {action}: {stats['total_requests']} requests, "
              f"{success_rate*100:.1f}% success")
```

### Example 5: Template Management

```python
import requests

API_URL = "http://localhost:8000/api/v1"
TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create template
template_response = requests.post(
    f"{API_URL}/templates",
    json={
        "name": "REST API Endpoint",
        "action": "generate",
        "content": "Create a {{ framework }} REST API endpoint for {{ resource }} with {{ methods }} methods",
        "description": "Template for REST endpoints"
    },
    headers=headers
)

if template_response.status_code == 200:
    template_id = template_response.json()["data"]["id"]
    print(f"Created template: {template_id}")
    
    # Use template
    use_response = requests.post(
        f"{API_URL}/templates/{template_id}/use",
        json={
            "framework": "FastAPI",
            "resource": "users",
            "methods": "GET, POST, PUT, DELETE"
        },
        headers=headers
    )
    
    if use_response.status_code == 200:
        code = use_response.json()["data"]["code"]
        print(f"Generated code:\n{code}")
```

## Common Use Cases

### Use Case 1: Generate Code for a New Project

```bash
#!/bin/bash

TOKEN="your-token"
API_URL="http://localhost:8000/api/v1"

# 1. Generate main module
curl -X POST "$API_URL/actions/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create the main module for a blog API with post CRUD operations"
  }' > main.json

# 2. Generate utils
curl -X POST "$API_URL/actions/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create utility functions for database operations"
  }' > utils.json

# 3. Generate tests
curl -X POST "$API_URL/actions/test" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "./main.py",
    "framework": "pytest"
  }' > tests.json

echo "Project files generated!"
```

### Use Case 2: Refactor Legacy Code

```python
import requests
import os

def refactor_project(project_path, requirements):
    """Refactor all Python files in a project."""
    
    API_URL = "http://localhost:8000/api/v1"
    TOKEN = os.environ.get("JM_API_TOKEN")
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Find all Python files
    py_files = []
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    
    # Refactor each file
    for py_file in py_files:
        response = requests.post(
            f"{API_URL}/actions/refactor",
            json={
                "file_path": py_file,
                "requirements": requirements
            },
            headers=headers
        )
        
        if response.status_code == 200:
            refactored = response.json()["data"]["refactored_code"]
            with open(py_file, "w") as f:
                f.write(refactored)
            print(f"Refactored: {py_file}")

# Usage
refactor_project(
    "./myproject",
    "Add type hints, improve variable names, add docstrings"
)
```

## Error Handling

### Handling Common Errors

```python
import requests

API_URL = "http://localhost:8000/api/v1"
TOKEN = "your-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

try:
    response = requests.post(
        f"{API_URL}/actions/generate",
        json={"prompt": "Generate code"},
        headers=headers,
        timeout=30
    )
    
    # Check status code
    if response.status_code == 401:
        print("Error: Invalid or expired token")
    elif response.status_code == 429:
        print("Error: Rate limit exceeded. Wait and retry.")
    elif response.status_code == 500:
        print("Error: Server error")
    elif response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"Success: {data['data']}")
        else:
            print(f"API Error: {data['error']}")
    
except requests.exceptions.Timeout:
    print("Error: Request timeout")
except requests.exceptions.ConnectionError:
    print("Error: Cannot connect to server")
except Exception as e:
    print(f"Error: {e}")
```

### Retry Logic with Exponential Backoff

```python
import requests
import time

def call_api_with_retry(endpoint, data, max_retries=3):
    """Call API with retry logic."""
    
    API_URL = "http://localhost:8000/api/v1"
    TOKEN = "your-token"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{API_URL}/{endpoint}",
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                return {"error": f"Status {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Request failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return {"error": str(e)}
    
    return {"error": "Max retries exceeded"}

# Usage
result = call_api_with_retry(
    "actions/generate",
    {"prompt": "Create a function"}
)
```

## Tips & Best Practices

1. **Always use Bearer token authentication** - Don't send tokens in URLs
2. **Implement rate limiting** - Respect 100 req/min limit per IP
3. **Handle errors gracefully** - Check status codes and error responses
4. **Use pagination** - For large result sets, use limit/offset
5. **Cache responses** - Reduce API calls for frequently accessed data
6. **Monitor metrics** - Use `/metrics` endpoints to track usage
7. **Use audit logs** - Review `/audit` endpoints for compliance
8. **Set appropriate timeouts** - API responses can take 1-3 seconds
9. **Batch operations when possible** - Generate multiple code snippets at once
10. **Keep tokens secure** - Store in environment variables, never in code
