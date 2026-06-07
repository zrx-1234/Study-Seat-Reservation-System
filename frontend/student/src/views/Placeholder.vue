<template>
  <div class="placeholder-page">
    <el-card class="placeholder-card">
      <div class="emoji">🚧</div>
      <h2>{{ pageName }}</h2>
      <p class="status">该功能正在开发中</p>
      <p class="hint">学生组同学正在加紧开发，敬请期待！</p>

      <div class="meta">
        <p><strong>负责小组：</strong>系统-学生部分（成员C、成员D）</p>
        <p><strong>预计完成：</strong>Sprint 1（第 1-2 周）</p>
      </div>

      <el-button type="primary" @click="$router.push('/login')">返回登录</el-button>
      <el-button @click="$router.back()">返回上一页</el-button>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const pageName = computed(() => {
  const map = {
    Home: '我的主页',
    Rooms: '自习室列表',
    Seats: '座位搜索',
    Reservations: '我的预约',
    CheckIn: '签到',
    Assistant: 'AI 助手'
  }
  return map[route.name] || route.name || '此页面'
})
</script>

<style scoped>
.placeholder-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

.placeholder-card {
  width: 100%;
  max-width: 500px;
  text-align: center;
  padding: 20px;
}

.emoji {
  font-size: 64px;
  margin-bottom: 16px;
}

h2 {
  margin: 0 0 12px;
  color: #303133;
}

.status {
  color: #e6a23c;
  font-size: 16px;
  font-weight: 500;
  margin: 8px 0;
}

.hint {
  color: #909399;
  margin: 8px 0 24px;
}

.meta {
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 6px;
  margin: 20px 0;
  text-align: left;
  font-size: 14px;
  color: #606266;
}

.meta p {
  margin: 4px 0;
}
</style>
