# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import abc
from collections.abc import Collection, Sequence
import dataclasses
import functools
import json
from typing import Any, override, Self

import ginjarator

from dseomn_website import layout
from dseomn_website import metadata
from dseomn_website import paths


@dataclasses.dataclass(frozen=True, kw_only=True)
class ImageConversion:
    suffix: str
    sh_command: str

    @classmethod
    def jpeg(
        cls,
        *,
        max_width: int,
        max_height: int,
        quality: int,
    ) -> Self:
        return cls(
            suffix=f"{max_width}x{max_height}q{quality}.jpg",
            sh_command=" ".join(
                (
                    "magick",
                    '"$in"',
                    f"-resize '{max_width}x{max_height}>'",
                    f"-quality {quality}",
                    '"$out"',
                )
            ),
        )

    @classmethod
    def png(
        cls,
        *,
        max_width: int,
        max_height: int,
    ) -> Self:
        return cls(
            suffix=f"{max_width}x{max_height}.png",
            sh_command=" ".join(
                (
                    "magick",
                    "-define png:exclude-chunk=date,tIME",
                    '"$in"',
                    f"-resize '{max_width}x{max_height}>'",
                    '"$out"',
                )
            ),
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class ImageOutput:
    """Result of applying an ImageConversion to an image."""

    source: ginjarator.paths.Filesystem
    conversion: ImageConversion

    @functools.cached_property
    def work_path(self) -> ginjarator.paths.Filesystem:
        return (
            paths.work(self.source.parent)
            / f"{self.source.stem}-{self.conversion.suffix}"
        )

    @functools.cached_property
    def cache_buster_path(self) -> ginjarator.paths.Filesystem:
        return self.work_path.with_suffix(
            f"{self.work_path.suffix}.cache-buster"
        )

    @functools.cached_property
    def cache_buster_prefix(self) -> str:
        return str(paths.ASSETS / f"{self.work_path.stem}-")

    @functools.cached_property
    def cache_buster_suffix(self) -> str:
        return self.work_path.suffix

    @functools.cached_property
    def url_path(self) -> str | None:
        output_path = ginjarator.api().fs.read_text(self.cache_buster_path)
        if output_path is None:
            return None
        return paths.to_url_path(output_path)

    @functools.cached_property
    def metadata_path(self) -> ginjarator.paths.Filesystem:
        return self.work_path.with_suffix(f"{self.work_path.suffix}.json")

    @functools.cached_property
    def metadata(self) -> Any:
        raw = ginjarator.api().fs.read_text(self.metadata_path)
        if raw is None:
            return None
        return json.loads(raw)[0]["image"]


class ImageProfile(abc.ABC):
    """A use case for an image."""

    @abc.abstractmethod
    def outputs(
        self,
        source: ginjarator.paths.Filesystem | str,
    ) -> Collection[ImageOutput]:
        """Returns the source image's outputs."""

    def primary_output(
        self,
        source: ginjarator.paths.Filesystem | str,
    ) -> ImageOutput:
        """Returns the primary/default output."""
        raise NotImplementedError()

    def responsive_sizes(self) -> str:
        """Returns the img.sizes attribute."""
        raise NotImplementedError()


class FaviconProfile(ImageProfile):
    @override
    def outputs(
        self,
        source: ginjarator.paths.Filesystem | str,
    ) -> Collection[ImageOutput]:
        # https://blog.hubspot.com/website/what-is-a-favicon#size
        return tuple(
            ImageOutput(
                source=ginjarator.paths.Filesystem(source),
                conversion=ImageConversion.png(max_width=size, max_height=size),
            )
            for size in (16, 32, 96, 180, 300, 512)
        )


class NormalImageProfile(ImageProfile):
    def __init__(
        self,
        *,
        lossy_conversions: Sequence[ImageConversion],
        lossless_conversions: Sequence[ImageConversion],
        container_max_inline_size: str,
        container_padding_inline: str,
    ) -> None:
        """Initializer.

        Args:
            lossy_conversions: Conversions to use for lossy sources. First item
                is the primary one.
            lossless_conversions: Conversions to use for lossless sources. First
                item is the primary one.
            container_max_inline_size: The image's container's max-inline-size.
            container_padding_inline: The image's container's padding-inline.
        """
        self._lossy_conversions = lossy_conversions
        self._lossless_conversions = lossless_conversions
        self._container_max_inline_size = container_max_inline_size
        self._container_padding_inline = container_padding_inline

    def _conversions(
        self,
        source: ginjarator.paths.Filesystem,
    ) -> Sequence[ImageConversion]:
        if source.name.endswith((".jpg",)):
            return self._lossy_conversions
        elif source.name.endswith((".png",)):
            return self._lossless_conversions
        else:
            raise NotImplementedError(f"{source.name=}")

    @override
    def outputs(
        self,
        source: ginjarator.paths.Filesystem | str,
    ) -> Collection[ImageOutput]:
        source_path = ginjarator.paths.Filesystem(source)
        return tuple(
            ImageOutput(source=source_path, conversion=conversion)
            for conversion in self._conversions(source_path)
        )

    @override
    def primary_output(
        self,
        source: ginjarator.paths.Filesystem | str,
    ) -> ImageOutput:
        source_path = ginjarator.paths.Filesystem(source)
        return ImageOutput(
            source=source_path,
            conversion=self._conversions(source_path)[0],
        )

    @override
    def responsive_sizes(self) -> str:
        container_inline_size = f"min(100vi, {self._container_max_inline_size})"
        return (
            f"calc({container_inline_size} - "
            f"2 * {self._container_padding_inline})"
        )


IMAGE_PROFILES = {
    "favicon": FaviconProfile(),
    # Images that take the full width of an article.
    "main": NormalImageProfile(
        lossy_conversions=(
            ImageConversion.jpeg(max_width=960, max_height=960, quality=90),
            ImageConversion.jpeg(max_width=480, max_height=480, quality=90),
            ImageConversion.jpeg(max_width=1920, max_height=1920, quality=90),
        ),
        lossless_conversions=(
            ImageConversion.png(max_width=960, max_height=960),
            ImageConversion.png(max_width=480, max_height=480),
            ImageConversion.png(max_width=1920, max_height=1920),
        ),
        container_max_inline_size=layout.MAIN_COLUMN_MAX_INLINE_SIZE,
        container_padding_inline=layout.MAIN_COLUMN_PADDING_INLINE,
    ),
}

FAVICON = ginjarator.paths.Filesystem(
    "../private/media/P1230630-raw-crop-square.jpg"
)


def all_image_outputs() -> Collection[ImageOutput]:
    outputs = set[ImageOutput]()
    outputs.update(IMAGE_PROFILES["favicon"].outputs(FAVICON))
    for page in metadata.Page.all():
        for source, profile_names in page.media.profile_names_by_image.items():
            for profile_name in profile_names:
                outputs.update(IMAGE_PROFILES[profile_name].outputs(source))
    return outputs
