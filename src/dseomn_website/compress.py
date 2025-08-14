#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import abc
import argparse
from collections.abc import Sequence
import pathlib
import subprocess
import sys
import textwrap
from typing import override
import urllib.parse


def _ninja_escape(value: str) -> str:
    return value.translate(
        str.maketrans(
            dict[str, int | str | None](
                {
                    " ": "$ ",
                    ":": "$:",
                    "$": "$$",
                }
            )
        )
    )


def _output_path(input_path: pathlib.Path, suffix: str) -> pathlib.Path:
    return input_path.parent / f"{input_path.name}{suffix}"


class Encoding(abc.ABC):
    def __init__(self, *, name: str) -> None:
        self.name = name
        # Use a non-standard suffix so that Apache can send these files with
        # Content-Encoding and send files with the standard suffixes with
        # Content-Type of the compressed type and no Content-Encoding.
        self.suffix = f".c-e-{name}"

    @abc.abstractmethod
    def encode(
        self,
        input_path: pathlib.Path,
        output_path: pathlib.Path,
    ) -> None:
        # When changing implementations of this, run slow tests.
        raise NotImplementedError()


class Brotli(Encoding):
    @override
    def encode(
        self,
        input_path: pathlib.Path,
        output_path: pathlib.Path,
    ) -> None:
        subprocess.run(
            (
                "brotli",
                "--force",
                "--no-copy-stat",
                f"--output={output_path}",
                "--best",
                "--",
                str(input_path),
            ),
            check=True,
        )


class Gzip(Encoding):
    @override
    def encode(
        self,
        input_path: pathlib.Path,
        output_path: pathlib.Path,
    ) -> None:
        with (
            input_path.open(mode="rb") as input_file,
            output_path.open(mode="wb") as output_file,
        ):
            subprocess.run(
                (
                    "gzip",
                    "--no-name",  # This also prevents including the timestamp.
                    "--best",
                ),
                stdin=input_file,
                stdout=output_file,
                check=True,
            )


class Zstd(Encoding):
    @override
    def encode(
        self,
        input_path: pathlib.Path,
        output_path: pathlib.Path,
    ) -> None:
        with (
            input_path.open(mode="rb") as input_file,
            output_path.open(mode="wb") as output_file,
        ):
            subprocess.run(
                ("zstd", "-19", "--quiet"),
                stdin=input_file,
                stdout=output_file,
                check=True,
            )


ENCODINGS = (
    Brotli(name="br"),
    Gzip(name="gzip"),
    Zstd(name="zstd"),
)


def _actual_input_path(args: argparse.Namespace) -> pathlib.Path:
    if args.indirect:
        return pathlib.Path(args.input_file.read_text())
    else:
        return args.input_file


def _dyndep(args: argparse.Namespace) -> None:
    actual_input_path = _actual_input_path(args)
    input_paths = {
        str(args.input_file),
        str(actual_input_path),
    }
    output_paths = (
        str(_output_path(actual_input_path, ".var")),
        *(
            str(_output_path(actual_input_path, encoding.suffix))
            for encoding in ENCODINGS
        ),
    )
    args.dyndep.write_text(
        textwrap.dedent(
            f"""\
            ninja_dyndep_version = 1
            build $
                    {_ninja_escape(str(args.stamp))} $
                    | $
                    {" ".join(map(_ninja_escape, output_paths))} $
                    : $
                    dyndep $
                    | $
                    {" ".join(map(_ninja_escape, input_paths))}
            """
        )
    )


def _compress(args: argparse.Namespace) -> None:
    actual_input_path = _actual_input_path(args)
    content_type = {
        ".atom": "application/atom+xml",
        ".css": "text/css",
        ".html": "text/html",
        ".txt": "text/plain",
    }[actual_input_path.suffix]
    var_parts = [
        textwrap.dedent(
            f"""\
            Content-Type: {content_type}
            URI: {urllib.parse.quote(actual_input_path.name)}
            """
        ),
    ]
    for encoding in ENCODINGS:
        output_path = _output_path(actual_input_path, encoding.suffix)
        encoding.encode(actual_input_path, output_path)
        var_parts.append(
            textwrap.dedent(
                f"""\
                Content-Encoding: {encoding.name}
                Content-Type: {content_type}
                URI: {urllib.parse.quote(output_path.name)}
                """
            )
        )
    _output_path(actual_input_path, ".var").write_text("\n".join(var_parts))
    args.stamp.write_text("")


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--stamp",
        type=pathlib.Path,
        required=True,
        help="Stamp file.",
    )
    parser.add_argument(
        "--indirect",
        action="store_true",
        help="input_file is a file that contains the actual file's filename.",
    )
    parser.add_argument(
        "input_file",
        type=pathlib.Path,
        help="File to compress.",
    )


def main(
    *,
    args: Sequence[str] = sys.argv[1:],
) -> None:
    parser = argparse.ArgumentParser()
    parser.set_defaults(subcommand=lambda args: parser.print_help())
    subparsers = parser.add_subparsers()

    dyndep_parser = subparsers.add_parser(
        "dyndep",
        help="Write a dyndep file for the compress subcommand.",
    )
    dyndep_parser.set_defaults(subcommand=_dyndep)
    _add_common_args(dyndep_parser)
    dyndep_parser.add_argument(
        "--dyndep",
        type=pathlib.Path,
        required=True,
        help="Ninja dyndep file to write.",
    )

    compress_parser = subparsers.add_parser(
        "compress",
        help="Compress a file.",
    )
    compress_parser.set_defaults(subcommand=_compress)
    _add_common_args(compress_parser)

    parsed_args = parser.parse_args(args)
    parsed_args.subcommand(parsed_args)


if __name__ == "__main__":
    main()
