# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import datetime
import http
import pathlib
import textwrap
import uuid

import ginjarator.testing
import pytest

from dseomn_website import metadata


def test_site() -> None:
    assert list(metadata.SITE.tags) == sorted(set(metadata.SITE.tags))


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


def test_page_all() -> None:
    with ginjarator.testing.api_for_scan():
        assert metadata.Page.all()


def test_page_url() -> None:
    assert (
        metadata.Page(url_path="/foo/", title="Foo").url
        == "https://david.mandelberg.org/foo/"
    )


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
    "contents,error_regex",
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
            r"published date and directory name don't match",
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
            r"not sorted and unique",
        ),
    ),
)
def test_post_load_error(
    contents: str,
    error_regex: str,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["posts"]
            templates = ["posts/2025-06-27-foo/index.html.jinja"]
            """
        )
    )
    (tmp_path / "posts/2025-06-27-foo").mkdir(parents=True)
    (tmp_path / "posts/2025-06-27-foo/index.html.jinja").write_text("")
    (tmp_path / "posts/2025-06-27-foo/metadata.toml").write_text(contents)

    with ginjarator.testing.api_for_scan(
        current_template="posts/2025-06-27-foo/index.html.jinja",
        root_path=tmp_path,
    ):
        with pytest.raises(ValueError, match=error_regex):
            metadata.Post.load(ginjarator.api().current_template)


@pytest.mark.parametrize(
    "contents,expected",
    (
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                """
            ),
            metadata.Post(
                url_path="/2025/06/27/foo/",
                title="Foo",
                id="2025-06-27-foo",
                uuid=uuid.UUID("67ed54bc-e214-4177-9846-2236de449037"),
                published=datetime.datetime.fromisoformat(
                    "2025-06-27 14:15:01-04:00"
                ),
                author=metadata.SITE.author,
                tags=(),
            ),
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 14:15:01-04:00
                title = "Foo"
                author = "Someone Else"
                tags = ["dance", "music"]
                """
            ),
            metadata.Post(
                url_path="/2025/06/27/foo/",
                title="Foo",
                id="2025-06-27-foo",
                uuid=uuid.UUID("67ed54bc-e214-4177-9846-2236de449037"),
                published=datetime.datetime.fromisoformat(
                    "2025-06-27 14:15:01-04:00"
                ),
                author="Someone Else",
                tags=("dance", "music"),
            ),
        ),
    ),
)
def test_post_load(
    contents: str,
    expected: metadata.Post,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["posts"]
            templates = ["posts/2025-06-27-foo/index.html.jinja"]
            """
        )
    )
    (tmp_path / "posts/2025-06-27-foo").mkdir(parents=True)
    (tmp_path / "posts/2025-06-27-foo/index.html.jinja").write_text("")
    (tmp_path / "posts/2025-06-27-foo/metadata.toml").write_text(contents)

    with ginjarator.testing.api_for_scan(
        current_template="posts/2025-06-27-foo/index.html.jinja",
        root_path=tmp_path,
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


@pytest.mark.parametrize(
    "metadata_1,metadata_2,error_regex",
    (
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 23:59:59-04:00
                title = "Foo"
                """
            ),
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 00:00:00-04:00
                title = "Bar"
                """
            ),
            r"Duplicate uuid",
        ),
        (
            textwrap.dedent(
                """\
                uuid = "67ed54bc-e214-4177-9846-2236de449037"
                published = 2025-06-27 00:00:00-04:00
                title = "Foo"
                """
            ),
            textwrap.dedent(
                """\
                uuid = "f056342d-b090-4266-9e65-de87e37a094e"
                published = 2025-06-27 00:00:00-04:00
                title = "Bar"
                """
            ),
            r"Duplicate published",
        ),
    ),
)
def test_post_all_duplicate(
    metadata_1: str,
    metadata_2: str,
    error_regex: str,
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "ginjarator.toml").write_text(
        textwrap.dedent(
            """\
            source_paths = ["posts"]
            templates = [
                "posts/2025-06-27-foo/index.html.jinja",
                "posts/2025-06-27-bar/index.html.jinja",
            ]
            """
        )
    )
    (tmp_path / "posts/2025-06-27-foo").mkdir(parents=True)
    (tmp_path / "posts/2025-06-27-foo/index.html.jinja").write_text("")
    (tmp_path / "posts/2025-06-27-foo/metadata.toml").write_text(metadata_1)
    (tmp_path / "posts/2025-06-27-bar").mkdir(parents=True)
    (tmp_path / "posts/2025-06-27-bar/index.html.jinja").write_text("")
    (tmp_path / "posts/2025-06-27-bar/metadata.toml").write_text(metadata_2)

    with ginjarator.testing.api_for_scan(root_path=tmp_path):
        with pytest.raises(ValueError, match=error_regex):
            metadata.Post.all()


def test_post_all() -> None:
    with ginjarator.testing.api_for_scan():
        actual = metadata.Post.all()

    assert actual[0].published > actual[1].published


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
