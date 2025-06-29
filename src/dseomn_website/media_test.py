# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import collections
import json
import pathlib
import textwrap

import ginjarator
import ginjarator.testing
import pytest

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


def test_favicon_profile_outputs() -> None:
    assert media.ImageOutput(
        source=ginjarator.paths.Filesystem("foo"),
        conversion=media.ImageConversion.png(max_width=16, max_height=16),
    ) in media.FaviconProfile().outputs("foo")


def test_favicon_profile_primary_output() -> None:
    with pytest.raises(NotImplementedError):
        media.FaviconProfile().primary_output("foo")


def test_favicon_profile_responsive_sizes() -> None:
    with pytest.raises(NotImplementedError):
        media.FaviconProfile().responsive_sizes()


def test_normal_image_profile_outputs() -> None:
    primary_conversion = media.ImageConversion.jpeg(
        max_width=960, max_height=960, quality=90
    )
    other_conversion = media.ImageConversion.jpeg(
        max_width=480, max_height=480, quality=90
    )
    profile = media.NormalImageProfile(
        lossy_conversions=(primary_conversion, other_conversion),
        container_max_inline_size="",
        container_padding_inline="",
    )
    source = ginjarator.paths.Filesystem("foo.jpg")

    assert collections.Counter(profile.outputs(source)) == collections.Counter(
        (
            media.ImageOutput(source=source, conversion=primary_conversion),
            media.ImageOutput(source=source, conversion=other_conversion),
        )
    )
    assert profile.primary_output(source) == media.ImageOutput(
        source=source,
        conversion=primary_conversion,
    )


def test_normal_image_profile_outputs_unknown_extension() -> None:
    profile = media.NormalImageProfile(
        lossy_conversions=(),
        container_max_inline_size="",
        container_padding_inline="",
    )
    source = ginjarator.paths.Filesystem("foo.txt")

    with pytest.raises(NotImplementedError):
        profile.outputs(source)
    with pytest.raises(NotImplementedError):
        profile.primary_output(source)


def test_normal_image_profile_responsive_sizes() -> None:
    profile = media.NormalImageProfile(
        lossy_conversions=(),
        container_max_inline_size="60em",
        container_padding_inline="1em",
    )

    assert profile.responsive_sizes() == (
        "(width <= calc(60em - 2 * 1em)) calc(100vw - 2 * 1em), "
        "calc(60em - 2 * 1em)"
    )


def test_all_image_output_configs() -> None:
    # TODO: dseomn - For now this is just a smoke test because
    # all_image_output_configs() uses hardcoded inputs. Once it gets its configs
    # from the filesystem, this should test more of the logic.
    assert media.FAVICON in tuple(
        config.source for config in media.all_image_output_configs()
    )
