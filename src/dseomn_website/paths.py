# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Collection
import urllib.parse

import ginjarator

PRIVATE = ginjarator.paths.Filesystem("../private")

WORK = ginjarator.paths.Filesystem("work")

OUTPUT = ginjarator.paths.Filesystem("output")
ASSETS = OUTPUT / "assets"
DIR_INDEXES = (
    "index.html",  # Should probably come first for performance, maybe?
    "index.atom",
)


def work(
    source: ginjarator.paths.Filesystem | str,
) -> ginjarator.paths.Filesystem:
    """Returns a path in WORK for the given source path."""
    source_path = ginjarator.paths.Filesystem(source)
    if source_path.is_relative_to(PRIVATE):
        relative = source_path.relative_to(PRIVATE)
    else:
        relative = source_path
    return WORK / relative


def from_url_path(
    url_path: str,
    *,
    dir_index: str = "index.html",
) -> ginjarator.paths.Filesystem:
    """Returns an fs path from a url path."""
    unquoted = urllib.parse.unquote(url_path)
    if dir_index not in DIR_INDEXES:
        raise ValueError(
            f"Invalid dir_index {dir_index!r}, allowed values are: "
            f"{DIR_INDEXES}"
        )
    if not unquoted.startswith("/"):
        raise NotImplementedError("Relative url paths are not supported.")
    elif unquoted == "/":
        return OUTPUT / dir_index
    relative = unquoted.removeprefix("/")
    if relative.endswith("/"):
        return OUTPUT / relative / dir_index
    else:
        return OUTPUT / relative


def to_url_path(path: ginjarator.paths.Filesystem | str) -> str:
    """Returns a url path from an fs path."""
    path = ginjarator.paths.Filesystem(path)
    if not path.is_relative_to(OUTPUT):
        raise ValueError(f"{str(path)!r} is not in {str(OUTPUT)!r}")
    relative = path.relative_to(OUTPUT)
    if relative.name in DIR_INDEXES:
        if len(relative.parts) == 1:
            unquoted = "/"
        else:
            unquoted = f"/{relative.parent}/"
    else:
        unquoted = f"/{relative}"
    return urllib.parse.quote(unquoted)
