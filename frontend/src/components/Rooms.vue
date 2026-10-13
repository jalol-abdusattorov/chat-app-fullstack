<template>
    <div>
        <div v-for="room in roomsStore.rooms" :key="room.room_id">
            <SingleRoom
                :room="room"
                :is-selected="room.room_id === currentRoomId"
                @click="switchRoom(room.room_id)"
            />
        </div>
    </div>
</template>

<script>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import SingleRoom from './SingleRoom.vue';
import { useRoomsStore } from '../stores/RoomsStore.js';

    export default {
        components: { SingleRoom },
        setup(props) {
            const roomsStore = useRoomsStore()
            const router = useRouter()
            const route = useRoute()

            const currentRoomId = computed(() => route.params.room_id)

            const switchRoom = (room_id) => {
                router.push({ name: "ChatRoom", params: { room_id: room_id } })
            }

            return { 
                switchRoom,
                currentRoomId,
                roomsStore
            }
        }
    }
</script>

<style scoped>

</style>