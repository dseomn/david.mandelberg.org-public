# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import ginjarator
import pytest

from dseomn_website import paths


@pytest.mark.parametrize(
    "source,expected",
    (
        ("standalone/about", "work/standalone/about"),
        ("../private/standalone/about", "work/standalone/about"),
    ),
)
def test_work(source: str, expected: str) -> None:
    assert paths.work(source) == ginjarator.paths.Filesystem(expected)


@pytest.mark.parametrize(
    "url_path,dir_index,error_class,error_regex",
    (
        ("/", "not-an-index", ValueError, r"Invalid dir_index"),
        ("foo", "index.html", NotImplementedError, r"Relative url paths"),
    ),
)
def test_from_url_path_error(
    url_path: str,
    dir_index: str,
    error_class: type[Exception],
    error_regex: str,
) -> None:
    with pytest.raises(error_class, match=error_regex):
        paths.from_url_path(url_path, dir_index=dir_index)


@pytest.mark.parametrize(
    "url_path,expected",
    (
        ("/", "output/index.html"),
        ("/foo/", "output/foo/index.html"),
        ("/foo", "output/foo"),
    ),
)
def test_from_url_path(url_path: str, expected: str) -> None:
    assert paths.from_url_path(url_path) == ginjarator.paths.Filesystem(
        expected
    )


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
