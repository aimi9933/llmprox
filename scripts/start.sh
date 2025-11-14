#!/bin/bash

# 启动IDE Python Proxy Server的便捷脚本

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行部署脚本:"
    echo "   ./scripts/deploy.sh"
    exit 1
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 检查Ollama服务
echo "🔍 检查Ollama服务..."
if ! ollama list &> /dev/null; then
    echo "⚠️  Ollama服务未运行，正在启动..."
    ollama serve &
    sleep 5
fi

# 启动服务器
echo "🚀 启动IDE Python Proxy Server..."
echo "📖 API文档: http://localhost:8000/docs"
echo "🏥 健康检查: http://localhost:8000/health"
echo "⏹️  按 Ctrl+C 停止服务"
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000