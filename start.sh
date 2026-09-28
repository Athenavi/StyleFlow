#!/usr/bin/env bash
# StyleFlow 一键启动（macOS / Linux）
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PY=python3
  elif command -v python >/dev/null 2>&1; then
    PY=python
  else
    echo "[错误] 未检测到 Python，请先安装 Python 3.11 或更高版本" >&2
    exit 1
  fi
fi

exec "$PY" start.py "$@"
