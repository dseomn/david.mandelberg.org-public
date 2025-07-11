# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Generator
import contextlib
import pathlib

import pytest

from dseomn_website import cache_buster


@pytest.fixture(autouse=True)
def _root_path(tmp_path: pathlib.Path) -> Generator[None, None, None]:
    with contextlib.chdir(tmp_path):
        yield


def test_main() -> None:
    src_path = pathlib.Path("src")
    src_path.mkdir()
    work_path = pathlib.Path("work")
    work_path.mkdir()
    assets_path = pathlib.Path("output/assets")
    assets_path.mkdir(parents=True)
    input_path = src_path / "some-file.txt"
    input_path.write_text("kumquat")
    filename_path = work_path / "some-file.txt.cache-buster-output-filename"
    dyndep_path = work_path / "dyndep"
    output_path = assets_path / "some-file-bq8UGvsFuv-F1FnQBRj4UA==.txt"
    copy_stamp_path = work_path / "some-file.txt.cache-buster-copy-stamp"

    cache_buster.main(args=(f"--work-dir={work_path}", "hash", str(input_path)))
    cache_buster.main(
        args=(
            f"--work-dir={work_path}",
            "dyndep",
            f"--dyndep={dyndep_path}",
            str(input_path),
        ),
    )
    cache_buster.main(args=(f"--work-dir={work_path}", "copy", str(input_path)))

    assert filename_path.read_text() == str(output_path)
    assert dyndep_path.exists()
    assert output_path.read_text() == "kumquat"
    assert copy_stamp_path.exists()
