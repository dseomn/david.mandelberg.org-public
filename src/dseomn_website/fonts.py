# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0


from collections.abc import Sequence
import itertools


def _families_to_css(families: Sequence[str], generic: str) -> str:
    return ", ".join(
        (
            *(f'"{family}"' for family in families),
            generic,
        )
    )


SERIF_FAMILIES = (
    "Noto Serif",
    "Noto Sans Math",
    "Noto Color Emoji",
)
SERIF_FAMILIES_CSS = _families_to_css(SERIF_FAMILIES, "serif")
MONOSPACE_FAMILIES = (
    "Noto Sans Mono",
    "Noto Color Emoji",
)
MONOSPACE_FAMILIES_CSS = _families_to_css(MONOSPACE_FAMILIES, "monospace")
ALL_FAMILY_SEQUENCES = (SERIF_FAMILIES, MONOSPACE_FAMILIES)
ALL_FAMILIES = tuple(
    sorted(set(itertools.chain.from_iterable(ALL_FAMILY_SEQUENCES)))
)
