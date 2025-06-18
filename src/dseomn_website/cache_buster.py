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


def _hash(args: argparse.Namespace) -> None:
    file_hash = base64.urlsafe_b64encode(
        hashlib.sha256(args.file.read_bytes()).digest()[:16]
    ).decode()
    filename = "".join((args.prefix, file_hash, args.suffix))
    copy_stamp = f"{args.write_filename}.copy-stamp"
    args.dyndep.write_text(
        textwrap.dedent(
            f"""\
            ninja_dyndep_version = 1
            build $
                    {_ninja_escape(copy_stamp)} $
                    | $
                    {_ninja_escape(filename)} $
                    : $
                    dyndep
            """
        )
    )
    args.write_filename.write_text(filename)


def _copy(args: argparse.Namespace) -> None:
    copy_path = pathlib.Path(args.read_filename.read_text())
    copy_path.write_bytes(args.file.read_bytes())
    pathlib.Path(f"{args.read_filename}.copy-stamp").write_text("")


def main(
    *,
    args: Sequence[str] = sys.argv[1:],
) -> None:
    parser = argparse.ArgumentParser()
    parser.set_defaults(subcommand=lambda args: parser.print_help())
    subparsers = parser.add_subparsers()

    hash_parser = subparsers.add_parser(
        "hash",
        help="Hash a file for cache busting.",
    )
    hash_parser.set_defaults(subcommand=_hash)
    hash_parser.add_argument(
        "--dyndep",
        type=pathlib.Path,
        required=True,
        help="Ninja dyndep file to write.",
    )
    hash_parser.add_argument(
        "--write-filename",
        type=pathlib.Path,
        required=True,
        help="File to write the filename with the hash to.",
    )
    hash_parser.add_argument(
        "--prefix",
        required=True,
        help="Part of the resulting path, before the hash.",
    )
    hash_parser.add_argument(
        "--suffix",
        required=True,
        help="Part of the resulting path, after the hash.",
    )
    hash_parser.add_argument(
        "file",
        type=pathlib.Path,
        help="File to hash.",
    )

    copy_parser = subparsers.add_parser(
        "copy",
        help="Create a copy containing the hash in the filename.",
    )
    copy_parser.set_defaults(subcommand=_copy)
    copy_parser.add_argument(
        "--read-filename",
        type=pathlib.Path,
        required=True,
        help="File to read the filename from.",
    )
    copy_parser.add_argument(
        "file",
        type=pathlib.Path,
        help="File to copy.",
    )

    parsed_args = parser.parse_args(args)
    parsed_args.subcommand(parsed_args)


if __name__ == "__main__":
    main()
