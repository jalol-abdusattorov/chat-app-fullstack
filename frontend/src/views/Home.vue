<template>
    <div>
        <router-link :to="{ name: 'Room', params: { 'room_id': 1234567 } }">Room 1, id: 1234567</router-link>
    </div>
</template>

<script>
    export default {
        
    }
</script>

<style scoped>

</style>