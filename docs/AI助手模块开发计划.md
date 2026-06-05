# AI助手模块开发计划

> **负责人**: 成员E、成员F (AI智能化部分)  
> **模块标识**: MOD-AI + API-AI + frontend/ai  
> **开发周期**: 预计4-6周  
> **文档版本**: v1.0  
> **日期**: 2026-06-05

---

## 1. 模块职责概述

### 1.1 负责范围

根据**小组分工安排文档**，AI组负责以下代码文件：

```
backend/
├── api/ai.py                       # AI助手API接口
├── domain/ai/                      # AI智能助手领域模块
│   ├── service.py                  # 主服务接口
│   ├── intent_parser.py            # 意图识别
│   ├── llm_client.py               # 大模型客户端
│   ├── session_store.py            # 会话管理
│   └── dto.py                      # 数据传输对象
└── tests/
    ├── api/test_ai.py              # API测试
    └── domain/ai/                  # 领域层测试

frontend/ai/                        # AI助手前端应用
└── src/
    ├── views/
    │   ├── Login.vue
    │   └── Assistant.vue           # 聊天界面
    ├── components/                 # 待创建
    ├── router/
    └── utils/
```

### 1.2 核心功能

1. **自然语言理解 (NLU)**
   - 意图识别：识别用户查询座位、查询预约、系统FAQ等意图
   - 槽位提取：提取日期、时间、座位偏好等参数

2. **多轮对话管理**
   - 会话上下文维护
   - 历史消息存储
   - 会话清除功能

3. **领域数据查询**
   - 调用 MOD-ROOM 查询座位可用性
   - 调用 MOD-RESV 查询用户预约记录
   - 调用 MOD-NOTIF 查询通知

4. **自然语言生成 (NLG)**
   - 结构化数据转自然语言回复
   - 支持模板生成和LLM生成两种模式

5. **前端聊天界面**
   - 对话气泡展示
   - 输入框与发送
   - 会话管理

---

## 2. 技术架构设计

### 2.1 意图识别策略（两级方案）

```
用户输入
    ↓
┌─────────────────────────┐
│ Level 1: 关键词匹配      │ ← 保底方案，无需外部依赖
│ - 正则表达式             │
│ - 关键词字典             │
│ - 规则引擎              │
└─────────┬───────────────┘
          │ 置信度 < 0.7?
          ↓
┌─────────────────────────┐
│ Level 2: LLM意图识别    │ ← 提升体验，需LLM API
│ - Prompt Engineering    │
│ - Few-shot Learning     │
│ - 结构化输出            │
└─────────┬───────────────┘
          ↓
      意图 + 槽位
```

### 2.2 意图类型定义

| 意图类型 | 描述 | 需要调用的模块 | 槽位参数 |
|---------|------|--------------|---------|
| `query_empty_seat` | 查询空座位 | MOD-ROOM.search_seats() | date, start_time, end_time, has_window, has_plug |
| `query_room_info` | 查询自习室信息 | MOD-ROOM.list_rooms() | room_type, keyword |
| `query_my_reservation` | 查询我的预约 | MOD-RESV.get_user_active_reservations() | status |
| `query_notification` | 查询通知 | MOD-NOTIF.get_unread_count() | - |
| `system_faq` | 系统帮助 | 本地知识库 | topic |
| `chitchat` | 闲聊 | LLM生成 | - |
| `unknown` | 无法识别 | - | - |

### 2.3 LLM客户端设计

支持多种LLM提供商，通过适配器模式实现：

```python
# 抽象接口
class LLMClient(ABC):
    @abstractmethod
    def chat(self, messages: List[dict], **kwargs) -> str:
        pass

# 具体实现
class OpenAIClient(LLMClient):
    """OpenAI API (GPT-3.5/GPT-4)"""
    
class ClaudeClient(LLMClient):
    """Anthropic Claude API"""
    
class LocalModelClient(LLMClient):
    """本地模型 (如 Ollama)"""
    
class MockLLMClient(LLMClient):
    """测试用Mock客户端"""
```

**推荐方案**: 
- 开发阶段：使用 `MockLLMClient` 或本地 Ollama
- 演示阶段：接入 OpenAI GPT-3.5-turbo (成本低)

### 2.4 会话存储策略

```python
# 会话存储结构
{
    "session_id": "uuid-string",
    "user_id": 123,
    "messages": [
        {"role": "user", "content": "今晚有空座吗", "timestamp": "2026-06-05 19:00:00"},
        {"role": "assistant", "content": "...", "timestamp": "2026-06-05 19:00:01"}
    ],
    "context": {
        "last_intent": "query_empty_seat",
        "extracted_slots": {"date": "2026-06-05"}
    },
    "created_at": "2026-06-05 19:00:00",
    "updated_at": "2026-06-05 19:00:01"
}
```

**存储方案**:
- **Phase 1**: 进程内字典 (开发调试)
- **Phase 2**: Redis (生产环境，支持分布式)

---

## 3. 详细开发计划

### 3.1 迭代规划

#### **Sprint 1 (第1-2周): 基础架构搭建**

**目标**: 完成基础框架，实现关键词匹配的意图识别

**任务分工**:
- **成员E**: 后端核心逻辑
  - [ ] 创建 `domain/ai/dto.py`，定义所有DTO
  - [ ] 实现 `domain/ai/session_store.py` (基于字典的会话存储)
  - [ ] 实现 `domain/ai/intent_parser.py` Level 1 (关键词匹配)
  - [ ] 实现 `domain/ai/service.py` 核心接口:
    - `chat()` - 基础流程
    - `get_session_history()`
    - `clear_session()`
  - [ ] 实现 `api/ai.py` 三个端点

- **成员F**: 前端界面 + 后端测试
  - [ ] 完善 `frontend/ai/src/views/Assistant.vue` 聊天界面
  - [ ] 创建 `frontend/ai/src/components/ChatMessage.vue` 消息组件
  - [ ] 创建 `frontend/ai/src/components/ChatInput.vue` 输入组件
  - [ ] 编写 `tests/domain/ai/test_session_store.py`
  - [ ] 编写 `tests/domain/ai/test_intent_parser.py`

**验收标准**:
- ✅ 能识别3种基本意图 (查座位、查预约、系统帮助)
- ✅ 前端能完成登录并显示聊天界面
- ✅ 能完成一次完整对话 (用户输入 → 意图识别 → 调用领域服务 → 返回回复)
- ✅ 单元测试覆盖率 > 60%

---

#### **Sprint 2 (第3-4周): LLM集成 + 高级功能**

**目标**: 接入大语言模型，提升意图识别准确率，完善对话体验

**任务分工**:
- **成员E**: LLM集成
  - [ ] 实现 `domain/ai/llm_client.py`:
    - `LLMClient` 抽象类
    - `MockLLMClient` 测试客户端
    - `OpenAIClient` 或 `ClaudeClient`
    - 重试机制、超时处理
  - [ ] 升级 `intent_parser.py` Level 2 (LLM意图识别)
  - [ ] 实现 `generate_reply()` - 使用LLM生成自然回复
  - [ ] 实现多轮对话上下文管理

- **成员F**: 前端优化 + API测试
  - [ ] 前端显示结构化卡片 (座位推荐卡片)
  - [ ] 前端显示加载动画 (等待LLM响应)
  - [ ] 前端支持会话历史查看
  - [ ] 前端支持清除会话
  - [ ] 编写 `tests/api/test_ai.py` 完整API测试
  - [ ] 编写 `tests/domain/ai/test_llm_client.py`

**验收标准**:
- ✅ LLM能正确识别7种意图，准确率 > 85%
- ✅ 能处理模糊输入 (如 "明天晚上有位置吗")
- ✅ 能维护3轮以上的对话上下文
- ✅ 前端显示结构化座位推荐卡片
- ✅ 单元测试覆盖率 > 75%

---

#### **Sprint 3 (第5-6周): 优化 + 集成测试**

**目标**: 性能优化、用户体验提升、完整集成测试

**任务分工**:
- **成员E**: 性能优化
  - [ ] 实现会话缓存 (Redis可选)
  - [ ] 实现意图识别结果缓存
  - [ ] 添加请求限流 (防止LLM API滥用)
  - [ ] 添加错误重试和降级策略
  - [ ] 性能测试和优化

- **成员F**: 用户体验优化
  - [ ] 前端添加快捷按钮 (快速查询今晚座位)
  - [ ] 前端支持语音输入 (可选)
  - [ ] 前端优化移动端适配
  - [ ] 编写端到端测试脚本
  - [ ] 编写用户操作手册

**验收标准**:
- ✅ 响应时间 < 3秒 (90%请求)
- ✅ LLM API失败时能优雅降级
- ✅ 前端体验流畅，无明显卡顿
- ✅ 单元测试覆盖率 > 80%
- ✅ 通过完整的端到端测试

---

## 4. 关键实现细节

### 4.1 意图识别 Prompt 设计

```python
INTENT_CLASSIFICATION_PROMPT = """
你是一个自习座位预约系统的意图分类助手。
用户会用自然语言询问座位相关问题，你需要识别用户的意图。

可能的意图类型：
1. query_empty_seat - 查询空座位 (例如: "今晚有空座吗", "明天上午理科图书馆还有位置吗")
2. query_room_info - 查询自习室信息 (例如: "有哪些自习室", "理科图书馆在哪")
3. query_my_reservation - 查询我的预约 (例如: "我的预约", "我预约了哪些座位")
4. query_notification - 查询通知 (例如: "有没有新通知", "我的消息")
5. system_faq - 系统帮助 (例如: "怎么预约", "签到码是什么")
6. chitchat - 闲聊 (例如: "你好", "天气怎么样")
7. unknown - 无法识别

用户输入: {user_message}

请以JSON格式返回:
{{
    "intent": "intent_type",
    "confidence": 0.95,
    "slots": {{
        "date": "2026-06-05",
        "time_range": "evening",
        "has_window": true
    }}
}}
"""
```

### 4.2 槽位提取规则

```python
# 日期提取
DATE_PATTERNS = {
    "今天": lambda: datetime.now().date(),
    "明天": lambda: datetime.now().date() + timedelta(days=1),
    "后天": lambda: datetime.now().date() + timedelta(days=2),
    r"(\d+)月(\d+)日": lambda m: date(datetime.now().year, int(m.group(1)), int(m.group(2))),
    "周末": lambda: get_next_weekend()
}

# 时间段提取
TIME_RANGE_PATTERNS = {
    "早上|上午": ("08:00", "12:00"),
    "中午": ("12:00", "14:00"),
    "下午": ("14:00", "18:00"),
    "晚上|今晚": ("18:00", "22:00")
}

# 座位偏好提取
SEAT_PREFERENCE_PATTERNS = {
    "靠窗": {"has_window": True},
    "有插座|有电源": {"has_plug": True}
}
```

### 4.3 回复生成模板

```python
REPLY_TEMPLATES = {
    "query_empty_seat_success": """
{date} {time_range} 有 {count} 个可用座位。

推荐座位:
{recommendations}

需要帮您预约吗？
    """,
    
    "query_empty_seat_empty": """
抱歉，{date} {time_range} 暂时没有符合条件的空座。

建议:
1. 尝试其他时间段
2. 调整座位偏好条件
    """,
    
    "query_my_reservation_success": """
您当前有 {count} 个进行中的预约:

{reservations}
    """
}
```

### 4.4 错误处理策略

```python
class AIService:
    def chat(self, user_id: int, message: str, session_id: str = None):
        try:
            # 1. 意图识别
            intent = self._parse_intent_with_fallback(message, context)
            
            # 2. 执行意图
            result = self._execute_intent_with_retry(intent, user_id)
            
            # 3. 生成回复
            reply = self._generate_reply_with_template(result, message)
            
            return ChatResponseDTO(...)
            
        except LLMAPIError as e:
            # LLM API失败 -> 降级到关键词匹配
            logger.error(f"LLM API failed: {e}, falling back to keyword matching")
            return self._handle_with_keywords(message, user_id)
            
        except Exception as e:
            # 其他错误 -> 返回友好提示
            logger.error(f"Unexpected error in chat: {e}")
            return ChatResponseDTO(
                reply="抱歉，我暂时无法理解您的问题。请尝试换个说法，或直接访问座位搜索页面。",
                action="error",
                payload={"error_type": "system_error"}
            )
```

---

## 5. 协作边界与接口调用

### 5.1 依赖的其他模块

AI模块**只读调用**以下模块，**禁止修改**它们的代码：

| 模块 | 调用接口 | 用途 |
|------|---------|------|
| MOD-USER | `get_current_user(user_id)` | 获取用户基本信息 |
| MOD-ROOM | `list_rooms(...)` | 查询自习室列表 |
| MOD-ROOM | `search_seats(...)` | 搜索座位 |
| MOD-ROOM | `get_room_seats(...)` | 获取自习室座位 |
| MOD-RESV | `get_user_active_reservations(user_id)` | 查询用户预约 |
| MOD-NOTIF | `get_unread_count(user_id)` | 查询未读通知数 |
| INF-AUTH | `get_current_user_id()` | 获取当前登录用户ID |
| INF-EXC | `success_response()`, `error_response()` | 统一响应格式 |

### 5.2 调用示例

```python
# domain/ai/service.py

from domain.room import service as room_service
from domain.reservation import service as resv_service
from domain.user import service as user_service
from domain.notification import service as notif_service

def execute_intent(intent: IntentDTO, user_id: int) -> ActionResultDTO:
    """根据意图调用对应的领域服务"""
    
    if intent.intent_type == "query_empty_seat":
        # 调用座位搜索
        seats = room_service.search_seats(
            query_date=intent.slots.get("date"),
            has_window=intent.slots.get("has_window"),
            has_plug=intent.slots.get("has_plug"),
            page=1,
            per_page=5
        )
        return ActionResultDTO(success=True, data=seats)
    
    elif intent.intent_type == "query_my_reservation":
        # 调用预约查询
        reservations = resv_service.get_user_active_reservations(user_id)
        return ActionResultDTO(success=True, data=reservations)
    
    elif intent.intent_type == "query_notification":
        # 调用通知查询
        count = notif_service.get_unread_count(user_id)
        return ActionResultDTO(success=True, data={"unread_count": count})
    
    else:
        return ActionResultDTO(success=False, error="Unknown intent")
```

---

## 6. 测试策略

### 6.1 单元测试

```python
# tests/domain/ai/test_intent_parser.py

def test_intent_parser_query_empty_seat():
    """测试查询空座意图识别"""
    parser = IntentParser()
    
    test_cases = [
        ("今晚有空座吗", "query_empty_seat", {"date": today, "time_range": "evening"}),
        ("明天上午理科图书馆还有位置吗", "query_empty_seat", {"date": tomorrow, "time_range": "morning"}),
        ("我想找个靠窗有插座的座位", "query_empty_seat", {"has_window": True, "has_plug": True})
    ]
    
    for message, expected_intent, expected_slots in test_cases:
        intent = parser.parse_intent(message, context={})
        assert intent.intent_type == expected_intent
        assert intent.slots == expected_slots
```

### 6.2 集成测试

```python
# tests/api/test_ai.py

def test_ai_chat_full_flow(client, auth_token):
    """测试完整对话流程"""
    
    # 1. 发送消息
    response = client.post('/api/v1/ai/chat', 
        json={"message": "今晚有空座吗"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json['data']
    
    # 2. 验证响应结构
    assert 'reply' in data
    assert 'action' in data
    assert 'session_id' in data
    assert data['action'] == 'search_seats'
    
    # 3. 验证payload
    assert 'available_count' in data['payload']
    assert 'recommendations' in data['payload']
```

### 6.3 端到端测试

```bash
# E2E测试脚本
# tests/e2e/test_ai_assistant.py

def test_ai_conversation_flow():
    """模拟完整的用户对话"""
    
    session = AITestSession()
    
    # 第1轮对话
    response1 = session.chat("今晚有空座吗")
    assert "可用座位" in response1.reply
    
    # 第2轮对话 (利用上下文)
    response2 = session.chat("要靠窗的")
    assert response2.payload['recommendations'][0]['has_window'] == True
    
    # 第3轮对话
    response3 = session.chat("我的预约呢")
    assert response3.action == "show_reservations"
```

---

## 7. 部署配置

### 7.1 环境变量

```bash
# .env 文件

# LLM配置
LLM_PROVIDER=openai  # openai | claude | local | mock
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_BASE_URL=https://api.openai.com/v1

# Claude配置 (可选)
CLAUDE_API_KEY=sk-ant-xxxxx
CLAUDE_MODEL=claude-3-sonnet-20240229

# 会话配置
SESSION_STORE_TYPE=memory  # memory | redis
REDIS_URL=redis://localhost:6379/1
SESSION_MAX_HISTORY=20
SESSION_EXPIRE_SECONDS=3600

# 限流配置
AI_RATE_LIMIT_PER_USER=30  # 每用户每分钟最多30次请求
```

### 7.2 requirements.txt 补充

```txt
# AI模块依赖
openai>=1.0.0              # OpenAI API客户端
anthropic>=0.7.0           # Claude API客户端 (可选)
redis>=4.5.0               # Redis客户端 (可选)
python-dotenv>=1.0.0       # 环境变量管理
```

---

## 8. 风险管理

| 风险 | 影响 | 应对策略 |
|------|------|---------|
| LLM API不稳定或费用超支 | 高 | 1. 实现降级机制，LLM失败时使用关键词匹配<br>2. 添加请求缓存，减少重复调用<br>3. 使用便宜的模型 (GPT-3.5-turbo) |
| 意图识别准确率低 | 中 | 1. 收集真实用户输入数据<br>2. 不断优化Prompt<br>3. 增加关键词规则覆盖 |
| 会话管理内存泄漏 | 中 | 1. 设置会话过期时间<br>2. 限制每个会话的历史消息数量<br>3. 定期清理过期会话 |
| 跨模块接口变更 | 低 | 1. 依赖稳定的Service接口<br>2. 编写Mock测试，减少对其他模块的依赖<br>3. 接口变更时及时沟通 |

---

## 9. 里程碑检查点

### Week 2 (Sprint 1结束)
- [ ] 后端三个API端点可调用
- [ ] 前端聊天界面基本可用
- [ ] 能识别3种基本意图
- [ ] 单元测试覆盖率 > 60%
- [ ] Demo: 展示一次完整对话

### Week 4 (Sprint 2结束)
- [ ] LLM集成完成
- [ ] 意图识别准确率 > 85%
- [ ] 前端显示结构化卡片
- [ ] 单元测试覆盖率 > 75%
- [ ] Demo: 展示多轮对话和座位推荐

### Week 6 (Sprint 3结束)
- [ ] 性能优化完成 (响应时间 < 3s)
- [ ] 错误处理和降级策略完善
- [ ] 单元测试覆盖率 > 80%
- [ ] 端到端测试通过
- [ ] Demo: 完整功能演示

---

## 10. 参考资料

### 10.1 内部文档
- [自习座位预约系统软件架构设计方案-v2.md](./自习座位预约系统软件架构设计方案-v2.md)
- [详细设计文档.md](./详细设计文档.md)
- [API接口文档.md](./API接口文档.md)
- [小组分工安排文档.md](./小组分工安排文档.md)

### 10.2 技术文档
- OpenAI API文档: https://platform.openai.com/docs
- Claude API文档: https://docs.anthropic.com
- Flask文档: https://flask.palletsprojects.com
- Vue 3文档: https://vuejs.org
- Element Plus文档: https://element-plus.org

### 10.3 示例项目
- ChatGPT API示例: https://github.com/openai/openai-cookbook
- Flask聊天机器人: https://github.com/topics/chatbot-flask

---

## 11. 下一步行动

### 立即开始 (本周)
1. **成员E**: 
   - 创建 `domain/ai/dto.py`，定义所有数据结构
   - 搭建 `domain/ai/service.py` 框架
   - 实现 `session_store.py` 基础版本

2. **成员F**:
   - 完善前端 `Assistant.vue` 聊天界面
   - 创建消息组件 `ChatMessage.vue`
   - 编写第一个单元测试

### 本周会议议题
1. 确认LLM提供商选择 (OpenAI / Claude / 本地模型)
2. 确认开发环境配置
3. 同步其他组的接口进度，确认依赖可用性
4. 分配详细任务到每日

---

**祝开发顺利！如有问题随时沟通协调。**
