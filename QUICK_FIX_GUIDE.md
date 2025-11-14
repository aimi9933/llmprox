# 快速修复指南：pydantic-settings 依赖问题

## 问题
运行 `./scripts/start.sh` 时出现 `ModuleNotFoundError: No module named 'pydantic_settings'` 错误。

## 原因
项目使用 Pydantic v2.5.0，但缺少 `pydantic-settings` 包。

## 快速修复方法

### 方法一：运行修复脚本（推荐）
```bash
# 将以下脚本保存到 /root/llmprox/ 目录并执行
chmod +x fix_pydantic_settings.sh
./fix_pydantic_settings.sh
```

### 方法二：手动修复
```bash
cd /root/llmprox
source venv/bin/activate
pip install pydantic-settings==2.1.0
```

### 方法三：更新 requirements.txt 并重新安装
1. 编辑 `/root/llmprox/requirements.txt`，在第4行后添加：
   ```
   pydantic-settings==2.1.0
   ```

2. 重新安装依赖：
   ```bash
   cd /root/llmprox
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 验证修复
```bash
source venv/bin/activate
python -c "from app.core.config import settings; print('Import successful')"
```

## llama.cpp 配置
由于您使用 llama.cpp，请确保：

1. llama.cpp 服务运行在 `http://localhost:8080`
2. 创建 `.env` 文件（如果不存在）：
   ```bash
   cp .env.example .env
   ```

3. 编辑 `.env` 文件，设置：
   ```
   LLM_PROVIDER=llama_cpp
   LLAMA_CPP_BASE_URL=http://localhost:8080
   DEFAULT_MODEL=your_model_name
   ```

## 启动服务
```bash
./scripts/start.sh
```

## 访问服务
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health