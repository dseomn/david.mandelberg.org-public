# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import textwrap

import ginjarator
import ginjarator.testing

from dseomn_website import media


def test_image_output_scan() -> None:
    source = ginjarator.paths.Filesystem(
        "../private/media/P1230630-raw-crop-square.jpg"
    )
    conversion = media.ImageConversion.png(max_width=16, max_height=16)

    with ginjarator.testing.api_for_scan():
        image_output = media.ImageOutput(source=source, conversion=conversion)

        assert image_output.work_path == ginjarator.paths.Filesystem(
            "work/media/P1230630-raw-crop-square-16x16.png"
        )
        assert image_output.cache_buster_path == ginjarator.paths.Filesystem(
            "work/media/P1230630-raw-crop-square-16x16.png.cache-buster"
        )
        assert image_output.url_path is None
        assert image_output.metadata_path == ginjarator.paths.Filesystem(
            "work/media/P1230630-raw-crop-square-16x16.png.json"
        )
        assert image_output.metadata is None


def test_image_output_render(tmp_path: pathlib.Path) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["media"]
            build_paths = ["work"]
            """
        )
    )
    (tmp_path / "work/media").mkdir(parents=True)
    (tmp_path / "work/media/foo-16x16.png.cache-buster").write_text(
        "output/media/foo-16x16-some-hash.png"
    )
    (tmp_path / "work/media/foo-16x16.png.json").write_text(
        json.dumps(dict(kumquat=42))
    )

    with ginjarator.testing.api_for_render(
        root_path=tmp_path,
        dependencies=(
            "work/media/foo-16x16.png.cache-buster",
            "work/media/foo-16x16.png.json",
        ),
    ):
        image_output = media.ImageOutput(
            source=ginjarator.paths.Filesystem("media/foo.jpg"),
            conversion=media.ImageConversion.png(max_width=16, max_height=16),
        )

        assert image_output.url_path == "/media/foo-16x16-some-hash.png"
        assert image_output.metadata == dict(kumquat=42)


def test_image_output_config() -> None:
    config = media.ImageOutputConfig(
        source=ginjarator.paths.Filesystem("media/foo.jpg"),
        conversion=media.ImageConversion.png(max_width=16, max_height=16),
        output_dir=ginjarator.paths.Filesystem("output/media"),
    )

    assert config.cache_buster_prefix == "output/media/foo-16x16-"
    assert config.cache_buster_suffix == ".png"
