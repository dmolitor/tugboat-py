from pathlib import Path
import pyperclip
from pygit2 import Repository
import re

BADGE_URL = "https://mybinder.org/badge_logo.svg"
DEFAULT_IMAGE = "rocker/binder:4"


def _use_badge(
    label: str,
    href: str,
    image_url: str,
    readme: str | Path = "README.md",
    add_readme_badge: bool = True,
) -> str:
    readme = Path(readme)
    badge = f"[![{label}]({image_url})]({href})"
    start = "<!-- badges: start -->"
    end = "<!-- badges: end -->"
    instructions = f"{start}\n" f"{badge}\n" f"{end}"

    # Copy instructions to the clipboard and also print them
    def copy_instructions() -> str:
        pyperclip.copy(instructions)
        print("Add the following to your README.md file:\n\n" + instructions)
        print("\nCopied to clipboard.")
        return badge

    # Determine whether to modify README.md or just return instructions
    if not add_readme_badge:
        return copy_instructions()
    if not readme.exists():
        return copy_instructions()
    # Modify README.md
    text = readme.read_text()
    if badge in text:
        print(f"Badge already exists in {readme}")
        return badge
    if start not in text or end not in text:
        return copy_instructions()
    before, rest = text.split(start, maxsplit=1)
    badges, after = rest.split(end, maxsplit=1)
    badges = badges.rstrip() + f"\n{badge}\n"
    readme.write_text(f"{before}{start}{badges}{end}{after}")
    print(f"Added badge to {readme}")
    return badge


def _binder_dockerfile() -> str:
    dock = f"""FROM {DEFAULT_IMAGE}""" + """
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --chown=${NB_USER} . /home/rstudio
WORKDIR /home/rstudio
USER root
RUN printf "RETICULATE_PYTHON_ENV=/home/rstudio/.venv\\nVIRTUAL_ENV=/home/rstudio/.venv\\n" >> /usr/local/lib/R/etc/Renviron.site
USER ${NB_USER}
RUN test -f pyproject.toml || uv init --app . || true
RUN uv sync --all-groups --all-extras
RUN uv add -r requirements-tugboat.txt"""
    return dock


def binderize(
    project: Path | str = Path("."),
    branch: str = "main",
    urlpath: str = "rstudio",
    add_readme_badge: bool = True,
    overwrite: bool = True,
    verbose: bool = False,
) -> None:
    """
    Prepare a GitHub repository to be launched via Binder.

    Writes a ``.binder/Dockerfile`` and inserts a Binder launch badge into
    the project's README.md (or copies the badge snippet to the clipboard
    if the README has no badge section to insert into).

    Parameters
    ----------
    project : Path or str, default Path(".")
        Path to the local Git repository to binderize. Must be a GitHub repository.
    branch : str, default "main"
        Branch to point the Binder launch link at.
    urlpath : str, default "rstudio"
        URL path Binder should open to on launch (e.g. "rstudio", "lab").
    add_readme_badge : bool, default True
        Whether to attempt to insert the Binder badge into the project's
        README.md. If False, the badge snippet is copied to the clipboard
        and printed instead.
    overwrite : bool, default True
        Whether to overwrite an existing ``.binder/Dockerfile``.
    verbose : bool, default False
        Whether to print the generated Binder Dockerfile contents.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If the repository is not a GitHub repository.
    """
    # Create repo object and extract url, username, repo name, etc.
    repo = Repository(project)
    git_remote = repo.remotes["origin"].url
    local_repo = Path(repo.workdir)
    username_repo = re.sub(r".*github\.com[:/](.*)\.git$", r"\1", git_remote).split("/")
    if git_remote.find("github.com") == -1:
        raise ValueError("Only GitHub repositories are currently supported.")
    # Generate Dockerfile
    dock = _binder_dockerfile()
    if verbose:
        print(dock)
    binder_dir = local_repo / ".binder"
    if not binder_dir.is_dir():
        binder_dir.mkdir()
    dockerfile_path = binder_dir / "Dockerfile"
    if overwrite:
        dockerfile_path.write_text(dock)
    # Construct Binder badge and insert into README (if possible)
    binder_url = f"https://mybinder.org/v2/gh/{'/'.join(username_repo)}/{branch}?urlpath={urlpath}"
    _use_badge(
        label="Launch RStudio Binder",
        href=binder_url,
        image_url=BADGE_URL,
        readme=local_repo / "README.md",
        add_readme_badge=add_readme_badge,
    )
    # Give the user final instructions
    print("Your repository has been configured for Binder.")
    print("[x] Commit and push all changes")
    print("[x] Launch Binder at: ", binder_url)
