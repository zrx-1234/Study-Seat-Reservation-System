<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>学生登录</h2>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="学号" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" style="width: 100%">登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request.js'

const router = useRouter()
const form = reactive({ username: '', password: '' })

async function handleLogin() {
  try {
    const res = await request.post('/student/auth/login', form)
    localStorage.setItem('student_token', res.data.access_token)
    localStorage.setItem('student_user', JSON.stringify(res.data.user))
    ElMessage.success('登录成功')
    router.push('/')
  } catch (err) {
    // 错误已在拦截器中提示
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f5f5f5;
}
.login-card {
  width: 360px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 20px;
}
</style>
