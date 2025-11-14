"""
IDE Python Proxy Server 使用示例

这个文件展示了如何使用IDE Python Proxy Server的各种功能。
"""

import requests
import json
import time

# 服务器基础URL
BASE_URL = "http://localhost:8000"


def test_health_check():
    """测试健康检查"""
    print("🏥 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def test_get_models():
    """测试获取可用模型"""
    print("🧠 测试获取可用模型...")
    response = requests.get(f"{BASE_URL}/health/models")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def test_code_completion():
    """测试代码补全"""
    print("✍️ 测试代码补全...")
    
    request_data = {
        "code": "def calculate_average(numbers):\n    total = sum(numbers)\n    count = len(numbers)\n    ",
        "file_path": "utils.py",
        "cursor_position": 70,
        "language": "python",
        "max_tokens": 128,
        "temperature": 0.7
    }
    
    response = requests.post(f"{BASE_URL}/code/complete", json=request_data)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"会话ID: {data['session_id']}")
        print(f"响应时间: {data['response_time_ms']:.2f}ms")
        print("补全建议:")
        for i, (suggestion, confidence) in enumerate(zip(data['suggestions'], data['confidence_scores'])):
            print(f"  {i+1}. (置信度: {confidence:.2f}) {suggestion}")
        print(f"上下文块数量: {len(data['context_chunks'])}")
    else:
        print(f"错误: {response.text}")
    print()


def test_debug_analysis():
    """测试调试分析"""
    print("🐛 测试调试分析...")
    
    request_data = {
        "code": '''
def divide_numbers(a, b):
    result = a / b
    return result

# 测试调用
print(divide_numbers(10, 0))  # 这里会出错
''',
        "file_path": "math_utils.py",
        "error_message": "ZeroDivisionError: division by zero",
        "language": "python"
    }
    
    response = requests.post(f"{BASE_URL}/code/debug", json=request_data)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"会话ID: {data['session_id']}")
        print(f"响应时间: {data['response_time_ms']:.2f}ms")
        print("分析结果:")
        print(data['analysis'])
        print("\n修复建议:")
        for i, suggestion in enumerate(data['suggestions']):
            print(f"  {i+1}. {suggestion}")
        if data['fixed_code']:
            print("\n修复后的代码:")
            print(data['fixed_code'])
    else:
        print(f"错误: {response.text}")
    print()


def test_context_analysis():
    """测试上下文分析"""
    print("📝 测试上下文分析...")
    
    request_data = {
        "code": '''
import requests
import json

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

# 使用示例
client = APIClient("https://api.example.com")
data = client.get("/users")
''',
        "file_path": "api_client.py",
        "language": "python",
        "max_chunks": 5
    }
    
    response = requests.post(f"{BASE_URL}/code/context", json=request_data)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"处理时间: {data['processing_time_ms']:.2f}ms")
        print(f"总Token数: {data['total_tokens']}")
        print(f"代码块数量: {len(data['chunks'])}")
        
        for i, chunk in enumerate(data['chunks']):
            print(f"\n代码块 {i+1}:")
            print(f"  ID: {chunk['id']}")
            print(f"  行号: {chunk['start_line']}-{chunk['end_line']}")
            print(f"  Token数: {chunk['token_count']}")
            print(f"  内容预览: {chunk['content'][:100]}...")
    else:
        print(f"错误: {response.text}")
    print()


def test_chat_interaction():
    """测试聊天交互"""
    print("💬 测试聊天交互...")
    
    # 第一次对话
    request_data = {
        "message": "如何优化这个Python函数的性能？",
        "context_code": '''
def find_duplicates(items):
    duplicates = []
    for i, item1 in enumerate(items):
        for j, item2 in enumerate(items):
            if i != j and item1 == item2:
                if item1 not in duplicates:
                    duplicates.append(item1)
    return duplicates
''',
        "file_path": "utils.py",
        "language": "python"
    }
    
    response = requests.post(f"{BASE_URL}/chat/message", json=request_data)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        session_id = data['session_id']
        print(f"会话ID: {session_id}")
        print(f"响应时间: {data['response_time_ms']:.2f}ms")
        print("AI回复:")
        print(data['response'])
        
        # 继续对话
        print("\n" + "="*50)
        print("继续对话...")
        
        follow_up_data = {
            "message": "能给我一个具体的优化代码示例吗？",
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/chat/message", json=follow_up_data)
        if response.status_code == 200:
            data = response.json()
            print("AI回复:")
            print(data['response'])
        
        # 获取对话历史
        print("\n" + "="*50)
        print("获取对话历史...")
        history_response = requests.get(f"{BASE_URL}/chat/history/{session_id}")
        if history_response.status_code == 200:
            history_data = history_response.json()
            print(f"消息总数: {history_data['total_messages']}")
            for msg in history_data['messages']:
                print(f"{msg['role']}: {msg['content'][:100]}...")
    else:
        print(f"错误: {response.text}")
    print()


def main():
    """主函数"""
    print("🚀 IDE Python Proxy Server 使用示例")
    print("="*60)
    
    try:
        # 基础功能测试
        test_health_check()
        test_get_models()
        
        # 代码功能测试
        test_context_analysis()
        test_code_completion()
        test_debug_analysis()
        
        # 聊天功能测试
        test_chat_interaction()
        
        print("✅ 所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行:")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")


if __name__ == "__main__":
    main()