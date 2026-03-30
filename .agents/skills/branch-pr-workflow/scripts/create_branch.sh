#!/usr/bin/env bash
# create_branch.sh: codex/<slug> 브랜치를 생성하거나 전환한다.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <branch-slug-or-title> [prefix]"
  exit 1
fi

RAW_NAME="$1"
PREFIX="${2:-codex}"

normalize_slug() {
  local value slug
  value="$1"
  slug="$(printf "%s" "${value}" | tr '[:upper:]' '[:lower:]')"
  slug="$(printf "%s" "${slug}" | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-{2,}/-/g')"
  if [[ -z "${slug}" ]]; then
    slug="update"
  fi
  printf "%s" "${slug}"
}

if ! ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "[branch] 오류: git 저장소가 아닙니다."
  exit 1
fi

cd "${ROOT_DIR}"
SLUG="$(normalize_slug "${RAW_NAME}")"
TARGET_BRANCH="${PREFIX}/${SLUG}"

CURRENT_BRANCH="$(git branch --show-current || true)"
if [[ "${CURRENT_BRANCH}" == "${TARGET_BRANCH}" ]]; then
  echo "[branch] 이미 ${TARGET_BRANCH} 브랜치에 있습니다."
  echo "${TARGET_BRANCH}"
  exit 0
fi

if git show-ref --verify --quiet "refs/heads/${TARGET_BRANCH}"; then
  git switch "${TARGET_BRANCH}"
  echo "[branch] 기존 브랜치로 전환: ${TARGET_BRANCH}"
else
  git switch -c "${TARGET_BRANCH}"
  echo "[branch] 새 브랜치 생성: ${TARGET_BRANCH}"
fi

echo "${TARGET_BRANCH}"
