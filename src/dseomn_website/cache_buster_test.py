# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import pathlib

from dseomn_website import cache_buster


def test_main(tmp_path: pathlib.Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "work").mkdir()
    (tmp_path / "output").mkdir()
    original_path = tmp_path / "src/some-file.txt"
    original_path.write_text("kumquat")
    dyndep_path = tmp_path / "work/dyndep"
    filename_path = tmp_path / "work/filename"
    copy_stamp_path = tmp_path / "work/filename.copy-stamp"
    output_path = tmp_path / "output/some-file-bq8UGvsFuv-F1FnQBRj4UA==.txt"

    cache_buster.main(
        args=(
            "hash",
            f"--dyndep={dyndep_path}",
            f"--write-filename={filename_path}",
            f"--prefix={tmp_path}/output/some-file-",
            "--suffix=.txt",
            str(original_path),
        ),
    )
    cache_buster.main(
        args=(
            "copy",
            f"--read-filename={filename_path}",
            str(original_path),
        ),
    )

    assert dyndep_path.exists()
    assert filename_path.read_text() == str(output_path)
    assert copy_stamp_path.exists()
    assert output_path.read_text() == "kumquat"
