# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import datetime
import http
import pathlib
import textwrap

import ginjarator.testing
import pytest

from dseomn_website import metadata


def test_site() -> None:
    assert list(metadata.SITE.tags) == sorted(set(metadata.SITE.tags))


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
        expected = {
            metadata.Standalone.load(template)
            for template in ginjarator.api().fs.read_config().templates
            if template.is_relative_to("standalone")
        }

        actual = metadata.Standalone.all()

    assert metadata.Standalone(url_path="/about/", title="About") in actual
    assert set(actual) == expected


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
                uuid="67ed54bc-e214-4177-9846-2236de449037",
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
                uuid="67ed54bc-e214-4177-9846-2236de449037",
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


def test_post_all() -> None:
    with ginjarator.testing.api_for_scan():
        actual = metadata.Post.all()

    assert actual[0].published > actual[1].published


@pytest.mark.parametrize(
    "page_number,expected",
    (
        (1, metadata.Page(url_path="/", title="Blog")),
        (2, metadata.Page(url_path="/page/2/", title="Blog (page 2)")),
    ),
)
def test_post_list_page(page_number: int, expected: metadata.Page) -> None:
    assert (
        metadata.PostList(url_path="/", title="Blog").page(page_number)
        == expected
    )


def test_post_list_properties() -> None:
    post_list = metadata.PostList(url_path="/", title="Blog")

    assert post_list.feed_url_path == "/feed/"


def test_main_nav() -> None:
    with ginjarator.testing.api_for_scan():
        assert metadata.main_nav()
