# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from email import headerregistry
import http
import itertools
import pathlib
from typing import cast
import urllib.parse

import ginjarator
import lxml.html
import pytest
import requests

from dseomn_website import fonts
from dseomn_website import metadata
from dseomn_website import paths

_BASE = "http://localhost:19265"

pytestmark = pytest.mark.output


_OUTPUT_PATHS = frozenset(
    path
    for path in pathlib.Path(paths.OUTPUT).glob("**/*")
    if path.is_file()
    and path.name != ".htaccess"
    and path.suffix != ".var"
    and not path.suffix.startswith(".c-e-")
)
# One path per suffix.
_OUTPUT_PATH_EXAMPLES = frozenset(
    next(iter(group))
    for _, group in itertools.groupby(
        sorted(_OUTPUT_PATHS, key=lambda path: (path.suffix, path)),
        key=lambda path: path.suffix,
    )
)
_OUTPUT_PATH_PARAMS = tuple(
    pytest.param(
        path,
        marks=() if path in _OUTPUT_PATH_EXAMPLES else (pytest.mark.slow,),
        id=str(path),
    )
    for path in sorted(_OUTPUT_PATHS)
)


def test_pages_match_metadata() -> None:
    with ginjarator.testing.api_for_scan():
        assert {
            paths.to_url_path(ginjarator.paths.Filesystem(path))
            for path in pathlib.Path(paths.OUTPUT).glob("**/*.html")
        } == {page.url_path for page in metadata.Page.all()}


@pytest.mark.parametrize("path", _OUTPUT_PATH_PARAMS)
def test_ok(path: pathlib.Path) -> None:
    url_path = paths.to_url_path(ginjarator.paths.Filesystem(path))
    header_registry = headerregistry.HeaderRegistry()

    response = requests.get(urllib.parse.urljoin(_BASE, url_path))

    assert not response.history
    assert response.status_code == http.HTTPStatus.OK

    assert "content-type" in response.headers
    content_type = cast(
        headerregistry.ContentTypeHeader,
        header_registry(
            "content-type",
            response.headers["content-type"],
        ),
    )
    if content_type.maintype == "text":
        assert content_type.params["charset"] == "utf-8"
    else:
        assert "charset" not in content_type.params

    assert response.content == path.read_bytes()


@pytest.mark.parametrize(
    "request_url_path,response_url_path",
    (
        ("/index.html", "/"),
        ("/about/index.html", "/about/"),
        ("/feed/index.atom", "/feed/"),
        ("/2025/04/01/placeholder/", "/2025/04/02/placeholder/"),
    ),
)
def test_redirect(request_url_path: str, response_url_path: str) -> None:
    response = requests.get(urllib.parse.urljoin(_BASE, request_url_path))

    assert len(response.history) == 1
    assert response.url == urllib.parse.urljoin(_BASE, response_url_path)
    assert response.status_code == http.HTTPStatus.OK


@pytest.mark.parametrize(
    "url_path,expected",
    (
        ("/.htaccess", http.HTTPStatus.FORBIDDEN),
        ("/does-not-exist", http.HTTPStatus.NOT_FOUND),
        (
            # Valid index filename, but file does not exist, so no redirect.
            "/index.atom",
            http.HTTPStatus.NOT_FOUND,
        ),
    ),
)
def test_error(url_path: str, expected: http.HTTPStatus) -> None:
    response = requests.get(urllib.parse.urljoin(_BASE, url_path))

    assert not response.history
    assert response.status_code == expected
    assert (
        response.text
        == pathlib.Path(
            paths.OUTPUT / f"errors/{expected.value}/index.html"
        ).read_text()
    )


def test_font_coverage() -> None:
    actual_code_points = set()
    for html_path in pathlib.Path(paths.OUTPUT).glob("**/*.html"):
        document = lxml.html.document_fromstring(html_path.read_text())
        actual_code_points.update(document.text_content())
        for node in document.iter():
            for attr_value in node.values():
                # Most attribute values aren't rendered as text, but some like
                # img.alt are.
                actual_code_points.update(attr_value)
    for css_path in pathlib.Path(paths.OUTPUT).glob("**/*.css"):
        # The content property can produce text to be rendered.
        actual_code_points.update(css_path.read_text())

    assert set(fonts.CODE_POINTS) >= actual_code_points
