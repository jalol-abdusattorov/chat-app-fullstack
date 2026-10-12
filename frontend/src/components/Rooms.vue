<template>
    <div>
        <SingleRoom :room="room" v-for="room in rooms" :key="room.room_id" />
    </div>
</template>

<script>
import SingleRoom from './SingleRoom.vue';

    export default {
        props: ['rooms'],
        components: { SingleRoom }
    }
</script>

<style scoped>

</style>