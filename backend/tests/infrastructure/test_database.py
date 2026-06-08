"""
INF-DB 测试：数据库访问模块
覆盖分页查询、事务管理、批量插入、安全获取或创建
"""

import pytest
from extensions import db
from infrastructure.database import paginate_query, transaction, bulk_insert, safe_get_or_create


# ============================================================================
# 测试模型
# ============================================================================

class SampleItem(db.Model):
    __tablename__ = 'sample_item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    category = db.Column(db.String(64), nullable=True)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def seed_items(app):
    """向测试数据库插入5条示例数据"""
    with app.app_context():
        db.session.add_all([
            SampleItem(name='item1', category='A'),
            SampleItem(name='item2', category='A'),
            SampleItem(name='item3', category='B'),
            SampleItem(name='item4', category='B'),
            SampleItem(name='item5', category='B'),
        ])
        db.session.commit()


# ============================================================================
# 1. 分页查询测试
# ============================================================================

class TestPaginateQuery:
    """测试通用分页辅助函数"""

    def test_paginate_returns_correct_structure(self, app, seed_items):
        with app.app_context():
            query = SampleItem.query.order_by(SampleItem.id)
            result = paginate_query(query, page=1, per_page=2)
            assert 'items' in result
            assert 'total' in result
            assert 'page' in result
            assert 'per_page' in result
            assert 'pages' in result
            assert result['total'] == 5
            assert result['page'] == 1
            assert result['per_page'] == 2
            assert result['pages'] == 3
            assert len(result['items']) == 2

    def test_paginate_empty_result(self, app):
        with app.app_context():
            query = SampleItem.query.order_by(SampleItem.id)
            result = paginate_query(query, page=1, per_page=10)
            assert result['total'] == 0
            assert result['items'] == []
            assert result['pages'] == 0

    def test_paginate_second_page(self, app, seed_items):
        with app.app_context():
            query = SampleItem.query.order_by(SampleItem.id)
            result = paginate_query(query, page=2, per_page=2)
            assert result['page'] == 2
            assert len(result['items']) == 2
            assert result['items'][0].name == 'item3'

    def test_paginate_beyond_range(self, app, seed_items):
        with app.app_context():
            query = SampleItem.query.order_by(SampleItem.id)
            result = paginate_query(query, page=10, per_page=2)
            assert result['items'] == []
            assert result['page'] == 10


# ============================================================================
# 2. 事务管理测试
# ============================================================================

class TestTransaction:
    """测试事务上下文管理器"""

    def test_transaction_commits_on_success(self, app):
        with app.app_context():
            with transaction() as session:
                session.add(SampleItem(name='tx_item'))
            # 事务外查询确认已提交
            item = SampleItem.query.filter_by(name='tx_item').first()
            assert item is not None

    def test_transaction_rolls_back_on_error(self, app):
        with app.app_context():
            try:
                with transaction():
                    db.session.add(SampleItem(name='rollback_item'))
                    raise ValueError('强制失败')
            except ValueError:
                pass
            item = SampleItem.query.filter_by(name='rollback_item').first()
            assert item is None

    def test_transaction_rolls_back_on_db_error(self, app):
        with app.app_context():
            try:
                with transaction():
                    # 违反非空约束触发数据库错误
                    db.session.add(SampleItem(name=None))
            except Exception:
                pass
            item = SampleItem.query.filter_by(category=None).first()
            assert item is None


# ============================================================================
# 3. 批量插入测试
# ============================================================================

class TestBulkInsert:
    """测试批量插入"""

    def test_bulk_insert_creates_records(self, app):
        with app.app_context():
            bulk_insert(SampleItem, [
                {'name': 'bulk1', 'category': 'X'},
                {'name': 'bulk2', 'category': 'X'},
                {'name': 'bulk3', 'category': 'X'},
            ])
            items = SampleItem.query.filter_by(category='X').all()
            assert len(items) == 3

    def test_bulk_insert_empty_list_does_nothing(self, app):
        with app.app_context():
            bulk_insert(SampleItem, [])
            count = SampleItem.query.count()
            assert count == 0


# ============================================================================
# 4. 安全获取或创建测试
# ============================================================================

class TestSafeGetOrCreate:
    """测试获取或创建"""

    def test_creates_new_record(self, app):
        with app.app_context():
            item, created = safe_get_or_create(SampleItem, name='new_item')
            assert created is True
            assert item.name == 'new_item'
            assert item.id is not None

    def test_returns_existing_record(self, app):
        with app.app_context():
            db.session.add(SampleItem(name='existing'))
            db.session.commit()

            item, created = safe_get_or_create(SampleItem, name='existing')
            assert created is False
            assert item.name == 'existing'

    def test_uses_defaults_on_create(self, app):
        with app.app_context():
            item, created = safe_get_or_create(
                SampleItem,
                defaults={'category': 'electronics'},
                name='iphone'
            )
            assert created is True
            assert item.name == 'iphone'
            assert item.category == 'electronics'

    def test_defaults_do_not_override_existing(self, app):
        with app.app_context():
            db.session.add(SampleItem(name='old', category='original'))
            db.session.commit()

            item, created = safe_get_or_create(
                SampleItem,
                defaults={'category': 'new_category'},
                name='old'
            )
            assert created is False
            assert item.category == 'original'  # 不应被 defaults 覆盖
