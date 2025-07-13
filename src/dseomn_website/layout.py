# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

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
