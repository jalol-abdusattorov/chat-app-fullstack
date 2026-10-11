import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "Home",
      component: () => import('../views/Home.vue'),
      meta: { requireAuth: true }
    },
    {
      path: "/room/:room_id",
      name: "Room",
      component: () => import('../views/Room.vue'),
      props: true,
      meta: { requireAuth: true }
    },
    {
      path: "/register",
      name: "Register",
      component: () => import('../views/Register.vue'),
      props: true,
      meta: { requireGuest: true }
    },
    {
      path: "/login",
      name: "Login",
      component: () => import('../views/Login.vue'),
      props: true,
      meta: { requireGuest: true }
    },
  ],
})

router.beforeEach((to, from) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth) {
    if (!authStore.token || isTokenExpired(authStore.token)) {
      authStore.logout()
      return { name: 'Login' }
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: "Login" }
  }

  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    return { name: "Home" }
  }

  return true
})

export default router
