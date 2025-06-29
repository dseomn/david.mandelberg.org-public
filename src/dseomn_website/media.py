# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
import dataclasses
import functools
import json
from typing import Any, Self

import ginjarator

from dseomn_website import paths


@dataclasses.dataclass(frozen=True, kw_only=True)
class ImageConversion:
    suffix: str
    magick_args: Sequence[str]

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
            magick_args=(
                "-resize",
                f"{max_width}x{max_height}>",
                "-quality",
                str(quality),
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
            magick_args=(
                "-resize",
                f"{max_width}x{max_height}>",
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
        return json.loads(raw)


@dataclasses.dataclass(frozen=True, kw_only=True)
class ImageOutputConfig(ImageOutput):
    """Config data needed to build an ImageOutput."""

    output_dir: ginjarator.paths.Filesystem

    @property
    def cache_buster_prefix(self) -> str:
        return str(self.output_dir / f"{self.work_path.stem}-")

    @property
    def cache_buster_suffix(self) -> str:
        return self.work_path.suffix
