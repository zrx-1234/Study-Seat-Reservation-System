# AI助手模块 - 使用文档

> 版本: v1.0  
> 更新日期: 2026-06-05

---

## 目录

1. [快速开始](#快速开始)
2. [API接口](#api接口)
3. [配置说明](#配置说明)
4. [测试指南](#测试指南)
5. [常见问题](#常见问题)

---

## 快速开始

### 1. 基础测试（无需API key）

```bash
cd backend

# 测试Mock LLM客户端
python test_llm.py

# 运行单元测试
pytest tests/domain/ai/ -v

# 启动后端服务
python app.py
```

### 2. 使用API

#### 2.1 登录获取Token

```bash
curl -X POST http://localhost:5000/api/v1/student/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "2025123456", "password": "123456"}'
```

返回:
```json
{
  "code": 200,
  "data": {
    "token": "eyJ0eXAiOiJKV1Q...",
    "user": {...}
  }
}
```

#### 2.2 发送聊天消息

```bash
curl -X POST http://localhost:5000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "今晚有空座吗？"
  }'
```

返回:
```json
{
  "code": 200,
  "data": {
    "reply": "找到 12 个可用座位。\n\n推荐座位：\n• 理科图书馆301 A01 (靠窗) (有插座)\n",
    "action": "query_empty_seat",
    "payload": {
      "date": "2026-06-05",
      "available_count": 12,
      "recommendations": [...]
    },
    "session_id": "uuid-xxx"
  }
}
```

---

## API接口

### 1. POST /api/v1/ai/chat

**描述**: 与AI助手对话

**请求头**:
- `Authorization: Bearer <token>` - 必需
- `Content-Type: application/json`

**请求体**:
```json
{
  "message": "用户消息",
  "session_id": "会话ID（可选，用于多轮对话）"
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "reply": "AI回复",
    "action": "动作类型",
    "payload": {},
    "session_id": "会话ID"
  }
}
```

**限流**: 30次/分钟（可配置）

**支持的意图类型**:
- `query_empty_seat` - 查询空座位
- `query_my_reservation` - 查询我的预约
- `query_room_info` - 查询自习室信息
- `query_notification` - 查询通知
- `system_faq` - 系统帮助
- `chitchat` - 闲聊
- `unknown` - 无法识别

### 2. GET /api/v1/ai/history

**描述**: 获取会话历史

**请求参数**:
- `session_id` - 会话ID（必需）

**响应**:
```json
{
  "code": 200,
  "data": {
    "messages": [
      {
        "role": "user",
        "content": "今晚有空座吗",
        "timestamp": "2026-06-05T19:00:00"
      },
      {
        "role": "assistant",
        "content": "找到12个可用座位...",
        "timestamp": "2026-06-05T19:00:01"
      }
    ]
  }
}
```

### 3. POST /api/v1/ai/clear

**描述**: 清除会话历史

**请求体**:
```json
{
  "session_id": "会话ID"
}
```

---

## 配置说明

### 环境变量配置

创建 `.env` 文件（从 `.env.example` 复制）:

```bash
# LLM提供商选择
LLM_PROVIDER=mock          # mock | openai | claude

# OpenAI配置
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_BASE_URL=https://api.openai.com/v1

# 会话配置
SESSION_MAX_HISTORY=20
SESSION_EXPIRE_SECONDS=3600

# 限流配置
AI_RATE_LIMIT_PER_USER=30
AI_RATE_LIMIT_WINDOW=60

# 功能开关
LLM_INTENT_RECOGNITION=auto    # auto | true | false
USE_LLM_REPLY=false            # true | false
```

### 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `LLM_PROVIDER` | `mock` | LLM提供商：mock（测试）/ openai / claude |
| `OPENAI_API_KEY` | - | OpenAI API密钥 |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | 使用的模型 |
| `AI_RATE_LIMIT_PER_USER` | `30` | 每用户限流次数 |
| `AI_RATE_LIMIT_WINDOW` | `60` | 限流时间窗口（秒） |
| `LLM_INTENT_RECOGNITION` | `auto` | LLM意图识别：auto（自动）/ true（强制）/ false（禁用） |
| `USE_LLM_REPLY` | `false` | 是否使用LLM生成回复 |

---

## 测试指南

### 单元测试

```bash
# 运行所有AI模块测试
pytest tests/domain/ai/ -v

# 运行特定测试文件
pytest tests/domain/ai/test_intent_parser.py -v

# 查看测试覆盖率
pytest tests/domain/ai/ --cov=domain.ai --cov-report=html
```

### 测试用例

#### 1. 测试意图识别

```python
from domain.ai.intent_parser import parse_intent_by_keywords

result = parse_intent_by_keywords("今晚有空座吗")
print(result)
# {'intent_type': 'query_empty_seat', 'confidence': 0.7, 'slots': {...}}
```

#### 2. 测试多轮对话

```bash
# 第1轮
curl -X POST .../ai/chat -d '{"message": "我想找个座位"}'
# 返回 session_id

# 第2轮（使用相同session_id）
curl -X POST .../ai/chat -d '{"message": "明天晚上", "session_id": "xxx"}'

# 第3轮
curl -X POST .../ai/chat -d '{"message": "要靠窗的", "session_id": "xxx"}'
```

---

## 常见问题

### Q1: 如何启用OpenAI？

**A**: 
1. 安装依赖: `pip install openai`
2. 配置 `.env` 文件：
   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key
   ```
3. 重启服务

### Q2: 如何调整限流配置？

**A**: 在 `.env` 中设置：
```
AI_RATE_LIMIT_PER_USER=50      # 改为50次/分钟
AI_RATE_LIMIT_WINDOW=60
```

### Q3: 为什么LLM调用失败？

**A**: 检查以下几点：
1. API key是否正确
2. 网络连接是否正常
3. 查看日志中的错误信息
4. 检查OpenAI账户余额

系统会自动降级到关键词匹配，不影响基本功能。

### Q4: 如何清理会话缓存？

**A**: 会话会自动过期（默认1小时）。手动清理：
```bash
curl -X POST .../ai/clear -d '{"session_id": "xxx"}'
```

### Q5: 如何查看日志？

**A**: 日志输出到标准输出，使用JSON格式。查看：
```bash
# 启动服务时重定向日志
python app.py 2>&1 | tee ai.log

# 筛选AI模块日志
cat ai.log | grep '"name":"ai"'
```

---

## 性能指标

### 响应时间

| 场景 | 平均耗时 | 说明 |
|------|----------|------|
| 关键词匹配 | < 50ms | 本地处理 |
| LLM意图识别 | 500-2000ms | 依赖API |
| 完整对话 | < 3000ms | 含LLM调用 |

### 限流说明

- 默认: 30次/分钟/用户
- 超限返回: HTTP 429
- 响应头包含限流信息:
  - `X-RateLimit-Limit`: 限制次数
  - `X-RateLimit-Remaining`: 剩余次数
  - `X-RateLimit-Window`: 时间窗口

---

## 下一步

- 阅读 [部署指南](./AI助手模块部署指南.md)
- 查看 [开发计划](./AI助手模块开发计划.md)
- 参考 [架构设计](./自习座位预约系统软件架构设计方案-v2.md)
