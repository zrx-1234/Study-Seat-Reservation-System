"""
MOD-AI: 智能助手模块 - 大语言模型客户端

实现策略：
1. 抽象基类 LLMClient - 定义统一接口
2. MockLLMClient - 测试用，无需真实API
3. OpenAIClient - 接入OpenAI API（可选）
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os
import json


# ============================================================================
# 抽象基类
# ============================================================================

class LLMClient(ABC):
    """大语言模型客户端抽象基类"""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        聊天接口

        Args:
            messages: 消息列表，格式 [{"role": "user|assistant", "content": "..."}]
            **kwargs: 额外参数（temperature, max_tokens等）

        Returns:
            str: LLM生成的回复文本
        """
        pass

    @abstractmethod
    def parse_intent(self, user_message: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        使用LLM进行意图识别

        Args:
            user_message: 用户输入消息
            context: 上下文消息列表（可选）

        Returns:
            dict: {"intent": "...", "confidence": 0.9, "slots": {...}}
        """
        pass


# ============================================================================
# Mock实现 - 用于开发测试
# ============================================================================

class MockLLMClient(LLMClient):
    """Mock LLM客户端 - 不调用真实API，返回预设响应"""

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """返回固定的Mock响应"""
        last_message = messages[-1]['content'] if messages else ""

        # 简单的规则响应
        if '座位' in last_message or '空座' in last_message:
            return "根据当前情况，理科图书馆301有12个可用座位，推荐靠窗的A01座位。"
        elif '预约' in last_message and '我的' in last_message:
            return "您当前有1个进行中的预约：明天下午2点，理科图书馆301，座位A05。"
        elif '通知' in last_message:
            return "您有2条未读通知，最新的是预约提醒。"
        else:
            return "我是自习室预约助手，可以帮您查询空座位、管理预约。有什么需要帮助的吗？"

    def parse_intent(self, user_message: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Mock意图识别 - 返回预设意图"""
        message_lower = user_message.lower()

        # 简单关键词匹配
        if any(kw in message_lower for kw in ['座位', '空座', '位置', '自习室']):
            return {
                'intent': 'query_empty_seat',
                'confidence': 0.9,
                'slots': {'date': 'today'}
            }
        elif '我的' in message_lower and '预约' in message_lower:
            return {
                'intent': 'query_my_reservation',
                'confidence': 0.95,
                'slots': {}
            }
        elif '通知' in message_lower:
            return {
                'intent': 'query_notification',
                'confidence': 0.9,
                'slots': {}
            }
        else:
            return {
                'intent': 'chitchat',
                'confidence': 0.6,
                'slots': {}
            }


# ============================================================================
# OpenAI实现（可选）
# ============================================================================

class OpenAIClient(LLMClient):
    """OpenAI API客户端"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化OpenAI客户端

        Args:
            api_key: API密钥，如不提供则从环境变量读取
            model: 模型名称，如不提供则从环境变量读取
        """
        self.api_key = (api_key or os.getenv('OPENAI_API_KEY') or '').strip()
        self.model = (model or os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')).strip()
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1').strip()

        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        调用OpenAI Chat API

        实现了自动重试机制：
        - 最多重试3次
        - 指数退避策略
        - 超时处理

        TODO: 添加更完善的Token限制和速率限制
        """
        import time

        max_retries = 3
        retry_delay = 1  # 初始延迟1秒

        for attempt in range(max_retries):
            try:
                import openai

                client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', 500),
                    timeout=kwargs.get('timeout', 30)  # 30秒超时
                )

                if not response.choices:
                    raise Exception("OpenAI API returned empty choices")

                content = response.choices[0].message.content
                if not content:
                    raise Exception("OpenAI API returned empty response")

                return content

            except ImportError:
                # 缺少依赖包，不重试
                raise ImportError("openai package not installed. Run: pip install openai")

            except Exception as e:
                error_msg = str(e)

                # 最后一次尝试，不再重试
                if attempt == max_retries - 1:
                    raise Exception(f"OpenAI API call failed after {max_retries} attempts: {error_msg}")

                # 判断是否应该重试
                should_retry = False

                # 网络错误、超时、服务器错误 - 应该重试
                if any(keyword in error_msg.lower() for keyword in
                       ['timeout', 'connection', 'network', '500', '502', '503', '504']):
                    should_retry = True

                # 速率限制 - 应该重试
                if 'rate limit' in error_msg.lower() or '429' in error_msg:
                    should_retry = True
                    retry_delay = 5  # 速率限制延迟更长

                # 认证错误、无效请求 - 不重试
                if any(keyword in error_msg.lower() for keyword in
                       ['authentication', 'invalid', 'api key', '401', '400']):
                    should_retry = False
                    raise Exception(f"OpenAI API call failed: {error_msg}")

                if should_retry:
                    print(f"OpenAI API调用失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                    print(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    raise Exception(f"OpenAI API call failed: {error_msg}")

    def parse_intent(self, user_message: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        使用OpenAI进行意图识别

        优化的Prompt设计：
        1. 明确的角色定义
        2. 详细的意图说明和示例
        3. 结构化的JSON输出格式
        4. Few-shot learning示例
        """

        # 构建系统提示词
        system_prompt = """你是一个自习座位预约系统的意图分类助手。你的任务是理解用户的自然语言输入，识别用户的意图，并提取关键信息。

**意图类型定义**：

1. **query_empty_seat** - 查询空座位
   - 用户想知道是否有可用的座位
   - 示例："今晚有空座吗"、"明天上午理科图书馆还有位置吗"、"我想找个靠窗的座位"

2. **query_room_info** - 查询自习室信息
   - 用户询问自习室的基本信息
   - 示例："有哪些自习室"、"图书馆在哪"、"自习室几点开门"

3. **query_my_reservation** - 查询我的预约
   - 用户想查看自己的预约记录
   - 示例："我的预约"、"我预约了什么"、"查看我的预约记录"

4. **query_notification** - 查询通知
   - 用户想查看通知消息
   - 示例："有没有新通知"、"我的消息"、"有什么提醒"

5. **system_faq** - 系统帮助
   - 用户询问如何使用系统
   - 示例："怎么预约"、"如何使用"、"帮助"、"签到码是什么"

6. **chitchat** - 闲聊
   - 日常问候或闲聊
   - 示例："你好"、"谢谢"、"再见"

7. **unknown** - 无法识别
   - 无法明确归类的输入

**槽位提取规则**：
- date: 日期信息（today, tomorrow, 2026-06-05, 周末等）
- time_range: 时间段（早上、下午、晚上）
- start_time: 开始时间
- end_time: 结束时间
- has_window: 是否靠窗（true/false）
- has_plug: 是否有插座（true/false）
- room_type: 自习室类型（public/department）

**输出格式**：
必须返回有效的JSON格式，包含以下字段：
{
    "intent": "intent_type",
    "confidence": 0.95,
    "slots": {
        "date": "today",
        "has_window": true
    }
}

**重要**：只返回JSON，不要有任何其他文字。"""

        # 构建用户提示词
        user_prompt = f"""请分析以下用户输入并返回JSON格式的意图识别结果：

用户输入："{user_message}"

返回格式示例：
{{"intent": "query_empty_seat", "confidence": 0.9, "slots": {{"date": "today", "has_window": true}}}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # 调用OpenAI，使用较低的temperature确保输出稳定
            response = self.chat(messages, temperature=0.2, max_tokens=300)

            # 尝试解析JSON响应
            # 清理可能的markdown代码块标记
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()

            result = json.loads(response)

            # 验证返回格式
            if 'intent' not in result:
                result['intent'] = 'unknown'
            if 'confidence' not in result:
                result['confidence'] = 0.5
            if 'slots' not in result:
                result['slots'] = {}

            return result

        except json.JSONDecodeError as e:
            # JSON解析失败，降级到关键词匹配
            print(f"LLM返回的JSON解析失败: {e}, 响应内容: {response[:100]}")
            return {
                'intent': 'unknown',
                'confidence': 0.3,
                'slots': {}
            }
        except Exception as e:
            # 其他错误，返回unknown
            print(f"LLM意图识别失败: {e}")
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'slots': {}
            }


# ============================================================================
# 工厂函数 - 根据配置创建客户端
# ============================================================================

def create_llm_client(provider: str = "mock") -> LLMClient:
    """
    工厂函数：根据提供商名称创建LLM客户端

    Args:
        provider: 'mock' | 'openai' | 'claude' (目前只实现了mock和openai)

    Returns:
        LLMClient实例
    """
    provider = (provider or "mock").strip().lower()

    if provider == "mock":
        return MockLLMClient()
    elif provider == "openai":
        model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo').strip()
        return OpenAIClient(model=model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# ============================================================================
# 向后兼容的函数接口
# ============================================================================

def call_llm(prompt: str, context: List[Dict] = None) -> str:
    """
    调用外部大语言模型API（OpenAI/Claude/国内模型）
    包含：请求重试、超时处理、Token限制、Fallback降级逻辑

    TODO: 实现LLM调用逻辑
    当前实现：使用Mock客户端作为保底方案
    """
    # 默认使用Mock客户端
    provider = os.getenv('LLM_PROVIDER', 'mock').strip().lower()
    client = create_llm_client(provider)

    # 构造消息列表
    messages = list(context) if context else []
    messages.append({"role": "user", "content": prompt})

    return client.chat(messages)
