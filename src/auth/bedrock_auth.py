import os
import json
import boto3
from src.utils.logger import get_logger

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
        ValueError: If authentication credentials are not configured
    """
    auth_mode = detect_auth_mode()

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
            raise ValueError(
                "IAM authentication requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
            )

        logger.info("Using IAM authentication")
        return boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )


def invoke_bedrock(client, model_id: str, body: dict, use_cache: bool = False) -> dict:
    """
    Invoke Bedrock model with request body.

    Args:
        client: boto3 bedrock-runtime client
        model_id: Bedrock model ID
        body: Request body (dict with Bedrock format)
        use_cache: Whether cache support is enabled (for tracking)

    Returns:
        dict with 'content', 'stop_reason', and 'usage'
        usage includes 'cache_creation_input_tokens' and 'cache_read_input_tokens' if caching

    Raises:
        Exception: If API call fails
    """
    try:
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )

        response_body = json.loads(response["body"].read())

        usage = response_body["usage"]

        # Track cache metrics if available
        if use_cache:
            usage.setdefault("cache_creation_input_tokens", 0)
            usage.setdefault("cache_read_input_tokens", 0)

        return {
            "content": response_body["content"][0]["text"],
            "stop_reason": response_body["stop_reason"],
            "usage": usage
        }

    except Exception as e:
        logger.error(f"Bedrock API call failed: {str(e)}")
        raise


def invoke_bedrock_streaming(client, model_id: str, body: dict):
    """
    Invoke Bedrock model with streaming response.

    Args:
        client: boto3 bedrock-runtime client
        model_id: Bedrock model ID
        body: Request body (dict with Bedrock format)

    Yields:
        Parsed event dictionaries from the streaming response

    Raises:
        Exception: If API call fails
    """
    try:
        response = client.invoke_model_with_response_stream(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
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

    except Exception as e:
        logger.error(f"Bedrock streaming call failed: {str(e)}")
        raise
