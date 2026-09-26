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
│   ├── app/seed.py           示例数据生成规格（确定性生成）
│   ├── app/seed_check.py     示例数据启动校验
│   └── app/store.py          内存数据仓库（启动时先校验再装载）
├── .gitignore
└── docker-compose.yml
```

## 启动

### 本地开发（推荐）

```bash
make install    # 安装前后端依赖；虚拟环境损坏会自动重建
make check      # 校验示例数据（重点：客户申诉的申诉编号、申诉单位、涉及报告、申诉内容）
make backend    # 启动后端，启动前自动校验示例数据
make frontend   # 启动前端 dev server
```

其他常用目标：`make seed`（重新生成示例数据并验证两次生成一致）、
`make build`（前端生产构建）、`make clean`（清理 .venv、node_modules 等本地残留）。

### 后端

```bash
cd backend
./run.sh        # 自动准备 .venv、按 requirements.txt 装依赖、校验示例数据后再启动
```

`run.sh` 的行为约定：

- `.venv` 缺失或损坏（比如从别的机器拷贝过来的残留）时自动重建；
- `requirements.txt` 没变化就跳过依赖安装，变化了才重新安装；
- 启动前执行 `python -m app.seed_check` 校验示例数据，失败会逐条打印原因
  并以非零码退出，不会带着坏数据起服务；修复后重新执行 `./run.sh` 即可。

健康检查：`curl http://127.0.0.1:8000/api/health`

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认监听 `http://127.0.0.1:5173/`，dev server 不会自动打开浏览器，
需要自己访问。`/api` 由 vite 代理到后端 `http://127.0.0.1:8000`。

## 示例数据

示例数据由 `backend/app/seed.py` 中的 `MODULE_SPECS` 规格表**确定性生成**：
同样的规格在任何机器、任何时间生成的结果完全一致，每次启动都重新生成，
运行期的改动不会残留到下一次启动。

- 改数据只改 `MODULE_SPECS`，不要手工编辑生成结果；
- `python -m app.seed --verify` 验证重复生成结果一致；
- `python -m app.seed_check`（或 `make check`）校验数据，客户申诉模块会
  专项检查申诉编号（`COMP-四位数字` 且不重复）、申诉单位、涉及报告、申诉内容；
- 校验失败会打印具体模块、行号、字段和原因，修复后重启即恢复一致。

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
