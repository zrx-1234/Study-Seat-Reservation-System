<template>
  <div class="users-page">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="用户名/姓名" clearable />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="searchForm.role_id" placeholder="全部" clearable style="width: 150px;">
            <el-option
              v-for="role in roleList"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="openDialog()">+ 新增管理员</el-button>
    </div>

    <el-card v-loading="loading">
      <el-table :data="tableData" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="department" label="院系" min-width="120">
          <template #default="{ row }">
            {{ row.department || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180">
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="roles" label="角色" min-width="150">
          <template #default="{ row }">
            <el-tag
              v-for="role in row.roles"
              :key="role.id"
              size="small"
              style="margin-right: 4px;"
            >
              {{ role.name }}
            </el-tag>
            <span v-if="!row.roles || row.roles.length === 0" class="text-gray">无角色</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag type="success" v-if="row.is_active !== false">正常</el-tag>
            <el-tag type="info" v-else>已禁用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">注销</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        background
        layout="prev, pager, next, total"
        :total="pagination.total"
        :page-size="pagination.per_page"
        :current-page="pagination.page"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="用户名" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" placeholder="密码" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="姓名" />
        </el-form-item>
        <el-form-item label="院系">
          <el-input v-model="form.department" placeholder="院系" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_ids" multiple placeholder="选择角色" style="width: 100%;">
            <el-option
              v-for="role in roleList"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request.js'

const loading = ref(false)
const tableData = ref([])
const roleList = ref([])
const searchForm = reactive({
  keyword: '',
  role_id: ''
})
const pagination = reactive({
  total: 0,
  page: 1,
  per_page: 10
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增管理员')
const formRef = ref(null)
const isEdit = ref(false)
const currentId = ref(null)
const form = reactive({
  username: '',
  password: '',
  name: '',
  department: '',
  email: '',
  role_ids: []
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...searchForm
    }
    const res = await request.get('/admin/users', { params })
    tableData.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (err) {
    console.error('获取用户列表失败', err)
  } finally {
    loading.value = false
  }
}

const fetchRoles = async () => {
  try {
    const res = await request.get('/admin/roles', { params: { per_page: 999 } })
    roleList.value = res.data.items || []
  } catch (err) {
    console.error('获取角色列表失败', err)
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchUsers()
}

const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.role_id = ''
  handleSearch()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchUsers()
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  dialogTitle.value = row ? '编辑管理员' : '新增管理员'
  currentId.value = row ? row.id : null
  if (row) {
    Object.assign(form, {
      username: row.username,
      password: '',
      name: row.name,
      department: row.department || '',
      email: row.email || '',
      role_ids: row.roles ? row.roles.map(r => r.id) : []
    })
  } else {
    Object.assign(form, {
      username: '',
      password: '',
      name: '',
      department: '',
      email: '',
      role_ids: []
    })
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    const payload = {
      username: form.username,
      name: form.name,
      department: form.department,
      email: form.email,
      role_ids: form.role_ids
    }
    if (isEdit.value) {
      await request.put(`/admin/users/${currentId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      payload.password = form.password
      await request.post('/admin/users', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (err) {
    console.error('提交失败', err)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要注销管理员 "${row.name}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.delete(`/admin/users/${row.id}`)
    ElMessage.success('注销成功')
    fetchUsers()
  }).catch(() => {})
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
})
</script>

<style scoped>
.search-card {
  margin-bottom: 16px;
}

.toolbar {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.text-gray {
  color: #909399;
}
</style>
