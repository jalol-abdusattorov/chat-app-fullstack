<template>
    <div class="main-chat-layout">
        <ChatSideBar :rooms="userRooms" />

        <div class="chat-main-content">
            <p style="margin: auto; color: #94a3b8;">Select a conversation to start chatting</p>
        </div>
    </div>
</template>

<script>
import { onMounted, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRoomsStore } from '../stores/RoomsStore'
import ChatSideBar from '../components/ChatSideBar.vue';

export default {
	components: { ChatSideBar },
  	setup() {
    	const authStore = useAuthStore()
		const roomsStore = useRoomsStore()

		const userRooms = ref([])

		const formatDate = (date) => {
		if (!date) return

		const monthMap = {
			'01': 'Jan',
			'02': 'Feb',
			'03': 'Mar',
			'04': 'Apr',
			'05': 'May',
			'06': 'Jun',
			'07': 'Jul',
			'08': 'Aug',
			'09': 'Sep',
			'10': 'Oct',
			'11': 'Nov',
			'12': 'Dec'
		}

		date = date.substring(0, 10)

		const month = date.slice(5, 7)
		const day = date.slice(-2)

		return `${day} ${monthMap[month]}`
		}

		async function loadUserRooms() {
		userRooms.value = await roomsStore.getUserRooms(
			authStore.user.id
		)

		if (userRooms.value?.rooms) {
			userRooms.value = userRooms.value.rooms
		}
		}

		onMounted(async () => {
		await loadUserRooms()
		})

		return {
		roomsStore,
		userRooms,
		formatDate,
		}
	}
}
</script>


<style scoped>
.main-chat-layout {
    display: flex;
    flex-direction: row;
    width: 100%;
    height: 100vh;
    height: 100dvh;
    min-width: 0;
    overflow: hidden;
    background: var(--app-bg);
}

.chat-main-content {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-width: 0;
    min-height: 0;
    overflow: hidden;
    background: var(--app-bg);
    color: var(--text-primary);
    transition: background-color 0.2s ease, color 0.2s ease;
}

@media (max-width: 600px) {
    .main-chat-layout {
        width: 100%;
    }
}
</style>
