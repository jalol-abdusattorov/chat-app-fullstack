<template>
    <main class="app-root">
        <button
            class="theme-toggle"
            type="button"
            @click="toggleTheme"
            :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
            :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        >
            <span aria-hidden="true">{{ isDark ? '☀️' : '🌙' }}</span>
            <span>{{ isDark ? 'Light mode' : 'Dark mode' }}</span>
        </button>

        <RouterView />
    </main>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const isDark = ref(false)

onMounted(() => {
    try {
        isDark.value = localStorage.getItem('app-theme') === 'dark'
    } catch {
        isDark.value = false
    }

    applyTheme()
})

function applyTheme() {
    document.documentElement.dataset.theme = isDark.value ? 'dark' : 'light'

    try {
        localStorage.setItem('app-theme', isDark.value ? 'dark' : 'light')
    } catch {
    }
}

function toggleTheme() {
    isDark.value = !isDark.value
    applyTheme()
}

watch(isDark, applyTheme)
</script>

<style>
.app-root {
    width: 100%;
    height: 100%;
    min-height: 0;
    background: var(--app-bg);
    color: var(--text-primary);
}
</style>
