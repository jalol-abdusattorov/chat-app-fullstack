import { defineStore } from "pinia";
import { ref } from "vue";
import api from "../api/axios";

export const useMessagesStore = defineStore('MessagesStore', () => {
    const loading = ref(false)
    const error = ref(null)

    async function getRoomMessages(roomId, userId, beforeSeq) {
        loading.value = true
        error.value = null

        try {
            let params = { params: { user_id: userId, limit: 50 } }
            if (beforeSeq !== null ) params = { params: { user_id: userId, limit: 50, before_seq: String(beforeSeq) } }

            const response = await api.get(`/room/${roomId}/messages`, params)
            const data = response.data

            return data
        } catch (exc) {
            error.value = 
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed to fetch"
            console.error(exc);
        } finally {
            loading.value = false
        }
    }

    async function editMessage(messageId, roomId, newMessage) {
        loading.value = true
        error.value = null

        try {
            const response = await api.put(`/messages/edit-message/${messageId}`,
                null,
                {
                    params: {
                        room_id: roomId,
                        edited_message: newMessage,
                    }
                }
            )

            return response
        } catch (exc) {
            error.value =
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed to fetch"
            console.error(exc)
        }
    }

    async function deleteMessage(roomId, messageId) {
        loading.value = true
        error.value = null

        try {
            const params = {
                params: {
                    room_id: roomId,
                }
            }
            const response = await api.delete(`/messages/delete-message/${messageId}`, params)
            const data = response.data

            return data
        } catch (exc) {
            error.value =
                exc.response?.data?.detail ||
                exc.response?.data?.message ||
                "Failed to fetch"
            console.error(exc)
        }
    }

    return {
        error,
        loading,
        getRoomMessages,
        editMessage,
        deleteMessage,
    }
})