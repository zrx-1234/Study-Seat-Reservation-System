<template>
  <div id="app">
    <el-container v-if="showLayout" class="layout">
      <el-header class="header">
        <div class="brand" @click="go('/')">
          <span class="logo">📚</span>
          <span class="title">自习座位预约</span>
        </div>
        <el-menu
          mode="horizontal"
          :default-active="activeIndex"
          class="nav"
          router
          :ellipsis="false"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/rooms">自习室</el-menu-item>
          <el-menu-item index="/seats">找座位</el-menu-item>
          <el-menu-item index="/reservations">我的预约</el-menu-item>
          <el-menu-item index="/checkin">签到</el-menu-item>
          <el-menu-item index="/violations">违约记录</el-menu-item>
        </el-menu>
        <div class="user-area">
          <el-badge :value="unread" :hidden="unread === 0" class="bell">
            <el-button text circle @click="go('/notifications')">
              <span style="font-size:18px">🔔</span>
            </el-button>
          </el-badge>
          <el-dropdown @command="onCommand">
            <span class="user-name">
              {{ userName }} <el-icon><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main">
        <router-view @refresh-unread="loadUnread" />
      </el-main>
    </el-container>

    <router-view v-else />
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowDown } from '@element-plus/icons-vue'
import { listNotifications } from './api/student.js'

const route = useRoute()
const router = useRouter()
const unread = ref(0)

const showLayout = computed(() => route.path !== '/login')
const activeIndex = computed(() => route.path)

const userName = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('student_user') || '{}').name || '同学'
  } catch (e) {
    return '同学'
  }
})

function go(path) {
  router.push(path)
}

function onCommand(cmd) {
  if (cmd === 'logout') {
    localStorage.removeItem('student_token')
    localStorage.removeItem('student_user')
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/')
  }
}

async function loadUnread() {
  if (!localStorage.getItem('student_token')) return
  try {
    const res = await listNotifications({ is_read: false, per_page: 1 })
    unread.value = res.data.unread_count ?? res.data.total ?? 0
  } catch (e) {
    // 静默
  }
}

watch(() => route.path, loadUnread)
onMounted(loadUnread)
</script>

<style>
* {
  box-sizing: border-box;
}
body {
  margin: 0;
}
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
  color: #1f2d3d;
}
.layout {
  min-height: 100vh;
  background: #f3f5f9;
}
.header {
  display: flex;
  align-items: center;
  background: #ffffff;
  border-bottom: 1px solid #ebeef5;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin-right: 32px;
  white-space: nowrap;
}
.brand .logo {
  font-size: 22px;
}
.brand .title {
  font-size: 18px;
  font-weight: 700;
  color: #2563eb;
}
.nav {
  flex: 1;
  border-bottom: none !important;
}
.user-area {
  display: flex;
  align-items: center;
  gap: 18px;
}
.user-name {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #475569;
}
.bell .el-button {
  height: 32px;
}
.main {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 16px;
}
</style>
