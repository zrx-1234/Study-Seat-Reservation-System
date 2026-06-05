<template>
  <div>
    <div class="hero">
      <div>
        <h2>你好，{{ profile.name || '同学' }} 👋</h2>
        <p class="sub">{{ profile.department }} · {{ profile.username }}</p>
      </div>
      <el-button type="primary" size="large" @click="$router.push('/seats')">
        立即找座位
      </el-button>
    </div>

    <el-row :gutter="16" class="stats">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/reservations')">
          <div class="stat-value">{{ profile.active_reservations ?? 0 }}</div>
          <div class="stat-label">进行中的预约</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/violations')">
          <div class="stat-value warn">{{ profile.total_violations ?? 0 }}</div>
          <div class="stat-label">累计违约</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card" @click="$router.push('/notifications')">
          <div class="stat-value">{{ unread }}</div>
          <div class="stat-label">未读通知</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="block" shadow="never">
      <template #header>
        <div class="block-header">
          <span>近期预约</span>
          <el-link type="primary" @click="$router.push('/reservations')">查看全部</el-link>
        </div>
      </template>
      <el-empty v-if="!loading && reservations.length === 0" description="暂无预约，去找个座位吧" />
      <el-table v-else :data="reservations" v-loading="loading">
        <el-table-column prop="room_name" label="自习室" />
        <el-table-column prop="seat_number" label="座位" width="90" />
        <el-table-column label="时间">
          <template #default="{ row }">
            {{ fmt(row.start_time) }} ~ {{ fmtTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProfile, listReservations, listNotifications } from '../api/student.js'
import { fmt, fmtTime, statusText, statusType } from '../utils/format.js'

const profile = ref({})
const reservations = ref([])
const unread = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const [p, r, n] = await Promise.all([
      getProfile(),
      listReservations({ page: 1, per_page: 5 }),
      listNotifications({ is_read: false, per_page: 1 })
    ])
    profile.value = p.data
    reservations.value = r.data.items
    unread.value = n.data.unread_count ?? n.data.total ?? 0
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #2563eb, #4f8cff);
  color: #fff;
  border-radius: 14px;
  padding: 28px 32px;
  margin-bottom: 20px;
}
.hero h2 {
  margin: 0;
}
.hero .sub {
  margin: 6px 0 0;
  opacity: 0.85;
}
.stats {
  margin-bottom: 20px;
}
.stat-card {
  text-align: center;
  cursor: pointer;
  border-radius: 12px;
}
.stat-value {
  font-size: 34px;
  font-weight: 800;
  color: #2563eb;
}
.stat-value.warn {
  color: #e6a23c;
}
.stat-label {
  color: #6b7280;
  margin-top: 6px;
}
.block {
  border-radius: 12px;
}
.block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
