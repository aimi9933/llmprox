import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.services.chunker import SemanticChunker
from app.services.context_manager import context_manager
from app.models.schemas import CompletionRequest, DebugRequest


client = TestClient(app)


class TestCodeAPI:
    """代码API测试"""
    
    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "llm_status" in data
    
    def test_get_config(self):
        """测试获取配置"""
        response = client.get("/health/config")
        assert response.status_code == 200
        data = response.json()
        assert "api_version" in data
        assert "llm_provider" in data
    
    def test_context_analysis(self):
        """测试上下文分析"""
        request_data = {
            "code": "def hello_world():\n    print('Hello, World!')\n    return True",
            "file_path": "test.py",
            "language": "python",
            "max_chunks": 5
        }
        
        response = client.post("/code/context", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "total_tokens" in data
        assert "processing_time_ms" in data
    
    def test_code_completion(self):
        """测试代码补全"""
        request_data = {
            "code": "def calculate_sum(a, b):\n    ",
            "file_path": "test.py",
            "cursor_position": 28,
            "language": "python",
            "max_tokens": 100
        }
        
        response = client.post("/code/complete", json=request_data)
        # 注意：这个测试可能需要LLM服务运行
        if response.status_code == 200:
            data = response.json()
            assert "suggestions" in data
            assert "session_id" in data
        else:
            # 如果LLM服务不可用，应该返回500错误
            assert response.status_code in [500, 503]
    
    def test_debug_analysis(self):
        """测试调试分析"""
        request_data = {
            "code": "def divide(a, b):\n    return a / b",
            "file_path": "test.py",
            "error_message": "ZeroDivisionError: division by zero",
            "language": "python"
        }
        
        response = client.post("/code/debug", json=request_data)
        # 注意：这个测试可能需要LLM服务运行
        if response.status_code == 200:
            data = response.json()
            assert "analysis" in data
            assert "suggestions" in data
        else:
            assert response.status_code in [500, 503]


class TestChatAPI:
    """聊天API测试"""
    
    def test_chat_message(self):
        """测试聊天消息"""
        request_data = {
            "message": "What is Python?",
            "context_code": "print('Hello, World!')",
            "file_path": "test.py",
            "language": "python"
        }
        
        response = client.post("/chat/message", json=request_data)
        # 注意：这个测试可能需要LLM服务运行
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "session_id" in data
        else:
            assert response.status_code in [500, 503]
    
    def test_get_chat_history(self):
        """测试获取聊天历史"""
        session_id = "test-session-123"
        response = client.get(f"/chat/history/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "session_id" in data
    
    def test_list_sessions(self):
        """测试列出会话"""
        response = client.get("/chat/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data


class TestSemanticChunker:
    """语义分块器测试"""
    
    def setup_method(self):
        self.chunker = SemanticChunker()
    
    def test_count_tokens(self):
        """测试token计数"""
        text = "Hello, world! This is a test."
        token_count = self.chunker.count_tokens(text)
        assert token_count > 0
        assert isinstance(token_count, int)
    
    def test_chunk_python_code(self):
        """测试Python代码分块"""
        code = '''
def function1():
    """First function"""
    return "hello"

class MyClass:
    def method1(self):
        return True
    
    def method2(self):
        return False

def function2():
    """Second function"""
    pass
'''
        
        chunks = self.chunker.chunk_code(code, "test.py", "python")
        assert len(chunks) > 0
        
        # 检查每个块的基本属性
        for chunk in chunks:
            assert chunk.id
            assert chunk.content
            assert chunk.file_path == "test.py"
            assert chunk.language == "python"
            assert chunk.token_count > 0
            assert chunk.start_line >= 0
            assert chunk.end_line >= chunk.start_line
    
    def test_chunk_javascript_code(self):
        """测试JavaScript代码分块"""
        code = '''
function function1() {
    return "hello";
}

class MyClass {
    method1() {
        return true;
    }
    
    method2() {
        return false;
    }
}

function function2() {
    return null;
}
'''
        
        chunks = self.chunker.chunk_code(code, "test.js", "javascript")
        assert len(chunks) > 0
        
        for chunk in chunks:
            assert chunk.language == "javascript"
            assert chunk.token_count > 0


class TestContextManager:
    """上下文管理器测试"""
    
    @pytest.mark.asyncio
    async def test_dialog_session_creation(self):
        """测试对话会话创建"""
        session_id = context_manager.dialog_memory.get_or_create_session()
        assert session_id
        assert session_id in context_manager.dialog_memory.sessions
        
        # 测试获取现有会话
        same_session_id = context_manager.dialog_memory.get_or_create_session(session_id)
        assert same_session_id == session_id
    
    @pytest.mark.asyncio
    async def test_add_dialog_message(self):
        """测试添加对话消息"""
        from app.models.schemas import DialogMessage
        from datetime import datetime
        
        session_id = context_manager.dialog_memory.get_or_create_session()
        
        message = DialogMessage(
            id="test-message-1",
            role="user",
            content="Hello, how are you?",
            timestamp=datetime.now(),
            session_id=session_id
        )
        
        await context_manager.dialog_memory.add_message(message)
        
        # 验证消息已添加
        messages = context_manager.dialog_memory.sessions[session_id]
        assert len(messages) == 1
        assert messages[0].content == "Hello, how are you?"
    
    @pytest.mark.asyncio
    async def test_embedding_service(self):
        """测试嵌入服务"""
        text1 = "Python is a programming language"
        text2 = "JavaScript is also a programming language"
        text3 = "The weather is nice today"
        
        # 相似文本应该有较高的相似度
        similarity1 = await context_manager.embedding_service.compute_similarity(text1, text2)
        
        # 不相关文本应该有较低的相似度
        similarity2 = await context_manager.embedding_service.compute_similarity(text1, text3)
        
        assert similarity1 > similarity2
        assert 0 <= similarity1 <= 1
        assert 0 <= similarity2 <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])