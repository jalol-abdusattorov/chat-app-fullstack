<template>
    <aside class="sidebar-wrapper" :style="{ width: sidebarWidth + 'px' }">
        <div class="sidebar-header">
            <h1 class="rooms-title">Rooms</h1>
            <span class="chat-count-badge">
                {{ roomsStore.rooms.length }} chats
            </span>
        </div>

        <!-- Scrollable rooms list -->
        <div class="rooms-container">
            <Rooms />
        </div>

        <!-- Fixed bottom action -->
        <div class="sidebar-footer">
            <button class="create-room-btn" @click="openModal">
                <span class="plus-icon-wrapper">+</span>
                <div class="btn-text-container">
                    <span class="btn-title">Create Room</span>
                    <span class="btn-subtitle">Start a new conversation</span>
                </div>
            </button>
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
                    placeholder="e.g. Project Team"
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
                        :disabled="!roomName.trim()"
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
import { ref, onBeforeUnmount } from 'vue';
import { useRoomsStore } from '../stores/RoomsStore.js';
import Rooms from './Rooms.vue';
import Modal from './Modal.vue';
import { useAuthStore } from '../stores/auth.js';
import { useUsersStore } from '../stores/UsersStore.js';

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
        let debounceTimer = null;

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

            if (!name) {
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
                resetForm();
                closeModal();
            } catch (err) {
                formError.value = err.response?.data?.detail || 'Failed to create room. Please try again.';
            }
        };

        onBeforeUnmount(() => {
            stopResize();
        });

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
            removeMember,
            error,
        };
    }
};
</script>

<style scoped>
.sidebar-wrapper {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        Helvetica, Arial, sans-serif;
    height: 100vh;
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    position: relative;
    flex-shrink: 0;
}

.sidebar-header {
    padding: 20px 16px 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f3f4f6;
}

.rooms-title {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 700;
    color: #111827;
}

.chat-count-badge {
    font-size: 0.75rem;
    font-weight: 600;
    background-color: #f3f4f6;
    color: #4b5563;
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
    border-top: 1px solid #e5e7eb;
    background-color: #ffffff;
}

.create-room-btn {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 12px;
    width: 100%;
    padding: 12px 16px;
    border: 2px dashed #3b82f6;
    border-radius: 12px;
    background: #ffffff;
    color: #111827;
    cursor: pointer;
    transition: background 0.2s ease, border-color 0.2s ease;
    text-align: left;
}

.create-room-btn:hover {
    background: #f8fafc;
    border-color: #2563eb;
}

.create-room-btn:active {
    background: #f1f5f9;
}

.plus-icon-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: #eff6ff;
    color: #2563eb;
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
    color: #2563eb;
}

.btn-subtitle {
    font-size: 0.78rem;
    color: #6b7280;
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
    color: #111827;
}

.modal-heading p {
    margin: 0 0 16px;
    font-size: 0.95rem;
    color: #6b7280;
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
    color: #374151;
}

.create-room-form input,
.create-room-form textarea,
.create-room-form select {
    width: 100%;
    box-sizing: border-box;
    padding: 12px 14px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    background: #ffffff;
    color: #111827;
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
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.search-results-list {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    max-height: 150px;
    overflow-y: auto;
    margin-top: 4px;
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
    background-color: #f3f4f6;
}

.user-info-display {
    display: flex;
    flex-direction: column;
}

.username-text {
    font-weight: 600;
    color: #111827;
}

.display-name-text {
    font-size: 0.78rem;
    color: #6b7280;
}

.add-member-btn {
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 4px;
    width: 22px;
    height: 22px;
    cursor: pointer;
}

.added-members-section {
    margin-top: 12px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 10px 12px;
}

.added-members-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.82rem;
    font-weight: 600;
    color: #4b5563;
    margin-bottom: 8px;
}

.member-count-badge {
    background-color: #eff6ff;
    color: #2563eb;
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
    background: #ffffff;
    border: 1px solid #d1d5db;
    padding: 4px 10px 4px 4px;
    border-radius: 20px;
    font-size: 0.85rem;
    color: #111827;
}

.member-avatar {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background-color: #2563eb;
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
    color: #9ca3af;
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
    color: #dc2626;
}

.form-error {
    margin: 8px 0;
    padding: 8px 12px;
    background-color: #fef2f2;
    border: 1px solid #fee2e2;
    border-radius: 8px;
    color: #dc2626;
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
    border: 1px solid #d1d5db;
    background: #ffffff;
    color: #374151;
}

.cancel-btn:hover {
    background: #f3f4f6;
}

.submit-btn {
    border: none;
    background: #2563eb;
    color: #ffffff;
}

.submit-btn:hover:not(:disabled) {
    background: #1d4ed8;
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
</style>