"""
MOD-AI: 智能助手模块 - DTO定义
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class ChatResponseDTO:
    reply: str
    action: str
    payload: Dict[str, Any]
    session_id: str


@dataclass
class ChatMessageDTO:
    role: str
    content: str
    timestamp: str


@dataclass
class IntentDTO:
    intent_type: str
    confidence: float
    slots: Dict[str, Any]


@dataclass
class ActionResultDTO:
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
