# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Iterable, Sequence
import dataclasses
import functools
import itertools

import ginjarator

from dseomn_website import paths


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
    "Noto Sans Math",
    "Noto Color Emoji",
)
MONOSPACE_FAMILIES_CSS = _families_to_css(MONOSPACE_FAMILIES, "monospace")
ALL_FAMILY_SEQUENCES = (SERIF_FAMILIES, MONOSPACE_FAMILIES)
ALL_FAMILIES = tuple(
    sorted(set(itertools.chain.from_iterable(ALL_FAMILY_SEQUENCES)))
)


def _code_point_range(start: str, end: str) -> Iterable[str]:
    yield from map(chr, range(ord(start), ord(end) + 1))


# All code points that the fonts should cover. When changing this, run slow
# tests.
CODE_POINTS = (
    "\n",
    " ",
    "!",
    '"',
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    "+",
    ",",
    "-",
    ".",
    "/",
    *_code_point_range("0", "9"),
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    *_code_point_range("A", "Z"),
    "[",
    "\\",
    "]",
    "^",
    "_",
    *_code_point_range("a", "z"),
    "{",
    "}",
    "\N{NO-BREAK SPACE}",
    "°",
    "×",
    "ä",
    "å",
    "ê",
    "ö",
    "ø",
    "ƒ",
    "–",
    "—",
    "‘",
    "’",
    "“",
    "”",
    "…",
    "⁄",
    "™",
    "←",
    "→",
    "∕",
    "\N{VARIATION SELECTOR-16}",
    "🏷",
    "👤",
    "📅",
)

CODE_POINTS_BY_FAMILY = {
    "Noto Color Emoji": (
        " ",
        "#",
        "*",
        *_code_point_range("0", "9"),
        "™",
        "🏷",
        "👤",
        "📅",
    ),
    "Noto Sans Math": (
        " ",
        "!",
        '"',
        "#",
        "$",
        "%",
        "&",
        "'",
        "(",
        ")",
        "*",
        "+",
        ",",
        "-",
        ".",
        "/",
        *_code_point_range("0", "9"),
        ":",
        ";",
        "<",
        "=",
        ">",
        "?",
        "@",
        *_code_point_range("A", "Z"),
        "[",
        "\\",
        "]",
        "^",
        "_",
        *_code_point_range("a", "z"),
        "{",
        "}",
        "\N{NO-BREAK SPACE}",
        "°",
        "×",
        "—",
        "‘",
        "’",
        "“",
        "”",
        "…",
        "⁄",
        "←",
        "→",
        "∕",
    ),
    "Noto Sans Mono": (
        " ",
        "!",
        '"',
        "#",
        "$",
        "%",
        "&",
        "'",
        "(",
        ")",
        "*",
        "+",
        ",",
        "-",
        ".",
        "/",
        *_code_point_range("0", "9"),
        ":",
        ";",
        "<",
        "=",
        ">",
        "?",
        "@",
        *_code_point_range("A", "Z"),
        "[",
        "\\",
        "]",
        "^",
        "_",
        *_code_point_range("a", "z"),
        "{",
        "}",
        "\N{NO-BREAK SPACE}",
        "°",
        "×",
        "ä",
        "å",
        "ê",
        "ö",
        "ø",
        "ƒ",
        "–",
        "—",
        "‘",
        "’",
        "“",
        "”",
        "…",
        "⁄",
        "™",
        "←",
        "→",
    ),
    "Noto Serif": (
        " ",
        "!",
        '"',
        "#",
        "$",
        "%",
        "&",
        "'",
        "(",
        ")",
        "*",
        "+",
        ",",
        "-",
        ".",
        "/",
        *_code_point_range("0", "9"),
        ":",
        ";",
        "<",
        "=",
        ">",
        "?",
        "@",
        *_code_point_range("A", "Z"),
        "[",
        "\\",
        "]",
        "^",
        "_",
        *_code_point_range("a", "z"),
        "{",
        "}",
        "\N{NO-BREAK SPACE}",
        "°",
        "×",
        "ä",
        "å",
        "ê",
        "ö",
        "ø",
        "ƒ",
        "–",
        "—",
        "‘",
        "’",
        "“",
        "”",
        "…",
        "⁄",
        "™",
    ),
}


@dataclasses.dataclass(frozen=True, kw_only=True)
class Font:
    source: ginjarator.paths.Filesystem
    family: str
    style: str
    weight: str

    @functools.cached_property
    def unicodes(self) -> str:
        """Value for passing to fonttools subset --unicodes."""
        return ",".join(
            f"{ord(code_point):x}"
            for code_point in CODE_POINTS_BY_FAMILY[self.family]
        )

    @functools.cached_property
    def work_path(self) -> ginjarator.paths.Filesystem:
        return paths.work(self.source.parent) / f"{self.source.stem}.woff2"

    @functools.cached_property
    def url_path(self) -> str | None:
        output_path = ginjarator.api().fs.read_text(
            self.work_path.with_suffix(
                f"{self.work_path.suffix}.cache-buster-output-filename"
            )
        )
        if output_path is None:
            return None
        return paths.to_url_path(output_path)


_PRIVATE_THIRD_PARTY = paths.PRIVATE / "third_party"
FONTS = (
    Font(
        source=(
            _PRIVATE_THIRD_PARTY / "Noto_Color_Emoji/NotoColorEmoji-Regular.ttf"
        ),
        family="Noto Color Emoji",
        style="normal",
        weight="400",
    ),
    Font(
        source=(
            _PRIVATE_THIRD_PARTY / "Noto_Sans_Math/NotoSansMath-Regular.ttf"
        ),
        family="Noto Sans Math",
        style="normal",
        weight="400",
    ),
    Font(
        source=(
            _PRIVATE_THIRD_PARTY
            / "Noto_Sans_Mono/NotoSansMono-VariableFont_wdth,wght.ttf"
        ),
        family="Noto Sans Mono",
        style="normal",
        weight="100 900",
    ),
    Font(
        source=(
            _PRIVATE_THIRD_PARTY
            / "Noto_Serif/NotoSerif-Italic-VariableFont_wdth,wght.ttf"
        ),
        family="Noto Serif",
        style="italic",
        weight="100 900",
    ),
    Font(
        source=(
            _PRIVATE_THIRD_PARTY
            / "Noto_Serif/NotoSerif-VariableFont_wdth,wght.ttf"
        ),
        family="Noto Serif",
        style="normal",
        weight="100 900",
    ),
)
