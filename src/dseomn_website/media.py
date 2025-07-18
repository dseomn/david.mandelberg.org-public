# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import abc
import collections
from collections.abc import Collection, Mapping, Sequence
import dataclasses
import functools
from typing import Any, override, Self

import ginjarator
import PIL.Image

from dseomn_website import layout
from dseomn_website import metadata
from dseomn_website import paths


@dataclasses.dataclass(frozen=True, kw_only=True)
class ImageConversion:
    work_suffix: str
    output_suffix: str
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
            work_suffix=f"-{max_width}x{max_height}q{quality}.jpg",
            output_suffix=f"-q{quality}.jpg",
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
            work_suffix=f"-{max_width}x{max_height}.png",
            output_suffix=f".png",
            sh_command=" ".join(
                (
                    "magick",
                    "-define png:exclude-chunk=date,tIME",
                    '"$in"',
                    f"-resize '{max_width}x{max_height}>'",
                    '"$out"',
                    "&&",
                    'optipng -quiet "$out"',
                )
            ),
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class ImageOutputMetadata:
    width: int
    height: int
    mime_type: str


@dataclasses.dataclass(frozen=True, kw_only=True)
class ImageOutput:
    """Result of applying an ImageConversion to an image."""

    source: ginjarator.paths.Filesystem
    conversion: ImageConversion

    @functools.cached_property
    def work_path(self) -> ginjarator.paths.Filesystem:
        return (
            paths.work(self.source.parent)
            / f"{self.source.stem}{self.conversion.work_suffix}"
        )

    @functools.cached_property
    def output_filename_base(self) -> str:
        return f"{self.source.stem}{self.conversion.output_suffix}"

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

    @functools.cached_property
    def metadata(self) -> ImageOutputMetadata | None:
        if not ginjarator.api().fs.add_dependency(self.work_path):
            return None
        with PIL.Image.open(ginjarator.api().fs.root / self.work_path) as image:
            return ImageOutputMetadata(
                width=image.width,
                height=image.height,
                mime_type=image.get_format_mimetype(),
            )


class ImageProfile(abc.ABC):
    """A use case for an image."""

    @abc.abstractmethod
    def outputs(
        self,
        source: ginjarator.paths.Filesystem | str,
    ) -> Collection[ImageOutput]:
        """Returns the source image's outputs."""

    def unique_outputs(
        self,
        source: ginjarator.paths.Filesystem | str,
    ) -> Collection[ImageOutput]:
        """Returns the outputs with duplicate url_paths filtered out."""
        outputs = []
        url_paths = set()
        for output in self.outputs(source):
            if output.url_path is None or output.url_path not in url_paths:
                outputs.append(output)
                url_paths.add(output.url_path)
        return outputs

    def primary_output(
        self,
        source: ginjarator.paths.Filesystem | str,
    ) -> ImageOutput:
        """Returns the primary/default output."""
        raise NotImplementedError()

    def responsive_sizes(self) -> str:
        """Returns the img.sizes attribute."""
        # TODO: https://caniuse.com/mdn-html_elements_img_sizes_auto - Use auto.
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
        max_width: int,
        max_height: int,
        jpeg_quality: int,
        factors: Sequence[int],
        inline_size: str,
    ) -> None:
        """Initializer.

        Args:
            max_width: Max width of the smallest output.
            max_height: Max height of the smallest output.
            jpeg_quality: JPEG quality.
            factors: Max width/height multipliers. First one is for the primary
                output.
            inline_size: CSS inline size of the image.
        """
        self._lossy_conversions = []
        self._lossless_conversions = []
        for factor in factors:
            self._lossy_conversions.append(
                ImageConversion.jpeg(
                    max_width=max_width * factor,
                    max_height=max_height * factor,
                    quality=jpeg_quality,
                )
            )
            self._lossless_conversions.append(
                ImageConversion.png(
                    max_width=max_width * factor,
                    max_height=max_height * factor,
                )
            )
        self._inline_size = inline_size

    def _conversions(
        self,
        source: ginjarator.paths.Filesystem,
    ) -> Sequence[ImageConversion]:
        if source.name.casefold().endswith((".jpg",)):
            return self._lossy_conversions
        elif source.name.casefold().endswith((".png",)):
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
        return self._inline_size


def _em_to_pixels_half(length_em: int) -> int:
    """Returns a length in pixels, divided by 2 for half-resolution images."""
    return length_em * layout.PIXELS_PER_EM // 2


IMAGE_PROFILES = {
    "favicon": FaviconProfile(),
    "float": NormalImageProfile(
        max_width=_em_to_pixels_half(layout.FLOAT_MAX_INLINE_SIZE_EM),
        max_height=_em_to_pixels_half(layout.FLOAT_MAX_INLINE_SIZE_EM * 2),
        jpeg_quality=90,
        factors=(4, 2, 1),
        inline_size=layout.FLOAT_CONTENTS_INLINE_SIZE,
    ),
    "full_screen": NormalImageProfile(
        max_width=3840 // 4,
        max_height=3840 // 4,
        jpeg_quality=90,
        factors=(4, 2, 1),
        inline_size="100vi",
    ),
    "gallery_thumbnail": NormalImageProfile(
        max_width=_em_to_pixels_half(layout.MAIN_COLUMN_MAX_INLINE_SIZE_EM),
        max_height=_em_to_pixels_half(layout.GALLERY_ITEM_MAX_BLOCK_SIZE_EM),
        jpeg_quality=80,
        factors=(4, 2, 1),
        # As of 2025-07-12, this isn't supported widely enough to use most
        # places yet. However, calculating the width of a gallery thumbnail
        # would be somewhat complicated because it depends (at least) on the
        # aspect ratio. So this should work for browsers that support it, and
        # hopefully not be too bad for others.
        inline_size="auto",
    ),
    "main": NormalImageProfile(
        max_width=_em_to_pixels_half(layout.MAIN_COLUMN_MAX_INLINE_SIZE_EM),
        max_height=_em_to_pixels_half(
            layout.MAIN_COLUMN_MAX_INLINE_SIZE_EM * 2
        ),
        jpeg_quality=90,
        factors=(4, 2, 1),
        inline_size=layout.MAIN_COLUMN_CONTENTS_INLINE_SIZE,
    ),
    "opengraph": NormalImageProfile(
        max_width=1920,
        max_height=1920,
        jpeg_quality=90,
        factors=(1,),
        inline_size="auto",  # Unused.
    ),
}

FAVICON = ginjarator.paths.Filesystem(
    "../private/media/P1230630-raw-crop-square.jpg"
)


def image_outputs_by_source() -> (
    Mapping[ginjarator.paths.Filesystem, Collection[ImageOutput]]
):
    outputs = collections.defaultdict[
        ginjarator.paths.Filesystem, set[ImageOutput]
    ](set)
    outputs[FAVICON].update(IMAGE_PROFILES["favicon"].outputs(FAVICON))
    for page in metadata.Page.all():
        for media_item in page.media.item_by_source.values():
            if not isinstance(media_item, metadata.Image):
                continue
            profile_names = set[str]()
            if media_item.gallery is not None:
                profile_names.add("gallery_thumbnail")
            if media_item.opengraph:
                profile_names.add("opengraph")
            if media_item.float_:
                profile_names.add("float")
            if media_item.full_screen:
                profile_names.add("full_screen")
            if media_item.main:
                profile_names.add("main")
            for profile_name in profile_names:
                outputs[media_item.source].update(
                    IMAGE_PROFILES[profile_name].outputs(media_item.source)
                )
    return outputs
