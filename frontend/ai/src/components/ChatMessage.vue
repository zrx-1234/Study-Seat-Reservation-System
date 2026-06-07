<template>
  <div :class="['message-wrapper', message.type]">
    <div class="message-avatar">
      <el-avatar :size="32">{{ message.type === 'user' ? '我' : 'AI' }}</el-avatar>
    </div>
    <div class="message-body">
      <!-- 文本内容 -->
      <div class="message-bubble" v-if="message.content">
        <div class="message-text" v-html="formatText(message.content)"></div>
      </div>

      <!-- 加载动画 -->
      <div class="message-bubble loading-bubble" v-if="message.loading">
        <span class="loading-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </span>
      </div>

      <!-- 座位推荐卡片 -->
      <div class="message-cards" v-if="message.action === 'search_seats' && message.payload">
        <el-card
          v-for="seat in (message.payload.recommendations || [])"
          :key="seat.seat_id"
          class="seat-card"
          shadow="hover"
        >
          <div class="seat-card-header">
            <span class="seat-number">{{ seat.seat_number }}</span>
            <el-tag size="small" type="success" v-if="seat.has_window">靠窗</el-tag>
            <el-tag size="small" type="warning" v-if="seat.has_plug">有插座</el-tag>
          </div>
          <div class="seat-card-body">
            <p>{{ seat.room_name }}</p>
            <p class="text-secondary">{{ seat.room_location }}</p>
          </div>
          <div class="seat-card-footer">
            <span class="text-secondary">可用时段:</span>
            <el-tag
              v-for="slot in seat.available_slots"
              :key="slot"
              size="small"
              type="info"
              class="slot-tag"
            >
              {{ slot }}
            </el-tag>
          </div>
        </el-card>
      </div>

      <!-- 预约记录卡片 -->
      <div class="message-cards" v-if="message.action === 'show_reservations' && message.payload">
        <el-card
          v-for="res in (message.payload.reservations || [])"
          :key="res.id"
          class="reservation-card"
          shadow="hover"
        >
          <div class="reservation-header">
            <span class="seat-number">{{ res.seat_number }}</span>
            <el-tag size="small" :type="res.status === 'reserved' ? 'success' : 'info'">
              {{ statusLabel(res.status) }}
            </el-tag>
          </div>
          <div class="reservation-body">
            <p>{{ res.room_name }}</p>
            <p class="text-secondary">{{ res.start_time }} ~ {{ res.end_time }}</p>
          </div>
        </el-card>
      </div>

      <!-- 时间戳 -->
      <div class="message-time">{{ message.timestamp || '' }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const formatText = (text) => {
  if (!text) return ''
  return text.replace(/\n/g, '<br/>')
}

const statusLabel = (status) => {
  const labels = {
    'reserved': '已预约',
    'checked_in': '已签到',
    'completed': '已完成',
    'cancelled': '已取消',
    'defaulted': '违约'
  }
  return labels[status] || status
}
</script>

<style scoped>
.message-wrapper {
  display: flex;
  margin-bottom: 16px;
  gap: 10px;
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.message-body {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message-wrapper.user .message-body {
  align-items: flex-end;
}

.message-wrapper.assistant .message-body {
  align-items: flex-start;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.message-wrapper.user .message-bubble {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-wrapper.assistant .message-bubble {
  background: #f0f2f5;
  color: #333;
  border-bottom-left-radius: 4px;
}

.loading-bubble {
  padding: 12px 18px;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
.dot:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 卡片样式 */
.message-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.seat-card, .reservation-card {
  max-width: 280px;
}

.seat-card-header, .reservation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.seat-number {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.seat-card-body p, .reservation-body p {
  margin: 2px 0;
  font-size: 13px;
}

.text-secondary {
  color: #909399;
  font-size: 12px;
}

.seat-card-footer {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.slot-tag {
  margin: 2px;
}

.message-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 2px;
}
</style>
