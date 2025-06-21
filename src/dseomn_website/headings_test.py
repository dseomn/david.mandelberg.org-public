# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from dseomn_website import headings


@pytest.mark.parametrize(
    "html,offset,error_regex",
    (
        ("<h1>foo</h1>", -1, r"adjust h1 by offset -1"),
        ("<h6>foo</h6>", 1, r"adjust h6 by offset 1"),
    ),
)
def test_article_error(html: str, offset: int, error_regex: str) -> None:
    with pytest.raises(ValueError, match=error_regex):
        headings.article(html, offset=offset)


@pytest.mark.parametrize(
    "html,offset,expected",
    (
        (
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
            ),
            0,
            "".join(
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
            ),
        ),
        ("<h1>foo</h1>", 1, '<h2 class="h1">foo</h2>'),
    ),
)
def test_article(html: str, offset: int, expected: str) -> None:
    assert headings.article(html, offset=offset) == expected
