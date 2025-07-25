# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import collections
import importlib.resources
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
                work_suffix="-64x48q90.jpg",
                output_suffix="-q90.jpg",
                sh_command=(
                    '''magick "$in" -resize '64x48>' -quality 90 "$out"'''
                ),
            ),
        ),
        (
            media.ImageConversion.png(max_width=64, max_height=48),
            media.ImageConversion(
                work_suffix="-64x48.png",
                output_suffix=".png",
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
    output_1 = tmp_path / f"1{conversion.work_suffix}"
    output_2 = tmp_path / f"2{conversion.work_suffix}"

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
        assert image_output.output_filename_base == (
            "P1230630-raw-crop-square.png"
        )
        assert image_output.url_path is None
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
    (tmp_path / "work/media/foo-16x16.png").write_bytes(
        (importlib.resources.files() / "test-16x12.png").read_bytes()
    )
    (
        tmp_path / "work/media/foo-16x16.png.cache-buster-output-filename"
    ).write_text("output/media/foo-16x16-some-hash.png")

    with ginjarator.testing.api_for_render(
        root_path=tmp_path,
        dependencies=(
            "work/media/foo-16x16.png",
            "work/media/foo-16x16.png.cache-buster-output-filename",
        ),
    ):
        image_output = media.ImageOutput(
            source=ginjarator.paths.Filesystem("media/foo.jpg"),
            conversion=media.ImageConversion.png(max_width=16, max_height=16),
        )

        assert image_output.url_path == "/media/foo-16x16-some-hash.png"
        assert image_output.metadata == media.ImageOutputMetadata(
            width=16,
            height=12,
            mime_type="image/png",
        )


def test_image_profile_unique_outputs_scan(tmp_path: pathlib.Path) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["media"]
            build_paths = ["work"]
            """
        )
    )
    source = ginjarator.paths.Filesystem("foo.png")
    profile = media.NormalImageProfile(
        max_width=16,
        max_height=16,
        jpeg_quality=100,
        factors=(1, 2, 4),
        inline_size="",
    )

    with ginjarator.testing.api_for_scan():
        assert tuple(profile.unique_outputs(source)) == tuple(
            profile.outputs(source)
        )


def test_image_profile_unique_outputs_render(tmp_path: pathlib.Path) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["media"]
            build_paths = ["work"]
            """
        )
    )
    source = ginjarator.paths.Filesystem("media/foo.png")
    (tmp_path / "work/media").mkdir(parents=True)
    (
        tmp_path / "work/media/foo-16x16.png.cache-buster-output-filename"
    ).write_text("output/assets/foo-16x16.png")
    (
        tmp_path / "work/media/foo-32x32.png.cache-buster-output-filename"
    ).write_text("output/assets/foo-32x32.png")
    (
        tmp_path / "work/media/foo-64x64.png.cache-buster-output-filename"
    ).write_text("output/assets/foo-32x32.png")
    profile = media.NormalImageProfile(
        max_width=16,
        max_height=16,
        jpeg_quality=100,
        factors=(1, 2, 4),
        inline_size="",
    )

    with ginjarator.testing.api_for_render(
        root_path=tmp_path,
        dependencies=(
            "work/media/foo-16x16.png.cache-buster-output-filename",
            "work/media/foo-32x32.png.cache-buster-output-filename",
            "work/media/foo-64x64.png.cache-buster-output-filename",
        ),
    ):
        assert tuple(
            output.url_path for output in profile.unique_outputs(source)
        ) == (
            "/assets/foo-16x16.png",
            "/assets/foo-32x32.png",
        )


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


@pytest.mark.parametrize(
    "source,primary_conversion,other_conversion",
    (
        (
            ginjarator.paths.Filesystem("foo.jpg"),
            media.ImageConversion.jpeg(
                max_width=960,
                max_height=960,
                quality=90,
            ),
            media.ImageConversion.jpeg(
                max_width=480,
                max_height=480,
                quality=90,
            ),
        ),
        (
            ginjarator.paths.Filesystem("foo.png"),
            media.ImageConversion.png(max_width=960, max_height=960),
            media.ImageConversion.png(max_width=480, max_height=480),
        ),
    ),
)
def test_normal_image_profile_outputs(
    source: ginjarator.paths.Filesystem,
    primary_conversion: media.ImageConversion,
    other_conversion: media.ImageConversion,
) -> None:
    profile = media.NormalImageProfile(
        max_width=480,
        max_height=480,
        jpeg_quality=90,
        factors=(2, 1),
        inline_size="60em",
    )

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
        max_width=16,
        max_height=16,
        jpeg_quality=100,
        factors=(1,),
        inline_size="60em",
    )
    source = ginjarator.paths.Filesystem("foo.txt")

    with pytest.raises(NotImplementedError):
        profile.outputs(source)
    with pytest.raises(NotImplementedError):
        profile.primary_output(source)


def test_normal_image_profile_responsive_sizes() -> None:
    profile = media.NormalImageProfile(
        max_width=16,
        max_height=16,
        jpeg_quality=100,
        factors=(1,),
        inline_size="60em",
    )

    assert profile.responsive_sizes() == "60em"


def test_image_outputs_by_source() -> None:
    with ginjarator.testing.api_for_scan():
        outputs_by_source = media.image_outputs_by_source()

    assert outputs_by_source[media.FAVICON]
    assert outputs_by_source[
        ginjarator.paths.Filesystem(
            "../private/errors/404/P1250746-raw-unsharp.jpg"
        )
    ]
