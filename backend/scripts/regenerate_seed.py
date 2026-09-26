#!/usr/bin/env python3
"""根据 app/seed_spec.py 重新生成 app/seed.py，保证示例数据可重复生成。

用法：
    python3 scripts/regenerate_seed.py          # 重新生成 app/seed.py 并校验
    python3 scripts/regenerate_seed.py --check  # 只校验不写入，不一致时退出码为 1
"""
from __future__ import annotations

import argparse
import pprint
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.seed_check import format_issues, verify_seed, verify_seed_rows  # noqa: E402
from app.seed_spec import build_seed_rows  # noqa: E402

SEED_PATH = BACKEND_ROOT / "app" / "seed.py"

HEADER = '''"""示例数据：由 app/seed_spec.py 生成，请勿手工编辑。

重新生成：make reseed（或 python3 scripts/regenerate_seed.py）。
启动时会按 app/seed_check.py 的规则校验本文件，校验失败服务拒绝启动。
"""
from __future__ import annotations

from typing import Any

'''


def render_seed_module() -> str:
    rows = build_seed_rows()
    return HEADER + "SEED_ROWS: dict[str, list[dict[str, Any]]] = " + pprint.pformat(
        rows, width=100, sort_dicts=False
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只校验现有 seed.py，不写入")
    args = parser.parse_args()

    if args.check:
        issues = verify_seed()
        if issues:
            print(format_issues(issues), file=sys.stderr)
            return 1
        print("示例数据校验通过：seed.py 与规格一致。")
        return 0

    content = render_seed_module()
    if SEED_PATH.exists() and SEED_PATH.read_text(encoding="utf-8") == content:
        print("app/seed.py 已是最新，仍执行校验。")
    else:
        SEED_PATH.write_text(content, encoding="utf-8")
        print("已重新生成 app/seed.py。")
    # 无论是否重写都做语义校验：规格本身有问题时，不能因为文件“已是最新”就放行。
    # 校验的是本次生成结果（与文件内容一致），避免 import 缓存读到旧模块。
    issues = verify_seed_rows(build_seed_rows())
    if issues:
        print(format_issues(issues), file=sys.stderr)
        return 1
    print("示例数据校验全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
