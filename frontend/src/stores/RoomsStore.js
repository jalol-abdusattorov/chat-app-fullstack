import { defineStore } from "pinia";
import { ref } from "vue";

export const useRoomsStore = defineStore('roomsStore', () => {
    const loading = ref(false)
    const error = ref(null)

    _ = 0

    return {
        loading,
        error,
    }
})