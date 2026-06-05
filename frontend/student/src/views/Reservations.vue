<template>
  <div>
    <h3 class="page-title">我的预约</h3>

    <el-tabs v-model="status" @tab-change="reload">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="已预约" name="reserved" />
      <el-tab-pane label="已签到" name="checked_in" />
      <el-tab-pane label="已完成" name="completed" />
      <el-tab-pane label="已取消" name="cancelled" />
      <el-tab-pane label="违约" name="violation" />
    </el-tabs>

    <el-card shadow="never" class="block">
      <el-empty v-if="!loading && items.length === 0" description="暂无预约记录" />
      <el-table v-else :data="items" v-loading="loading">
        <el-table-column prop="room_name" label="自习室" min-width="160" />
        <el-table-column prop="seat_number" label="座位" width="90" />
        <el-table-column label="时间" min-width="200">
          <template #default="{ row }">
            {{ fmt(row.start_time) }} ~ {{ fmtTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'reserved'"
              type="success"
              size="small"
              @click="openCheckIn(row)"
            >签到</el-button>
            <el-button
              v-if="row.status === 'reserved'"
              type="danger"
              size="small"
              plain
              @click="onCancel(row)"
            >取消</el-button>
            <span v-if="row.status !== 'reserved'" class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > perPage"
        class="pager"
        layout="prev, pager, next"
        :total="total"
        :page-size="perPage"
        :current-page="page"
        @current-change="onPage"
      />
    </el-card>

    <!-- 签到弹窗 -->
    <el-dialog v-model="checkInVisible" title="预约签到" width="380px">
      <p class="ci-info" v-if="currentRow">
        {{ currentRow.room_name }} · {{ currentRow.seat_number }}
      </p>
      <el-input v-model="code" placeholder="请输入签到码" maxlength="16" />
      <template #footer>
        <el-button @click="checkInVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="doCheckIn">确认签到</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listReservations, cancelReservation, checkIn } from '../api/student.js'
import { fmt, fmtTime, statusText, statusType } from '../utils/format.js'

const items = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 10
const status = ref('')
const loading = ref(false)

const checkInVisible = ref(false)
const currentRow = ref(null)
const code = ref('')
const submitting = ref(false)

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, per_page: perPage }
    if (status.value) params.status = status.value
    const res = await listReservations(params)
    items.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  load()
}

function onPage(p) {
  page.value = p
  load()
}

async function onCancel(row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入取消原因（可选）', '取消预约', {
      confirmButtonText: '确认取消',
      cancelButtonText: '再想想',
      inputPlaceholder: '临时有事…'
    })
    await cancelReservation(row.id, value)
    ElMessage.success('已取消预约')
    load()
  } catch (e) {
    // 用户放弃或拦截器已提示
  }
}

function openCheckIn(row) {
  currentRow.value = row
  code.value = ''
  checkInVisible.value = true
}

async function doCheckIn() {
  if (!code.value) {
    ElMessage.warning('请输入签到码')
    return
  }
  submitting.value = true
  try {
    await checkIn(currentRow.value.id, code.value)
    ElMessage.success('签到成功')
    checkInVisible.value = false
    load()
  } catch (e) {
    // 拦截器已提示
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.block {
  border-radius: 12px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
.muted {
  color: #c0c4cc;
}
.ci-info {
  margin: 0 0 12px;
  color: #475569;
}
</style>
