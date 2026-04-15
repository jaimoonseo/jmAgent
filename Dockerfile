FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir \
    boto3 \
    python-dotenv \
    pydantic \
    pydantic-settings \
    PyYAML \
    fastapi \
    uvicorn \
    python-multipart \
    httpx \
    PyGithub \
    PyJWT \
    Jinja2

# Copy source
COPY src/ ./src/
COPY setup.py .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2"]
