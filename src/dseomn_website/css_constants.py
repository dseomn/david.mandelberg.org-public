# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
import itertools

# https://developer.mozilla.org/en-US/docs/Web/CSS/font-size says "by default
# 1em is equivalent to 16px". The purpose of this constant is not to override
# that, but to give default conversions from em to px for resizing images that
# will be layed out with em units.
PIXELS_PER_EM = 16

MAIN_COLUMN_MAX_INLINE_SIZE_EM = 60
MAIN_COLUMN_MAX_INLINE_SIZE = f"{MAIN_COLUMN_MAX_INLINE_SIZE_EM}em"
MAIN_COLUMN_PADDING_INLINE_EM = 1
MAIN_COLUMN_PADDING_INLINE = f"{MAIN_COLUMN_PADDING_INLINE_EM}em"
MAIN_COLUMN_CONTENTS_INLINE_SIZE = (
    "min("
    f"100vi - 2 * {MAIN_COLUMN_PADDING_INLINE}, "
    f"{MAIN_COLUMN_MAX_INLINE_SIZE}"
    ")"
)

FLOAT_MAX_INLINE_SIZE_EM = 20
FLOAT_MAX_INLINE_SIZE = f"{FLOAT_MAX_INLINE_SIZE_EM}em"
FLOAT_CONTENTS_INLINE_SIZE = (
    f"min({MAIN_COLUMN_CONTENTS_INLINE_SIZE}, {FLOAT_MAX_INLINE_SIZE})"
)

GALLERY_ITEM_MAX_BLOCK_SIZE_EM = 12
GALLERY_ITEM_MAX_BLOCK_SIZE = f"{GALLERY_ITEM_MAX_BLOCK_SIZE_EM}em"


def _font_families_to_css(font_families: Sequence[str], generic: str) -> str:
    return ", ".join(
        (
            *(f'"{font_family}"' for font_family in font_families),
            generic,
        )
    )


SERIF_FONT_FAMILIES = (
    "Noto Serif",
    "Noto Sans Math",
    "Noto Color Emoji",
)
SERIF_FONT_FAMILIES_CSS = _font_families_to_css(SERIF_FONT_FAMILIES, "serif")
MONOSPACE_FONT_FAMILIES = (
    "Noto Sans Mono",
    "Noto Color Emoji",
)
MONOSPACE_FONT_FAMILIES_CSS = _font_families_to_css(
    MONOSPACE_FONT_FAMILIES,
    "monospace",
)
ALL_FONT_FAMILY_SEQUENCES = (SERIF_FONT_FAMILIES, MONOSPACE_FONT_FAMILIES)
ALL_FONT_FAMILIES = tuple(
    sorted(set(itertools.chain.from_iterable(ALL_FONT_FAMILY_SEQUENCES)))
)
