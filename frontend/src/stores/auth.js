import api from "../api/axios.js";
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export function isTokenExpired(token) {
  if (!token) return true;

  try {
    const decoded = jwtDecode(token);
    const currentTime = Date.now() / 1000;

    return decoded.exp < currentTime;
  } catch (error) {
    return true;
  }
}

export const useAuthStore = defineStore('authStore', () => {
    const user = ref(JSON.parse(localStorage.getItem('user') || null))
    const token = ref(localStorage.getItem('token') || null)
    const loading = ref(false)
    const error = ref(null)

    const isAuthenticated = computed(() => !!user.value && !!token.value)

    function setAuthData(userData, tokenValue) {
        user.value = userData
        token.value = tokenValue

        localStorage.setItem('user', JSON.stringify(userData))
        localStorage.setItem('token', tokenValue)
    }

    const register = async (credentials) => {
        loading.value = true
        error.value = null

        try {
            const response = await api.post('/users', credentials)
            const data = response.data

            const tokenValue = data.token

            if (data.user_id && tokenValue) {
                const userData = { id: data.user_id, email: credentials.email }
                setAuthData(userData, tokenValue)
            }

            return data
        } catch (exc) {
            error.value =
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                'Registration failed'
            throw exc
        } finally {
            loading.value = false
        }
    }

    const login = async (credentials) => {
        loading.value = true
        error.value = null

        try {
            const formData = new URLSearchParams()
            formData.append('username', credentials.email)
            formData.append('password', credentials.password)

            const response = await api.post('/api/auth/login', formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })

            const data = response.data

            const tokenValue = data.token.access_token
            const userId = data.id

            const userData = { id: userId, email: credentials.email }

            setAuthData(userData, tokenValue)

            return userData
        } catch (err) {
            error.value =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                'Invalid email or password'
            console.error(err);
        } finally {
            loading.value = false
        }
    }

    function logout() {
        user.value = null
        token.value = null
        error.value = null

        localStorage.removeItem('user')
        localStorage.removeItem('token')
    }

    return {
        loading,
        error,
        user,
        token,
        isAuthenticated,
        register,
        login,
        logout
    }
})