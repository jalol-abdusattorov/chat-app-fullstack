<template>
    <div class="main-chat-layout">
        <ChatSideBar />

		<router-view :key="$route.params.room_id" />

		<div class="chat-main-content" v-if="!inRoom">
            <p style="margin: auto; color: #94a3b8;">Select a conversation to start chatting</p>
        </div>
    </div>
</template>

<script>
import { computed, onBeforeMount, onMounted } from 'vue'
import { useRoomsStore } from '../stores/RoomsStore'
import ChatSideBar from '../components/ChatSideBar.vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth.js';

export default {
	components: { ChatSideBar },
  	setup() {
		const roomsStore = useRoomsStore()

		const route = useRoute()
		const inRoom = computed(() => {
			const url = route.path
			if (url.slice(1)) {
				return true
			}
			return false
		})

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
			await roomsStore.getUserRooms()
		}

		async function handleSocketMessage(event) {	
			let data

			try {
				data = JSON.parse(event.data)
			} catch (error) {
				console.error("Invalid websocket message:", error)
			}

			if (data.type !== 'new_message') return


			const idx = roomsStore.rooms.findIndex(r => r.room_id == data.room_id)
			if (idx == -1) return

			const room = roomsStore.rooms[idx]
			room.last_message = {
				sender_id: data.sender.id,
				body: data.body,
				created_at: data.created_at,
				display_name: useAuthStore().user.id === data.sender.id ? 'you' : data.sender.display_name,
			}

			if (inRoom.value) return
			room.unread_count++
		}

		let activeSocket = null
		onMounted(async () => {
			await loadUserRooms()
			activeSocket = roomsStore.connectSocket()

			activeSocket.addEventListener(
				'message',
				handleSocketMessage
			)
		})

		onBeforeMount(() => {
			if (activeSocket) {
				activeSocket.removeEventListener(
					'message',
					handleSocketMessage
				)
			}
		})

		return {
			roomsStore,
			formatDate,
			inRoom,
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
