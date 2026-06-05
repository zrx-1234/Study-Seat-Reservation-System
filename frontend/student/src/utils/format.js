// 预约状态映射
const STATUS_TEXT = {
  reserved: '已预约',
  checked_in: '已签到',
  completed: '已完成',
  cancelled: '已取消',
  violation: '违约'
}

const STATUS_TYPE = {
  reserved: 'primary',
  checked_in: 'success',
  completed: 'info',
  cancelled: 'info',
  violation: 'danger'
}

const NOTIF_TEXT = {
  remind: '预约提醒',
  check_in_alert: '签到提醒',
  violation: '违约通知',
  cancel: '取消通知',
  system: '系统通知'
}

export function statusText(status) {
  return STATUS_TEXT[status] || status
}

export function statusType(status) {
  return STATUS_TYPE[status] || 'info'
}

export function notifText(type) {
  return NOTIF_TEXT[type] || '通知'
}

// 完整日期时间：2025-04-14 09:00
export function fmt(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// 仅时间：09:00
export function fmtTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// 仅日期：2025-04-14
export function fmtDate(value) {
  if (!value) return '-'
  const d = new Date(value)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

// 将 Date 转为 YYYY-MM-DD（用于查询参数）
export function toDateStr(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function pad(n) {
  return String(n).padStart(2, '0')
}
