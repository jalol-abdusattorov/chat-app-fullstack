<template>
    <main class="page">
        <div class="shell">
            <aside class="intro">
                <div class="lanyard" aria-hidden="true">
                    <div class="sway">
                        <div class="strap"></div>
                        <div class="clip"></div>

                        <div
                            class="badge"
                            @click="
                                $event.currentTarget.parentElement.classList.remove('tingle');
                                void $event.currentTarget.parentElement.offsetWidth;
                                $event.currentTarget.parentElement.classList.add('tingle')
                            "
                        >
                            <span class="slot"></span>

                            <div class="avatar">
                                {{ email.trim().charAt(0).toUpperCase() || '?' }}
                            </div>

                            <p class="badge-name">Welcome back</p>
                            <p class="badge-handle" :class="{ 'is-empty': !email.trim() }">
                                {{ email.trim() || 'you@example.com' }}
                            </p>
                        </div>
                    </div>
                </div>

                <div class="intro-text">
                    <h2>Pick up where you left off.</h2>
                    <p>Your card updates as you type.</p>
                </div>
            </aside>

            <form class="form" @submit.prevent="handleSubmit">
                <div v-if="authStore.loading" class="loading" role="status">
                    <span class="spinner" aria-hidden="true"></span>
                    Loading...
                </div>

                <header class="form-head">
                    <h1>Log in</h1>
                    <p>Enter your email and password to continue.</p>
                </header>

                <div class="fields">
                    <div class="field">
                        <label for="email">Email</label>
                        <input
                            id="email"
                            v-model="email"
                            type="email"
                            autocomplete="email"
                            required
                        >
                    </div>

                    <div class="field">
                        <label for="password">Password</label>
                        <div class="password">
                            <input
                                id="password"
                                v-model="password"
                                :type="showPassword ? 'text' : 'password'"
                                autocomplete="current-password"
                                required
                            >

                            <button
                                type="button"
                                class="toggle"
                                @click="togglePassword"
                                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                            >
                                <svg v-if="showPassword" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                    <path d="M17.94 17.94A10.9 10.9 0 0 1 12 19c-6.5 0-10-7-10-7a18.3 18.3 0 0 1 4.06-4.94M9.9 5.24A10.4 10.4 0 0 1 12 5c6.5 0 10 7 10 7a18.5 18.5 0 0 1-2.16 3.19M14.12 14.12a3 3 0 1 1-4.24-4.24M1 1l22 22" />
                                </svg>
                                <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
                                    <circle cx="12" cy="12" r="3" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <div class="messages">
                    <p v-if="authStore.error" class="alert" role="alert">{{ authStore.error }}</p>
                </div>

                <button type="submit" class="submit">Log in</button>

                <p class="switch">
                    Don't have an account?
                    <router-link :to="{ name: 'Register' }">Create one</router-link>
                </p>
            </form>
        </div>
    </main>
</template>

<script>
import { useAuthStore } from '../stores/auth';
import { onUnmounted, ref } from 'vue';
import { useRouter } from 'vue-router'

    export default {
        name: "Login",
        setup() {
            const authStore = useAuthStore()
            const router = useRouter()

            const email = ref('')
            const password = ref('')
            const showPassword = ref(false)

            const togglePassword = () => {
                showPassword.value = !showPassword.value
            }

            const handleSubmit = async () => {
                try {
                    const response = await authStore.login({ email: email.value, password: password.value })

                    if (response?.id && response?.email) {
                        router.replace({ name: "Home" })
                    }
                } catch (exc) {
                    
                }
            }
            onUnmounted(() => {
                authStore.error = null
            })

            return { email, password, showPassword, togglePassword, authStore, handleSubmit }
        }
    }
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600..800&family=DM+Sans:opsz,wght@9..40,400..700&display=swap');

/* =========================
   TOKENS
   ========================= */

.page {
    --saffron: #f7c948;
    --cobalt: #2f45e0;
    --cobalt-deep: #2337c2;
    --ink: #1f2430;
    --muted: #646c7e;
    --line: #cdd2de;
    --line-strong: #9aa2b6;
    --surface: #ffffff;
    --danger: #c4261d;
    --danger-bg: #fdecea;

    --font-display: 'Bricolage Grotesque', ui-sans-serif, system-ui, sans-serif;
    --font-body: 'DM Sans', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;

    padding: 32px 16px;
    color: var(--ink);
    font-family: var(--font-body);
    font-optical-sizing: auto;
    -webkit-font-smoothing: antialiased;
}

.page *,
.page *::before,
.page *::after {
    box-sizing: border-box;
}

/* =========================
   SHELL
   ========================= */

.shell {
    display: grid;
    grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
    min-height: 580px;
    max-width: 1040px;
    margin: 0 auto;
    overflow: hidden;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 28px;
    box-shadow: 0 30px 60px -34px rgba(31, 36, 48, 0.4);
    text-align: left;
}

/* =========================
   LEFT PANEL: THE BADGE
   ========================= */

.intro {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 40px;
    padding: 0 40px 44px;
    overflow: hidden;
    background: var(--saffron);
}

.lanyard {
    width: min(100%, 250px);
    margin: 0 auto;
    transform: rotate(-2deg);
    transform-origin: 50% 0;
    animation: swing 1.8s ease-out 0.2s both;
}

@keyframes swing {
    0%   { transform: rotate(8deg); }
    22%  { transform: rotate(-6deg); }
    44%  { transform: rotate(4deg); }
    66%  { transform: rotate(-3deg); }
    100% { transform: rotate(-2deg); }
}

/* Whole hanging unit; pivots from the top of the strap when the badge is pressed */
.sway {
    display: flow-root;
    transform-origin: 50% 0;
}

.sway.tingle {
    animation: tingle 0.75s ease-out;
}

@keyframes tingle {
    0%   { transform: rotate(0deg); }
    14%  { transform: rotate(6deg); }
    32%  { transform: rotate(-5deg); }
    50%  { transform: rotate(3.5deg); }
    68%  { transform: rotate(-2deg); }
    84%  { transform: rotate(1deg); }
    100% { transform: rotate(0deg); }
}

.strap {
    width: 24px;
    height: 96px;
    margin: -24px auto 0;
    background: var(--cobalt);
    border-inline: 2px solid var(--ink);
}

.clip {
    position: relative;
    z-index: 2;
    width: 18px;
    height: 30px;
    margin: 0 auto -16px;
    background: #e7e9f0;
    border: 2px solid var(--ink);
    border-radius: 6px;
}

.badge {
    position: relative;
    z-index: 1;
    padding: 44px 22px 28px;
    text-align: center;
    background: var(--surface);
    border: 2px solid var(--ink);
    border-radius: 18px;
    box-shadow: 0 22px 30px -16px rgba(90, 60, 0, 0.55);
    cursor: pointer;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
    transform-origin: 50% 0;
    transition: transform 0.12s ease;
}

.badge:active {
    transform: scale(0.97);
}

.slot {
    position: absolute;
    top: 12px;
    left: 50%;
    width: 56px;
    height: 10px;
    transform: translateX(-50%);
    background: var(--saffron);
    border: 2px solid var(--ink);
    border-radius: 999px;
}

.avatar {
    display: grid;
    place-items: center;
    width: 84px;
    height: 84px;
    margin: 0 auto 16px;
    color: #ffffff;
    background: var(--cobalt);
    border: 2px solid var(--ink);
    border-radius: 50%;
    font-family: var(--font-display);
    font-size: 2.4rem;
    font-weight: 800;
    line-height: 1;
}

.badge-name {
    margin: 0;
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -0.02em;
}

.badge-handle {
    margin: 4px 0 0;
    color: var(--cobalt);
    font-size: 0.9rem;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.badge .is-empty {
    opacity: 0.45;
}

.intro-text h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(2rem, 3.4vw, 2.9rem);
    font-weight: 800;
    line-height: 1.02;
    letter-spacing: -0.03em;
}

.intro-text p {
    margin: 12px 0 0;
    font-size: 0.95rem;
    font-weight: 500;
}

/* =========================
   FORM
   ========================= */

.form {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 48px 52px 44px;
}

.form-head h1 {
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(1.6rem, 2.4vw, 2rem);
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.1;
}

.form-head p {
    margin: 8px 0 0;
    color: var(--muted);
    font-size: 0.95rem;
}

.fields {
    display: grid;
    gap: 20px;
    margin-top: 30px;
}

.field label {
    display: block;
    margin-bottom: 6px;
    font-size: 0.875rem;
    font-weight: 600;
}

.field input {
    display: block;
    width: 100%;
    height: 46px;
    padding: 0 14px;
    color: var(--ink);
    background: var(--surface);
    border: 1.5px solid var(--line);
    border-radius: 8px;
    font: inherit;
    font-size: 0.9375rem;
    outline: none;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.field input:hover {
    border-color: var(--line-strong);
}

.field input:focus {
    border-color: var(--cobalt);
    box-shadow: 0 0 0 3px rgba(47, 69, 224, 0.18);
}

/* Password field */

.password {
    position: relative;
}

.field .password input {
    padding-right: 48px;
}

.toggle {
    position: absolute;
    top: 50%;
    right: 6px;
    display: grid;
    place-items: center;
    width: 34px;
    height: 34px;
    padding: 0;
    transform: translateY(-50%);
    color: var(--muted);
    background: transparent;
    border: 0;
    border-radius: 6px;
    cursor: pointer;
    transition: color 0.15s ease, background-color 0.15s ease;
}

.toggle:hover {
    color: var(--ink);
    background: #eef0f6;
}

.toggle:focus-visible {
    outline: 2px solid var(--cobalt);
    outline-offset: 1px;
}

/* =========================
   MESSAGES
   ========================= */

.messages {
    display: grid;
    gap: 8px;
    margin-top: 18px;
}

.messages:empty {
    display: none;
}

.alert {
    margin: 0;
    padding: 10px 14px;
    color: var(--danger);
    background: var(--danger-bg);
    border-left: 3px solid var(--danger);
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 600;
}

/* =========================
   SUBMIT
   ========================= */

.submit {
    display: block;
    width: 100%;
    height: 50px;
    margin-top: 26px;
    color: #ffffff;
    background: var(--cobalt);
    border: 0;
    border-radius: 10px;
    font: inherit;
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.submit:hover:not(:disabled) {
    background: var(--cobalt-deep);
    transform: translateY(-1px);
    box-shadow: 0 10px 18px -8px rgba(47, 69, 224, 0.55);
}

.submit:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: none;
}

.submit:focus-visible {
    outline: 2px solid var(--cobalt);
    outline-offset: 3px;
}

.submit:disabled {
    color: #8a91a3;
    background: #e3e6ee;
    cursor: not-allowed;
}

.switch {
    margin: 18px 0 0;
    color: var(--muted);
    font-size: 0.9rem;
    text-align: center;
}

.switch a {
    color: var(--cobalt);
    font-weight: 600;
    text-decoration: none;
}

.switch a:hover {
    text-decoration: underline;
}

.switch a:focus-visible {
    outline: 2px solid var(--cobalt);
    outline-offset: 2px;
    border-radius: 3px;
}

/* =========================
   LOADING
   ========================= */

.loading {
    position: absolute;
    top: 20px;
    right: 24px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    color: var(--muted);
    background: #eef0f6;
    border-radius: 999px;
    font-size: 0.8125rem;
    font-weight: 500;
}

.spinner {
    width: 12px;
    height: 12px;
    border: 2px solid var(--line-strong);
    border-top-color: var(--cobalt);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* =========================
   RESPONSIVE
   ========================= */

@media (max-width: 860px) {
    .shell {
        grid-template-columns: 1fr;
        min-height: 0;
    }

    .intro {
        padding: 32px 28px;
    }

    .lanyard {
        display: none;
    }

    .intro-text h2 {
        font-size: 1.9rem;
    }

    .form {
        padding: 32px 24px 28px;
    }
}

@media (max-width: 560px) {
    .page {
        padding: 16px 12px;
    }

    .shell {
        border-radius: 20px;
    }
}

@media (prefers-reduced-motion: reduce) {
    .lanyard,
    .sway.tingle {
        animation: none;
    }

    .spinner {
        animation-duration: 1.6s;
    }

    .submit,
    .toggle,
    .field input {
        transition: none;
    }
}
</style>