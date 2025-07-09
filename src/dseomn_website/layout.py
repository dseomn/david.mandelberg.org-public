# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

# When changing these values, also check if the image sizes in media.py need
# changing too.
MAIN_COLUMN_MAX_INLINE_SIZE = "60em"
MAIN_COLUMN_PADDING_INLINE = "1em"
MAIN_COLUMN_CONTENTS_INLINE_SIZE = (
    "calc("
    f"min(100vi, {MAIN_COLUMN_MAX_INLINE_SIZE}) "
    f"- 2 * {MAIN_COLUMN_PADDING_INLINE}"
    ")"
)
