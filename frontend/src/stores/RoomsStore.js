import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../api/axios";
import { useAuthStore } from "./auth";

export const useRoomsStore = defineStore('roomsStore', () => {
    const loading = ref(false)
    const error = ref(null)
    const rooms = ref([])

    async function getUserRooms() {
        loading.value = true
        error.value = null

        try {
            const response = await api.get(`/users/get-user-rooms`)
            const data = response.data

            rooms.value = data.rooms
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

    async function getRoomDetails(roomId, userId) {
        loading.value = true
        error.value = null

        try {
            const response = await api.get(`/rooms/${roomId}`, { params: { user_id: userId } })
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

    async function createRoom(roomData) {
        loading.value = true
        error.value = null

        try {
            const response = await api.post(`/rooms/create-room`, roomData)
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
        rooms,
        getUserRooms,
        getRoomDetails,
        createRoom,
    }
})