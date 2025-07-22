# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
import io
import itertools
import pathlib
import textwrap

import fontTools.subset
import ginjarator.testing
import pytest

from dseomn_website import fonts


def test_code_points_is_sorted_and_unique() -> None:
    assert list(fonts.CODE_POINTS) == sorted(set(fonts.CODE_POINTS))


def test_code_points_are_code_points() -> None:
    assert not {s for s in fonts.CODE_POINTS if len(s) != 1}


@pytest.mark.parametrize("families", fonts.ALL_FAMILY_SEQUENCES)
def test_code_points_covered_by_family_stack(
    families: Sequence[str],
) -> None:
    coverage_not_necessary = {
        "\n",
        "\N{VARIATION SELECTOR-16}",
    }
    assert (
        set(
            itertools.chain.from_iterable(
                fonts.CODE_POINTS_BY_FAMILY[family] for family in families
            )
        )
        - coverage_not_necessary
        == set(fonts.CODE_POINTS) - coverage_not_necessary
    )


@pytest.mark.parametrize("family", fonts.ALL_FAMILIES)
def test_code_points_by_family_is_sorted_and_unique(family: str) -> None:
    assert list(fonts.CODE_POINTS_BY_FAMILY[family]) == sorted(
        set(fonts.CODE_POINTS_BY_FAMILY[family])
    )


def test_font_scan() -> None:
    font = fonts.Font(
        source=ginjarator.paths.Filesystem(
            "../private/third_party/foo/foo.ttf"
        ),
        family="Foo",
        style="normal",
        weight="400",
    )

    with ginjarator.testing.api_for_scan():
        assert font.work_path == ginjarator.paths.Filesystem(
            "work/third_party/foo/foo.woff2"
        )
        assert font.url_path is None


def test_font_unicodes() -> None:
    font = next(
        iter(font for font in fonts.FONTS if font.family == "Noto Serif")
    )
    assert ord("a") == 0x61
    assert "61" in font.unicodes.split(",")


def test_font_render(tmp_path: pathlib.Path) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["fonts"]
            build_paths = ["work"]
            """
        )
    )
    (tmp_path / "work/fonts").mkdir(parents=True)
    (tmp_path / "work/fonts/foo.woff2.cache-buster-output-filename").write_text(
        "output/assets/foo-some-hash.woff2"
    )
    font = fonts.Font(
        source=ginjarator.paths.Filesystem("fonts/foo.ttf"),
        family="Foo",
        style="normal",
        weight="400",
    )

    with ginjarator.testing.api_for_render(
        root_path=tmp_path,
        dependencies=("work/fonts/foo.woff2.cache-buster-output-filename",),
    ):
        assert font.url_path == "/assets/foo-some-hash.woff2"


def test_fonts_match_families() -> None:
    assert {font.family for font in fonts.FONTS} == set(fonts.ALL_FAMILIES)


def _subset_font(
    font: fonts.Font,
    *,
    options: fontTools.subset.Options,
    text: str,
) -> tuple[frozenset[str], bytes]:
    subset = fontTools.subset.load_font(str(font.source), options=options)
    subsetter = fontTools.subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(subset)
    subset_io = io.BytesIO()
    subset.save(subset_io)
    return (
        frozenset(map(chr, subset.getBestCmap())),
        subset_io.getvalue(),
    )


@pytest.mark.slow
@pytest.mark.parametrize("font", fonts.FONTS)
def test_font_code_points(font: fonts.Font) -> None:
    # If CODE_POINTS_BY_FAMILY has any code points that the font doesn't have,
    # the ignore_missing_unicodes should catch that. If CODE_POINTS_BY_FAMILY is
    # missing any code points that both CODE_POINTS and the font have, the two
    # subsets should be different.
    explicit_subset_code_points, explicit_subset_bytes = _subset_font(
        font,
        options=fontTools.subset.Options(ignore_missing_unicodes=False),
        text="".join(fonts.CODE_POINTS_BY_FAMILY[font.family]),
    )
    implicit_subset_code_points, implicit_subset_bytes = _subset_font(
        font,
        options=fontTools.subset.Options(ignore_missing_unicodes=True),
        text="".join(fonts.CODE_POINTS),
    )
    assert explicit_subset_code_points == implicit_subset_code_points
    assert explicit_subset_bytes == implicit_subset_bytes
