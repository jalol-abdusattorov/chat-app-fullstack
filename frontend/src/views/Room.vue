<template>
    <Transition name="room-leave">
        <div class="chat-room" v-if="room && !isLeaving" key="chat-room">
            <div class="chat-header">
                <div class="header-info">
                    <h3>{{ room.name || room.other_member }}</h3>
                    <p>{{ room.member_count }} members</p>
                </div>
                <!-- 3 Vertical Dots Settings Button -->
                <button class="settings-dots-btn" @click="openSettings" title="Room Settings">
                    &#8942;
                </button>
            </div>

            <div class="message-log" ref="messageLogRef" @scroll="onScroll">
                <!-- Empty state when room is fresh and has no messages -->
                <div v-if="messages && messages.length === 0" class="empty-state">
                    <div class="empty-icon">💬</div>
                    <p>No messages yet. Start the conversation!</p>
                </div>

                <!-- Message rows -->
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

                <!-- Typing Indicator Bubble inside the message stream -->
                <div v-if="Object.keys(typingUsers).length > 0" class="message-row typing-row">
                    <div class="message-bubble typing-bubble">
                        <span class="typing-text">
                            {{ Object.values(typingUsers).join(', ') }} {{ Object.keys(typingUsers).length === 1 ? 'is' : 'are' }} typing...
                        </span>
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

            <!-- Vertical resize handle -->
            <div
                class="chat-resize-handle"
                @mousedown="startChatResize"
                title="Drag to resize the message area"
            ></div>

            <form @submit.prevent="submit" class="chat-form">
                <input
                    v-model="draft"
                    placeholder="Type a message..."
                    @input="handleTypingInput"
                />
                <button :disabled="!draft.trim()">Send</button>
            </form>


            <Modal :is-open="isSettingsOpen" @close="closeSettings">
                <template #header>
                    <div class="room-modal-heading">
                        <button
                            v-if="memberToKick"
                            type="button"
                            class="kick-back-btn"
                            aria-label="Back to room settings"
                            @click="cancelKick"
                        >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="m15 18-6-6 6-6" />
                            </svg>
                        </button>

                        <div>
                            <h3>{{ memberToKick ? 'Remove member' : 'Room Settings' }}</h3>
                            <p v-if="memberToKick">Confirm this action before continuing.</p>
                            <p v-else>Manage your room and its members.</p>
                        </div>
                    </div>
                </template>

                <div v-if="!memberToKick" class="room-settings-content">
                    <div class="setting-group">
                        <label>Room Name</label>
                        <p class="setting-value">{{ room.name || 'Private Chat' }}</p>
                    </div>

                    <div class="setting-group">
                        <label>Total Members</label>
                        <p class="setting-value">{{ room.member_count }}</p>
                    </div>

                    <div class="setting-group">
                        <div class="members-heading">
                            <label>Members</label>

                            <div class="members-heading-actions">
                                <span class="members-count">{{ roomMembers.length }}</span>

                                <button
                                    v-if="isOwner"
                                    type="button"
                                    class="add-members-btn"
                                    @click="openAddMembers"
                                >
                                    <span>+</span>
                                    Add
                                </button>
                            </div>
                        </div>

                        <div class="members-scroll-container">
                            <div
                                v-for="member in roomMembers"
                                :key="member.user_id"
                                class="member-item"
                            >
                                <div class="member-info">
                                    <div class="member-avatar">
                                        {{ (member.display_name || member.username || 'M').charAt(0).toUpperCase() }}
                                    </div>

                                    <div class="member-details">
                                        <span class="member-name">
                                            {{ member.display_name || member.username || 'Member' }}
                                            <span
                                                v-if="String(member.user_id) === String(authStore.user.id)"
                                                class="you-label"
                                            >You</span>
                                        </span>

                                        <span
                                            class="member-role"
                                            :class="{ 'role-owner': member.role === 'owner' }"
                                        >
                                            {{ member.role || 'Member' }}
                                        </span>
                                    </div>
                                </div>

                                <button
                                    v-if="
                                        String(room.owner_id) === String(authStore.user.id) &&
                                        String(member.user_id) !== String(authStore.user.id) &&
                                        member.role !== 'owner'
                                    "
                                    type="button"
                                    class="kick-member-btn"
                                    :disabled="kickingUserId !== null"
                                    title="Remove member"
                                    :aria-label="`Remove ${member.display_name || member.username || 'member'}`"
                                    @click="confirmKick(member)"
                                >
                                    <svg viewBox="0 0 24 24" fill="none"
                                        stroke="currentColor" stroke-width="1.8"
                                        stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                        <circle cx="10" cy="7" r="4" />
                                        <path d="M19 8v6" />
                                        <path d="M16 11h6" />
                                    </svg>
                                </button>
                            </div>

                            <div v-if="roomMembers.length === 0" class="members-empty">
                                No members found.
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Confirmation replaces the settings content in the SAME modal -->
                <div v-else class="kick-confirm-content">
                    <div class="kick-confirm-icon">
                        <svg viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="1.8"
                            stroke-linecap="round" stroke-linejoin="round">
                            <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                            <circle cx="10" cy="7" r="4" />
                            <path d="m17 10 5 5" />
                            <path d="m22 10-5 5" />
                        </svg>
                    </div>

                    <p class="kick-confirm-message">
                        Are you sure you want to remove
                        <strong>{{ memberToKick.display_name || memberToKick.username || 'this member' }}</strong>
                        from this room? They will no longer be a member of this conversation.
                    </p>
                </div>

                <template #footer>
                    <div class="room-modal-actions">
                        <button
                            type="button"
                            class="kick-cancel-btn"
                            :disabled="kickingUserId !== null"
                            @click="memberToKick ? cancelKick() : closeSettings()"
                        >
                            {{ memberToKick ? 'Back' : 'Close' }}
                        </button>

                        <button
                            v-if="memberToKick"
                            type="button"
                            class="kick-confirm-btn"
                            :disabled="kickingUserId !== null"
                            @click="executeKick"
                        >
                            <span v-if="kickingUserId !== null" class="kick-spinner"></span>
                            {{ kickingUserId !== null ? 'Removing...' : 'Remove member' }}
                        </button>
                    </div>
                </template>
            </Modal>

            <Modal :is-open="isAddMembersOpen" @close="closeAddMembers">
                <template #header>
                    <div class="room-modal-heading">
                        <div>
                            <h3>Add Members</h3>
                            <p>Search for users and select who can join this room.</p>
                        </div>
                    </div>
                </template>

                <div class="add-members-content">
                    <label for="search-room-users">Search users</label>

                    <input
                        id="search-room-users"
                        v-model="searchingMembersValue"
                        @input="onTypingMembers"
                        type="text"
                        placeholder="Search by username..."
                        class="add-members-search"
                        :disabled="isAddingMembers"
                    />

                    <!-- Search results -->
                    <div
                        v-if="usersStore.searchResults?.length"
                        class="add-members-search-results"
                    >
                        <button
                            v-for="user in usersStore.searchResults"
                            :key="user._id"
                            type="button"
                            class="add-member-search-result"
                            @click="addMember(user)"
                            :disabled="
                                isAddingMembers ||
                                addingMembers.includes(String(user._id))
                            "
                        >
                            <span class="add-member-avatar">
                                {{ (user.username || 'U').charAt(0).toUpperCase() }}
                            </span>

                            <span class="add-member-user-info">
                                <span class="add-member-username">{{ user.username }}</span>
                                <span v-if="user.display_name" class="add-member-display-name">
                                    {{ user.display_name }}
                                </span>
                            </span>

                            <span class="add-member-plus">
                                {{ addingMembers.includes(String(user._id)) ? '✓' : '+' }}
                            </span>
                        </button>
                    </div>

                    <p
                        v-else-if="searchingMembersValue.trim()"
                        class="add-members-hint"
                    >
                        No users found. Try another username.
                    </p>

                    <!-- Selected users -->
                    <div v-if="selectedUsersObjects.length" class="selected-members-section">
                        <div class="selected-members-heading">
                            <span>Selected Members</span>
                            <span class="members-count">
                                {{ selectedUsersObjects.length }}
                            </span>
                        </div>

                        <div class="selected-members-list">
                            <div
                                v-for="user in selectedUsersObjects"
                                :key="user._id"
                                class="selected-member-chip"
                            >

                                <span class="selected-member-name">
                                    {{ user.username }}
                                </span>

                                <button
                                    type="button"
                                    class="remove-selected-member"
                                    title="Remove selection"
                                    :disabled="isAddingMembers"
                                    @click="removeMember(user._id)"
                                >
                                    &times;
                                </button>
                            </div>
                        </div>
                    </div>

                    <p v-if="addMembersError" class="form-error">
                        {{ addMembersError }}
                    </p>
                </div>

                <template #footer>
                    <div class="room-modal-actions">
                        <button
                            type="button"
                            class="kick-cancel-btn"
                            :disabled="isAddingMembers"
                            @click="closeAddMembers"
                        >
                            Cancel
                        </button>

                        <button
                            type="button"
                            class="add-members-submit"
                            :disabled="!addingMembers.length || isAddingMembers"
                            @click="addNewMembers"
                        >
                            {{ isAddingMembers ? 'Adding...' : `Add ${addingMembers.length} Members` }}
                        </button>
                    </div>
                </template>
            </Modal>

        </div>
    </Transition>
</template>

<script>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoomsStore } from '../stores/RoomsStore';
import { useAuthStore } from '../stores/auth';
import { useMessagesStore } from '../stores/MessagesStore';
import { useUsersStore } from '../stores/UsersStore';
import { useRouter } from 'vue-router';
import Modal from '../components/Modal.vue';

export default {
    props: ['room_id', 'socket'],
    components: {
        Modal
    },
    setup(props) {
        const authStore = useAuthStore()
        const roomsStore = useRoomsStore()
        const messagesStore = useMessagesStore()
        const usersStore = useUsersStore()
        const router = useRouter()

        const draft = ref('')
        const room = ref(null)
        const messages = ref(null)
        const nextBeforeSeq = ref(null)
        const lastSeq = ref(0)
        const messageLogRef = ref(null)
        const isLeaving = ref(false)
        const activeUsers = ref(null)
        const roomMembers = ref([])

        const isAddMembersOpen = ref(false)
        const isAddingMembers = ref(false)
        const addingMembers = ref([])
        const searchingMembersValue = ref('')
        const selectedUsersObjects = ref([])
        const addMembersError = ref('')
        function onTypingMembers() {
            clearTimeout(membersSearchTimer)

            membersSearchTimer = setTimeout(async () => {
                const query = searchingMembersValue.value.trim()

                if (!query) {
                    usersStore.searchResults = []
                    return
                }

                try {
                    await usersStore.searchUsers(query)

                    // Hide users who are already in the room.
                    const existingIds = new Set(
                        roomMembers.value.map(member => String(member.user_id))
                    )

                    const selectedIds = new Set(addingMembers.value)

                    usersStore.searchResults = (usersStore.searchResults || []).filter(user => {
                        const id = String(user._id)

                        return (
                            !existingIds.has(id) &&
                            id !== String(authStore.user?.id) &&
                            !selectedIds.has(id)
                        )
                    })
                } catch (error) {
                    console.error('Failed to search users:', error)
                    addMembersError.value = 'Could not search users. Please try again.'
                }
            }, 300)
        }
        function addMember(user) {
            if (!isOwner.value || !user?._id || isAddingMembers.value) return

            const userId = String(user._id)

            if (addingMembers.value.includes(userId)) return

            addingMembers.value.push(userId)
            selectedUsersObjects.value.push(user)

            // Clear the search so the owner can search for the next person.
            searchingMembersValue.value = ''
            usersStore.searchResults = []
            addMembersError.value = ''
        }
        function removeMember(userId) {
            if (isAddingMembers.value) return

            const id = String(userId)

            addingMembers.value = addingMembers.value.filter(
                selectedId => selectedId !== id
            )

            selectedUsersObjects.value = selectedUsersObjects.value.filter(
                user => String(user._id) !== id
            )
        }
        function openAddMembers() {
            if (!isOwner.value) return

            isSettingsOpen.value = false

            addingMembers.value = []
            selectedUsersObjects.value = []
            searchingMembersValue.value = ''
            addMembersError.value = ''
            usersStore.searchResults = []

            isAddMembersOpen.value = true
        }
        function closeAddMembers() {
            if (isAddingMembers.value) return

            clearTimeout(membersSearchTimer)

            isAddMembersOpen.value = false
            addingMembers.value = []
            selectedUsersObjects.value = []
            searchingMembersValue.value = ''
            addMembersError.value = ''
            usersStore.searchResults = []
        }

        let membersSearchTimer = null
        const isOwner = computed(() => {
            return String(authStore.user?.id) === String(room.value?.owner_id)
        })

        let leaveTimer = null
        let readTimer = null
        let lastSentRead = 0
        let loadingOlder = false

        let typingTimeout = null
        const TYPING_TIMER_LENGTH = 2000
        const typingUsers = ref({}) 

        function handleTypingInput() {
            const socket = roomsStore.socket
            if (!socket || socket.readyState != WebSocket.OPEN) return

            if (!typingTimeout) {
                socket.send(JSON.stringify({
                    type: "typing",
                    room_id: props.room_id,
                    is_typing: true
                }))
            } else {
                clearTimeout(typingTimeout)
            }

            typingTimeout = setTimeout(() => {
                socket.send(JSON.stringify({
                    type: "typing",
                    room_id: props.room_id,
                    is_typing: false
                }))
                typingTimeout = null
            }, TYPING_TIMER_LENGTH)
        }

        const contextMenu = ref({
            visible: false,
            x: 0,
            y: 0,
            message: null
        })
        const editingMessageId = ref(null)
        const editDraft = ref('')

        const chatFormHeight = ref(90)

        let isChatResizing = false
        let resizeStartY = 0
        let resizeStartHeight = 0

        function startChatResize(event) {
            if (event.button !== 0) return

            isChatResizing = true
            resizeStartY = event.clientY
            resizeStartHeight = chatFormHeight.value

            document.body.style.userSelect = 'none'
            document.body.style.cursor = 'ns-resize'

            document.addEventListener('mousemove', resizeChatForm)
            document.addEventListener('mouseup', stopChatResize)
        }

        function resizeChatForm(event) {
            if (!isChatResizing) return

            // Dragging upward increases the typing section's height.
            const difference = resizeStartY - event.clientY

            chatFormHeight.value = Math.max(
                90,
                Math.min(160, resizeStartHeight + difference)
            )
        }

        function stopChatResize() {
            isChatResizing = false

            document.removeEventListener('mousemove', resizeChatForm)
            document.removeEventListener('mouseup', stopChatResize)

            document.body.style.userSelect = ''
            document.body.style.cursor = ''
        }

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
            if (!roomsStore.socket || roomsStore.socket.readyState !== WebSocket.OPEN) {
                console.warn('Socket not connected')
                return false
            }

            roomsStore.socket.send(JSON.stringify({
                room_id: props.room_id,
                body: text,
            }))
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
        function handleKeydown(event) {
            if (event.key !== 'Escape') return

            if (editingMessageId.value !== null) {
                cancelEditMessage()
                return
            }

            if (isLeaving.value) return

            isLeaving.value = true

            leaveTimer = setTimeout(() => {
                router.push('/')
            }, 250)
        }
        
        function isMyMessage(m) {
            if (!m) return false;
            const senderId = m.sender?.id ?? m.sender_id ?? m.sender;
            return senderId == authStore.user.id;
        }

        async function loadRoomDetails() {
            try {
                const data = await roomsStore.getRoomDetails(props.room_id)
                if (data?.ok) {
                    room.value = data.room
                } else {
                    router.push({ name: 'Home' })
                }
            } catch (error) {
                router.push({ name: 'Home' })
            }
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

        function handleSocketMessage(event) {
            let data

            try {
                data = JSON.parse(event.data)
            } catch (error) {
                console.error("Invalid Websocket message", error)
            }

            if (data.room_id != props.room_id) return

            if (data.type == 'new_message') onNewMessage(data)
            if (data.type == 'message_updated') applyMessageUpdate(data)
            if (data.type == 'message_deleted') applyMessageDelete(data)
            if (data.type == 'typing') {
                if (data.user_id == authStore.user.id) return
                if (data.is_typing) {
                    typingUsers.value[data.user_id] = data.user.display_name
                } else {
                    delete typingUsers.value[data.user_id]
                }
            }
            if (data.type == 'error') console.warn("WebSocket error", data.error)
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

        async function loadRoomMembers() {
            const data = await roomsStore.getRoomMembers(props.room_id)
            if (!data.ok) roomMembers.value = []
            roomMembers.value = data.members
        }
        const isSettingsOpen = ref(false)

        async function openSettings() {
            isSettingsOpen.value = true
            await loadRoomMembers()
        }
        function closeSettings() {
            isSettingsOpen.value = false
        }

        const memberToKick = ref(null)
        const kickingUserId = ref(null)

        function confirmKick(member) {
            if (!room.value || !member) return

            if (String(member.user_id) === String(authStore.user.id)) return
            if (member.role === 'owner') return
            if (String(room.value.owner_id) !== String(authStore.user.id)) return

            memberToKick.value = member
        }

        function cancelKick() {
            if (kickingUserId.value !== null) return
            memberToKick.value = null
        }

        async function executeKick() {
            const member = memberToKick.value
            if (!member || kickingUserId.value !== null) return

            const userId = String(member.user_id)
            kickingUserId.value = userId

            try {
                const success = await kickUser(userId)

                if (!success) return

                roomMembers.value = roomMembers.value.filter(
                    m => String(m.user_id) !== userId
                )

                if (room.value) {
                    room.value.member_count = Math.max(
                        0,
                        room.value.member_count - 1
                    )
                }

                memberToKick.value = null
            } catch (error) {
                console.error('Failed to remove room member:', error)
            } finally {
                kickingUserId.value = null
            }
        }

        async function kickUser(userId) {
            const data = await roomsStore.kickUser(props.room_id, userId)
            return data?.ok === true
        }
        async function addNewMembers() {
            if (!isOwner.value || !addingMembers.value.length || isAddingMembers.value) {
                return
            }

            isAddingMembers.value = true
            addMembersError.value = ''

            try {
                const data = await roomsStore.addMembers(
                    props.room_id,
                    addingMembers.value
                )

                if (!data?.ok) {
                    addMembersError.value = data?.message || 'Failed to add members.'
                    return
                }

                await loadRoomMembers()
                await roomsStore.getUserRooms()

                isAddingMembers.value = false
                closeAddMembers()
            } catch (error) {
                console.error('Failed to add members:', error)
                addMembersError.value =
                    error.response?.data?.detail || 'Failed to add members. Please try again.'
            } finally {
                isAddingMembers.value = false
            }
        }

        let activeSocket = null
        onMounted(async () => {
            document.addEventListener('keydown', handleKeydown)
            document.addEventListener('visibilitychange', markReadSoon)
            document.addEventListener('click', closeMessageMenu)
            document.addEventListener('keydown', closeMessageMenu)

            await loadRoomDetails()
            await loadInitial()
            await nextTick()
            scrollToBottom()
            markReadSoon()

            activeSocket = roomsStore.socket
            if (activeSocket) {
                activeSocket.addEventListener(
                    'message',
                    handleSocketMessage
                )
            }
        })

        onBeforeUnmount(async () => {
            clearTimeout(readTimer)
            clearTimeout(leaveTimer)
            clearTimeout(membersSearchTimer)
            document.removeEventListener('keydown', handleKeydown)
            document.removeEventListener('visibilitychange', markReadSoon)
            document.removeEventListener('click', closeMessageMenu)
            document.removeEventListener('keydown', closeMessageMenu)

            if (activeSocket) {
                activeSocket.removeEventListener(
                    'message',
                    handleSocketMessage
                )
            }

            stopChatResize()
            await roomsStore.getUserRooms()
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
            activeUsers,
            handleTypingInput,
            typingUsers,
            isSettingsOpen,
            openSettings,
            closeSettings,
            roomMembers,
            memberToKick,
            kickingUserId,
            confirmKick,
            cancelKick,
            executeKick,
            kickUser,
            chatFormHeight,
            startChatResize,
            stopChatResize,
            isOwner,
            isAddMembersOpen,
            isAddingMembers,
            addingMembers,
            openAddMembers,
            closeAddMembers,
            addNewMembers,
            searchingMembersValue,
            selectedUsersObjects,
            addMembersError,
            onTypingMembers,
            addMember,
            removeMember,
            usersStore,
        }
    }
}
</script>

<style scoped>
/* Chat Room Container */
.chat-room {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--app-bg);
    color: var(--text-primary);
    position: relative;
    overflow: hidden;
}

/* Chat Header */
.chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    padding-right: 160px;
    background-color: var(--surface);
    border-bottom: 1px solid var(--border);
}

.header-info h3 {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-primary);
}

.header-info p {
    margin: 2px 0 0 0;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.settings-dots-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: 1.2rem;
    padding: 4px 8px;
    cursor: pointer;
    border-radius: 6px;
    transition: background-color 0.2s, color 0.2s;
}

.settings-dots-btn:hover {
    background-color: var(--surface-hover);
    color: var(--text-primary);
}

/* Message Log Area */
.message-log {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.empty-state {
    margin: auto;
    text-align: center;
    color: var(--text-muted);
}

.empty-icon {
    font-size: 2.5rem;
    margin-bottom: 8px;
}

/* Message Rows & Bubbles */
.message-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
}

.message-row.my-message {
    align-items: flex-end;
}

.message-bubble {
    max-width: 70%;
    padding: 10px 14px;
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text-primary);
    box-shadow: var(--shadow);
    font-size: 0.95rem;
    word-break: break-word;
}

.message-row.my-message .message-bubble {
    background-color: var(--accent-soft);
    border-color: var(--border);
}

.message-bubble.deleted {
    font-style: italic;
    color: var(--text-muted);
    background-color: transparent;
    border: 1px dashed var(--border);
    box-shadow: none;
}

.sender-name {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--accent);
    margin-bottom: 4px;
}

.message-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 4px;
    font-size: 0.7rem;
    color: var(--text-muted);
    align-self: flex-end;
}

.edited-indicator {
    font-style: italic;
}

/* Typing Indicator */
.typing-row {
    opacity: 0.8;
}

.typing-bubble {
    background-color: var(--surface-secondary) !important;
    color: var(--text-secondary) !important;
    font-size: 0.85rem;
    font-style: italic;
}

/* Chat Input Form */
.chat-form {
    display: flex;
    gap: 10px;
    padding: 16px 20px;
    background-color: var(--surface);
    border-top: 1px solid var(--border);
}

.chat-form input {
    flex: 1;
    padding: 10px 14px;
    background-color: var(--input-bg);
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    color: var(--text-primary);
    font: inherit;
    outline: none;
}

.chat-form input:focus {
    border-color: var(--accent);
}

.chat-form button {
    padding: 0 20px;
    background-color: var(--accent);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s;
}

.chat-form button:hover:not(:disabled) {
    background-color: var(--accent-hover);
}

.chat-form button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Resize Handle */
.chat-resize-handle {
    height: 4px;
    width: 100%;
    cursor: ns-resize;
    background-color: transparent;
    transition: background-color 0.2s;
}

.chat-resize-handle:hover {
    background-color: var(--accent);
}

/* Context Menu */
.message-context-menu {
    position: fixed;
    z-index: 1000;
    background-color: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    padding: 4px;
    min-width: 160px;
}

.context-menu-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: transparent;
    border: none;
    color: var(--text-primary);
    font: inherit;
    font-size: 0.9rem;
    cursor: pointer;
    border-radius: 6px;
    text-align: left;
    width: 100%;
}

.context-menu-item:hover {
    background-color: var(--surface-hover);
}

.context-menu-item.delete-item {
    color: var(--danger);
}

.context-menu-item.delete-item:hover {
    background-color: var(--danger-soft);
}

.kick-back-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    padding: 0;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

.kick-back-btn:hover {
    background-color: var(--surface-hover);
    color: var(--text-primary);
    border-color: var(--border-strong);
}

.kick-back-btn svg {
    width: 16px;
    height: 16px;
}

/* Room Modal Styles & Settings Content */
.room-modal-heading {
    display: flex;
    align-items: center;
    gap: 12px;
}

.room-modal-heading h3 {
    margin: 0;
    font-size: 1.1rem;
    color: var(--text-primary);
}

.room-modal-heading p {
    margin: 2px 0 0 0;
    font-size: 0.85rem;
    color: var(--text-secondary);
}

.room-settings-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
    color: var(--text-primary);
}

.setting-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.setting-group label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
}

.setting-value {
    font-size: 0.95rem;
    color: var(--text-primary);
    margin: 0;
}

.members-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.members-heading-actions {
    display: flex;
    align-items: center;
    gap: 8px;
}

.add-members-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 6px 12px;
    background-color: var(--accent);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s ease, transform 0.1s ease;
}

.add-members-btn:hover {
    background-color: var(--accent-hover);
}

.add-members-btn:active {
    transform: scale(0.97);
}

.members-count {
    font-size: 0.75rem;
    background-color: var(--surface-secondary);
    border: 1px solid var(--border);
    padding: 2px 8px;
    border-radius: 12px;
    color: var(--text-secondary);
}

.add-members-submit {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 8px 16px;
    background-color: var(--accent);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s ease, opacity 0.2s ease, transform 0.1s ease;
}

.add-members-submit:hover:not(:disabled) {
    background-color: var(--accent-hover);
}

.add-members-submit:active:not(:disabled) {
    transform: scale(0.97);
}

.add-members-submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}   

/* Members Scroll Container & List Items */
.members-scroll-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 260px;
    overflow-y: auto;
    margin-top: 8px;
    padding-right: 4px;
}

.member-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    background-color: var(--surface-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    transition: background-color 0.2s ease, border-color 0.2s ease;
}

.member-item:hover {
    background-color: var(--surface-hover);
    border-color: var(--border-strong);
}

.member-info {
    display: flex;
    align-items: center;
    gap: 12px;
}

.member-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background-color: var(--accent-soft);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.9rem;
}

.member-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.member-name {
    font-weight: 500;
    color: var(--text-primary);
    font-size: 0.95rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

.you-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    background-color: var(--surface);
    border: 1px solid var(--border);
    padding: 1px 6px;
    border-radius: 4px;
}

.member-role {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.member-role.role-owner {
    color: var(--accent);
    font-weight: 600;
}

.kick-member-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--danger);
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease, border-color 0.2s ease;
}

.kick-member-btn:hover {
    background-color: var(--danger-soft);
    border-color: var(--danger);
}

.kick-member-btn svg {
    width: 16px;
    height: 16px;
}

.members-empty {
    text-align: center;
    padding: 16px;
    color: var(--text-muted);
    font-size: 0.9rem;
}

/* Modal Actions & Footers */
.room-modal-actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    width: 100%;
}

/* Kick Confirmation Modal Styling */
.kick-confirm-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 12px 0 8px 0;
}

.kick-confirm-icon {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background-color: var(--danger-soft);
    color: var(--danger);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}

.kick-confirm-icon svg {
    width: 32px;
    height: 32px;
}

.kick-confirm-message {
    font-size: 0.95rem;
    color: var(--text-secondary);
    line-height: 1.5;
    margin: 0;
}

.kick-confirm-message strong {
    color: var(--text-primary);
}

/* Back / Cancel Button inside modal footer */
.kick-cancel-btn {
    padding: 8px 16px;
    margin-top: 10px;
    background-color: var(--surface-secondary);
    border: 1px solid var(--border);
    color: var(--text-primary);
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s ease, border-color 0.2s ease;
}

.kick-cancel-btn:hover:not(:disabled) {
    background-color: var(--surface-hover);
    border-color: var(--border-strong);
}

.kick-cancel-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.kick-confirm-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background-color: var(--danger);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
}

.kick-confirm-btn:hover {
    opacity: 0.9;
}

/* Add Members Modal Styling */
.add-members-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.add-members-content label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
}

.add-members-search {
    padding: 10px 14px;
    background-color: var(--input-bg);
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    color: var(--text-primary);
    font: inherit;
    outline: none;
}

.add-members-search:focus {
    border-color: var(--accent);
}

.add-members-search-results {
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-height: 200px;
    overflow-y: auto;
}

.add-member-search-result {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 8px 12px;
    background-color: var(--surface-secondary);
    border: 1px solid var(--border);
    border-radius: 6px;
    cursor: pointer;
    color: var(--text-primary);
    transition: background-color 0.2s;
}

.add-member-search-result:hover:not(:disabled) {
    background-color: var(--surface-hover);
}

.add-member-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background-color: var(--accent-soft);
    color: var(--accent);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.8rem;
}

.add-member-user-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    margin-left: 10px;
}

.add-member-username {
    font-weight: 500;
    font-size: 0.9rem;
}

.add-member-display-name {
    font-size: 0.75rem;
    color: var(--text-secondary);
}

.add-member-plus {
    font-weight: bold;
    color: var(--accent);
}

.selected-members-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 4px;
}

.selected-members-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
}

.selected-members-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.selected-member-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 8px 4px 4px;
    background-color: var(--surface-secondary);
    border: 1px solid var(--border);
    border-radius: 16px;
    font-size: 0.85rem;
}

.selected-member-name {
    color: var(--text-primary);
}

.remove-selected-member {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 1.1rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 2px;
}

.remove-selected-member:hover {
    color: var(--danger);
}

.form-error {
    color: var(--danger);
    font-size: 0.85rem;
    margin: 0;
}
</style>
