#!/usr/bin/env bash
# Codex worktree 생성 시 실행되는 기본 셋업 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKTREE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export UV_PROJECT_ENVIRONMENT="${WORKTREE_ROOT}/.venv"
export UV_CACHE_DIR="${UV_CACHE_DIR:-${HOME}/.cache/uv}"

# Homebrew/local bin이 빠진 셸에서도 공통 툴 탐색이 가능하도록 PATH를 보강한다.
if [[ -d "/opt/homebrew/bin" ]]; then
  export PATH="/opt/homebrew/bin:${PATH}"
fi
if [[ -d "${HOME}/.local/bin" ]]; then
  export PATH="${HOME}/.local/bin:${PATH}"
fi

_find_uv_bin() {
  if command -v uv >/dev/null 2>&1; then
    command -v uv
    return 0
  fi
  if [[ -x "${HOME}/.local/bin/uv" ]]; then
    echo "${HOME}/.local/bin/uv"
    return 0
  fi
  if [[ -x "/opt/homebrew/bin/uv" ]]; then
    echo "/opt/homebrew/bin/uv"
    return 0
  fi
  return 1
}

_find_main_worktree_root() {
  local current_root path line
  current_root="${WORKTREE_ROOT}"
  path=""

  while IFS= read -r line; do
    case "${line}" in
      worktree\ *)
        path="${line#worktree }"
        ;;
      branch\ refs/heads/main)
        if [[ -n "${path}" && "${path}" != "${current_root}" ]]; then
          echo "${path}"
          return 0
        fi
        ;;
    esac
  done < <(git -C "${WORKTREE_ROOT}" worktree list --porcelain 2>/dev/null || true)

  return 1
}

_sync_env_file_from_main_worktree() {
  local env_name src dst
  env_name="$1"
  dst="${WORKTREE_ROOT}/${env_name}"

  if [[ -f "${dst}" ]]; then
    echo "[setup] ${env_name} 이미 존재하여 복사를 건너뜁니다."
    return 0
  fi

  if [[ -z "${MAIN_WORKTREE_ROOT:-}" ]]; then
    echo "[setup] main worktree를 찾지 못해 ${env_name} 자동 복사를 건너뜁니다."
    return 0
  fi

  src="${MAIN_WORKTREE_ROOT}/${env_name}"
  if [[ ! -f "${src}" ]]; then
    echo "[setup] main worktree에 ${env_name} 파일이 없어 복사를 건너뜁니다."
    return 0
  fi

  cp "${src}" "${dst}"
  chmod 600 "${dst}" || true
  echo "[setup] ${env_name}을(를) main worktree에서 복사했습니다."
}

if ! UV_BIN="$(_find_uv_bin)"; then
  echo "[setup] 오류: uv 실행 파일을 찾을 수 없습니다."
  exit 127
fi

# Codex 하위 프로세스(예: git pre-commit hook)에서도 uv를 찾을 수 있게 PATH를 보강한다.
export PATH="$(dirname "${UV_BIN}"):${PATH}"

MAIN_WORKTREE_ROOT=""
if MAIN_WORKTREE_ROOT="$(_find_main_worktree_root)"; then
  echo "[setup] main worktree 감지: ${MAIN_WORKTREE_ROOT}"
else
  MAIN_WORKTREE_ROOT=""
  echo "[setup] main worktree를 찾지 못했습니다."
fi

_sync_env_file_from_main_worktree "dev.env"
_sync_env_file_from_main_worktree "prod.env"
echo "[setup] worktree 가상환경 준비: ${UV_PROJECT_ENVIRONMENT}"
if [[ -f "${UV_PROJECT_ENVIRONMENT}/pyvenv.cfg" ]]; then
  echo "[setup] 기존 가상환경 재사용"
else
  "${UV_BIN}" venv "${UV_PROJECT_ENVIRONMENT}"
fi

echo "[setup] uv 의존성 동기화 시작 (cache: ${UV_CACHE_DIR})"
cd "${WORKTREE_ROOT}"
"${UV_BIN}" sync --locked

if [[ "${SKIP_FEATURE_ISSUE_SYNC:-0}" != "1" ]] && [[ -f "${WORKTREE_ROOT}/scripts/sync_feature_issues.py" ]]; then
  GH_BIN=""
  if command -v gh >/dev/null 2>&1; then
    GH_BIN="$(command -v gh)"
  elif [[ -x "/opt/homebrew/bin/gh" ]]; then
    GH_BIN="/opt/homebrew/bin/gh"
  elif [[ -x "/usr/local/bin/gh" ]]; then
    GH_BIN="/usr/local/bin/gh"
  fi

  if [[ -z "${GITHUB_TOKEN:-}" ]] && [[ -n "${GH_BIN}" ]]; then
    if "${GH_BIN}" auth status >/dev/null 2>&1; then
      GITHUB_TOKEN="$("${GH_BIN}" auth token 2>/dev/null || true)"
      export GITHUB_TOKEN
    fi
  fi

  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    echo "[setup] feature_list <-> GitHub issue 동기화 실행"
    if ! "${UV_BIN}" run python scripts/sync_feature_issues.py --create-missing --sync-state --write-feature-file --apply; then
      echo "[setup] 경고: feature issue 동기화 실패 (개발 환경 셋업은 계속 진행)"
    fi
  else
    echo "[setup] 안내: GITHUB_TOKEN/gh auth 없음으로 feature issue 동기화 단계는 건너뜀"
  fi
fi

echo "[setup] worktree 셋업 완료"
