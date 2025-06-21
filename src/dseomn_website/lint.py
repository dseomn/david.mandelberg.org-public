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


def html(document_or_fragment: str, /) -> None:
    """Raises an exception if the html has issues."""
    parsed = lxml.html.fromstring(document_or_fragment)
    _headings(parsed)
