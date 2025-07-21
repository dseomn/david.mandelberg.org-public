# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import collections
from collections.abc import Sequence
from email import headerregistry
import http
import itertools
import json
import pathlib
import subprocess
from typing import cast
import urllib.parse

import ginjarator
import icu
import lxml.html
import pytest
import requests

from dseomn_website import fonts
from dseomn_website import metadata
from dseomn_website import paths

_BASE = "http://localhost:19265"

pytestmark = pytest.mark.output


def test_pages_match_metadata() -> None:
    with ginjarator.testing.api_for_scan():
        assert {
            paths.to_url_path(ginjarator.paths.Filesystem(path))
            for path in pathlib.Path(paths.OUTPUT).glob("**/*.html")
        } == {page.url_path for page in metadata.Page.all()}


@pytest.mark.parametrize(
    "url_path",
    sorted(
        paths.to_url_path(ginjarator.paths.Filesystem(path))
        for path in pathlib.Path(paths.OUTPUT).glob("**/*")
        if path.is_file() and path != paths.OUTPUT / ".htaccess"
    ),
)
def test_ok(url_path: str) -> None:
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


@pytest.mark.parametrize("fonts_configured", fonts.ALL_FAMILY_SEQUENCES)
def test_font_coverage(
    fonts_configured: Sequence[str],
    tmp_path: pathlib.Path,
) -> None:
    grapheme_clusters = set()
    for html_path in pathlib.Path(paths.OUTPUT).glob("**/*.html"):
        html_text_icu = icu.UnicodeString(
            lxml.html.document_fromstring(html_path.read_text()).text_content()
        )
        grapheme_cluster_iter = icu.BreakIterator.createCharacterInstance(
            icu.Locale.getRoot()
        )
        grapheme_cluster_iter.setText(html_text_icu)
        for start, end in itertools.pairwise(
            itertools.chain((0,), grapheme_cluster_iter)
        ):
            grapheme_clusters.add(str(html_text_icu[start:end]))
    pango_json_path = tmp_path / "pango.json"
    pango_font_description = ",".join(fonts_configured) + " 12"
    subprocess.run(
        (
            "pango-view",
            "--no-display",
            f"--font={pango_font_description}",
            f"--language={metadata.SITE.language}",
            f"--text={''.join(sorted(grapheme_clusters))}",
            f"--serialize-to={pango_json_path}",
        ),
        check=True,
    )
    pango_serialized = json.loads(pango_json_path.read_text())

    texts_by_font_used = collections.defaultdict[str, list[str]](list)
    for line in pango_serialized["output"]["lines"]:
        for run in line["runs"]:
            font_used = run["font"]["description"].removesuffix(" 12")
            texts_by_font_used[font_used].append(run["text"])

    assert texts_by_font_used
    assert not {
        font_used: "".join(texts)
        for font_used, texts in texts_by_font_used.items()
        if font_used not in fonts_configured
    }
