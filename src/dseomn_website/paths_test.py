# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

import pytest

from dseomn_website import paths


def test_from_url_path_error() -> None:
    with pytest.raises(NotImplementedError, match="Relative url paths"):
        paths.from_url_path("foo")


@pytest.mark.parametrize(
    "url_path,expected",
    (
        ("/", "output/index.html"),
        ("/foo/", "output/foo/index.html"),
        ("/foo", "output/foo"),
    ),
)
def test_from_url_path(url_path: str, expected: str) -> None:
    assert paths.from_url_path(url_path) == pathlib.PurePath(expected)


def test_to_url_path_error() -> None:
    with pytest.raises(ValueError, match="not in"):
        paths.to_url_path("foo")


@pytest.mark.parametrize(
    "path,expected",
    (
        ("output/index.html", "/"),
        ("output/foo/index.html", "/foo/"),
        ("output/foo", "/foo"),
    ),
)
def test_to_url_path(path: str, expected: str) -> None:
    assert paths.to_url_path(path) == expected
