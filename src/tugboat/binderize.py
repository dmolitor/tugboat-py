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
    add_readme_badge: bool = True
) -> str:
    readme = Path(readme)
    badge = f"[![{label}]({image_url})]({href})"
    start = "<!-- badges: start -->"
    end = "<!-- badges: end -->"
    instructions = (
        f"{start}\n"
        f"{badge}\n"
        f"{end}"
    )
    # Copy instructions to the clipboard and also print them
    def copy_instructions() -> None:
        pyperclip.copy(instructions)
        print("Add the following to your README.md file:\n\n" + instructions)
        print("\nCopied to clipboard.")
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
    verbose: bool = False
) -> None:
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
        add_readme_badge=add_readme_badge
    )
    # Give the user final instructions
    print("Your repository has been configured for Binder.")
    print("[x] Commit and push all changes")
    print("[x] Launch Binder at: ", binder_url)

