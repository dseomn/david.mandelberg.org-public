# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping
import urllib.parse


def mailto(
    to: str,
    *,
    headers: Mapping[str, str] | None = None,
    body: str | None = None,
) -> str:
    # https://datatracker.ietf.org/doc/html/rfc6068
    query = dict[str, str]()
    if headers is not None:
        query.update(headers)
    if body is not None:
        query["body"] = "".join(f"{line}\r\n" for line in body.splitlines())
    return urllib.parse.SplitResult(
        scheme="mailto",
        netloc="",
        path=urllib.parse.quote(to, safe="@"),
        query=urllib.parse.urlencode(
            query,
            safe="",
            quote_via=urllib.parse.quote,
        ),
        fragment="",
    ).geturl()
