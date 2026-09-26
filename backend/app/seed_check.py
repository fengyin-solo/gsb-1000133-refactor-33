"""示例数据启动校验：服务启动前先把数据问题拦下来，并打印具体原因。

重点校验客户申诉（complain）的关键字段：申诉编号、申诉单位、涉及报告、申诉内容；
其余模块做通用一致性检查。数据与校验都基于 app.seed 的生成结果，
避免两边各自维护、环境变化后残留旧状态。

用法：``python -m app.seed_check``，全部通过退出码 0，否则打印原因并退出码 1。
"""
from __future__ import annotations

import re
import sys
from typing import Any

# 客户申诉关键字段：逐行必须非空
COMPLAIN_KEY_FIELDS = ["申诉编号", "申诉单位", "涉及报告", "申诉内容"]
COMPLAIN_CODE_PATTERN = re.compile(r"^COMP-\d{4}$")


class SeedDataError(RuntimeError):
    """示例数据校验未通过；消息里列出全部具体问题，方便一次性修完。"""


def validate_seed(tables: dict[str, list[dict[str, Any]]]) -> list[str]:
    """返回问题列表，空列表表示校验通过。"""
    problems: list[str] = []
    for module, rows in tables.items():
        if not rows:
            problems.append(f"{module}：没有任何示例数据")
            continue
        ids = [row.get("id") for row in rows]
        if len(set(ids)) != len(ids):
            problems.append(f"{module}：id 存在重复 {ids}")
        key_sets = {tuple(row.keys()) for row in rows}
        if len(key_sets) != 1:
            problems.append(f"{module}：各行的字段集合不一致，请检查生成规格")
        for row in rows:
            row_id = row.get("id", "?")
            if not str(row.get("status") or "").strip():
                problems.append(f"{module} 第{row_id}行：status 为空")
            for field, value in row.items():
                if field.endswith("编号"):
                    if not str(value or "").strip():
                        problems.append(f"{module} 第{row_id}行：{field} 为空")
        for field in rows[0]:
            if field.endswith("编号"):
                values = [row.get(field) for row in rows]
                if len(set(values)) != len(values):
                    problems.append(f"{module}：{field} 存在重复 {values}")
    problems.extend(_validate_complain(tables.get("complain", [])))
    return problems


def _validate_complain(rows: list[dict[str, Any]]) -> list[str]:
    """客户申诉关键字段专项校验：申诉编号、申诉单位、涉及报告、申诉内容。"""
    problems: list[str] = []
    if not rows:
        return ["complain：缺少客户申诉示例数据"]
    codes: list[str] = []
    for row in rows:
        row_id = row.get("id", "?")
        for field in COMPLAIN_KEY_FIELDS:
            value = row.get(field)
            if not str(value or "").strip():
                problems.append(f"complain 第{row_id}行：关键字段「{field}」为空")
        code = str(row.get("申诉编号") or "")
        if code and not COMPLAIN_CODE_PATTERN.match(code):
            problems.append(
                f"complain 第{row_id}行：申诉编号「{code}」格式应为 COMP-四位数字"
            )
        codes.append(code)
    if len(set(codes)) != len(codes):
        problems.append(f"complain：申诉编号存在重复 {codes}")
    return problems


def ensure_valid(tables: dict[str, list[dict[str, Any]]]) -> None:
    """校验不通过时抛出 SeedDataError，消息逐条列出原因。"""
    problems = validate_seed(tables)
    if problems:
        detail = "\n".join(f"  - {item}" for item in problems)
        raise SeedDataError(
            f"示例数据校验未通过，共 {len(problems)} 处问题：\n{detail}\n"
            "请修正 app/seed.py 中的 MODULE_SPECS 后重新启动。"
        )


def main() -> int:
    try:
        from app.seed import SEED_ROWS
    except Exception as exc:  # 生成阶段就失败（如字段类型写错）时，同样给出可读原因
        print(f"示例数据生成失败：{exc}")
        print("请修正 app/seed.py 中的 MODULE_SPECS 后重新启动。")
        return 1
    problems = validate_seed(SEED_ROWS)
    if problems:
        print(f"示例数据校验未通过，共 {len(problems)} 处问题：")
        for item in problems:
            print(f"  - {item}")
        print("请修正 app/seed.py 中的 MODULE_SPECS 后重新启动。")
        return 1
    total = sum(len(rows) for rows in SEED_ROWS.values())
    print(f"示例数据校验通过：{len(SEED_ROWS)} 个模块、共 {total} 条记录；")
    print("客户申诉关键字段（申诉编号、申诉单位、涉及报告、申诉内容）均符合要求。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
