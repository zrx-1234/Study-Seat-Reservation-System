"""
用户模块服务测试
"""
import pytest
from domain.user.service import authenticate


def test_authenticate_invalid_user():
    """
    测试无效用户认证失败
    """
    user, token = authenticate('invalid_user', 'wrong_password')
    assert user is None
    assert token is None
