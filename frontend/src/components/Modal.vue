<!-- BaseModal.vue -->
<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

defineEmits(['close']);
</script>

<template>
    <!-- Teleport moves the modal directly under <body> to prevent CSS overflow issues -->
    <Teleport to="body">
        <Transition name="fade">
            <div v-if="isOpen" class="modal-overlay" @click.self="$emit('close')">
                <div class="modal-content">
                    <!-- Header slot -->
                    <header class="modal-header">
                        <slot name="header">Default Title</slot>
                        <button class="close-btn" @click="$emit('close')">&times;</button>
                    </header>

                    <!-- Main body slot -->
                    <section class="modal-body">
                        <slot>Default body text goes here.</slot>
                    </section>

                    <!-- Footer slot -->
                    <footer v-if="$slots.footer" class="modal-footer">
                        <slot name="footer" />
                    </footer>
                </div>
            </div>
        </Transition>
    </Teleport>
</template>

<style scoped>
/* Modal Base Styles */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background: #ffffff;
    border-radius: 12px;
    width: min(90%, 450px);
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    padding: 24px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
}

.modal-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 16px;
}

.close-btn {
    background: transparent;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6b7280;
    line-height: 1;
}

.close-btn:hover {
    color: #111827;
}

/* Fade Transition Styles */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>