"""
INF-DB: 数据库访问模块
SQLAlchemy相关辅助函数
"""

from extensions import db

# 这里可以放置数据库相关的通用工具函数
# 例如分页辅助、批量操作等

def paginate_query(query, page: int = 1, per_page: int = 20):
    """
    通用分页辅助函数
    返回 (items, total, page, per_page, pages)
    """
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }
