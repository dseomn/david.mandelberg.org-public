# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from email import headerregistry
import http
import pathlib
from typing import cast
import urllib.parse

import ginjarator
import pytest
import requests

from dseomn_website import paths

_BASE = "http://localhost:19265"

pytestmark = pytest.mark.output


@pytest.mark.parametrize(
    "url_path",
    sorted(
        paths.to_url_path(ginjarator.paths.Filesystem(path))
        for path in pathlib.Path(paths.OUTPUT).glob("**/*")
        if path.is_file() and path != paths.OUTPUT / ".htaccess"
    ),
)
def test_all(url_path: str) -> None:
    header_registry = headerregistry.HeaderRegistry()

    response = requests.get(urllib.parse.urljoin(_BASE, url_path))

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
