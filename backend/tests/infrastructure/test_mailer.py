"""
INF-MSG 测试：消息网关模块
覆盖邮件发送、统一通知入口、异常处理
"""

import smtplib

import pytest
from unittest.mock import patch, MagicMock

import infrastructure.mailer as mailer
from infrastructure.mailer import (
    send_email,
    send_wechat_message,
    send_notification,
    MessageChannel,
)
from infrastructure.exceptions import DomainException


# ============================================================================
# 1. 邮件发送测试
# ============================================================================

class TestSendEmail:
    """测试邮件发送"""

    @patch('infrastructure.mailer.smtplib.SMTP')
    def test_calls_smtp_with_host_and_port(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        # 临时设置发件人
        original_from = mailer.SMTP_FROM
        mailer.SMTP_FROM = 'test@fdu.edu.cn'
        try:
            send_email('to@fdu.edu.cn', '测试主题', '<p>内容</p>')
        finally:
            mailer.SMTP_FROM = original_from

        mock_smtp_class.assert_called_once()
        mock_server.sendmail.assert_called_once()
        # 验证收件人
        _, call_args, _ = mock_server.sendmail.mock_calls[0]
        assert 'to@fdu.edu.cn' in call_args[1]

    @patch('infrastructure.mailer.smtplib.SMTP')
    def test_uses_login_when_credentials_configured(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        original_user = mailer.SMTP_USER
        original_pass = mailer.SMTP_PASSWORD
        mailer.SMTP_USER = 'admin'
        mailer.SMTP_PASSWORD = 'secret'
        try:
            send_email('to@fdu.edu.cn', '主题', '内容')
            mock_server.login.assert_called_once_with('admin', 'secret')
        finally:
            mailer.SMTP_USER = original_user
            mailer.SMTP_PASSWORD = original_pass

    @patch('infrastructure.mailer.smtplib.SMTP')
    def test_skips_login_when_no_credentials(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        original_user = mailer.SMTP_USER
        original_pass = mailer.SMTP_PASSWORD
        mailer.SMTP_USER = ''
        mailer.SMTP_PASSWORD = ''
        try:
            send_email('to@fdu.edu.cn', '主题', '内容')
            mock_server.login.assert_not_called()
        finally:
            mailer.SMTP_USER = original_user
            mailer.SMTP_PASSWORD = original_pass

    @patch('infrastructure.mailer.smtplib.SMTP')
    def test_raises_domain_exception_on_smtp_error(self, mock_smtp_class):
        mock_smtp_class.side_effect = smtplib.SMTPException('连接超时')

        with pytest.raises(DomainException) as exc_info:
            send_email('to@fdu.edu.cn', '主题', '内容')
        assert exc_info.value.code == 500
        assert '邮件发送失败' in exc_info.value.message


# ============================================================================
# 2. 微信消息测试
# ============================================================================

class TestSendWechatMessage:
    """测试微信消息（当前为预留）"""

    def test_does_not_raise(self):
        """预留接口不应抛异常"""
        send_wechat_message(1, '测试内容')


# ============================================================================
# 3. 统一通知入口测试
# ============================================================================

class TestSendNotification:
    """测试统一消息发送入口"""

    @patch('infrastructure.mailer.send_email')
    def test_routes_to_email(self, mock_send_email):
        send_notification(
            user_id=1,
            channel=MessageChannel.EMAIL,
            title='预约提醒',
            content='您的预约即将开始',
            recipient='student@fdu.edu.cn'
        )
        mock_send_email.assert_called_once_with(
            to='student@fdu.edu.cn',
            subject='预约提醒',
            content='您的预约即将开始'
        )

    def test_email_requires_recipient(self):
        with pytest.raises(DomainException) as exc_info:
            send_notification(
                user_id=1,
                channel=MessageChannel.EMAIL,
                title='标题',
                content='内容'
            )
        assert exc_info.value.code == 400
        assert 'recipient' in exc_info.value.message

    @patch('infrastructure.mailer.send_wechat_message')
    def test_routes_to_wechat(self, mock_send_wechat):
        send_notification(
            user_id=1,
            channel=MessageChannel.WECHAT,
            title='标题',
            content='内容'
        )
        mock_send_wechat.assert_called_once_with(user_id=1, content='内容')

    def test_rejects_unknown_channel(self):
        with pytest.raises(DomainException) as exc_info:
            send_notification(
                user_id=1,
                channel='sms',  # 不支持的渠道
                title='标题',
                content='内容'
            )
        assert exc_info.value.code == 400
        assert '不支持' in exc_info.value.message
