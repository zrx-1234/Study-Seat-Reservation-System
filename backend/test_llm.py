"""
测试OpenAI连接和LLM客户端

使用方法:
1. 复制 .env.example 为 .env
2. 填写你的 OPENAI_API_KEY
3. 运行: python test_llm.py
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from domain.ai.llm_client import create_llm_client, MockLLMClient, OpenAIClient


def test_mock_client():
    """测试Mock客户端"""
    print("=" * 60)
    print("测试 Mock LLM 客户端")
    print("=" * 60)

    client = MockLLMClient()

    # 测试聊天
    messages = [
        {"role": "user", "content": "今晚有空座吗？"}
    ]
    response = client.chat(messages)
    print(f"用户: {messages[0]['content']}")
    print(f"AI: {response}")
    print()

    # 测试意图识别
    intent = client.parse_intent("明天上午有靠窗的座位吗")
    print(f"意图识别: {intent}")
    print()


def test_openai_client():
    """测试OpenAI客户端"""
    print("=" * 60)
    print("测试 OpenAI 客户端")
    print("=" * 60)

    # 检查API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'sk-your-api-key-here':
        print("❌ 未配置 OPENAI_API_KEY")
        print("请在 .env 文件中设置正确的 API key")
        return

    try:
        client = OpenAIClient(api_key=api_key)

        # 测试聊天
        messages = [
            {"role": "user", "content": "你好，请用一句话介绍自己"}
        ]
        print(f"用户: {messages[0]['content']}")
        response = client.chat(messages, max_tokens=100)
        print(f"AI: {response}")
        print()

        # 测试意图识别
        print("测试意图识别...")
        intent = client.parse_intent("明天晚上有空座吗")
        print(f"意图识别结果: {intent}")
        print()

        print("✅ OpenAI 连接成功！")

    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请安装: pip install openai")
    except Exception as e:
        print(f"❌ OpenAI API 调用失败: {e}")


def test_factory():
    """测试工厂函数"""
    print("=" * 60)
    print("测试工厂函数")
    print("=" * 60)

    # 测试根据环境变量创建客户端
    provider = os.getenv('LLM_PROVIDER', 'mock')
    print(f"当前 LLM_PROVIDER: {provider}")

    client = create_llm_client(provider)
    print(f"创建的客户端类型: {type(client).__name__}")
    print()


if __name__ == '__main__':
    # 尝试加载 .env 文件
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 已加载 .env 文件")
    except ImportError:
        print("⚠️  未安装 python-dotenv，将使用系统环境变量")
        print("建议安装: pip install python-dotenv")

    print()

    # 运行测试
    test_mock_client()
    test_factory()

    # 只有配置了OpenAI才测试
    if os.getenv('LLM_PROVIDER') == 'openai':
        test_openai_client()
    else:
        print("=" * 60)
        print("提示: 要测试 OpenAI，请在 .env 中设置:")
        print("  LLM_PROVIDER=openai")
        print("  OPENAI_API_KEY=sk-your-key")
        print("=" * 60)
