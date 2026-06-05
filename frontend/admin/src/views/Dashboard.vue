<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-title">自习室总数</div>
          <div class="stat-value">{{ stats.total_rooms }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-title">座位总数</div>
          <div class="stat-value">{{ stats.total_seats }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-title">今日预约</div>
          <div class="stat-value">{{ stats.today_reservations }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-title">今日违约</div>
          <div class="stat-value" style="color: #f56c6c;">{{ stats.today_violations }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行统计 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-title">活跃用户数</div>
          <div class="stat-value" style="color: #67c23a;">{{ stats.active_users }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-row style="margin-top: 20px;">
      <el-col :span="24">
        <el-card title="快捷入口">
          <template #header>
            <span>快捷入口</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="4">
              <el-button type="primary" plain @click="$router.push('/rooms')">自习室管理</el-button>
            </el-col>
            <el-col :span="4">
              <el-button type="success" plain @click="$router.push('/seats')">座位管理</el-button>
            </el-col>
            <el-col :span="4">
              <el-button type="warning" plain @click="$router.push('/reservations')">预约记录</el-button>
            </el-col>
            <el-col :span="4">
              <el-button type="danger" plain @click="$router.push('/violations')">违约记录</el-button>
            </el-col>
            <el-col :span="4">
              <el-button type="info" plain @click="$router.push('/users')">管理员账号</el-button>
            </el-col>
            <el-col :span="4">
              <el-button plain @click="$router.push('/settings')">系统配置</el-button>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../utils/request.js'

const stats = ref({
  total_rooms: 0,
  total_seats: 0,
  today_reservations: 0,
  today_violations: 0,
  active_users: 0
})

const fetchStats = async () => {
  try {
    const res = await request.get('/admin/dashboard/stats')
    stats.value = res.data || stats.value
  } catch (err) {
    console.error('获取统计数据失败', err)
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.stat-card {
  text-align: center;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}
</style>
