"""Suche und Ranking (description > details > files > category)."""

from __future__ import annotations

from changelog_mcp.store.query import search_entries

from .conftest import make_entry, make_release


def _corpus() -> list:
    return [
        make_entry("e-1", "0.1.0", category="Added", description="CSV Export",
                   files=["src/export.py"]),
        make_entry("e-2", "0.1.1", category="Fixed", description="Bugfix",
                   details=["betrifft den export von daten"]),
        make_entry("e-3", "0.1.2", category="export", description="Nichts",
                   files=["src/other.py"]),
    ]


def test_ranking_description_beats_details_and_category() -> None:
    results = search_entries(_corpus(), query="export")
    # description-Treffer (e-1) muss vor details-Treffer (e-2) und
    # category-Treffer (e-3) liegen.
    assert [e.id for e in results] == ["e-1", "e-2", "e-3"]


def test_without_query_sorted_by_version_desc() -> None:
    results = search_entries(_corpus())
    assert [e.version for e in results] == ["0.1.2", "0.1.1", "0.1.0"]


def test_filters_are_and_combined() -> None:
    results = search_entries(_corpus(), category="Added", file="export.py")
    assert [e.id for e in results] == ["e-1"]


def test_version_prefix_filter() -> None:
    corpus = [make_entry("e-1", "1.2.0"), make_entry("e-2", "2.0.0")]
    results = search_entries(corpus, version="1.")
    assert [e.id for e in results] == ["e-1"]


def test_released_filter() -> None:
    records = _corpus() + [make_release("0.1.2", ["e-1"])]
    released = search_entries(records, released=True)
    unreleased = search_entries(records, released=False)
    assert [e.id for e in released] == ["e-1"]
    assert {e.id for e in unreleased} == {"e-2", "e-3"}


def test_date_range_inclusive() -> None:
    corpus = [
        make_entry("e-1", "0.1.0", date="2026-01-01"),
        make_entry("e-2", "0.1.1", date="2026-06-15"),
        make_entry("e-3", "0.1.2", date="2026-12-31"),
    ]
    results = search_entries(corpus, date_from="2026-06-01", date_to="2026-06-30")
    assert [e.id for e in results] == ["e-2"]


def test_limit_applies() -> None:
    corpus = [make_entry(f"e-{i}", f"0.1.{i}") for i in range(5)]
    assert len(search_entries(corpus, limit=2)) == 2
