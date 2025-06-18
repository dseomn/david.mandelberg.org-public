# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import lxml.html


def article(html: str, /) -> str:
    """Adjusts the headings of an <article>."""
    parsed = lxml.html.fragment_fromstring(html)
    for heading_level in range(1, 7):
        for element in parsed.cssselect(f"h{heading_level}"):
            element.classes.add(f"h{heading_level}")
    return lxml.html.tostring(parsed, encoding="unicode")
