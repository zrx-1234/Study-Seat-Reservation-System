<template>
  <div class="roles-page">
    <div class="toolbar">
      <el-button type="primary" @click="openDialog()">+ 新增角色</el-button>
    </div>

    <el-card v-loading="loading">
      <el-table :data="tableData" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="角色名称" width="150" />
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="permissions" label="权限" min-width="300">
          <template #default="{ row }">
            <el-tag
              v-for="perm in row.permissions"
              :key="perm.id"
              size="small"
              style="margin-right: 4px; margin-bottom: 4px;"
            >
              {{ perm.name }}
            </el-tag>
            <span v-if="!row.permissions || row.permissions.length === 0" class="text-gray">无权限</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="550px">
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" placeholder="角色名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="2" placeholder="角色描述" />
        </el-form-item>
        <el-form-item label="权限">
          <el-checkbox-group v-model="form.permission_ids">
            <el-checkbox
              v-for="perm in allPermissions"
              :key="perm.id"
              :label="perm.id"
            >
              {{ perm.name }}（{{ perm.code }}）
            </el-checkbox>
          </el-checkbox-group>
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
const allPermissions = ref([])
const pagination = reactive({
  total: 0,
  page: 1,
  per_page: 10
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增角色')
const formRef = ref(null)
const isEdit = ref(false)
const currentId = ref(null)
const form = reactive({
  name: '',
  description: '',
  permission_ids: []
})

const rules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }]
}

const fetchRoles = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/roles', {
      params: { page: pagination.page, per_page: pagination.per_page }
    })
    tableData.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (err) {
    console.error('获取角色列表失败', err)
  } finally {
    loading.value = false
  }
}

const fetchPermissions = async () => {
  try {
    const res = await request.get('/admin/permissions')
    allPermissions.value = res.data.items || []
  } catch (err) {
    console.error('获取权限列表失败', err)
  }
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchRoles()
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  dialogTitle.value = row ? '编辑角色' : '新增角色'
  currentId.value = row ? row.id : null
  if (row) {
    Object.assign(form, {
      name: row.name,
      description: row.description || '',
      permission_ids: row.permissions ? row.permissions.map(p => p.id) : []
    })
  } else {
    Object.assign(form, {
      name: '',
      description: '',
      permission_ids: []
    })
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    const payload = {
      name: form.name,
      description: form.description,
      permission_ids: form.permission_ids
    }
    if (isEdit.value) {
      await request.put(`/admin/roles/${currentId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/roles', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchRoles()
  } catch (err) {
    console.error('提交失败', err)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除角色 "${row.name}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.delete(`/admin/roles/${row.id}`)
    ElMessage.success('删除成功')
    fetchRoles()
  }).catch(() => {})
}

onMounted(() => {
  fetchRoles()
  fetchPermissions()
})
</script>

<style scoped>
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
