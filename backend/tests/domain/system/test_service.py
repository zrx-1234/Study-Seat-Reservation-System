"""
MOD-SYS 测试：系统配置模块服务层
覆盖配置读取、写入、批量更新、缓存、默认值初始化
"""

import pytest

from domain.system.models import SystemConfig
from domain.system.dto import ConfigDTO, ConfigUpdateDTO
from domain.system import service as sys_service
from domain.system.service import VALID_CONFIG_KEYS
from infrastructure.cache import get_config_cache, clear_config_cache
from infrastructure.exceptions import ValidationError


# ============================================================================
# 固件
# ============================================================================

@pytest.fixture(autouse=True)
def clear_cache_before_each():
    """每个测试前清空配置缓存"""
    clear_config_cache()
    yield
    clear_config_cache()


@pytest.fixture
def seeded_config(db_session):
    """预置一条测试配置"""
    cfg = SystemConfig(
        config_key='max_reservation_hours',
        config_value='4',
        description='单次最大预约时长（小时）'
    )
    db_session.add(cfg)
    db_session.commit()
    return cfg


# ============================================================================
# 1. get_config 测试
# ============================================================================

class TestGetConfig:
    """测试单配置读取"""

    def test_get_existing_config(self, db_session, seeded_config):
        value = sys_service.get_config('max_reservation_hours')
        assert value == '4'

    def test_get_nonexistent_config_returns_none(self, db_session):
        assert sys_service.get_config('not_a_key') is None

    def test_get_config_uses_cache(self, db_session, seeded_config):
        # 首次读取，回填缓存
        sys_service.get_config('max_reservation_hours')
        cache = get_config_cache()
        assert cache['max_reservation_hours'] == '4'

        # 直接修改数据库（绕过缓存）
        seeded_config.config_value = '99'
        db_session.commit()

        # 仍应从缓存拿到旧值
        assert sys_service.get_config('max_reservation_hours') == '4'


# ============================================================================
# 2. get_config_as_int 测试
# ============================================================================

class TestGetConfigAsInt:
    """测试整数型配置读取"""

    def test_returns_int_value(self, db_session, seeded_config):
        assert sys_service.get_config_as_int('max_reservation_hours') == 4

    def test_returns_default_when_missing(self, db_session):
        assert sys_service.get_config_as_int('nonexistent', default=42) == 42

    def test_returns_default_when_not_int(self, db_session):
        cfg = SystemConfig(
            config_key='max_reservation_hours',
            config_value='not_a_number',
            description='无效值'
        )
        db_session.add(cfg)
        db_session.commit()
        assert sys_service.get_config_as_int('max_reservation_hours', default=7) == 7


# ============================================================================
# 3. get_all_configs 测试
# ============================================================================

class TestGetAllConfigs:
    """测试全量配置列表"""

    def test_empty_database(self, db_session):
        result = sys_service.get_all_configs()
        assert result == []

    def test_returns_config_dtos(self, db_session):
        cfg1 = SystemConfig(config_key='max_reservation_hours', config_value='4', description='desc1')
        cfg2 = SystemConfig(config_key='max_active_reservations', config_value='2', description='desc2')
        db_session.add_all([cfg1, cfg2])
        db_session.commit()

        result = sys_service.get_all_configs()
        assert len(result) == 2
        assert all(isinstance(r, ConfigDTO) for r in result)
        keys = [r.key for r in result]
        assert 'max_reservation_hours' in keys
        assert 'max_active_reservations' in keys

    def test_description_defaults_to_empty_string(self, db_session):
        cfg = SystemConfig(config_key='max_reservation_hours', config_value='4', description=None)
        db_session.add(cfg)
        db_session.commit()

        result = sys_service.get_all_configs()
        assert result[0].description == ''


# ============================================================================
# 4. set_config 测试
# ============================================================================

class TestSetConfig:
    """测试单配置更新"""

    def test_create_new_config(self, db_session):
        dto = sys_service.set_config('max_reservation_hours', '6', '期末考试周调整')
        assert isinstance(dto, ConfigDTO)
        assert dto.key == 'max_reservation_hours'
        assert dto.value == '6'
        assert dto.description == '期末考试周调整'

        # 数据库验证
        cfg = SystemConfig.query.filter_by(config_key='max_reservation_hours').first()
        assert cfg is not None
        assert cfg.config_value == '6'

    def test_update_existing_config(self, db_session, seeded_config):
        dto = sys_service.set_config('max_reservation_hours', '8', '新描述')
        assert dto.value == '8'
        assert dto.description == '新描述'

        cfg = SystemConfig.query.filter_by(config_key='max_reservation_hours').first()
        assert cfg.config_value == '8'

    def test_update_value_without_changing_description(self, db_session, seeded_config):
        # 不传入 description，应保留原描述
        dto = sys_service.set_config('max_reservation_hours', '8')
        assert dto.value == '8'
        assert dto.description == '单次最大预约时长（小时）'

    def test_invalid_key_raises_validation_error(self, db_session):
        with pytest.raises(ValidationError) as exc_info:
            sys_service.set_config('invalid_key', '123')
        assert 'Invalid config key' in str(exc_info.value)

    def test_clears_cache_on_update(self, db_session, seeded_config):
        # 先回填缓存
        sys_service.get_config('max_reservation_hours')
        assert get_config_cache()['max_reservation_hours'] == '4'

        # 更新后缓存应被清除
        sys_service.set_config('max_reservation_hours', '10')
        assert 'max_reservation_hours' not in get_config_cache()

        # 下次读取应从数据库拿到新值
        assert sys_service.get_config('max_reservation_hours') == '10'


# ============================================================================
# 5. batch_set_configs 测试
# ============================================================================

class TestBatchSetConfigs:
    """测试批量配置更新"""

    def test_batch_update_success(self, db_session):
        items = [
            ConfigUpdateDTO(key='max_reservation_hours', value='6', description='期末'),
            ConfigUpdateDTO(key='max_active_reservations', value='3', description='增加'),
        ]
        results = sys_service.batch_set_configs(items)
        assert len(results) == 2

        cfg1 = SystemConfig.query.filter_by(config_key='max_reservation_hours').first()
        cfg2 = SystemConfig.query.filter_by(config_key='max_active_reservations').first()
        assert cfg1.config_value == '6'
        assert cfg2.config_value == '3'

    def test_batch_update_existing_and_new(self, db_session, seeded_config):
        items = [
            ConfigUpdateDTO(key='max_reservation_hours', value='10', description='改'),
            ConfigUpdateDTO(key='no_show_threshold_minutes', value='30', description='改'),
        ]
        sys_service.batch_set_configs(items)

        assert seeded_config.config_value == '10'
        assert SystemConfig.query.filter_by(config_key='no_show_threshold_minutes').first().config_value == '30'

    def test_invalid_key_in_batch_raises_and_rolls_back(self, db_session, seeded_config):
        items = [
            ConfigUpdateDTO(key='max_reservation_hours', value='10', description='合法'),
            ConfigUpdateDTO(key='bad_key', value='20', description='非法'),
        ]
        with pytest.raises(ValidationError):
            sys_service.batch_set_configs(items)

        # 验证第一条也没有被写入（事务回滚）
        db_session.refresh(seeded_config)
        assert seeded_config.config_value == '4'
        assert SystemConfig.query.filter_by(config_key='bad_key').first() is None

    def test_batch_clears_cache(self, db_session, seeded_config):
        sys_service.get_config('max_reservation_hours')
        assert get_config_cache()['max_reservation_hours'] == '4'

        items = [
            ConfigUpdateDTO(key='max_reservation_hours', value='99', description='改'),
        ]
        sys_service.batch_set_configs(items)
        assert 'max_reservation_hours' not in get_config_cache()


# ============================================================================
# 6. init_default_configs 测试
# ============================================================================

class TestInitDefaultConfigs:
    """测试默认配置初始化"""

    def test_creates_all_defaults_on_empty_db(self, db_session):
        sys_service.init_default_configs()
        configs = SystemConfig.query.all()
        assert len(configs) == len(VALID_CONFIG_KEYS)

        keys = {c.config_key for c in configs}
        assert keys == VALID_CONFIG_KEYS

    def test_does_not_overwrite_existing(self, db_session, seeded_config):
        sys_service.init_default_configs()
        db_session.refresh(seeded_config)
        # 预置值 '4' 不应被覆盖
        assert seeded_config.config_value == '4'

        # 其他默认值应被创建
        assert SystemConfig.query.count() == len(VALID_CONFIG_KEYS)

    def test_idempotent(self, db_session):
        sys_service.init_default_configs()
        sys_service.init_default_configs()
        assert SystemConfig.query.count() == len(VALID_CONFIG_KEYS)


# ============================================================================
# 7. VALID_CONFIG_KEYS 白名单测试
# ============================================================================

class TestValidConfigKeys:
    """测试预定义白名单完整性"""

    def test_contains_expected_keys(self):
        expected = {
            'max_reservation_hours',
            'no_show_threshold_minutes',
            'remind_before_minutes',
            'check_in_alert_minutes',
            'sign_in_code_refresh_hours',
            'max_active_reservations'
        }
        assert VALID_CONFIG_KEYS == expected
