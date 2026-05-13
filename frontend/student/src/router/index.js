import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/rooms',
    name: 'Rooms',
    component: () => import('../views/Rooms.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/seats',
    name: 'Seats',
    component: () => import('../views/Seats.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/reservations',
    name: 'Reservations',
    component: () => import('../views/Reservations.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/checkin',
    name: 'CheckIn',
    component: () => import('../views/CheckIn.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/assistant',
    name: 'Assistant',
    component: () => import('../views/Assistant.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录跳转登录页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('student_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
