# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping

import pytest

from dseomn_website import iri


@pytest.mark.parametrize(
    "to,headers,body,expected",
    (
        ("user@example.com", None, None, "mailto:user@example.com"),
        ("user%name@example.com", None, None, "mailto:user%25name@example.com"),
        (
            "user@example.com",
            {"subject": "kumquats are a fruit"},
            None,
            "mailto:user@example.com?subject=kumquats%20are%20a%20fruit",
        ),
        (
            "user@example.com",
            None,
            "foo\nbar",
            "mailto:user@example.com?body=foo%0D%0Abar%0D%0A",
        ),
    ),
)
def test_mailto(
    to: str,
    headers: Mapping[str, str] | None,
    body: str | None,
    expected: str,
) -> None:
    assert iri.mailto(to, headers=headers, body=body) == expected
