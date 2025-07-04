# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from dseomn_website import lint


@pytest.mark.parametrize(
    "fragments",
    (
        "<script></script>",
        "<p><script></script></p>",
        "<p></p><script></script>",
        "<!-- comment -->",
        '<?xml version="1.0"?>',
        "<p id=foo></p>",
    ),
)
def test_comment_error(fragments: str) -> None:
    with pytest.raises(ValueError, match="Not allowed"):
        lint.comment(fragments)


@pytest.mark.parametrize(
    "fragments",
    (
        '<p><a href="foo">foo</a></p>',
        "<p>foo</p><p>bar</p>",
        "<p>&amp;</p>",
    ),
)
def test_comment(fragments: str) -> None:
    lint.comment(fragments)


@pytest.mark.parametrize(
    "html,error_regex",
    (
        ("<h1>foo</h1>", r"does not have a heading class"),
        ("<h2>foo</h2>", r"does not have a heading class"),
        ("<h3>foo</h3>", r"does not have a heading class"),
        ("<h4>foo</h4>", r"does not have a heading class"),
        ("<h5>foo</h5>", r"does not have a heading class"),
        ("<h6>foo</h6>", r"does not have a heading class"),
        (
            "<!doctype html><body><h1>foo</h1></body>",
            r"does not have a heading class",
        ),
        (
            "<!doctype html><body><h2>foo</h2></body>",
            r"does not have a heading class",
        ),
        (
            "<!doctype html><body><h3>foo</h3></body>",
            r"does not have a heading class",
        ),
        (
            "<!doctype html><body><h4>foo</h4></body>",
            r"does not have a heading class",
        ),
        (
            "<!doctype html><body><h5>foo</h5></body>",
            r"does not have a heading class",
        ),
        (
            "<!doctype html><body><h6>foo</h6></body>",
            r"does not have a heading class",
        ),
        ('<h1 class="h1 h2">foo</h1>', r"has multiple heading classes"),
        (
            '<div><article id="foo"><div><p id="bar"></div></article></div>',
            r"its id does not start with",
        ),
        (
            "".join(
                (
                    '<article id="foo">',
                    '<article id="foo-bar" class="comment">',
                    '<p id="quux">',
                    "</article>",
                    "</article>",
                )
            ),
            r"its id does not start with",
        ),
    ),
)
def test_html_error(html: str, error_regex: str) -> None:
    with pytest.raises(ValueError, match=error_regex):
        lint.html(html)


@pytest.mark.parametrize(
    "html",
    (
        '<h2 class="h1">foo</h2>',
        '<div><article id="foo"><div><p id="foo-bar"></div></article></div>',
        '<div><article><div><p id="bar"></div></article></div>',
        "".join(
            (
                '<article id="foo">',
                '<article id="foo-bar">',
                '<p id="foo-bar-quux">',
                "</article>",
                "</article>",
            )
        ),
        "".join(
            (
                '<article id="foo">',
                '<article id="foo-bar" class="comment">',
                '<p id="foo-quux">',
                "</article>",
                "</article>",
            )
        ),
    ),
)
def test_html(html: str) -> None:
    lint.html(html)
