import { createRouter, createWebHistory } from 'vue-router'
import Assistant from '../views/Assistant.vue'

const routes = [
  // TODO: Add routes
  // - /login - Login page
  // - /rooms - Study room list
  // - /seats - Seat search
  // - /reservation - My reservations
  // - /checkin - Check-in page
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
