<template>
  <div>
    <h3 class="page-title">自习室</h3>

    <el-card shadow="never" class="filter">
      <el-form inline>
        <el-form-item label="日期">
          <el-date-picker
            v-model="date"
            type="date"
            value-format="YYYY-MM-DD"
            :clearable="false"
            @change="load"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="roomType" placeholder="全部" clearable style="width: 150px" @change="load">
            <el-option label="全校公共" value="public" />
            <el-option label="院系专属" value="department" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-loading="loading">
      <el-empty v-if="!loading && rooms.length === 0" description="暂无可用自习室" />
      <el-row :gutter="16">
        <el-col v-for="room in rooms" :key="room.id" :span="8">
          <el-card shadow="hover" class="room-card" @click="goSeats(room)">
            <div class="room-top">
              <span class="room-name">{{ room.name }}</span>
              <el-tag size="small" :type="room.room_type === 'public' ? 'success' : 'warning'">
                {{ room.room_type === 'public' ? '公共' : '院系' }}
              </el-tag>
            </div>
            <p class="room-loc">📍 {{ room.location }}</p>
            <p class="room-time">🕐 {{ room.open_time }} ~ {{ room.close_time }}</p>
            <div class="room-foot">
              <span class="seats"><b>{{ room.available_seats }}</b> 个可约座位</span>
              <el-button type="primary" link>选座 →</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listRooms } from '../api/student.js'
import { toDateStr } from '../utils/format.js'

const router = useRouter()
const rooms = ref([])
const loading = ref(false)
const date = ref(toDateStr(new Date()))
const roomType = ref('')

async function load() {
  loading.value = true
  try {
    const params = { date: date.value }
    if (roomType.value) params.room_type = roomType.value
    const res = await listRooms(params)
    rooms.value = res.data.items
  } finally {
    loading.value = false
  }
}

function goSeats(room) {
  router.push({ path: '/seats', query: { room_id: room.id, date: date.value } })
}

onMounted(load)
</script>

<style scoped>
.filter {
  margin-bottom: 16px;
  border-radius: 12px;
}
.room-card {
  margin-bottom: 16px;
  border-radius: 12px;
  cursor: pointer;
}
.room-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.room-name {
  font-size: 16px;
  font-weight: 700;
}
.room-loc,
.room-time {
  color: #6b7280;
  margin: 8px 0 0;
  font-size: 13px;
}
.room-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
}
.room-foot .seats b {
  color: #2563eb;
  font-size: 18px;
}
</style>
