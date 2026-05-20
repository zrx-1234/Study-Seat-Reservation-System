"""
INF-DB: 数据库访问模块
SQLAlchemy相关辅助函数
"""

from contextlib import contextmanager
from typing import Type, List, Dict, Any, Tuple

from extensions import db


def paginate_query(query, page: int = 1, per_page: int = 20):
    """
    通用分页辅助函数
    返回包含 items, total, page, per_page, pages 的字典
    """
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }


@contextmanager
def transaction():
    """
    事务上下文管理器
    成功时自动 commit，异常时自动 rollback 并重新抛出
    """
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def bulk_insert(model_class, records: List[Dict[str, Any]]):
    """
    批量插入记录（用于导入大量座位等场景）
    注意：不触发 ORM 事件，返回值为 None
    """
    if not records:
        return
    db.session.bulk_insert_mappings(model_class, records)
    db.session.commit()


def safe_get_or_create(model_class, defaults: Dict[str, Any] = None, **kwargs) -> Tuple[Any, bool]:
    """
    获取或创建记录
    :param model_class: 模型类
    :param defaults: 创建时使用的额外字段（查询字段冲突时 kwargs 优先级更高）
    :param kwargs: 查询条件字段
    :return: (instance, created)  instance 为对象，created 为是否新建
    """
    instance = model_class.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = {**(defaults or {}), **kwargs}
    instance = model_class(**params)
    db.session.add(instance)
    db.session.commit()
    return instance, True
