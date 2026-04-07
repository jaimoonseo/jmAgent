# jmAgent REST API - Deployment Guide

Complete guide to deploy and run the jmAgent REST API in development and production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Configuration](#configuration)
4. [Running the Server](#running-the-server)
5. [Production Deployment](#production-deployment)
6. [Docker Deployment](#docker-deployment)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Monitoring](#monitoring)

## Prerequisites

- **Python**: 3.10 or higher
- **pip**: Python package manager
- **AWS Account**: For Bedrock API access (either API Key or IAM credentials)
- **Git**: For cloning the repository
- **OS**: Linux, macOS, or Windows (with WSL2)

### Check Prerequisites

```bash
python3 --version  # Should be 3.10+
pip --version      # Should be 21.0+
aws --version      # Optional: For AWS configuration
```

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/jmAgent.git
cd jmAgent
```

### 2. Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate venv
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install the package in editable mode
pip install -e .
```

### 4. Configure Environment

Create a `.env` file in the project root:

```bash
# AWS Bedrock Configuration
# Option 1: Use API Key
AWS_BEARER_TOKEN_BEDROCK=ABSK-xxxxxxxxxxxxxxxxxxx
# Option 2: Use IAM (set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)

AWS_BEDROCK_REGION=us-east-1

# jmAgent API Configuration
JMAGENT_API_JWT_SECRET_KEY=your-secret-key-at-least-32-characters-long
JMAGENT_API_JWT_EXPIRATION_MINUTES=30

# Optional
JM_DEFAULT_MODEL=haiku  # haiku, sonnet, opus
JM_LOG_LEVEL=INFO
JMAGENT_API_RATE_LIMIT_ENABLED=true
JMAGENT_API_RATE_LIMIT_PER_MINUTE=100
```

### 5. Verify Setup

```bash
# Test authentication
python src/auth/bedrock_auth.py

# Expected output: "Successfully authenticated with AWS Bedrock"
```

## Configuration

### Environment Variables

**Required**:
- `AWS_BEARER_TOKEN_BEDROCK` OR AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`)
- `JMAGENT_API_JWT_SECRET_KEY` (minimum 32 characters)

**Optional**:

```bash
# API Server
JM_HOST=127.0.0.1
JM_PORT=8000
JM_DEBUG=False

# JWT
JMAGENT_API_JWT_EXPIRATION_MINUTES=30
JMAGENT_API_JWT_ALGORITHM=HS256

# Model
JM_DEFAULT_MODEL=haiku
JM_TEMPERATURE=0.2
JM_MAX_TOKENS=4096

# Rate Limiting
JMAGENT_API_RATE_LIMIT_ENABLED=true
JMAGENT_API_RATE_LIMIT_PER_MINUTE=100

# Logging
JM_LOG_LEVEL=INFO
JMAGENT_API_ENABLE_REQUEST_LOGGING=true
JMAGENT_API_ENABLE_ERROR_LOGGING=true
```

### AWS Configuration

**Using API Key (Recommended for development)**:

```bash
# Set in .env or environment
export AWS_BEARER_TOKEN_BEDROCK=ABSK-your-key-here
export AWS_BEDROCK_REGION=us-east-1
```

**Using IAM Credentials (Recommended for production)**:

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

# Option 2: AWS credentials file (~/.aws/credentials)
[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key

# Option 3: AWS configuration file (~/.aws/config)
[default]
region = us-east-1
```

### JWT Secret Generation

Generate a strong secret for production:

```bash
# Option 1: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Option 2: Using OpenSSL
openssl rand -base64 32

# Option 3: Using /dev/urandom
head -c 32 /dev/urandom | base64
```

## Running the Server

### Development Mode

```bash
# With auto-reload
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

# Or using Python
python -m uvicorn src.api.main:app --reload

# Access API:
# - Health: http://localhost:8000/api/v1/health
# - Docs: http://localhost:8000/api/docs
# - ReDoc: http://localhost:8000/api/redoc
```

### Production Mode

```bash
# Using Uvicorn with multiple workers
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn (recommended)
pip install gunicorn
gunicorn src.api.main:app -w 4 -b 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker

# Using Gunicorn with SSL
gunicorn src.api.main:app \
  -w 4 \
  -b 0.0.0.0:8000 \
  --worker-class uvicorn.workers.UvicornWorker \
  --certfile=/path/to/cert.pem \
  --keyfile=/path/to/key.pem
```

### Verify Server is Running

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Expected response:
# {"success": true, "data": {"status": "healthy"}}

# Detailed health
curl http://localhost:8000/api/v1/health/detailed
```

## Production Deployment

### System Requirements

- **CPU**: 2+ cores recommended
- **Memory**: 2GB minimum, 4GB+ recommended
- **Disk**: 10GB free space
- **Network**: Stable internet (for Bedrock API calls)

### Systemd Service (Linux)

Create `/etc/systemd/system/jmagent-api.service`:

```ini
[Unit]
Description=jmAgent REST API
After=network.target

[Service]
User=jmagent
WorkingDirectory=/home/jmagent/jmAgent
Environment="PATH=/home/jmagent/jmAgent/venv/bin"
Environment="AWS_BEARER_TOKEN_BEDROCK=ABSK-xxx"
Environment="JMAGENT_API_JWT_SECRET_KEY=xxx"
ExecStart=/home/jmagent/jmAgent/venv/bin/gunicorn \
  src.api.main:app \
  -w 4 \
  -b 0.0.0.0:8000 \
  --worker-class uvicorn.workers.UvicornWorker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable jmagent-api
sudo systemctl start jmagent-api
sudo systemctl status jmagent-api
```

### Nginx Reverse Proxy

Configure `/etc/nginx/sites-available/jmagent`:

```nginx
server {
    listen 80;
    server_name api.example.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'" always;
    
    # Proxy to jmAgent API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 30s;
    }
    
    # Docs
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }
    
    location /redoc {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

Enable and test:

```bash
sudo ln -s /etc/nginx/sites-available/jmagent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install package
RUN pip install -e .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run server
CMD ["gunicorn", "src.api.main:app", "-w", "4", "-b", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  jmagent-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AWS_BEARER_TOKEN_BEDROCK=${AWS_BEARER_TOKEN_BEDROCK}
      - AWS_BEDROCK_REGION=${AWS_BEDROCK_REGION}
      - JMAGENT_API_JWT_SECRET_KEY=${JMAGENT_API_JWT_SECRET_KEY}
      - JM_LOG_LEVEL=INFO
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - ./logs:/app/logs
```

Build and run:

```bash
# Build image
docker build -t jmagent:1.0 .

# Or use Docker Compose
docker-compose up -d

# Check status
docker ps
docker logs jmagent-api

# Stop
docker-compose down
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api_integration_workflows.py -v

# Run with coverage
pytest tests/ --cov=src/api --cov-report=html

# Run API tests only
pytest tests/test_api_*.py -v
```

### Integration Tests

```bash
# Run integration test suite
pytest tests/test_api_integration_workflows.py -v

# Run specific integration test
pytest tests/test_api_integration_workflows.py::TestGenerateCodeToMetricsWorkflow -v
```

### Manual Testing

```bash
# Start server
uvicorn src.api.main:app --reload

# In another terminal, run smoke tests
TOKEN=$(curl -X POST http://localhost:8000/auth/token -d "user=test")

# Test endpoints
curl http://localhost:8000/api/v1/health
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/health/detailed
curl -X POST http://localhost:8000/api/v1/actions/generate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt": "test"}' \
  -H "Content-Type: application/json"
```

## Troubleshooting

### API Won't Start

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check dependencies
pip list | grep -E "fastapi|uvicorn|boto3"

# Check for port conflicts
lsof -i :8000  # Should be empty

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Authentication Errors

```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify JWT secret is set
echo $JMAGENT_API_JWT_SECRET_KEY

# Test token generation
python3 -c "from src.api.security.auth import create_token; print(create_token('test', 'test'))"
```

### Slow Responses

```bash
# Check Bedrock API connectivity
curl https://bedrock.us-east-1.amazonaws.com/

# Monitor logs
tail -f logs/jmagent.log

# Check system resources
top  # Monitor CPU/memory
df -h  # Check disk space
```

### Rate Limiting Issues

```bash
# Check rate limit configuration
curl -I http://localhost:8000/api/v1/health

# Look for X-RateLimit headers in response
# If being rate-limited:
# 1. Increase JMAGENT_API_RATE_LIMIT_PER_MINUTE
# 2. Wait for limit window to reset
# 3. Use exponential backoff in client code
```

### Database Errors

```bash
# Verify audit database
ls -la audit.db

# Check database integrity
sqlite3 audit.db ".tables"

# Recreate if corrupted
rm audit.db
# Restart API to recreate
```

## Monitoring

### Health Checks

```bash
# Simple health check
curl http://localhost:8000/api/v1/health

# Detailed health check
curl http://localhost:8000/api/v1/health/detailed

# In monitoring tool (every 30 seconds)
* * * * * curl -f http://localhost:8000/api/v1/health || alert
```

### Metrics

```bash
# Get metrics summary
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/metrics/summary

# Monitor in real-time
watch -n 5 'curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/metrics/summary | jq .'
```

### Logs

```bash
# View API logs
tail -f logs/jmagent.log

# Filter by level
grep ERROR logs/jmagent.log
grep WARNING logs/jmagent.log

# Analyze logs
grep "duration_ms" logs/jmagent.log | awk '{sum+=$NF; count++} END {print "Avg:", sum/count}'
```

### Uptime Monitoring

```bash
# Using systemd
systemctl status jmagent-api

# Using docker
docker stats jmagent-api

# Custom monitoring script
#!/bin/bash
while true; do
  status=$(curl -s http://localhost:8000/api/v1/health | jq -r '.success')
  if [ "$status" != "true" ]; then
    echo "API is down!" | mail -s "jmAgent Alert" admin@example.com
  fi
  sleep 300  # Check every 5 minutes
done
```

## Next Steps

1. **Set up SSL/TLS**: Use Let's Encrypt for free certificates
2. **Configure backups**: Back up audit logs and configurations
3. **Set up monitoring**: Use Prometheus, DataDog, or similar
4. **Plan for scaling**: Use load balancers if needed
5. **Document procedures**: Create runbooks for common operations
6. **Plan updates**: Test updates in staging before production

## Support

For issues and questions:

1. Check logs: `tail -f logs/jmagent.log`
2. Review API docs: `http://localhost:8000/api/docs`
3. Test endpoints: Use curl or Postman
4. Contact support: See project README for contact info
