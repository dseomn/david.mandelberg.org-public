# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from dseomn_website import headings


def test_article() -> None:
    assert headings.article(
        "".join(
            (
                "<article>",
                "<h1>H 1</h1>",
                "<h2>H 2</h2>",
                "<h3>H 3</h3>",
                "<div>",
                "<h4>H 4</h4>",
                "<h5>H 5</h5>",
                "<h6>H 6</h6>",
                "<p>P</p>",
                "</div>",
                "</article>",
            )
        )
    ) == "".join(
        (
            "<article>",
            '<h1 class="h1">H 1</h1>',
            '<h2 class="h2">H 2</h2>',
            '<h3 class="h3">H 3</h3>',
            "<div>",
            '<h4 class="h4">H 4</h4>',
            '<h5 class="h5">H 5</h5>',
            '<h6 class="h6">H 6</h6>',
            "<p>P</p>",
            "</div>",
            "</article>",
        )
    )


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
    ),
)
def test_lint_error(html: str, error_regex: str) -> None:
    with pytest.raises(ValueError, match=error_regex):
        headings.lint(html)


def test_lint() -> None:
    headings.lint('<h2 class="h1">foo</h2>')
