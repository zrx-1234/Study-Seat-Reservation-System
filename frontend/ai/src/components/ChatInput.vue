<template>
  <div class="chat-input-area">
    <div class="input-wrapper">
      <el-input
        v-model="inputText"
        placeholder="输入您的问题，如：今晚有空座吗？"
        @keyup.enter="handleSend"
        :disabled="disabled"
        clearable
        resize="none"
        class="chat-text-input"
      />
      <el-button
        type="primary"
        :icon="'Promotion'"
        @click="handleSend"
        :disabled="disabled || !inputText.trim()"
        :loading="loading"
        class="send-btn"
      >
        发送
      </el-button>
    </div>
    <div class="input-tips" v-if="!disabled">
      <span>按 Enter 发送</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send'])
const inputText = ref('')

const handleSend = () => {
  const text = inputText.value.trim()
  if (!text || props.loading || props.disabled) return

  emit('send', text)
  inputText.value = ''
}
</script>

<style scoped>
.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}

.input-wrapper {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chat-text-input {
  flex: 1;
}

.send-btn {
  flex-shrink: 0;
}

.input-tips {
  margin-top: 6px;
  font-size: 11px;
  color: #c0c4cc;
  text-align: right;
}
</style>
