<template>
  <div>
    <h3 class="page-title">快速签到</h3>

    <el-card shadow="never" class="block">
      <el-empty v-if="!loading && items.length === 0" description="暂无待签到的预约" />
      <div v-else v-loading="loading" class="list">
        <div v-for="row in items" :key="row.id" class="ci-item">
          <div class="ci-left">
            <div class="ci-room">{{ row.room_name }} · {{ row.seat_number }}</div>
            <div class="ci-time">{{ fmt(row.start_time) }} ~ {{ fmtTime(row.end_time) }}</div>
          </div>
          <div class="ci-right">
            <el-input
              v-model="codes[row.id]"
              placeholder="签到码"
              maxlength="16"
              style="width: 160px"
            />
            <el-button type="success" :loading="loadingId === row.id" @click="doCheckIn(row)">
              签到
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listReservations, checkIn } from '../api/student.js'
import { fmt, fmtTime } from '../utils/format.js'

const items = ref([])
const codes = reactive({})
const loading = ref(false)
const loadingId = ref(null)

async function load() {
  loading.value = true
  try {
    const res = await listReservations({ status: 'reserved', per_page: 50 })
    items.value = res.data.items
  } finally {
    loading.value = false
  }
}

async function doCheckIn(row) {
  const code = codes[row.id]
  if (!code) {
    ElMessage.warning('请输入签到码')
    return
  }
  loadingId.value = row.id
  try {
    await checkIn(row.id, code)
    ElMessage.success('签到成功')
    load()
  } catch (e) {
    // 拦截器已提示
  } finally {
    loadingId.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.block {
  border-radius: 12px;
}
.ci-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 4px;
  border-bottom: 1px solid #f0f2f5;
}
.ci-item:last-child {
  border-bottom: none;
}
.ci-room {
  font-weight: 700;
}
.ci-time {
  color: #6b7280;
  font-size: 13px;
  margin-top: 4px;
}
.ci-right {
  display: flex;
  gap: 10px;
}
</style>
