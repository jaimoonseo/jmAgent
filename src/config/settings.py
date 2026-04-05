"""Pydantic-based configuration settings for jmAgent."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from dotenv import load_dotenv
import os
from src.errors.exceptions import ConfigurationError


class Settings(BaseModel):
    """
    Configuration settings for jmAgent with Pydantic validation.

    All settings support environment variables with JMAGENT_ prefix.
    Example: JMAGENT_DEFAULT_MODEL=sonnet

    Note: Use Settings() or Settings.from_env() to automatically read environment
    variables. Use Settings(field=value) to override specific fields.
    """

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    # jmAgent Core Settings
    jm_default_model: str = Field(
        default="haiku",
        description="Default LLM model (haiku, sonnet, or opus)"
    )
    jm_temperature: float = Field(
        default=0.2,
        description="Sampling temperature for model (0.0-1.0)"
    )
    jm_max_tokens: int = Field(
        default=4096,
        description="Maximum output tokens"
    )
    aws_bedrock_region: str = Field(
        default="us-east-1",
        description="AWS Bedrock region"
    )
    jm_project_root: Optional[str] = Field(
        default=None,
        description="Project root directory for context analysis"
    )

    # AWS Credentials (optional, for IAM or API Key auth)
    aws_bearer_token_bedrock: Optional[str] = Field(
        default=None,
        description="AWS Bedrock API Key (ABSK)"
    )
    aws_access_key_id: Optional[str] = Field(
        default=None,
        description="AWS Access Key ID"
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        description="AWS Secret Access Key"
    )

    # Phase 3 Advanced Features
    jm_enable_caching: bool = Field(
        default=True,
        description="Enable prompt caching"
    )
    jm_cache_ttl: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    jm_enable_streaming: bool = Field(
        default=False,
        description="Enable streaming responses"
    )

    @classmethod
    def from_env(cls, **overrides) -> "Settings":
        """
        Create Settings from environment variables.

        Reads all JMAGENT_ prefixed environment variables.
        Provided overrides take precedence.

        Args:
            **overrides: Explicit field values to override environment variables

        Returns:
            Settings instance with values from environment and overrides
        """
        env_dict = {}

        field_specs = {
            "jm_default_model": str,
            "jm_temperature": float,
            "jm_max_tokens": int,
            "aws_bedrock_region": str,
            "jm_project_root": str,
            "aws_bearer_token_bedrock": str,
            "aws_access_key_id": str,
            "aws_secret_access_key": str,
            "jm_enable_caching": bool,
            "jm_cache_ttl": int,
            "jm_enable_streaming": bool,
        }

        for field_name, field_type in field_specs.items():
            if field_name in overrides:
                # Overrides take precedence
                env_dict[field_name] = overrides[field_name]
            else:
                # Try multiple env var name formats for AWS fields
                if field_name.startswith("aws_"):
                    # Try both "JMAGENT_AWS_*" and "JMAGENT_*" formats
                    env_var1 = f"JMAGENT_{field_name.upper()}"  # JMAGENT_AWS_BEDROCK_REGION
                    env_var2 = f"JMAGENT_{field_name[4:].upper()}"  # JMAGENT_BEDROCK_REGION
                    env_value = os.getenv(env_var1) or os.getenv(env_var2)
                else:
                    # For jm_ fields, construct normally
                    if field_name.startswith("jm_"):
                        env_suffix = field_name[3:].upper()  # Remove "jm_"
                    else:
                        env_suffix = field_name.upper()
                    env_var = f"JMAGENT_{env_suffix}"
                    env_value = os.getenv(env_var)

                if env_value is not None:
                    if field_type is bool:
                        env_dict[field_name] = env_value.lower() in {
                            "true", "1", "yes", "on"
                        }
                    elif field_type is int:
                        try:
                            env_dict[field_name] = int(env_value)
                        except ValueError:
                            raise ValueError(f"Invalid integer value for {field_name}: '{env_value}'")
                    elif field_type is float:
                        try:
                            env_dict[field_name] = float(env_value)
                        except ValueError:
                            raise ValueError(f"Invalid float value for {field_name}: '{env_value}'")
                    else:
                        env_dict[field_name] = env_value

        return cls(**env_dict)


    @field_validator("jm_default_model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate that model is one of the supported options."""
        valid_models = {"haiku", "sonnet", "opus"}
        if v not in valid_models:
            raise ValueError(
                f"jm_default_model must be one of {valid_models}, got '{v}'"
            )
        return v

    @field_validator("jm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range [0.0, 1.0]."""
        if isinstance(v, str):
            v = float(v)
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                f"jm_temperature must be between 0.0 and 1.0, got {v}"
            )
        return v

    @field_validator("jm_max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max_tokens is positive."""
        if isinstance(v, str):
            v = int(v)
        if v <= 0:
            raise ValueError(
                f"jm_max_tokens must be positive, got {v}"
            )
        return v

    @field_validator("aws_bedrock_region")
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate AWS region format."""
        # Basic validation for common region patterns
        valid_regions = {
            # US regions
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            # EU regions
            "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
            "eu-north-1",
            # Asia Pacific regions
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
            "ap-northeast-2", "ap-south-1",
            # Canada
            "ca-central-1",
            # South America
            "sa-east-1",
        }
        if v not in valid_regions:
            raise ValueError(
                f"aws_bedrock_region '{v}' is not a valid AWS region. "
                f"Valid regions: {sorted(valid_regions)}"
            )
        return v

    @field_validator("jm_project_root")
    @classmethod
    def validate_project_root(cls, v: Optional[str]) -> Optional[str]:
        """Validate that project root path exists if provided."""
        if v is None:
            return v

        path = Path(v)
        if not path.exists():
            raise ValueError(
                f"jm_project_root '{v}' does not exist"
            )
        if not path.is_dir():
            raise ValueError(
                f"jm_project_root '{v}' is not a directory"
            )
        return v

    @field_validator("jm_cache_ttl")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache_ttl is positive."""
        if isinstance(v, str):
            v = int(v)
        if v <= 0:
            raise ValueError(
                f"jm_cache_ttl must be positive, got {v}"
            )
        return v

    @classmethod
    def from_env_file(
        cls,
        env_file: Optional[Path | str] = None
    ) -> "Settings":
        """
        Load settings from a .env file.

        Args:
            env_file: Path to .env file. If None, uses '.env' in current directory.

        Returns:
            Settings instance loaded from .env file.

        Raises:
            ConfigurationError: If the .env file doesn't exist.
        """
        if env_file is None:
            env_file = Path(".env")
        else:
            env_file = Path(env_file)

        if not env_file.exists():
            raise ConfigurationError(
                f"Environment file not found: {env_file}"
            )

        # Load environment variables from file
        load_dotenv(env_file)

        # Return settings initialized from now-loaded environment
        return cls.from_env()

    def model_dump(self) -> dict:
        """
        Convert settings to dictionary.

        Returns:
            Dictionary representation of settings.
        """
        return {
            "jm_default_model": self.jm_default_model,
            "jm_temperature": self.jm_temperature,
            "jm_max_tokens": self.jm_max_tokens,
            "aws_bedrock_region": self.aws_bedrock_region,
            "jm_project_root": self.jm_project_root,
            "aws_bearer_token_bedrock": self.aws_bearer_token_bedrock,
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "jm_enable_caching": self.jm_enable_caching,
            "jm_cache_ttl": self.jm_cache_ttl,
            "jm_enable_streaming": self.jm_enable_streaming,
        }
