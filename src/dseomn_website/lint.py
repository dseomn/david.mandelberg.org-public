# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import lxml.html


def _headings(parsed: Any) -> None:
    levels = {f"h{n}" for n in range(1, 7)}
    for element in parsed.cssselect(",".join(levels)):
        heading_classes = set(element.classes) & levels
        if not heading_classes:
            raise ValueError(f"{element.tag} does not have a heading class.")
        elif len(heading_classes) > 1:
            raise ValueError(
                f"{element.tag} has multiple heading classes: {heading_classes}"
            )


def _ids(parsed: Any) -> None:
    # Blog posts can be embedded in lists with other posts. To prevent ID
    # collisions, make sure that every ID in a blog post has the blog post's own
    # ID as a prefix.
    for article in parsed.cssselect("article[id]"):
        article_id = article.get("id")
        for descendant in article.cssselect("[id]"):
            descendant_id = descendant.get("id")
            if descendant is not article and not descendant_id.startswith(
                f"{article_id}-"
            ):
                raise ValueError(
                    f"{descendant_id!r} is descendant of {article_id!r}, but "
                    "its id does not start with that."
                )


def html(document_or_fragment: str, /) -> None:
    """Raises an exception if the html has issues."""
    parsed = lxml.html.fromstring(document_or_fragment)
    _headings(parsed)
    _ids(parsed)
