import os
import json
import boto3
from src.utils.logger import get_logger
from src.errors.exceptions import (
    BedrockAPIError,
    RateLimitError,
    ModelError,
    AuthenticationError,
    ConfigurationError,
)
from src.resilience.retry import retry_with_backoff

logger = get_logger(__name__)


def detect_auth_mode() -> str:
    """
    Detect authentication mode: 'api_key' or 'iam'.

    Returns:
        'api_key' if AWS_BEARER_TOKEN_BEDROCK is set or ACCESS_KEY starts with 'ABSK'
        'iam' otherwise
    """
    bearer = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "").strip()
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()

    if bearer or (access_key and access_key.upper().startswith("ABSK")):
        return "api_key"

    return "iam"


def build_bedrock_runtime(region: str = "us-east-1"):
    """
    Build Bedrock runtime client with flexible authentication.

    Args:
        region: AWS region (default: us-east-1)

    Returns:
        boto3 bedrock-runtime client

    Raises:
        ConfigurationError: If authentication credentials are not configured
        AuthenticationError: If authentication setup fails
    """
    auth_mode = detect_auth_mode()

    try:
        if auth_mode == "api_key":
            bearer = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "").strip()
            if bearer:
                os.environ["AWS_BEARER_TOKEN_BEDROCK"] = bearer
                logger.info("Using API Key authentication (ABSK)")
            else:
                logger.info("Using API Key authentication (ABSK from ACCESS_KEY)")

            return boto3.client("bedrock-runtime", region_name=region)

        else:
            # IAM authentication
            access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
            secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()

            if not access_key or not secret_key:
                logger.error("Missing IAM credentials")
                raise ConfigurationError(
                    "IAM authentication requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
                )

            logger.info("Using IAM authentication")
            return boto3.client(
                "bedrock-runtime",
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
    except ConfigurationError:
        raise
    except Exception as e:
        logger.error(f"Failed to build Bedrock client: {str(e)}")
        raise AuthenticationError(f"Failed to initialize Bedrock client: {str(e)}")


@retry_with_backoff(max_attempts=3, initial_delay=1.0, max_delay=10.0)
def invoke_bedrock(client, model_id: str, body: dict, use_cache: bool = False) -> dict:
    """
    Invoke Bedrock model with request body and automatic retry on failure.

    Args:
        client: boto3 bedrock-runtime client
        model_id: Bedrock model ID
        body: Request body (dict with Bedrock format)
        use_cache: Whether cache support is enabled (for tracking)

    Returns:
        dict with 'content', 'stop_reason', and 'usage'
        usage includes 'cache_creation_input_tokens' and 'cache_read_input_tokens' if caching

    Raises:
        RateLimitError: If API rate limit exceeded (retry_after included)
        ModelError: If model not found or invalid
        BedrockAPIError: For other API failures
    """
    try:
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )

        response_body = json.loads(response["body"].read())

        usage = response_body["usage"]

        # Track cache metrics if available
        if use_cache:
            usage.setdefault("cache_creation_input_tokens", 0)
            usage.setdefault("cache_read_input_tokens", 0)

        logger.info(
            "Bedrock call successful",
            extra={
                "model": model_id,
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
        )

        return {
            "content": response_body["content"][0]["text"],
            "stop_reason": response_body.get("stop_reason", "end_turn"),
            "usage": usage,
        }

    except Exception as e:
        error_str = str(e).lower()

        # Rate limit errors
        if "throttling" in error_str or "too many requests" in error_str:
            logger.warning(
                "Rate limited on Bedrock API",
                extra={"model": model_id, "error": str(e)},
            )
            raise RateLimitError(str(e), retry_after=60)

        # Model not found or invalid
        elif "model" in error_str and ("not found" in error_str or "invalid" in error_str):
            logger.error(
                "Invalid or missing model",
                extra={"model": model_id, "error": str(e)},
            )
            raise ModelError(f"Model {model_id} not found or invalid: {str(e)}")

        # Generic Bedrock API error
        else:
            logger.error(
                "Bedrock API error",
                extra={"model": model_id, "error": str(e)},
            )
            raise BedrockAPIError(f"Bedrock API failed: {str(e)}")


@retry_with_backoff(max_attempts=3, initial_delay=1.0, max_delay=10.0)
def invoke_bedrock_streaming(client, model_id: str, body: dict):
    """
    Invoke Bedrock model with streaming response and automatic retry on failure.

    Args:
        client: boto3 bedrock-runtime client
        model_id: Bedrock model ID
        body: Request body (dict with Bedrock format)

    Yields:
        Parsed event dictionaries from the streaming response

    Raises:
        RateLimitError: If API rate limit exceeded (retry_after included)
        ModelError: If model not found or invalid
        BedrockAPIError: For other API failures
    """
    try:
        response = client.invoke_model_with_response_stream(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )

        # Stream events from response body
        for event_wrapper in response.get("body", []):
            try:
                # Extract the byte data from the event
                chunk_bytes = event_wrapper.get("chunk", {}).get("bytes", "")
                if chunk_bytes:
                    # Parse the JSON event
                    event = json.loads(chunk_bytes)
                    yield event
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                logger.debug(f"Skipping unparseable event: {str(e)}")
                continue

        logger.info("Bedrock streaming call completed", extra={"model": model_id})

    except Exception as e:
        error_str = str(e).lower()

        # Rate limit errors
        if "throttling" in error_str or "too many requests" in error_str:
            logger.warning(
                "Rate limited on Bedrock streaming",
                extra={"model": model_id, "error": str(e)},
            )
            raise RateLimitError(str(e), retry_after=60)

        # Model not found or invalid
        elif "model" in error_str and ("not found" in error_str or "invalid" in error_str):
            logger.error(
                "Invalid or missing model for streaming",
                extra={"model": model_id, "error": str(e)},
            )
            raise ModelError(f"Model {model_id} not found or invalid: {str(e)}")

        # Generic Bedrock API error
        else:
            logger.error(
                "Bedrock streaming API error",
                extra={"model": model_id, "error": str(e)},
            )
            raise BedrockAPIError(f"Bedrock streaming API failed: {str(e)}")
