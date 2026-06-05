<template>
  <div>
    <h3 class="page-title">违约记录</h3>

    <el-card shadow="never" class="block">
      <el-result
        v-if="!loading && items.length === 0"
        icon="success"
        title="暂无违约记录"
        sub-title="继续保持良好的预约习惯 👍"
      />
      <el-table v-else :data="items" v-loading="loading">
        <el-table-column prop="room_name" label="自习室" min-width="160" />
        <el-table-column prop="seat_number" label="座位" width="90" />
        <el-table-column label="违约时间" min-width="180">
          <template #default="{ row }">{{ fmt(row.violation_time) }}</template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="140" />
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listViolations } from '../api/student.js'
import { fmt } from '../utils/format.js'

const items = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 15
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await listViolations({ page: page.value, per_page: perPage })
    items.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onPage(p) {
  page.value = p
  load()
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
</style>
