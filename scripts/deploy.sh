#!/bin/bash

# IDE Python Proxy Server 一键部署脚本

set -e

echo "🚀 开始部署 IDE Python Proxy Server..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 错误: 需要 Python 3.8 或更高版本，当前版本: $python_version"
    exit 1
fi

echo "✅ Python 版本检查通过: $python_version"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📚 安装依赖包..."
pip install -r requirements.txt

# 检查Ollama是否安装
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama 未安装，正在安装..."
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # 等待Ollama启动
    echo "⏳ 等待Ollama服务启动..."
    sleep 5
else
    echo "✅ Ollama 已安装"
fi

# 检查Ollama服务状态
echo "🔍 检查Ollama服务状态..."
if ! ollama list &> /dev/null; then
    echo "⚠️  Ollama服务未运行，正在启动..."
    # 尝试启动Ollama服务
    if command -v systemctl &> /dev/null; then
        sudo systemctl start ollama 2>/dev/null || echo "请手动启动Ollama服务"
    else
        echo "请手动启动Ollama服务: ollama serve"
    fi
    sleep 3
fi

# 下载默认模型
echo "🧠 下载CodeLlama模型..."
if ! ollama list | grep -q "codellama"; then
    ollama pull codellama
else
    echo "✅ CodeLlama模型已存在"
fi

# 创建配置文件
if [ ! -f ".env" ]; then
    echo "⚙️ 创建配置文件..."
    cp .env.example .env
    echo "✅ 已创建 .env 配置文件，请根据需要修改配置"
fi

# 创建日志目录
mkdir -p logs

echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 使用说明:"
echo "1. 启动服务:"
echo "   source venv/bin/activate"
echo "   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. 访问API文档:"
echo "   http://localhost:8000/docs"
echo ""
echo "3. 健康检查:"
echo "   curl http://localhost:8000/health"
echo ""
echo "4. 测试代码补全:"
echo "   curl -X POST http://localhost:8000/code/complete \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"code\":\"def hello():\\n    \", \"file_path\":\"test.py\", \"cursor_position\":15, \"language\":\"python\"}'"
echo ""
echo "🐛 如有问题，请检查:"
echo "- Ollama服务是否运行: ollama list"
echo "- 端口8000是否被占用"
echo "- Python虚拟环境是否正确激活"
echo ""