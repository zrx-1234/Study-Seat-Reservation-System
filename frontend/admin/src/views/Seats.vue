<template>
  <div class="seats-page">
    <!-- 自习室选择 -->
    <el-card class="search-card">
      <el-form :inline="true">
        <el-form-item label="选择自习室">
          <el-select v-model="selectedRoomId" placeholder="请选择自习室" @change="handleRoomChange" style="width: 300px;">
            <el-option
              v-for="room in roomList"
              :key="room.id"
              :label="room.name"
              :value="room.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterStatus" placeholder="全部" clearable style="width: 120px;" @change="fetchSeats">
            <el-option label="可用" value="available" />
            <el-option label="维护中" value="maintenance" />
            <el-option label="已注销" value="retired" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchSeats">刷新</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="openBatchDialog" :disabled="!selectedRoomId">+ 批量新增座位</el-button>
    </div>

    <!-- 座位列表 -->
    <el-card v-loading="loading">
      <el-empty v-if="!selectedRoomId" description="请先选择自习室" />
      <div v-else>
        <p class="room-info">
          自习室：<strong>{{ currentRoomName }}</strong>
          | 共 {{ pagination.total }} 个座位
        </p>
        <el-table :data="tableData" border stripe>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="seat_number" label="座位编号" width="120" />
          <el-table-column prop="has_window" label="靠窗" width="80">
            <template #default="{ row }">
              <el-tag type="success" v-if="row.has_window">是</el-tag>
              <el-tag type="info" v-else>否</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="has_plug" label="插座" width="80">
            <template #default="{ row }">
              <el-tag type="success" v-if="row.has_plug">有</el-tag>
              <el-tag type="info" v-else>无</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag type="success" v-if="row.status === 'available'">可用</el-tag>
              <el-tag type="warning" v-else-if="row.status === 'maintenance'">维护</el-tag>
              <el-tag type="info" v-else>已注销</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)" v-if="row.status !== 'retired'">注销</el-button>
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
      </div>
    </el-card>

    <!-- 批量新增对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量新增座位" width="500px">
      <el-form :model="batchForm" label-width="120px">
        <el-form-item label="座位前缀">
          <el-input v-model="batchForm.prefix" placeholder="例如：A" style="width: 120px;" />
        </el-form-item>
        <el-form-item label="起始编号">
          <el-input-number v-model="batchForm.start_number" :min="1" />
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="batchForm.count" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="靠窗">
          <el-switch v-model="batchForm.has_window" />
        </el-form-item>
        <el-form-item label="有插座">
          <el-switch v-model="batchForm.has_plug" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑座位" width="400px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="座位编号">
          <el-input v-model="editForm.seat_number" />
        </el-form-item>
        <el-form-item label="靠窗">
          <el-switch v-model="editForm.has_window" />
        </el-form-item>
        <el-form-item label="有插座">
          <el-switch v-model="editForm.has_plug" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status">
            <el-option label="可用" value="available" />
            <el-option label="维护中" value="maintenance" />
            <el-option label="已注销" value="retired" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEditSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request.js'

const roomList = ref([])
const selectedRoomId = ref(null)
const currentRoomName = computed(() => {
  const room = roomList.value.find(r => r.id === selectedRoomId.value)
  return room ? room.name : ''
})

const loading = ref(false)
const tableData = ref([])
const filterStatus = ref('')
const pagination = reactive({
  total: 0,
  page: 1,
  per_page: 20
})

const batchDialogVisible = ref(false)
const batchForm = reactive({
  prefix: 'A',
  start_number: 1,
  count: 10,
  has_window: false,
  has_plug: true
})

const editDialogVisible = ref(false)
const editForm = reactive({
  id: null,
  seat_number: '',
  has_window: false,
  has_plug: false,
  status: 'available'
})

const fetchRooms = async () => {
  try {
    const res = await request.get('/admin/rooms', { params: { per_page: 999 } })
    roomList.value = res.data.items || []
    if (roomList.value.length > 0 && !selectedRoomId.value) {
      selectedRoomId.value = roomList.value[0].id
      fetchSeats()
    }
  } catch (err) {
    console.error('获取自习室列表失败', err)
  }
}

const handleRoomChange = () => {
  pagination.page = 1
  fetchSeats()
}

const fetchSeats = async () => {
  if (!selectedRoomId.value) return
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    const res = await request.get(`/admin/rooms/${selectedRoomId.value}/seats`, { params })
    tableData.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (err) {
    console.error('获取座位列表失败', err)
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchSeats()
}

const openBatchDialog = () => {
  Object.assign(batchForm, {
    prefix: 'A',
    start_number: 1,
    count: 10,
    has_window: false,
    has_plug: true
  })
  batchDialogVisible.value = true
}

const handleBatchSubmit = async () => {
  try {
    await request.post(`/admin/rooms/${selectedRoomId.value}/seats`, {
      prefix: batchForm.prefix,
      start_number: batchForm.start_number,
      count: batchForm.count,
      has_window: batchForm.has_window,
      has_plug: batchForm.has_plug
    })
    ElMessage.success('批量创建成功')
    batchDialogVisible.value = false
    fetchSeats()
  } catch (err) {
    console.error('批量创建失败', err)
  }
}

const openEditDialog = (row) => {
  Object.assign(editForm, {
    id: row.id,
    seat_number: row.seat_number,
    has_window: row.has_window,
    has_plug: row.has_plug,
    status: row.status
  })
  editDialogVisible.value = true
}

const handleEditSubmit = async () => {
  try {
    await request.put(`/admin/seats/${editForm.id}`, {
      seat_number: editForm.seat_number,
      has_window: editForm.has_window,
      has_plug: editForm.has_plug,
      status: editForm.status
    })
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    fetchSeats()
  } catch (err) {
    console.error('更新失败', err)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要注销座位 "${row.seat_number}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.delete(`/admin/seats/${row.id}`)
    ElMessage.success('注销成功')
    fetchSeats()
  }).catch(() => {})
}

onMounted(() => {
  fetchRooms()
})
</script>

<style scoped>
.search-card {
  margin-bottom: 16px;
}

.toolbar {
  margin-bottom: 16px;
}

.room-info {
  margin-bottom: 12px;
  color: #606266;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
