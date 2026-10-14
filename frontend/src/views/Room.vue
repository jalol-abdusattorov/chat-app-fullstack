<template>
    <Transition name="room-leave">
        <div class="chat-room" v-if="room && !isLeaving" key="chat-room">
            <div class="chat-header">
                <h3>{{ room.name || room.other_member }}</h3>
                <p>{{ room.member_count }} members</p>
            </div>

            <div class="message-log" ref="messageLogRef" @scroll="onScroll">
                <!-- Empty state when room is fresh and has no messages -->
                <div v-if="messages && messages.length === 0" class="empty-state">
                    <div class="empty-icon">💬</div>
                    <p>No messages yet. Start the conversation!</p>
                </div>

                <div
                    v-for="m in messages"
                    :key="m.id"
                    class="message-row"
                    :class="{ 'my-message': isMyMessage(m) }"
                    @contextmenu.prevent="openMessageMenu($event, m)"
                >
                    <div class="message-bubble" v-if="m.body">
                        <!-- Sender name for group chats (other users only) -->
                        <div
                            class="sender-name"
                            :class="{
                                'room-owner': m.sender?.id == room.owner_id
                                && m.sender?.id != authStore.user.id
                            }"
                            v-if="room.type !== 'private' && !isMyMessage(m)"
                        >
                            {{ m.sender?.display_name || 'Member' }}
                        </div>

                        <div v-if="editingMessageId === (m.id)" class="message-edit">
                            <textarea
                                v-model="editDraft"
                                class="edit-input"
                                rows="2"
                                autofocus
                                @keydown.enter.exact.prevent="saveEditedMessage"
                                @keydown.escape.stop="cancelEditMessage"
                            ></textarea>

                            <div class="edit-actions">
                                <button
                                    type="button"
                                    class="edit-save"
                                    :disabled="!editDraft.trim()"
                                    @click.stop="saveEditedMessage"
                                >
                                    Save
                                </button>

                                <button
                                    type="button"
                                    class="edit-cancel"
                                    @click.stop="cancelEditMessage"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>

                        <div v-else class="message-text">
                            {{ m.body }}
                        </div>

                        <!-- Modern Timestamp & Edited Meta Container -->
                        <div class="message-meta">
                            <span v-if="m.edited_at" class="edited-indicator">edited</span>
                            <span class="message-time">
                                {{ m.created_at ? m.created_at.slice(11, 16) : '' }}
                            </span>
                        </div>
                    </div>
                    <div class="message-bubble deleted" v-else>
                        This message was deleted
                    </div>
                </div>
            </div>

            <div
                v-if="contextMenu.visible"
                class="message-context-menu"
                :style="{
                    left: `${contextMenu.x}px`,
                    top: `${contextMenu.y}px`
                }"
                @contextmenu.prevent
                >
                <button
                    class="context-menu-item delete-item"
                    @click.stop="handleDeleteMessage"
                >
                    <span>🗑️</span>
                    Delete
                </button>
                <button
                    class="context-menu-item edit-item"
                    @click.stop="startEditMessage"
                >
                    <span>✏️</span>
                    Edit
                </button>
            </div>

            <form @submit.prevent="submit" class="chat-form">
                <input v-model="draft" placeholder="Type a message..." />
                <button :disabled="!draft.trim()">Send</button>
            </form>
        </div>
    </Transition>
</template>

<script>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoomsStore } from '../stores/RoomsStore';
import { useAuthStore } from '../stores/auth';
import { useMessagesStore } from '../stores/MessagesStore';
import { useUsersStore } from '../stores/UsersStore';
import { useRouter } from 'vue-router';

    export default {
        props: ['room_id'],
        setup(props) {
            const authStore = useAuthStore()
            const roomsStore = useRoomsStore()
            const messagesStore = useMessagesStore()
            const usersStore = useUsersStore()
            const router = useRouter()
            let socket = null

            const draft = ref('')
            const room = ref(null)
            const messages = ref(null)
            const nextBeforeSeq = ref(null)
            const lastSeq = ref(0)
            const messageLogRef = ref(null)
            const isLeaving = ref(false)
            let leaveTimer = null
            let readTimer = null
            let lastSentRead = 0
            let loadingOlder = false

            const contextMenu = ref({
                visible: false,
                x: 0,
                y: 0,
                message: null
            })
            const editingMessageId = ref(null)
            const editDraft = ref('')

            function startEditMessage() {
                const message = contextMenu.value.message

                closeMessageMenu()

                if (!message || !message.body) return

                if (!isMyMessage(message)) return

                editingMessageId.value = message._id ?? message.id
                editDraft.value = message.body
            }

            function cancelEditMessage() {
                editingMessageId.value = null
                editDraft.value = ''
            }

            async function saveEditedMessage() {
                const messageId = editingMessageId.value
                const newMessage = editDraft.value.trim()

                if (!messageId || !newMessage) return

                const message = messages.value?.find(
                    m => (m._id ?? m.id) === messageId
                )

                if (!message) {
                    cancelEditMessage()
                    return
                }

                if (newMessage === message.body) {
                    cancelEditMessage()
                    return
                }

                try {
                    const success = await editMessage(messageId, newMessage)

                    if (!success) return

                    cancelEditMessage()
                } catch (error) {
                    console.error('Failed to edit message:', error)
                }
            }

            function openMessageMenu(event, message) {
                const menuWidth = 170
                const menuHeight = 55

                contextMenu.value = {
                    visible: true,
                    x: Math.min(event.clientX, window.innerWidth - menuWidth - 8),
                    y: Math.min(event.clientY, window.innerHeight - menuHeight - 8),
                    message
                }
            }

            function closeMessageMenu() {
                contextMenu.value.visible = false
            }

            async function handleDeleteMessage() {
                const message = contextMenu.value.message

                closeMessageMenu()

                if (!message) return
                if (message.sender.id != authStore.user.id) return

                await deleteMessage(message.id)
            }

            async function deleteMessage(messageId) {
                await messagesStore.deleteMessage(props.room_id, messageId)
            }
            async function editMessage(messageId, newMessage) {
                const res = await messagesStore.editMessage(messageId, props.room_id, newMessage)
                if (!(res.status == 200)) {
                    return false
                }
                return true
            }

            function isAtBottom(threshold = 80) {
                const el = messageLogRef.value
                if (!el) return false
                return el.scrollHeight - el.scrollTop - el.clientHeight < threshold
            }

            function onScroll() {
                const el = messageLogRef.value
                if (!el) return

                if (el.scrollTop < 80) loadOlder()
                markReadSoon()
            }

            function scrollToBottom() {
                const el = messageLogRef.value
                if (el) el.scrollTop = el.scrollHeight
            }

            async function sendRead(seq) {
                if (seq <= lastSentRead) return
                lastSentRead = seq

                try {
                    const response = await usersStore.readMessages(props.room_id, seq)
                    if (!response.ok) {
                        lastSentRead = 0
                    }
                } catch {
                    lastSentRead = 0
                }
            }

            function markReadSoon() {
                if (document.visibilityState !== 'visible') return
                if (!messages.value?.length || !isAtBottom()) return
                clearTimeout(readTimer)
                readTimer = setTimeout(() => sendRead(lastSeq.value), 500)
            }

            function sendMessage(text) {
                if (!socket || socket.readyState !== WebSocket.OPEN) {
                    console.warn('Socket not connected')
                    return false
                }

                socket.send(text)
                return true
            }
            function submit() {
                const text = draft.value.trim()
                if (!text) return
                if (sendMessage(text)) draft.value = ''
            }

            function findMessage(id) {
                return messages.value.find(m => m.id === id)
            }

            function applyMessageUpdate(data) {
                const m = findMessage(data.id)
                if (!m) return
                m.body = data.body
                m.edited_at = data.edited_at
            }
            function applyMessageDelete(data) {
                const m = findMessage(data.id)
                if (!m) return
                m.body = null
                m.deleted = true
            }
            function handleKeydown(event) {
                if (event.key !== 'Escape') return

                // If editing a message, cancel editing first.
                if (editingMessageId.value !== null) {
                    cancelEditMessage()
                    return
                }

                // Prevent triggering the animation multiple times.
                if (isLeaving.value) return

                isLeaving.value = true

                // Wait for the slide-out animation to finish.
                leaveTimer = setTimeout(() => {
                    router.push('/')
                }, 250)
            }
            
            // Helper to robustly check if the message belongs to the current user
            function isMyMessage(m) {
                if (!m) return false;
                const senderId = m.sender?.id ?? m.sender_id ?? m.sender;
                return senderId == authStore.user.id;
            }

            async function loadRoomDetails() {
                const res = await roomsStore.getRoomDetails(props.room_id, authStore.user.id)
                room.value = res?.status == 'success' ? res.room : res
            }
            async function loadInitial() {
                const data = await messagesStore.getRoomMessages(props.room_id, authStore.user.id, null)
                if (!data) {
                    return
                }
                messages.value = data.messages.slice().reverse()
                nextBeforeSeq.value = data.next_before_seq
                lastSeq.value = messages.value.at(-1)?.seq ?? 0

                await nextTick()
            }

            async function loadOlder() {
                if (loadingOlder) return
                if (nextBeforeSeq.value === null) return
                const el = messageLogRef.value
                if (!el) return

                loadingOlder = true
                const oldHeight = el.scrollHeight

                try {
                    const data = await messagesStore.getRoomMessages(
                        props.room_id,
                        authStore.user.id,
                        nextBeforeSeq.value
                    )
                    if (!data) return

                    messages.value = [...data.messages.slice().reverse(), ...messages.value]
                    nextBeforeSeq.value = data.next_before_seq

                    await nextTick()
                    el.scrollTop += el.scrollHeight - oldHeight
                } finally {
                    loadingOlder = false
                }
            }

            onMounted(async () => {
                document.addEventListener('keydown', handleKeydown)
                document.addEventListener('visibilitychange', markReadSoon)
                await loadRoomDetails()
                await loadInitial()
                await nextTick()
                scrollToBottom()
                markReadSoon()
                connectSocket()

                document.addEventListener('click', closeMessageMenu)
                document.addEventListener('keydown', closeMessageMenu)
            })

            function connectSocket() {
                const base = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000'

                socket = new WebSocket(`${base}/ws/${props.room_id}?token=${encodeURIComponent(authStore.token)}`)

                socket.onmessage = (event) => {
                    const data = JSON.parse(event.data)
                    if (data.type === 'new_message') onNewMessage(data)
                    if (data.type === 'message_updated') applyMessageUpdate(data)
                    if (data.type === 'message_deleted') applyMessageDelete(data)
                    if (data.type === 'error') console.warn('WS error:', data.error)
                }

                socket.onerror = (e) => console.error('WebSocket error', e)
                socket.onclose = (e) => console.log('WebSocket closed', e.code, e.reason)
            }

            async function onNewMessage(msg) {
                if (!messages.value) return
                if (msg.seq <= lastSeq.value) return

                const wasAtBottom = isAtBottom()
                messages.value.push(msg)
                lastSeq.value = msg.seq

                await nextTick()
                if (wasAtBottom) scrollToBottom()
                markReadSoon()
            }

            onBeforeUnmount(async () => {
                socket?.close()
                clearTimeout(readTimer)
                clearTimeout(leaveTimer)
                document.removeEventListener('keydown', handleKeydown)
                document.removeEventListener('visibilitychange', markReadSoon)
                document.removeEventListener('click', closeMessageMenu)
                document.removeEventListener('keydown', closeMessageMenu)

                const data = await roomsStore.getUserRooms()
                if (data?.ok != true) {
                    console.log(data)
                }
            })

            return {
                room,
                messages,
                authStore,
                isMyMessage,
                sendMessage,
                draft,
                submit,
                messageLogRef,
                markReadSoon,
                onScroll,
                contextMenu,
                openMessageMenu,
                handleDeleteMessage,
                editingMessageId,
                editDraft,
                startEditMessage,
                saveEditedMessage,
                cancelEditMessage,
                isLeaving,
            }
        }
    }
</script>

<style scoped>
.chat-room {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100vh;
    background: #fdfdfd;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.chat-header {
    padding: 16px 20px;
    background: #ffffff;
    border-bottom: 1px solid #eaeaea;
}

.chat-header h3 {
    margin: 0;
    font-size: 1.1rem;
    color: #333;
}

.message-log {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 20px;
    overflow-y: auto;
    background-color: #f7f9fb;
    position: relative;
}

.empty-state {
    margin: auto;
    text-align: center;
    color: #888;
    font-size: 0.95rem;
}

.empty-icon {
    font-size: 2.5rem;
    margin-bottom: 8px;
}

.message-row {
    display: flex;
    width: 100%;
    justify-content: flex-start; /* Other users' messages on the left */
}

.message-row.my-message {
    justify-content: flex-end; /* Your messages on the right */
}

.message-bubble {
    position: relative;
    max-width: 65%;
    min-width: 70px;
    padding: 8px 12px 22px 12px;
    border-radius: 12px;
    background-color: #ffffff;
    color: #2c3e50;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
    word-break: break-word;
    font-size: 0.95rem;
    line-height: 1.4;
    border-top-left-radius: 2px;
}

.my-message .message-bubble {
    background-color: #dcf8c6;
    border-top-left-radius: 12px;
    border-top-right-radius: 2px;
    text-align: right; /* Aligns the message text to the right for your messages */
}

.message-bubble.deleted {
    background-color: #ececec;
    color: #888;
    font-style: italic;
    padding-bottom: 10px;
    min-width: auto;
    text-align: left;
}

.sender-name {
    font-size: 0.75rem;
    font-weight: 600;
    color: #007bff;
    margin-bottom: 4px;
    text-align: left;
}

.sender-name.room-owner {
  color: #9333ea;
}


.message-context-menu {
  position: fixed;
  z-index: 1000;
  min-width: 170px;
  padding: 5px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  animation: context-menu-appear 0.12s ease-out;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  text-align: left;
  font-size: 14px;
  cursor: pointer;
}

.delete-item {
  color: #dc2626;
}

.delete-item:hover {
  background: #fef2f2;
}

.edit-item {
  color: #2669dc;
}

.edit-item:hover {
  background: #fef2f2;
}


.message-edit {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 220px;
}

.edit-input {
    width: 100%;
    box-sizing: border-box;
    resize: vertical;
    min-height: 55px;
    padding: 9px 10px;
    border: 1px solid #93c5fd;
    border-radius: 8px;
    outline: none;
    background: #ffffff;
    color: #1f2937;
    font: inherit;
    line-height: 1.4;
}

.edit-input:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.edit-actions {
    display: flex;
    justify-content: flex-end;
    gap: 6px;
}

.edit-actions button {
    padding: 5px 10px;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
}

.edit-save {
    background: #2563eb;
    color: white;
}

.edit-save:hover {
    background: #1d4ed8;
}

.edit-save:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.edit-cancel {
    background: #e5e7eb;
    color: #374151;
}

.edit-cancel:hover {
    background: #d1d5db;
}

@keyframes context-menu-appear {
  from {
    opacity: 0;
    transform: scale(0.96);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}


.message-text {
    white-space: pre-wrap;
}

/* Metadata Styling (Time & Edited) */
.message-meta {
    position: absolute;
    bottom: 4px;
    right: 10px;
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.68rem;
    color: #888;
    user-select: none;
}

.my-message .message-meta {
    right: auto;
    left: 10px; /* Moves timestamp to the bottom-left of the bubble for your messages, preventing text collision */
    color: #558b55;
}

.edited-indicator {
    font-style: italic;
    color: #999;
}

.my-message .edited-indicator {
    color: #558b55;
}

.chat-form {
    display: flex;
    padding: 12px 20px;
    background: #ffffff;
    border-top: 1px solid #eaeaea;
    gap: 10px;
}

.chat-form input {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid #ddd;
    border-radius: 8px;
    outline: none;
}

.chat-form button {
    padding: 10px 20px;
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}

.chat-form button:disabled {
    background-color: #cbd5e1;
    cursor: not-allowed;
}

/* Room exit animation */
.room-leave-leave-active {
    transition:
        transform 250ms ease-in,
        opacity 250ms ease-in;
}

.room-leave-leave-to {
    transform: translateX(100%);
    opacity: 0;
}

/* Respect reduced-motion preferences */
@media (prefers-reduced-motion: reduce) {
    .room-leave-leave-active {
        transition-duration: 0.01ms;
    }
}
</style>
