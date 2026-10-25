# =========================================================
# HZX 定时任务系统 —— 运行时镜像（FastAPI + APScheduler）
#
# 说明：
#   1. 前端产物需先在宿主机构建：cd frontend && npm run build
#      （Vite 输出到 backend/static，构建时打入镜像）
#   2. Python 依赖使用随包携带的离线 wheel（backend/wheels），
#      无需容器联网即可安装，适合内网 / 沙箱环境部署。
# =========================================================
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# ---------- Python 依赖（离线 wheel）----------
COPY backend/requirements.txt ./
COPY backend/wheels ./wheels
RUN pip install --no-index --find-links=./wheels -r requirements.txt \
    && rm -rf ./wheels

# ---------- 后端代码 ----------
COPY backend/app ./app

# ---------- 前端构建产物 ----------
COPY backend/static ./static

RUN mkdir -p /app/data

EXPOSE 6100

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:6100/api/health', timeout=4).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6100"]
