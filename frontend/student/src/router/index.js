import { createRouter, createWebHistory } from 'vue-router'

// 学生端业务页面尚未开发完成，所有受保护路由统一使用 Placeholder 占位
const Placeholder = () => import('../views/Placeholder.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Home',
    component: Placeholder,
    meta: { requiresAuth: true }
  },
  {
    path: '/rooms',
    name: 'Rooms',
    component: Placeholder,
    meta: { requiresAuth: true }
  },
  {
    path: '/seats',
    name: 'Seats',
    component: Placeholder,
    meta: { requiresAuth: true }
  },
  {
    path: '/reservations',
    name: 'Reservations',
    component: Placeholder,
    meta: { requiresAuth: true }
  },
  {
    path: '/checkin',
    name: 'CheckIn',
    component: Placeholder,
    meta: { requiresAuth: true }
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('../views/Notifications.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/violations',
    name: 'Violations',
    component: () => import('../views/Violations.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/assistant',
    name: 'Assistant',
    component: Placeholder,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
