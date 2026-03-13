#!/usr/bin/env bash
set -euo pipefail

ENV_NAME=${1:-craw4jiucai}
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] conda 未找到，请先安装 Anaconda/Miniconda 并确保 conda 在 PATH 中。" >&2
  exit 1
fi

echo "[INFO] 使用 conda 环境: ${ENV_NAME}"

start_backend() {
  echo "[INFO] 启动后端: conda run -n ${ENV_NAME} python main.py --port 8208"
  conda run -n "${ENV_NAME}" python "${REPO_ROOT}/main.py" --port 8208
}

start_frontend() {
  cd "${REPO_ROOT}/frontend"
  if [ ! -d node_modules ]; then
    echo "[INFO] 检测到未安装前端依赖，正在执行 npm install..."
    npm install
  fi
  echo "[INFO] 启动前端: npm run dev (端口 3060)"
  npm run dev
}

start_backend &
backend_pid=$!

start_frontend &
frontend_pid=$!

cleanup() {
  echo "\n[INFO] 停止服务..."
  kill ${backend_pid} ${frontend_pid} 2>/dev/null || true
}

trap cleanup INT TERM EXIT

wait -n
cleanup
wait
