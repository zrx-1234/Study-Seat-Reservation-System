"""
AI模块 - 日志配置

提供结构化日志功能
"""
import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str = 'ai'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 如果还没有handler，添加一个
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)

            # 使用JSON格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """内部日志方法"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level
        }

        if extra:
            log_data.update(extra)

        # 转为JSON字符串
        log_message = json.dumps(log_data, ensure_ascii=False)

        # 根据级别调用对应方法
        if level == 'DEBUG':
            self.logger.debug(log_message)
        elif level == 'INFO':
            self.logger.info(log_message)
        elif level == 'WARNING':
            self.logger.warning(log_message)
        elif level == 'ERROR':
            self.logger.error(log_message)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self._log('INFO', message, kwargs)

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self._log('DEBUG', message, kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self._log('WARNING', message, kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self._log('ERROR', message, kwargs)

    def log_intent_recognition(self, message: str, intent: str, confidence: float,
                                method: str = 'keyword', duration_ms: float = 0):
        """记录意图识别"""
        self.info(
            'Intent recognized',
            user_message=message,
            intent_type=intent,
            confidence=confidence,
            method=method,
            duration_ms=duration_ms
        )

    def log_llm_call(self, provider: str, model: str, tokens: Optional[int] = None,
                     duration_ms: float = 0, success: bool = True, error: Optional[str] = None):
        """记录LLM调用"""
        self.info(
            'LLM API called',
            provider=provider,
            model=model,
            tokens=tokens,
            duration_ms=duration_ms,
            success=success,
            error=error
        )

    def log_chat_session(self, user_id: int, session_id: str, message: str,
                         intent: str, reply_length: int, duration_ms: float):
        """记录聊天会话"""
        self.info(
            'Chat completed',
            user_id=user_id,
            session_id=session_id,
            message_length=len(message),
            intent=intent,
            reply_length=reply_length,
            duration_ms=duration_ms
        )

    def log_cache_hit(self, key: str, cache_type: str = 'intent'):
        """记录缓存命中"""
        self.debug(
            'Cache hit',
            cache_type=cache_type,
            key=key
        )

    def log_rate_limit(self, user_id: int, remaining: int):
        """记录限流"""
        self.warning(
            'Rate limit triggered',
            user_id=user_id,
            remaining=remaining
        )


# 全局日志实例
logger = StructuredLogger('ai')
