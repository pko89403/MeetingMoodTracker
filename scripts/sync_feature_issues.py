#!/usr/bin/env python3
"""feature_list.json과 GitHub Issue를 동기화하는 스크립트."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, parse, request

GITHUB_API_BASE = "https://api.github.com"
FEATURE_MARKER_PATTERN = re.compile(r"<!--\s*feature_id:([a-zA-Z0-9_-]+)\s*-->")


@dataclass(slots=True)
class IssueRecord:
    """동기화에 필요한 GitHub Issue 최소 정보를 담는다."""

    number: int
    state: str
    title: str
    html_url: str
    feature_id: str | None


@dataclass(slots=True)
class SyncCounters:
    """동기화 실행 결과 카운터를 집계한다."""

    linked: int = 0
    created: int = 0
    state_changed: int = 0
    missing: int = 0
    metadata_changed: int = 0


def parse_args() -> argparse.Namespace:
    """CLI 인자를 파싱한다."""
    parser = argparse.ArgumentParser(
        description="feature_list.json <-> GitHub Issue 동기화"
    )
    parser.add_argument(
        "--feature-file",
        default="feature_list.json",
        help="동기화 대상 feature list 경로",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub 저장소 (owner/repo). 미지정 시 origin remote에서 자동 추론",
    )
    parser.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="GitHub API 토큰 환경변수 이름",
    )
    parser.add_argument(
        "--create-missing",
        action="store_true",
        help="매핑 이슈가 없으면 새 Issue를 생성",
    )
    parser.add_argument(
        "--sync-state",
        action="store_true",
        help="passes 값과 Issue open/closed 상태를 동기화",
    )
    parser.add_argument(
        "--write-feature-file",
        action="store_true",
        help="동기화된 Issue 메타데이터를 feature file에 기록",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="실제 GitHub 변경을 수행(미지정 시 dry-run)",
    )
    return parser.parse_args()


def infer_repo_from_origin() -> str:
    """현재 git origin URL에서 owner/repo를 추론한다."""
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("remote.origin.url을 찾을 수 없습니다.")

    url = result.stdout.strip()
    if not url:
        raise RuntimeError("origin remote URL이 비어 있습니다.")

    if url.startswith("git@github.com:"):
        path = url.split(":", maxsplit=1)[1]
    elif url.startswith("https://github.com/"):
        path = url.removeprefix("https://github.com/")
    else:
        raise RuntimeError(f"지원하지 않는 origin URL 형식: {url}")

    repo = path.removesuffix(".git").strip("/")
    if repo.count("/") != 1:
        raise RuntimeError(f"owner/repo 형식 파싱 실패: {repo}")
    return repo


def load_feature_file(path: Path) -> dict[str, Any]:
    """feature_list.json 파일을 로드한다."""
    return json.loads(path.read_text(encoding="utf-8"))


def extract_feature_id_from_issue(title: str, body: str | None) -> str | None:
    """Issue 제목/본문에서 feature_id를 추출한다."""
    if body:
        marker_match = FEATURE_MARKER_PATTERN.search(body)
        if marker_match:
            return marker_match.group(1)

    title_match = re.search(r"\[(feat_[a-zA-Z0-9_\-]+)]", title)
    if title_match:
        return title_match.group(1)

    return None


def _normalize_issue_rule_items(value: Any) -> list[str]:
    """issue_rule 배열 필드를 공백 제거된 문자열 목록으로 정규화한다."""
    if not isinstance(value, list):
        return []

    normalized: list[str] = []
    for item in value:
        if isinstance(item, str):
            stripped = item.strip()
            if stripped:
                normalized.append(stripped)
    return normalized


def _append_issue_rule_section(*, lines: list[str], title: str, items: list[str]) -> None:
    """issue_rule 섹션을 본문에 조건부로 추가한다."""
    if not items:
        return
    lines.extend(["", f"## {title}"])
    lines.extend([f"- {item}" for item in items])


def build_issue_body(feature: dict[str, Any]) -> str:
    """신규 Issue 생성 시 사용할 본문을 만든다."""
    feature_id = feature["id"]
    description = feature.get("description", "")
    lines = [
        f"<!-- feature_id:{feature_id} -->",
        "## 목적",
        description if description else "feature_list.json 기준 기능 추적",
    ]

    issue_rule = feature.get("issue_rule")
    if isinstance(issue_rule, dict):
        objective = issue_rule.get("objective")
        if isinstance(objective, str) and objective.strip():
            lines.extend(["", "## 작업 목표", objective.strip()])

        _append_issue_rule_section(
            lines=lines,
            title="범위 (In Scope)",
            items=_normalize_issue_rule_items(issue_rule.get("in_scope")),
        )
        _append_issue_rule_section(
            lines=lines,
            title="비범위 (Out of Scope)",
            items=_normalize_issue_rule_items(issue_rule.get("out_of_scope")),
        )
        _append_issue_rule_section(
            lines=lines,
            title="구현 체크리스트",
            items=_normalize_issue_rule_items(issue_rule.get("implementation_checklist")),
        )
        _append_issue_rule_section(
            lines=lines,
            title="검증 시나리오",
            items=_normalize_issue_rule_items(issue_rule.get("verification")),
        )

        done_criteria = _normalize_issue_rule_items(issue_rule.get("done_criteria"))
        if not done_criteria:
            done_criteria = _normalize_issue_rule_items(
                issue_rule.get("acceptance_criteria")
            )
        _append_issue_rule_section(
            lines=lines,
            title="완료 조건 (Definition of Done)",
            items=done_criteria,
        )

    lines.extend(
        [
            "",
            "## 동기화 기준",
            "- source: feature_list.json",
            f"- feature_id: `{feature_id}`",
            f"- passes: `{feature.get('passes')}`",
        ]
    )
    return "\n".join(lines)


def github_request(
    *,
    method: str,
    repo: str,
    path: str,
    token: str | None,
    payload: dict[str, Any] | None = None,
) -> Any:
    """GitHub REST API를 호출하고 JSON 응답을 반환한다."""
    url = f"{GITHUB_API_BASE}/repos/{repo}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "meeting-mood-tracker-feature-sync",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data_bytes: bytes | None = None
    if payload is not None:
        data_bytes = json.dumps(payload).encode("utf-8")

    req = request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with request.urlopen(req) as response:  # noqa: S310
            content_type = response.headers.get("Content-Type", "")
            body = response.read().decode("utf-8")
            if "application/json" in content_type and body:
                return json.loads(body)
            if body:
                return json.loads(body)
            return None
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"GitHub API 실패 {exc.code} {method} {url}: {detail}"
        ) from exc


def list_all_issues(repo: str, token: str | None) -> list[IssueRecord]:
    """저장소의 모든 Issue(=PR 제외)를 가져온다."""
    issues: list[IssueRecord] = []
    page = 1

    while True:
        query = parse.urlencode({"state": "all", "per_page": 100, "page": page})
        raw_items = github_request(
            method="GET",
            repo=repo,
            path=f"/issues?{query}",
            token=token,
        )
        if not raw_items:
            break

        for item in raw_items:
            if "pull_request" in item:
                continue
            feature_id = extract_feature_id_from_issue(
                title=item.get("title", ""),
                body=item.get("body"),
            )
            issues.append(
                IssueRecord(
                    number=item["number"],
                    state=item["state"],
                    title=item["title"],
                    html_url=item["html_url"],
                    feature_id=feature_id,
                )
            )

        if len(raw_items) < 100:
            break
        page += 1

    return issues


def create_issue(
    *,
    repo: str,
    token: str,
    title: str,
    body: str,
    labels: list[str] | None = None,
) -> IssueRecord:
    """신규 Issue를 생성한다."""
    payload: dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    created = github_request(
        method="POST",
        repo=repo,
        path="/issues",
        token=token,
        payload=payload,
    )
    return IssueRecord(
        number=created["number"],
        state=created["state"],
        title=created["title"],
        html_url=created["html_url"],
        feature_id=extract_feature_id_from_issue(created["title"], created.get("body")),
    )


def update_issue_state(*, repo: str, token: str, number: int, state: str) -> IssueRecord:
    """Issue 상태(open/closed)를 업데이트한다."""
    updated = github_request(
        method="PATCH",
        repo=repo,
        path=f"/issues/{number}",
        token=token,
        payload={"state": state},
    )
    return IssueRecord(
        number=updated["number"],
        state=updated["state"],
        title=updated["title"],
        html_url=updated["html_url"],
        feature_id=extract_feature_id_from_issue(updated["title"], updated.get("body")),
    )


def write_issue_metadata(feature: dict[str, Any], issue: IssueRecord) -> bool:
    """feature 엔트리에 GitHub Issue 메타데이터를 기록하고 변경 여부를 반환한다."""
    existing = feature.get("github_issue")
    if isinstance(existing, dict):
        same_number = existing.get("number") == issue.number
        same_url = existing.get("url") == issue.html_url
        same_state = existing.get("state") == issue.state
        if same_number and same_url and same_state:
            return False

    feature["github_issue"] = {
        "number": issue.number,
        "url": issue.html_url,
        "state": issue.state,
        "synced_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
    }
    return True


def print_summary(
    *,
    repo: str,
    dry_run: bool,
    counters: SyncCounters,
    lines: list[str],
) -> None:
    """동기화 결과를 사람이 읽기 쉬운 형태로 출력한다."""
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[feature-issue-sync] repo={repo} mode={mode}")
    for line in lines:
        print(line)
    print(
        "[feature-issue-sync] summary: "
        f"linked={counters.linked}, created={counters.created}, "
        f"state_changed={counters.state_changed}, metadata_changed={counters.metadata_changed}, "
        f"missing={counters.missing}"
    )


def main() -> int:
    """feature_list.json과 GitHub Issue를 동기화한다."""
    args = parse_args()
    dry_run = not args.apply

    feature_path = Path(args.feature_file)
    if not feature_path.exists():
        print(f"[feature-issue-sync] ERROR: feature file not found: {feature_path}")
        return 1

    repo = args.repo or infer_repo_from_origin()
    token = os.getenv(args.token_env)

    if not dry_run and (args.create_missing or args.sync_state) and not token:
        print(
            "[feature-issue-sync] ERROR: apply 모드에서 GitHub 변경을 하려면 "
            f"{args.token_env} 환경변수가 필요합니다."
        )
        return 1

    data = load_feature_file(feature_path)
    features = data.get("features", [])
    if not isinstance(features, list):
        print("[feature-issue-sync] ERROR: 'features' must be a list")
        return 1

    issues = list_all_issues(repo=repo, token=token)
    issue_map: dict[str, IssueRecord] = {
        issue.feature_id: issue for issue in issues if issue.feature_id
    }

    counters = SyncCounters()
    lines: list[str] = []
    feature_file_dirty = False

    for feature in features:
        feature_id = feature.get("id")
        feature_name = feature.get("name", "")
        if not isinstance(feature_id, str) or not feature_id:
            lines.append("- skip: invalid feature id")
            continue

        expected_state = "closed" if bool(feature.get("passes")) else "open"
        issue = issue_map.get(feature_id)

        if issue is None and args.create_missing:
            issue_title = f"[{feature_id}] {feature_name}" if feature_name else f"[{feature_id}]"
            issue_body = build_issue_body(feature)
            if dry_run:
                lines.append(
                    f"- create(dry-run): {feature_id} -> issue '{issue_title}'"
                )
            else:
                assert token is not None
                issue = create_issue(
                    repo=repo,
                    token=token,
                    title=issue_title,
                    body=issue_body,
                    labels=["feature-sync"],
                )
                issue_map[feature_id] = issue
                counters.created += 1
                lines.append(
                    f"- created: {feature_id} -> #{issue.number} ({issue.html_url})"
                )

        if issue is None:
            counters.missing += 1
            lines.append(f"- missing: {feature_id} (linked issue 없음)")
            continue

        counters.linked += 1

        if args.sync_state and issue.state != expected_state:
            if dry_run:
                lines.append(
                    f"- state(dry-run): {feature_id} #{issue.number} "
                    f"{issue.state} -> {expected_state}"
                )
            else:
                assert token is not None
                issue = update_issue_state(
                    repo=repo,
                    token=token,
                    number=issue.number,
                    state=expected_state,
                )
                counters.state_changed += 1
                lines.append(
                    f"- state: {feature_id} #{issue.number} -> {issue.state}"
                )

        if args.write_feature_file and write_issue_metadata(feature, issue):
            counters.metadata_changed += 1
            feature_file_dirty = True

    if args.write_feature_file and feature_file_dirty:
        feature_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        lines.append(f"- wrote: {feature_path}")
    elif args.write_feature_file:
        lines.append("- skipped write: no metadata changes")

    print_summary(repo=repo, dry_run=dry_run, counters=counters, lines=lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
