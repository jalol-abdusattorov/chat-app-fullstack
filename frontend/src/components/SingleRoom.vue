<template>
    <div
        class="chat-room-item" 
        :class="{ 
            'has-unread': room.unread_count > 0,
            'is-selected': isSelected,
            'not-member': !isUsersRoom
        }"
    >
        <!-- Room Avatar / Initial -->
        <div class="room-avatar">
            {{ roomInitial }}
        </div>

        <!-- Room Details -->
        <div class="room-info">
            <div class="room-header">
                <h4 class="room-name">
                    <span v-if="!isUsersRoom" class="warning-symbol">⚠️ </span>
                    {{ room.name }}
                </h4>
                <span v-if="formattedTime" class="room-time">{{ formattedTime }}</span>
            </div>

            <div class="room-preview">
                <p class="message-text">
                    <span v-if="room.last_message">
                        <strong v-if="room.last_message.display_name" class="sender-name">
                            {{ room.last_message.display_name }}:
                        </strong>
                        {{ room.last_message.body }}
                    </span>
                    <span v-else class="empty-room">
                        No messages yet. Start the conversation!
                    </span>
                </p>

                <!-- Unread Badge -->
                <span v-if="isUsersRoom && room.unread_count > 0" class="unread-badge">
                    {{ room.unread_count > 99 ? '99+' : room.unread_count }}
                </span>
            </div>
        </div>

        <!-- Join Room Button (if not a member) -->
        <button 
            v-if="!isUsersRoom"
            type="button" 
            class="join-room-btn"
            :disabled="!canJoin"
            @click.stop="canJoin && joinRoom()"
        >
            Join Chat
        </button>

        <!-- Leave Room Button (if already a member) -->
        <button 
            v-else
            type="button" 
            class="leave-room-btn" 
            title="Leave room"
            @click.stop="openConfirmModal"
        >
            &times;
        </button>

        <!-- Leave Confirmation Modal -->
        <Modal :is-open="isLeaveModalOpen" @close="closeConfirmModal">
            <template #header>
                <div class="modal-title-container">
                    <h3>Leave Room</h3>
                </div>
            </template>

            <p class="modal-desc">
                Are you sure you want to leave <strong>{{ room.name }}</strong>? You won't be able to see messages unless you rejoin.
            </p>

            <template #footer>
                <div class="modal-actions">
                    <button type="button" class="cancel-btn" @click="closeConfirmModal">
                        Cancel
                    </button>
                    <button type="button" class="confirm-leave-btn" @click="confirmLeaveRoom">
                        Leave Room
                    </button>
                </div>
            </template>
        </Modal>
    </div>
</template>

<script>
import { computed, ref } from 'vue'
import { useRoomsStore } from '../stores/RoomsStore';
import { useRouter } from 'vue-router';
import Modal from './Modal.vue';

export default {
    name: 'ChatRoomItem',
    components: { Modal },
    props: {
        room: {
            type: Object,
            required: true,
            default: () => ({
                room_id: '',
                name: '',
                type: 'group',
                last_message: null,
                unread_count: 0,
                is_member: true
            })
        },
        isSelected: {
            type: Boolean,
            default: false
        }
    },
    setup(props) {
        const roomsStore = useRoomsStore()
        const router = useRouter()
        const isLeaveModalOpen = ref(false)

        const isUsersRoom = computed(() => {
            if (props.room.is_member !== undefined) {
                return props.room.is_member
            }
            return roomsStore.userRooms.includes(props.room.room_id)
        })

        // Adjust condition here if you have specific rules on whether a user is allowed to join
        const canJoin = computed(() => {
            return true 
        })

        const roomInitial = computed(() => {
            return props.room.name ? props.room.name.charAt(0).toUpperCase() : '#'
        })

        const formattedTime = computed(() => {
            if (!props.room.last_message || !props.room.last_message.created_at) return ''
            
            const date = new Date(props.room.last_message.created_at)
            const now = new Date()
            
            if (date.toDateString() === now.toDateString()) {
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
        })

        const openConfirmModal = () => {
            isLeaveModalOpen.value = true
        }
        const closeConfirmModal = () => {
            isLeaveModalOpen.value = false
        }

        const joinRoom = async () => {
            try {
                if (typeof roomsStore.joinRoom === 'function') {
                    await roomsStore.joinRoom(props.room.room_id)
                    roomsStore.subscribeToRoom(props.room.room_id)
                }
                await roomsStore.getUserRooms()
                router.push({ name: "ChatRoom", params: { id: props.room.room_id } })
            } catch (error) {
                console.error("Failed to join room:", error)
            }
        }

        const confirmLeaveRoom = async () => {
            try {
                if (props.room.type === 'private') {
                    await roomsStore.leavePrivateChat(props.room.room_id)
                } else if (props.room.type === 'group') {
                    await roomsStore.leaveGroupChat(props.room.room_id)
                }
                closeConfirmModal()
                router.push({ name: "Home" })
                await roomsStore.getUserRooms()
            } catch (error) {
                console.error("Failed to leave room:", error)
            }
        }

        return {
            roomInitial,
            formattedTime,
            isLeaveModalOpen,
            openConfirmModal,
            closeConfirmModal,
            confirmLeaveRoom,
            joinRoom,
            isUsersRoom,
            canJoin,
        }
    }
}
</script>

<style scoped>
.chat-room-item {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    gap: 12px;
    background-color: #ffffff;
    cursor: pointer;
    transition: all 0.2s ease;
    width: 100%;
    box-sizing: border-box;
    border-bottom: 1px solid #f3f4f6;
    position: relative;
}

.chat-room-item:hover {
    background-color: #f8fafc;
}

.chat-room-item.is-selected {
    background-color: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding-left: 12px;
}

.chat-room-item.not-member {
    background-color: #fafafa;
}

.room-avatar {
    width: 46px;
    height: 46px;
    border-radius: 50%;
    background-color: #e0e7ff;
    color: #4f46e5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 1.1rem;
    flex-shrink: 0;
}

.room-info {
    flex-grow: 1;
    min-width: 0;
}

.room-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4px;
}

.room-name {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: #111827;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.warning-symbol {
    font-size: 0.85rem;
}

.room-time {
    font-size: 0.75rem;
    color: #9ca3af;
    flex-shrink: 0;
    margin-left: 8px;
}

.room-preview {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
}

.message-text {
    margin: 0;
    font-size: 0.85rem;
    color: #6b7280;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex-grow: 1;
}

.sender-name {
    color: #374151;
    font-weight: 500;
}

.empty-room {
    font-style: italic;
    color: #9ca3af;
}

.unread-badge {
    background-color: #3b82f6;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 9999px;
    min-width: 20px;
    text-align: center;
    flex-shrink: 0;
}

.has-unread .room-name {
    color: #111827;
    font-weight: 700;
}

.has-unread .message-text {
    color: #1f2937;
    font-weight: 600;
}

/* Join Button Style */
.join-room-btn {
    background-color: #3b82f6;
    color: white;
    border: none;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    flex-shrink: 0;
    transition: background-color 0.2s ease;
}

.join-room-btn:hover {
    background-color: #2563eb;
}

.join-room-btn:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
    opacity: 0.7;
}

/* Leave Room Button */
.leave-room-btn {
    background: transparent;
    border: none;
    color: #9ca3af;
    font-size: 1.25rem;
    line-height: 1;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s ease, background-color 0.2s ease, color 0.2s ease;
    flex-shrink: 0;
}

.chat-room-item:hover .leave-room-btn {
    opacity: 1;
}

.leave-room-btn:hover {
    background-color: #fee2e2;
    color: #dc2626;
}

/* Modal Custom Layout Styles */
.modal-title-container h3 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: #111827;
}

.modal-desc {
    margin: 0 0 8px;
    font-size: 0.95rem;
    color: #4b5563;
    line-height: 1.5;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    width: 100%;
}

.cancel-btn,
.confirm-leave-btn {
    padding: 10px 18px;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}

.cancel-btn {
    border: 1px solid #d1d5db;
    background: #ffffff;
    color: #374151;
}

.cancel-btn:hover {
    background: #f3f4f6;
}

.confirm-leave-btn {
    border: none;
    background: #dc2626;
    color: #ffffff;
}

.confirm-leave-btn:hover {
    background: #b91c1c;
}
</style>