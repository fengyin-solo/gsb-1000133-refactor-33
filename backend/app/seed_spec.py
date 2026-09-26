"""示例数据规格：所有模块的字段、状态与关键校验规则的唯一事实来源。

- app/seed.py 由 scripts/regenerate_seed.py 根据本文件生成，请勿手工编辑；
- app/seed_check.py 按本文件声明的规则做启动检查；
- 调整示例数据时只改这里，然后执行 make reseed 重新生成并校验。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# 每行通用标记：前两行待处理，第二行异常，最后一行已办结
ROW_PENDING = (True, True, False)
ROW_ABNORMAL = (False, True, False)


@dataclass(frozen=True)
class FieldSpec:
    """一个业务字段的生成规则。"""

    name: str
    kind: str  # code / text / date / int / float / ref / fixed
    prefix: str = ""  # kind=code 时的编号前缀
    values: tuple[Any, ...] = ()  # kind=fixed 时的逐行取值（单值则每行相同）
    ref_module: str = ""  # kind=ref 时引用的模块
    ref_field: str = ""  # kind=ref 时引用的字段


@dataclass(frozen=True)
class FieldCheck:
    """启动检查规则：kind 支持 required / unique / pattern / min_length / ref。"""

    field: str
    kind: str
    message: str
    pattern: str = ""
    min_length: int = 0
    ref_module: str = ""
    ref_field: str = ""


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    label: str
    rows: int
    statuses: tuple[str, ...]
    fields: tuple[FieldSpec, ...]
    checks: tuple[FieldCheck, ...] = ()


def code(name: str, prefix: str) -> FieldSpec:
    return FieldSpec(name=name, kind="code", prefix=prefix)


def text(name: str) -> FieldSpec:
    return FieldSpec(name=name, kind="text")


def date(name: str) -> FieldSpec:
    return FieldSpec(name=name, kind="date")


# 客户申诉的演示数据：申诉单位、涉及报告、申诉内容都按真实业务口吻准备，
# 涉及报告逐行引用检测报告模块的 REPO-000X，保证引用完整性可被校验。
COMPLAIN_UNITS = ("杭州临安区蓝天食品厂", "宁波海曙区康泰门诊部", "金华婺城区育才中学")
COMPLAIN_CONTENTS = (
    "报告 REPO-0001 中菌落总数实测值与检测原始记录不一致，申请复核检测数据并重新出具报告。",
    "报告 REPO-0002 未按委托合同约定附 CMA 资质认定标志，申请补发带标志的正式报告。",
    "报告 REPO-0003 样品接收时间与实际送样时间不符，申请核实收样记录并更正报告信息。",
)

# 客户申诉关键字段的启动检查规则：编号格式与唯一性、单位非空、
# 涉及报告必须引用检测报告模块中真实存在的报告编号、申诉内容要写清事实与诉求。
COMPLAIN_CHECKS = (
    FieldCheck(field="申诉编号", kind="pattern", pattern=r"^COMP-\d{4}$",
               message="申诉编号必须符合 COMP-XXXX 格式"),
    FieldCheck(field="申诉编号", kind="unique",
               message="申诉编号不允许重复"),
    FieldCheck(field="申诉单位", kind="required",
               message="申诉单位不能为空"),
    FieldCheck(field="涉及报告", kind="required",
               message="涉及报告不能为空"),
    FieldCheck(field="涉及报告", kind="ref", ref_module="report", ref_field="报告编号",
               message="涉及报告必须引用检测报告模块中存在的报告编号"),
    FieldCheck(field="申诉内容", kind="required",
               message="申诉内容不能为空"),
    FieldCheck(field="申诉内容", kind="min_length", min_length=10,
               message="申诉内容至少 10 个字符，需写清事实与诉求"),
)

MODULE_SPECS: tuple[ModuleSpec, ...] = (
    ModuleSpec(
        name="sample", label="样品接收", rows=3,
        statuses=("待接收", "已接收", "已退回"),
        fields=(code("样品编号", "SAMP"), text("样品名称"), text("委托单位"), text("样品类型"),
                date("接收日期"), text("保存条件"), text("送样人员"), text("接收状态")),
    ),
    ModuleSpec(
        name="task", label="检测任务", rows=3,
        statuses=("待分配", "已分配", "检测中"),
        fields=(code("任务编号", "TASK"), text("所属样品"), text("检测项目"), text("检测标准"),
                text("指定检测员"), date("截止日期"), text("优先级"), text("任务状态")),
    ),
    ModuleSpec(
        name="instrument", label="仪器管理", rows=3,
        statuses=("在用", "待校准", "校准中"),
        fields=(code("仪器编号", "INST"), text("仪器名称"), text("型号规格"), text("所属实验室"),
                text("校准周期"), text("上次校准日"), text("下次校准日"), text("仪器状态")),
    ),
    ModuleSpec(
        name="calibration", label="校准记录", rows=3,
        statuses=("待校准", "校准中", "已合格"),
        fields=(code("记录编号", "CALI"), code("仪器编号", "CALI"), text("校准机构"),
                date("校准日期"), text("校准结果"), text("偏差值"), text("校准证书号"), text("记录状态")),
    ),
    ModuleSpec(
        name="reagent", label="试剂耗材", rows=3,
        statuses=("在库", "已领用", "已用完"),
        fields=(code("试剂编号", "REAG"), text("试剂名称"), text("规格等级"), text("生产厂家"),
                text("有效期至"), text("存放位置"), text("领用人员"), text("使用状态")),
    ),
    ModuleSpec(
        name="result", label="检测结果", rows=3,
        statuses=("待录入", "已录入", "待审核"),
        fields=(code("结果编号", "RESU"), text("所属任务"), text("检测项"), text("实测值"),
                text("标准限值"), text("判定结论"), date("检测日期"), text("结果状态")),
    ),
    ModuleSpec(
        name="report", label="检测报告", rows=3,
        statuses=("待编制", "编制中", "待批准"),
        fields=(code("报告编号", "REPO"), text("委托单位"), text("样品名称"), text("报告类型"),
                text("编制人"), text("批准人"), date("签发日期"), text("报告状态")),
    ),
    ModuleSpec(
        name="qc", label="质量控制", rows=3,
        statuses=("待检测", "检测中", "受控"),
        fields=(code("质控编号", "QC"), text("质控类别"), text("标准值"), text("允许偏差"),
                text("实测值"), text("判定结果"), date("检测日期"), text("质控状态")),
    ),
    ModuleSpec(
        name="deviation", label="偏离处理", rows=3,
        statuses=("已发现", "调查中", "已处理"),
        fields=(code("偏离编号", "DEVI"), text("偏离描述"), text("涉及样品"), text("发现人"),
                date("发现日期"), text("处理措施"), text("验证结果"), text("偏离状态")),
    ),
    ModuleSpec(
        name="sample_storage", label="样品留存", rows=3,
        statuses=("留存中", "即将到期", "已处置"),
        fields=(code("留存编号", "SAMP"), code("样品编号", "SAMP"), text("留存位置"),
                date("留存期限"), date("到期日期"), text("保管人员"), text("处理方式"), text("留存状态")),
    ),
    ModuleSpec(
        name="contract", label="委托合同", rows=3,
        statuses=("待签约", "执行中", "已完成"),
        fields=(code("合同编号", "CONT"), text("委托单位"), text("联系人"),
                FieldSpec(name="样品数量", kind="int"), text("检测项目"),
                FieldSpec(name="合同金额", kind="float"), date("签约日期"), text("合同状态")),
    ),
    ModuleSpec(
        name="staff", label="检测人员", rows=3,
        statuses=("在岗", "培训中", "离岗"),
        fields=(code("员工编号", "STAF"), text("姓名"), text("技术职称"), text("资质证书"),
                text("授权项目"), text("在岗状态"), date("考核日期"), text("考核结果")),
    ),
    ModuleSpec(
        name="method", label="检测方法", rows=3,
        statuses=("草案", "验证中", "现行有效"),
        fields=(code("方法编号", "METH"), text("方法名称"), text("适用标准"), text("检测范围"),
                text("检出限"), text("方法版本"), date("批准日期"), text("方法状态")),
    ),
    ModuleSpec(
        name="environment", label="环境监测", rows=3,
        statuses=("正常", "预警", "超标"),
        fields=(code("记录编号", "ENVI"), text("监测区域"), text("温度值"), text("湿度值"),
                text("压差值"), date("记录时间"), text("记录人员"), text("环境状态")),
    ),
    ModuleSpec(
        name="complain", label="客户申诉", rows=3,
        statuses=("待受理", "受理中", "已答复"),
        fields=(code("申诉编号", "COMP"),
                FieldSpec(name="申诉单位", kind="fixed", values=COMPLAIN_UNITS),
                FieldSpec(name="涉及报告", kind="ref", ref_module="report", ref_field="报告编号"),
                FieldSpec(name="申诉内容", kind="fixed", values=COMPLAIN_CONTENTS),
                date("受理日期"), text("处理结果"), date("回复日期"), text("申诉状态")),
        checks=COMPLAIN_CHECKS,
    ),
    ModuleSpec(
        name="audit", label="内审管理", rows=3,
        statuses=("计划中", "执行中", "已完成"),
        fields=(code("内审编号", "AUDI"), text("审核范围"), text("审核组长"), date("审核日期"),
                text("不符合项"), date("纠正期限"), text("跟踪验证"), text("内审状态")),
    ),
    ModuleSpec(
        name="equipment_repair", label="仪器维修", rows=3,
        statuses=("已报修", "维修中", "已修复"),
        fields=(code("维修编号", "EQUI"), code("仪器编号", "EQUI"), text("故障描述"),
                text("报修人"), date("报修日期"), text("维修单位"), date("修复日期"), text("维修状态")),
    ),
    ModuleSpec(
        name="document", label="体系文档", rows=3,
        statuses=("草案", "审批中", "正式发布"),
        fields=(code("文档编号", "DOCU"), text("文档名称"), text("文档类型"), text("编制人"),
                text("版本号"), date("生效日期"), text("分发范围"), text("文档状态")),
    ),
)


def _field_value(spec: ModuleSpec, field_spec: FieldSpec, index: int,
                 built: dict[str, list[dict[str, Any]]]) -> Any:
    kind = field_spec.kind
    if kind == "code":
        return f"{field_spec.prefix}-{index:04d}"
    if kind == "text":
        return f"{spec.label}样例{index}"
    if kind == "date":
        return f"2026-09-{index:02d}"
    if kind == "int":
        return index * 10
    if kind == "float":
        return index * 12.5
    if kind == "ref":
        ref_rows = built.get(field_spec.ref_module, [])
        if index - 1 >= len(ref_rows):
            raise ValueError(
                f"模块 {spec.name} 字段「{field_spec.name}」引用 {field_spec.ref_module} "
                f"第 {index} 行，但被引用模块尚未生成"
            )
        return ref_rows[index - 1][field_spec.ref_field]
    if kind == "fixed":
        if len(field_spec.values) == 1:
            return field_spec.values[0]
        return field_spec.values[index - 1]
    raise ValueError(f"模块 {spec.name} 字段「{field_spec.name}」使用了未知类型：{kind}")


def build_seed_rows() -> dict[str, list[dict[str, Any]]]:
    """按规格确定性地生成全部示例数据；同样的规格永远生成同样的数据。"""
    built: dict[str, list[dict[str, Any]]] = {}
    for spec in MODULE_SPECS:
        rows: list[dict[str, Any]] = []
        for index in range(1, spec.rows + 1):
            row: dict[str, Any] = {
                "id": index,
                "status": spec.statuses[(index - 1) % len(spec.statuses)],
                "pending": ROW_PENDING[(index - 1) % len(ROW_PENDING)],
                "abnormal": ROW_ABNORMAL[(index - 1) % len(ROW_ABNORMAL)],
            }
            for field_spec in spec.fields:
                row[field_spec.name] = _field_value(spec, field_spec, index, built)
            rows.append(row)
        built[spec.name] = rows
    return built
