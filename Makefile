.PHONY: install backend frontend reseed check check-seed check-frontend build

install:
	cd backend && ./scripts/ensure_venv.sh
	cd frontend && npm ci

# 重新生成示例数据 app/seed.py（唯一入口，生成后自动校验）
reseed:
	cd backend && python3 scripts/regenerate_seed.py

# 启动检查：示例数据可重复生成，关键申诉字段（申诉编号、申诉单位、涉及报告、申诉内容）齐全
check-seed:
	cd backend && python3 -m app.seed_check

check-frontend:
	cd frontend && npm run typecheck

check: check-seed check-frontend

build: check
	cd frontend && npm run build

backend:
	cd backend && ./run.sh

frontend:
	cd frontend && npm run dev
