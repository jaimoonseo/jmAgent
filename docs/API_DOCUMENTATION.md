# jmAgent REST API Documentation

## Overview

The jmAgent REST API provides a comprehensive interface for code generation, refactoring, testing, explanation, bug fixing, and configuration management. Built with FastAPI, it offers high-performance asynchronous endpoints with robust authentication, rate limiting, and comprehensive logging.

**Base URL**: `http://localhost:8000/api/v1`  
**Current Version**: 1.0.0  
**Status**: Production Ready

## Quick Start

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Generate Code
```bash
curl -X POST http://localhost:8000/api/v1/actions/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python function to calculate factorial"
  }'
```

## Authentication

The API supports two authentication methods:

### JWT Bearer Token

**How to get a token**: Contact your administrator or use the internal token generation service.

**Usage in requests**:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:8000/api/v1/health/detailed
```

**Token Structure**:
- `user_id`: Unique user identifier
- `agent_id`: Unique agent identifier
- `iat`: Token issued at timestamp
- `exp`: Token expiration timestamp

**Token Expiration**: Tokens expire after 30 minutes by default (configurable).

### API Key

Some endpoints support API key authentication for service-to-service communication.

**Usage in requests**:
```bash
curl -H "x-api-key: your-api-key" \
  http://localhost:8000/api/v1/health
```

## Response Format

All API responses follow a consistent JSON format:

**Success Response**:
```json
{
  "success": true,
  "data": {
    // endpoint-specific data
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "ERROR_TYPE"
}
```

## Rate Limiting

- **Default Limit**: 100 requests per minute per IP address
- **Status Code**: 429 (Too Many Requests)
- **Headers**:
  - `X-RateLimit-Limit`: Total allowed requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

## Endpoint Reference

### Health Endpoints

#### GET /health
Health check endpoint (no authentication required).

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy"
  }
}
```

#### GET /health/detailed
Detailed health information including system status.

**Response**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-04-06T13:56:00Z"
  }
}
```

#### GET /status
API status endpoint (requires authentication).

**Headers Required**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "success": true,
  "data": {
    "uptime": 3600,
    "requests_processed": 150,
    "version": "1.0.0"
  }
}
```

### Action Endpoints

#### POST /actions/generate
Generate code using natural language prompts.

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "prompt": "Create a FastAPI endpoint for user registration",
  "language": "python",
  "model": "haiku",
  "temperature": 0.2,
  "max_tokens": 2048
}
```

**Parameters**:
- `prompt` (string, required): Natural language description of code to generate
- `language` (string, optional): Programming language (python, typescript, sql, bash, etc.)
- `model` (string, optional): Model to use (haiku, sonnet, opus). Default: haiku
- `temperature` (float, optional): 0.0-1.0. Lower = more consistent. Default: 0.2
- `max_tokens` (integer, optional): Maximum response length. Default: 2048

**Response**:
```json
{
  "success": true,
  "data": {
    "code": "def generate_code(): ...",
    "language": "python",
    "tokens_used": 145,
    "model_used": "haiku"
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/actions/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a Python function to validate email addresses",
    "language": "python"
  }'
```

#### POST /actions/refactor
Refactor existing code.

**Authentication**: Required

**Request Body**:
```json
{
  "file_path": "/path/to/file.py",
  "requirements": "Add type hints and docstrings",
  "model": "sonnet",
  "temperature": 0.3
}
```

**Parameters**:
- `file_path` (string, required): Path to the file to refactor
- `requirements` (string, required): Specific refactoring requirements
- `model` (string, optional): Model to use
- `temperature` (float, optional): Temperature for generation

**Response**:
```json
{
  "success": true,
  "data": {
    "refactored_code": "def improved_function(): ...",
    "changes_made": ["Added type hints", "Added docstrings"],
    "tokens_used": 234
  }
}
```

#### POST /actions/test
Generate tests for code.

**Authentication**: Required

**Request Body**:
```json
{
  "file_path": "/path/to/file.py",
  "framework": "pytest",
  "language": "python"
}
```

**Parameters**:
- `file_path` (string, required): Path to the file
- `framework` (string, required): Test framework (pytest, vitest, jest, unittest, etc.)
- `language` (string, optional): Programming language

**Response**:
```json
{
  "success": true,
  "data": {
    "tests": "def test_function(): ...",
    "framework": "pytest",
    "tokens_used": 156
  }
}
```

#### POST /actions/explain
Explain code functionality.

**Authentication**: Required

**Request Body**:
```json
{
  "file_path": "/path/to/file.py",
  "focus_area": "algorithm",
  "language": "korean"
}
```

**Parameters**:
- `file_path` (string, required): Path to the file
- `focus_area` (string, optional): Specific area to focus on
- `language` (string, optional): Output language (english, korean, chinese, etc.)

**Response**:
```json
{
  "success": true,
  "data": {
    "explanation": "이 코드는 ...",
    "language": "korean"
  }
}
```

#### POST /actions/fix
Fix bugs in code.

**Authentication**: Required

**Request Body**:
```json
{
  "file_path": "/path/to/file.py",
  "error_message": "TypeError: 'NoneType' object is not subscriptable"
}
```

**Parameters**:
- `file_path` (string, required): Path to the file
- `error_message` (string, required): Error message or description

**Response**:
```json
{
  "success": true,
  "data": {
    "fixed_code": "def corrected_function(): ...",
    "bug_explanation": "The issue was due to missing null check",
    "tokens_used": 187
  }
}
```

#### POST /actions/chat
Interactive chat with the agent.

**Authentication**: Required

**Request Body**:
```json
{
  "message": "How do I refactor this function?",
  "conversation_id": "conv_123"
}
```

**Parameters**:
- `message` (string, required): User message
- `conversation_id` (string, optional): Conversation ID for context continuation

**Response**:
```json
{
  "success": true,
  "data": {
    "response": "To refactor this function...",
    "conversation_id": "conv_123",
    "turn_number": 2
  }
}
```

### Configuration Endpoints

#### GET /config
Retrieve current configuration.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": {
    "all_settings": {
      "host": "127.0.0.1",
      "port": 8000,
      "debug": false,
      "rate_limit_enabled": true,
      "rate_limit_per_minute": 100
    }
  }
}
```

#### POST /config
Update a single configuration setting.

**Authentication**: Required

**Request Body**:
```json
{
  "key": "debug",
  "value": true
}
```

**Parameters**:
- `key` (string, required): Setting key
- `value` (any, required): Setting value

**Response**:
```json
{
  "success": true,
  "data": {
    "key": "debug",
    "value": true
  }
}
```

#### PUT /config
Replace all configuration settings.

**Authentication**: Required (Admin only)

**Request Body**:
```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "debug": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "updated_count": 3
  }
}
```

#### DELETE /config/{key}
Delete (reset) a configuration setting to default.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": {
    "key": "debug",
    "default_value": false
  }
}
```

#### POST /config/reset
Reset all configuration to defaults.

**Authentication**: Required (Admin only)

**Response**:
```json
{
  "success": true,
  "data": {
    "reset": true,
    "defaults_count": 12
  }
}
```

### Metrics Endpoints

#### GET /metrics/summary
Get overall metrics summary.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": {
    "total_requests": 150,
    "total_tokens": 25000,
    "average_response_time_ms": 1200,
    "by_action": {
      "generate": {
        "total_requests": 50,
        "total_tokens": 10000,
        "success_rate": 0.96
      }
    }
  }
}
```

#### GET /metrics/by-action
Get metrics grouped by action type.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "action": "generate",
      "total_requests": 50,
      "success_count": 48,
      "failure_count": 2
    }
  ]
}
```

#### GET /metrics/by-model
Get metrics grouped by model used.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "model": "haiku",
      "total_requests": 100,
      "average_tokens": 200
    }
  ]
}
```

#### POST /metrics/reset
Reset all metrics to zero.

**Authentication**: Required (Admin only)

**Response**:
```json
{
  "success": true,
  "data": {
    "reset": true
  }
}
```

### Audit Endpoints

#### GET /audit/logs
Retrieve recent audit logs.

**Authentication**: Required

**Query Parameters**:
- `limit` (integer): Number of logs to return (1-100, default: 20)
- `offset` (integer): Pagination offset (default: 0)

**Response**:
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "id": 1,
        "timestamp": "2026-04-06T13:56:00Z",
        "user_id": "test_user",
        "action": "generate",
        "status": "success",
        "details": {
          "error": null,
          "duration": 1200,
          "tokens_used": 145
        }
      }
    ],
    "total": 150,
    "limit": 20,
    "offset": 0
  }
}
```

#### GET /audit/search
Search audit logs with filters.

**Authentication**: Required

**Query Parameters**:
- `action` (string): Filter by action type
- `user_id` (string): Filter by user ID
- `status` (string): Filter by status (success, error)
- `start_date` (string): Filter by start date (ISO format)
- `end_date` (string): Filter by end date (ISO format)
- `limit` (integer): Number of results (1-100)
- `offset` (integer): Pagination offset

**Example**:
```bash
curl "http://localhost:8000/api/v1/audit/search?action=generate&status=success" \
  -H "Authorization: Bearer $TOKEN"
```

#### GET /audit/export
Export audit logs in CSV or JSON format.

**Authentication**: Required

**Query Parameters**:
- `format` (string): Export format (csv or json, default: csv)
- `start_date` (string, optional): Filter by start date
- `end_date` (string, optional): Filter by end date

**Response**: File download

**Example**:
```bash
curl "http://localhost:8000/api/v1/audit/export?format=csv" \
  -H "Authorization: Bearer $TOKEN" \
  -o audit_logs.csv
```

#### GET /audit/summary
Get audit statistics summary.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": {
    "total_logs": 500,
    "actions": {
      "generate": 200,
      "refactor": 150,
      "test": 100,
      "explain": 50
    },
    "success_rate": 0.98,
    "error_rate": 0.02
  }
}
```

#### DELETE /audit/logs
Delete all audit logs.

**Authentication**: Required (Admin only)

**Response**:
```json
{
  "success": true,
  "data": {
    "cleared": true,
    "count": 500
  }
}
```

### Plugin Endpoints

#### GET /plugins
List all available plugins.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": {
    "plugins": [
      {
        "name": "code_formatter",
        "description": "Format code using language-specific formatters",
        "enabled": true,
        "version": "1.0.0"
      }
    ]
  }
}
```

#### GET /plugins/{name}
Get plugin details.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": {
    "name": "code_formatter",
    "description": "...",
    "enabled": true,
    "config_schema": {
      "type": "object",
      "properties": {
        "line_length": {"type": "integer"}
      }
    }
  }
}
```

#### POST /plugins/{name}/enable
Enable a plugin.

**Authentication**: Required (Admin recommended)

**Response**:
```json
{
  "success": true,
  "data": {
    "name": "code_formatter",
    "enabled": true
  }
}
```

#### POST /plugins/{name}/disable
Disable a plugin.

**Authentication**: Required (Admin recommended)

**Response**:
```json
{
  "success": true,
  "data": {
    "name": "code_formatter",
    "enabled": false
  }
}
```

#### GET /plugins/{name}/config
Get plugin configuration.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": {
    "name": "code_formatter",
    "config": {
      "line_length": 100,
      "use_tabs": false
    }
  }
}
```

#### POST /plugins/{name}/config
Update plugin configuration.

**Authentication**: Required

**Request Body**:
```json
{
  "line_length": 120,
  "use_tabs": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "name": "code_formatter",
    "config": {
      "line_length": 120,
      "use_tabs": true
    }
  }
}
```

### Template Endpoints

#### GET /templates
List all templates (built-in and custom).

**Authentication**: Required

**Query Parameters**:
- `action` (string, optional): Filter by action type

**Response**:
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "id": "builtin_1",
        "name": "FastAPI Endpoint",
        "action": "generate",
        "description": "Generate a FastAPI endpoint",
        "is_custom": false
      },
      {
        "id": "custom_1",
        "name": "My Custom Template",
        "action": "generate",
        "is_custom": true
      }
    ]
  }
}
```

#### GET /templates/{id}
Get template details and content.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "custom_1",
    "name": "My Custom Template",
    "action": "generate",
    "content": "Create a FastAPI endpoint: {{ requirements }}",
    "variables": ["requirements"],
    "description": "My template"
  }
}
```

#### POST /templates
Create a custom template.

**Authentication**: Required

**Request Body**:
```json
{
  "name": "My Template",
  "action": "generate",
  "content": "Create a {{ language }} function: {{ requirements }}",
  "description": "Custom template for generation"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "custom_1",
    "name": "My Template",
    "created_at": "2026-04-06T13:56:00Z"
  }
}
```

#### PUT /templates/{id}
Update a custom template.

**Authentication**: Required

**Request Body**:
```json
{
  "content": "Updated content: {{ new_variable }}",
  "description": "Updated description"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "custom_1",
    "updated_at": "2026-04-06T14:00:00Z"
  }
}
```

#### DELETE /templates/{id}
Delete a custom template.

**Authentication**: Required

**Note**: Built-in templates cannot be deleted.

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "custom_1",
    "deleted": true
  }
}
```

#### POST /templates/{id}/preview
Preview template with variables filled in.

**Authentication**: Required

**Request Body**:
```json
{
  "language": "python",
  "requirements": "calculate factorial"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "preview": "Create a python function: calculate factorial"
  }
}
```

#### POST /templates/{id}/use
Use a template for code generation or other actions.

**Authentication**: Required

**Request Body**:
```json
{
  "language": "python",
  "requirements": "validate email addresses",
  "model": "haiku"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "code": "def validate_email(email: str) -> bool: ...",
    "tokens_used": 145
  }
}
```

## Common Patterns

### Pagination

Endpoints that return lists support pagination with `limit` and `offset`:

```bash
# First page
curl "http://localhost:8000/api/v1/audit/logs?limit=20&offset=0" \
  -H "Authorization: Bearer $TOKEN"

# Second page
curl "http://localhost:8000/api/v1/audit/logs?limit=20&offset=20" \
  -H "Authorization: Bearer $TOKEN"
```

### Filtering

Use query parameters to filter results:

```bash
curl "http://localhost:8000/api/v1/audit/search?action=generate&status=success&user_id=john" \
  -H "Authorization: Bearer $TOKEN"
```

### Error Handling

All errors follow a consistent format with HTTP status codes:

- `400`: Bad Request - Invalid input
- `401`: Unauthorized - Missing/invalid authentication
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource doesn't exist
- `422`: Unprocessable Entity - Validation error
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error

**Error Response Example**:
```json
{
  "success": false,
  "error": "Invalid prompt provided",
  "error_code": "VALIDATION_ERROR"
}
```

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

## Rate Limits & Performance

- **Default Rate Limit**: 100 requests per minute per IP
- **Typical Response Time**: 1-3 seconds (depends on model and request complexity)
- **Max Tokens**: 4096 (default, configurable per request)
- **Concurrent Requests**: Unlimited (rate-limited by minute)

## Support

For issues, questions, or feature requests, please:

1. Check the OpenAPI documentation at `/api/docs`
2. Review error messages and error codes
3. Contact your system administrator
4. Submit an issue to the project repository
