#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0
"""Creates a copy of a file, with part of the hash in the new filename."""
# TODO: https://github.com/ninja-build/ninja/issues/1186 - Consider using
# symlinks instead of copies.

import argparse
import base64
from collections.abc import Sequence
import hashlib
import json
import pathlib
import sys
import textwrap


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


def _output_filename_path(
    *,
    work_dir: pathlib.Path,
    input_file: pathlib.Path,
) -> pathlib.Path:
    return work_dir / f"{input_file.name}.cache-buster-output-filename"


def _hash(args: argparse.Namespace) -> None:
    file_hash = base64.urlsafe_b64encode(
        hashlib.sha256(args.input_file.read_bytes()).digest()[:16]
    ).decode()
    if args.image_size_from_metadata is None:
        output_filename_extra = ""
    else:
        image_metadata = json.loads(args.image_size_from_metadata.read_text())[
            0
        ]["image"]
        image_width = image_metadata["geometry"]["width"]
        image_height = image_metadata["geometry"]["height"]
        output_filename_extra = f"-{image_width}x{image_height}"
    _output_filename_path(
        work_dir=args.work_dir,
        input_file=args.input_file,
    ).write_text(
        f"output/assets/{args.output_filename_base.stem}{output_filename_extra}"
        f"-{file_hash}{args.output_filename_base.suffix}"
    )


def _dyndep(args: argparse.Namespace) -> None:
    output_filenames = frozenset(
        _output_filename_path(
            work_dir=args.work_dir,
            input_file=input_file,
        ).read_text()
        for input_file in args.input_file
    )
    args.dyndep.write_text(
        textwrap.dedent(
            f"""\
            ninja_dyndep_version = 1
            build $
                    {_ninja_escape(str(args.copy_stamp))} $
                    | $
                    {" ".join(map(_ninja_escape, output_filenames))} $
                    : $
                    dyndep
            """
        )
    )


def _copy(args: argparse.Namespace) -> None:
    written = set[pathlib.Path]()
    for input_file in args.input_file:
        output_path = pathlib.Path(
            _output_filename_path(
                work_dir=args.work_dir,
                input_file=input_file,
            ).read_text()
        )
        if output_path in written:
            if input_file.read_bytes() != output_path.read_bytes():
                raise ValueError(
                    "Multiple files with different contents hash to "
                    f"{str(output_path)!r}"
                )
        else:
            output_path.write_bytes(input_file.read_bytes())
            written.add(output_path)
    args.copy_stamp.write_text("")


def main(
    *,
    args: Sequence[str] = sys.argv[1:],
) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=pathlib.Path,
        required=True,
        help="Directory to keep work files in.",
    )
    parser.set_defaults(subcommand=lambda args: parser.print_help())
    subparsers = parser.add_subparsers()

    hash_parser = subparsers.add_parser(
        "hash",
        help="Hash a file for cache busting.",
    )
    hash_parser.set_defaults(subcommand=_hash)
    hash_parser.add_argument(
        "--output-filename-base",
        type=pathlib.PurePath,
        required=True,
        help="Output filename, without directory or hash.",
    )
    hash_parser.add_argument(
        "--image-size-from-metadata",
        default=None,
        type=pathlib.Path,
        help=(
            "Image metadata file to get the size from to add to the output "
            "filename."
        ),
    )
    hash_parser.add_argument(
        "input_file",
        type=pathlib.Path,
        help="File to hash and copy.",
    )

    dyndep_parser = subparsers.add_parser(
        "dyndep",
        help="Write a dyndep file for the copy subcommand.",
    )
    dyndep_parser.set_defaults(subcommand=_dyndep)
    dyndep_parser.add_argument(
        "--dyndep",
        type=pathlib.Path,
        required=True,
        help="Ninja dyndep file to write.",
    )
    dyndep_parser.add_argument(
        "--copy-stamp",
        type=pathlib.Path,
        required=True,
        help="Stamp file for the copy subcommand.",
    )
    dyndep_parser.add_argument(
        "input_file",
        nargs="+",
        type=pathlib.Path,
        help="File to hash and copy.",
    )

    copy_parser = subparsers.add_parser(
        "copy",
        help="Create a copy containing the hash in the filename.",
    )
    copy_parser.set_defaults(subcommand=_copy)
    copy_parser.add_argument(
        "--copy-stamp",
        type=pathlib.Path,
        required=True,
        help="Stamp file for the copy subcommand.",
    )
    copy_parser.add_argument(
        "input_file",
        nargs="+",
        type=pathlib.Path,
        help="File to hash and copy.",
    )

    parsed_args = parser.parse_args(args)
    parsed_args.subcommand(parsed_args)


if __name__ == "__main__":
    main()
