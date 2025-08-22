#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import argparse
from collections.abc import Sequence
import datetime
import fractions
import json
import pathlib
import sys
from typing import Any

import markupsafe
import PIL.ExifTags
import PIL.Image
import PIL.ImageFile
import PIL.ImageOps
import PIL.TiffImagePlugin

PIL.Image.MAX_IMAGE_PIXELS = None

# See https://github.com/python-pillow/Pillow/issues/9162
PIL.ImageFile.MAXBLOCK = 512 * 1024 * 1024


def _exif_to_fraction(
    value: PIL.TiffImagePlugin.IFDRational | None,
) -> fractions.Fraction | None:
    if value is None or value.denominator == 0:
        return None
    # Pass the values separately so that they're reduced.
    return fractions.Fraction(int(value.numerator), int(value.denominator))


def _human_readable_html(image: PIL.ImageFile.ImageFile) -> Any:
    # A list of (key, values) instead of a dict, to preserve order in JSON.
    result = list[tuple[str, tuple[str, ...]]]()

    exif = image.getexif()
    exif_ifd = exif.get_ifd(PIL.ExifTags.IFD.Exif)

    if PIL.ExifTags.Base.DateTimeOriginal in exif_ifd:
        result.append(
            (
                "Taken",
                (
                    str(
                        markupsafe.Markup("<time>{}</time>").format(
                            datetime.datetime.strptime(
                                exif_ifd[PIL.ExifTags.Base.DateTimeOriginal],
                                "%Y:%m:%d %H:%M:%S",
                            ).isoformat(sep=" ")
                        )
                    ),
                ),
            )
        )

    # Hardcoding the list of cameras serves two unrelated purposes: 1. It fixes
    # duplication like with the Canon PowerShot S90. 2. When adding a new camera
    # I can look at the metadata that camera writes and decide whether to change
    # anything else about this script.
    if (
        camera := {
            ("Canon", "Canon PowerShot A530"): "Canon PowerShot A530",
            ("Canon", "Canon PowerShot S90"): "Canon PowerShot S90",
            ("Panasonic", "DMC-GH2"): "Panasonic DMC-GH2",
            (None, None): None,
        }[
            (
                exif.get(PIL.ExifTags.Base.Make),
                exif.get(PIL.ExifTags.Base.Model),
            )
        ]
    ) is not None:
        result.append(("Camera", (camera,)))

    result.append(
        (
            "Resolution",
            (f"{image.width} × {image.height}",),
        )
    )

    if (
        f_number := _exif_to_fraction(exif_ifd.get(PIL.ExifTags.Base.FNumber))
    ) is not None:
        result.append(
            (
                "Aperture",
                (
                    (
                        "\N{LATIN SMALL LETTER F WITH HOOK}\N{DIVISION SLASH}"
                        f"{f_number:.2g}"
                    ),
                ),
            )
        )

    if (
        exposure_time := _exif_to_fraction(
            exif_ifd.get(PIL.ExifTags.Base.ExposureTime)
        )
    ) is not None:
        result.append(
            (
                "Exposure time",
                (
                    (
                        f"{exposure_time:.1f}\N{NO-BREAK SPACE}s"
                        if exposure_time >= 1
                        else (
                            f"{exposure_time.numerator}\N{FRACTION SLASH}"
                            f"{exposure_time.denominator}\N{NO-BREAK SPACE}s"
                        )
                    ),
                ),
            )
        )

    focal_length_parts = []
    if (
        focal_length := _exif_to_fraction(
            exif_ifd.get(PIL.ExifTags.Base.FocalLength)
        )
    ) is not None:
        focal_length_parts.append(f"{focal_length}\N{NO-BREAK SPACE}mm")
    if (
        focal_length_35mm_equiv := exif_ifd.get(
            PIL.ExifTags.Base.FocalLengthIn35mmFilm
        )
    ) is not None:
        focal_length_parts.append(
            str(
                markupsafe.escape(
                    f"{focal_length_35mm_equiv}\N{NO-BREAK SPACE}mm "
                    "(35\N{NO-BREAK SPACE}mm equivalent)"
                )
            )
        )
    if focal_length_parts:
        result.append(("Focal length", tuple(focal_length_parts)))

    if (iso := exif_ifd.get(PIL.ExifTags.Base.ISOSpeedRatings)) is not None:
        result.append(
            (
                "ISO",
                (str(markupsafe.escape(iso)),),
            )
        )

    software = []
    for software_tag in (
        PIL.ExifTags.Base.Software,
        PIL.ExifTags.Base.ProcessingSoftware,
    ):
        if software_tag in exif:
            software.append(str(markupsafe.escape(exif[software_tag].strip())))
    if software:
        result.append(("Software", tuple(software)))

    return result


def main(
    *,
    args: Sequence[str] = sys.argv[1:],
) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "image",
        type=pathlib.Path,
        help="Image file to read.",
    )
    parser.add_argument(
        "metadata",
        type=pathlib.Path,
        help="Metadata JSON file to write.",
    )
    parsed_args = parser.parse_args(args)

    with PIL.Image.open(parsed_args.image) as image:
        # https://github.com/python-pillow/Pillow/discussions/9115
        PIL.ImageOps.exif_transpose(image, in_place=True)

        parsed_args.metadata.write_text(
            json.dumps(
                dict(
                    height=image.height,
                    human_readable_html=_human_readable_html(image),
                    width=image.width,
                )
            )
        )


if __name__ == "__main__":
    main()
