<template>
  <div class="settings-page">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>系统参数配置</span>
          <el-button type="primary" @click="handleSaveAll" :disabled="!hasChanges">保存修改</el-button>
        </div>
      </template>

      <el-alert
        title="以下参数将影响系统的核心业务规则，修改后即时生效，请谨慎操作。"
        type="warning"
        :closable="false"
        style="margin-bottom: 20px;"
      />

      <el-table :data="configList" border stripe>
        <el-table-column prop="key" label="配置项" width="250">
          <template #default="{ row }">
            <strong>{{ configLabels[row.key] || row.key }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="value" label="当前值" width="150">
          <template #default="{ row }">
            <el-input-number
              v-if="isNumberConfig(row.key)"
              v-model="row.value"
              :min="1"
              @change="markChanged(row)"
            />
            <el-input
              v-else
              v-model="row.value"
              @change="markChanged(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="300">
          <template #default="{ row }">
            {{ row.description }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag type="success" v-if="row.changed">已修改</el-tag>
            <el-tag type="info" v-else>默认</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request.js'

const loading = ref(false)
const configList = ref([])

const configLabels = {
  max_reservation_hours: '单次最大预约时长（小时）',
  no_show_threshold_minutes: '超时未签到判定违约阈值（分钟）',
  remind_before_minutes: '预约开始前提醒时间（分钟）',
  check_in_alert_minutes: '预约开始后未签到再次提醒时间（分钟）',
  sign_in_code_refresh_hours: '动态签到码更新周期（小时）',
  max_active_reservations: '学生同时最大进行中的预约数'
}

const isNumberConfig = (key) => {
  return ['max_reservation_hours', 'no_show_threshold_minutes', 'remind_before_minutes',
    'check_in_alert_minutes', 'sign_in_code_refresh_hours', 'max_active_reservations'].includes(key)
}

const hasChanges = computed(() => {
  return configList.value.some(c => c.changed)
})

const fetchConfigs = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/configs')
    configList.value = (res.data.items || []).map(item => ({
      ...item,
      originalValue: item.value,
      changed: false
    }))
  } catch (err) {
    console.error('获取配置失败', err)
  } finally {
    loading.value = false
  }
}

const markChanged = (row) => {
  row.changed = row.value !== row.originalValue
}

const handleSaveAll = async () => {
  try {
    const changed = configList.value.filter(c => c.changed)
    for (const item of changed) {
      await request.put(`/admin/configs/${item.key}`, {
        value: String(item.value),
        description: item.description
      })
      item.originalValue = item.value
      item.changed = false
    }
    ElMessage.success('配置保存成功')
  } catch (err) {
    console.error('保存配置失败', err)
  }
}

onMounted(() => {
  fetchConfigs()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
