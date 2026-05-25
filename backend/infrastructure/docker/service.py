import logging
from pathlib import Path

import docker
from docker.errors import DockerException

from config import settings

logger = logging.getLogger(__name__)


class DockerDeployService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def is_available(self) -> bool:
        try:
            self.client.ping()
            return True
        except DockerException:
            return False

    def build_image(self, path: Path, tag: str) -> str:
        image, logs = self.client.images.build(path=str(path), tag=tag, rm=True)
        log_lines = []
        for chunk in logs:
            if "stream" in chunk:
                log_lines.append(chunk["stream"].strip())
        return "\n".join(log_lines[-50:]) or f"Built image {image.tags}"

    def _container_init_bind(self) -> dict | None:
        init_dir = Path(settings.deploy_workspace) / "container-init"
        if not init_dir.exists():
            return None
        return {str(init_dir.resolve()): {"bind": "/app/data", "mode": "ro"}}

    def run_container(
        self,
        image_tag: str,
        app_name: str,
        port: int = 8080,
        git_branch: str | None = None,
        task_id: int | None = None,
    ) -> str:
        container_name = f"devopsforge-{app_name}"
        try:
            old = self.client.containers.get(container_name)
            old.stop()
            old.remove()
        except docker.errors.NotFound:
            pass

        environment = {
            "APP_SEED": "1",
            "APP_NAME": app_name,
        }
        if git_branch:
            environment["GIT_BRANCH"] = git_branch
        if task_id:
            environment["TASK_ID"] = str(task_id)

        env_file = Path(settings.deploy_workspace) / "container-init" / "default.env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    environment[k.strip()] = v.strip()

        volumes = self._container_init_bind()
        logs = []
        if volumes:
            logs.append(f"Mounted init data: {list(volumes.keys())[0]} -> /app/data")

        container = self.client.containers.run(
            image_tag,
            name=container_name,
            detach=True,
            ports={f"{port}/tcp": port},
            restart_policy={"Name": "unless-stopped"},
            environment=environment,
            volumes=volumes or None,
        )
        msg = f"Container {container.name} started: {container.short_id}"
        if git_branch:
            msg += f" (branch={git_branch})"
        if volumes:
            msg += "; " + logs[0]
        return msg

    def stop_container(self, app_name: str) -> str:
        container_name = f"devopsforge-{app_name}"
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            return f"Stopped {container_name}"
        except docker.errors.NotFound:
            return f"No container {container_name}"
