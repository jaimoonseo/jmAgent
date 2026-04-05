"""Comprehensive tests for configuration management system."""

import os
import pytest
import tempfile
from pathlib import Path
from src.config.settings import Settings
from src.errors.exceptions import ConfigurationError


@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Clean up JMAGENT environment variables before each test."""
    # Store original env vars
    original_env = {}
    jmagent_keys = [k for k in os.environ if k.startswith("JMAGENT_")]
    for key in jmagent_keys:
        original_env[key] = os.environ.pop(key)

    yield

    # Restore original env vars
    for key in list(os.environ.keys()):
        if key.startswith("JMAGENT_"):
            del os.environ[key]
    for key, value in original_env.items():
        os.environ[key] = value


class TestSettingsBasics:
    """Test basic settings initialization and defaults."""

    def test_settings_init_with_defaults(self):
        """Test Settings initialization with default values."""
        settings = Settings()
        assert settings.jm_default_model == "haiku"
        assert settings.jm_temperature == 0.2
        assert settings.jm_max_tokens == 4096
        assert settings.aws_bedrock_region == "us-east-1"
        assert settings.jm_project_root is None

    def test_settings_init_with_env_vars(self, monkeypatch):
        """Test Settings initialization from environment variables."""
        monkeypatch.setenv("JMAGENT_DEFAULT_MODEL", "sonnet")
        monkeypatch.setenv("JMAGENT_TEMPERATURE", "0.5")
        monkeypatch.setenv("JMAGENT_MAX_TOKENS", "2048")
        monkeypatch.setenv("JMAGENT_AWS_BEDROCK_REGION", "eu-west-1")

        settings = Settings.from_env()
        assert settings.jm_default_model == "sonnet"
        assert settings.jm_temperature == 0.5
        assert settings.jm_max_tokens == 2048
        assert settings.aws_bedrock_region == "eu-west-1"

    def test_settings_init_with_explicit_values(self):
        """Test Settings initialization with explicit keyword arguments."""
        settings = Settings(
            jm_default_model="opus",
            jm_temperature=0.8,
            jm_max_tokens=8192,
            aws_bedrock_region="ap-southeast-1"
        )
        assert settings.jm_default_model == "opus"
        assert settings.jm_temperature == 0.8
        assert settings.jm_max_tokens == 8192
        assert settings.aws_bedrock_region == "ap-southeast-1"

    def test_settings_env_vars_override_defaults(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("JMAGENT_TEMPERATURE", "0.9")
        settings = Settings.from_env()
        assert settings.jm_temperature == 0.9


class TestSettingsValidation:
    """Test settings validation."""

    def test_temperature_valid_bounds(self):
        """Test that temperature values within bounds are valid."""
        # Test lower bound
        settings = Settings(jm_temperature=0.0)
        assert settings.jm_temperature == 0.0

        # Test upper bound
        settings = Settings(jm_temperature=1.0)
        assert settings.jm_temperature == 1.0

        # Test middle value
        settings = Settings(jm_temperature=0.5)
        assert settings.jm_temperature == 0.5

    def test_temperature_validation_below_zero(self):
        """Test that temperature below 0.0 raises validation error."""
        with pytest.raises(ValueError):
            Settings(jm_temperature=-0.1)

    def test_temperature_validation_above_one(self):
        """Test that temperature above 1.0 raises validation error."""
        with pytest.raises(ValueError):
            Settings(jm_temperature=1.1)

    def test_max_tokens_positive(self):
        """Test that max_tokens must be positive."""
        with pytest.raises(ValueError):
            Settings(jm_max_tokens=0)

        with pytest.raises(ValueError):
            Settings(jm_max_tokens=-100)

    def test_max_tokens_valid_positive(self):
        """Test that positive max_tokens values are valid."""
        settings = Settings(jm_max_tokens=1)
        assert settings.jm_max_tokens == 1

        settings = Settings(jm_max_tokens=10000)
        assert settings.jm_max_tokens == 10000

    def test_model_validation_valid_models(self):
        """Test that valid model names are accepted."""
        for model in ["haiku", "sonnet", "opus"]:
            settings = Settings(jm_default_model=model)
            assert settings.jm_default_model == model

    def test_model_validation_invalid_model(self):
        """Test that invalid model names raise validation error."""
        with pytest.raises(ValueError):
            Settings(jm_default_model="invalid_model")

    def test_aws_region_validation_valid(self):
        """Test that valid AWS regions are accepted."""
        valid_regions = ["us-east-1", "eu-west-1", "ap-southeast-1"]
        for region in valid_regions:
            settings = Settings(aws_bedrock_region=region)
            assert settings.aws_bedrock_region == region

    def test_aws_region_validation_invalid(self):
        """Test that invalid AWS regions raise validation error."""
        with pytest.raises(ValueError):
            Settings(aws_bedrock_region="invalid-region")

    def test_project_root_validation_nonexistent(self):
        """Test that non-existent project root paths raise validation error."""
        with pytest.raises(ValueError):
            Settings(jm_project_root="/nonexistent/path/that/does/not/exist")

    def test_project_root_validation_valid_path(self):
        """Test that valid project root paths are accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Settings(jm_project_root=tmpdir)
            assert settings.jm_project_root == tmpdir

    def test_project_root_optional(self):
        """Test that project root is optional."""
        settings = Settings.from_env()
        assert settings.jm_project_root is None


class TestPhase3Settings:
    """Test Phase 3 advanced features settings."""

    def test_caching_enabled_by_default(self):
        """Test that caching is enabled by default."""
        settings = Settings()
        assert settings.jm_enable_caching is True

    def test_caching_can_be_disabled(self, monkeypatch):
        """Test that caching can be disabled."""
        monkeypatch.setenv("JMAGENT_ENABLE_CACHING", "false")
        settings = Settings.from_env()
        assert settings.jm_enable_caching is False

    def test_cache_ttl_default(self):
        """Test default cache TTL."""
        settings = Settings.from_env()
        assert settings.jm_cache_ttl == 3600

    def test_cache_ttl_from_env(self, monkeypatch):
        """Test cache TTL from environment variable."""
        monkeypatch.setenv("JMAGENT_CACHE_TTL", "7200")
        settings = Settings.from_env()
        assert settings.jm_cache_ttl == 7200

    def test_cache_ttl_positive(self):
        """Test that cache TTL must be positive."""
        with pytest.raises(ValueError):
            Settings(jm_cache_ttl=0)

        with pytest.raises(ValueError):
            Settings(jm_cache_ttl=-100)

    def test_streaming_disabled_by_default(self):
        """Test that streaming is disabled by default."""
        settings = Settings.from_env()
        assert settings.jm_enable_streaming is False

    def test_streaming_can_be_enabled(self, monkeypatch):
        """Test that streaming can be enabled."""
        monkeypatch.setenv("JMAGENT_ENABLE_STREAMING", "true")
        settings = Settings.from_env()
        assert settings.jm_enable_streaming is True


class TestAWSSettings:
    """Test AWS credential settings."""

    def test_aws_bearer_token_optional(self):
        """Test that AWS bearer token is optional."""
        settings = Settings.from_env()
        assert settings.aws_bearer_token_bedrock is None

    def test_aws_bearer_token_from_env(self, monkeypatch):
        """Test AWS bearer token from environment variable."""
        token = "ABSK-test-token-12345"
        monkeypatch.setenv("JMAGENT_AWS_BEARER_TOKEN_BEDROCK", token)
        settings = Settings.from_env()
        assert settings.aws_bearer_token_bedrock == token

    def test_aws_access_key_optional(self):
        """Test that AWS access key ID is optional."""
        settings = Settings.from_env()
        assert settings.aws_access_key_id is None

    def test_aws_access_key_from_env(self, monkeypatch):
        """Test AWS access key ID from environment variable."""
        key = "AKIAIOSFODNN7EXAMPLE"
        monkeypatch.setenv("JMAGENT_AWS_ACCESS_KEY_ID", key)
        settings = Settings.from_env()
        assert settings.aws_access_key_id == key

    def test_aws_secret_key_optional(self):
        """Test that AWS secret access key is optional."""
        settings = Settings.from_env()
        assert settings.aws_secret_access_key is None

    def test_aws_secret_key_from_env(self, monkeypatch):
        """Test AWS secret access key from environment variable."""
        secret = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        monkeypatch.setenv("JMAGENT_AWS_SECRET_ACCESS_KEY", secret)
        settings = Settings.from_env()
        assert settings.aws_secret_access_key == secret


class TestEnvFileLoading:
    """Test loading settings from .env files."""

    def test_load_from_env_file(self, monkeypatch):
        """Test loading settings from a .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "JMAGENT_DEFAULT_MODEL=sonnet\n"
                "JMAGENT_TEMPERATURE=0.7\n"
                "JMAGENT_MAX_TOKENS=8192\n"
            )

            # Change to tmpdir to use relative .env
            monkeypatch.chdir(tmpdir)
            settings = Settings.from_env_file(env_file)

            assert settings.jm_default_model == "sonnet"
            assert settings.jm_temperature == 0.7
            assert settings.jm_max_tokens == 8192

    def test_load_from_env_file_defaults(self, monkeypatch):
        """Test that unspecified settings use defaults when loading from .env."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("JMAGENT_DEFAULT_MODEL=opus\n")

            monkeypatch.chdir(tmpdir)
            settings = Settings.from_env_file(env_file)

            assert settings.jm_default_model == "opus"
            assert settings.jm_temperature == 0.2  # Default
            assert settings.jm_max_tokens == 4096  # Default

    def test_load_from_env_file_nonexistent(self):
        """Test that loading from non-existent .env file raises error."""
        with pytest.raises(ConfigurationError):
            Settings.from_env_file("/nonexistent/.env")

    def test_load_from_default_env_file(self, monkeypatch):
        """Test loading from default .env file in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("JMAGENT_TEMPERATURE=0.3\n")

            monkeypatch.chdir(tmpdir)
            settings = Settings.from_env_file()

            assert settings.jm_temperature == 0.3


class TestSettingsIntegration:
    """Integration tests for settings system."""

    def test_settings_with_all_fields(self):
        """Test Settings with all fields specified."""
        settings = Settings(
            jm_default_model="opus",
            jm_temperature=0.6,
            jm_max_tokens=8192,
            aws_bedrock_region="eu-west-1",
            jm_project_root=None,
            aws_bearer_token_bedrock="ABSK-token",
            aws_access_key_id="AKIA123",
            aws_secret_access_key="secret",
            jm_enable_caching=False,
            jm_cache_ttl=7200,
            jm_enable_streaming=True,
        )

        assert settings.jm_default_model == "opus"
        assert settings.jm_temperature == 0.6
        assert settings.jm_max_tokens == 8192
        assert settings.aws_bedrock_region == "eu-west-1"
        assert settings.aws_bearer_token_bedrock == "ABSK-token"
        assert settings.aws_access_key_id == "AKIA123"
        assert settings.aws_secret_access_key == "secret"
        assert settings.jm_enable_caching is False
        assert settings.jm_cache_ttl == 7200
        assert settings.jm_enable_streaming is True

    def test_settings_to_dict(self):
        """Test converting settings to dictionary."""
        settings = Settings(jm_default_model="sonnet")
        settings_dict = settings.model_dump()

        assert settings_dict["jm_default_model"] == "sonnet"
        assert settings_dict["jm_temperature"] == 0.2
        assert "aws_bedrock_region" in settings_dict

    def test_settings_equality(self):
        """Test settings equality."""
        settings1 = Settings(jm_default_model="sonnet")
        settings2 = Settings(jm_default_model="sonnet")

        # Settings with same values should have same values
        assert settings1.jm_default_model == settings2.jm_default_model

    def test_settings_immutability(self):
        """Test that settings are frozen/immutable."""
        settings = Settings.from_env()

        with pytest.raises(Exception):  # Pydantic freezes raise Exception
            settings.jm_default_model = "sonnet"


class TestSettingsEnvVariablePrefix:
    """Test environment variable prefix handling."""

    def test_jmagent_prefix_conversion(self, monkeypatch):
        """Test that JMAGENT_ prefix is properly handled."""
        monkeypatch.setenv("JMAGENT_DEFAULT_MODEL", "sonnet")
        monkeypatch.setenv("JMAGENT_TEMPERATURE", "0.4")
        settings = Settings.from_env()
        assert settings.jm_default_model == "sonnet"
        assert settings.jm_temperature == 0.4

    def test_env_var_case_insensitive(self, monkeypatch):
        """Test that environment variables are case-insensitive."""
        # Note: Pydantic uses uppercase by default for env vars
        monkeypatch.setenv("JMAGENT_DEFAULT_MODEL", "opus")
        settings = Settings.from_env()
        assert settings.jm_default_model == "opus"


class TestSettingsErrorMessages:
    """Test error messages for invalid settings."""

    def test_validation_error_temperature(self):
        """Test validation error message for invalid temperature."""
        with pytest.raises(ValueError) as exc_info:
            Settings(jm_temperature=1.5)
        assert "temperature" in str(exc_info.value).lower()

    def test_validation_error_model(self):
        """Test validation error message for invalid model."""
        with pytest.raises(ValueError) as exc_info:
            Settings(jm_default_model="gpt4")
        assert "model" in str(exc_info.value).lower()

    def test_validation_error_region(self):
        """Test validation error message for invalid region."""
        with pytest.raises(ValueError) as exc_info:
            Settings(aws_bedrock_region="invalid")
        assert "region" in str(exc_info.value).lower()


class TestSettingsDocumentation:
    """Test that settings have proper documentation."""

    def test_settings_has_docstring(self):
        """Test that Settings class has a docstring."""
        assert Settings.__doc__ is not None
        assert len(Settings.__doc__) > 0

    def test_settings_field_descriptions(self):
        """Test that settings fields have descriptions."""
        # Check if Pydantic model has field info
        assert hasattr(Settings, "model_fields")
        fields = Settings.model_fields
        assert len(fields) > 0


class TestBooleanEnvVarParsing:
    """Test parsing of boolean environment variables."""

    def test_parse_true_variants(self, monkeypatch):
        """Test parsing various true variants."""
        for true_val in ["true", "True", "TRUE", "1", "yes"]:
            monkeypatch.setenv("JMAGENT_ENABLE_CACHING", true_val)
            settings = Settings.from_env()
            assert settings.jm_enable_caching is True

    def test_parse_false_variants(self, monkeypatch):
        """Test parsing various false variants."""
        for false_val in ["false", "False", "FALSE", "0", "no"]:
            monkeypatch.setenv("JMAGENT_ENABLE_CACHING", false_val)
            settings = Settings.from_env()
            assert settings.jm_enable_caching is False


class TestIntegerEnvVarParsing:
    """Test parsing of integer environment variables."""

    def test_parse_max_tokens_from_env(self, monkeypatch):
        """Test parsing max_tokens as integer."""
        monkeypatch.setenv("JMAGENT_MAX_TOKENS", "8192")
        settings = Settings.from_env()
        assert settings.jm_max_tokens == 8192
        assert isinstance(settings.jm_max_tokens, int)

    def test_parse_cache_ttl_from_env(self, monkeypatch):
        """Test parsing cache_ttl as integer."""
        monkeypatch.setenv("JMAGENT_CACHE_TTL", "7200")
        settings = Settings.from_env()
        assert settings.jm_cache_ttl == 7200
        assert isinstance(settings.jm_cache_ttl, int)

    def test_invalid_integer_raises(self, monkeypatch):
        """Test that invalid integers raise error."""
        monkeypatch.setenv("JMAGENT_MAX_TOKENS", "not_a_number")
        with pytest.raises(ValueError):
            Settings.from_env()


class TestFloatEnvVarParsing:
    """Test parsing of float environment variables."""

    def test_parse_temperature_from_env(self, monkeypatch):
        """Test parsing temperature as float."""
        monkeypatch.setenv("JMAGENT_TEMPERATURE", "0.75")
        settings = Settings.from_env()
        assert settings.jm_temperature == 0.75
        assert isinstance(settings.jm_temperature, float)

    def test_invalid_float_raises(self, monkeypatch):
        """Test that invalid floats raise error."""
        monkeypatch.setenv("JMAGENT_TEMPERATURE", "invalid")
        with pytest.raises(ValueError):
            Settings.from_env()
