"""
MOD-AI: 智能助手模块 - DTO定义
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ChatResponseDTO:
    """AI聊天响应DTO"""
    reply: str                          # 自然语言回复
    action: str                         # 动作类型: text, search_seats, show_reservations, redirect, error
    payload: Dict[str, Any]             # 结构化数据负载
    session_id: str                     # 会话ID

    def to_dict(self) -> dict:
        """转换为字典，方便JSON序列化"""
        return {
            'reply': self.reply,
            'action': self.action,
            'payload': self.payload,
            'session_id': self.session_id
        }


@dataclass
class ChatMessageDTO:
    """聊天消息DTO"""
    role: str                           # user | assistant
    content: str                        # 消息内容
    timestamp: str                      # ISO格式时间戳

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }


@dataclass
class IntentDTO:
    """意图识别结果DTO"""
    intent_type: str                    # 意图类型
    confidence: float                   # 置信度 0-1
    slots: Dict[str, Any] = field(default_factory=dict)  # 提取的槽位参数

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'intent_type': self.intent_type,
            'confidence': self.confidence,
            'slots': self.slots
        }


@dataclass
class ActionResultDTO:
    """动作执行结果DTO"""
    success: bool                       # 是否成功
    data: Optional[Dict[str, Any]] = None      # 返回数据
    error: Optional[str] = None         # 错误信息

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error
        }


@dataclass
class SessionContextDTO:
    """会话上下文DTO - 用于管理完整的对话会话"""
    session_id: str                     # 会话ID
    user_id: int                        # 用户ID
    messages: List[ChatMessageDTO] = field(default_factory=list)  # 历史消息
    last_intent: Optional[str] = None   # 上一次识别的意图
    extracted_slots: Dict[str, Any] = field(default_factory=dict)  # 累积提取的槽位
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'last_intent': self.last_intent,
            'extracted_slots': self.extracted_slots,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
