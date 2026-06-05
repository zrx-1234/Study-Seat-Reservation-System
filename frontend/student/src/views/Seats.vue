<template>
  <div>
    <h3 class="page-title">找座位</h3>

    <el-card shadow="never" class="filter">
      <el-form inline>
        <el-form-item label="自习室">
          <el-select v-model="roomId" placeholder="请选择自习室" style="width: 220px" @change="loadSeats">
            <el-option v-for="r in rooms" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="date"
            type="date"
            value-format="YYYY-MM-DD"
            :clearable="false"
            :disabled-date="disablePastDate"
            @change="loadSeats"
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="onlyWindow" @change="loadSeats">仅靠窗</el-checkbox>
          <el-checkbox v-model="onlyPlug" @change="loadSeats">仅有插座</el-checkbox>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-loading="loading">
      <el-empty v-if="!loading && roomId && seats.length === 0" description="该自习室暂无可用座位" />
      <el-empty v-if="!roomId" description="请选择一个自习室开始选座" />

      <el-row :gutter="14">
        <el-col v-for="seat in seats" :key="seat.id" :span="6">
          <el-card
            shadow="hover"
            class="seat-card"
            :class="{ disabled: seat.available_slots.length === 0 }"
            @click="openBooking(seat)"
          >
            <div class="seat-head">
              <span class="seat-no">{{ seat.seat_number }}</span>
              <div class="tags">
                <el-tag v-if="seat.has_window" size="small" type="success" effect="plain">窗</el-tag>
                <el-tag v-if="seat.has_plug" size="small" type="warning" effect="plain">插座</el-tag>
              </div>
            </div>
            <div class="slots">
              <span v-if="seat.available_slots.length === 0" class="full">今日已约满</span>
              <el-tag
                v-for="slot in seat.available_slots"
                :key="slot"
                size="small"
                class="slot"
                effect="light"
              >
                {{ slot }}
              </el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 预约弹窗 -->
    <el-dialog v-model="dialogVisible" title="预约座位" width="420px">
      <div v-if="current">
        <p class="dialog-seat">
          {{ roomName }} · 座位 <b>{{ current.seat_number }}</b>
        </p>
        <p class="dialog-slots">可用时段：
          <el-tag v-for="s in current.available_slots" :key="s" size="small" class="slot">{{ s }}</el-tag>
        </p>
        <el-form label-width="80px">
          <el-form-item label="日期">
            <el-input :model-value="date" disabled />
          </el-form-item>
          <el-form-item label="开始">
            <el-select v-model="startHour" placeholder="开始时间" style="width: 100%">
              <el-option v-for="h in selectableStartHours" :key="h" :label="`${pad(h)}:00`" :value="h" />
            </el-select>
          </el-form-item>
          <el-form-item label="结束">
            <el-select v-model="endHour" placeholder="结束时间" style="width: 100%">
              <el-option
                v-for="h in selectableEndHours"
                :key="h"
                :label="`${pad(h)}:00`"
                :value="h"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确认预约</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listRooms, getRoomSeats, createReservation } from '../api/student.js'
import { toDateStr } from '../utils/format.js'

const route = useRoute()
const rooms = ref([])
const seats = ref([])
const roomId = ref(null)
const date = ref(toDateStr(new Date()))
const onlyWindow = ref(false)
const onlyPlug = ref(false)
const loading = ref(false)

const dialogVisible = ref(false)
const current = ref(null)
const startHour = ref(null)
const endHour = ref(null)
const submitting = ref(false)

const roomName = computed(() => rooms.value.find(r => r.id === roomId.value)?.name || '')
const currentFreeHours = computed(() => {
  if (!current.value) return []
  const free = new Set()
  for (const slot of current.value.available_slots || []) {
    const [start, end] = slot.split('-')
    const startH = Number(start.slice(0, 2))
    const endH = Number(end.slice(0, 2))
    for (let h = startH; h < endH; h += 1) free.add(h)
  }
  return [...free].sort((a, b) => a - b)
})

const selectableStartHours = computed(() => currentFreeHours.value)

const selectableEndHours = computed(() => {
  if (startHour.value == null) return []
  const free = new Set(currentFreeHours.value)
  const options = []
  for (let end = startHour.value + 1; end <= 24; end += 1) {
    let valid = true
    for (let h = startHour.value; h < end; h += 1) {
      if (!free.has(h)) {
        valid = false
        break
      }
    }
    if (!valid) break
    options.push(end)
  }
  return options
})

function pad(n) {
  return String(n).padStart(2, '0')
}

function disablePastDate(rawDate) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return rawDate.getTime() < today.getTime()
}

async function loadRooms() {
  const res = await listRooms({ date: date.value })
  rooms.value = res.data.items
}

async function loadSeats() {
  if (!roomId.value) return
  loading.value = true
  try {
    const res = await getRoomSeats(roomId.value, date.value)
    let list = res.data.seats
    if (onlyWindow.value) list = list.filter(s => s.has_window)
    if (onlyPlug.value) list = list.filter(s => s.has_plug)
    seats.value = list
  } finally {
    loading.value = false
  }
}

function openBooking(seat) {
  if (seat.available_slots.length === 0) {
    ElMessage.warning('该座位今日已约满')
    return
  }
  current.value = seat
  startHour.value = selectableStartHours.value[0] ?? null
  endHour.value = selectableEndHours.value[0] ?? null
  dialogVisible.value = true
}

async function submit() {
  if (startHour.value == null || endHour.value == null) {
    ElMessage.warning('请选择有效的起止时间')
    return
  }
  if (!selectableEndHours.value.includes(endHour.value)) {
    ElMessage.warning('结束时间必须大于开始时间，且至少 1 小时')
    return
  }
  submitting.value = true
  try {
    await createReservation({
      seat_id: current.value.id,
      start_time: `${date.value}T${pad(startHour.value)}:00:00`,
      end_time: `${date.value}T${pad(endHour.value)}:00:00`
    })
    ElMessage.success('预约成功')
    dialogVisible.value = false
    loadSeats()
  } catch (e) {
    // 拦截器已提示
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadRooms()
  if (route.query.room_id) {
    roomId.value = Number(route.query.room_id)
    if (route.query.date) {
      const picked = new Date(route.query.date)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      date.value = picked >= today ? route.query.date : toDateStr(today)
    }
    loadSeats()
  }
})

watch(startHour, () => {
  if (endHour.value == null || !selectableEndHours.value.includes(endHour.value)) {
    endHour.value = selectableEndHours.value[0] ?? null
  }
})
</script>

<style scoped>
.filter {
  margin-bottom: 16px;
  border-radius: 12px;
}
.seat-card {
  margin-bottom: 14px;
  border-radius: 12px;
  cursor: pointer;
  min-height: 120px;
}
.seat-card.disabled {
  opacity: 0.55;
}
.seat-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.seat-no {
  font-size: 18px;
  font-weight: 800;
  color: #1f2d3d;
}
.tags {
  display: flex;
  gap: 4px;
}
.slots {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.slot {
  margin: 0;
}
.full {
  color: #c0c4cc;
  font-size: 13px;
}
.dialog-seat {
  font-size: 15px;
}
.dialog-slots {
  color: #6b7280;
  font-size: 13px;
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
</style>
