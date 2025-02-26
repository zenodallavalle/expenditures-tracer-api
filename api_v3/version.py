import logging


from dataclasses import dataclass, field
import os
import re
import subprocess
from typing import List

import semver


logger = logging.getLogger(__name__)


PRE_RELEASE_BRANCHES = ["main", "master"]
PREFIX_RELEASE_BRANCH = "release"


@dataclass(frozen=True)
class Version:
    sha1: str
    branch: str
    tags: List[str] = field(default_factory=list)
    recent_tags: List[str] = field(default_factory=list)
    additional_commits: int = 0


def from_repository(repo: os.path) -> Version:
    git_cmd = "git"

    if subprocess.call([git_cmd, "--version"], stdout=subprocess.PIPE) != 0:
        raise OSError(f"Command not available: {git_cmd}")

    if not os.access(repo, os.R_OK):
        raise PermissionError(f"No read access to: {repo}")

    recent_tags = []
    additional_commits = 0

    sha1 = (
        subprocess.check_output([git_cmd, "rev-parse", "--short", "HEAD"], cwd=repo)
        .decode("utf-8")
        .strip()
    )
    branch = (
        subprocess.check_output([git_cmd, "branch", "--show-current"], cwd=repo)
        .decode("utf-8")
        .strip()
    )
    tags = subprocess.check_output(
        [git_cmd, "tag", "--list", "--points-at", sha1], cwd=repo
    ).decode("utf-8")
    tag_list = list(filter(bool, tags.split("\n")))

    if tag_list:
        return Version(
            sha1=sha1,
            branch=branch,
            tags=tag_list,
            recent_tags=recent_tags,
            additional_commits=additional_commits,
        )

    try:
        describe = subprocess.check_output(
            [git_cmd, "describe", "--tags"], cwd=repo
        ).decode("utf-8")
        pattern = re.compile(r"(.+)-(\d+)-(.+)")
        match = pattern.match(describe)
        if match:
            recent_tags = [match.group(1)]
            additional_commits = int(match.group(2))
        else:
            logger.debug("Could not parse git-describe output: %s", describe)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logger.debug("Error calling git-describe: %s", ex)

    return Version(
        sha1=sha1,
        branch=branch,
        tags=tag_list,
        recent_tags=recent_tags,
        additional_commits=additional_commits,
    )


def from_git_info(gversion: Version) -> semver.Version:
    if gversion.tags:
        if len(gversion.tags) > 1:
            logger.warning(
                "More than one tag available, using first of: %s", gversion.tags
            )
        return semver.Version.parse(gversion.tags[0])

    prerelease = (
        f"pre.{gversion.additional_commits}"
        if gversion.branch in PRE_RELEASE_BRANCHES
        or gversion.branch.startswith(PREFIX_RELEASE_BRANCH)
        else f"dev.{gversion.additional_commits}"
    )
    build = f"g{gversion.sha1}"

    if gversion.recent_tags:
        if len(gversion.recent_tags) > 1:
            logger.warning(
                "More than one recent_tags available, using first of: %s",
                gversion.recent_tags,
            )

        sversion = semver.Version.parse(gversion.recent_tags[0]).bump_patch()
        sversion = semver.Version(
            sversion.major, sversion.minor, sversion.patch, prerelease, build
        )

        return sversion

    return semver.Version(0, 0, 0, prerelease, build)
