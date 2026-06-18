import os
from pathlib import Path
import sys
from typing import List

from .utils import _generate

PY_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"
DEFAULT_IMAGE = f"python:{PY_VERSION}-slim"

def _dockerfile(project_name: str | None = None, project: str = str(Path(".").resolve()), FROM: str | None = None) -> str:
    if project_name is None:
        project_dir = f"/{Path(project).name}"
    else:
        project_dir = f"/{project_name}"
    if not FROM:
        FROM = DEFAULT_IMAGE
    dock = f"""FROM {FROM}
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY . {project_dir}
WORKDIR {project_dir}
RUN test -f pyproject.toml || uv init --app . || true
RUN uv sync --all-groups --all-extras
RUN uv add -r requirements-tugboat.txt"""
    return dock

def _dockerignore(project: str, exclude: List[str] | str | None = None) -> None:
    if not isinstance(exclude, List) and exclude:
        exclude = [exclude]
    elif not exclude:
        exclude = []
    exclude = list(set(exclude + ["Dockerfile", ".dockerignore", "**/.DS_Store"]))
    dockerignore_path = str(Path(project) / ".dockerignore")
    with open(dockerignore_path, "w") as path:
        path.writelines(f"{item}\n" for item in exclude)

def create(
    project: str = str(Path(".").resolve()),
    FROM: str | None = None,
    exclude: List[str] | str | None = None,
    verbose: bool = False,
    **kwargs
) -> None:
    project = os.path.abspath(project)
    # Scan for dependencies and generate requirements.txt
    _generate(project_path=project, **kwargs)
    # Generate .dockerignore
    _dockerignore(project=project, exclude=exclude)
    # Generate Dockerfile
    dock = _dockerfile(project=project, FROM=FROM)
    if verbose:
        print(dock)
    dockerfile_path = Path(project) / "Dockerfile"
    dockerfile_path.write_text(dock)
