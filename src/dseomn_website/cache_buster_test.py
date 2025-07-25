# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Generator
import contextlib
import importlib.resources
import pathlib

import pytest

from dseomn_website import cache_buster


@pytest.fixture(autouse=True)
def _root_path(tmp_path: pathlib.Path) -> Generator[None, None, None]:
    with contextlib.chdir(tmp_path):
        yield


@pytest.mark.parametrize(
    "output_filename_base,expected_output_path",
    (
        (
            "some-file-renamed.txt",
            "output/assets/some-file-renamed-bq8UGvsFuv-F1FnQBRj4UDpo.txt",
        ),
        (
            "some-file-renamed",
            "output/assets/some-file-renamed-bq8UGvsFuv-F1FnQBRj4UDpo",
        ),
    ),
)
def test_hash_normal(
    output_filename_base: str,
    expected_output_path: str,
) -> None:
    work_path = pathlib.Path("work")
    work_path.mkdir()
    (work_path / "some-file.txt").write_text("kumquat")

    cache_buster.main(
        args=(
            f"--work-dir={work_path}",
            "hash",
            f"--output-filename-base={output_filename_base}",
            "work/some-file.txt",
        )
    )

    assert (
        work_path / "some-file.txt.cache-buster-output-filename"
    ).read_text() == expected_output_path


def test_hash_image() -> None:
    work_path = pathlib.Path("work")
    work_path.mkdir()
    (work_path / "some-file.png").write_bytes(
        (importlib.resources.files() / "test-16x12.png").read_bytes()
    )

    cache_buster.main(
        args=(
            f"--work-dir={work_path}",
            "hash",
            "--output-filename-base=some-file-renamed.png",
            "--image",
            "work/some-file.png",
        )
    )

    assert (
        work_path / "some-file.png.cache-buster-output-filename"
    ).read_text() == (
        "output/assets/some-file-renamed-16x12-eMEfp_WCHH9h79DkO5e3dgLC.png"
    )


def test_dyndep() -> None:
    work_path = pathlib.Path("work")
    work_path.mkdir()
    dyndep_path = work_path / "dyndep"
    (work_path / "some-file.txt.cache-buster-output-filename").write_text(
        "work/out"
    )

    cache_buster.main(
        args=(
            f"--work-dir={work_path}",
            "dyndep",
            f"--dyndep={dyndep_path}",
            f"--copy-stamp=work/some-copy-stamp",
            "work/some-file.txt",
        ),
    )

    assert dyndep_path.exists()


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
