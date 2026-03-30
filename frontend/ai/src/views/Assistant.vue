<template>
  <div class="assistant-container">
    <div class="chat-header">
      <h3>智能助手</h3>
    </div>

    <div class="chat-messages" ref="messagesRef">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.type]"
      >
        <div class="message-content">{{ msg.content }}</div>
      </div>
    </div>

    <div class="chat-suggestions" v-if="suggestions.length">
      <span
        v-for="(suggestion, index) in suggestions"
        :key="index"
        class="suggestion-tag"
        @click="sendMessage(suggestion)"
      >
        {{ suggestion }}
      </span>
    </div>

    <div class="chat-input">
      <input
        v-model="inputMessage"
        placeholder="输入您的问题..."
        @keyup.enter="sendMessage(inputMessage)"
      />
      <button @click="sendMessage(inputMessage)">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const messagesRef = ref(null)
const inputMessage = ref('')
const messages = ref([])
const suggestions = ref([])

// TODO: 接入API
const API_BASE = '/api/ai/assistant'

const sendMessage = async (text) => {
  if (!text.trim()) return

  // 添加用户消息
  messages.value.push({
    type: 'user',
    content: text
  })

  inputMessage.value = ''
  scrollToBottom()

  try {
    const response = await axios.post(`${API_BASE}/chat`, {
      message: text,
      user_id: getCurrentUserId()
    })

    const { reply, suggestions: sug } = response.data.data
    messages.value.push({
      type: 'assistant',
      content: reply
    })
    suggestions.value = sug || []
  } catch (error) {
    messages.value.push({
      type: 'assistant',
      content: '抱歉，服务出错了，请稍后再试。'
    })
  }

  scrollToBottom()
}

const scrollToBottom = () => {
  setTimeout(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  }, 100)
}

const getCurrentUserId = () => {
  // TODO: 获取当前登录用户ID
  return null
}

const loadHistory = async () => {
  // TODO: 加载对话历史
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.assistant-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 600px;
  margin: 0 auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.chat-header {
  padding: 12px 16px;
  background: #409eff;
  color: white;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
}

.chat-messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  min-height: 300px;
}

.message {
  margin-bottom: 12px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.5;
}

.message.user .message-content {
  background: #409eff;
  color: white;
}

.message.assistant .message-content {
  background: #f0f0f0;
  color: #333;
}

.chat-suggestions {
  padding: 8px 16px;
  border-top: 1px solid #eee;
}

.suggestion-tag {
  display: inline-block;
  padding: 4px 12px;
  margin-right: 8px;
  margin-bottom: 4px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 16px;
  font-size: 12px;
  cursor: pointer;
}

.suggestion-tag:hover {
  background: #409eff;
  color: white;
}

.chat-input {
  display: flex;
  padding: 12px 16px;
  border-top: 1px solid #ddd;
}

.chat-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 4px;
  outline: none;
}

.chat-input input:focus {
  border-color: #409eff;
}

.chat-input button {
  margin-left: 10px;
  padding: 10px 20px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.chat-input button:hover {
  background: #66b1ff;
}
</style>
