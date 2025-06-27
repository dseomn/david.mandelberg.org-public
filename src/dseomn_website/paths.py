# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Collection

import ginjarator

OUTPUT = ginjarator.paths.Filesystem("output")
DIR_INDEXES = (
    "index.html",
    "index.xml",
)


def from_url_path(
    url_path: str,
    *,
    dir_index: str = "index.html",
) -> ginjarator.paths.Filesystem:
    """Returns an fs path from a url path."""
    if dir_index not in DIR_INDEXES:
        raise ValueError(
            f"Invalid dir_index {dir_index!r}, allowed values are: "
            f"{DIR_INDEXES}"
        )
    if not url_path.startswith("/"):
        raise NotImplementedError("Relative url paths are not supported.")
    elif url_path == "/":
        return OUTPUT / dir_index
    relative = url_path.removeprefix("/")
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
            return "/"
        else:
            return f"/{relative.parent}/"
    else:
        return f"/{relative}"
