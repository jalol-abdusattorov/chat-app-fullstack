<template>
    <div 
        class="chat-room-item" 
        :class="{ 
            'has-unread': room.unread_count > 0,
            'is-selected': isSelected 
        }"
    >
        <!-- Room Avatar / Initial -->
        <div class="room-avatar">
            {{ roomInitial }}
        </div>

        <!-- Room Details -->
        <div class="room-info">
            <div class="room-header">
                <h4 class="room-name">{{ room.name }}</h4>
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
                <span v-if="room.unread_count > 0" class="unread-badge">
                    {{ room.unread_count > 99 ? '99+' : room.unread_count }}
                </span>
            </div>
        </div>
    </div>
</template>

<script>
import { computed } from 'vue'

export default {
    name: 'ChatRoomItem',
    props: {
        room: {
            type: Object,
            required: true,
            default: () => ({
                room_id: '',
                name: '',
                last_message: null,
                unread_count: 0
            })
        },
        isSelected: {
            type: Boolean,
            default: false
        }
    },
    setup(props) {
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

        return {
            roomInitial,
            formattedTime
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
}

.chat-room-item:hover {
    background-color: #f8fafc;
}

/* Selected state highlight */
.chat-room-item.is-selected {
    background-color: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding-left: 12px; /* adjusts padding to keep alignment consistent with border */
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
</style>