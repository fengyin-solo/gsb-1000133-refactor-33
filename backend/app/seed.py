"""示例数据：由规格表确定性生成，保证换机器、换环境后重新生成结果完全一致。

维护方式：
- 改数据只改下面的 MODULE_SPECS，不要手工编辑生成结果；
- ``python -m app.seed`` 重新生成并打印摘要，``--verify`` 验证两次生成一致；
- 启动时的字段校验在 app.seed_check，与本模块共用同一份生成结果，
  避免"数据一份、检查一份"各自维护导致环境变化后残留旧状态。
"""
from __future__ import annotations

import json
import sys
from typing import Any

ROWS_PER_MODULE = 3
BASE_DATE = "2026-09-0"

# 字段类型：
#   ("code", 前缀)  -> 前缀-000N
#   ("text",)       -> 「<模块标签>样例N」
#   ("date",)       -> 2026-09-0N
#   ("int", 基数)   -> 基数 * N
#   ("float", 基数) -> 基数 * N
FieldSpec = tuple

MODULE_SPECS: dict[str, dict[str, Any]] = {
    "sample": {
        "label": "样品接收",
        "statuses": ["待接收", "已接收", "已退回"],
        "fields": [
            ("样品编号", "code", "SAMP"),
            ("样品名称", "text"),
            ("委托单位", "text"),
            ("样品类型", "text"),
            ("接收日期", "date"),
            ("保存条件", "text"),
            ("送样人员", "text"),
            ("接收状态", "text"),
        ],
    },
    "task": {
        "label": "检测任务",
        "statuses": ["待分配", "已分配", "检测中"],
        "fields": [
            ("任务编号", "code", "TASK"),
            ("所属样品", "text"),
            ("检测项目", "text"),
            ("检测标准", "text"),
            ("指定检测员", "text"),
            ("截止日期", "date"),
            ("优先级", "text"),
            ("任务状态", "text"),
        ],
    },
    "instrument": {
        "label": "仪器管理",
        "statuses": ["在用", "待校准", "校准中"],
        "fields": [
            ("仪器编号", "code", "INST"),
            ("仪器名称", "text"),
            ("型号规格", "text"),
            ("所属实验室", "text"),
            ("校准周期", "text"),
            ("上次校准日", "text"),
            ("下次校准日", "text"),
            ("仪器状态", "text"),
        ],
    },
    "calibration": {
        "label": "校准记录",
        "statuses": ["待校准", "校准中", "已合格"],
        "fields": [
            ("记录编号", "code", "CALI"),
            ("仪器编号", "code", "CALI"),
            ("校准机构", "text"),
            ("校准日期", "date"),
            ("校准结果", "text"),
            ("偏差值", "text"),
            ("校准证书号", "text"),
            ("记录状态", "text"),
        ],
    },
    "reagent": {
        "label": "试剂耗材",
        "statuses": ["在库", "已领用", "已用完"],
        "fields": [
            ("试剂编号", "code", "REAG"),
            ("试剂名称", "text"),
            ("规格等级", "text"),
            ("生产厂家", "text"),
            ("有效期至", "text"),
            ("存放位置", "text"),
            ("领用人员", "text"),
            ("使用状态", "text"),
        ],
    },
    "result": {
        "label": "检测结果",
        "statuses": ["待录入", "已录入", "待审核"],
        "fields": [
            ("结果编号", "code", "RESU"),
            ("所属任务", "text"),
            ("检测项", "text"),
            ("实测值", "text"),
            ("标准限值", "text"),
            ("判定结论", "text"),
            ("检测日期", "date"),
            ("结果状态", "text"),
        ],
    },
    "report": {
        "label": "检测报告",
        "statuses": ["待编制", "编制中", "待批准"],
        "fields": [
            ("报告编号", "code", "REPO"),
            ("委托单位", "text"),
            ("样品名称", "text"),
            ("报告类型", "text"),
            ("编制人", "text"),
            ("批准人", "text"),
            ("签发日期", "date"),
            ("报告状态", "text"),
        ],
    },
    "qc": {
        "label": "质量控制",
        "statuses": ["待检测", "检测中", "受控"],
        "fields": [
            ("质控编号", "code", "QC"),
            ("质控类别", "text"),
            ("标准值", "text"),
            ("允许偏差", "text"),
            ("实测值", "text"),
            ("判定结果", "text"),
            ("检测日期", "date"),
            ("质控状态", "text"),
        ],
    },
    "deviation": {
        "label": "偏离处理",
        "statuses": ["已发现", "调查中", "已处理"],
        "fields": [
            ("偏离编号", "code", "DEVI"),
            ("偏离描述", "text"),
            ("涉及样品", "text"),
            ("发现人", "text"),
            ("发现日期", "date"),
            ("处理措施", "text"),
            ("验证结果", "text"),
            ("偏离状态", "text"),
        ],
    },
    "sample_storage": {
        "label": "样品留存",
        "statuses": ["留存中", "即将到期", "已处置"],
        "fields": [
            ("留存编号", "code", "SAMP"),
            ("样品编号", "code", "SAMP"),
            ("留存位置", "text"),
            ("留存期限", "date"),
            ("到期日期", "date"),
            ("保管人员", "text"),
            ("处理方式", "text"),
            ("留存状态", "text"),
        ],
    },
    "contract": {
        "label": "委托合同",
        "statuses": ["待签约", "执行中", "已完成"],
        "fields": [
            ("合同编号", "code", "CONT"),
            ("委托单位", "text"),
            ("联系人", "text"),
            ("样品数量", "int", 10),
            ("检测项目", "text"),
            ("合同金额", "float", 12.5),
            ("签约日期", "date"),
            ("合同状态", "text"),
        ],
    },
    "staff": {
        "label": "检测人员",
        "statuses": ["在岗", "培训中", "离岗"],
        "fields": [
            ("员工编号", "code", "STAF"),
            ("姓名", "text"),
            ("技术职称", "text"),
            ("资质证书", "text"),
            ("授权项目", "text"),
            ("在岗状态", "text"),
            ("考核日期", "date"),
            ("考核结果", "text"),
        ],
    },
    "method": {
        "label": "检测方法",
        "statuses": ["草案", "验证中", "现行有效"],
        "fields": [
            ("方法编号", "code", "METH"),
            ("方法名称", "text"),
            ("适用标准", "text"),
            ("检测范围", "text"),
            ("检出限", "text"),
            ("方法版本", "text"),
            ("批准日期", "date"),
            ("方法状态", "text"),
        ],
    },
    "environment": {
        "label": "环境监测",
        "statuses": ["正常", "预警", "超标"],
        "fields": [
            ("记录编号", "code", "ENVI"),
            ("监测区域", "text"),
            ("温度值", "text"),
            ("湿度值", "text"),
            ("压差值", "text"),
            ("记录时间", "date"),
            ("记录人员", "text"),
            ("环境状态", "text"),
        ],
    },
    "complain": {
        "label": "客户申诉",
        "statuses": ["待受理", "受理中", "已答复"],
        "fields": [
            ("申诉编号", "code", "COMP"),
            ("申诉单位", "text"),
            ("涉及报告", "text"),
            ("申诉内容", "text"),
            ("受理日期", "date"),
            ("处理结果", "text"),
            ("回复日期", "date"),
            ("申诉状态", "text"),
        ],
    },
    "audit": {
        "label": "内审管理",
        "statuses": ["计划中", "执行中", "已完成"],
        "fields": [
            ("内审编号", "code", "AUDI"),
            ("审核范围", "text"),
            ("审核组长", "text"),
            ("审核日期", "date"),
            ("不符合项", "text"),
            ("纠正期限", "date"),
            ("跟踪验证", "text"),
            ("内审状态", "text"),
        ],
    },
    "equipment_repair": {
        "label": "仪器维修",
        "statuses": ["已报修", "维修中", "已修复"],
        "fields": [
            ("维修编号", "code", "EQUI"),
            ("仪器编号", "code", "EQUI"),
            ("故障描述", "text"),
            ("报修人", "text"),
            ("报修日期", "date"),
            ("维修单位", "text"),
            ("修复日期", "date"),
            ("维修状态", "text"),
        ],
    },
    "document": {
        "label": "体系文档",
        "statuses": ["草案", "审批中", "正式发布"],
        "fields": [
            ("文档编号", "code", "DOCU"),
            ("文档名称", "text"),
            ("文档类型", "text"),
            ("编制人", "text"),
            ("版本号", "text"),
            ("生效日期", "date"),
            ("分发范围", "text"),
            ("文档状态", "text"),
        ],
    },
}


def _field_value(spec: FieldSpec, label: str, index: int) -> Any:
    kind = spec[1]
    if kind == "code":
        return f"{spec[2]}-{index:04d}"
    if kind == "text":
        return f"{label}样例{index}"
    if kind == "date":
        return f"{BASE_DATE}{index}"
    if kind == "int":
        return int(spec[2]) * index
    if kind == "float":
        return float(spec[2]) * index
    raise ValueError(f"未知字段类型：{kind!r}（{spec!r}）")


def build_seed_rows() -> dict[str, list[dict[str, Any]]]:
    """从规格表确定性生成全部示例数据；同样的规格在任何环境下生成同样结果。"""
    tables: dict[str, list[dict[str, Any]]] = {}
    for module, spec in MODULE_SPECS.items():
        rows: list[dict[str, Any]] = []
        for index in range(1, ROWS_PER_MODULE + 1):
            row: dict[str, Any] = {
                "id": index,
                "status": spec["statuses"][index - 1],
                "pending": index < ROWS_PER_MODULE,
                "abnormal": index == 2,
            }
            for field in spec["fields"]:
                row[field[0]] = _field_value(field, spec["label"], index)
            rows.append(row)
        tables[module] = rows
    return tables


SEED_ROWS: dict[str, list[dict[str, Any]]] = build_seed_rows()


def main(argv: list[str]) -> int:
    if "--json" in argv:
        print(json.dumps(SEED_ROWS, ensure_ascii=False, indent=2))
        return 0
    if "--verify" in argv:
        again = build_seed_rows()
        if again != SEED_ROWS:
            print("示例数据重复生成结果不一致，请检查 MODULE_SPECS 是否含有随机或时间相关取值")
            return 1
        print("重复生成校验通过：两次生成的示例数据完全一致")
    total = sum(len(rows) for rows in SEED_ROWS.values())
    print(f"已生成 {len(SEED_ROWS)} 个模块、共 {total} 条示例数据：")
    for module, rows in SEED_ROWS.items():
        print(f"  - {module}: {len(rows)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
