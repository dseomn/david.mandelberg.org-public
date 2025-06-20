# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from dseomn_website import pagination


@pytest.mark.parametrize(
    "current,total,expected",
    (
        (1, 1, [1]),
        (1, 5, [1, 2, 3, 4, 5]),
        (5, 5, [1, 2, 3, 4, 5]),
        (1, 6, [1, 2, 3, None, 6]),
        (6, 6, [1, None, 4, 5, 6]),
        (4, 7, [1, 2, 3, 4, 5, 6, 7]),
        (5, 9, [1, 2, 3, 4, 5, 6, 7, 8, 9]),
        (6, 11, [1, None, 4, 5, 6, 7, 8, None, 11]),
    ),
)
def test_nav(current: int, total: int, expected: list[int | None]) -> None:
    assert list(pagination.nav(current=current, total=total)) == expected
