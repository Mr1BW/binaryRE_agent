#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

# 清理旧进程
kill -9 $(lsof -ti:7860) 2>/dev/null || true
kill -9 $(lsof -ti:5173) 2>/dev/null || true
sleep 1

echo "=== 启动后端 (API :7860) ==="
cd "$DIR"
source venv/bin/activate
nohup python run.py --api-only > app.log 2>&1 &
BACKEND_PID=$!

echo "=== 启动前端 (Vite :5173) ==="
cd "$DIR/frontend"
nohup npx vite --port 5173 > ../frontend-dev.log 2>&1 &
FRONTEND_PID=$!

sleep 5

# 验证
BACKEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:7860 2>/dev/null || echo "000")
FRONTEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>/dev/null || echo "000")

if [ "$BACKEND_OK" = "200" ] && [ "$FRONTEND_OK" = "200" ]; then
    echo ""
    echo "✓ 后端运行中: http://localhost:7860 (PID $BACKEND_PID)"
    echo "✓ 前端运行中: http://localhost:5173 (PID $FRONTEND_PID)"
    echo ""
    echo "浏览器打开: http://localhost:5173"
    echo "停止命令:   kill $BACKEND_PID $FRONTEND_PID"
else
    echo "✗ 启动失败"
    echo "后端日志: tail $DIR/app.log"
    echo "前端日志: tail $DIR/frontend-dev.log"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi
