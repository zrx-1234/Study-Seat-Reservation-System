<template>
  <div class="rooms-page">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="名称/位置" clearable />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.room_type" placeholder="全部" clearable style="width: 120px;">
            <el-option label="公共" value="public" />
            <el-option label="院系" value="department" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="全部" clearable style="width: 120px;">
            <el-option label="启用" :value="true" />
            <el-option label="注销" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="openDialog()">+ 新增自习室</el-button>
    </div>

    <!-- 数据表格 -->
    <el-card>
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="名称" min-width="180" />
        <el-table-column prop="location" label="位置" min-width="150" />
        <el-table-column prop="capacity" label="容量" width="80" />
        <el-table-column prop="room_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.room_type === 'public'">公共</el-tag>
            <el-tag type="success" v-else>院系</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="所属院系" min-width="120">
          <template #default="{ row }">
            {{ row.department || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="open_time" label="开放时间" width="120" />
        <el-table-column prop="close_time" label="关闭时间" width="120" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag type="success" v-if="row.is_active">启用</el-tag>
            <el-tag type="info" v-else>注销</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">注销</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="自习室名称" />
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" placeholder="例如：理科图书馆 3楼" />
        </el-form-item>
        <el-form-item label="容量">
          <el-input-number v-model="form.capacity" :min="1" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.room_type">
            <el-radio label="public">公共</el-radio>
            <el-radio label="department">院系</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="所属院系" v-if="form.room_type === 'department'">
          <el-input v-model="form.department" placeholder="院系名称" />
        </el-form-item>
        <el-form-item label="开放时间">
          <el-time-picker v-model="form.open_time" placeholder="选择时间" format="HH:mm:ss" value-format="HH:mm:ss" />
        </el-form-item>
        <el-form-item label="关闭时间">
          <el-time-picker v-model="form.close_time" placeholder="选择时间" format="HH:mm:ss" value-format="HH:mm:ss" />
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
const searchForm = reactive({
  keyword: '',
  room_type: '',
  is_active: ''
})
const pagination = reactive({
  total: 0,
  page: 1,
  per_page: 10
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增自习室')
const formRef = ref(null)
const isEdit = ref(false)
const currentId = ref(null)
const form = reactive({
  name: '',
  location: '',
  capacity: 60,
  room_type: 'public',
  department: '',
  open_time: '07:00:00',
  close_time: '22:00:00'
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...searchForm
    }
    const res = await request.get('/admin/rooms', { params })
    tableData.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (err) {
    console.error('获取自习室列表失败', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const resetSearch = () => {
  searchForm.keyword = ''
  searchForm.room_type = ''
  searchForm.is_active = ''
  handleSearch()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const openDialog = (row = null) => {
  isEdit.value = !!row
  dialogTitle.value = row ? '编辑自习室' : '新增自习室'
  currentId.value = row ? row.id : null
  if (row) {
    Object.assign(form, {
      name: row.name,
      location: row.location || '',
      capacity: row.capacity,
      room_type: row.room_type,
      department: row.department || '',
      open_time: row.open_time,
      close_time: row.close_time
    })
  } else {
    Object.assign(form, {
      name: '',
      location: '',
      capacity: 60,
      room_type: 'public',
      department: '',
      open_time: '07:00:00',
      close_time: '22:00:00'
    })
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    const payload = { ...form }
    if (payload.room_type !== 'department') {
      payload.department = null
    }
    if (isEdit.value) {
      await request.put(`/admin/rooms/${currentId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/rooms', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (err) {
    console.error('提交失败', err)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要注销自习室 "${row.name}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.delete(`/admin/rooms/${row.id}`)
    ElMessage.success('注销成功')
    fetchData()
  }).catch(() => {})
}

onMounted(() => {
  fetchData()
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
</style>
