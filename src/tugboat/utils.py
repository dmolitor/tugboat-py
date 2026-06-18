from concurrent.futures import ThreadPoolExecutor
import os
from pigar.dist import DEFAULT_PYPI_INDEX_URL
from pigar.parser import DEFAULT_GLOB_EXCLUDE_PATTERNS
from pigar.__main__ import generate as generate_cli
import platform
import shutil
from typing import List


class DockerNotFoundError(Exception):
    pass


def _run_in_thread(fn, *args, **kwargs):
    """Execute a function in a separate thread"""
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(fn, *args, **kwargs).result()


def is_windows() -> bool:
    return platform.system() == "Windows"


def stop_if_docker_not_installed() -> None:
    """Ensure Docker is installed"""
    if not shutil.which("docker"):
        raise DockerNotFoundError(
            "Visit https://docs.docker.com/get-docker/ to get started!"
        )


# `generate` is a Click (https://click.palletsprojects.com/en/stable/)
# cli object. The underlying `generate` function is stored at `generate.callback`
def _generate(
    requirement_file: str = "requirements-tugboat.txt",
    with_referenced_comments: bool = False,
    comparison_specifier: str = list(("==", "~=", ">=", ">", "-"))[4],
    show_differences: bool = True,
    visit_doc_string: bool = False,
    exclude_glob: List[str] = list(DEFAULT_GLOB_EXCLUDE_PATTERNS),
    follow_symbolic_links: bool = True,
    dry_run: bool = False,
    index_url: str = DEFAULT_PYPI_INDEX_URL,
    include_prereleases: bool = False,
    question_answer: str = "yes",
    auto_select: bool = False,
    experimental_features: List[str] = [],
    project_path: str = os.curdir,
) -> None:
    """Recreate an internal API for pigar's `generate` CLI function"""
    kwargs = dict(
        requirement_file=requirement_file,
        with_referenced_comments=with_referenced_comments,
        comparison_specifier=comparison_specifier,
        show_differences=show_differences,
        visit_doc_string=visit_doc_string,
        exclude_glob=exclude_glob,
        follow_symbolic_links=follow_symbolic_links,
        dry_run=dry_run,
        index_url=index_url,
        include_prereleases=include_prereleases,
        question_answer=question_answer,
        auto_select=auto_select,
        experimental_features=experimental_features,
        project_path=project_path,
    )
    # Run in separate thread so this does NOT fail when run in Jupyter environment
    _run_in_thread(generate_cli.callback, **kwargs)
