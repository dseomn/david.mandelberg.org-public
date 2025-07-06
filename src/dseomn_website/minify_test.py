# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from dseomn_website import minify


def test_html() -> None:
    assert minify.html("<p>foo</p>\n") == "<p>foo"


def test_xml() -> None:
    assert minify.xml("<foo />\n") == "<foo/>"
