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
