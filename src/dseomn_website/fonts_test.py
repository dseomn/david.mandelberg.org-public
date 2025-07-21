# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pathlib
import textwrap

import ginjarator.testing

from dseomn_website import fonts


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
        assert font.work_path_copy == ginjarator.paths.Filesystem(
            "work/third_party/foo/foo.ttf"
        )
        assert font.work_path == ginjarator.paths.Filesystem(
            "work/third_party/foo/foo.woff2"
        )
        assert font.url_path is None


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
