# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import http
import pathlib

import pytest
import requests

from dseomn_website import paths

_BASE = "http://localhost:19265"

pytestmark = pytest.mark.output


@pytest.mark.parametrize(
    "url_path",
    sorted(
        paths.to_url_path(path)
        for path in pathlib.Path(paths.OUTPUT).glob("**/*")
        if path.is_file() and path != paths.OUTPUT / ".htaccess"
    ),
)
def test_all(url_path: str) -> None:
    response = requests.get(_BASE + url_path)

    assert response.status_code == http.HTTPStatus.OK
    assert "content-type" in response.headers
