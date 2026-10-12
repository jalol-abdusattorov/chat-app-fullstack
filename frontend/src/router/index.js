import { createRouter, createWebHistory } from 'vue-router'
import { isTokenExpired, useAuthStore } from '../stores/auth.js'

const router = createRouter({
history: createWebHistory(import.meta.env.BASE_URL),
routes: [
    {
        path: "/",
        name: "Home",
        component: () => import('../views/Home.vue'),
        meta: { requiresAuth: true },
        children: [
            {
                path: "",
                name: "ChatSideBar",
                component: () => import('../components/ChatSideBar.vue')
            },
            {
                path: ":room_id",
                name: "ChatRoom",
                component: () => import('../views/Room.vue')
            }
        ]
    },
    {
        path: "/register",
        name: "Register",
        component: () => import('../views/Register.vue'),
        props: true,
        meta: { requiresGuest: true }
    },
    {
        path: "/login",
        name: "Login",
        component: () => import('../views/Login.vue'),
        props: true,
        meta: { requiresGuest: true }
    },
    {
        path: "/logout",
        name: "Logout",
        component: () => import('../views/Logout.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: "/:pathMatch(.*)*",
        name: "NotFound",
        component: () => import('../views/NotFound.vue')
    }
],
})

router.beforeEach((to, from) => {
    const authStore = useAuthStore()

    if (to.meta.requiresAuth) {
        if (isTokenExpired(authStore.token)) {
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
