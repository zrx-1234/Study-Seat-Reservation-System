<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <span>📚 自习预约系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/">
          <span class="menu-icon">📊</span>
          <span>仪表盘</span>
        </el-menu-item>

        <el-sub-menu index="/resource">
          <template #title>
            <span class="menu-icon">🏢</span>
            <span>资源管理</span>
          </template>
          <el-menu-item index="/rooms">自习室管理</el-menu-item>
          <el-menu-item index="/seats">座位管理</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="/reservation">
          <template #title>
            <span class="menu-icon">📅</span>
            <span>预约管理</span>
          </template>
          <el-menu-item index="/reservations">预约记录</el-menu-item>
          <el-menu-item index="/violations">违约记录</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="/system">
          <template #title>
            <span class="menu-icon">⚙️</span>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/roles">角色权限</el-menu-item>
          <el-menu-item index="/users">管理员账号</el-menu-item>
          <el-menu-item index="/settings">系统配置</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-right">
          <span class="user-name">{{ userName }}</span>
          <el-dropdown @command="handleCommand">
            <span class="user-avatar">
              <el-avatar :size="32">{{ userName.charAt(0) }}</el-avatar>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => route.path)

const user = JSON.parse(localStorage.getItem('admin_user') || '{}')
const userName = computed(() => user.name || user.username || '管理员')

const handleCommand = (cmd) => {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
      ElMessage.success('已退出登录')
      router.push('/login')
    }).catch(() => {})
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid #1f2d3d;
  color: #fff;
}

.sidebar-menu {
  border-right: none;
}

.menu-icon {
  display: inline-block;
  width: 24px;
  text-align: center;
  margin-right: 5px;
}

.main-container {
  background-color: #f0f2f5;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  z-index: 10;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  font-size: 14px;
  color: #606266;
}

.user-avatar {
  cursor: pointer;
}

.main-content {
  padding: 20px;
  overflow-y: auto;
}
</style>
