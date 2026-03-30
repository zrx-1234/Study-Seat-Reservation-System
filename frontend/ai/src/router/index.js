import { createRouter, createWebHistory } from 'vue-router'
import Assistant from '../views/Assistant.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/assistant'
  },
  {
    path: '/assistant',
    name: 'Assistant',
    component: Assistant
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
