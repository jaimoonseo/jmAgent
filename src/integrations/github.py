"""GitHub API integration for jmAgent."""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime

from github import Github
from github.GithubException import GithubException

from src.integrations.base import BaseIntegration
from src.errors.exceptions import (
    JmAgentError,
    AuthenticationError,
)
from src.logging.logger import StructuredLogger


logger = StructuredLogger(__name__)


@dataclass
class GitHubContext:
    """
    Repository context from GitHub.

    Attributes:
        owner: Repository owner username
        repo: Repository name
        url: Repository URL
        description: Repository description
        language: Primary programming language
        stars: Number of stars
        watchers: Number of watchers
        forks: Number of forks
        readme: README content (first 2000 chars)
        file_tree: List of repository files/dirs
        key_files: List of important files (setup.py, requirements.txt, etc.)
    """

    owner: str
    repo: str
    url: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    watchers: int
    forks: int
    readme: Optional[str]
    file_tree: List[str]
    key_files: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class GitHubClient(BaseIntegration):
    """
    GitHub API client for jmAgent.

    Provides methods for:
    - Repository context loading (README, file tree, metadata)
    - Pull request operations (list, create, update, close)
    - Issue operations (list, create, update, close)
    - Repository search and filtering
    - Rate limit tracking
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token. If None, reads from
                   GITHUB_TOKEN environment variable.

        Raises:
            AuthenticationError: If no token is provided and GITHUB_TOKEN
                                 environment variable is not set.
        """
        self._token = token or os.getenv("GITHUB_TOKEN")
        if not self._token:
            raise AuthenticationError(
                "GitHub token not provided. Set GITHUB_TOKEN environment "
                "variable or pass token to GitHubClient(token=...)"
            )

        self._gh = None
        self._authenticated = False
        self._current_user = None

    async def authenticate(self) -> None:
        """
        Authenticate with GitHub API.

        Raises:
            AuthenticationError: If authentication fails.
        """
        try:
            self._gh = Github(self._token)
            self._current_user = self._gh.get_user()
            user_login = self._current_user.login if hasattr(self._current_user, 'login') else "unknown"
            self._authenticated = True

            logger.info(
                "GitHub authentication successful",
                extra={
                    "user": user_login,
                    "auth_method": "personal_token",
                }
            )
        except GithubException as e:
            self._authenticated = False
            error_msg = f"GitHub authentication failed: {str(e)}"
            logger.error(
                "GitHub authentication failed",
                extra={"error": str(e)}
            )
            raise AuthenticationError(error_msg)
        except Exception as e:
            self._authenticated = False
            error_msg = f"GitHub authentication error: {str(e)}"
            logger.error(
                "GitHub authentication error",
                extra={"error": str(e)}
            )
            raise AuthenticationError(error_msg)

    def is_authenticated(self) -> bool:
        """Check if authenticated with GitHub API."""
        return self._authenticated

    async def get_status(self) -> Dict[str, Any]:
        """
        Get status of GitHub integration.

        Returns:
            dict: Status information including authentication status and
                  rate limit information.
        """
        status = {
            "authenticated": self._authenticated,
            "service": "github",
        }

        if self._authenticated:
            try:
                rate_limit = self.get_rate_limit_status()
                status.update({
                    "user": self._current_user.login if self._current_user else None,
                    "rate_limit": rate_limit,
                })
            except Exception as e:
                logger.error(
                    "Failed to get rate limit status",
                    extra={"error": str(e)}
                )

        return status

    async def get_context(self, repo: Optional[str] = None) -> Dict[str, Any]:
        """
        Get repository context for prompt injection.

        Args:
            repo: Repository in format "owner/repo". If None, uses
                  environment variable GITHUB_REPO.

        Returns:
            dict: Repository context including metadata, README, file tree.

        Raises:
            JmAgentError: If context retrieval fails.
        """
        if not repo:
            repo = os.getenv("GITHUB_REPO")

        if not repo:
            raise JmAgentError(
                "No repository specified. Pass repo parameter or set "
                "GITHUB_REPO environment variable"
            )

        try:
            gh_repo = self._gh.get_repo(repo)

            # Get repository info
            owner, repo_name = repo.split("/")
            info = self.get_repository_info(repo)

            # Get README
            readme = self.get_readme(repo)

            # Get file tree
            file_tree = self.get_file_tree(repo, max_depth=2)

            # Get key files
            key_files = self._identify_key_files(file_tree)

            context = GitHubContext(
                owner=owner,
                repo=repo_name,
                url=gh_repo.html_url,
                description=gh_repo.description,
                language=gh_repo.language,
                stars=info["stars"],
                watchers=info["watchers"],
                forks=info["forks"],
                readme=readme,
                file_tree=file_tree[:50],  # Limit to 50 items
                key_files=key_files,
            )

            logger.info(
                "Repository context loaded",
                extra={
                    "repo": repo,
                    "owner": owner,
                    "files_count": len(file_tree),
                    "has_readme": readme is not None,
                }
            )

            return context.to_dict()

        except Exception as e:
            error_msg = f"Failed to load repository context: {str(e)}"
            logger.error(
                "Repository context load failed",
                extra={"repo": repo, "error": str(e)}
            )
            raise JmAgentError(error_msg)

    def get_repository(self, repo: str) -> Any:
        """
        Get repository object from GitHub.

        Args:
            repo: Repository in format "owner/repo".

        Returns:
            Repository object from PyGithub.

        Raises:
            JmAgentError: If repository not found or API error occurs.
        """
        if not self._authenticated:
            raise JmAgentError("Not authenticated with GitHub")

        try:
            return self._gh.get_repo(repo)
        except GithubException as e:
            if e.status == 404:
                raise JmAgentError(f"Repository not found: {repo}")
            raise JmAgentError(f"GitHub API error: {str(e)}")
        except Exception as e:
            raise JmAgentError(f"Failed to get repository: {str(e)}")

    def get_repository_info(self, repo: str) -> Dict[str, Any]:
        """
        Get repository metadata.

        Args:
            repo: Repository in format "owner/repo".

        Returns:
            dict: Repository metadata including stars, language, forks, etc.

        Raises:
            JmAgentError: If retrieval fails.
        """
        try:
            gh_repo = self.get_repository(repo)
            return {
                "name": gh_repo.name,
                "full_name": gh_repo.full_name,
                "description": gh_repo.description,
                "url": gh_repo.html_url,
                "language": gh_repo.language,
                "stars": gh_repo.stargazers_count,
                "watchers": gh_repo.watchers_count,
                "forks": gh_repo.forks_count,
                "open_issues": gh_repo.open_issues_count,
                "created_at": gh_repo.created_at.isoformat(),
                "updated_at": gh_repo.updated_at.isoformat(),
            }
        except JmAgentError:
            raise
        except Exception as e:
            raise JmAgentError(f"Failed to get repository info: {str(e)}")

    def get_readme(self, repo: str) -> Optional[str]:
        """
        Get README content from repository.

        Args:
            repo: Repository in format "owner/repo".

        Returns:
            str: README content (first 2000 chars) or None if not found.

        Raises:
            JmAgentError: If retrieval fails.
        """
        try:
            gh_repo = self.get_repository(repo)
            readme = gh_repo.get_readme()
            content = readme.decoded_content.decode("utf-8")
            # Limit to first 2000 characters
            return content[:2000]
        except GithubException as e:
            if e.status == 404:
                logger.info(
                    "README not found",
                    extra={"repo": repo}
                )
                return None
            raise JmAgentError(f"GitHub API error: {str(e)}")
        except Exception as e:
            logger.warning(
                "Failed to get README",
                extra={"repo": repo, "error": str(e)}
            )
            return None

    def get_file_tree(
        self,
        repo: str,
        path: str = "",
        max_depth: int = 2,
        _current_depth: int = 0
    ) -> List[str]:
        """
        Get file tree structure of repository.

        Args:
            repo: Repository in format "owner/repo".
            path: Path within repository to start from (empty = root).
            max_depth: Maximum directory depth to traverse.
            _current_depth: Current recursion depth (internal).

        Returns:
            list: List of file paths in repository.

        Raises:
            JmAgentError: If retrieval fails.
        """
        if _current_depth >= max_depth:
            return []

        try:
            gh_repo = self.get_repository(repo)
            contents = gh_repo.get_contents(path)

            files = []
            if not isinstance(contents, list):
                contents = [contents]

            for content in contents:
                if content.type == "file":
                    files.append(content.path)
                elif content.type == "dir" and _current_depth < max_depth - 1:
                    # Recursively get subdirectory contents
                    try:
                        subfiles = self.get_file_tree(
                            repo,
                            content.path,
                            max_depth,
                            _current_depth + 1
                        )
                        files.extend(subfiles)
                    except Exception:
                        # Skip directories we can't access
                        pass

            return files

        except GithubException as e:
            raise JmAgentError(f"Failed to get file tree: {str(e)}")
        except Exception as e:
            raise JmAgentError(f"Failed to get file tree: {str(e)}")

    def list_pull_requests(
        self,
        repo: str,
        state: str = "open",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List pull requests from repository.

        Args:
            repo: Repository in format "owner/repo".
            state: PR state filter ("open", "closed", "all").
            limit: Maximum number of PRs to return.

        Returns:
            list: List of pull request dictionaries.

        Raises:
            JmAgentError: If retrieval fails.
        """
        try:
            gh_repo = self.get_repository(repo)
            prs = gh_repo.get_pulls(state=state)

            pr_list = []
            for pr in prs[:limit]:
                pr_list.append({
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body,
                    "state": pr.state,
                    "author": pr.user.login if pr.user else None,
                    "created_at": pr.created_at.isoformat(),
                    "updated_at": pr.updated_at.isoformat(),
                    "url": pr.html_url,
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "changed_files": pr.changed_files,
                })

            logger.info(
                "Pull requests listed",
                extra={
                    "repo": repo,
                    "state": state,
                    "count": len(pr_list),
                }
            )

            return pr_list

        except JmAgentError:
            raise
        except Exception as e:
            raise JmAgentError(f"Failed to list pull requests: {str(e)}")

    def create_pull_request(
        self,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a pull request.

        Args:
            repo: Repository in format "owner/repo".
            title: PR title.
            body: PR description.
            head: Branch to merge from.
            base: Branch to merge into (default: main).

        Returns:
            dict: Created pull request information.

        Raises:
            JmAgentError: If creation fails.
        """
        try:
            gh_repo = self.get_repository(repo)
            pr = gh_repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )

            logger.info(
                "Pull request created",
                extra={
                    "repo": repo,
                    "number": pr.number,
                    "title": title,
                }
            )

            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "url": pr.html_url,
            }

        except JmAgentError:
            raise
        except Exception as e:
            raise JmAgentError(f"Failed to create pull request: {str(e)}")

    def update_pull_request(
        self,
        repo: str,
        number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a pull request.

        Args:
            repo: Repository in format "owner/repo".
            number: PR number.
            title: New title (optional).
            body: New body (optional).
            state: New state: "open" or "closed" (optional).

        Returns:
            dict: Updated pull request information.

        Raises:
            JmAgentError: If update fails.
        """
        try:
            gh_repo = self.get_repository(repo)
            pr = gh_repo.get_pull(number)

            if title is not None or body is not None or state is not None:
                pr.edit(
                    title=title or pr.title,
                    body=body or pr.body,
                    state=state or pr.state
                )

            logger.info(
                "Pull request updated",
                extra={"repo": repo, "number": number}
            )

            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "url": pr.html_url,
            }

        except JmAgentError:
            raise
        except Exception as e:
            raise JmAgentError(f"Failed to update pull request: {str(e)}")

    def close_pull_request(
        self,
        repo: str,
        number: int
    ) -> Dict[str, Any]:
        """
        Close a pull request.

        Args:
            repo: Repository in format "owner/repo".
            number: PR number.

        Returns:
            dict: Closed pull request information.

        Raises:
            JmAgentError: If close fails.
        """
        return self.update_pull_request(repo, number, state="closed")

    def list_issues(
        self,
        repo: str,
        state: str = "open",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List issues from repository.

        Args:
            repo: Repository in format "owner/repo".
            state: Issue state filter ("open", "closed", "all").
            limit: Maximum number of issues to return.

        Returns:
            list: List of issue dictionaries.

        Raises:
            JmAgentError: If retrieval fails.
        """
        try:
            gh_repo = self.get_repository(repo)
            issues = gh_repo.get_issues(state=state)

            issue_list = []
            for issue in issues[:limit]:
                issue_list.append({
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "author": issue.user.login if issue.user else None,
                    "created_at": issue.created_at.isoformat(),
                    "updated_at": issue.updated_at.isoformat(),
                    "url": issue.html_url,
                    "labels": [label.name for label in issue.labels],
                })

            logger.info(
                "Issues listed",
                extra={
                    "repo": repo,
                    "state": state,
                    "count": len(issue_list),
                }
            )

            return issue_list

        except JmAgentError:
            raise
        except Exception as e:
            raise JmAgentError(f"Failed to list issues: {str(e)}")

    def create_issue(
        self,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create an issue.

        Args:
            repo: Repository in format "owner/repo".
            title: Issue title.
            body: Issue description.
            labels: List of label names (optional).

        Returns:
            dict: Created issue information.

        Raises:
            JmAgentError: If creation fails.
        """
        try:
            gh_repo = self.get_repository(repo)
            issue = gh_repo.create_issue(
                title=title,
                body=body,
                labels=labels or []
            )

            logger.info(
                "Issue created",
                extra={
                    "repo": repo,
                    "number": issue.number,
                    "title": title,
                }
            )

            return {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "url": issue.html_url,
            }

        except JmAgentError:
            raise
        except Exception as e:
            raise JmAgentError(f"Failed to create issue: {str(e)}")

    def update_issue(
        self,
        repo: str,
        number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update an issue.

        Args:
            repo: Repository in format "owner/repo".
            number: Issue number.
            title: New title (optional).
            body: New body (optional).
            state: New state: "open" or "closed" (optional).
            labels: New labels (optional).

        Returns:
            dict: Updated issue information.

        Raises:
            JmAgentError: If update fails.
        """
        try:
            gh_repo = self.get_repository(repo)
            issue = gh_repo.get_issue(number)

            if title is not None or body is not None or state is not None:
                issue.edit(
                    title=title or issue.title,
                    body=body or issue.body,
                    state=state or issue.state,
                    labels=labels or [label.name for label in issue.labels]
                )

            logger.info(
                "Issue updated",
                extra={"repo": repo, "number": number}
            )

            return {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "url": issue.html_url,
            }

        except JmAgentError:
            raise
        except Exception as e:
            raise JmAgentError(f"Failed to update issue: {str(e)}")

    def close_issue(
        self,
        repo: str,
        number: int
    ) -> Dict[str, Any]:
        """
        Close an issue.

        Args:
            repo: Repository in format "owner/repo".
            number: Issue number.

        Returns:
            dict: Closed issue information.

        Raises:
            JmAgentError: If close fails.
        """
        return self.update_issue(repo, number, state="closed")

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get GitHub API rate limit status.

        Returns:
            dict: Rate limit information including remaining and total.

        Raises:
            JmAgentError: If check fails.
        """
        if not self._authenticated:
            raise JmAgentError("Not authenticated with GitHub")

        try:
            rate_limit = self._gh.get_rate_limit()
            return {
                "limit": rate_limit.core.limit,
                "remaining": rate_limit.core.remaining,
                "reset": rate_limit.core.reset,
            }
        except Exception as e:
            raise JmAgentError(f"Failed to get rate limit status: {str(e)}")

    def _identify_key_files(self, file_tree: List[str]) -> List[str]:
        """
        Identify important files in repository.

        Args:
            file_tree: List of all files in repository.

        Returns:
            list: List of key file paths.
        """
        key_file_patterns = [
            "setup.py",
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "Dockerfile",
            "docker-compose.yml",
            "README.md",
            "LICENSE",
            "Makefile",
            "tox.ini",
            "pytest.ini",
            ".github",
        ]

        key_files = []
        for file in file_tree:
            for pattern in key_file_patterns:
                if pattern in file:
                    key_files.append(file)
                    break

        return key_files[:10]  # Limit to 10 key files
