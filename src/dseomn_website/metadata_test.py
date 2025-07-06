# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import datetime
import http
import pathlib
import textwrap
from typing import Any
import uuid

import ginjarator.testing
import pytest

from dseomn_website import metadata
from dseomn_website import paths


def test_user_parse_error() -> None:
    with pytest.raises(ValueError, match=r"invalid_key_kumquat"):
        metadata.User.parse(dict(name="foo", invalid_key_kumquat=42))


@pytest.mark.parametrize(
    "raw,expected",
    (
        (
            "dseomn",
            metadata.User(
                name="David Mandelberg",
                uri="/",
                email_address="david@mandelberg.org",
            ),
        ),
        (
            dict(name="Someone"),
            metadata.User(name="Someone"),
        ),
        (
            dict(
                name="Someone",
                uri="https://example.com",
                email_address="someone@example.com",
            ),
            metadata.User(
                name="Someone",
                uri="https://example.com",
                email_address="someone@example.com",
            ),
        ),
    ),
)
def test_user_parse(raw: Any, expected: metadata.User) -> None:
    assert metadata.User.parse(raw) == expected


@pytest.mark.parametrize(
    "email_address,extension,error_regex",
    (
        ("someone+foo@example.com", "bar", r"already has extension"),
        ("someone@example.com", "a" * 64, r"too long"),
    ),
)
def test_user_email_address_with_extension_error(
    email_address: str,
    extension: str,
    error_regex: str,
) -> None:
    user = metadata.User(name="Someone", email_address=email_address)
    with pytest.raises(ValueError, match=error_regex):
        user.email_address_with_extension(extension)


def test_user_email_address_with_extension() -> None:
    user = metadata.User(name="Someone", email_address="someone@example.com")
    assert user.email_address_with_extension("foo") == "someone+foo@example.com"


def test_site() -> None:
    assert list(metadata.SITE.tags) == sorted(set(metadata.SITE.tags))


def test_resource_url() -> None:
    assert (
        metadata.Resource(url_path="/foo/").url
        == "https://david.mandelberg.org/foo/"
    )


def test_media_parse_error() -> None:
    with pytest.raises(ValueError, match=r"invalid_key_kumquat"):
        metadata.Media.parse(dict(invalid_key_kumquat=42))


def test_media_parse() -> None:
    assert metadata.Media.parse(
        dict(
            images=dict(
                figure=["foo.png"],
                main=["foo.png", "bar.jpg"],
            ),
        ),
    ) == metadata.Media(
        profile_names_by_image={
            ginjarator.paths.Filesystem("foo.png"): {"figure", "main"},
            ginjarator.paths.Filesystem("bar.jpg"): {"main"},
        },
    )


@pytest.mark.parametrize(
    "contents,error_regex",
    (
        (
            textwrap.dedent(
                """\
                published = 2025-07-03 15:47:37-04:00
                author = "dseomn"
                invalid_key_kumquat = "bar"
                """
            ),
            r"invalid_key_kumquat",
        ),
        (
            textwrap.dedent(
                """\
                published = 2025-07-03 15:47:37
                author = "dseomn"
                """
            ),
            r"no timezone",
        ),
    ),
)
def test_comment_load_error(
    contents: str,
    error_regex: str,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["comments"]
            """
        )
    )
    (tmp_path / "comments").mkdir()
    (
        tmp_path / "comments/6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc.toml"
    ).write_text(contents)

    with ginjarator.testing.api_for_scan(root_path=tmp_path):
        with pytest.raises(ValueError, match=error_regex):
            metadata.Comment.load(
                parent_url_path="/",
                parent_path=ginjarator.paths.Filesystem("comments"),
                comment_id="comment-6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc",
                comment_uuid=uuid.UUID("6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc"),
            )


@pytest.mark.parametrize(
    "contents,expected",
    (
        (
            textwrap.dedent(
                """\
                published = 2025-07-03 15:47:37-04:00
                author.name = "Someone Else"
                """
            ),
            metadata.Comment(
                url_path="/#comment-6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc",
                id="comment-6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc",
                uuid=uuid.UUID("6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc"),
                published=datetime.datetime.fromisoformat(
                    "2025-07-03 19:47:37Z"
                ),
                author=metadata.User(name="Someone Else"),
                in_reply_to=None,
                contents_path=ginjarator.paths.Filesystem(
                    "comments/6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc.html"
                ),
            ),
        ),
        (
            textwrap.dedent(
                """\
                published = "Thu, 3 Jul 2025 15:56:21 -0400"
                author.name = "Someone Else"
                """
            ),
            metadata.Comment(
                url_path="/#comment-6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc",
                id="comment-6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc",
                uuid=uuid.UUID("6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc"),
                published=datetime.datetime.fromisoformat(
                    "2025-07-03 19:56:21Z"
                ),
                author=metadata.User(name="Someone Else"),
                in_reply_to=None,
                contents_path=ginjarator.paths.Filesystem(
                    "comments/6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc.html"
                ),
            ),
        ),
        (
            textwrap.dedent(
                """\
                published = 2025-07-03 15:47:37-04:00
                author.name = "Someone Else"
                in_reply_to = "4e276685-4c4d-4e68-9d87-388363160661"
                """
            ),
            metadata.Comment(
                url_path="/#comment-6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc",
                id="comment-6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc",
                uuid=uuid.UUID("6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc"),
                published=datetime.datetime.fromisoformat(
                    "2025-07-03 19:47:37Z"
                ),
                author=metadata.User(name="Someone Else"),
                in_reply_to=uuid.UUID("4e276685-4c4d-4e68-9d87-388363160661"),
                contents_path=ginjarator.paths.Filesystem(
                    "comments/6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc.html"
                ),
            ),
        ),
    ),
)
def test_comment_load(
    contents: str,
    expected: metadata.Comment,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["comments"]
            """
        )
    )
    (tmp_path / "comments").mkdir()
    (
        tmp_path / "comments/6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc.html"
    ).write_text("<p>kumquat")
    (
        tmp_path / "comments/6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc.toml"
    ).write_text(contents)

    with ginjarator.testing.api_for_scan(root_path=tmp_path):
        actual = metadata.Comment.load(
            parent_url_path="/",
            parent_path=ginjarator.paths.Filesystem("comments"),
            comment_id="comment-6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc",
            comment_uuid=uuid.UUID("6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc"),
        )

        assert actual == expected
        assert actual.contents == "<p>kumquat"


def test_comment_contents_error(tmp_path: pathlib.Path) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["comments"]
            """
        )
    )
    (tmp_path / "comments").mkdir()
    (
        tmp_path / "comments/6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc.html"
    ).write_text("<script></script>")
    (
        tmp_path / "comments/6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc.toml"
    ).write_text(
        textwrap.dedent(
            """\
            published = 2025-07-03 15:47:37-04:00
            author.name = "Someone Else"
            """
        )
    )
    with ginjarator.testing.api_for_scan(root_path=tmp_path):
        comment = metadata.Comment.load(
            parent_url_path="/",
            parent_path=ginjarator.paths.Filesystem("comments"),
            comment_id="comment-6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc",
            comment_uuid=uuid.UUID("6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc"),
        )

        with pytest.raises(ValueError, match=r"Not allowed"):
            comment.contents


def test_page_all() -> None:
    with ginjarator.testing.api_for_scan():
        assert metadata.Page.all()


def test_page_full_title() -> None:
    assert (
        metadata.Page(url_path="/foo/", title="Foo").full_title
        == "Foo — David Mandelberg"
    )


def test_error_load_error(tmp_path: pathlib.Path) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["errors"]
            templates = ["errors/404/index.html.jinja"]
            """
        )
    )
    (tmp_path / "errors/404").mkdir(parents=True)
    (tmp_path / "errors/404/index.html.jinja").write_text("")
    (tmp_path / "errors/404/metadata.toml").write_text(
        textwrap.dedent(
            """\
            invalid_key_kumquat = "bar"
            """
        )
    )

    with ginjarator.testing.api_for_scan(root_path=tmp_path):
        with pytest.raises(ValueError, match=r"invalid_key_kumquat"):
            metadata.Error.load(
                ginjarator.paths.Filesystem("errors/404/index.html.jinja")
            )


def test_error_load() -> None:
    with ginjarator.testing.api_for_scan():
        error_metadata = metadata.Error.load(
            ginjarator.paths.Filesystem("errors/404/index.html.jinja")
        )

    assert error_metadata.url_path == "/errors/404/"
    assert error_metadata.title == "404 Not Found"
    assert error_metadata.status == http.HTTPStatus.NOT_FOUND


def test_error_all() -> None:
    with ginjarator.testing.api_for_scan():
        actual = metadata.Error.all()

    assert http.HTTPStatus.NOT_FOUND in tuple(
        error_metadata.status for error_metadata in actual
    )


def test_standalone_load_error(tmp_path: pathlib.Path) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["standalone"]
            templates = ["standalone/foo/index.html.jinja"]
            """
        )
    )
    (tmp_path / "standalone/foo").mkdir(parents=True)
    (tmp_path / "standalone/foo/index.html.jinja").write_text("")
    (tmp_path / "standalone/foo/metadata.toml").write_text(
        textwrap.dedent(
            """\
            title = "Foo"
            invalid_key_kumquat = "bar"
            """
        )
    )

    with ginjarator.testing.api_for_scan(
        current_template="standalone/foo/index.html.jinja",
        root_path=tmp_path,
    ):
        with pytest.raises(ValueError, match=r"invalid_key_kumquat"):
            metadata.Standalone.load(ginjarator.api().current_template)


def test_standalone_load(tmp_path: pathlib.Path) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["standalone"]
            templates = ["standalone/foo/index.html.jinja"]
            """
        )
    )
    (tmp_path / "standalone/foo").mkdir(parents=True)
    (tmp_path / "standalone/foo/index.html.jinja").write_text("")
    (tmp_path / "standalone/foo/metadata.toml").write_text(
        textwrap.dedent(
            """\
            title = "Foo"
            """
        )
    )

    with ginjarator.testing.api_for_scan(
        current_template="standalone/foo/index.html.jinja",
        root_path=tmp_path,
    ):
        standalone_metadata = metadata.Standalone.load(
            ginjarator.api().current_template
        )

    assert standalone_metadata.url_path == "/foo/"
    assert standalone_metadata.title == "Foo"


def test_standalone_all() -> None:
    with ginjarator.testing.api_for_scan():
        expected = tuple(
            metadata.Standalone.load(template)
            for template in ginjarator.api().fs.read_config().templates
            if template.is_relative_to("standalone")
        )

        actual = metadata.Standalone.all()

    assert {standalone.url_path for standalone in actual} == {
        standalone.url_path for standalone in expected
    }


@pytest.mark.parametrize(
    "contents,comments_metadata,error_regex",
    (
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                invalid_key_kumquat = "bar"
                """
            ),
            {},
            r"invalid_key_kumquat",
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 1995-06-27 14:15:01-04:00
                title = "Foo"
                """
            ),
            {},
            r"published date and directory name don't match",
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01
                title = "Foo"
                """
            ),
            {},
            r"no timezone",
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                tags = ["unknown-tag"]
                """
            ),
            {},
            r"Unknown tags",
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                tags = ["dance", "dance"]
                """
            ),
            {},
            r"not sorted and unique",
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                tags = ["music", "dance"]
                """
            ),
            {},
            r"not sorted and unique",
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                comments = [
                    "096aa7f3-827a-4824-91f0-97da7cbd160b",
                    "131294af-bba3-4296-a7e8-1f2eb5ca741c",
                ]
                """
            ),
            {
                "096aa7f3-827a-4824-91f0-97da7cbd160b": textwrap.dedent(
                    """\
                    published = 2025-07-03 16:15:35-04:00
                    author.name = "Someone Else"
                    """
                ),
                "131294af-bba3-4296-a7e8-1f2eb5ca741c": textwrap.dedent(
                    """\
                    published = 2025-07-02 16:15:35-04:00
                    author.name = "Someone Else"
                    """
                ),
            },
            r"not sorted",
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                comments = [
                    "096aa7f3-827a-4824-91f0-97da7cbd160b",
                ]
                """
            ),
            {
                "096aa7f3-827a-4824-91f0-97da7cbd160b": textwrap.dedent(
                    """\
                    published = 2025-07-03 16:15:35-04:00
                    author.name = "Someone Else"
                    in_reply_to = "26918b04-49ce-4ce8-aecc-8643b360ce56"
                    """
                ),
            },
            r"invalid in_reply_to",
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                comments = [
                    "096aa7f3-827a-4824-91f0-97da7cbd160b",
                    "131294af-bba3-4296-a7e8-1f2eb5ca741c",
                ]
                """
            ),
            {
                "096aa7f3-827a-4824-91f0-97da7cbd160b": textwrap.dedent(
                    """\
                    published = 2025-07-02 16:15:35-04:00
                    author.name = "Someone Else"
                    in_reply_to = "131294af-bba3-4296-a7e8-1f2eb5ca741c"
                    """
                ),
                "131294af-bba3-4296-a7e8-1f2eb5ca741c": textwrap.dedent(
                    """\
                    published = 2025-07-03 16:15:35-04:00
                    author.name = "Someone Else"
                    """
                ),
            },
            r"invalid in_reply_to",
        ),
    ),
)
def test_post_load_error(
    contents: str,
    comments_metadata: dict[str, str],
    error_regex: str,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "public").mkdir()
    (tmp_path / "public/ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["posts", "../private"]
            templates = ["posts/2025-06-27-foo/index.html.jinja"]
            """
        )
    )
    (tmp_path / "public/posts/2025-06-27-foo").mkdir(parents=True)
    (tmp_path / "public/posts/2025-06-27-foo/index.html.jinja").write_text("")
    (tmp_path / "public/posts/2025-06-27-foo/metadata.toml").write_text(
        contents
    )
    (tmp_path / "private/posts/2025-06-27-foo/comments").mkdir(parents=True)
    for comment_uuid, comment_metadata in comments_metadata.items():
        (
            tmp_path
            / f"private/posts/2025-06-27-foo/comments/{comment_uuid}.toml"
        ).write_text(comment_metadata)

    with ginjarator.testing.api_for_scan(
        current_template="posts/2025-06-27-foo/index.html.jinja",
        root_path=(tmp_path / "public"),
    ):
        with pytest.raises(ValueError, match=error_regex):
            metadata.Post.load(ginjarator.api().current_template)


@pytest.mark.parametrize(
    ",".join(
        (
            "contents",
            "comments_metadata",
            "expected",
            "expected_comment_by_uuid",
            "expected_comments_by_parent",
        )
    ),
    (
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                """
            ),
            {},
            metadata.Post(
                url_path="/2025/06/27/foo/",
                title="Foo",
                id="2025-06-27-foo",
                uuid=uuid.UUID("67ed54bc-e214-4177-9846-2236de449037"),
                published=datetime.datetime.fromisoformat(
                    "2025-06-27 18:15:01-00:00"
                ),
                author=metadata.SITE.author,
                tags=(),
                url_path_aliases=frozenset(),
                comments=(),
            ),
            {},
            {None: []},
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-26 22:15:01-04:00
                title = "Foo"
                author.name = "Someone Else"
                tags = ["dance", "music"]
                comments = [
                    "096aa7f3-827a-4824-91f0-97da7cbd160b",
                    "131294af-bba3-4296-a7e8-1f2eb5ca741c",
                ]
                """
            ),
            {
                "096aa7f3-827a-4824-91f0-97da7cbd160b": textwrap.dedent(
                    """\
                    published = 2025-07-02 16:15:35-04:00
                    author.name = "Someone Else"
                    """
                ),
                "131294af-bba3-4296-a7e8-1f2eb5ca741c": textwrap.dedent(
                    """\
                    published = 2025-07-03 16:15:35-04:00
                    author.name = "David Mandelberg"
                    in_reply_to = "096aa7f3-827a-4824-91f0-97da7cbd160b"
                    """
                ),
            },
            metadata.Post(
                url_path="/2025/06/27/foo/",
                title="Foo",
                id="2025-06-27-foo",
                uuid=uuid.UUID("67ed54bc-e214-4177-9846-2236de449037"),
                published=datetime.datetime.fromisoformat(
                    "2025-06-27 02:15:01-00:00"
                ),
                author=metadata.User(name="Someone Else"),
                tags=("dance", "music"),
                url_path_aliases=frozenset(("/2025/06/26/foo/",)),
                comments=(
                    metadata.Comment(
                        url_path=(
                            "/2025/06/27/foo/#2025-06-27-foo-comment-"
                            "096aa7f3-827a-4824-91f0-97da7cbd160b"
                        ),
                        id=(
                            "2025-06-27-foo-comment-"
                            "096aa7f3-827a-4824-91f0-97da7cbd160b"
                        ),
                        uuid=uuid.UUID("096aa7f3-827a-4824-91f0-97da7cbd160b"),
                        published=datetime.datetime.fromisoformat(
                            "2025-07-02 20:15:35Z"
                        ),
                        author=metadata.User(name="Someone Else"),
                        in_reply_to=None,
                        contents_path=ginjarator.paths.Filesystem(
                            "../private/posts/2025-06-27-foo/comments/"
                            "096aa7f3-827a-4824-91f0-97da7cbd160b.html"
                        ),
                    ),
                    metadata.Comment(
                        url_path=(
                            "/2025/06/27/foo/#2025-06-27-foo-comment-"
                            "131294af-bba3-4296-a7e8-1f2eb5ca741c"
                        ),
                        id=(
                            "2025-06-27-foo-comment-"
                            "131294af-bba3-4296-a7e8-1f2eb5ca741c"
                        ),
                        uuid=uuid.UUID("131294af-bba3-4296-a7e8-1f2eb5ca741c"),
                        published=datetime.datetime.fromisoformat(
                            "2025-07-03 20:15:35Z"
                        ),
                        author=metadata.User(name="David Mandelberg"),
                        in_reply_to=uuid.UUID(
                            "096aa7f3-827a-4824-91f0-97da7cbd160b"
                        ),
                        contents_path=ginjarator.paths.Filesystem(
                            "../private/posts/2025-06-27-foo/comments/"
                            "131294af-bba3-4296-a7e8-1f2eb5ca741c.html"
                        ),
                    ),
                ),
            ),
            {
                uuid.UUID("096aa7f3-827a-4824-91f0-97da7cbd160b"): (
                    metadata.Comment(
                        url_path=(
                            "/2025/06/27/foo/#2025-06-27-foo-comment-"
                            "096aa7f3-827a-4824-91f0-97da7cbd160b"
                        ),
                        id=(
                            "2025-06-27-foo-comment-"
                            "096aa7f3-827a-4824-91f0-97da7cbd160b"
                        ),
                        uuid=uuid.UUID("096aa7f3-827a-4824-91f0-97da7cbd160b"),
                        published=datetime.datetime.fromisoformat(
                            "2025-07-02 20:15:35Z"
                        ),
                        author=metadata.User(name="Someone Else"),
                        in_reply_to=None,
                        contents_path=ginjarator.paths.Filesystem(
                            "../private/posts/2025-06-27-foo/comments/"
                            "096aa7f3-827a-4824-91f0-97da7cbd160b.html"
                        ),
                    )
                ),
                uuid.UUID("131294af-bba3-4296-a7e8-1f2eb5ca741c"): (
                    metadata.Comment(
                        url_path=(
                            "/2025/06/27/foo/#2025-06-27-foo-comment-"
                            "131294af-bba3-4296-a7e8-1f2eb5ca741c"
                        ),
                        id=(
                            "2025-06-27-foo-comment-"
                            "131294af-bba3-4296-a7e8-1f2eb5ca741c"
                        ),
                        uuid=uuid.UUID("131294af-bba3-4296-a7e8-1f2eb5ca741c"),
                        published=datetime.datetime.fromisoformat(
                            "2025-07-03 20:15:35Z"
                        ),
                        author=metadata.User(name="David Mandelberg"),
                        in_reply_to=uuid.UUID(
                            "096aa7f3-827a-4824-91f0-97da7cbd160b"
                        ),
                        contents_path=ginjarator.paths.Filesystem(
                            "../private/posts/2025-06-27-foo/comments/"
                            "131294af-bba3-4296-a7e8-1f2eb5ca741c.html"
                        ),
                    )
                ),
            },
            {
                None: [
                    metadata.Comment(
                        url_path=(
                            "/2025/06/27/foo/#2025-06-27-foo-comment-"
                            "096aa7f3-827a-4824-91f0-97da7cbd160b"
                        ),
                        id=(
                            "2025-06-27-foo-comment-"
                            "096aa7f3-827a-4824-91f0-97da7cbd160b"
                        ),
                        uuid=uuid.UUID("096aa7f3-827a-4824-91f0-97da7cbd160b"),
                        published=datetime.datetime.fromisoformat(
                            "2025-07-02 20:15:35Z"
                        ),
                        author=metadata.User(name="Someone Else"),
                        in_reply_to=None,
                        contents_path=ginjarator.paths.Filesystem(
                            "../private/posts/2025-06-27-foo/comments/"
                            "096aa7f3-827a-4824-91f0-97da7cbd160b.html"
                        ),
                    )
                ],
                uuid.UUID("096aa7f3-827a-4824-91f0-97da7cbd160b"): [
                    metadata.Comment(
                        url_path=(
                            "/2025/06/27/foo/#2025-06-27-foo-comment-"
                            "131294af-bba3-4296-a7e8-1f2eb5ca741c"
                        ),
                        id=(
                            "2025-06-27-foo-comment-"
                            "131294af-bba3-4296-a7e8-1f2eb5ca741c"
                        ),
                        uuid=uuid.UUID("131294af-bba3-4296-a7e8-1f2eb5ca741c"),
                        published=datetime.datetime.fromisoformat(
                            "2025-07-03 20:15:35Z"
                        ),
                        author=metadata.User(name="David Mandelberg"),
                        in_reply_to=uuid.UUID(
                            "096aa7f3-827a-4824-91f0-97da7cbd160b"
                        ),
                        contents_path=ginjarator.paths.Filesystem(
                            "../private/posts/2025-06-27-foo/comments/"
                            "131294af-bba3-4296-a7e8-1f2eb5ca741c.html"
                        ),
                    ),
                ],
                uuid.UUID("131294af-bba3-4296-a7e8-1f2eb5ca741c"): [],
            },
        ),
    ),
)
def test_post_load(
    contents: str,
    comments_metadata: dict[str, str],
    expected: metadata.Post,
    expected_comment_by_uuid: dict[uuid.UUID, metadata.Comment],
    expected_comments_by_parent: dict[uuid.UUID | None, list[metadata.Comment]],
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "public").mkdir()
    (tmp_path / "public/ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["posts", "../private"]
            templates = ["posts/2025-06-27-foo/index.html.jinja"]
            """
        )
    )
    (tmp_path / "public/posts/2025-06-27-foo").mkdir(parents=True)
    (tmp_path / "public/posts/2025-06-27-foo/index.html.jinja").write_text("")
    (tmp_path / "public/posts/2025-06-27-foo/metadata.toml").write_text(
        contents
    )
    (tmp_path / "private/posts/2025-06-27-foo/comments").mkdir(parents=True)
    for comment_uuid, comment_metadata in comments_metadata.items():
        (
            tmp_path
            / f"private/posts/2025-06-27-foo/comments/{comment_uuid}.toml"
        ).write_text(comment_metadata)

    with ginjarator.testing.api_for_scan(
        current_template="posts/2025-06-27-foo/index.html.jinja",
        root_path=(tmp_path / "public"),
    ):
        post_metadata = metadata.Post.load(ginjarator.api().current_template)

    assert post_metadata == expected
    assert post_metadata.work_path == ginjarator.paths.Filesystem(
        "work/posts/2025-06-27-foo"
    )
    assert post_metadata.include_fragment_path == ginjarator.paths.Filesystem(
        "work/posts/2025-06-27-foo/include-fragment.html"
    )
    assert post_metadata.atom_fragment_path == ginjarator.paths.Filesystem(
        "work/posts/2025-06-27-foo/atom-fragment.xml"
    )
    assert post_metadata.comment_by_uuid == expected_comment_by_uuid
    assert post_metadata.comments_by_parent == expected_comments_by_parent


@pytest.mark.parametrize(
    "source_dir_name_1,metadata_1,source_dir_name_2,metadata_2,error_regex",
    (
        (
            "2025-06-26-foo",
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-26 00:00:00-04:00
                title = "Foo"
                """
            ),
            "2025-06-27-foo",
            textwrap.dedent(
                """\
                uuid = "f056342d-b090-4266-9e65-de87e37a094e"
                published = 2025-06-26 23:00:00-04:00
                title = "Foo"
                """
            ),
            r"Duplicate URL path",
        ),
        (
            "2025-06-27-foo",
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 23:59:59Z
                title = "Foo"
                """
            ),
            "2025-06-27-bar",
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 00:00:00Z
                title = "Bar"
                """
            ),
            r"Duplicate uuid",
        ),
        (
            "2025-06-27-foo",
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 12:00:00-04:00
                title = "Foo"
                """
            ),
            "2025-06-27-bar",
            textwrap.dedent(
                """\
                uuid = "f056342d-b090-4266-9e65-de87e37a094e"
                published = 2025-06-27 16:00:00Z
                title = "Bar"
                """
            ),
            r"Duplicate published",
        ),
    ),
)
def test_post_all_duplicate(
    source_dir_name_1: str,
    metadata_1: str,
    source_dir_name_2: str,
    metadata_2: str,
    error_regex: str,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            f"""\
            source_paths = ["posts"]
            templates = [
                "posts/{source_dir_name_1}/index.html.jinja",
                "posts/{source_dir_name_2}/index.html.jinja",
            ]
            """
        )
    )
    (tmp_path / f"posts/{source_dir_name_1}").mkdir(parents=True)
    (tmp_path / f"posts/{source_dir_name_1}/index.html.jinja").write_text("")
    (tmp_path / f"posts/{source_dir_name_1}/metadata.toml").write_text(
        metadata_1
    )
    (tmp_path / f"posts/{source_dir_name_2}").mkdir(parents=True)
    (tmp_path / f"posts/{source_dir_name_2}/index.html.jinja").write_text("")
    (tmp_path / f"posts/{source_dir_name_2}/metadata.toml").write_text(
        metadata_2
    )

    with ginjarator.testing.api_for_scan(root_path=tmp_path):
        with pytest.raises(ValueError, match=error_regex):
            metadata.Post.all()


def test_post_all() -> None:
    with ginjarator.testing.api_for_scan():
        actual = metadata.Post.all()

    assert actual[0].published > actual[1].published


def test_post_all_no_unlisted_comments() -> None:
    with ginjarator.testing.api_for_scan():
        posts = metadata.Post.all()

    for post in posts:
        comments_path = pathlib.Path(
            paths.PRIVATE / "posts" / post.id / "comments"
        )
        if comments_path.exists():
            comments_filenames = {
                child.name for child in comments_path.iterdir()
            }
        else:
            comments_filenames = set()
        assert comments_filenames == {
            *(f"{comment.uuid}.html" for comment in post.comments),
            *(f"{comment.uuid}.toml" for comment in post.comments),
        }


def test_post_list_page_all() -> None:
    with ginjarator.testing.api_for_scan():
        pages = metadata.PostListPage.all()
        assert pages
        assert all(page.posts for page in pages)


def test_post_list_main() -> None:
    with ginjarator.testing.api_for_scan():
        assert tuple(metadata.PostList.main().posts) == tuple(
            metadata.Post.all()
        )


def test_post_list_tag() -> None:
    with ginjarator.testing.api_for_scan():
        posts = metadata.PostList.tag("dance").posts

    assert posts
    assert all("dance" in post.tags for post in posts)


def test_post_list_all() -> None:
    with ginjarator.testing.api_for_scan():
        lists = metadata.PostList.all()
        assert lists
        assert all(post_list.posts for post_list in lists)
        assert all(post_list.feed_posts for post_list in lists)


def test_post_list_pages() -> None:
    with ginjarator.testing.api_for_scan():
        pages = metadata.PostList.main().page_by_number

    with pytest.raises(LookupError):
        pages[0]
    assert pages[1].url_path == "/"
    assert pages[1].title == "Blog"
    assert pages[1].page_number == 1
    assert pages[2].url_path == "/page/2/"
    assert pages[2].title == "Blog (page 2)"
    assert pages[2].page_number == 2
    assert all(page.posts for page in pages.values())


def test_post_list_link_by_year() -> None:
    with ginjarator.testing.api_for_scan():
        post_list = metadata.PostList.main()
        most_recent_2025 = max(
            (post for post in post_list.posts if post.published.year == 2025),
            key=lambda post: post.published,
        )

        assert post_list.link_by_year[2025].endswith(f"#{most_recent_2025.id}")
        assert list(post_list.link_by_year) == sorted(
            post_list.link_by_year,
            reverse=True,
        )


def test_post_list_feed_url_path() -> None:
    with ginjarator.testing.api_for_scan():
        post_list = metadata.PostList.main()

    assert post_list.feed_url_path == "/feed/"


def test_main_nav() -> None:
    with ginjarator.testing.api_for_scan():
        assert metadata.main_nav()
