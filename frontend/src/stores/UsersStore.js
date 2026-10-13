import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../api/axios";

export const useUsersStore = defineStore('usersStore', () => {
    const loading = ref(false)
    const error = ref(null)

    async function getUserDetails(user_id) {
        loading.value = true
        error.value = null

        try {
            const response = await api.get(`/users/${user_id}`)
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

    async function getUserUsername(user_id) {
        loading.value = true
        error.value = null

        try {
            const response = await api.get(`/users/${user_id}/display_name`)
            const data = response.data
            console.log(data);

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

    async function readMessages(roomId, seq) {
        loading.value = true
        error.value = null

        try {
            const response = await api.put(`/users/read-messages`, null, { params: { room_id: roomId, seq: seq } })

            return response
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
        getUserDetails,
        getUserUsername,
        readMessages,
    }
})