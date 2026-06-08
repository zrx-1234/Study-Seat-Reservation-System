import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue')
      },
      {
        path: 'rooms',
        name: 'Rooms',
        component: () => import('../views/Rooms.vue')
      },
      {
        path: 'seats',
        name: 'Seats',
        component: () => import('../views/Seats.vue')
      },
      {
        path: 'reservations',
        name: 'Reservations',
        component: () => import('../views/Reservations.vue')
      },
      {
        path: 'violations',
        name: 'Violations',
        component: () => import('../views/Violations.vue')
      },
      {
        path: 'roles',
        name: 'Roles',
        component: () => import('../views/Roles.vue')
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/Users.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue')
      }
    ]
  }
]

const router = createRouter({
  // 子路径部署时使用 /admin/ 作为路由前缀
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫：未登录跳转登录页
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
