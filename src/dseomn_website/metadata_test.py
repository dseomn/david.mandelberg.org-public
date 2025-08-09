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
import markupsafe
import pytest

from dseomn_website import metadata
from dseomn_website import paths


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    # Normally, loading the same template should return the same data, but
    # that's not the case in these tests which use different root directories
    # with the same relative template paths.
    metadata.Error.load.cache_clear()
    metadata.Standalone.load.cache_clear()
    metadata.Post.load.cache_clear()


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


def test_fragment_error() -> None:
    with pytest.raises(ValueError, match=r"no fragment ID"):
        metadata.Resource(url_path="/foo/").fragment("")


def test_fragment() -> None:
    fragment = metadata.Resource(url_path="/foo/").fragment("bar")

    assert fragment.url_path == "/foo/#bar"
    assert fragment.id == "bar"
    assert fragment.url_fragment == "#bar"


def test_image_details_page_item() -> None:
    assert metadata.Image(
        source=ginjarator.paths.Filesystem("foo.png"),
        gallery="main",
        opengraph=False,
        description_template=ginjarator.paths.Filesystem("foo.html.jinja"),
        alt="Foo?",
        float_=True,
        full_screen=False,
        main=True,
    ).details_page_item() == metadata.Image(
        source=ginjarator.paths.Filesystem("foo.png"),
        gallery=None,
        opengraph=True,
        description_template=ginjarator.paths.Filesystem("foo.html.jinja"),
        alt="Foo?",
        float_=False,
        full_screen=True,
        main=False,
    )


def test_image_aspect_ratio() -> None:
    with ginjarator.testing.api_for_scan():
        image = metadata.Image(
            source=ginjarator.paths.Filesystem(
                "src/dseomn_website/test-16x12.png"
            ),
            gallery=None,
            opengraph=False,
            description_template=None,
            alt="",
            float_=False,
            full_screen=False,
            main=False,
        )
        assert image.aspect_ratio == 16 / 12


@pytest.mark.parametrize(
    "source,key,expected_values",
    (
        (
            "src/dseomn_website/test-16x12.png",
            "Taken",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Taken",
            ("<time>2013-02-08 16:18:16</time>",),
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Camera",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Camera",
            ("Panasonic DMC-GH2",),
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Resolution",
            ("16 × 12",),
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Aperture",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Aperture",
            ("ƒ∕8",),
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030256-raw.JPG",
            "Aperture",
            ("ƒ∕6.3",),
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Exposure time",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Exposure time",
            ("1⁄80 s",),
        ),
        (
            (
                "../private/posts/2013-07-06-nordic-fiddles-and-feet/"
                "P1070388-raw.jpg"
            ),
            "Exposure time",
            ("13.0 s",),
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Focal length",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Focal length",
            ("42 mm", "84 mm (35 mm equivalent)"),
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "ISO",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "ISO",
            ("500",),
        ),
        (
            "src/dseomn_website/test-16x12.png",
            "Software",
            None,
        ),
        (
            "../private/posts/2013-02-12-snow-photos/P1030242-raw.JPG",
            "Software",
            ("Ver.1.1", "UFRaw 0.18"),
        ),
        (
            (
                "../private/posts/2013-02-12-snow-photos/"
                "P1030324-raw-P1030337-raw.jpg"
            ),
            "Software",
            ("Hugin 2011.4.0.cf9be9344356",),
        ),
    ),
)
def test_image_metadata(
    source: str,
    key: str,
    expected_values: tuple[str, ...] | None,
) -> None:
    with ginjarator.testing.api_for_scan():
        image = metadata.Image(
            source=ginjarator.paths.Filesystem(source),
            gallery=None,
            opengraph=False,
            description_template=None,
            alt="",
            float_=False,
            full_screen=False,
            main=False,
        )
        metadata_html = {
            str(markupsafe.escape(k)): tuple(
                map(str, map(markupsafe.escape, v))
            )
            for k, v in image.metadata.items()
        }
    assert metadata_html.get(key) == expected_values


@pytest.mark.parametrize(
    "raw,error_regex",
    (
        (dict(invalid_key_kumquat=42), r"invalid_key_kumquat"),
        (
            dict(items=[dict(type="invalid", source="foo")]),
            r"Unknown media item type",
        ),
        (
            dict(
                items=[
                    dict(
                        type="image",
                        source="foo",
                        alt="",
                        invalid_key_kumquat=42,
                    ),
                ],
            ),
            r"invalid_key_kumquat",
        ),
        (
            dict(
                items=[
                    dict(type="image", source="foo", alt="alt-1"),
                    dict(type="image", source="foo", alt="alt-2"),
                ],
            ),
            r"Duplicate item source",
        ),
    ),
)
def test_media_parse_error(raw: Any, error_regex: str) -> None:
    with pytest.raises(ValueError, match=error_regex):
        metadata.Media.parse(raw)


def test_media_parse() -> None:
    actual = metadata.Media.parse(
        dict(
            items=[
                dict(
                    type="image",
                    source="foo.png",
                    gallery="main",
                    opengraph=True,
                    alt="Foo?",
                    float=True,
                    full_screen=True,
                    description_template="foo.html.jinja",
                ),
                dict(
                    type="image",
                    source="bar.jpg",
                    alt="Bar!",
                    main=True,
                ),
            ],
        )
    )

    foo = metadata.Image(
        source=ginjarator.paths.Filesystem("foo.png"),
        gallery="main",
        opengraph=True,
        description_template=ginjarator.paths.Filesystem("foo.html.jinja"),
        alt="Foo?",
        float_=True,
        full_screen=True,
        main=False,
    )
    bar = metadata.Image(
        source=ginjarator.paths.Filesystem("bar.jpg"),
        gallery=None,
        opengraph=False,
        description_template=None,
        alt="Bar!",
        float_=False,
        full_screen=False,
        main=True,
    )
    assert actual == metadata.Media(
        item_by_source={
            ginjarator.paths.Filesystem("foo.png"): foo,
            ginjarator.paths.Filesystem("bar.jpg"): bar,
        },
    )
    assert actual.item_by_source_str == {"foo.png": foo, "bar.jpg": bar}


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
    "contents,expected,expected_pseudo_title",
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
            "Comment by Someone Else on 2025-07-03 19:47:37+00:00",
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
            "Comment by Someone Else on 2025-07-03 19:56:21+00:00",
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
            "Comment by Someone Else on 2025-07-03 19:47:37+00:00",
        ),
    ),
)
def test_comment_load(
    contents: str,
    expected: metadata.Comment,
    expected_pseudo_title: str,
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
        assert actual.atom_fragment_path == ginjarator.paths.Filesystem(
            "work/comments/6c60576a-33eb-4b8c-89d1-f6ab5c5b6ebc/fragment.atom"
        )
        assert actual.pseudo_title == expected_pseudo_title


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


def test_feed() -> None:
    updated = datetime.datetime(2025, 1, 1)
    feed = metadata.Feed[int](
        url_path="/feed/",
        title="Foo",
        updated_callback=lambda: updated,
        entries_callback=lambda: (0, 7),
    )

    assert feed.updated == updated
    assert feed.entries == (0, 7)


def test_feed_all() -> None:
    with ginjarator.testing.api_for_scan():
        assert metadata.Feed.all()


@pytest.mark.parametrize(
    "template,cls",
    (
        ("errors/404/index.html.jinja", metadata.Error),
        ("standalone/about/index.html.jinja", metadata.Standalone),
        ("posts/2009-06-16-hello-world/index.html.jinja", metadata.Post),
    ),
)
def test_page_current(template: str, cls: type[metadata.Page]) -> None:
    with ginjarator.testing.api_for_scan(current_template=template):
        assert isinstance(metadata.Page.current(), cls)


def test_page_current_not_implemented() -> None:
    with ginjarator.testing.api_for_scan(
        current_template="css/common.less.jinja",
    ):
        with pytest.raises(NotImplementedError):
            metadata.Page.current()


def test_page_all() -> None:
    with ginjarator.testing.api_for_scan():
        assert metadata.Page.all()


def test_page_full_title() -> None:
    assert (
        metadata.Page(url_path="/foo/", title="Foo").full_title
        == "Foo — David Mandelberg"
    )


def test_page_media_item_details_by_source() -> None:
    page = metadata.Page(
        url_path="/foo/",
        title="Foo",
        media=metadata.Media.parse(
            dict(
                items=[
                    dict(
                        type="image",
                        source="foo.png",
                        alt="Foo?",
                        gallery="main",
                    ),
                    dict(
                        type="image",
                        source="bar.jpg",
                        alt="Bar!",
                        main=True,
                    ),
                ],
            )
        ),
    )

    assert page.media_item_details_by_source.keys() == {
        ginjarator.paths.Filesystem("foo.png"),
    }


def test_media_item_details_create() -> None:
    parent = metadata.Page(
        url_path="/foo/",
        title="Foo",
        media=metadata.Media.parse(
            dict(
                items=[
                    dict(
                        type="image",
                        source="bar.jpg",
                        alt="Bar!",
                        gallery="main",
                    ),
                ],
            )
        ),
    )

    media_item_details = metadata.MediaItemDetails.create(
        parent,
        ginjarator.paths.Filesystem("bar.jpg"),
    )

    assert media_item_details == metadata.MediaItemDetails(
        url_path="/foo/bar/",
        title="bar.jpg",
        media=metadata.Media.parse(
            dict(
                items=[
                    dict(
                        type="image",
                        source="bar.jpg",
                        alt="Bar!",
                        opengraph=True,
                        full_screen=True,
                    ),
                ],
            )
        ),
        item=parent.media.item_by_source_str["bar.jpg"],
    )
    assert media_item_details.item_fragment.url_path == "/foo/bar/#bar.jpg"


def test_media_item_details_all() -> None:
    with ginjarator.testing.api_for_scan():
        assert metadata.MediaItemDetails.all()


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
            metadata.Standalone.load(ginjarator.api().paths.current_template)


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
            ginjarator.api().paths.current_template
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
            metadata.Post.load(ginjarator.api().paths.current_template)


@pytest.mark.parametrize(
    ",".join(
        (
            "contents",
            "comments_metadata",
            "expected",
            "expected_comment_by_uuid",
            "expected_comments_by_parent",
            "expected_comments_feed_updated",
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
            datetime.datetime.fromisoformat("2025-06-27 18:15:01-00:00"),
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
            datetime.datetime.fromisoformat("2025-07-03 20:15:35Z"),
        ),
    ),
)
def test_post_load(
    contents: str,
    comments_metadata: dict[str, str],
    expected: metadata.Post,
    expected_comment_by_uuid: dict[uuid.UUID, metadata.Comment],
    expected_comments_by_parent: dict[uuid.UUID | None, list[metadata.Comment]],
    expected_comments_feed_updated: datetime.datetime,
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
        post_metadata = metadata.Post.load(
            ginjarator.api().paths.current_template
        )

    assert post_metadata == expected
    assert post_metadata.fragment("bar").id == "2025-06-27-foo-bar"
    assert post_metadata.work_path == ginjarator.paths.Filesystem(
        "work/posts/2025-06-27-foo"
    )
    assert post_metadata.include_fragment_path == ginjarator.paths.Filesystem(
        "work/posts/2025-06-27-foo/include-fragment.html"
    )
    assert post_metadata.atom_fragment_path == ginjarator.paths.Filesystem(
        "work/posts/2025-06-27-foo/fragment.atom"
    )
    assert post_metadata.comments_section == metadata.Fragment(
        url_path="/2025/06/27/foo/#2025-06-27-foo-comments",
    )
    assert post_metadata.comment_by_uuid == expected_comment_by_uuid
    assert post_metadata.comments_by_parent == expected_comments_by_parent
    assert (
        post_metadata.comments_feed.url_path == "/2025/06/27/foo/comments/feed/"
    )
    assert (
        post_metadata.comments_feed.title == "Comments — Foo — David Mandelberg"
    )
    assert post_metadata.comments_feed.updated == expected_comments_feed_updated
    assert tuple(post_metadata.comments_feed.entries) == tuple(
        reversed(post_metadata.comments)
    )


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
        assert all(post_list.feed.entries for post_list in lists)


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


def test_post_list_feed() -> None:
    with ginjarator.testing.api_for_scan():
        post_list = metadata.PostList.main()

        assert post_list.feed.url_path == "/feed/"
        assert post_list.feed.title == "Blog — David Mandelberg"
        assert post_list.feed.updated == max(
            post.published for post in post_list.posts
        )


@pytest.mark.parametrize(
    "comments_1,comments_2,expected_updated,expected_comment_uuids",
    (
        ({}, {}, datetime.datetime.fromisoformat("2024-01-01 00:00:00Z"), ()),
        (
            {
                "1892c575-2bf8-48df-b2bc-4a944b6a3631": textwrap.dedent(
                    """\
                    published = 2024-02-01 00:00:00Z
                    author.name = "Someone"
                    """
                ),
                "6c7a6ce4-0231-458c-8410-8c651f52a3e1": textwrap.dedent(
                    """\
                    published = 2025-03-01 00:00:00Z
                    author.name = "Someone"
                    """
                ),
            },
            {
                "c4e08f7b-f82c-42a2-95cb-39d7fc29b46a": textwrap.dedent(
                    """\
                    published = 2025-02-01 00:00:00Z
                    author.name = "Someone"
                    """
                ),
            },
            datetime.datetime.fromisoformat("2025-03-01 00:00:00Z"),
            (
                "6c7a6ce4-0231-458c-8410-8c651f52a3e1",  # 2025-03-01
                "c4e08f7b-f82c-42a2-95cb-39d7fc29b46a",  # 2025-02-01
                "1892c575-2bf8-48df-b2bc-4a944b6a3631",  # 2024-02-01
            ),
        ),
    ),
)
def test_post_list_comments_feed(
    comments_1: dict[str, str],
    comments_2: dict[str, str],
    expected_updated: datetime.datetime,
    expected_comment_uuids: tuple[str, ...],
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "public").mkdir()
    (tmp_path / "public/ginjarator.toml").write_text(
        textwrap.dedent(
            f"""\
            source_paths = ["posts", "../private"]
            templates = [
                "posts/2024-01-01-foo/index.html.jinja",
                "posts/2025-01-01-bar/index.html.jinja",
            ]
            """
        )
    )
    (tmp_path / "public/posts/2024-01-01-foo").mkdir(parents=True)
    (tmp_path / "public/posts/2024-01-01-foo/metadata.toml").write_text(
        textwrap.dedent(
            f"""\
            uuid = "4cb2c225-2b0d-4056-8b39-698509e59659"
            published = 2024-01-01 00:00:00Z
            title = "Foo"
            comments = {list(comments_1)}
            """
        )
    )
    (tmp_path / "private/posts/2024-01-01-foo/comments").mkdir(parents=True)
    for comment_uuid, comment_metadata in comments_1.items():
        (
            tmp_path
            / f"private/posts/2024-01-01-foo/comments/{comment_uuid}.toml"
        ).write_text(comment_metadata)
    (tmp_path / "public/posts/2025-01-01-bar").mkdir(parents=True)
    (tmp_path / "public/posts/2025-01-01-bar/metadata.toml").write_text(
        textwrap.dedent(
            f"""\
            uuid = "46aca45c-1619-41fa-97fb-9858de6b94d4"
            published = 2025-01-01 00:00:00Z
            title = "Bar"
            comments = {list(comments_2)}
            """
        )
    )
    (tmp_path / "private/posts/2025-01-01-bar/comments").mkdir(parents=True)
    for comment_uuid, comment_metadata in comments_2.items():
        (
            tmp_path
            / f"private/posts/2025-01-01-bar/comments/{comment_uuid}.toml"
        ).write_text(comment_metadata)

    with ginjarator.testing.api_for_scan(root_path=tmp_path / "public"):
        post_list = metadata.PostList.main()

        assert post_list.comments_feed.url_path == "/comments/feed/"
        assert (
            post_list.comments_feed.title
            == "Comments — Blog — David Mandelberg"
        )
        assert post_list.comments_feed.updated == expected_updated
        assert (
            tuple(
                str(comment.uuid) for comment in post_list.comments_feed.entries
            )
            == expected_comment_uuids
        )


def test_main_nav() -> None:
    with ginjarator.testing.api_for_scan():
        assert metadata.main_nav()
