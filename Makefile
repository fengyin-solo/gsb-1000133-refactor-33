.PHONY: install seed check backend frontend build clean

install: ## 安装前后端依赖（虚拟环境损坏会自动重建）
	cd backend && ./run.sh --deps-only
	cd frontend && npm install

seed: ## 重新生成示例数据并验证两次生成结果一致
	cd backend && .venv/bin/python -m app.seed --verify

check: ## 校验示例数据（重点：客户申诉的申诉编号、申诉单位、涉及报告、申诉内容）
	cd backend && .venv/bin/python -m app.seed_check

backend: ## 启动后端（启动前自动校验示例数据，失败会打印原因）
	cd backend && ./run.sh

frontend: ## 启动前端 dev server
	cd frontend && npm run dev

build: ## 前端生产构建（含类型检查）
	cd frontend && npm run build

clean: ## 清理本地环境残留（虚拟环境、node_modules、构建产物）
	rm -rf backend/.venv frontend/node_modules frontend/dist
