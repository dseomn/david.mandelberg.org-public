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


def lint(html: str, /) -> None:
    """Raises an exception if the html has issues with its headings."""
    parsed = lxml.html.fromstring(html)
    levels = {f"h{n}" for n in range(1, 7)}
    for element in parsed.cssselect(",".join(levels)):
        heading_classes = set(element.classes) & levels
        if not heading_classes:
            raise ValueError(f"{element.tag} does not have a heading class.")
        elif len(heading_classes) > 1:
            raise ValueError(
                f"{element.tag} has multiple heading classes: {heading_classes}"
            )
