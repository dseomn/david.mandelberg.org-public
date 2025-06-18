# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

OUTPUT = pathlib.PurePath("output")


def from_url_path(
    url_path: str,
    *,
    dir_index: str = "index.html",
) -> pathlib.PurePath:
    """Returns an fs path from a url path."""
    if not url_path.startswith("/"):
        raise NotImplementedError("Relative url paths are not supported.")
    elif url_path == "/":
        return OUTPUT / dir_index
    relative = url_path.removeprefix("/")
    if relative.endswith("/"):
        return OUTPUT / relative / dir_index
    else:
        return OUTPUT / relative
