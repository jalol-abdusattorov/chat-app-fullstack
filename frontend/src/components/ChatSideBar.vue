<template>
    <aside class="sidebar-wrapper" :style="{ width: sidebarWidth + 'px' }">
        <div class="sidebar-header">
            <h1 class="rooms-title">Rooms</h1>
            <span class="chat-count-badge">{{ roomsStore.rooms.length }} chats</span>
        </div>

        <div class="rooms-container">
            <Rooms />
        </div>

        <!-- Resize Handle -->
        <div class="resize-handle" @mousedown="startResize"></div>
    </aside>
</template>

<script>
import { ref } from 'vue';
import Rooms from './Rooms.vue';
import { useRoomsStore } from '../stores/RoomsStore.js';

export default {
    name: 'ChatSideBar',
    components: { Rooms },

    setup() {
        const roomsStore = useRoomsStore()
        const sidebarWidth = ref(330);
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

        return {
            sidebarWidth,
            startResize,
            roomsStore
        };
    }
};
</script>

<style scoped>
.sidebar-wrapper {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    height: 100vh;
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    position: relative; /* Required for absolute positioning of the resize handle */
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
    overflow-y: auto;
}

/* Horizontal Resize Handle */
.resize-handle {
    position: absolute;
    top: 0;
    right: -4px; /* Centered right on the border edge */
    width: 8px;
    height: 100%;
    cursor: ew-resize;
    z-index: 10;
}

.resize-handle:hover {
    background-color: rgba(59, 130, 246, 0.2); /* Soft blue indicator on hover */
}
</style>