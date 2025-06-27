# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
import dataclasses
import datetime
import tomllib
from typing import Self

import ginjarator

from dseomn_website import paths


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
class Page:
    url_path: str
    title: str

    @property
    def url(self) -> str:
        return SITE.url + self.url_path

    @property
    def full_title(self) -> str:
        return f"{self.title} — {SITE.title}"


STANDALONE_PAGES = {
    ginjarator.paths.Filesystem("standalone/about/index.html.jinja"): Page(
        url_path="/about/",
        title="About",
    ),
}


@dataclasses.dataclass(frozen=True, kw_only=True)
class Post(Page):
    id: str
    uuid: str
    published: datetime.datetime
    author: str
    tags: Sequence[str]

    def __post_init__(self) -> None:
        if unknown_tags := set(self.tags) - set(SITE.tags):
            raise ValueError(f"Unknown tags: {unknown_tags}")
        if list(self.tags) != sorted(set(self.tags)):
            raise ValueError(f"{self.tags} is not sorted and unique.")

    @classmethod
    def load(cls, template: ginjarator.paths.Filesystem) -> Self:
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
        published = raw["published"]
        source_dir_name = template.parent.name
        source_dir_date_prefix = published.strftime("%Y-%m-%d-")
        if not source_dir_name.startswith(source_dir_date_prefix):
            raise ValueError(
                f"{template}'s published date and directory name don't match."
            )
        slug = source_dir_name.removeprefix(source_dir_date_prefix)
        return cls(
            url_path=f"/{published.strftime("%Y/%m/%d")}/{slug}/",
            title=raw["title"],
            id=source_dir_name,
            uuid=raw["uuid"],
            published=published,
            author=raw.get("author", SITE.author),
            tags=tuple(raw.get("tags", [])),
        )

    @property
    def work_path(self) -> ginjarator.paths.Filesystem:
        return paths.WORK / "posts" / self.id

    @property
    def include_fragment_path(self) -> ginjarator.paths.Filesystem:
        return self.work_path / "include-fragment.html"

    @property
    def atom_fragment_path(self) -> ginjarator.paths.Filesystem:
        return self.work_path / "atom-fragment.xml"


@dataclasses.dataclass(frozen=True, kw_only=True)
class PostList(Page):
    def page(self, page_number: int) -> Page:
        if page_number == 1:
            return Page(
                url_path=self.url_path,
                title=self.title,
            )
        else:
            return Page(
                url_path=f"{self.url_path}page/{page_number}/",
                title=f"{self.title} (page {page_number})",
            )

    @property
    def feed_url_path(self) -> str:
        return f"{self.url_path}feed/"


BLOG_MAIN_LIST = PostList(
    url_path="/",
    title="Blog",
)
BLOG_TAG_LISTS = {
    tag: PostList(
        url_path=f"/tag/{tag}/",
        title=f"Tag: {tag}",
    )
    for tag in SITE.tags
}
