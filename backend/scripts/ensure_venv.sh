#!/usr/bin/env bash
# 确保 backend/.venv 可用：缺失、残留自其他环境、或 pip 跑不起来时重建。
set -euo pipefail
cd "$(dirname "$0")/.."

create_venv() {
  rm -rf .venv
  if python3 -m venv .venv 2>/dev/null && .venv/bin/python -m pip --version >/dev/null 2>&1; then
    return 0
  fi
  # 系统缺少 ensurepip（如 Debian 未装 python3-venv）时，降级为手动引导 pip
  echo "python3 -m venv 自带的 pip 不可用，改用 --without-pip 并手动引导 pip..." >&2
  rm -rf .venv
  python3 -m venv --without-pip .venv
  curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
  .venv/bin/python /tmp/get-pip.py -q
  rm -f /tmp/get-pip.py
}

if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
  if [ -d .venv ]; then
    echo "检测到 .venv 不可用（缺失或残留自其他环境），正在重建..." >&2
  fi
  create_venv
fi
.venv/bin/pip install -q -r requirements.txt
