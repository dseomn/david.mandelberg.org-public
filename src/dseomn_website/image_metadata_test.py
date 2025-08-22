# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
from typing import Any

import pytest

from dseomn_website import image_metadata


def _metadata(image_path: str, *, tmp_path: pathlib.Path) -> Any:
    metadata_path = tmp_path / "metadata.json"
    image_metadata.main(args=(image_path, str(metadata_path)))
    return json.loads(metadata_path.read_text())


@pytest.mark.parametrize(
    "image_path,expected_width,expected_height",
    (
        ("src/dseomn_website/test-16x12.png", 16, 12),
        (
            # Test that EXIF orientation is used.
            (
                "../private/posts/2013-12-15-vancouver-and-canadian-rockies/"
                "IMG_4439.JPG"
            ),
            2736,
            3648,
        ),
    ),
)
def test_size(
    image_path: str,
    expected_width: int,
    expected_height: int,
    tmp_path: pathlib.Path,
) -> None:
    metadata = _metadata(image_path, tmp_path=tmp_path)
    assert metadata["width"] == expected_width
    assert metadata["height"] == expected_height


@pytest.mark.parametrize(
    "image_path,key,expected_values",
    (
        (
            "src/dseomn_website/test-16x12.png",
            "Taken",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Taken",
            ["<time>2013-02-08 16:18:16</time>"],
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Camera",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Camera",
            ["Panasonic DMC-GH2"],
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Resolution",
            ["16 × 12"],
        ),
        (
            # Test that EXIF orientation is used.
            (
                "../private/posts/2013-12-15-vancouver-and-canadian-rockies/"
                "IMG_4439.JPG"
            ),
            "Resolution",
            ["2736 × 3648"],
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Aperture",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Aperture",
            ["ƒ∕8"],
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030256-raw.JPG",
            "Aperture",
            ["ƒ∕6.3"],
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Exposure time",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Exposure time",
            ["1⁄80 s"],
        ),
        (
            (
                "../private/posts/2013-07-06-nordic-fiddles-and-feet/"
                "P1070388-raw.jpg"
            ),
            "Exposure time",
            ["13.0 s"],
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Focal length",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Focal length",
            ["42 mm", "84 mm (35 mm equivalent)"],
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "ISO",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "ISO",
            ["500"],
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Software",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Software",
            ["Ver.1.1", "UFRaw 0.18"],
        ),
        (
            (
                "../private/posts/2013-02-12-snow-photos/"
                "P1030324-raw-P1030337-raw.jpg"
            ),
            "Software",
            ["Hugin 2011.4.0.cf9be9344356"],
        ),
    ),
)
def test_human_readable_html(
    image_path: str,
    key: str,
    expected_values: list[str] | None,
    tmp_path: pathlib.Path,
) -> None:
    metadata = _metadata(image_path, tmp_path=tmp_path)
    human_readable_html = dict(metadata["human_readable_html"])
    # Assert no duplicate keys.
    assert len(human_readable_html) == len(metadata["human_readable_html"])
    assert human_readable_html.get(key) == expected_values
