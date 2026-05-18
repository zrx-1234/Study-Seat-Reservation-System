"""
API-AI: AI助手接口模块
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from infrastructure.exceptions import success_response, error_response
from infrastructure.auth import get_current_user_id
from domain.ai import service as ai_service

ai_bp = Blueprint('ai', __name__, url_prefix='/api/v1/ai')

# ============================================================================
# AI 助手接口
# ============================================================================

@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """智能助手交互"""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    message = data.get('message')
    session_id = data.get('session_id')

    if not message:
        return error_response('message不能为空', code=400)

    result = ai_service.chat(user_id, message, session_id=session_id)
    return success_response(data=result)


@ai_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """获取会话历史"""
    session_id = request.args.get('session_id')
    if not session_id:
        return error_response('session_id不能为空', code=400)

    history = ai_service.get_session_history(session_id)
    return success_response(data={'messages': history})


@ai_bp.route('/clear', methods=['POST'])
@jwt_required()
def clear_session():
    """清除会话"""
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if session_id:
        ai_service.clear_session(session_id)

    return success_response(data=None)
