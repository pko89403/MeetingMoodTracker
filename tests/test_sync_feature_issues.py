"""feature_list <-> GitHub Issue 동기화 스크립트 테스트."""

from __future__ import annotations

import scripts.sync_feature_issues as sync


def test_extract_feature_id_from_issue_marker() -> None:
    body = """<!-- feature_id:feat_logic_topic_extraction -->\n본문"""
    result = sync.extract_feature_id_from_issue("임의 제목", body)
    assert result == "feat_logic_topic_extraction"


def test_extract_feature_id_from_issue_title() -> None:
    result = sync.extract_feature_id_from_issue(
        "[feat_logic_mood_analysis] Mood and Severity Analysis", None
    )
    assert result == "feat_logic_mood_analysis"


def test_list_all_issues_filters_pull_request(monkeypatch) -> None:
    page1 = [
        {
            "number": 10,
            "state": "open",
            "title": "[feat_logic_topic_extraction] Topic Extraction",
            "html_url": "https://github.com/example/repo/issues/10",
            "body": "",
        },
        {
            "number": 11,
            "state": "closed",
            "title": "PR title",
            "html_url": "https://github.com/example/repo/pull/11",
            "body": "",
            "pull_request": {"url": "https://api.github.com/repos/example/repo/pulls/11"},
        },
    ]

    calls = {"count": 0}

    def fake_request(**_: object):
        calls["count"] += 1
        return page1 if calls["count"] == 1 else []

    monkeypatch.setattr(sync, "github_request", fake_request)
    issues = sync.list_all_issues(repo="example/repo", token=None)

    assert len(issues) == 1
    assert issues[0].number == 10
    assert issues[0].feature_id == "feat_logic_topic_extraction"


def test_write_issue_metadata() -> None:
    feature = {"id": "feat_logic_topic_extraction"}
    issue = sync.IssueRecord(
        number=12,
        state="open",
        title="[feat_logic_topic_extraction] Topic Extraction",
        html_url="https://github.com/example/repo/issues/12",
        feature_id="feat_logic_topic_extraction",
    )

    sync.write_issue_metadata(feature, issue)

    assert feature["github_issue"]["number"] == 12
    assert feature["github_issue"]["state"] == "open"
    assert feature["github_issue"]["url"] == "https://github.com/example/repo/issues/12"
    assert "synced_at" in feature["github_issue"]


def test_write_issue_metadata_returns_false_when_unchanged() -> None:
    feature = {
        "id": "feat_logic_topic_extraction",
        "github_issue": {
            "number": 12,
            "url": "https://github.com/example/repo/issues/12",
            "state": "open",
            "synced_at": "2026-03-30T00:00:00+00:00",
        },
    }
    issue = sync.IssueRecord(
        number=12,
        state="open",
        title="[feat_logic_topic_extraction] Topic Extraction",
        html_url="https://github.com/example/repo/issues/12",
        feature_id="feat_logic_topic_extraction",
    )

    changed = sync.write_issue_metadata(feature, issue)

    assert changed is False
    assert feature["github_issue"]["synced_at"] == "2026-03-30T00:00:00+00:00"
