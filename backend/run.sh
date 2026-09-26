#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
./scripts/ensure_venv.sh
# 启动前置检查：示例数据与规格不一致时直接失败并打印原因，不带残留状态启动
.venv/bin/python -m app.seed_check
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
