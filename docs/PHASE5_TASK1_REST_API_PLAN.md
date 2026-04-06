# Phase 5, Task 1: REST API Server for jmAgent

**Status**: Planning  
**Priority**: Critical (Foundation for Web Dashboard, Slack Bot, IDE Extensions)  
**Duration**: 4-5 weeks (20-25 days)  
**Target**: Production-ready REST API microservice  
**Date**: 2026-04-04

---

## 1. Executive Summary

Transform jmAgent from a local CLI tool into a network-accessible microservice. The REST API becomes the foundation for:
- Web Dashboard (Phase 5, Task 2)
- Slack Bot (Phase 5, Task 3)
- VS Code Extension (Phase 5, Task 4)
- Mobile App (Phase 6)

**Key Success Metric**: All 6 action endpoints + 5 management endpoint categories fully functional, 50+ integration tests passing, <500ms response times.

---

## 2. API Specification (RESTful Design)

### 2.1 Action Endpoints (Core)

```
POST   /api/v1/actions/generate
├─ Request:  { prompt, language?, model?, temperature?, max_tokens?, context? }
├─ Response: { id, status, code, tokens_used, duration_ms, metadata }
└─ Async:    Job ID returned immediately, optional streaming

POST   /api/v1/actions/refactor
├─ Request:  { file_path, code, requirements, language?, model? }
├─ Response: { id, status, refactored_code, changes, tokens_used, duration_ms }
└─ Async:    Full refactored code in response

POST   /api/v1/actions/test
├─ Request:  { file_path, code, framework, language?, coverage_target? }
├─ Response: { id, status, test_code, coverage, tokens_used, duration_ms }
└─ Async:    Generated tests with coverage analysis

POST   /api/v1/actions/explain
├─ Request:  { file_path, code, language?, detail_level? }
├─ Response: { id, status, explanation, summary, key_points, tokens_used }
└─ Language: Support Korean (ko), English (en) output

POST   /api/v1/actions/fix
├─ Request:  { file_path, code, error, context?, language? }
├─ Response: { id, status, fixed_code, diagnosis, solution, tokens_used }
└─ Async:    Root cause analysis included

POST   /api/v1/actions/chat
├─ Request:  { message, conversation_id?, history?, model? }
├─ Response: { id, status, reply, conversation_id, tokens_used }
└─ Async:    Multi-turn conversation with session management
```

### 2.2 Configuration Endpoints

```
GET    /api/v1/config
├─ Response: { model, temperature, max_tokens, language, auth_mode, ... }
└─ Public:   Non-sensitive config only

PUT    /api/v1/config
├─ Request:  { model?, temperature?, max_tokens?, language? }
├─ Response: { status, updated_config }
└─ Auth:     Required

GET    /api/v1/config/{key}
├─ Response: { key, value, description }
└─ Example:  GET /api/v1/config/model → { key: "model", value: "haiku" }

PATCH  /api/v1/config/{key}
├─ Request:  { value }
├─ Response: { key, value, previous_value }
└─ Auth:     Required
```

### 2.3 Metrics Endpoints

```
GET    /api/v1/metrics/summary
├─ Response: { 
│   total_requests, total_tokens, avg_duration_ms,
│   by_action: { generate: {...}, refactor: {...}, ... },
│   cost_estimate_usd, uptime_seconds
│ }
└─ Time:     Last 24h, 7d, 30d, all-time options

GET    /api/v1/metrics/by-action
├─ Response: { 
│   generate: { count, avg_duration, total_tokens, error_rate },
│   refactor: { ... },
│   test: { ... },
│   explain: { ... },
│   fix: { ... },
│   chat: { ... }
│ }
└─ Aggregation: Hourly, daily, weekly options

GET    /api/v1/metrics/by-model
├─ Response: { haiku: {...}, sonnet: {...}, opus: {...} }
└─ Breakdown: Cost and token usage by model

DELETE /api/v1/metrics
├─ Request:  { confirm: true }
├─ Response: { status, deleted_records }
└─ Auth:     Admin only
```

### 2.4 Audit Endpoints

```
GET    /api/v1/audit/logs
├─ Response: [
│   { id, timestamp, action, user, ip, status, tokens_used, duration_ms },
│   ...
│ ]
├─ Pagination: limit=50, offset=0
└─ Filters:    action, user, status, date_from, date_to

GET    /api/v1/audit/search
├─ Request:  { query, action?, user?, status?, date_range? }
├─ Response: { matches, total, page, total_pages }
└─ Full-text: Search logs by action, error messages, user

GET    /api/v1/audit/summary
├─ Response: { 
│   total_actions, today, this_week, this_month,
│   error_count, error_rate, top_users, top_actions
│ }
└─ Dashboard-friendly aggregated data

DELETE /api/v1/audit/logs
├─ Request:  { confirm: true, before_date?: ISO-8601 }
├─ Response: { status, deleted_records }
└─ Auth:     Admin only
```

### 2.5 Plugins Endpoints

```
GET    /api/v1/plugins
├─ Response: [
│   { name, version, enabled, description, endpoints[], dependencies[] },
│   ...
│ ]
└─ Includes: Built-in and third-party plugins

POST   /api/v1/plugins/{name}/enable
├─ Response: { status, name, enabled: true }
└─ Auth:     Required

POST   /api/v1/plugins/{name}/disable
├─ Response: { status, name, enabled: false }
└─ Auth:     Required

POST   /api/v1/plugins/install
├─ Request:  { name, version?, source? }
├─ Response: { status, installed_plugins[] }
└─ Auth:     Admin only

DELETE /api/v1/plugins/{name}
├─ Response: { status, name, uninstalled: true }
└─ Auth:     Admin only
```

### 2.6 Templates Endpoints

```
GET    /api/v1/templates
├─ Response: [
│   { id, name, category, description, language, framework, ... },
│   ...
│ ]
└─ Categories: web, mobile, cli, data, ml, ...

GET    /api/v1/templates/{id}
├─ Response: { id, name, content, variables[], examples[] }
└─ Full template with placeholders

POST   /api/v1/templates/use
├─ Request:  { template_id, variables: { ... } }
├─ Response: { id, status, generated_code }
└─ Async:    Template instantiation

POST   /api/v1/templates/create
├─ Request:  { name, category, language, content, variables[], examples[] }
├─ Response: { id, name, created_at }
└─ Auth:     Required

PUT    /api/v1/templates/{id}
├─ Request:  { name?, content?, variables? }
├─ Response: { id, name, updated_at }
└─ Auth:     Required

DELETE /api/v1/templates/{id}
├─ Response: { status, id, deleted: true }
└─ Auth:     Admin only
```

### 2.7 Health & Status Endpoints

```
GET    /api/v1/health
├─ Response: { status: "healthy" | "degraded" | "unhealthy" }
└─ Quick check for load balancers

GET    /api/v1/status
├─ Response: {
│   status, uptime_seconds, version, bedrock_status,
│   cache_status, database_status, request_count_1h,
│   avg_response_time_ms, active_jobs
│ }
└─ Detailed server state

GET    /api/v1/status/jobs
├─ Response: [
│   { id, action, status, progress, eta_seconds, tokens_used },
│   ...
│ ]
└─ Track long-running operations
```

---

## 3. Technology Stack

### 3.1 Core Stack
- **Framework**: FastAPI (v0.104+) - async-native, auto OpenAPI docs
- **Server**: Uvicorn (v0.24+) - ASGI server, WebSocket support
- **Validation**: Pydantic (v2.0+) - request/response schemas
- **Database**: SQLite (existing audit.db) + SQLAlchemy ORM
- **Caching**: Redis (optional, Phase 5.1+) - session & response caching
- **Task Queue**: Celery (optional, Phase 5.1+) - background jobs

### 3.2 Security
- **Authentication**: JWT (JSON Web Tokens)
- **API Keys**: Support both JWT and API Key auth
- **Rate Limiting**: Token bucket algorithm, Redis-backed
- **CORS**: Configurable CORS headers
- **HTTPS**: SSL/TLS via Uvicorn config
- **CSRF**: Token-based CSRF protection
- **Validation**: Pydantic + input sanitization

### 3.3 Observability
- **Logging**: Existing StructuredLogger (src/utils/logging.py)
- **Metrics**: Prometheus-compatible (future Phase 5.1)
- **Tracing**: OpenTelemetry-ready (future Phase 6)
- **Audit**: Existing AuditStorage (src/audit/storage.py)

### 3.4 Testing & Documentation
- **Testing**: pytest + httpx (async HTTP client)
- **Test Data**: Factory fixtures with factory_boy
- **Documentation**: Swagger UI + OpenAPI v3.1
- **Load Testing**: locust (Phase 5.1)

### 3.5 Deployment
- **Docker**: Alpine-based image (~200MB)
- **Docker Compose**: Local development & CI/CD
- **Environment**: 12-factor app config
- **Health Checks**: Kubernetes-ready probes

---

## 4. Implementation Plan (5 Subtasks)

### Subtask 1: Project Structure & FastAPI Setup (3-4 days)
**Objective**: Create API framework with middleware & error handling

**Tasks**:
- [ ] Initialize `src/api/` directory structure
- [ ] Create FastAPI app with `src/api/main.py`
- [ ] Implement CORS, compression, gzip middleware
- [ ] Design unified error response schema
- [ ] Create exception handlers (BadRequest, Unauthorized, NotFound, etc.)
- [ ] Setup request/response logging middleware
- [ ] Configure startup/shutdown hooks
- [ ] Create Pydantic base schemas for responses
- [ ] Implement pagination helper utilities
- [ ] Write 10+ unit tests for middleware & error handling

**Deliverables**:
- `src/api/main.py` - FastAPI app with middleware
- `src/api/models/responses.py` - Common response schemas
- `src/api/middleware/` - Error handling, logging, CORS
- `tests/test_api_middleware.py`

**Definition of Done**:
- FastAPI app starts on port 8000 (configurable)
- All middleware tests pass
- Error responses follow consistent schema

---

### Subtask 2: Authentication & Security (2-3 days)
**Objective**: Implement JWT authentication & API key management

**Tasks**:
- [ ] Design JWT token schema (sub, exp, scopes, iat)
- [ ] Implement JWT creation & validation (`src/api/auth/jwt.py`)
- [ ] Create API key generation & storage (in-memory + SQLite option)
- [ ] Implement bearer token extraction from headers
- [ ] Create dependency for protected routes
- [ ] Implement role-based access control (RBAC) - admin, user, viewer
- [ ] Add rate limiting per user/IP (initial: Redis-free using in-memory)
- [ ] Setup SSL/TLS config helpers
- [ ] Write 15+ security tests (token validation, expiration, scopes, etc.)
- [ ] Document authentication flow & client setup

**Deliverables**:
- `src/api/auth/jwt.py` - JWT token management
- `src/api/auth/security.py` - Security utilities & rate limiting
- `src/api/middleware/auth.py` - Authentication middleware
- `tests/test_api_auth.py`
- `docs/API_AUTHENTICATION.md`

**Definition of Done**:
- JWT tokens can be created, validated, and refreshed
- Protected routes reject unauthorized requests
- Rate limiting blocks excessive requests
- Security tests all passing

---

### Subtask 3: Action Endpoints (3-4 days)
**Objective**: Implement /api/v1/actions/* endpoints connected to JmAgent

**Tasks**:
- [ ] Create request/response schemas for all 6 actions (`src/api/schemas/actions.py`)
- [ ] Implement `POST /api/v1/actions/generate` endpoint
- [ ] Implement `POST /api/v1/actions/refactor` endpoint
- [ ] Implement `POST /api/v1/actions/test` endpoint
- [ ] Implement `POST /api/v1/actions/explain` endpoint (with Korean output support)
- [ ] Implement `POST /api/v1/actions/fix` endpoint
- [ ] Implement `POST /api/v1/actions/chat` endpoint with conversation history
- [ ] Add async job tracking with unique IDs
- [ ] Implement optional streaming responses (SSE for generate/test/chat)
- [ ] Add request validation & sanitization
- [ ] Write 30+ integration tests for all action endpoints
- [ ] Test error handling (bad request, server error, timeout)

**Deliverables**:
- `src/api/routes/actions.py` - All 6 action endpoints
- `src/api/schemas/actions.py` - Request/response schemas
- `tests/test_api_actions.py` - 30+ integration tests

**Definition of Done**:
- All 6 endpoints return proper responses
- Streaming works for generate/test/chat
- Error handling tested & robust
- Response times <500ms (non-streaming)

---

### Subtask 4: Management Endpoints (2-3 days)
**Objective**: Implement config, metrics, audit, plugins, templates endpoints

**Tasks**:
- [ ] Create schemas for config, metrics, audit, plugins, templates (`src/api/schemas/`)
- [ ] Implement `GET /api/v1/config` & `PUT /api/v1/config`
- [ ] Implement `GET /api/v1/config/{key}` & `PATCH /api/v1/config/{key}`
- [ ] Implement `GET /api/v1/metrics/summary` & `/by-action` & `/by-model`
- [ ] Implement `DELETE /api/v1/metrics` (admin only)
- [ ] Implement `GET /api/v1/audit/logs` & `/search` & `/summary`
- [ ] Implement `DELETE /api/v1/audit/logs` (admin only)
- [ ] Implement `GET /api/v1/plugins` & `POST /plugins/{name}/enable` & `/disable`
- [ ] Implement `GET /api/v1/templates` & `/templates/{id}` & `POST /use`
- [ ] Implement `GET /api/v1/health` & `/status` & `/status/jobs`
- [ ] Add pagination & filtering for list endpoints
- [ ] Write 20+ tests for management endpoints

**Deliverables**:
- `src/api/routes/config.py`
- `src/api/routes/metrics.py`
- `src/api/routes/audit.py`
- `src/api/routes/plugins.py`
- `src/api/routes/templates.py`
- `src/api/routes/health.py`
- `src/api/schemas/` - All schema files
- `tests/test_api_management.py`

**Definition of Done**:
- All endpoints return correct data structures
- Pagination works with limit/offset
- Filtering works where applicable
- Admin-only endpoints properly protected

---

### Subtask 5: Testing, Documentation & Deployment (2-3 days)
**Objective**: Complete test suite, API documentation, and Docker deployment

**Tasks**:
- [ ] Write 50+ integration tests covering all endpoints
- [ ] Test error scenarios (400, 401, 403, 404, 500)
- [ ] Load test basic performance (<500ms response time)
- [ ] Generate Swagger/OpenAPI documentation
- [ ] Create API usage guide & examples (`docs/API.md`)
- [ ] Create deployment guide (`docs/API_DEPLOYMENT.md`)
- [ ] Create client library examples (curl, Python, JavaScript)
- [ ] Create `docker/Dockerfile` for API server
- [ ] Create `docker/docker-compose.yml` for local development
- [ ] Test Docker build & basic operations
- [ ] Create `.env.example` with required variables
- [ ] Document configuration options & environment variables
- [ ] Setup CI/CD pipeline for API tests (GitHub Actions)

**Deliverables**:
- `tests/test_api_*.py` - 50+ tests, all passing
- `docs/API.md` - Full API reference & examples
- `docs/API_DEPLOYMENT.md` - Deployment & configuration
- `docker/Dockerfile`
- `docker/docker-compose.yml`
- `.env.example`
- Swagger UI at `http://localhost:8000/docs`

**Definition of Done**:
- All 50+ tests pass
- API documentation complete with examples
- Docker image builds successfully
- Can deploy and test locally with docker-compose

---

## 5. Project Structure

```
src/api/
├── __init__.py                          # Package initialization
├── main.py                              # FastAPI app & router setup
├── config.py                            # API configuration (port, workers, etc.)
│
├── auth/
│   ├── __init__.py
│   ├── jwt.py                          # JWT token creation/validation
│   ├── keys.py                         # API key management
│   ├── security.py                     # Password hashing, rate limiting
│   └── dependencies.py                 # Dependency injection for auth
│
├── routes/
│   ├── __init__.py
│   ├── actions.py                      # /api/v1/actions/* endpoints
│   ├── config.py                       # /api/v1/config/* endpoints
│   ├── metrics.py                      # /api/v1/metrics/* endpoints
│   ├── audit.py                        # /api/v1/audit/* endpoints
│   ├── plugins.py                      # /api/v1/plugins/* endpoints
│   ├── templates.py                    # /api/v1/templates/* endpoints
│   └── health.py                       # /api/v1/health, /status
│
├── schemas/
│   ├── __init__.py
│   ├── common.py                       # Pagination, filters, errors
│   ├── actions.py                      # Request/response for actions
│   ├── config.py                       # Config schemas
│   ├── metrics.py                      # Metrics schemas
│   ├── audit.py                        # Audit schemas
│   ├── plugins.py                      # Plugin schemas
│   └── templates.py                    # Template schemas
│
├── models/
│   ├── __init__.py
│   ├── responses.py                    # ApiResponse, ErrorResponse
│   ├── job.py                          # AsyncJob model
│   └── user.py                         # User/Admin model
│
├── middleware/
│   ├── __init__.py
│   ├── auth.py                         # Authentication middleware
│   ├── error_handler.py                # Exception handlers
│   ├── logging.py                      # Request/response logging
│   ├── rate_limit.py                   # Rate limiting middleware
│   └── cors.py                         # CORS configuration
│
├── services/
│   ├── __init__.py
│   ├── agent_service.py                # JmAgent wrapper
│   ├── job_service.py                  # Async job tracking
│   ├── config_service.py               # Config management
│   ├── metrics_service.py              # Metrics aggregation
│   ├── audit_service.py                # Audit log queries
│   ├── plugin_service.py               # Plugin management
│   └── template_service.py             # Template management
│
└── utils/
    ├── __init__.py
    ├── pagination.py                   # Pagination helpers
    ├── filters.py                      # Filter parsing
    └── validators.py                   # Input validation

tests/
├── __init__.py
├── conftest.py                         # pytest fixtures & setup
├── test_api_health.py                  # Health endpoint tests
├── test_api_auth.py                    # Authentication tests
├── test_api_actions.py                 # Action endpoint tests
├── test_api_config.py                  # Config endpoint tests
├── test_api_metrics.py                 # Metrics endpoint tests
├── test_api_audit.py                   # Audit endpoint tests
├── test_api_plugins.py                 # Plugin endpoint tests
├── test_api_templates.py               # Template endpoint tests
├── test_api_integration.py             # Full integration tests
└── fixtures/
    ├── __init__.py
    ├── client.py                       # FastAPI TestClient
    ├── auth.py                         # Auth fixtures (tokens, users)
    └── data.py                         # Test data generators

docker/
├── Dockerfile                          # Multi-stage API build
└── docker-compose.yml                  # Local dev with Bedrock

docs/
├── API.md                              # Full API reference
├── API_AUTHENTICATION.md               # Auth flow & setup
├── API_DEPLOYMENT.md                   # Production deployment
├── API_EXAMPLES.md                     # Client library examples
└── API_PERFORMANCE.md                  # Benchmarks & tuning

.env.example                            # Template environment file
```

---

## 6. Timeline & Milestones

### Week 1-2: Foundation (Subtasks 1-2)
- **Days 1-4**: Project structure, FastAPI setup, middleware
- **Days 5-8**: JWT auth, API keys, rate limiting
- **Milestone**: API starts, protected routes work

### Week 3-4: Core Features (Subtask 3)
- **Days 9-13**: Action endpoint implementation
- **Days 14-16**: Streaming responses, async job tracking
- **Milestone**: All 6 actions accessible via API

### Week 4: Management (Subtask 4)
- **Days 17-19**: Config, metrics, audit endpoints
- **Days 20-21**: Plugins, templates, health endpoints
- **Milestone**: Full admin API available

### Week 5: Polish & Deployment (Subtask 5)
- **Days 22-24**: Testing, documentation, Docker
- **Days 25-26**: Performance optimization, CI/CD setup
- **Milestone**: Production-ready API with 50+ tests passing

---

## 7. Dependencies & Integration Points

### Existing Code Reuse
```python
# Core agent
from src.agent import JmAgent
from src.models import CodeAction, CodeResponse

# Configuration
from src.config.settings import Settings
from src.utils.logging import StructuredLogger

# Data persistence
from src.audit.storage import AuditStorage
from src.database import Database

# Utilities
from src.utils.token_counter import estimate_tokens
from src.utils.code_formatter import format_code
from src.utils.file_handler import FileHandler

# Plugins
from src.plugins.manager import PluginManager
from src.templates.manager import TemplateManager
```

### New Dependencies to Add
```
# Core API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6

# Authentication & Security
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pydantic-settings>=2.0.0

# Optional: Task Queue & Caching
celery>=5.3.0
redis>=5.0.0

# Testing
httpx>=0.25.0
pytest-asyncio>=0.21.0
factory-boy>=3.3.0
```

**Installation**:
```bash
pip install fastapi uvicorn python-jose passlib python-multipart pydantic-settings httpx pytest-asyncio factory-boy
```

---

## 8. Success Criteria

### Functional Requirements
- [ ] **Actions API**: All 6 endpoints (generate, refactor, test, explain, fix, chat) fully functional
- [ ] **Config API**: GET/PUT endpoints working with persistent config
- [ ] **Metrics API**: Summary, by-action, by-model endpoints with correct aggregations
- [ ] **Audit API**: Logs, search, summary endpoints with proper queries
- [ ] **Plugins API**: List, enable, disable endpoints functional
- [ ] **Templates API**: CRUD operations fully working
- [ ] **Health API**: Both `/health` and `/status` returning correct data

### Non-Functional Requirements
- [ ] **Performance**: Average response time <500ms (non-streaming actions)
- [ ] **Throughput**: Handle 100+ concurrent requests (load tested)
- [ ] **Reliability**: 99.5% uptime in testing
- [ ] **Security**: JWT validation, rate limiting, input sanitization
- [ ] **Documentation**: OpenAPI docs complete, 100+ examples

### Testing Requirements
- [ ] **Unit Tests**: 30+ covering auth, middleware, utilities
- [ ] **Integration Tests**: 50+ covering all endpoints
- [ ] **Error Cases**: 20+ tests for error handling
- [ ] **Performance Tests**: Load testing with 100+ concurrent users
- [ ] **Security Tests**: Auth bypass attempts, injection attacks

### Deployment Requirements
- [ ] **Docker**: Image builds, passes security scan
- [ ] **Configuration**: All settings via environment variables
- [ ] **Documentation**: README, deployment guide, examples
- [ ] **CI/CD**: GitHub Actions pipeline runs tests on push

---

## 9. Assumptions & Constraints

### Assumptions
1. **JmAgent is thread-safe** and can be reused across multiple requests
2. **Bedrock API remains stable** (no major breaking changes during Phase 5)
3. **SQLite is sufficient** for audit storage at current scale
4. **In-memory rate limiting is acceptable** (Redis added in Phase 5.1)
5. **Streaming responses are optional** (fallback to batch response)

### Constraints
1. **No external dependencies** beyond listed (boto3, pydantic, fastapi)
2. **Single-server deployment** for Phase 5 (clustering in Phase 6)
3. **JWT tokens valid for 24 hours** (configurable)
4. **API key limit: 10 keys per user** (configurable)
5. **Request timeout: 30 seconds** (configurable per action)

### Risks & Mitigation
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Bedrock API latency spikes | Slow responses | Implement request timeout, circuit breaker |
| High concurrent load | Memory/CPU exhaustion | Rate limiting, connection pooling |
| JWT key exposure | Security breach | Rotate keys monthly, use HTTPS only |
| SQLite under load | Audit data loss | Background async writes, periodic backups |
| Streaming connection drops | Incomplete data | Resumable streaming with checksums |

---

## 10. Post-Phase 5 Roadmap

### Phase 5.1: Optimization & Scaling (2-3 weeks)
- Redis caching for metrics & config
- Celery background jobs for long operations
- Load testing & performance tuning
- Helm charts for Kubernetes
- Prometheus metrics export

### Phase 5.2: Advanced Features (2-3 weeks)
- WebSocket support for real-time streaming
- Batch operation endpoints
- Custom workflow builder API
- Integration with GitHub/GitLab APIs
- OpenTelemetry distributed tracing

### Phase 6: Enterprise Features (4-6 weeks)
- Multi-tenancy support
- Team collaboration
- RBAC with fine-grained permissions
- Audit webhooks & event streaming
- Advanced analytics dashboard

---

## 11. Getting Started Checklist

### Before Starting Implementation
- [ ] Review this plan with team
- [ ] Confirm Bedrock credentials for testing
- [ ] Setup FastAPI development environment
- [ ] Create API repository/branch (if separate from main)
- [ ] Setup local Docker environment
- [ ] Create test database schema (audit.db)

### Initial Setup Commands
```bash
# Install dependencies
pip install -r requirements-api.txt

# Create API structure
mkdir -p src/api/{auth,routes,schemas,models,middleware,services,utils}
mkdir -p tests/fixtures
mkdir -p docker docs

# Initialize FastAPI app
python -c "from fastapi import FastAPI; app = FastAPI(); print('FastAPI ready')"

# Run initial tests
pytest tests/ -v --tb=short
```

### First Week Deliverables
1. ✅ Directory structure created
2. ✅ FastAPI app starts on port 8000
3. ✅ Middleware tests passing
4. ✅ JWT authentication working
5. ✅ 1-2 example action endpoints working

---

## References

- **CLAUDE.md**: jmAgent architecture & design decisions
- **Phase 2 Completion**: Context loading, prompt caching, streaming support
- **Phase 3 Completion**: Advanced features baseline
- **API Design**: RESTful principles, Swagger/OpenAPI standard
- **Security**: OWASP Top 10, JWT best practices
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Bedrock API**: AWS Bedrock runtime documentation

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-04  
**Author**: jmAgent Planning Team  
**Status**: Ready for Implementation
