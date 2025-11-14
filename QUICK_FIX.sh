#!/bin/bash

# 修复 pydantic-settings 依赖问题的快速脚本
# 适用于 /root/llmprox 目录

set -e

echo "🔧 修复 pydantic-settings 依赖问题..."

# 切换到项目目录
cd /root/llmprox

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行:"
    echo "   ./scripts/deploy.sh"
    exit 1
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 安装 pydantic-settings
echo "📦 安装 pydantic-settings..."
pip install pydantic-settings==2.1.0

# 验证安装
echo "🔍 验证安装..."
python -c "from app.core.config import settings; print('✅ pydantic-settings 安装成功!')"

echo ""
echo "🎉 修复完成!"
echo "现在可以运行: ./scripts/start.sh"