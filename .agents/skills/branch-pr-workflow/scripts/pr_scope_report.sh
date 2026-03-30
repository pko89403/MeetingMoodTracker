#!/usr/bin/env bash
# pr_scope_report.sh: 커밋/PR 범위 판단을 위한 변경사항 리포트를 출력한다.

set -euo pipefail

BASE_REF="${1:-origin/main}"

if ! ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "[scope] 오류: git 저장소가 아닙니다."
  exit 1
fi

cd "${ROOT_DIR}"

print_section() {
  local title
  title="$1"
  echo
  echo "== ${title} =="
}

BASE_REF_EXISTS="false"
if git rev-parse --verify --quiet "${BASE_REF}" >/dev/null; then
  BASE_REF_EXISTS="true"
fi

echo "[scope] repo: ${ROOT_DIR}"
echo "[scope] base_ref: ${BASE_REF} (exists=${BASE_REF_EXISTS})"

print_section "Current Branch / Status"
git status -sb

print_section "Staged Files"
if ! git diff --name-only --cached | sed '/^$/d'; then
  true
fi

print_section "Unstaged Files"
if ! git diff --name-only | sed '/^$/d'; then
  true
fi

print_section "Untracked Files"
if ! git ls-files --others --exclude-standard | sed '/^$/d'; then
  true
fi

print_section "Staged Diffstat"
if ! git diff --cached --stat; then
  true
fi

print_section "Unstaged Diffstat"
if ! git diff --stat; then
  true
fi

if [[ "${BASE_REF_EXISTS}" == "true" ]]; then
  print_section "Commits ahead of ${BASE_REF}"
  if ! git log --oneline "${BASE_REF}..HEAD"; then
    true
  fi

  print_section "Files changed vs ${BASE_REF}"
  if ! git diff --name-status "${BASE_REF}...HEAD"; then
    true
  fi
else
  print_section "Files changed vs ${BASE_REF}"
  echo "[scope] 경고: base_ref를 찾지 못해 비교를 건너뜁니다."
fi

TMP_FILE="$(mktemp)"
{
  git diff --name-only --cached
  git diff --name-only
  git ls-files --others --exclude-standard
  if [[ "${BASE_REF_EXISTS}" == "true" ]]; then
    git diff --name-only "${BASE_REF}...HEAD"
  fi
} | sed '/^$/d' | sort -u > "${TMP_FILE}"

print_section "Suggested Commit Groups (by top-level path)"
if [[ -s "${TMP_FILE}" ]]; then
  awk -F/ '
    {
      top = $1;
      if (NF == 1) top = "(root)";
      count[top] += 1;
    }
    END {
      for (k in count) {
        printf "%s\t%d\n", k, count[k];
      }
    }
  ' "${TMP_FILE}" | sort -k2,2nr -k1,1
else
  echo "[scope] 변경 파일이 없습니다."
fi

rm -f "${TMP_FILE}"
