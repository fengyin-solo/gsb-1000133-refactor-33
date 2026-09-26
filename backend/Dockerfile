FROM python:3.12-slim
WORKDIR /srv/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# 构建期启动检查：示例数据与规格不一致时直接构建失败，不带残留状态出镜像
RUN python -m app.seed_check
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
