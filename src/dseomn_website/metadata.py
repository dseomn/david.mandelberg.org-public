# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import collections
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
import dataclasses
import datetime
import functools
import http
import itertools
import tomllib
from typing import Any, final, override, Self
import uuid

import ginjarator

from dseomn_website import paths


def _require_timezone(value: datetime.datetime) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{value} has no timezone.")


def _duplicates[T](iterable: Iterable[T]) -> Collection[T]:
    counter = collections.Counter(iterable)
    return tuple(item for item, count in counter.items() if count > 1)


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
class Media:
    profile_names_by_image: Mapping[
        ginjarator.paths.Filesystem, Collection[str]
    ]

    @classmethod
    def parse(cls, raw: Any) -> Self:
        if unexpected_keys := raw.keys() - {"images"}:
            raise ValueError(f"Unexpected keys: {unexpected_keys}")
        profile_names_by_image = collections.defaultdict[
            ginjarator.paths.Filesystem, set[str]
        ](set)
        for profile_name, sources in raw.get("images", {}).items():
            for source in sources:
                profile_names_by_image[ginjarator.paths.Filesystem(source)].add(
                    profile_name
                )
        return cls(
            profile_names_by_image=profile_names_by_image,
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class Page:
    url_path: str
    title: str
    media: Media = Media.parse({})

    @classmethod
    def all(cls) -> Collection[Self]:
        return tuple(
            itertools.chain.from_iterable(
                subclass.all() for subclass in cls.__subclasses__()
            )
        )

    @property
    def url(self) -> str:
        return SITE.url + self.url_path

    @property
    def full_title(self) -> str:
        return f"{self.title} — {SITE.title}"


@dataclasses.dataclass(frozen=True, kw_only=True)
class Error(Page):
    status: http.HTTPStatus

    @classmethod
    def load(cls, template: ginjarator.paths.Filesystem) -> Self:
        raw = tomllib.loads(
            ginjarator.api().fs.read_text(
                template.parent / "metadata.toml",
                defer_ok=False,
            )
        )
        if unexpected_keys := raw.keys() - {"media"}:
            raise ValueError(f"Unexpected keys: {unexpected_keys}")
        status = http.HTTPStatus(int(template.parent.name))
        return cls(
            url_path=f"/errors/{status.value}/",
            title=f"{status.value} {status.phrase}",
            media=Media.parse(raw.get("media", {})),
            status=status,
        )

    @override
    @classmethod
    def all(cls) -> Collection[Self]:
        return tuple(
            cls.load(template)
            for template in ginjarator.api().fs.read_config().templates
            if template.is_relative_to("errors")
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class Standalone(Page):
    @classmethod
    def load(cls, template: ginjarator.paths.Filesystem) -> Self:
        raw = tomllib.loads(
            ginjarator.api().fs.read_text(
                template.parent / "metadata.toml",
                defer_ok=False,
            )
        )
        if unexpected_keys := raw.keys() - {"title", "media"}:
            raise ValueError(f"Unexpected keys: {unexpected_keys}")
        return cls(
            url_path=f"/{template.relative_to("standalone").parent}/",
            title=raw["title"],
            media=Media.parse(raw.get("media", {})),
        )

    @override
    @classmethod
    def all(cls) -> Sequence[Self]:
        # This method is called by all pages for the nav links, so avoid
        # read_config() to prevent re-rendering all pages when the list of
        # templates changes. Also, the order is important for the nav links.
        return tuple(
            cls.load(ginjarator.paths.Filesystem(template))
            for template in ("standalone/about/index.html.jinja",)
        )


def _post_url_path(published: datetime.datetime, slug: str) -> str:
    return f"/{published.strftime("%Y/%m/%d")}/{slug}/"


@dataclasses.dataclass(frozen=True, kw_only=True)
class Post(Page):
    id: str
    uuid: uuid.UUID
    published: datetime.datetime
    author: str
    tags: Sequence[str]
    url_path_aliases: Collection[str]

    def __post_init__(self) -> None:
        if unknown_tags := set(self.tags) - set(SITE.tags):
            raise ValueError(f"Unknown tags: {unknown_tags}")
        if list(self.tags) != sorted(set(self.tags)):
            raise ValueError(f"{self.tags} is not sorted and unique.")

    @classmethod
    def load(cls, template: ginjarator.paths.Filesystem) -> Self:
        raw = tomllib.loads(
            ginjarator.api().fs.read_text(
                template.parent / "metadata.toml",
                defer_ok=False,
            )
        )
        if unexpected_keys := raw.keys() - {
            "uuid",
            "published",
            "title",
            "author",
            "tags",
            "media",
        }:
            raise ValueError(f"Unexpected keys: {unexpected_keys}")
        published_local = raw["published"]
        _require_timezone(published_local)
        published = published_local.astimezone(datetime.timezone.utc)
        source_dir_name = template.parent.name
        source_dir_date_prefix = published.strftime("%Y-%m-%d-")
        if not source_dir_name.startswith(source_dir_date_prefix):
            raise ValueError(
                f"{template}'s published date and directory name don't match."
            )
        slug = source_dir_name.removeprefix(source_dir_date_prefix)
        url_path = _post_url_path(published, slug)
        return cls(
            url_path=url_path,
            title=raw["title"],
            media=Media.parse(raw.get("media", {})),
            id=source_dir_name,
            uuid=uuid.UUID(raw["uuid"]),
            published=published,
            author=raw.get("author", SITE.author),
            tags=tuple(raw.get("tags", [])),
            url_path_aliases=(
                frozenset((_post_url_path(published_local, slug),)) - {url_path}
            ),
        )

    @override
    @classmethod
    def all(cls) -> Sequence[Self]:
        posts = sorted(
            (
                cls.load(template)
                for template in ginjarator.api().fs.read_config().templates
                if template.is_relative_to("posts")
                and template.parent != ginjarator.paths.Filesystem("posts")
            ),
            key=lambda post_metadata: post_metadata.published,
            reverse=True,
        )
        if url_path_duplicates := _duplicates(
            itertools.chain.from_iterable(
                {post.url_path, *post.url_path_aliases} for post in posts
            )
        ):
            raise ValueError(f"Duplicate URL paths: {url_path_duplicates}")
        if uuid_duplicates := _duplicates(post.uuid for post in posts):
            raise ValueError(f"Duplicate uuids: {uuid_duplicates}")
        if published_duplicates := _duplicates(
            post.published for post in posts
        ):
            raise ValueError(
                f"Duplicate published dates: {published_duplicates}"
            )
        return posts

    @property
    def work_path(self) -> ginjarator.paths.Filesystem:
        return paths.WORK / "posts" / self.id

    @property
    def include_fragment_path(self) -> ginjarator.paths.Filesystem:
        return self.work_path / "include-fragment.html"

    @property
    def atom_fragment_path(self) -> ginjarator.paths.Filesystem:
        return self.work_path / "atom-fragment.xml"


_POSTS_PER_PAGE = 10
_POSTS_PER_FEED = 20


@final
@dataclasses.dataclass(frozen=True, kw_only=True)
class PostListPage(Page):
    page_number: int
    posts: Sequence[Post]

    @override
    @classmethod
    def all(cls) -> Collection[Self]:
        return tuple(
            itertools.chain.from_iterable(
                post_list.page_by_number.values()
                for post_list in PostList.all()
            )
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class PostList(Page):
    filter: Callable[[Post], bool]

    @classmethod
    def main(cls) -> Self:
        return cls(
            url_path="/",
            title="Blog",
            filter=lambda post: True,
        )

    @classmethod
    def tag(cls, tag: str) -> Self:
        return cls(
            url_path=f"/tag/{tag}/",
            title=f"Tag: {tag}",
            filter=lambda post: tag in post.tags,
        )

    @override
    @classmethod
    def all(cls) -> Collection[Self]:
        return (
            cls.main(),
            *(cls.tag(tag) for tag in SITE.tags),
        )

    @functools.cached_property
    def posts(self) -> Sequence[Post]:
        return tuple(post for post in Post.all() if self.filter(post))

    def _page_url_path(self, page_number: int) -> str:
        if page_number == 1:
            return self.url_path
        else:
            return f"{self.url_path}page/{page_number}/"

    def _page_title(self, page_number: int) -> str:
        if page_number == 1:
            return self.title
        else:
            return f"{self.title} (page {page_number})"

    @functools.cached_property
    def page_by_number(self) -> Mapping[int, PostListPage]:
        return {
            page_number: PostListPage(
                url_path=self._page_url_path(page_number),
                title=self._page_title(page_number),
                page_number=page_number,
                posts=page_posts,
            )
            for page_number, page_posts in enumerate(
                itertools.batched(self.posts, _POSTS_PER_PAGE),
                start=1,
            )
        }

    @functools.cached_property
    def link_by_year(self) -> Mapping[int, str]:
        """Links to the most recent post of each year."""
        result = dict[int, str]()
        for page in self.page_by_number.values():
            for post in page.posts:
                result.setdefault(
                    post.published.year,
                    f"{page.url_path}#{post.id}",
                )
        return result

    @property
    def feed_url_path(self) -> str:
        return f"{self.url_path}feed/"

    @functools.cached_property
    def feed_posts(self) -> Sequence[Post]:
        return self.posts[:_POSTS_PER_FEED]


def main_nav() -> Sequence[Page]:
    return (
        PostList.main(),
        *Standalone.all(),
    )
