#!/usr/bin/env bash
# 本地启动入口：准备好虚拟环境与依赖，校验示例数据，再启动后端。
# 用法：
#   ./run.sh              启动服务（启动前自动做环境检查与数据校验）
#   ./run.sh --deps-only  只准备依赖并校验数据，不启动服务（供 make install 使用）
set -euo pipefail
cd "$(dirname "$0")"

# 虚拟环境损坏或来自其他机器（残留旧状态）时直接重建，而不是带病复用
if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c '' 2>/dev/null; then
  echo "虚拟环境缺失或不可用，重新创建 .venv ..."
  rm -rf .venv
  python3 -m venv .venv
fi

# requirements.txt 没变化就跳过安装，避免每次启动都重复装依赖
stamp=.venv/.requirements.stamp
if [ ! -f "$stamp" ] || ! cmp -s requirements.txt "$stamp"; then
  echo "安装/更新依赖 ..."
  .venv/bin/pip install -q -r requirements.txt
  cp requirements.txt "$stamp"
fi

# 启动前校验示例数据（重点：客户申诉关键字段）；失败会打印具体原因并以非零码退出
.venv/bin/python -m app.seed_check

if [ "${1:-}" = "--deps-only" ]; then
  exit 0
fi

exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
