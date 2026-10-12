import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../api/axios";

export const useRoomsStore = defineStore('roomsStore', () => {
    const loading = ref(false)
    const error = ref(null)

    async function getUserRooms(user_id) {
        loading.value = true
        error.value = null

        try {
            const response = await api.get(`/users/get-user-rooms/${user_id}`)
            const data = response.data

            return data
        } catch (exc) {
            error.value = 
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed to fetch"
            throw exc
        } finally {
            loading.value = false
        }
    }

    return {
        loading,
        error,
        getUserRooms,
    }
})