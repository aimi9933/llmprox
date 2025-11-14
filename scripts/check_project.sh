#!/bin/bash

# 快速测试脚本 - 验证项目结构

echo "🔍 检查项目结构..."

# 检查主要文件
files_to_check=(
    "app/main.py"
    "app/core/config.py"
    "app/models/schemas.py"
    "app/services/chunker.py"
    "app/services/llm_client.py"
    "app/services/context_manager.py"
    "app/api/code.py"
    "app/api/chat.py"
    "app/api/health.py"
    "requirements.txt"
    "README.md"
    "scripts/deploy.sh"
    "scripts/start.sh"
    "tests/test_main.py"
    "examples/client_example.py"
    "docs/api.md"
    ".env.example"
    ".gitignore"
)

missing_files=()
for file in "${files_to_check[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✅ 所有核心文件都存在"
else
    echo "❌ 缺少以下文件:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
fi

# 检查目录结构
echo ""
echo "📁 检查目录结构..."
directories_to_check=(
    "app"
    "app/core"
    "app/models"
    "app/services"
    "app/api"
    "tests"
    "scripts"
    "examples"
    "docs"
)

for dir in "${directories_to_check[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/"
    else
        echo "❌ $dir/ (缺失)"
    fi
done

# 统计代码行数
echo ""
echo "📊 代码统计..."
python_files=$(find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" | wc -l)
total_lines=$(find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" -exec wc -l {} + | tail -1 | awk '{print $1}')

echo "Python文件数量: $python_files"
echo "总代码行数: $total_lines"

# 检查脚本权限
echo ""
echo "🔐 检查脚本权限..."
if [ -x "scripts/deploy.sh" ]; then
    echo "✅ deploy.sh 可执行"
else
    echo "❌ deploy.sh 不可执行"
fi

if [ -x "scripts/start.sh" ]; then
    echo "✅ start.sh 可执行"
else
    echo "❌ start.sh 不可执行"
fi

echo ""
echo "🎉 项目结构检查完成！"
echo ""
echo "📋 下一步操作:"
echo "1. 运行部署脚本: ./scripts/deploy.sh"
echo "2. 启动服务: ./scripts/start.sh"
echo "3. 访问API文档: http://localhost:8000/docs"
echo "4. 运行示例: python examples/client_example.py"