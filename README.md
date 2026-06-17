# Study-Seat-Reservation-System

Project for Software Process Management, 2026 Spring, Team 29

## AI / LLM 配置

后端 AI 助手默认使用 `mock` 模式，无需外部 API，适合开发、测试和 CI。若需要接入真实 OpenAI API，请在 `backend` 目录创建并配置 `.env`。

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Windows 可使用：

```bash
copy .env.example .env
```

默认 mock 模式：

```env
LLM_PROVIDER=mock
USE_LLM_REPLY=false
LLM_INTENT_RECOGNITION=auto
```

启用 OpenAI：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_BASE_URL=https://api.openai.com/v1
USE_LLM_REPLY=true
LLM_INTENT_RECOGNITION=auto
```

说明：

- `USE_LLM_REPLY=true`：在支持的场景下使用真实 LLM 生成更自然的回复。
- `LLM_INTENT_RECOGNITION=auto`：关键词低置信度时才调用 LLM；如需强制测试 LLM 意图识别，可设为 `true`。
- 不要提交 `.env` 或真实 API Key。

手动连通性测试：

```bash
python test_llm.py
```

正式聊天接口为 `POST /api/v1/ai/chat`，需要登录后携带 JWT。前端 AI 助手会调用该接口。
