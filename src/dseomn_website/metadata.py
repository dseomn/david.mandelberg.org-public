# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
import dataclasses
import datetime
import pathlib
import tomllib
from typing import Self

import ginjarator


@dataclasses.dataclass(frozen=True, kw_only=True)
class Site:
    url: str
    title: str
    author: str
    email: str
    language: str
    direction: str
    tags: Sequence[str]


SITE = Site(
    url="https://david.mandelberg.org",
    title="David Mandelberg",
    author="David Mandelberg",
    email="david@mandelberg.org",
    language="en-US",
    direction="ltr",
    tags=(
        "dance",
        "music",
        "photos",
        "technology",
        "videos",
    ),
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class Post:
    uuid: str
    published: datetime.datetime
    title: str
    author: str
    tags: Sequence[str]

    def __post_init__(self) -> None:
        if unknown_tags := set(self.tags) - set(SITE.tags):
            raise ValueError(f"Unknown tags: {unknown_tags}")
        if list(self.tags) != sorted(set(self.tags)):
            raise ValueError(f"{self.tags} is not sorted and unique.")

    @classmethod
    def load(cls, template: pathlib.PurePath) -> Self:
        raw = tomllib.loads(
            ginjarator.api().fs.read_text(
                str(template.parent / "metadata.toml"),
                defer_ok=False,
            )
        )
        if unexpected_keys := raw.keys() - {
            "uuid",
            "published",
            "title",
            "author",
            "tags",
        }:
            raise ValueError(f"Unexpected keys: {unexpected_keys}")
        return cls(
            uuid=raw["uuid"],
            published=raw["published"],
            title=raw["title"],
            author=raw.get("author", SITE.author),
            tags=tuple(raw.get("tags", [])),
        )
