import hashlib
import re
import subprocess
from pathlib import Path

from git import Repo

from config import settings


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return (s[:max_len] or "task").rstrip("-")


class GitClient:
    def __init__(self, cache_root: Path | None = None):
        self.cache_root = cache_root or Path(settings.git_cache_dir)
        self.cache_root.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, repo_url: str) -> Path:
        key = hashlib.sha256(repo_url.encode()).hexdigest()[:16]
        return self.cache_root / key

    def list_remote_branches(self, repo_url: str) -> list[str]:
        try:
            out = subprocess.run(
                ["git", "ls-remote", "--heads", repo_url],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            branches = []
            for line in out.stdout.splitlines():
                if "\trefs/heads/" in line:
                    branches.append(line.split("refs/heads/")[-1].strip())
            return sorted(set(branches))
        except Exception:
            return ["main", "master"]

    def ensure_cached_repo(self, repo_url: str) -> Path:
        path = self._cache_path(repo_url)
        if (path / ".git").exists():
            repo = Repo(path)
            try:
                repo.remotes.origin.fetch(depth=1)
            except Exception:
                pass
            return path
        Repo.clone_from(repo_url, path, depth=1)
        return path

    def branch_name_for_task(self, task_id: int, title: str) -> str:
        return f"task/{task_id}-{slugify(title)}"

    def create_branch_for_task(
        self,
        repo_url: str,
        task_id: int,
        title: str,
        base_branch: str = "main",
    ) -> str:
        repo_path = self.ensure_cached_repo(repo_url)
        repo = Repo(repo_path)
        branch_name = self.branch_name_for_task(task_id, title)

        try:
            repo.git.checkout(base_branch)
        except Exception:
            try:
                repo.git.checkout("master")
                base_branch = "master"
            except Exception:
                base_branch = repo.active_branch.name

        if branch_name in [h.name for h in repo.heads]:
            repo.git.checkout(branch_name)
            return branch_name

        new_head = repo.create_head(branch_name, repo.commit(base_branch))
        new_head.checkout()
        return branch_name

    def clone_or_pull(self, repo_url: str, branch: str, target_dir: Path) -> tuple[str, str]:
        if target_dir.exists():
            import shutil

            shutil.rmtree(target_dir, ignore_errors=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            repo = Repo.clone_from(repo_url, target_dir, branch=branch, depth=1)
        except Exception:
            repo = Repo.clone_from(repo_url, target_dir, depth=1)
        sha = repo.head.commit.hexsha
        version = sha[:8]
        return sha, version

    def read_dockerfile(self, target_dir: Path) -> Path | None:
        dockerfile = target_dir / "Dockerfile"
        return dockerfile if dockerfile.exists() else None
