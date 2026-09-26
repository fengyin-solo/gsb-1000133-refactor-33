"""示例数据启动检查：生成脚本、run.sh 预检、服务启动共用同一套规则。

规则来源是 app.seed_spec（唯一事实来源），这里只负责执行校验并汇总问题；
任何一处失败都会带上模块名、行号与修复建议，修好后执行 make reseed 再重启即可。
直接运行 `python3 -m app.seed_check` 可手工做一次完整检查。
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.seed_spec import MODULE_SPECS, FieldCheck, ModuleSpec, build_seed_rows


@dataclass(frozen=True)
class SeedIssue:
    module: str
    row: int | None
    message: str

    def format(self) -> str:
        where = f"模块 {self.module}"
        if self.row is not None:
            where += f" 第 {self.row} 行"
        return f"{where}：{self.message}"


def _check_freshness(seed_rows: dict[str, list[dict[str, Any]]]) -> list[SeedIssue]:
    """新鲜度检查：seed.py 必须是由 seed_spec.py 生成的结果，防止手工改出残留状态。"""
    if seed_rows != build_seed_rows():
        return [SeedIssue(
            "seed", None,
            "app/seed.py 与 app/seed_spec.py 的生成结果不一致（可能被手工改过或规格已更新），"
            "请执行 make reseed 重新生成",
        )]
    return []


def _check_row(spec: ModuleSpec, row: dict[str, Any], index: int) -> list[SeedIssue]:
    issues: list[SeedIssue] = []

    def add(message: str) -> None:
        issues.append(SeedIssue(spec.name, index, message))

    if row.get("id") != index:
        add(f"id 应为 {index}，实际为 {row.get('id')!r}")
    status = row.get("status")
    if status not in spec.statuses:
        add(f"status「{status}」不在允许的状态序列 {list(spec.statuses)} 里")
    for flag in ("pending", "abnormal"):
        if not isinstance(row.get(flag), bool):
            add(f"标记字段 {flag} 必须是布尔值")

    known_fields = {field.name for field in spec.fields}
    extra = sorted(set(row) - known_fields - {"id", "status", "pending", "abnormal"})
    if extra:
        add(f"存在规格之外的字段：{'、'.join(extra)}，请同步 app/seed_spec.py")

    # 同一字段已有专项 required/pattern 检查时，通用的非空/格式检查让位，避免重复报错
    required_fields = {check.field for check in spec.checks if check.kind == "required"}
    pattern_fields = {check.field for check in spec.checks if check.kind == "pattern"}

    for field in spec.fields:
        if field.name not in row:
            add(f"缺少字段「{field.name}」")
            continue
        value = row[field.name]
        is_empty = value is None or (isinstance(value, str) and not value.strip())
        if is_empty and field.name not in required_fields:
            add(f"字段「{field.name}」不能为空")
            continue
        if field.kind == "code" and field.name not in pattern_fields and not is_empty:
            if not re.fullmatch(rf"{field.prefix}-\d{{4}}", str(value)):
                add(f"字段「{field.name}」必须符合 {field.prefix}-XXXX 格式，当前值「{value}」")
        elif field.kind == "date" and not is_empty:
            try:
                date.fromisoformat(str(value))
            except ValueError:
                add(f"字段「{field.name}」必须是 YYYY-MM-DD 日期，当前值「{value}」")
    return issues


def _check_module(spec: ModuleSpec, rows: list[dict[str, Any]]) -> list[SeedIssue]:
    issues: list[SeedIssue] = []
    if len(rows) != spec.rows:
        issues.append(SeedIssue(spec.name, None, f"示例数据应为 {spec.rows} 行，实际 {len(rows)} 行"))
    for index, row in enumerate(rows, start=1):
        issues.extend(_check_row(spec, row, index))
    return issues


def _run_field_check(spec: ModuleSpec, rows: list[dict[str, Any]], check: FieldCheck,
                     seed_rows: dict[str, list[dict[str, Any]]]) -> list[SeedIssue]:
    issues: list[SeedIssue] = []
    values = [row.get(check.field) for row in rows]

    def add(index: int, detail: str = "") -> None:
        suffix = f"，{detail}" if detail else ""
        issues.append(SeedIssue(spec.name, index, f"{check.message}{suffix}"))

    if check.kind == "required":
        for index, value in enumerate(values, start=1):
            if value is None or not str(value).strip():
                add(index)
    elif check.kind == "unique":
        seen: dict[str, int] = {}
        for index, value in enumerate(values, start=1):
            key = str(value)
            if key in seen:
                add(index, f"与第 {seen[key]} 行重复：{key}")
            else:
                seen[key] = index
    elif check.kind == "pattern":
        for index, value in enumerate(values, start=1):
            if not re.fullmatch(check.pattern, str(value or "")):
                add(index, f"当前值「{value}」")
    elif check.kind == "min_length":
        for index, value in enumerate(values, start=1):
            if len(str(value or "")) < check.min_length:
                add(index, f"当前仅 {len(str(value or ''))} 个字符")
    elif check.kind == "ref":
        ref_pool = {str(row.get(check.ref_field)) for row in seed_rows.get(check.ref_module, [])}
        for index, value in enumerate(values, start=1):
            text = str(value or "")
            if text and text not in ref_pool:
                add(index, f"「{text}」在 {check.ref_module} 模块中不存在")
    else:
        issues.append(SeedIssue(spec.name, None, f"未知检查类型：{check.kind}"))
    return issues


def verify_seed_rows(seed_rows: dict[str, list[dict[str, Any]]]) -> list[SeedIssue]:
    """语义校验：模块齐全、行数与字段符合规格、关键申诉字段通过专项检查。"""
    issues: list[SeedIssue] = []
    expected = {spec.name for spec in MODULE_SPECS}
    for name in sorted(expected - set(seed_rows)):
        issues.append(SeedIssue(name, None, "缺少该模块的示例数据，请执行 make reseed 重新生成"))
    for name in sorted(set(seed_rows) - expected):
        issues.append(SeedIssue(name, None, "存在规格之外的模块数据，请同步 app/seed_spec.py"))
    for spec in MODULE_SPECS:
        rows = seed_rows.get(spec.name)
        if rows is None:
            continue
        issues.extend(_check_module(spec, rows))
        for check in spec.checks:
            issues.extend(_run_field_check(spec, rows, check, seed_rows))
    return issues


def verify_seed() -> list[SeedIssue]:
    """完整校验：先核对 seed.py 是否由规格生成，再做语义校验。"""
    from app.seed import SEED_ROWS  # 延迟导入，避免生成脚本写入后读到旧缓存

    return [*_check_freshness(SEED_ROWS), *verify_seed_rows(SEED_ROWS)]


def format_issues(issues: list[SeedIssue]) -> str:
    lines = ["示例数据校验未通过，请按以下原因修复："]
    lines.extend(f"  - {issue.format()}" for issue in issues)
    lines.append("修复规格或数据后执行 make reseed 重新生成示例数据，再重新启动服务。")
    return "\n".join(lines)


def main() -> int:
    issues = verify_seed()
    if issues:
        print(format_issues(issues), file=sys.stderr)
        return 1
    print(f"示例数据校验通过：{len(MODULE_SPECS)} 个模块与规格一致，"
          "关键申诉字段（申诉编号、申诉单位、涉及报告、申诉内容）检查全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
