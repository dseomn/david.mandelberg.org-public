# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import collections
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
import dataclasses
import datetime
import email.headerregistry
import email.utils
import functools
import http
import itertools
import tomllib
from typing import Any, final, Literal, override, Self
import urllib.parse
import uuid as uuid_

import ginjarator

from dseomn_website import lint
from dseomn_website import paths


def _require_timezone(value: datetime.datetime) -> None:
    if value.tzinfo is None:
        raise ValueError(f"{value} has no timezone.")


def _comment_datetime(value: datetime.datetime | str) -> datetime.datetime:
    if isinstance(value, datetime.datetime):
        parsed = value
    else:
        parsed = email.utils.parsedate_to_datetime(value)
    _require_timezone(parsed)
    return parsed.astimezone(datetime.timezone.utc)


def _duplicates[T](iterable: Iterable[T]) -> Collection[T]:
    counter = collections.Counter(iterable)
    return tuple(item for item, count in counter.items() if count > 1)


def _title_join(*, parent: str, child: str) -> str:
    return f"{child} — {parent}"


@dataclasses.dataclass(frozen=True, kw_only=True)
class User:
    name: str
    uri: str | None = None
    email_address: str | None = None

    @classmethod
    def parse(cls, raw: Any) -> Self:
        if isinstance(raw, str):
            return {
                "dseomn": cls(
                    name="David Mandelberg",
                    uri="/",
                    email_address="david@mandelberg.org",
                ),
            }[raw]
        if unexpected_keys := raw.keys() - {"name", "uri", "email_address"}:
            raise ValueError(f"Unexpected keys: {unexpected_keys}")
        return cls(
            name=raw["name"],
            uri=raw.get("uri"),
            email_address=raw.get("email_address"),
        )

    def email_address_with_extension(self, extension: str) -> str:
        delimiter = "+"
        address = email.headerregistry.Address(addr_spec=self.email_address)
        if delimiter in address.username:
            raise ValueError(
                f"Address already has extension: {address.addr_spec!r}"
            )
        address_with_extension = email.headerregistry.Address(
            username=f"{address.username}{delimiter}{extension}",
            domain=address.domain,
        )
        if len(address_with_extension.username.encode("utf-8")) > 64:
            # https://datatracker.ietf.org/doc/html/rfc5321#section-4.5.3.1.1
            raise ValueError(
                f"Local part is too long: {address_with_extension.addr_spec!r}"
            )
        return address_with_extension.addr_spec


@dataclasses.dataclass(frozen=True, kw_only=True)
class Site:
    url: str
    title: str
    author: User
    language: str
    direction: str
    tags: Sequence[str]


SITE = Site(
    url="https://david.mandelberg.org",
    title="David Mandelberg",
    author=User.parse("dseomn"),
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
class Resource:
    url_path: str

    @property
    def url(self) -> str:
        return urllib.parse.urljoin(SITE.url, self.url_path)

    def fragment(self, id: str) -> "Fragment":
        return Fragment(
            url_path=urllib.parse.urljoin(
                self.url_path,
                f"#{urllib.parse.quote(id)}",
            ),
        )


@dataclasses.dataclass(frozen=True, kw_only=True)
class Fragment(Resource):

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError(f"{self} has no fragment ID.")

    @functools.cached_property
    def id(self) -> str:
        return urllib.parse.unquote(
            urllib.parse.urlsplit(self.url_path).fragment
        )

    @functools.cached_property
    def url_fragment(self) -> str:
        return f"#{self.id}"


@dataclasses.dataclass(frozen=True, kw_only=True)
class MediaItem:
    type_: str
    source: ginjarator.paths.Filesystem
    gallery: str | None
    opengraph: bool


@dataclasses.dataclass(frozen=True, kw_only=True)
class Image(MediaItem):
    type_: Literal["image"] = "image"
    alt: str
    float_: bool
    main: bool


def _parse_media_item(raw: Any) -> MediaItem:
    known_keys = {"type", "source", "gallery", "opengraph"}
    common_kwargs = dict(
        source=ginjarator.paths.Filesystem(raw["source"]),
        gallery=raw.get("gallery"),
        opengraph=raw.get("opengraph", False),
    )
    match raw["type"]:
        case "image":
            known_keys.update(("alt", "float", "main"))
            item = Image(
                **common_kwargs,
                alt=raw["alt"],
                float_=raw.get("float", False),
                main=raw.get("main", False),
            )
        case _:
            raise ValueError(f"Unknown media item type: {raw!r}")
    if unexpected_keys := raw.keys() - known_keys:
        raise ValueError(f"Unexpected keys: {unexpected_keys}")
    return item


@dataclasses.dataclass(frozen=True, kw_only=True)
class Media:
    item_by_source: Mapping[ginjarator.paths.Filesystem, MediaItem]

    @classmethod
    def parse(cls, raw: Any) -> Self:
        if unexpected_keys := raw.keys() - {"items"}:
            raise ValueError(f"Unexpected keys: {unexpected_keys}")
        item_by_source = {}
        for item_raw in raw.get("items", []):
            item = _parse_media_item(item_raw)
            if item.source in item_by_source:
                raise ValueError(f"Duplicate item source: {item.source}")
            item_by_source[item.source] = item
        return cls(item_by_source=item_by_source)

    @functools.cached_property
    def item_by_source_str(self) -> Mapping[str, MediaItem]:
        return {
            str(source): item for source, item in self.item_by_source.items()
        }


_COMMENTS_PER_FEED = 50


@dataclasses.dataclass(frozen=True, kw_only=True)
class Comment(Fragment):
    uuid: uuid_.UUID
    published: datetime.datetime
    author: User
    in_reply_to: uuid_.UUID | None
    contents_path: ginjarator.paths.Filesystem

    @classmethod
    def load(
        cls,
        *,
        parent_url_path: str,
        parent_path: ginjarator.paths.Filesystem,
        comment_id: str,
        comment_uuid: uuid_.UUID,
    ) -> Self:
        raw = tomllib.loads(
            ginjarator.api().fs.read_text(
                parent_path / f"{comment_uuid}.toml",
                defer_ok=False,
            )
        )
        if unexpected_keys := raw.keys() - {
            "published",
            "author",
            "in_reply_to",
        }:
            raise ValueError(f"Unexpected keys: {unexpected_keys}")
        return cls(
            url_path=urllib.parse.urljoin(
                parent_url_path,
                f"#{urllib.parse.quote(comment_id)}",
            ),
            uuid=comment_uuid,
            published=_comment_datetime(raw["published"]),
            author=User.parse(raw["author"]),
            in_reply_to=(
                uuid_.UUID(raw["in_reply_to"]) if "in_reply_to" in raw else None
            ),
            contents_path=parent_path / f"{comment_uuid}.html",
        )

    @functools.cached_property
    def contents(self) -> str:
        contents = ginjarator.api().fs.read_text(
            self.contents_path,
            defer_ok=False,
        )
        lint.comment(contents)
        return contents

    @functools.cached_property
    def atom_fragment_path(self) -> ginjarator.paths.Filesystem:
        return paths.WORK / f"comments/{self.uuid}/fragment.atom"

    @functools.cached_property
    def pseudo_title(self) -> str:
        """Synthesized title for places like atom feeds that require them."""
        return f"Comment by {self.author.name} on {self.published}"


@dataclasses.dataclass(frozen=True, kw_only=True)
class Feed[EntryType](Resource):
    title: str
    updated_callback: Callable[[], datetime.datetime]
    entries_callback: Callable[[], Sequence[EntryType]]

    @functools.cached_property
    def updated(self) -> datetime.datetime:
        return self.updated_callback()

    @functools.cached_property
    def entries(self) -> Sequence[EntryType]:
        return self.entries_callback()


@dataclasses.dataclass(frozen=True, kw_only=True)
class Page(Resource):
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
    def full_title(self) -> str:
        return _title_join(parent=SITE.title, child=self.title)


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
            url_path=urllib.parse.quote(f"/errors/{status.value}/"),
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
            url_path=urllib.parse.quote(
                f"/{template.relative_to("standalone").parent}/"
            ),
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
    return urllib.parse.quote(f"/{published.strftime("%Y/%m/%d")}/{slug}/")


@dataclasses.dataclass(frozen=True, kw_only=True)
class Post(Page):
    id: str
    uuid: uuid_.UUID
    published: datetime.datetime
    author: User
    tags: Sequence[str]
    url_path_aliases: Collection[str]
    comments: Sequence[Comment]

    def _comment_in_reply_to_is_valid(self, comment: Comment) -> bool:
        if comment.in_reply_to is None:
            return True
        if comment.in_reply_to not in self.comment_by_uuid:
            return False
        parent = self.comment_by_uuid[comment.in_reply_to]
        if comment.published <= parent.published:
            # In addition to catching mistakes, this also prevents graph cycles.
            return False
        return True

    def __post_init__(self) -> None:
        if unknown_tags := set(self.tags) - set(SITE.tags):
            raise ValueError(f"Unknown tags: {unknown_tags}")
        if list(self.tags) != sorted(set(self.tags)):
            raise ValueError(f"{self.tags} is not sorted and unique.")
        if list(self.comments) != sorted(
            self.comments,
            key=lambda comment: comment.published,
        ):
            raise ValueError(f"{self.comments} is not sorted.")
        if invalid_replies := {
            comment
            for comment in self.comments
            if not self._comment_in_reply_to_is_valid(comment)
        }:
            raise ValueError(
                f"{invalid_replies} have invalid in_reply_to fields."
            )

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
            "comments",
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
            uuid=uuid_.UUID(raw["uuid"]),
            published=published,
            author=(
                User.parse(raw["author"]) if "author" in raw else SITE.author
            ),
            tags=tuple(raw.get("tags", [])),
            url_path_aliases=(
                frozenset((_post_url_path(published_local, slug),)) - {url_path}
            ),
            comments=tuple(
                Comment.load(
                    parent_url_path=url_path,
                    parent_path=(
                        paths.PRIVATE / "posts" / source_dir_name / "comments"
                    ),
                    comment_id=f"{source_dir_name}-comment-{comment_uuid}",
                    comment_uuid=uuid_.UUID(comment_uuid),
                )
                for comment_uuid in raw.get("comments", [])
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
        return self.work_path / "fragment.atom"

    @functools.cached_property
    def comments_section(self) -> Fragment:
        return self.fragment(f"{self.id}-comments")

    @functools.cached_property
    def comment_by_uuid(self) -> Mapping[uuid_.UUID, Comment]:
        return {comment.uuid: comment for comment in self.comments}

    @functools.cached_property
    def comments_by_parent(
        self,
    ) -> Mapping[uuid_.UUID | None, Sequence[Comment]]:
        result: dict[uuid_.UUID | None, list[Comment]] = {
            None: [],
            **{comment.uuid: [] for comment in self.comments},
        }
        for comment in self.comments:
            result[comment.in_reply_to].append(comment)
        assert collections.Counter(
            itertools.chain.from_iterable(result.values())
        ) == collections.Counter(self.comments)
        return result

    @functools.cached_property
    def _comments_feed_entries(self) -> Sequence[Comment]:
        return sorted(
            self.comments,
            key=lambda comment: comment.published,
            reverse=True,
        )[:_COMMENTS_PER_FEED]

    @functools.cached_property
    def _comments_feed_updated(self) -> datetime.datetime:
        if self._comments_feed_entries:
            return self._comments_feed_entries[0].published
        else:
            return self.published

    @functools.cached_property
    def comments_feed(self) -> Feed[Comment]:
        return Feed(
            url_path=urllib.parse.urljoin(self.url_path, "comments/feed/"),
            title=_title_join(parent=self.full_title, child="Comments"),
            updated_callback=lambda: self._comments_feed_updated,
            entries_callback=lambda: self._comments_feed_entries,
        )


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
            url_path=urllib.parse.quote(f"/tag/{tag}/"),
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
            return urllib.parse.urljoin(self.url_path, f"page/{page_number}/")

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
                    urllib.parse.urljoin(
                        page.url_path,
                        f"#{urllib.parse.quote(post.id)}",
                    ),
                )
        return result

    @functools.cached_property
    def feed(self) -> Feed[Post]:
        return Feed(
            url_path=urllib.parse.urljoin(self.url_path, "feed/"),
            title=self.full_title,
            updated_callback=lambda: self.posts[0].published,
            entries_callback=lambda: self.posts[:_POSTS_PER_FEED],
        )

    @functools.cached_property
    def _comments_feed_entries(self) -> Sequence[Comment]:
        return tuple(
            sorted(
                itertools.chain.from_iterable(
                    post.comments for post in self.posts
                ),
                key=lambda comment: comment.published,
                reverse=True,
            )[:_COMMENTS_PER_FEED]
        )

    @functools.cached_property
    def _comments_feed_updated(self) -> datetime.datetime:
        if self._comments_feed_entries:
            return self._comments_feed_entries[0].published
        else:
            # In theory, the comments feed should have been created when the
            # list was created. Since empty lists aren't allowed, that should be
            # when the first post was published. In practice, that's probably
            # not always right, but it's probably good enough.
            return min(post.published for post in self.posts)

    @functools.cached_property
    def comments_feed(self) -> Feed[Comment]:
        return Feed(
            url_path=urllib.parse.urljoin(self.url_path, "comments/feed/"),
            title=_title_join(parent=self.full_title, child="Comments"),
            updated_callback=lambda: self._comments_feed_updated,
            entries_callback=lambda: self._comments_feed_entries,
        )


def main_nav() -> Sequence[Page]:
    return (
        PostList.main(),
        *Standalone.all(),
    )
