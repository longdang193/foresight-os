from pathlib import Path

from scripts.check_markdown_links import check_files


def test_valid_relative_and_reference_links(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("[guide][guide]\n\n[guide]: docs/guide.md\n", encoding="utf-8")

    assert check_files([readme], tmp_path) == []


def test_missing_relative_link_is_reported(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text("[missing](docs/missing.md)\n", encoding="utf-8")

    errors = check_files([readme], tmp_path)

    assert len(errors) == 1
    assert "README.md:1" in errors[0]
    assert "docs/missing.md" in errors[0]


def test_fragment_only_links_are_ignored(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text("[section](#section)\n", encoding="utf-8")

    assert check_files([readme], tmp_path) == []


def test_external_links_are_ignored(tmp_path: Path):
    readme = tmp_path / "README.md"
    readme.write_text(
        "[http](https://example.com) [mail](mailto:docs@example.com)\n",
        encoding="utf-8",
    )

    assert check_files([readme], tmp_path) == []


def test_explicit_untracked_canonical_page_is_checked(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    page = tmp_path / "docs" / "getting-started.md"
    page.write_text("# Getting Started\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("[start](docs/getting-started.md)\n", encoding="utf-8")

    assert check_files([readme, page], tmp_path) == []
