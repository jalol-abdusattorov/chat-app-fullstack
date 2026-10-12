<template>
    <aside class="sidebar-wrapper">
        <Rooms :rooms="rooms" />
    </aside>
</template>

<script>
import Rooms from './Rooms.vue';

export default {
    name: 'ChatSideBar',
    components: { Rooms },

    props: {
        rooms: {
            type: Array,
            default: () => []
        }
    }
};
</script>