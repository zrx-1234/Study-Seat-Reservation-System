import request from '../utils/request.js'

// ============================================================================
// 认证与个人信息
// ============================================================================

export function login(data) {
  return request.post('/student/auth/login', data)
}

export function register(data) {
  return request.post('/student/auth/register', data)
}

export function getProfile() {
  return request.get('/student/profile')
}

// ============================================================================
// 自习室与座位
// ============================================================================

export function listRooms(params) {
  return request.get('/student/rooms', { params })
}

export function getRoomSeats(roomId, date) {
  return request.get(`/student/rooms/${roomId}/seats`, { params: { date } })
}

export function searchSeats(params) {
  return request.get('/student/seats/search', { params })
}

// ============================================================================
// 预约
// ============================================================================

export function createReservation(data) {
  return request.post('/student/reservations', data)
}

export function listReservations(params) {
  return request.get('/student/reservations', { params })
}

export function getReservation(id) {
  return request.get(`/student/reservations/${id}`)
}

export function cancelReservation(id, reason) {
  return request.post(`/student/reservations/${id}/cancel`, { reason })
}

export function checkIn(id, code) {
  return request.post(`/student/reservations/${id}/check-in`, { code })
}

// ============================================================================
// 通知与违约
// ============================================================================

export function listNotifications(params) {
  return request.get('/student/notifications', { params })
}

export function markNotificationRead(id) {
  return request.put(`/student/notifications/${id}/read`)
}

export function markAllNotificationsRead() {
  return request.put('/student/notifications/read-all')
}

export function listViolations(params) {
  return request.get('/student/violations', { params })
}
