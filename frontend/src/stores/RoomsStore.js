import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../api/axios";
import { useAuthStore } from "./auth";

export const useRoomsStore = defineStore('roomsStore', () => {
    const loading = ref(false)
    const error = ref(null)
    const rooms = ref([])
    const socket = ref(null)

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

    function connectSocket() {
        const authStore = useAuthStore()
        if (
            socket.value &&
            (
                socket.value.readyState == WebSocket.OPEN ||
                socket.value.readyState == WebSocket.CONNECTING
            )
        ) {
            return socket.value
        }

        const base = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000'

        const ws = new WebSocket(
            `${base}/ws?token=${encodeURIComponent(authStore.token)}`
        )

        ws.onerror = (e) => console.error('WebSocket error', e)
        ws.onclose = (e) => console.log('WebSocket closed', e.code, e.reason)

        socket.value = ws
        return ws
    }

    return {
        loading,
        error,
        rooms,
        getUserRooms,
        getRoomDetails,
        socket,
        createRoom,
        connectSocket,
    }
})