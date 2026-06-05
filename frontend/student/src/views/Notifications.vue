<template>
  <div>
    <div class="head">
      <h3 class="page-title">通知中心</h3>
      <el-button type="primary" plain :disabled="unread === 0" @click="readAll">
        全部已读
      </el-button>
    </div>

    <el-card shadow="never" class="block">
      <el-empty v-if="!loading && items.length === 0" description="暂无通知" />
      <div v-else v-loading="loading" class="list">
        <div
          v-for="n in items"
          :key="n.id"
          class="notif"
          :class="{ unread: !n.is_read }"
          @click="read(n)"
        >
          <div class="dot" v-if="!n.is_read" />
          <div class="content">
            <div class="top">
              <el-tag size="small" :type="tagType(n.type)">{{ notifText(n.type) }}</el-tag>
              <span class="time">{{ fmt(n.created_at) }}</span>
            </div>
            <div class="text">{{ n.content }}</div>
          </div>
        </div>
      </div>

      <el-pagination
        v-if="total > perPage"
        class="pager"
        layout="prev, pager, next"
        :total="total"
        :page-size="perPage"
        :current-page="page"
        @current-change="onPage"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listNotifications, markNotificationRead, markAllNotificationsRead } from '../api/student.js'
import { fmt, notifText } from '../utils/format.js'

const emit = defineEmits(['refresh-unread'])
const items = ref([])
const total = ref(0)
const unread = ref(0)
const page = ref(1)
const perPage = 15
const loading = ref(false)

function tagType(type) {
  return { violation: 'danger', cancel: 'info', remind: 'primary', check_in_alert: 'warning', system: 'success' }[type] || 'info'
}

async function load() {
  loading.value = true
  try {
    const res = await listNotifications({ page: page.value, per_page: perPage })
    items.value = res.data.items
    total.value = res.data.total
    unread.value = res.data.unread_count ?? 0
  } finally {
    loading.value = false
  }
}

function onPage(p) {
  page.value = p
  load()
}

async function read(n) {
  if (n.is_read) return
  await markNotificationRead(n.id)
  n.is_read = true
  unread.value = Math.max(0, unread.value - 1)
  emit('refresh-unread')
}

async function readAll() {
  await markAllNotificationsRead()
  ElMessage.success('已全部标记为已读')
  load()
  emit('refresh-unread')
}

onMounted(load)
</script>

<style scoped>
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.block {
  border-radius: 12px;
}
.notif {
  display: flex;
  gap: 10px;
  padding: 14px 6px;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
}
.notif:last-child {
  border-bottom: none;
}
.notif.unread {
  background: #f5f9ff;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
  margin-top: 8px;
  flex-shrink: 0;
}
.notif:not(.unread) .content {
  margin-left: 18px;
}
.content {
  flex: 1;
}
.top {
  display: flex;
  align-items: center;
  gap: 10px;
}
.time {
  color: #9aa4b2;
  font-size: 12px;
}
.text {
  margin-top: 6px;
  color: #374151;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
