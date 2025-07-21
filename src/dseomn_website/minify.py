# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import subprocess


def html(document_or_fragments: str) -> str:
    return subprocess.run(
        ("minify", "--quiet", "--type=html"),
        input=document_or_fragments,
        stdout=subprocess.PIPE,
        check=True,
        text=True,
    ).stdout


def xml(document_or_fragments: str) -> str:
    return subprocess.run(
        ("minify", "--quiet", "--type=xml"),
        input=document_or_fragments,
        stdout=subprocess.PIPE,
        check=True,
        text=True,
    ).stdout
