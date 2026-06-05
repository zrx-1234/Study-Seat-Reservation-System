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
        <el-form-item class="action-row">
          <el-button @click="registerVisible = true">注册</el-button>
          <el-button type="primary" native-type="submit">登录</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-dialog v-model="registerVisible" title="学生注册" width="420px" destroy-on-close>
      <el-form :model="registerForm" label-width="72px">
        <el-form-item label="学号">
          <el-input v-model="registerForm.username" placeholder="请输入学号" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="registerForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="院系">
          <el-input v-model="registerForm.department" placeholder="例如：计算机学院（可选）" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="registerForm.email" placeholder="可选，用于通知" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="registerForm.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="registerVisible = false">取消</el-button>
        <el-button type="primary" :loading="registering" @click="handleRegister">注册并登录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, register as registerStudent } from '../api/student.js'

const router = useRouter()
const form = reactive({ username: '', password: '' })
const registerVisible = ref(false)
const registering = ref(false)
const registerForm = reactive({
  username: '',
  name: '',
  department: '',
  email: '',
  password: ''
})

async function handleLogin() {
  try {
    const res = await login(form)
    localStorage.setItem('student_token', res.data.access_token)
    localStorage.setItem('student_user', JSON.stringify(res.data.user))
    ElMessage.success('登录成功')
    router.push('/')
  } catch (err) {
    // 错误已在拦截器中提示
  }
}

async function handleRegister() {
  if (!registerForm.username || !registerForm.name || !registerForm.password) {
    ElMessage.warning('学号、姓名、密码为必填项')
    return
  }
  if (registerForm.password.length < 6) {
    ElMessage.warning('密码长度不能少于 6 位')
    return
  }

  registering.value = true
  try {
    const res = await registerStudent(registerForm)
    localStorage.setItem('student_token', res.data.access_token)
    localStorage.setItem('student_user', JSON.stringify(res.data.user))
    ElMessage.success('注册成功，已自动登录')
    registerVisible.value = false
    router.push('/')
  } catch (err) {
    // 错误已在拦截器中提示
  } finally {
    registering.value = false
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
.action-row :deep(.el-form-item__content) {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.action-row :deep(.el-button) {
  flex: 1;
}
</style>
