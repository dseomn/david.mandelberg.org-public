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


def test_copy_conflict() -> None:
    work_path = pathlib.Path("work")
    work_path.mkdir()
    (work_path / "file1").write_text("kumquat")
    (work_path / "file1.cache-buster-output-filename").write_text("work/out")
    (work_path / "file2").write_text("pomelo")
    (work_path / "file2.cache-buster-output-filename").write_text("work/out")

    with pytest.raises(ValueError, match=r"different contents"):
        cache_buster.main(
            args=(
                f"--work-dir={work_path}",
                "copy",
                f"--copy-stamp=work/copy-stamp",
                "work/file1",
                "work/file2",
            )
        )


def test_copy_multiple() -> None:
    work_path = pathlib.Path("work")
    work_path.mkdir()
    (work_path / "file1a").write_text("kumquat")
    (work_path / "file1a.cache-buster-output-filename").write_text("work/out1")
    (work_path / "file1b").write_text("kumquat")
    (work_path / "file1b.cache-buster-output-filename").write_text("work/out1")
    (work_path / "file2").write_text("pomelo")
    (work_path / "file2.cache-buster-output-filename").write_text("work/out2")
    copy_stamp_path = work_path / "copy-stamp"

    cache_buster.main(
        args=(
            f"--work-dir={work_path}",
            "copy",
            f"--copy-stamp={copy_stamp_path}",
            "work/file1a",
            "work/file1b",
            "work/file2",
        )
    )

    assert (work_path / "out1").read_text() == "kumquat"
    assert (work_path / "out2").read_text() == "pomelo"
    assert copy_stamp_path.exists()


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
    output_path = assets_path / "some-file-renamed-bq8UGvsFuv-F1FnQBRj4UA==.txt"
    copy_stamp_path = work_path / "some-file.txt.cache-buster-copy-stamp"

    cache_buster.main(
        args=(
            f"--work-dir={work_path}",
            "hash",
            "--output-filename-base=some-file-renamed.txt",
            str(input_path),
        )
    )
    cache_buster.main(
        args=(
            f"--work-dir={work_path}",
            "dyndep",
            f"--dyndep={dyndep_path}",
            f"--copy-stamp={copy_stamp_path}",
            str(input_path),
        ),
    )
    cache_buster.main(
        args=(
            f"--work-dir={work_path}",
            "copy",
            f"--copy-stamp={copy_stamp_path}",
            str(input_path),
        )
    )

    assert filename_path.read_text() == str(output_path)
    assert dyndep_path.exists()
    assert output_path.read_text() == "kumquat"
    assert copy_stamp_path.exists()
