<template>
    <aside class="sidebar-wrapper" :style="{ width: sidebarWidth + 'px' }">
        <div v-if="username" class="user-profile-card">
            <div class="profile-main">
                <div class="avatar-container">
                    <div class="user-avatar">
                        {{ username.charAt(0).toUpperCase() }}
                    </div>
                    <span class="online-status"></span>
                </div>

                <div class="user-details">
                    <span class="user-status-label">Logged in as</span>
                    <span class="username-display" :title="username">
                        {{ username }}
                    </span>
                </div>
            </div>

            <button
                type="button"
                class="logout-btn"
                @click="handleLoggingOut"
                title="Log out"
                aria-label="Log out"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                    <polyline points="16 17 21 12 16 7" />
                    <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
            </button>
        </div>

        <div class="sidebar-header">
            <h1 class="rooms-title">Rooms</h1>
            <span class="chat-count-badge">
                {{ roomsStore.rooms.length }} chats
            </span>
        </div>

        <!-- Search rooms bar -->
        <div class="rooms-search-wrapper">
            <div class="rooms-search-bar">
                <svg
                    class="rooms-search-icon"
                    xmlns="http://www.w3.org/2000/svg"
                    width="19"
                    height="19"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.35-4.35" />
                </svg>

                <input
                    v-model="chatsSearchingValue"
                    @input="onTypingChatsBar"
                    type="text"
                    class="rooms-search-input"
                    placeholder="Search conversations..."
                    aria-label="Search conversations"
                />
            </div>
        </div>

       <!-- Scrollable rooms container -->
        <div class="rooms-container">
            <Rooms />

            <!-- Empty state when no rooms exist -->
            <div v-if="!roomsStore.rooms || roomsStore.rooms.length === 0" class="rooms-empty-state">
                <div class="empty-icon">💬</div>
                <h3>You currently have no rooms</h3>
                <p>Create a room to start chatting with others.</p>
                <button type="button" class="create-room-action-btn" @click="openModal">
                    Create a room
                </button>
            </div>
        </div>

        <!-- Sliding Create Room panel -->
        <div
            class="create-room-drawer"
            :class="{ 'drawer-collapsed': !isCreateRoomExpanded }"
        >
            <!-- Arrow toggle -->
            <button
                type="button"
                class="drawer-arrow-toggle"
                @click="toggleCreateRoom"
                :aria-expanded="isCreateRoomExpanded"
                :aria-label="isCreateRoomExpanded ? 'Collapse create room panel' : 'Expand create room panel'"
                :title="isCreateRoomExpanded ? 'Collapse panel' : 'Expand panel'"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <!-- Down when open, up when closed -->
                    <polyline
                        v-if="isCreateRoomExpanded"
                        points="6 9 12 15 18 9"
                    />
                    <polyline
                        v-else
                        points="6 15 12 9 18 15"
                    />
                </svg>
            </button>

            <!-- This section slides away -->
            <div class="drawer-content">
                <button
                    type="button"
                    class="create-room-btn"
                    @click="openModal"
                >
                    <span class="plus-icon-wrapper">+</span>

                    <span class="btn-text-container">
                        <span class="btn-title">Create Room</span>
                        <span class="btn-subtitle">Start a new conversation</span>
                    </span>
                </button>
            </div>
        </div>

        <!-- Create room modal -->
        <Modal :is-open="isModalActive" @close="closeModal">
            <template #header>
                <div class="modal-heading">
                    <div>
                        <h2>Create a room</h2>
                        <p>Start a new conversation.</p>
                    </div>
                </div>
            </template>

            <form class="create-room-form" @submit.prevent="createRoom">
                <label for="room-name">Room name</label>
                <input
                    id="room-name"
                    v-model="roomName"
                    type="text"
                    :disabled="roomType == 'private'"
                    :placeholder="roomType == 'private' ? 'You cant enter a name to private chat' : 'e.g. Project Team'"
                    maxlength="80"
                    required
                />

                <label for="room-description">Description</label>
                <textarea
                    id="room-description"
                    v-model="roomDescription"
                    placeholder="What's this room about?"
                    rows="3"
                    maxlength="300"
                ></textarea>

                <label for="room-type">Room type</label>
                <select id="room-type" v-model="roomType">
                    <option value="group">Group room</option>
                    <option value="private">Private room</option>
                </select>

                <!-- Member search section -->
                <label for="search-users">Add members</label>
                <input
                    id="search-users"
                    v-model="searchingValue"
                    @input="onTyping"
                    type="text"
                    placeholder="Search by username..."
                />

                <!-- Search results dropdown/list -->
                <div v-if="usersStore.searchResults && usersStore.searchResults.length > 0" class="search-results-list">
                    <div 
                        v-for="user in usersStore.searchResults" 
                        :key="user._id" 
                        class="search-result-item"
                        @click="addMember(user)"
                    >
                        <div class="user-info-display">
                            <span class="username-text">{{ user.username }}</span>
                            <span class="display-name-text" v-if="user.display_name">({{ user.display_name }})</span>
                        </div>
                        <button type="button" class="add-member-btn">+</button>
                    </div>
                </div>

                <!-- Selected members chips -->
                <div class="added-members-section" v-if="roomMembers.length > 1">
                    <div class="added-members-header">
                        <span>Added Members</span>
                        <span class="member-count-badge">{{ roomMembers.length - 1 }} selected</span>
                    </div>
                    <div class="added-members-list">
                        <div 
                            v-for="member in selectedUsersObjects" 
                            :key="member._id" 
                            class="member-chip"
                        >
                            <div class="member-avatar">{{ member.username.charAt(0).toUpperCase() }}</div>
                            <span class="member-name">{{ member.username }}</span>
                            <button type="button" class="remove-member-btn" @click="removeMember(member._id)">&times;</button>
                        </div>
                    </div>
                </div>

                <!-- Form error state inside modal -->
                <p v-if="formError" class="form-error">
                    {{ formError }}
                </p>

                <div class="modal-actions">
                    <button
                        type="button"
                        class="cancel-btn"
                        @click="closeModal"
                    >
                        Cancel
                    </button>

                    <button
                        type="submit"
                        class="submit-btn"
                        :disabled="roomType == 'private' && roomMembers.length != 2 || roomType == 'group' && !roomName.trim()"
                    >
                        Create Room
                    </button>
                </div>
            </form>
        </Modal>

        <!-- Resize handle -->
        <div class="resize-handle" @mousedown="startResize"></div>
    </aside>
</template>

<script>
import { ref, onBeforeUnmount, onMounted } from 'vue';
import { useRoomsStore } from '../stores/RoomsStore.js';
import Rooms from './Rooms.vue';
import Modal from './Modal.vue';
import { useAuthStore } from '../stores/auth.js';
import { useUsersStore } from '../stores/UsersStore.js';
import { useRouter } from 'vue-router';

export default {
    name: 'ChatSideBar',
    components: { Rooms, Modal },
    setup() {
        const authStore = useAuthStore();
        const roomsStore = useRoomsStore();
        const usersStore = useUsersStore();

        const sidebarWidth = ref(330);
        const isModalActive = ref(false);

        const roomName = ref('');
        const roomType = ref('group');
        const roomMembers = ref([authStore.user?.id]);
        const selectedUsersObjects = ref([]);
        const roomDescription = ref('');
        const formError = ref('');
        const error = ref(null);
        const searchingValue = ref('');
        const username = ref(null)
        let debounceTimer = null;

        let debounceTimer2 = null
        const chatsSearchingValue = ref('')
        const onTypingChatsBar = () => {
            clearTimeout(debounceTimer2)
            debounceTimer2 = setTimeout(async () => {
                const search = chatsSearchingValue.value.trim()
                if (search) {
                    await roomsStore.searchRooms(search)
                } else {
                    await roomsStore.getUserRooms()
                }
            }, 200  )
        }


        const onTyping = () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(async () => {
                const query = searchingValue.value.trim();
                if (query) {
                    await usersStore.searchUsers(query);
                } else {
                    usersStore.searchResults = [];
                }
            }, 300);
        };

        let isResizing = false;

        const startResize = (e) => {
            isResizing = true;
            document.addEventListener('mousemove', resize);
            document.addEventListener('mouseup', stopResize);
            document.body.style.userSelect = 'none';
        };
        const resize = (e) => {
            if (!isResizing) return;
            let newWidth = e.clientX;
            if (newWidth < 240) newWidth = 240;
            if (newWidth > 550) newWidth = 550;
            sidebarWidth.value = newWidth;
        };
        const stopResize = () => {
            isResizing = false;
            document.removeEventListener('mousemove', resize);
            document.removeEventListener('mouseup', stopResize);
            document.body.style.userSelect = '';
        };

        const openModal = () => {
            formError.value = '';
            isModalActive.value = true;
        };
        const closeModal = () => {
            isModalActive.value = false;
            formError.value = '';
        };

        const addMember = (user) => {
            if (!roomMembers.value.includes(user._id)) {
                roomMembers.value.push(user._id);
                selectedUsersObjects.value.push(user);
            }
            searchingValue.value = '';
            usersStore.searchResults = [];
        };
        const removeMember = (userId) => {
            roomMembers.value = roomMembers.value.filter(id => id !== userId);
            selectedUsersObjects.value = selectedUsersObjects.value.filter(u => u._id !== userId);
        };

        const resetForm = () => {
            roomName.value = '';
            roomDescription.value = '';
            roomType.value = 'group';
            roomMembers.value = [authStore.user?.id];
            selectedUsersObjects.value = [];
            searchingValue.value = '';
            formError.value = '';
            if (usersStore.searchResults) usersStore.searchResults = [];
        };
        const createRoom = async () => {
            const name = roomName.value.trim();

            if (!name && roomType.value == 'group') {
                formError.value = 'Please enter a room name.';
                return;
            }

            if (name.length > 80) {
                formError.value = 'The room name cannot exceed 80 characters.';
                return;
            }

            const roomData = {
                name,
                room_type: roomType.value,
                room_members: roomMembers.value,
                description: roomDescription.value.trim(),
            };

            try {
                const data = await roomsStore.createRoom(roomData);
                if (data && data.ok === false) {
                    formError.value = data.message || 'Something went wrong, please try again.';
                    return;
                }
                roomsStore.subscribeToRoom(data.room_id)
                resetForm();
                closeModal();
            } catch (err) {
                formError.value = err.response?.data?.detail || 'Failed to create room. Please try again.';
                console.error(err)
            } finally {
                await roomsStore.getUserRooms()
            }
        };

        const getUsername = async () => {
            const data = await usersStore.getUserUsername(authStore.user.id)
            if (!data || !data?.display_name) username.value = null
            username.value = data.display_name
        }

        const router = useRouter()
        const handleLoggingOut = () => {
            router.push({ name: "Logout" })
        }


        onMounted(async () => {
            await getUsername()
        })

        onBeforeUnmount(() => {
            stopResize();
        });

        const isCreateRoomExpanded = ref(true);

        const toggleCreateRoom = () => {
            isCreateRoomExpanded.value = !isCreateRoomExpanded.value;
        };

        return {
            roomsStore,
            authStore,
            usersStore,
            sidebarWidth,
            isModalActive,
            roomName,
            roomDescription,
            roomType,
            roomMembers,
            selectedUsersObjects,
            searchingValue,
            formError,
            startResize,
            openModal,
            closeModal,
            createRoom,
            onTyping,
            addMember,
            username,
            removeMember,
            handleLoggingOut,
            chatsSearchingValue,
            onTypingChatsBar,
            error,
            isCreateRoomExpanded,
            toggleCreateRoom,
        };
    }
};
</script>

<style scoped>
.sidebar-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
    max-height: 100vh;
    max-height: 100dvh;
    background: var(--surface);
    border-right: 1px solid var(--border);
    position: relative;
    overflow: hidden; /* Locks outer sidebar scroll */
    flex-shrink: 0;
}

/* Make sure the rooms container component fills the remaining space and scrolls */
.rooms-container {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    min-height: 0; /* Crucial for flex child scrolling */
}

/* Prevent headers and buttons from breaking layout */
.user-profile-card,
.sidebar-header,
.rooms-search-wrapper,
.create-room-drawer {
    flex-shrink: 0;
}

.user-profile-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 12px 12px 16px;
    margin: 12px 16px 0;
    background-color: var(--app-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    box-sizing: border-box;
}

.user-profile-card:hover {
    border-color: var(--border-strong);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.profile-main {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 0;
}

.user-details {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
    flex: 1;
}

.username-display {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.3;
}

.logout-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    padding: 0;
    border: 1px solid transparent;
    border-radius: 10px;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition:
        background-color 0.2s ease,
        color 0.2s ease,
        border-color 0.2s ease;
}

.logout-btn:hover {
    background-color: var(--danger-soft);
    color: var(--danger);
    border-color: var(--border);
}

.logout-btn:focus-visible {
    outline: 2px solid var(--accent-hover);
    outline-offset: 2px;
}

.avatar-container {
    position: relative;
    flex-shrink: 0;
}

.user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.95rem;
    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.15);
}

.user-status-label {
    font-size: 0.72rem;
    font-weight: 500;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.02em;
    line-height: 1;
    margin-bottom: 3px;
}

.username-display {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.sidebar-header {
    padding: 20px 16px 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
}

.rooms-title {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text-primary);
}

.rooms-empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 24px;
    text-align: center;
    min-height: 100%;
    box-sizing: border-box;
    color: var(--text-muted);
}

.rooms-empty-state .empty-icon {
    font-size: 2.5rem;
    margin-bottom: 12px;
}

.rooms-empty-state h3 {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-primary); /* Uses theme variable instead of #f1f5f9 */
    margin: 0 0 6px 0;
}

.rooms-empty-state p {
    font-size: 0.85rem;
    color: var(--text-secondary); /* Uses theme variable instead of #94a3b8 */
    margin: 0 0 20px 0;
}

.create-room-action-btn {
    background-color: var(--accent);
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s ease, transform 0.1s ease;
}

.create-room-action-btn {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    padding: 10px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.create-room-action-btn:hover {
    background-color: var(--accent-hover);
}
.create-room-action-btn:active {
    transform: scale(0.97);
}

.chat-count-badge {
    font-size: 0.75rem;
    font-weight: 600;
    background-color: var(--surface-hover);
    color: var(--text-secondary);
    padding: 4px 8px;
    border-radius: 999px;
}

.rooms-container {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
}

.sidebar-footer {
    flex-shrink: 0;
    padding: 14px 16px;
    border-top: 1px solid var(--border);
    background-color: var(--surface);
}

.create-room-btn {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 12px;
    width: 100%;
    padding: 12px 16px;
    border: 2px dashed var(--accent);
    border-radius: 12px;
    background: var(--surface);
    color: var(--text-primary);
    cursor: pointer;
    transition: background 0.2s ease, border-color 0.2s ease;
    text-align: left;
}

.create-room-btn:hover {
    background: var(--app-bg);
    border-color: var(--accent-hover);
}

.create-room-btn:active {
    background: var(--surface-secondary);
}

.plus-icon-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: var(--accent-soft);
    color: var(--accent-hover);
    font-size: 1.2rem;
    font-weight: 600;
    flex-shrink: 0;
}

.btn-text-container {
    display: flex;
    flex-direction: column;
}

.btn-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--accent-hover);
}

.btn-subtitle {
    font-size: 0.78rem;
    color: var(--text-secondary);
    margin-top: 2px;
}

/* Modal Content & Form Layout Styles */
.modal-heading {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    width: 100%;
}

.modal-heading h2 {
    margin: 0 0 6px;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
}

.modal-heading p {
    margin: 0 0 16px;
    font-size: 0.95rem;
    color: var(--text-secondary);
}

.create-room-form {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
}

.create-room-form label {
    margin-top: 10px;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
}

.create-room-form input,
.create-room-form textarea,
.create-room-form select {
    width: 100%;
    box-sizing: border-box;
    padding: 12px 14px;
    border: 1px solid var(--border-strong);
    border-radius: 10px;
    background: var(--surface);
    color: var(--text-primary);
    font: inherit;
    font-size: 0.95rem;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.create-room-form textarea {
    resize: vertical;
}

.create-room-form input:focus,
.create-room-form textarea:focus,
.create-room-form select:focus {
    border-color: var(--accent-hover);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.search-results-list {
    background: var(--surface);
    border: 1px solid var(--border-strong);
    border-radius: 8px;
    max-height: 150px;
    overflow-y: auto;
    margin-top: 4px;
}

/* Search bar spacing */
.rooms-search-wrapper {
    padding: 14px 16px 10px;
    flex-shrink: 0;
    background-color: var(--surface);
    box-sizing: border-box;
}

.rooms-search-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    min-width: 0;
    height: 42px;
    padding: 0 12px;
    box-sizing: border-box;

    background-color: var(--app-bg);
    border: 1px solid var(--border);
    border-radius: 11px;

    color: var(--text-muted);
    transition:
        border-color 0.2s ease,
        background-color 0.2s ease,
        box-shadow 0.2s ease;
}

.rooms-search-bar:hover {
    border-color: var(--border-strong);
    background-color: var(--surface);
}

.rooms-search-bar:focus-within {
    background-color: var(--surface);
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
    color: var(--accent-hover);
}

.rooms-search-icon {
    flex-shrink: 0;
    pointer-events: none;
}

.rooms-search-input {
    flex: 1;
    width: 100%;
    min-width: 0;
    height: 100%;
    padding: 0;
    border: none;
    outline: none;
    background: transparent;

    color: var(--text-primary);
    font-family: inherit;
    font-size: 0.88rem;
    font-weight: 400;
}

.rooms-search-input::placeholder {
    color: var(--text-muted);
    opacity: 1;
}

.rooms-search-input:focus {
    outline: none;
}

.search-result-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    cursor: pointer;
    font-size: 0.9rem;
}

.search-result-item:hover {
    background-color: var(--surface-hover);
}

.user-info-display {
    display: flex;
    flex-direction: column;
}

.username-text {
    font-weight: 600;
    color: var(--text-primary);
}

.display-name-text {
    font-size: 0.78rem;
    color: var(--text-secondary);
}

.add-member-btn {
    background: var(--accent-hover);
    color: white;
    border: none;
    border-radius: 4px;
    width: 22px;
    height: 22px;
    cursor: pointer;
}

.added-members-section {
    margin-top: 12px;
    background: var(--surface-secondary);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 12px;
}

.added-members-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 8px;
}

.member-count-badge {
    background-color: var(--accent-soft);
    color: var(--accent-hover);
    padding: 2px 6px;
    border-radius: 999px;
    font-size: 0.75rem;
}

.added-members-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    max-height: 120px;
    overflow-y: auto;
}

.member-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--surface);
    border: 1px solid var(--border-strong);
    padding: 4px 10px 4px 4px;
    border-radius: 20px;
    font-size: 0.85rem;
    color: var(--text-primary);
}

.member-avatar {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background-color: var(--accent-hover);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: bold;
}

.remove-member-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 1rem;
    line-height: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    margin-left: 2px;
}

.remove-member-btn:hover {
    color: var(--danger);
}



.form-error {
    margin: 8px 0;
    padding: 8px 12px;
    background-color: var(--danger-soft);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--danger);
    font-size: 0.85rem;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 24px;
}

.cancel-btn,
.submit-btn {
    padding: 10px 18px;
    border-radius: 10px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}

.cancel-btn {
    border: 1px solid var(--border-strong);
    background: var(--surface);
    color: var(--text-primary);
}

.cancel-btn:hover {
    background: var(--surface-hover);
}

.submit-btn {
    border: none;
    background: var(--accent-hover);
    color: #ffffff;
}

.submit-btn:hover:not(:disabled) {
    background: var(--accent-hover);
}

.submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.resize-handle {
    position: absolute;
    top: 0;
    right: -4px;
    width: 8px;
    height: 100%;
    cursor: ew-resize;
    z-index: 10;
}

.resize-handle:hover {
    background-color: rgba(59, 130, 246, 0.2);
}
/* Sliding Create Room panel */
.create-room-drawer {
    position: relative;
    z-index: 5;
    flex-shrink: 0;
    padding: 4px 12px 4px;
    background: var(--surface);
    border-top: 1px solid var(--border);
    box-sizing: border-box;
    transition: padding 0.3s ease;
}

/* Minimal arrow button */
.drawer-arrow-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 38px;
    height: 26px;
    margin: 0 auto;
    padding: 0;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition:
        background-color 0.2s ease,
        color 0.2s ease;
}

.drawer-arrow-toggle:hover {
    background: var(--accent-soft);
    color: var(--accent-hover);
}

.drawer-arrow-toggle:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
}

/* Animate the Create Room button */
.drawer-content {
    display: grid;
    grid-template-rows: 1fr;
    opacity: 1;
    margin-top: 6px;
    overflow: hidden;
    transition:
        grid-template-rows 0.35s ease,
        opacity 0.25s ease,
        margin-top 0.35s ease;
}

.drawer-content > .create-room-btn {
    min-height: 0;
    overflow: hidden;
}

.create-room-btn {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    min-width: 0;
    padding: 12px;
    border: 1px dashed #93c5fd;
    border-radius: 12px;
    background: var(--surface-secondary);
    color: var(--text-primary);
    cursor: pointer;
    text-align: left;
    box-sizing: border-box;
    transition:
        background-color 0.2s ease,
        border-color 0.2s ease;
}

.create-room-btn:hover {
    background: var(--accent-soft);
    border-color: var(--accent);
}

.create-room-btn .btn-text-container {
    min-width: 0;
}

/* Collapsed: the button slides away and frees sidebar space */
.create-room-drawer.drawer-collapsed .drawer-content {
    grid-template-rows: 0fr;
    opacity: 0;
    margin-top: 0;
}

.create-room-drawer.drawer-collapsed {
    padding-bottom: 0px;
}
.sidebar-wrapper {
    background: var(--surface);
    color: var(--text-primary);
    border-color: var(--border);
}

.sidebar-header {
    background: var(--surface);
    border-color: var(--border);
}

.room-item:hover {
    background: var(--surface-hover);
}

.room-name {
    color: var(--text-primary);
}

.room-last-message {
    color: var(--text-secondary);
}
</style>
