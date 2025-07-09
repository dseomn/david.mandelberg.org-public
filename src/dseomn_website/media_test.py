# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import collections
import json
import pathlib
import subprocess
import textwrap
import time

import ginjarator
import ginjarator.testing
import pytest

from dseomn_website import media


@pytest.mark.parametrize(
    "actual,expected",
    (
        (
            media.ImageConversion.jpeg(max_width=64, max_height=48, quality=90),
            media.ImageConversion(
                suffix="64x48q90.jpg",
                sh_command=(
                    '''magick "$in" -resize '64x48>' -quality 90 "$out"'''
                ),
            ),
        ),
        (
            media.ImageConversion.png(max_width=64, max_height=48),
            media.ImageConversion(
                suffix="64x48.png",
                sh_command=(
                    """magick -define png:exclude-chunk=date,tIME "$in" """
                    '''-resize '64x48>' "$out" && optipng -quiet "$out"'''
                ),
            ),
        ),
    ),
)
def test_image_conversion(
    actual: media.ImageConversion,
    expected: media.ImageConversion,
) -> None:
    assert actual == expected


@pytest.mark.slow
@pytest.mark.parametrize(
    "conversion",
    (
        media.ImageConversion.jpeg(max_width=16, max_height=16, quality=90),
        media.ImageConversion.png(max_width=16, max_height=16),
    ),
)
def test_image_conversion_deterministic(
    conversion: media.ImageConversion,
    tmp_path: pathlib.Path,
) -> None:
    output_1 = tmp_path / f"1-{conversion.suffix}"
    output_2 = tmp_path / f"2-{conversion.suffix}"

    subprocess.run(
        conversion.sh_command,
        shell=True,
        check=True,
        env={
            "in": str(media.FAVICON),
            "out": str(output_1),
        },
    )
    time.sleep(1.01)  # Catch changes to second-resolution timestamps.
    subprocess.run(
        conversion.sh_command,
        shell=True,
        check=True,
        env={
            "in": str(media.FAVICON),
            "out": str(output_2),
        },
    )

    assert output_1.read_bytes() == output_2.read_bytes()


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
        assert (
            image_output.cache_buster_prefix
            == "output/assets/P1230630-raw-crop-square-16x16-"
        )
        assert image_output.cache_buster_suffix == ".png"
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
        json.dumps([dict(image=dict(kumquat=42))])
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


@pytest.mark.parametrize("lossy", (True, False))
def test_normal_image_profile_outputs(lossy: bool) -> None:
    primary_conversion = media.ImageConversion.jpeg(
        max_width=960, max_height=960, quality=90
    )
    other_conversion = media.ImageConversion.jpeg(
        max_width=480, max_height=480, quality=90
    )
    profile = media.NormalImageProfile(
        lossy_conversions=(
            (primary_conversion, other_conversion) if lossy else ()
        ),
        lossless_conversions=(
            () if lossy else (primary_conversion, other_conversion)
        ),
        inline_size="60em",
    )
    source = ginjarator.paths.Filesystem("foo.jpg" if lossy else "foo.png")

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
        lossless_conversions=(),
        inline_size="60em",
    )
    source = ginjarator.paths.Filesystem("foo.txt")

    with pytest.raises(NotImplementedError):
        profile.outputs(source)
    with pytest.raises(NotImplementedError):
        profile.primary_output(source)


def test_normal_image_profile_responsive_sizes() -> None:
    profile = media.NormalImageProfile(
        lossy_conversions=(),
        lossless_conversions=(),
        inline_size="60em",
    )

    assert profile.responsive_sizes() == "60em"


def test_all_image_outputs() -> None:
    with ginjarator.testing.api_for_scan():
        assert {output.source for output in media.all_image_outputs()} >= {
            media.FAVICON,
            ginjarator.paths.Filesystem(
                "../private/errors/404/P1250746-raw-unsharp.jpg"
            ),
        }
