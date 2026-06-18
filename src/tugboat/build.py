from pathlib import Path
import shutil
import subprocess as sp
import tempfile
from typing import List

from .utils import is_windows, stop_if_docker_not_installed

def _copy_build_context_to_temp(build_context: str) -> str | None:
    if not is_windows():
        return None
    tmp = tempfile.TemporaryDirectory()
    tmp_path = Path(tmp.name)
    build_context = Path(build_context)
    for item in build_context.iterdir():
        dest = tmp_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    return tmp.name

def _build_image(
    dockerfile: str,
    platforms: List[str] | str,
    repository: str,
    tag: str,
    build_args: List[str] | None,
    build_context: str,
    push: bool,
    verbose: bool,
) -> None:
    tmp = _copy_build_context_to_temp(build_context)
    if not isinstance(platforms, list):
        platforms = [platforms]
    try:
        if tmp is not None:
            build_context = tmp
        exec_args = [
            "docker",
            "buildx",
            "build",
            "-f",
            str(Path(dockerfile).resolve()),
            "--platform",
            ",".join(platforms),
            "-t",
            f"{repository}:{tag}",
        ]
        if build_args:
            exec_args.extend(build_args)
        exec_args.append(str(build_context))
        if push:
            exec_args.append("--push")
        if verbose:
            print("Building:")
            print(" ".join(exec_args))
        result = sp.run(exec_args)
        if result.returncode != 0:
            raise RuntimeError(f"Build failed with status: {result.returncode}")
    finally:
        if tmp is not None:
            tmp.cleanup()

def build(
    dockerfile: str = Path(".") / "Dockerfile",
    image_name: str = "tugboat",
    tag: str = "latest",
    platforms: List[str] | str = ["linux/amd64", "linux/arm64"],
    build_args: List[str] | None = None,
    build_context: str = str(Path(".").resolve()),
    push: bool = False,
    dh_username: str | None = None,
    dh_password: str | None = None,
    verbose: bool = False
) -> str:
    """Build a Docker image from a Dockerfile"""
    stop_if_docker_not_installed()
    if push:
        if dh_username is None or dh_password is None:
            raise RuntimeError("Both `dh_username` and `dh_password` must be provided")
        login_result = sp.run(
            ["docker", "login", "-u", dh_username, "--password-stdin"],
            input=dh_password,
            text=True,
            check=True,
        )
        if login_result.returncode != 0:
            raise RuntimeError(f"Docker login failed with status: {login_result.returncode}")
    if dh_username is None:
        repository = image_name
    else:
        repository = f"{dh_username}/{image_name}"
    _build_image(
        dockerfile=dockerfile,
        platforms=platforms,
        repository=repository,
        tag=tag,
        build_args=build_args,
        build_context=build_context,
        push=push,
        verbose=verbose
    )
    return f"{repository}:{tag}"
