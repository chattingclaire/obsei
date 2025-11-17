"""
GitHub Tool
Interact with GitHub API using PyGithub for repo search, metadata extraction, etc.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from github import Github, GithubException
from github.Repository import Repository
from github.NamedUser import NamedUser

logger = logging.getLogger(__name__)


class GitHubTool:
    """
    GitHub API interaction tool using PyGithub
    """

    def __init__(self, token: Optional[str] = None, max_retries: int = 3):
        """
        Initialize GitHub tool

        Args:
            token: GitHub personal access token
            max_retries: Maximum API retry attempts
        """
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.token:
            logger.warning("No GitHub token provided, API rate limits will be lower")
            self.github = Github()
        else:
            self.github = Github(self.token)

        self.max_retries = max_retries

        # Check rate limit
        rate_limit = self.github.get_rate_limit()
        logger.info(f"GitHub API initialized. Rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")

    def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search GitHub repositories

        Args:
            query: Search query (e.g., "language:python stars:>100")
            sort: Sort by (stars, forks, updated)
            order: Sort order (asc, desc)
            max_results: Maximum number of results

        Returns:
            List of repository metadata
        """
        try:
            repositories = self.github.search_repositories(
                query=query,
                sort=sort,
                order=order
            )

            results = []
            for i, repo in enumerate(repositories):
                if i >= max_results:
                    break

                results.append(self._extract_repo_metadata(repo))

            logger.info(f"Found {len(results)} repositories for query: {query}")
            return results

        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching repositories: {e}")
            return []

    def get_repository(self, owner: str, repo_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed repository information

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            Repository metadata
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            metadata = self._extract_repo_metadata(repo, detailed=True)

            logger.debug(f"Retrieved repository: {owner}/{repo_name}")
            return metadata

        except GithubException as e:
            logger.error(f"Error getting repository {owner}/{repo_name}: {e}")
            return None

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user/organization information

        Args:
            username: GitHub username

        Returns:
            User metadata
        """
        try:
            user = self.github.get_user(username)
            metadata = self._extract_user_metadata(user)

            logger.debug(f"Retrieved user: {username}")
            return metadata

        except GithubException as e:
            logger.error(f"Error getting user {username}: {e}")
            return None

    def get_trending_repos(
        self,
        language: Optional[str] = None,
        since: str = "daily",
        max_results: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Get trending repositories

        Args:
            language: Filter by programming language
            since: Time period (daily, weekly, monthly)
            max_results: Maximum number of results

        Returns:
            List of trending repositories
        """
        try:
            # Build query for recently popular repos
            query_parts = ["stars:>100"]

            if language:
                query_parts.append(f"language:{language}")

            # Use date range for "trending"
            if since == "daily":
                query_parts.append("created:>2024-01-01")
            elif since == "weekly":
                query_parts.append("created:>2023-01-01")

            query = " ".join(query_parts)

            return self.search_repositories(
                query=query,
                sort="stars",
                order="desc",
                max_results=max_results
            )

        except Exception as e:
            logger.error(f"Error getting trending repos: {e}")
            return []

    def get_repo_readme(self, owner: str, repo_name: str) -> Optional[str]:
        """
        Get repository README content

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            README content as string
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            readme = repo.get_readme()
            content = readme.decoded_content.decode("utf-8")

            logger.debug(f"Retrieved README for {owner}/{repo_name}")
            return content

        except GithubException as e:
            logger.error(f"Error getting README: {e}")
            return None

    def get_repo_languages(self, owner: str, repo_name: str) -> Dict[str, int]:
        """
        Get repository language statistics

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            Dict of language: bytes_of_code
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            languages = repo.get_languages()

            logger.debug(f"Retrieved languages for {owner}/{repo_name}")
            return languages

        except GithubException as e:
            logger.error(f"Error getting languages: {e}")
            return {}

    def get_repo_contributors(self, owner: str, repo_name: str, max_contributors: int = 10) -> List[Dict[str, Any]]:
        """
        Get repository contributors

        Args:
            owner: Repository owner
            repo_name: Repository name
            max_contributors: Maximum number of contributors

        Returns:
            List of contributor metadata
        """
        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            contributors = repo.get_contributors()

            results = []
            for i, contributor in enumerate(contributors):
                if i >= max_contributors:
                    break

                results.append({
                    "login": contributor.login,
                    "name": contributor.name,
                    "contributions": contributor.contributions,
                    "profile_url": contributor.html_url,
                    "avatar_url": contributor.avatar_url,
                    "bio": contributor.bio,
                    "company": contributor.company,
                    "location": contributor.location,
                    "email": contributor.email,
                    "followers": contributor.followers,
                })

            logger.debug(f"Retrieved {len(results)} contributors for {owner}/{repo_name}")
            return results

        except GithubException as e:
            logger.error(f"Error getting contributors: {e}")
            return []

    def search_code(self, query: str, max_results: int = 30) -> List[Dict[str, Any]]:
        """
        Search code across GitHub

        Args:
            query: Code search query
            max_results: Maximum number of results

        Returns:
            List of code search results
        """
        try:
            code_results = self.github.search_code(query=query)

            results = []
            for i, code in enumerate(code_results):
                if i >= max_results:
                    break

                results.append({
                    "name": code.name,
                    "path": code.path,
                    "repository": code.repository.full_name,
                    "url": code.html_url,
                    "sha": code.sha
                })

            logger.info(f"Found {len(results)} code results for query: {query}")
            return results

        except GithubException as e:
            logger.error(f"Error searching code: {e}")
            return []

    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Get current API rate limit status

        Returns:
            Rate limit information
        """
        try:
            rate_limit = self.github.get_rate_limit()

            return {
                "core": {
                    "limit": rate_limit.core.limit,
                    "remaining": rate_limit.core.remaining,
                    "reset": rate_limit.core.reset.isoformat()
                },
                "search": {
                    "limit": rate_limit.search.limit,
                    "remaining": rate_limit.search.remaining,
                    "reset": rate_limit.search.reset.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error getting rate limit: {e}")
            return {}

    def _extract_repo_metadata(self, repo: Repository, detailed: bool = False) -> Dict[str, Any]:
        """Extract metadata from repository object"""
        metadata = {
            "name": repo.name,
            "full_name": repo.full_name,
            "owner": repo.owner.login,
            "description": repo.description,
            "url": repo.html_url,
            "clone_url": repo.clone_url,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "watchers": repo.watchers_count,
            "open_issues": repo.open_issues_count,
            "language": repo.language,
            "topics": repo.get_topics(),
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
            "size": repo.size,
            "default_branch": repo.default_branch,
            "has_issues": repo.has_issues,
            "has_wiki": repo.has_wiki,
            "has_pages": repo.has_pages,
            "license": repo.license.name if repo.license else None,
        }

        if detailed:
            # Add more detailed information
            try:
                metadata["languages"] = repo.get_languages()
                metadata["subscriber_count"] = repo.subscribers_count
                metadata["network_count"] = repo.network_count
            except:
                pass

        return metadata

    def _extract_user_metadata(self, user: NamedUser) -> Dict[str, Any]:
        """Extract metadata from user object"""
        return {
            "login": user.login,
            "name": user.name,
            "email": user.email,
            "bio": user.bio,
            "company": user.company,
            "location": user.location,
            "blog": user.blog,
            "twitter_username": user.twitter_username,
            "profile_url": user.html_url,
            "avatar_url": user.avatar_url,
            "followers": user.followers,
            "following": user.following,
            "public_repos": user.public_repos,
            "public_gists": user.public_gists,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "type": user.type,
        }


# Convenience functions
def search_github_repos(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Convenience function to search GitHub repositories

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        List of repositories
    """
    tool = GitHubTool()
    return tool.search_repositories(query, max_results=max_results)


def get_github_repo(owner: str, repo_name: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get GitHub repository

    Args:
        owner: Repository owner
        repo_name: Repository name

    Returns:
        Repository metadata
    """
    tool = GitHubTool()
    return tool.get_repository(owner, repo_name)


def get_github_user(username: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get GitHub user

    Args:
        username: GitHub username

    Returns:
        User metadata
    """
    tool = GitHubTool()
    return tool.get_user(username)
