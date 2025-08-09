# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Generator
import contextlib
import pathlib
import textwrap

import pytest

from dseomn_website import compress


@pytest.fixture(autouse=True)
def _root_path(tmp_path: pathlib.Path) -> Generator[None, None, None]:
    with contextlib.chdir(tmp_path):
        pathlib.Path("output").mkdir()
        pathlib.Path("work").mkdir()
        pathlib.Path("work/output").mkdir()
        yield


def test_dyndep() -> None:
    compress.main(
        args=(
            "dyndep",
            "--stamp=work/output/foo.html.compress-stamp",
            "--dyndep=work/output/foo.html.compress-dd",
            "output/foo.html",
        ),
    )

    assert set(map(str, pathlib.Path(".").glob("**/*"))) == {
        "output",
        "work",
        "work/output",
        "work/output/foo.html.compress-dd",
    }


def test_dyndep_indirect() -> None:
    pathlib.Path("work/foo-path").write_text("output/foo.html")
    compress.main(
        args=(
            "dyndep",
            "--stamp=work/foo-path.compress-stamp",
            "--dyndep=work/foo-path.compress-dd",
            "--indirect",
            "work/foo-path",
        ),
    )

    assert set(map(str, pathlib.Path(".").glob("**/*"))) == {
        "output",
        "work",
        "work/output",
        "work/foo-path",
        "work/foo-path.compress-dd",
    }


def test_compress() -> None:
    pathlib.Path("output/foo.html").touch()

    compress.main(
        args=(
            "compress",
            "--stamp=work/output/foo.html.compress-stamp",
            "output/foo.html",
        )
    )

    assert set(map(str, pathlib.Path(".").glob("**/*"))) == {
        "output",
        "work",
        "work/output",
        "output/foo.html",
        "output/foo.html.c-e-br",
        "output/foo.html.c-e-gzip",
        "output/foo.html.c-e-zstd",
        "output/foo.html.var",
        "work/output/foo.html.compress-stamp",
    }
    assert pathlib.Path("output/foo.html.var").read_text() == textwrap.dedent(
        """\
        Content-Type: text/html
        URI: foo.html

        Content-Encoding: br
        Content-Type: text/html
        URI: foo.html.c-e-br

        Content-Encoding: gzip
        Content-Type: text/html
        URI: foo.html.c-e-gzip

        Content-Encoding: zstd
        Content-Type: text/html
        URI: foo.html.c-e-zstd
        """
    )


def test_compress_indirect() -> None:
    pathlib.Path("work/foo-path").write_text("output/foo.html")
    pathlib.Path("output/foo.html").touch()

    compress.main(
        args=(
            "compress",
            "--stamp=work/foo-path.compress-stamp",
            "--indirect",
            "work/foo-path",
        )
    )

    assert set(map(str, pathlib.Path(".").glob("**/*"))) == {
        "output",
        "work",
        "work/output",
        "work/foo-path",
        "output/foo.html",
        "output/foo.html.c-e-br",
        "output/foo.html.c-e-gzip",
        "output/foo.html.c-e-zstd",
        "output/foo.html.var",
        "work/foo-path.compress-stamp",
    }
    assert pathlib.Path("output/foo.html.var").read_text() == textwrap.dedent(
        """\
        Content-Type: text/html
        URI: foo.html

        Content-Encoding: br
        Content-Type: text/html
        URI: foo.html.c-e-br

        Content-Encoding: gzip
        Content-Type: text/html
        URI: foo.html.c-e-gzip

        Content-Encoding: zstd
        Content-Type: text/html
        URI: foo.html.c-e-zstd
        """
    )
