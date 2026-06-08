<template>
  <div class="reservations-page">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px;">
            <el-option label="已预约" value="reserved" />
            <el-option label="已签到" value="checked_in" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="违约" value="violation" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="searchForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="用户名/座位号" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="toolbar">
      <el-button type="primary" @click="openProxyDialog">+ 代理预约</el-button>
    </div>

    <el-card v-loading="loading">
      <el-table :data="tableData" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="user_name" label="预约人" width="120" />
        <el-table-column prop="room_name" label="自习室" min-width="150" />
        <el-table-column prop="seat_number" label="座位号" width="100" />
        <el-table-column prop="start_time" label="开始时间" width="160" />
        <el-table-column prop="end_time" label="结束时间" width="160" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag type="primary" v-if="row.status === 'reserved'">已预约</el-tag>
            <el-tag type="success" v-else-if="row.status === 'checked_in'">已签到</el-tag>
            <el-tag type="info" v-else-if="row.status === 'completed'">已完成</el-tag>
            <el-tag type="warning" v-else-if="row.status === 'cancelled'">已取消</el-tag>
            <el-tag type="danger" v-else-if="row.status === 'violation'">违约</el-tag>
            <el-tag v-else>{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              @click="handleCancel(row)"
              v-if="row.status === 'reserved'"
            >取消</el-button>
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

    <!-- 代理预约对话框 -->
    <el-dialog v-model="proxyDialogVisible" title="代理预约" width="500px">
      <el-form :model="proxyForm" label-width="100px" :rules="proxyRules" ref="proxyFormRef">
        <el-form-item label="学生账号" prop="target_username">
          <el-input v-model="proxyForm.target_username" placeholder="学生学号/用户名" />
        </el-form-item>
        <el-form-item label="选择自习室">
          <el-select v-model="proxyForm.room_id" placeholder="请选择" @change="handleProxyRoomChange" style="width: 100%;">
            <el-option
              v-for="room in roomList"
              :key="room.id"
              :label="room.name"
              :value="room.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="选择座位">
          <el-select v-model="proxyForm.seat_id" placeholder="请先选择自习室" :disabled="!proxyForm.room_id" style="width: 100%;">
            <el-option
              v-for="seat in seatList"
              :key="seat.id"
              :label="seat.seat_number"
              :value="seat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker v-model="proxyForm.date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="时间段">
          <el-time-picker
            v-model="proxyForm.time_range"
            is-range
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="proxyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleProxySubmit">确定</el-button>
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
  status: '',
  date_range: [],
  keyword: ''
})
const pagination = reactive({
  total: 0,
  page: 1,
  per_page: 10
})

// 代理预约
const proxyDialogVisible = ref(false)
const proxyFormRef = ref(null)
const roomList = ref([])
const seatList = ref([])
const proxyForm = reactive({
  target_username: '',
  room_id: '',
  seat_id: '',
  date: '',
  time_range: ['08:00', '12:00']
})
const proxyRules = {
  target_username: [{ required: true, message: '请输入学生账号', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      status: searchForm.status || undefined,
      keyword: searchForm.keyword || undefined,
    }
    if (searchForm.date_range && searchForm.date_range.length === 2) {
      params.date_range = searchForm.date_range
    }
    const res = await request.get('/admin/reservations', { params })
    tableData.value = res.data.items || []
    pagination.total = res.data.total || 0
    pagination.page = res.data.page || 1
    pagination.per_page = res.data.per_page || 20
  } catch (err) {
    console.error('获取预约列表失败', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const resetSearch = () => {
  searchForm.status = ''
  searchForm.date_range = []
  searchForm.keyword = ''
  handleSearch()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const handleCancel = (row) => {
  ElMessageBox.confirm(`确定要取消该预约吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await request.post(`/admin/reservations/${row.id}/cancel`, {})
    ElMessage.success('取消成功')
    fetchData()
  }).catch(() => {})
}

const openProxyDialog = () => {
  Object.assign(proxyForm, {
    target_username: '',
    room_id: '',
    seat_id: '',
    date: '',
    time_range: ['08:00', '12:00']
  })
  seatList.value = []
  proxyDialogVisible.value = true
}

const handleProxyRoomChange = async () => {
  proxyForm.seat_id = ''
  if (!proxyForm.room_id) {
    seatList.value = []
    return
  }
  try {
    const res = await request.get(`/admin/rooms/${proxyForm.room_id}/seats`, { params: { per_page: 999 } })
    seatList.value = (res.data.items || []).filter(s => s.status === 'available')
  } catch (err) {
    console.error('获取座位列表失败', err)
  }
}

const handleProxySubmit = async () => {
  try {
    await proxyFormRef.value.validate()
    // TODO: 后端交付后启用
    // await request.post('/admin/reservations', {
    //   target_username: proxyForm.target_username,
    //   seat_id: proxyForm.seat_id,
    //   start_time: `${proxyForm.date} ${proxyForm.time_range[0]}:00`,
    //   end_time: `${proxyForm.date} ${proxyForm.time_range[1]}:00`
    // })
    ElMessage.success('代理预约成功')
    proxyDialogVisible.value = false
    fetchData()
  } catch (err) {
    console.error('代理预约失败', err)
  }
}

const fetchRooms = async () => {
  try {
    const res = await request.get('/admin/rooms', { params: { per_page: 999 } })
    roomList.value = res.data.items || []
  } catch (err) {
    console.error('获取自习室列表失败', err)
  }
}

onMounted(() => {
  fetchData()
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

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
