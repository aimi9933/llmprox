# IDE Python Proxy Server

一个智能的Python代理服务器，为IDE提供长代码上下文管理、语义分块和对话记忆功能，支持本地LLM集成。

## 核心功能

- 🧠 **智能语义分块**: 基于代码语义的智能分块算法
- 💭 **对话记忆管理**: 维护上下文相关的对话历史
- 🔗 **本地LLM集成**: 支持Ollama、LM Studio等本地LLM
- ⚡ **高性能API**: 基于FastAPI的异步API服务
- 📝 **代码补全**: 智能代码补全和建议
- 🐛 **调试辅助**: 代码错误分析和修复建议

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 配置本地LLM

1. 安装Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. 下载模型: `ollama pull codellama`
3. 配置环境变量或修改配置文件

## API文档

启动服务后访问 `http://localhost:8000/docs` 查看完整API文档。

## 项目结构

```
├── app/
│   ├── api/          # API路由
│   ├── core/         # 核心配置
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑
│   └── utils/        # 工具函数
├── tests/            # 测试用例
├── scripts/          # 部署脚本
└── docs/            # 文档
```

## 开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
pytest

# 代码格式化
black .
isort .

# 类型检查
mypy .
```