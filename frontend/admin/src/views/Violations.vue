<template>
  <div class="violations-page">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
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
          <el-button type="success" @click="handleExport">导出 CSV</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="tableData" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="user_name" label="学生" width="120" />
        <el-table-column prop="room_name" label="自习室" min-width="150" />
        <el-table-column prop="seat_number" label="座位号" width="100" />
        <el-table-column prop="violation_time" label="违约时间" width="160" />
        <el-table-column prop="reason" label="原因" min-width="150">
          <template #default="{ row }">
            {{ row.reason || '超时未签到' }}
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request.js'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({
  date_range: [],
  keyword: ''
})
const pagination = reactive({
  total: 0,
  page: 1,
  per_page: 10
})

// Mock 数据先行，等后端交付后替换为真实请求
const fetchData = async () => {
  loading.value = true
  try {
    // TODO: 后端交付后替换为真实接口
    // const res = await request.get('/admin/violations', {
    //   params: { page: pagination.page, per_page: pagination.per_page, ...searchForm }
    // })
    const mockData = [
      {
        id: 1,
        user_name: '张三',
        room_name: '理科图书馆 301',
        seat_number: 'A01',
        violation_time: '2026-06-04 09:15:00',
        reason: '超时未签到'
      },
      {
        id: 2,
        user_name: '李四',
        room_name: '计算机学院 201',
        seat_number: 'C02',
        violation_time: '2026-06-03 14:20:00',
        reason: '超时未签到'
      }
    ]
    tableData.value = mockData
    pagination.total = mockData.length
  } catch (err) {
    console.error('获取违约记录失败', err)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const resetSearch = () => {
  searchForm.date_range = []
  searchForm.keyword = ''
  handleSearch()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const handleExport = () => {
  // TODO: 后端交付后替换为真实导出接口
  // window.open('/api/v1/admin/violations/export?format=csv')
  ElMessage.info('导出功能将在后端交付后启用')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.search-card {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
