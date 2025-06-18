# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

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
