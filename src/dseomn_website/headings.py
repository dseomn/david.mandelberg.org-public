# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import lxml.html


def article(
    html: str,
    /,
    offset: int = 0,
) -> str:
    """Adjusts the headings of an <article>."""
    parsed = lxml.html.fragment_fromstring(html)
    headings_by_level = {
        level: tuple(parsed.cssselect(f"h{level}")) for level in range(1, 7)
    }
    for heading_level, elements in headings_by_level.items():
        if not elements:
            continue
        if not 1 <= heading_level + offset <= 6:
            raise ValueError(
                f"Can't adjust h{heading_level} by offset {offset}."
            )
        for element in elements:
            element.tag = f"h{heading_level + offset}"
            element.classes.add(f"h{heading_level}")
    return lxml.html.tostring(parsed, encoding="unicode")
