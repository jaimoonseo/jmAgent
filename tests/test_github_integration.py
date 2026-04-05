"""Comprehensive tests for GitHub integration."""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from src.integrations.base import BaseIntegration
from src.integrations.github import GitHubClient, GitHubContext
from src.errors.exceptions import JmAgentError, AuthenticationError


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client instance."""
    with patch("src.integrations.github.Github") as mock_github_class:
        mock_instance = MagicMock()
        mock_user = MagicMock()
        mock_user.login = "testuser"
        mock_instance.get_user.return_value = mock_user
        mock_github_class.return_value = mock_instance
        yield mock_github_class, mock_instance


def create_github_mock():
    """Helper to create a properly configured Github mock."""
    mock_github_class = MagicMock()
    mock_instance = MagicMock()
    mock_user = MagicMock()
    mock_user.login = "testuser"
    mock_instance.get_user.return_value = mock_user
    mock_github_class.return_value = mock_instance
    return mock_github_class, mock_instance


class TestBaseIntegration:
    """Test BaseIntegration abstract base class."""

    def test_base_integration_cannot_instantiate(self):
        """Test that BaseIntegration cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseIntegration()

    def test_base_integration_subclass_requires_methods(self):
        """Test that subclasses must implement abstract methods."""
        class IncompleteIntegration(BaseIntegration):
            pass

        with pytest.raises(TypeError):
            IncompleteIntegration()

    def test_base_integration_subclass_with_all_methods(self):
        """Test that subclass with all abstract methods can be instantiated."""
        class CompleteIntegration(BaseIntegration):
            async def authenticate(self) -> None:
                pass

            def is_authenticated(self) -> bool:
                return True

            async def get_context(self) -> dict:
                return {}

            async def get_status(self) -> dict:
                return {"status": "ok"}

        integration = CompleteIntegration()
        assert integration is not None


class TestGitHubContext:
    """Test GitHubContext data class."""

    def test_github_context_initialization(self):
        """Test GitHubContext initialization with all fields."""
        context = GitHubContext(
            owner="owner",
            repo="repo",
            url="https://github.com/owner/repo",
            description="A test repo",
            language="Python",
            stars=100,
            watchers=50,
            forks=10,
            readme="# Test",
            file_tree=["file1.py", "file2.py"],
            key_files=["setup.py", "requirements.txt"]
        )

        assert context.owner == "owner"
        assert context.repo == "repo"
        assert context.url == "https://github.com/owner/repo"
        assert context.description == "A test repo"
        assert context.language == "Python"
        assert context.stars == 100
        assert context.watchers == 50
        assert context.forks == 10
        assert context.readme == "# Test"
        assert context.file_tree == ["file1.py", "file2.py"]
        assert context.key_files == ["setup.py", "requirements.txt"]

    def test_github_context_json_serialization(self):
        """Test GitHubContext serialization to JSON."""
        context = GitHubContext(
            owner="owner",
            repo="repo",
            url="https://github.com/owner/repo",
            description="A test repo",
            language="Python",
            stars=100,
            watchers=50,
            forks=10,
            readme="# Test",
            file_tree=["file1.py"],
            key_files=["setup.py"]
        )

        json_str = context.to_json()
        parsed = json.loads(json_str)

        assert parsed["owner"] == "owner"
        assert parsed["repo"] == "repo"
        assert parsed["stars"] == 100
        assert isinstance(parsed["file_tree"], list)

    def test_github_context_to_dict(self):
        """Test GitHubContext conversion to dict."""
        context = GitHubContext(
            owner="owner",
            repo="repo",
            url="https://github.com/owner/repo",
            description="A test repo",
            language="Python",
            stars=100,
            watchers=50,
            forks=10,
            readme="# Test",
            file_tree=["file1.py"],
            key_files=["setup.py"]
        )

        context_dict = context.to_dict()

        assert context_dict["owner"] == "owner"
        assert context_dict["repo"] == "repo"
        assert context_dict["stars"] == 100
        assert isinstance(context_dict, dict)


class TestGitHubClientAuthentication:
    """Test GitHub client authentication."""

    def test_github_client_initialization_with_token(self):
        """Test GitHub client initialization with token."""
        client = GitHubClient(token="test-token")
        assert client is not None

    def test_github_client_initialization_without_token_from_env(self):
        """Test GitHub client initialization without token uses environment."""
        with patch.dict("os.environ", {"GITHUB_TOKEN": "env-token"}):
            client = GitHubClient()
            assert client is not None

    @pytest.mark.asyncio
    async def test_github_client_authenticate_success(self):
        """Test successful authentication with GitHub."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance

            client = GitHubClient(token="test-token")
            await client.authenticate()

            assert client.is_authenticated() is True

    @pytest.mark.asyncio
    async def test_github_client_authenticate_failure(self):
        """Test authentication failure with invalid token."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_instance.get_user.side_effect = Exception("401 Bad credentials")
            mock_github_class.return_value = mock_instance

            client = GitHubClient(token="invalid-token")
            with pytest.raises(AuthenticationError):
                await client.authenticate()

    def test_github_client_no_token_raises_error(self):
        """Test that client initialization without token raises error."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuthenticationError):
                GitHubClient()

    def test_github_client_is_authenticated_before_auth(self):
        """Test is_authenticated returns False before authentication."""
        client = GitHubClient(token="test-token")
        assert client.is_authenticated() is False


class TestGitHubClientRepositoryOperations:
    """Test GitHub repository context loading."""

    @pytest.mark.asyncio
    async def test_get_repository_success(self):
        """Test successful repository retrieval."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user

            mock_repo = MagicMock()
            mock_repo.full_name = "owner/repo"
            mock_repo.description = "Test repo"
            mock_repo.language = "Python"
            mock_repo.stargazers_count = 100
            mock_repo.watchers_count = 50
            mock_repo.forks_count = 10
            mock_instance.get_repo.return_value = mock_repo

            mock_github_class.return_value = mock_instance

            client = GitHubClient(token="test-token")
            await client.authenticate()

            repo = client.get_repository("owner/repo")
            assert repo is not None

    @pytest.mark.asyncio
    async def test_get_repository_not_found(self):
        """Test repository not found."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_instance.get_repo.side_effect = Exception("Repository not found")
            mock_github_class.return_value = mock_instance

            client = GitHubClient(token="test-token")
            await client.authenticate()

            with pytest.raises(JmAgentError):
                client.get_repository("nonexistent/repo")

    @pytest.mark.asyncio
    async def test_get_readme_success(self):
        """Test successful README retrieval."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_readme = MagicMock()
            mock_readme.decoded_content = b"# Test README"

            mock_repo = MagicMock()
            mock_repo.get_readme.return_value = mock_readme

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            readme = client.get_readme("owner/repo")
            assert readme == "# Test README"

    @pytest.mark.asyncio
    async def test_get_readme_not_found(self):
        """Test README not found."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_repo = MagicMock()
            mock_repo.get_readme.side_effect = Exception("404 Not Found")

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            readme = client.get_readme("owner/repo")
            assert readme is None

    @pytest.mark.asyncio
    async def test_get_file_tree_success(self):
        """Test successful file tree retrieval."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_content1 = MagicMock()
            mock_content1.path = "file1.py"
            mock_content1.type = "file"

            mock_content2 = MagicMock()
            mock_content2.path = "dir"
            mock_content2.type = "dir"

            mock_repo = MagicMock()
            mock_repo.get_contents.return_value = [mock_content1, mock_content2]

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            tree = client.get_file_tree("owner/repo", max_depth=1)
            assert len(tree) > 0

    @pytest.mark.asyncio
    async def test_get_repository_info_success(self):
        """Test successful repository info retrieval."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_repo = MagicMock()
            mock_repo.full_name = "owner/repo"
            mock_repo.description = "Test repo"
            mock_repo.language = "Python"
            mock_repo.stargazers_count = 100
            mock_repo.watchers_count = 50
            mock_repo.forks_count = 10
            mock_repo.html_url = "https://github.com/owner/repo"

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            info = client.get_repository_info("owner/repo")
            assert info["stars"] == 100
            assert info["language"] == "Python"


class TestGitHubClientContextLoading:
    """Test GitHub context loading."""

    @pytest.mark.asyncio
    async def test_get_context_success(self):
        """Test successful context loading."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_repo = MagicMock()
            mock_repo.full_name = "owner/repo"
            mock_repo.description = "Test repo"
            mock_repo.language = "Python"
            mock_repo.stargazers_count = 100
            mock_repo.watchers_count = 50
            mock_repo.forks_count = 10
            mock_repo.html_url = "https://github.com/owner/repo"
            mock_repo.name = "repo"
            mock_repo.open_issues_count = 5
            mock_repo.created_at = datetime.now()
            mock_repo.updated_at = datetime.now()

            mock_readme = MagicMock()
            mock_readme.decoded_content = b"# Test README"
            mock_repo.get_readme.return_value = mock_readme

            mock_content = MagicMock()
            mock_content.path = "file.py"
            mock_content.type = "file"
            mock_repo.get_contents.return_value = [mock_content]

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            context_dict = await client.get_context(repo="owner/repo")
            assert "owner" in context_dict
            assert "repo" in context_dict
            assert "url" in context_dict

    @pytest.mark.asyncio
    async def test_get_context_returns_github_context(self):
        """Test get_context returns GitHubContext object."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_repo = MagicMock()
            mock_repo.full_name = "owner/repo"
            mock_repo.description = "Test repo"
            mock_repo.language = "Python"
            mock_repo.stargazers_count = 100
            mock_repo.watchers_count = 50
            mock_repo.forks_count = 10
            mock_repo.html_url = "https://github.com/owner/repo"
            mock_repo.name = "repo"
            mock_repo.open_issues_count = 5
            mock_repo.created_at = datetime.now()
            mock_repo.updated_at = datetime.now()

            mock_readme = MagicMock()
            mock_readme.decoded_content = b"# Test"
            mock_repo.get_readme.return_value = mock_readme

            mock_content = MagicMock()
            mock_content.path = "file.py"
            mock_content.type = "file"
            mock_repo.get_contents.return_value = [mock_content]

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            result = await client.get_context(repo="owner/repo")
            assert isinstance(result, dict)
            assert "owner" in result
            assert "file_tree" in result


class TestGitHubClientPullRequests:
    """Test GitHub pull request operations."""

    @pytest.mark.asyncio
    async def test_list_pull_requests_success(self):
        """Test successful pull request listing."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_pr = MagicMock()
            mock_pr.number = 123
            mock_pr.title = "Test PR"
            mock_pr.state = "open"
            mock_pr.created_at = datetime.now()
            mock_pr.updated_at = datetime.now()
            mock_pr.user = MagicMock(login="testuser")
            mock_pr.additions = 10
            mock_pr.deletions = 5
            mock_pr.changed_files = 3

            mock_repo = MagicMock()
            mock_repo.get_pulls.return_value = [mock_pr]

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            prs = client.list_pull_requests("owner/repo", state="open")
            assert len(prs) > 0
            assert prs[0]["number"] == 123

    @pytest.mark.asyncio
    async def test_list_pull_requests_with_filters(self):
        """Test pull request listing with filters."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_pr = MagicMock()
            mock_pr.number = 123
            mock_pr.title = "Test PR"
            mock_pr.state = "open"
            mock_pr.created_at = datetime.now()
            mock_pr.updated_at = datetime.now()
            mock_pr.user = MagicMock(login="testuser")
            mock_pr.additions = 10
            mock_pr.deletions = 5
            mock_pr.changed_files = 3

            mock_repo = MagicMock()
            mock_repo.get_pulls.return_value = [mock_pr]

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            prs = client.list_pull_requests("owner/repo", state="closed")
            mock_repo.get_pulls.assert_called()

    @pytest.mark.asyncio
    async def test_create_pull_request_success(self):
        """Test successful pull request creation."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_pr = MagicMock()
            mock_pr.number = 124
            mock_pr.title = "New PR"
            mock_pr.state = "open"
            mock_pr.html_url = "https://github.com/owner/repo/pull/124"

            mock_repo = MagicMock()
            mock_repo.create_pull.return_value = mock_pr

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            pr = client.create_pull_request(
                repo="owner/repo",
                title="New PR",
                body="Test PR body",
                head="feature-branch",
                base="main"
            )
            assert pr["number"] == 124

    @pytest.mark.asyncio
    async def test_update_pull_request_success(self):
        """Test successful pull request update."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_pr = MagicMock()
            mock_pr.number = 123
            mock_pr.title = "Updated PR"

            mock_repo = MagicMock()
            mock_repo.get_pull.return_value = mock_pr

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            pr = client.update_pull_request(
                repo="owner/repo",
                number=123,
                title="Updated PR"
            )
            assert pr["number"] == 123

    @pytest.mark.asyncio
    async def test_close_pull_request_success(self):
        """Test successful pull request closure."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_pr = MagicMock()
            mock_pr.number = 123
            mock_pr.state = "closed"

            mock_repo = MagicMock()
            mock_repo.get_pull.return_value = mock_pr

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            pr = client.close_pull_request("owner/repo", 123)
            mock_pr.edit.assert_called()


class TestGitHubClientIssues:
    """Test GitHub issue operations."""

    @pytest.mark.asyncio
    async def test_list_issues_success(self):
        """Test successful issue listing."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_issue = MagicMock()
            mock_issue.number = 456
            mock_issue.title = "Test Issue"
            mock_issue.state = "open"
            mock_issue.created_at = datetime.now()
            mock_issue.updated_at = datetime.now()
            mock_issue.user = MagicMock(login="testuser")
            mock_issue.labels = []

            mock_repo = MagicMock()
            mock_repo.get_issues.return_value = [mock_issue]

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            issues = client.list_issues("owner/repo", state="open")
            assert len(issues) > 0
            assert issues[0]["number"] == 456

    @pytest.mark.asyncio
    async def test_create_issue_success(self):
        """Test successful issue creation."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_issue = MagicMock()
            mock_issue.number = 457
            mock_issue.title = "New Issue"
            mock_issue.state = "open"
            mock_issue.html_url = "https://github.com/owner/repo/issues/457"

            mock_repo = MagicMock()
            mock_repo.create_issue.return_value = mock_issue

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            issue = client.create_issue(
                repo="owner/repo",
                title="New Issue",
                body="Issue body"
            )
            assert issue["number"] == 457

    @pytest.mark.asyncio
    async def test_update_issue_success(self):
        """Test successful issue update."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_issue = MagicMock()
            mock_issue.number = 456
            mock_issue.title = "Updated Issue"

            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            issue = client.update_issue(
                repo="owner/repo",
                number=456,
                title="Updated Issue"
            )
            assert issue["number"] == 456

    @pytest.mark.asyncio
    async def test_close_issue_success(self):
        """Test successful issue closure."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_issue = MagicMock()
            mock_issue.number = 456
            mock_issue.state = "closed"

            mock_repo = MagicMock()
            mock_repo.get_issue.return_value = mock_issue

            mock_instance.get_repo.return_value = mock_repo

            client = GitHubClient(token="test-token")
            await client.authenticate()

            issue = client.close_issue("owner/repo", 456)
            mock_issue.edit.assert_called()


class TestGitHubClientRateLimiting:
    """Test GitHub API rate limiting awareness."""

    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self):
        """Test rate limit status retrieval."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_rate_limit = MagicMock()
            mock_rate_limit.core.remaining = 4500
            mock_rate_limit.core.limit = 5000
            mock_rate_limit.core.reset = 1234567890

            mock_instance.get_rate_limit.return_value = mock_rate_limit

            client = GitHubClient(token="test-token")
            await client.authenticate()

            status = client.get_rate_limit_status()
            assert status["remaining"] == 4500
            assert status["limit"] == 5000

    @pytest.mark.asyncio
    async def test_warn_on_low_rate_limit(self):
        """Test warning when rate limit is low."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_rate_limit = MagicMock()
            mock_rate_limit.core.remaining = 100
            mock_rate_limit.core.limit = 5000

            mock_instance.get_rate_limit.return_value = mock_rate_limit

            client = GitHubClient(token="test-token")
            await client.authenticate()

            status = client.get_rate_limit_status()
            assert status["remaining"] == 100


class TestGitHubClientErrorHandling:
    """Test error handling in GitHub client."""

    @pytest.mark.asyncio
    async def test_handle_api_error_gracefully(self):
        """Test graceful handling of API errors."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_instance.get_repo.side_effect = Exception("API Error")
            mock_github_class.return_value = mock_instance

            client = GitHubClient(token="test-token")
            await client.authenticate()

            with pytest.raises(JmAgentError):
                client.get_repository("owner/repo")

    @pytest.mark.asyncio
    async def test_handle_network_error_gracefully(self):
        """Test graceful handling of network errors."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_instance.get_repo.side_effect = Exception("Network error")
            mock_github_class.return_value = mock_instance

            client = GitHubClient(token="test-token")
            await client.authenticate()

            with pytest.raises(JmAgentError):
                client.get_repository("owner/repo")


class TestGitHubClientStatusReport:
    """Test status reporting for GitHub integration."""

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        """Test successful status reporting."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            mock_user = MagicMock()
            mock_user.login = "testuser"

            mock_rate_limit = MagicMock()
            mock_rate_limit.core.remaining = 4500
            mock_rate_limit.core.limit = 5000
            mock_rate_limit.core.reset = 1234567890

            mock_instance.get_user.return_value = mock_user
            mock_instance.get_rate_limit.return_value = mock_rate_limit

            client = GitHubClient(token="test-token")
            await client.authenticate()

            status = await client.get_status()
            assert "authenticated" in status
            assert status["authenticated"] is True


class TestGitHubClientIntegration:
    """Integration tests for GitHub client."""

    @pytest.mark.asyncio
    async def test_full_workflow_get_repo_context(self):
        """Test full workflow of getting repository context."""
        with patch("src.integrations.github.Github") as mock_github_class:
            mock_instance = MagicMock()
            mock_user = MagicMock()
            mock_user.login = "testuser"
            mock_instance.get_user.return_value = mock_user
            mock_github_class.return_value = mock_instance
            mock_github = mock_instance
            # Setup mocks
            mock_repo = MagicMock()
            mock_repo.full_name = "owner/repo"
            mock_repo.description = "Test repo"
            mock_repo.language = "Python"
            mock_repo.stargazers_count = 100
            mock_repo.watchers_count = 50
            mock_repo.forks_count = 10
            mock_repo.html_url = "https://github.com/owner/repo"
            mock_repo.name = "repo"
            mock_repo.open_issues_count = 5
            mock_repo.created_at = datetime.now()
            mock_repo.updated_at = datetime.now()

            mock_readme = MagicMock()
            mock_readme.decoded_content = b"# Test"
            mock_repo.get_readme.return_value = mock_readme

            mock_content = MagicMock()
            mock_content.path = "file.py"
            mock_content.type = "file"
            mock_repo.get_contents.return_value = [mock_content]

            mock_user = MagicMock()
            mock_user.login = "testuser"

            mock_instance.get_repo.return_value = mock_repo
            mock_instance.get_user.return_value = mock_user

            client = GitHubClient(token="test-token")
            await client.authenticate()
            assert client.is_authenticated() is True

            # Get context
            context = await client.get_context(repo="owner/repo")
            assert context is not None
            assert context["owner"] == "owner"
            assert context["repo"] == "repo"
