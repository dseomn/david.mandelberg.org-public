# SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
#
# SPDX-License-Identifier: Apache-2.0

import datetime
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
        assert metadata.Post.load(ginjarator.api().current_template) == expected
