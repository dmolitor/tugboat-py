from pathlib import Path
import sys
from typing import Any, List

from .utils import _generate

PY_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"
DEFAULT_IMAGE = f"python:{PY_VERSION}-slim"


def _dockerfile(
    project_name: str | None = None,
    project: str = str(Path(".").resolve()),
    FROM: str | None = None,
) -> str:
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
    project: str | Path = Path("."),
    FROM: str | None = None,
    exclude: List[str] | str | None = None,
    verbose: bool = False,
    **kwargs: Any,
) -> None:
    """
    Generate a Dockerfile and .dockerignore from an analysis directory.

    Scans `project` for Python dependencies using pigar, writes them to
    a `requirements.txt` files, and generates a Dockerfile that copies the
    analysis directory into the image and installs those dependencies with uv.
    Since tugboat uses uv under the hood, it should be immediately compatible
    with any project that is already set up to use uv.

    Parameters
    ----------
    project : str, default current working directory
        Path to the analysis directory to generate a Dockerfile from.
    FROM : str or None, default None
        Base Docker image to use in the generated Dockerfile's ``FROM``
        instruction. If None, defaults to ``python:{version}-slim`` using
        the running Python's version.
    exclude : list of str, str, or None, default None
        File(s) or sub-directorie(s) to exclude from the Docker image via
        the generated ``.dockerignore``.
    verbose : bool, default False
        Whether to print the generated Dockerfile contents.
    **kwargs : Any
        Additional keyword arguments forwarded to pigar's dependency-scanning
        ``generate`` function (e.g. `dry_run`, `index_url`).

    Returns
    -------
    None
    """
    project = Path(project).resolve()
    # Scan for dependencies and generate requirements.txt
    _generate(
        requirement_file=str(project / "requirements-tugboat.txt"),
        project_path=str(project),
        **kwargs,
    )
    # Generate .dockerignore
    _dockerignore(project=str(project), exclude=exclude)
    # Generate Dockerfile
    dock = _dockerfile(project=str(project), FROM=FROM)
    if verbose:
        print(dock)
    dockerfile_path = project / "Dockerfile"
    dockerfile_path.write_text(dock)
