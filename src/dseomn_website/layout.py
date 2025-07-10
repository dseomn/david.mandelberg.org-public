# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

# When changing these values, also check if the image sizes in media.py need
# changing too.
MAIN_COLUMN_MAX_INLINE_SIZE = "60em"
MAIN_COLUMN_PADDING_INLINE = "1em"
MAIN_COLUMN_CONTENTS_INLINE_SIZE = (
    "min("
    f"100vi - 2 * {MAIN_COLUMN_PADDING_INLINE}, "
    f"{MAIN_COLUMN_MAX_INLINE_SIZE}"
    ")"
)
FLOAT_MAX_INLINE_SIZE = "20em"
FLOAT_CONTENTS_INLINE_SIZE = (
    f"min({MAIN_COLUMN_CONTENTS_INLINE_SIZE}, {FLOAT_MAX_INLINE_SIZE})"
)
