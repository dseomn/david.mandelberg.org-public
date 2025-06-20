# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Iterable


def nav(
    *,
    current: int,
    total: int,
    show_either_side: int = 2,
) -> Iterable[int | None]:
    """Yields page numbers for a navigation list.

    Args:
        current: Current page number, 1-indexed.
        total: Total number of pages.
        show_either_side: How many pages to show on either side of current.

    Yields:
        Either a page number for the list, or None for an ellipsis in a gap
        between page numbers.
    """
    for page in range(1, total + 1):
        if page in (1, total):
            yield page
        elif abs(page - current) <= show_either_side:
            yield page
        elif page in (2, total - 1):
            # First page of initial ellipsis, or last page of final ellipsis.
            if abs(page - current) == show_either_side + 1:
                # The ellipsis is only one page, so just show that page instead
                # of an ellipsis.
                yield page
            else:
                yield None
