import { defineStore } from "pinia";
import { ref } from "vue";

export const useMessagesStore = defineStore('MessagesStore', () => {
    const loading = ref(false)
    const error = ref(null)

    async function getRoomMessages(roomId, userId, seq) {
        loading.value = true
        error.value = null

        try {
            

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

    return {
        loading,
        error
    }
})