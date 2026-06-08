"""
INF-MSG: 消息网关模块
提供邮件/微信/短信发送接口的抽象与实现
"""

import os
import smtplib
from email.mime.text import MIMEText
from enum import Enum

from infrastructure.exceptions import DomainException


class MessageChannel(Enum):
    EMAIL = "email"
    WECHAT = "wechat"


# 从环境变量读取邮件配置，便于测试时覆盖
SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '25'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', 'noreply@fdu.edu.cn')


def send_email(to: str, subject: str, content: str):
    """
    发送邮件
    :param to: 收件人地址
    :param subject: 主题
    :param content: 正文（HTML或纯文本）
    """
    msg = MIMEText(content, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to], msg.as_string())
    except smtplib.SMTPException as e:
        raise DomainException(message=f'邮件发送失败: {e}', code=500)


def send_wechat_message(user_id: int, content: str):
    """
    发送微信消息（预留）
    实际接入需调用企业微信/微信服务号 API
    """
    # TODO: 接入企业微信或微信服务号 API
    pass


def send_notification(user_id: int, channel: MessageChannel, title: str, content: str, recipient: str = None):
    """
    统一消息发送入口
    :param user_id: 用户ID（用于记录日志）
    :param channel: 消息渠道
    :param title: 标题
    :param content: 内容
    :param recipient: 接收地址（邮件地址等，渠道相关）
    """
    if channel == MessageChannel.EMAIL:
        if not recipient:
            raise DomainException(message='邮件通知需要提供 recipient 参数', code=400)
        send_email(to=recipient, subject=title, content=content)
    elif channel == MessageChannel.WECHAT:
        send_wechat_message(user_id=user_id, content=content)
    else:
        raise DomainException(message=f'不支持的消息渠道: {channel}', code=400)
