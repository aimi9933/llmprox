# IDE Python Proxy Server API 文档

## 概述

IDE Python Proxy Server 是一个智能的代理服务器，为IDE提供代码补全、调试分析和对话记忆功能。通过语义分块和本地LLM集成，实现智能的代码上下文管理。

## 核心功能

- 🔍 **智能语义分块**: 基于代码语义的智能分块算法
- 🧠 **对话记忆管理**: 维护上下文相关的对话历史
- ⚡ **高性能API**: 基于FastAPI的异步API服务
- 🔗 **本地LLM集成**: 支持Ollama、LM Studio等本地LLM
- 📝 **代码补全**: 智能代码补全和建议
- 🐛 **调试辅助**: 代码错误分析和修复建议

## API 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: `v1`
- **认证**: 目前不需要认证（生产环境建议添加）

## API 端点

### 1. 健康检查和配置

#### GET `/health/`
健康检查接口

**响应示例**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "llm_provider": "ollama",
  "llm_status": "connected",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/health/models`
获取可用的LLM模型列表

**响应示例**:
```json
{
  "provider": "ollama",
  "models": ["codellama", "llama2", "mistral"],
  "default_model": "codellama"
}
```

#### GET `/health/config`
获取服务配置信息

**响应示例**:
```json
{
  "api_version": "1.0.0",
  "llm_provider": "ollama",
  "default_model": "codellama",
  "max_context_length": 8000,
  "max_chunk_size": 2000,
  "similarity_threshold": 0.7,
  "supported_extensions": [".py", ".js", ".ts", ".java"]
}
```

### 2. 代码分析

#### POST `/code/context`
分析代码并返回语义分块

**请求体**:
```json
{
  "code": "def hello():\n    print('Hello')",
  "file_path": "test.py",
  "language": "python",
  "max_chunks": 5
}
```

**响应示例**:
```json
{
  "chunks": [
    {
      "id": "abc123",
      "content": "def hello():\n    print('Hello')",
      "file_path": "test.py",
      "start_line": 1,
      "end_line": 2,
      "language": "python",
      "token_count": 10,
      "metadata": {
        "line_count": 2,
        "char_count": 25
      }
    }
  ],
  "total_tokens": 10,
  "processing_time_ms": 15.5
}
```

#### POST `/code/complete`
代码补全

**请求体**:
```json
{
  "code": "def calculate_sum(a, b):\n    ",
  "file_path": "utils.py",
  "cursor_position": 28,
  "language": "python",
  "context_window": 4000,
  "session_id": "optional-session-id",
  "max_tokens": 256,
  "temperature": 0.7
}
```

**响应示例**:
```json
{
  "suggestions": [
    "return a + b",
    "result = a + b\n    return result",
    "total = a + b\n    return total"
  ],
  "confidence_scores": [0.9, 0.8, 0.7],
  "context_chunks": [...],
  "session_id": "session-123",
  "response_time_ms": 250.5
}
```

#### POST `/code/debug`
代码调试分析

**请求体**:
```json
{
  "code": "def divide(a, b):\n    return a / b",
  "file_path": "math.py",
  "error_message": "ZeroDivisionError: division by zero",
  "language": "python",
  "session_id": "optional-session-id"
}
```

**响应示例**:
```json
{
  "analysis": "函数没有处理除零错误的情况...",
  "suggestions": [
    "添加除零检查",
    "使用try-except处理异常",
    "添加参数验证"
  ],
  "fixed_code": "def divide(a, b):\n    if b == 0:\n        raise ValueError('除数不能为零')\n    return a / b",
  "context_chunks": [...],
  "session_id": "session-123",
  "response_time_ms": 450.2
}
```

### 3. 聊天对话

#### POST `/chat/message`
发送聊天消息

**请求体**:
```json
{
  "message": "如何优化这个函数的性能？",
  "session_id": "optional-session-id",
  "context_code": "def slow_function():\n    # 代码内容",
  "file_path": "utils.py",
  "language": "python"
}
```

**响应示例**:
```json
{
  "response": "这个函数可以通过以下方式优化...",
  "session_id": "session-123",
  "context_chunks": [...],
  "response_time_ms": 320.1
}
```

#### GET `/chat/history/{session_id}`
获取聊天历史

**响应示例**:
```json
{
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "如何优化这个函数？",
      "timestamp": "2024-01-01T12:00:00Z",
      "context_chunks": ["chunk-1", "chunk-2"]
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "你可以通过以下方式优化...",
      "timestamp": "2024-01-01T12:00:05Z",
      "context_chunks": ["chunk-1", "chunk-2"]
    }
  ],
  "session_id": "session-123",
  "total_messages": 2
}
```

#### GET `/chat/sessions`
列出所有会话

**响应示例**:
```json
{
  "sessions": [
    {
      "session_id": "session-123",
      "message_count": 5,
      "last_activity": "2024-01-01T12:30:00Z",
      "roles": ["user", "assistant"]
    }
  ]
}
```

#### DELETE `/chat/session/{session_id}`
清除会话

**响应示例**:
```json
{
  "message": "Session cleared",
  "session_id": "session-123"
}
```

## 配置选项

服务器可以通过环境变量或`.env`文件配置：

```bash
# API设置
API_HOST=0.0.0.0
API_PORT=8000

# LLM设置
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=codellama

# 上下文管理
MAX_CONTEXT_LENGTH=8000
CHUNK_OVERLAP_RATIO=0.1
MAX_CHUNK_SIZE=2000

# 语义分块
EMBEDDING_MODEL=all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.7

# 对话记忆
MAX_DIALOG_HISTORY=20
MEMORY_TTL=3600
```

## 错误处理

API使用标准HTTP状态码：

- `200`: 成功
- `400`: 请求参数错误
- `500`: 服务器内部错误
- `503`: 服务不可用（如LLM服务未启动）

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

## 使用示例

### Python客户端示例

```python
import requests

# 代码补全
response = requests.post("http://localhost:8000/code/complete", json={
    "code": "def hello():\n    ",
    "file_path": "test.py",
    "cursor_position": 18,
    "language": "python"
})

if response.status_code == 200:
    data = response.json()
    for suggestion in data['suggestions']:
        print(suggestion)
```

### JavaScript客户端示例

```javascript
// 调试分析
const response = await fetch('http://localhost:8000/code/debug', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        code: 'function divide(a, b) { return a / b; }',
        file_path: 'utils.js',
        error_message: 'Cannot divide by zero',
        language: 'javascript'
    })
});

const data = await response.json();
console.log(data.analysis);
```

## 部署指南

### 快速部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd ide-python-proxy

# 2. 运行部署脚本
./scripts/deploy.sh

# 3. 启动服务
./scripts/start.sh
```

### 手动部署

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 4. 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 性能优化建议

1. **LLM配置**: 使用本地高性能LLM模型
2. **缓存策略**: 启用嵌入向量缓存
3. **并发处理**: 利用异步处理提高并发性能
4. **资源限制**: 合理设置上下文长度和分块大小

## 故障排除

### 常见问题

1. **LLM服务连接失败**
   - 检查Ollama是否安装和运行
   - 确认模型是否已下载

2. **内存使用过高**
   - 减少max_context_length
   - 调整chunk_overlap_ratio

3. **响应速度慢**
   - 使用更快的LLM模型
   - 启用嵌入缓存
   - 减少max_chunks_per_request

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看Ollama日志
journalctl -u ollama -f
```