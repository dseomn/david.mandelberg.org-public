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


def _output_path_example_key(path: pathlib.Path) -> object:
    """Returns a key to group output paths by and pick one from each group."""
    return (path.suffix, path.name in paths.DIR_INDEXES)


_OUTPUT_PATHS = frozenset(
    path
    for path in pathlib.Path(paths.OUTPUT).glob("**/*")
    if path.is_file()
    and path.name != ".htaccess"
    and path.suffix != ".var"
    and not path.suffix.startswith(".c-e-")
)
_OUTPUT_PATH_EXAMPLES = frozenset(
    next(iter(group))
    for _, group in itertools.groupby(
        sorted(
            _OUTPUT_PATHS,
            key=lambda path: (_output_path_example_key(path), path),
        ),
        key=_output_path_example_key,
    )
)


def _encoded_path(
    base_path: pathlib.Path, encoding: str | None
) -> pathlib.Path:
    if encoding is None:
        return base_path
    else:
        return base_path.parent / f"{base_path.name}.c-e-{encoding}"


def test_pages_match_metadata() -> None:
    with ginjarator.testing.api_for_scan():
        assert {
            paths.to_url_path(ginjarator.paths.Filesystem(path))
            for path in pathlib.Path(paths.OUTPUT).glob("**/*.html")
        } == {page.url_path for page in metadata.Page.all()}


@pytest.mark.parametrize(
    "url_path,expected_status_code,expected_content_path",
    (
        *(
            pytest.param(
                paths.to_url_path(ginjarator.paths.Filesystem(path)),
                http.HTTPStatus.OK,
                path,
                marks=(
                    () if path in _OUTPUT_PATH_EXAMPLES else (pytest.mark.slow,)
                ),
            )
            for path in sorted(_OUTPUT_PATHS)
        ),
        (
            "/.htaccess",
            http.HTTPStatus.FORBIDDEN,
            pathlib.Path("output/errors/403/index.html"),
        ),
        (
            "/does-not-exist",
            http.HTTPStatus.NOT_FOUND,
            pathlib.Path("output/errors/404/index.html"),
        ),
        (
            # Valid index filename, but file does not exist, so no redirect.
            "/index.atom",
            http.HTTPStatus.NOT_FOUND,
            pathlib.Path("output/errors/404/index.html"),
        ),
        (
            "/licenses/Noto_Serif_OFL.txt.c-e-invalid",
            http.HTTPStatus.NOT_FOUND,
            pathlib.Path("output/errors/404/index.html"),
        ),
    ),
)
@pytest.mark.parametrize(
    "accept,accept_encoding,expected_content_encoding",
    (
        (None, None, (None,)),
        ("*/*", None, (None,)),
        ("*/*", "br", ("br",)),
        ("*/*", "gzip", ("gzip",)),
        ("*/*", "zstd", ("zstd",)),
        (
            "*/*",
            # Roughly reverse size order, to make sure that the smallest is
            # picked, not the first listed.
            "gzip, zstd, br",
            ("gzip", "zstd", "br"),
        ),
        # TODO: https://bz.apache.org/bugzilla/show_bug.cgi?id=69775 - Test with
        # a non-matching accept header.
        ("*/*", "invalid", (None,)),
    ),
)
def test_final_response(
    url_path: str,
    accept: str | None,
    accept_encoding: str | None,
    expected_status_code: http.HTTPStatus,
    expected_content_encoding: tuple[str | None, ...],
    expected_content_path: pathlib.Path,
) -> None:
    compressible = expected_content_path.suffix not in (
        ".jpg",
        ".png",
        ".woff2",
    )
    header_registry = headerregistry.HeaderRegistry()

    response = requests.get(
        urllib.parse.urljoin(_BASE, url_path),
        headers={
            "accept": accept,
            "accept-encoding": accept_encoding,
        },
    )

    assert not response.history
    assert response.status_code == expected_status_code

    assert "content-location" not in response.headers
    content_encoding = response.headers.get("content-encoding")
    if "vary" in response.headers:
        vary = tuple(
            header.casefold().strip()
            for header in response.headers["vary"].split(",")
        )
    else:
        vary = ()
    if compressible:
        assert content_encoding in expected_content_encoding
        assert "accept-encoding" in vary
    else:
        assert content_encoding is None
        assert "accept-encoding" not in vary

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

    assert response.content == expected_content_path.read_bytes()
    # I don't see a way to get the encoded content from requests, so this uses
    # the content-length instead to assert that the right encoded data was sent.
    expected_encoding_sizes = {
        encoding: _encoded_path(expected_content_path, encoding).stat().st_size
        for encoding in (expected_content_encoding if compressible else (None,))
    }
    actual_encoding_size = int(response.headers["content-length"])
    assert actual_encoding_size == expected_encoding_sizes[content_encoding]
    assert actual_encoding_size == min(expected_encoding_sizes.values())


@pytest.mark.parametrize(
    "request_url_path,response_url_path",
    (
        ("/index.html", "/"),
        ("/index.html.c-e-br", "/"),
        ("/index.html.c-e-gzip", "/"),
        ("/index.html.c-e-zstd", "/"),
        ("/index.html.var", "/"),
        ("/about/index.html", "/about/"),
        ("/feed/index.atom", "/feed/"),
        ("/2025/04/01/placeholder/", "/2025/04/02/placeholder/"),
        ("/licenses/Noto_Serif_OFL.txt.c-e-br", "/licenses/Noto_Serif_OFL.txt"),
        (
            "/licenses/Noto_Serif_OFL.txt.c-e-gzip",
            "/licenses/Noto_Serif_OFL.txt",
        ),
        (
            "/licenses/Noto_Serif_OFL.txt.c-e-zstd",
            "/licenses/Noto_Serif_OFL.txt",
        ),
        ("/licenses/Noto_Serif_OFL.txt.var", "/licenses/Noto_Serif_OFL.txt"),
    ),
)
def test_redirect(request_url_path: str, response_url_path: str) -> None:
    response = requests.get(urllib.parse.urljoin(_BASE, request_url_path))

    assert len(response.history) == 1
    assert response.url == urllib.parse.urljoin(_BASE, response_url_path)
    assert response.status_code == http.HTTPStatus.OK


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
