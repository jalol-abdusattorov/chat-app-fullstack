import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../api/axios";
import { useAuthStore } from "./auth";

export const useRoomsStore = defineStore('roomsStore', () => {
    const loading = ref(false)
    const error = ref(null)
    const rooms = ref([])
    const userRooms = ref([])
    const socket = ref(null)
    const subscribedRooms = ref(new Set())

    async function getUserRooms() {
        loading.value = true
        error.value = null

        try {
            const response = await api.get(`/users/get-user-rooms`)
            const data = response.data

            rooms.value = data.rooms
            for (const i of data.rooms){
                userRooms.value.push(i.room_id)
            }
            userRooms.value = [...new Set(userRooms.value)]

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

    async function getRoomDetails(roomId) {
        loading.value = true
        error.value = null

        try {
            const response = await api.get(`/rooms/${roomId}`)
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

    async function leavePrivateChat(roomId) {
        loading.value = true
        error.value = null

        try {
            const response = await api.delete(`/users/leave-private/${roomId}`)
            const data = response.data

            return data
        } catch (exc) {
            error.value = 
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed"
            throw exc
        } finally {
            loading.value = false
        }
    }
    async function leaveGroupChat(roomId) {
        loading.value = true
        error.value = null

        try {
            const response = await api.delete(`/users/leave-group/${roomId}`)
            const data = response.data

            return data
        } catch (exc) {
            error.value = 
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed"
            throw exc
        } finally {
            loading.value = false
        }
    }

    async function searchRooms(search) {
        loading.value = true
        error.value = null

        try {
            const response = await api.get(`/search/rooms`, { params: { search: search } })
            const data = response.data
            if (data?.ok) {
                rooms.value = data.rooms
            }

            return data
        } catch (exc) {
            error.value = 
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed"
            throw exc
        } finally {
            loading.value = false
        }
    }

    async function joinRoom(roomId) {
        loading.value = true
        error.value = null

        try {
            const response = await api.post(`/join/room/${roomId}`)
            const data = response.data

            return data
        } catch (exc) {
            error.value = 
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed"
            throw exc
        } finally {
            loading.value = false
        }
    }

    async function getRoomMembers(roomId) {
        loading.value = true
        error.value = null

        try {
            const response = await api.get(`/room/${roomId}/members`)
            const data = response.data

            return data
        } catch (exc) {
            error.value = 
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed"
            throw exc
        } finally {
            loading.value = false
        }
    }
    async function kickUser(roomId, kickingUserId) {
        loading.value = true
        error.value = null

        try {
            const response = await api.delete(`/room/${roomId}/kick`, { params: { kicking_user_id: kickingUserId } })
            const data = response.data

            return data
        } catch (exc) {
            error.value = 
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed"
            throw exc
        } finally {
            loading.value = false
        }
    }
    async function addMembers(roomId, addingUsers) {
        loading.value = true
        error.value = null

        try {
            const response = await api.post(`/room/${roomId}/add-people`, { users: addingUsers })
            const data = response.data

            return data
        } catch (exc) {
            error.value = 
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed"
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

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data)
            if (data.type == 'subscribed') subscribedRooms.value.add(data.room_id)
        }

        ws.onopen = () => console.log("WebSocket opened")
        ws.onerror = (e) => console.error('WebSocket error', e)
        ws.onclose = (e) => {
            subscribedRooms.value.clear()
            console.log('WebSocket closed', e.code, e.reason)
        }

        socket.value = ws
        return ws
    }
    function subscribeToRoom(roomId) {
        if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
            console.warn("Socket not open")
            return false
        }
        if (subscribedRooms.value.has(roomId)) { 
            return true
        }

        socket.value.send(JSON.stringify({
            type: 'subscribe',
            room_id: roomId
        }))
        return true
    }

    return {
        loading,
        error,
        rooms,
        getUserRooms,
        getRoomDetails,
        searchRooms,
        userRooms,
        socket,
        createRoom,
        leavePrivateChat,
        leaveGroupChat,
        joinRoom,
        connectSocket,
        subscribeToRoom,
        subscribedRooms,
        getRoomMembers,
        kickUser,
        addMembers,
    }
})