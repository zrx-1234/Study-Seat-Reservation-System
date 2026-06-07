<template>
  <div class="assistant-page">
    <!-- 顶部栏 -->
    <div class="chat-header">
      <div class="header-left">
        <h3>AI 智能助手</h3>
        <el-tag size="small" type="info" v-if="sessionId" class="session-badge">
          会话已连接
        </el-tag>
      </div>
      <div class="header-right">
        <el-button text size="small" @click="handleClearSession" :disabled="!sessionId || messages.length === 0">
          清除会话
        </el-button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-body" ref="bodyRef">
      <div class="chat-messages">
        <div v-if="messages.length === 0 && !loading" class="welcome-hint">
          <div class="welcome-icon">
            <el-icon :size="48"><ChatDotRound /></el-icon>
          </div>
          <p class="welcome-title">你好，我是自习室预约助手</p>
          <p class="welcome-desc">可以帮你查询空座位、管理预约，试试问我：</p>
          <div class="welcome-suggestions">
            <span
              v-for="s in quickPrompts"
              :key="s"
              class="prompt-chip"
              @click="sendMessage(s)"
            >{{ s }}</span>
          </div>
        </div>

        <ChatMessage
          v-for="(msg, idx) in messages"
          :key="idx"
          :message="msg"
        />

        <!-- 加载中 -->
        <ChatMessage
          v-if="loading"
          :message="{ type: 'assistant', loading: true }"
        />
      </div>
    </div>

    <!-- 快捷提示（有消息后显示在输入框上方） -->
    <div class="quick-bar" v-if="messages.length > 0 && !loading">
      <span
        v-for="s in quickPrompts"
        :key="s"
        class="quick-chip"
        @click="sendMessage(s)"
      >{{ s }}</span>
    </div>

    <!-- 输入区域 -->
    <ChatInput
      :loading="loading"
      :disabled="false"
      @send="sendMessage"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'
import request from '../utils/request.js'
import ChatMessage from '../components/ChatMessage.vue'
import ChatInput from '../components/ChatInput.vue'

const bodyRef = ref(null)
const messages = ref([])
const sessionId = ref(null)
const loading = ref(false)

const quickPrompts = [
  '今晚有空座吗？',
  '帮我找靠窗的座位',
  '我的预约',
  '有哪些自习室？'
]

const sendMessage = async (text) => {
  if (!text.trim() || loading.value) return

  // 添加用户消息
  const timestamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  messages.value.push({
    type: 'user',
    content: text,
    timestamp
  })

  loading.value = true
  await nextTick()
  scrollToBottom()

  try {
    const body = { message: text }
    if (sessionId.value) {
      body.session_id = sessionId.value
    }

    const res = await request.post('/ai/chat', body)
    const { reply, action, payload, session_id } = res.data

    sessionId.value = session_id

    messages.value.push({
      type: 'assistant',
      content: reply,
      action: action || 'text',
      payload: payload || {},
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
  } catch (err) {
    messages.value.push({
      type: 'assistant',
      content: '抱歉，服务出错了，请稍后重试。',
      action: 'error',
      payload: {},
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  if (bodyRef.value) {
    bodyRef.value.scrollTop = bodyRef.value.scrollHeight
  }
}

const handleClearSession = async () => {
  try {
    await ElMessageBox.confirm('确定要清除当前会话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    if (sessionId.value) {
      await request.post('/ai/clear', { session_id: sessionId.value })
    }
    messages.value = []
    sessionId.value = null
    ElMessage.success('会话已清除')
  } catch (err) {
    if (err !== 'cancel') {
      // 直接清除本地数据
      messages.value = []
      sessionId.value = null
      ElMessage.success('会话已清除')
    }
  }
}

const loadHistory = async () => {
  // 页面加载时不自动加载历史（需要 sessionId）
  // 如果已有 sessionId（存在 localStorage），尝试恢复
  const savedSessionId = localStorage.getItem('ai_session_id')
  if (!savedSessionId) return

  try {
    const res = await request.get('/ai/history', { params: { session_id: savedSessionId } })
    const historyMessages = res.data?.messages || []

    if (historyMessages.length > 0) {
      sessionId.value = savedSessionId
      messages.value = historyMessages.map(msg => ({
        type: msg.role,
        content: msg.content,
        timestamp: msg.timestamp ? msg.timestamp.substring(11, 16) : ''
      }))

      await nextTick()
      scrollToBottom()
    }
  } catch (err) {
    localStorage.removeItem('ai_session_id')
  }
}

// 监听 sessionId 变化，持久化到 localStorage
watch(sessionId, (newVal) => {
  if (newVal) {
    localStorage.setItem('ai_session_id', newVal)
  } else {
    localStorage.removeItem('ai_session_id')
  }
})

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.assistant-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 680px;
  margin: 0 auto;
  background: #fff;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
}

/* 顶部栏 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: #409eff;
  color: #fff;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-header h3 {
  margin: 0;
  font-size: 17px;
}

.session-badge {
  font-size: 11px;
}

.header-right .el-button {
  color: #fff;
}

.header-right .el-button:hover {
  background: rgba(255, 255, 255, 0.15);
}

.header-right .el-button.is-disabled {
  color: rgba(255, 255, 255, 0.4);
}

/* 消息区 */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
  background: #fafbfc;
}

.chat-messages {
  display: flex;
  flex-direction: column;
}

/* 欢迎提示 */
.welcome-hint {
  text-align: center;
  padding: 40px 20px;
}

.welcome-icon {
  color: #409eff;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px;
}

.welcome-desc {
  font-size: 14px;
  color: #909399;
  margin: 0 0 20px;
}

.welcome-suggestions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.prompt-chip {
  display: inline-block;
  padding: 8px 18px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #d9ecff;
}

.prompt-chip:hover {
  background: #409eff;
  color: #fff;
}

/* 快捷栏 */
.quick-bar {
  padding: 8px 16px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.quick-chip {
  display: inline-block;
  padding: 4px 12px;
  background: #f0f5ff;
  color: #409eff;
  border-radius: 14px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #d9ecff;
}

.quick-chip:hover {
  background: #409eff;
  color: #fff;
}

/* 响应式 */
@media (max-width: 480px) {
  .assistant-page {
    max-width: 100%;
    height: 100dvh;
  }

  .chat-header {
    padding: 10px 14px;
  }

  .chat-header h3 {
    font-size: 15px;
  }

  .chat-body {
    padding: 12px 10px;
  }

  .prompt-chip {
    font-size: 13px;
    padding: 6px 14px;
  }
}
</style>
