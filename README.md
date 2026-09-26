# 实验室样品检测管理平台

面向检测实验室的样品接收、检测任务分配、仪器校准、试剂耗材、结果报告与质量审核的综合管理后台。

这是一个前后端分离的管理平台：前端 Vue 3 + Vite + TypeScript，后端 FastAPI（Python）。
两边各自独立启动，前端 dev server 已关掉自动打开页面，启动后按终端打印的地址手工打开。

## 目录结构

```text
.
├── frontend/                 Vue 3 + Vite + TypeScript 前端
│   ├── src/views/            每个业务模块一个页面
│   ├── src/api/              统一请求封装
│   ├── src/stores/           会话与筛选状态
│   └── vite.config.ts        dev server 配置（open: false）
├── backend/                  FastAPI（Python） 后端
│   ├── app/routers/          每个业务模块一组接口
│   ├── app/services/         业务规则与状态流转
│   ├── app/seed_spec.py      示例数据规格（唯一事实来源，含申诉关键字段校验规则）
│   ├── app/seed_check.py     启动检查：校验 seed.py 与规格一致、关键字段齐全
│   ├── app/seed.py           示例数据（由规格生成，请勿手工编辑）
│   ├── scripts/              regenerate_seed.py 重新生成示例数据、ensure_venv.sh 修复虚拟环境
│   └── app/store.py          内存数据仓库
├── .gitignore
└── docker-compose.yml
```

## 启动

### 后端

```bash
cd backend
./run.sh   # 自动修复/创建 .venv、装依赖、做启动检查，然后起服务
```

`run.sh` 启动前会依次做两件事，任一失败都会停下来并打印原因：

1. **环境检查**：`.venv` 不存在或残留自其他环境（解释器跑不起来）时自动重建；
2. **示例数据检查**：`python3 -m app.seed_check`，确认 `app/seed.py` 与
   `app/seed_spec.py` 一致，且客户申诉的关键字段（申诉编号、申诉单位、
   涉及报告、申诉内容）全部通过校验。

服务启动时（FastAPI lifespan）还会再跑一次同样的检查，直接 `uvicorn` 启动也拦得住。

健康检查：`curl http://127.0.0.1:8000/api/health`（返回里的 `seed.checked` 为 `true`
表示启动检查已通过）

### 前端

```bash
cd frontend
npm ci
npm run dev
```

前端默认监听 `http://127.0.0.1:5173/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8000`。

## 示例数据与启动检查

示例数据只有一份事实来源：`backend/app/seed_spec.py`。`app/seed.py` 是由它生成的
产物，生成与校验共用同一套规则，不会出现"数据改了、检查没跟上"的残留状态。

常用命令（在仓库根目录执行）：

| 命令 | 作用 |
| --- | --- |
| `make reseed` | 按 `seed_spec.py` 重新生成 `app/seed.py`，生成后自动校验 |
| `make check-seed` | 只校验不写入：seed.py 是否与规格一致、申诉关键字段是否齐全 |
| `make check` | 后端示例数据检查 + 前端类型检查 |
| `make build` | `make check` 通过后构建前端产物 |

客户申诉的启动检查规则（在 `seed_spec.py` 的 `COMPLAIN_CHECKS` 里维护）：

- 申诉编号必须符合 `COMP-XXXX` 格式且不允许重复；
- 申诉单位不能为空；
- 涉及报告必须引用检测报告模块中真实存在的报告编号（如 `REPO-0001`）；
- 申诉内容不能为空且至少 10 个字符，需写清事实与诉求。

失败处理：校验失败会列出模块、行号与原因，例如
`模块 complain 第 2 行：涉及报告必须引用检测报告模块中存在的报告编号，「REPO-9999」在 report 模块中不存在`。
按提示修 `seed_spec.py`（不要手改 `seed.py`），执行 `make reseed` 后重新启动即可，
每次启动都会重新校验，修复前后状态一致。

## 业务模块

| 模块 | 目录 | 业务对象 | 主要字段 |
| --- | --- | --- | --- |
| 样品接收 | `sample` | 检测样品 | 样品编号、样品名称、委托单位 |
| 检测任务 | `task` | 检测任务单 | 任务编号、所属样品、检测项目 |
| 仪器管理 | `instrument` | 检测仪器 | 仪器编号、仪器名称、型号规格 |
| 校准记录 | `calibration` | 校准记录单 | 记录编号、仪器编号、校准机构 |
| 试剂耗材 | `reagent` | 试剂耗材 | 试剂编号、试剂名称、规格等级 |
| 检测结果 | `result` | 检测结果 | 结果编号、所属任务、检测项 |
| 检测报告 | `report` | 检测报告 | 报告编号、委托单位、样品名称 |
| 质量控制 | `qc` | 质控样品 | 质控编号、质控类别、标准值 |
| 偏离处理 | `deviation` | 偏离记录 | 偏离编号、偏离描述、涉及样品 |
| 样品留存 | `sample_storage` | 留存样品 | 留存编号、样品编号、留存位置 |
| 委托合同 | `contract` | 委托检验合同 | 合同编号、委托单位、联系人 |
| 检测人员 | `staff` | 检测员 | 员工编号、姓名、技术职称 |
| 检测方法 | `method` | 检测方法 | 方法编号、方法名称、适用标准 |
| 环境监测 | `environment` | 环境记录 | 记录编号、监测区域、温度值 |
| 客户申诉 | `complain` | 申诉记录 | 申诉编号、申诉单位、涉及报告 |
| 内审管理 | `audit` | 内审记录 | 内审编号、审核范围、审核组长 |
| 仪器维修 | `equipment_repair` | 维修记录 | 维修编号、仪器编号、故障描述 |
| 体系文档 | `document` | 体系文档 | 文档编号、文档名称、文档类型 |

## 约定

- 每个模块的前端页面在 `frontend/src/views/<模块>/index.vue`，后端接口在
  `backend/app/routers/<模块>.py`，业务规则在 `backend/app/services/<模块>.py`。
- 列表接口统一返回 `{ items, total, page, size }`，动作接口统一返回 `{ ok, message }`。
- 状态流转只允许在 `app/services` 里改，路由层不做业务判断。
- 示例数据只改 `app/seed_spec.py` 再 `make reseed`，不要手工编辑 `app/seed.py`。
