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
                                {{ display_name.trim().charAt(0).toUpperCase() || '?' }}
                            </div>

                            <p class="badge-name" :class="{ 'is-empty': !display_name.trim() }">
                                {{ display_name.trim() || 'Your name' }}
                            </p>
                            <p class="badge-handle" :class="{ 'is-empty': !username.trim() }">
                                {{ '@' + (username.trim() || 'username') }}
                            </p>

                            <p class="badge-bio" :class="{ 'is-empty': !bio.trim() }">
                                {{ bio.trim() || 'Your bio will show up here.' }}
                            </p>
                        </div>
                    </div>
                </div>

                <div class="intro-text">
                    <h2>Make a name for yourself.</h2>
                    <p>Your card updates as you type.</p>
                </div>
            </aside>

            <form class="form" @submit.prevent="handleSubmit">
                <div v-if="authStore.loading" class="loading" role="status">
                    <span class="spinner" aria-hidden="true"></span>
                    Loading...
                </div>

                <header class="form-head">
                    <h1>Create your account</h1>
                    <p>Fill in the details below to get started.</p>
                </header>

                <div class="fields">
                    <div class="field">
                        <label for="username">Username</label>
                        <input
                            id="username"
                            v-model="username"
                            type="text"
                            autocomplete="username"
                            required
                        >
                        <p class="hint">At least 5 characters</p>
                    </div>

                    <div class="field">
                        <label for="display-name">Display name</label>
                        <input
                            id="display-name"
                            v-model="display_name"
                            type="text"
                            autocomplete="nickname"
                            required
                        >
                        <p class="hint">At least 5 characters</p>
                    </div>

                    <div class="field field--full">
                        <label for="bio">About me <span class="optional">(optional)</span></label>
                        <textarea
                            id="bio"
                            v-model="bio"
                            maxlength="200"
                            rows="4"
                            placeholder="Tell us a little about yourself..."
                        ></textarea>

                        <div class="bio-footer">
                            <span>Introduce yourself to other users</span>
                            <span class="counter" :class="{ 'is-near': bio.length >= 180 }">
                                {{ bio.length }}/200
                            </span>
                        </div>
                    </div>

                    <div class="field field--full">
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
                                autocomplete="new-password"
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

                    <div class="field">
                        <label for="password-confirmation">Confirm password</label>
                        <div class="password">
                            <input
                                id="password-confirmation"
                                v-model="passwordConfirmation"
                                :type="showPassword ? 'text' : 'password'"
                                autocomplete="new-password"
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

                <div class="terms">
                    <input id="terms" type="checkbox" v-model="termsAccepted" required>
                    <label for="terms">Accept terms and conditions</label>
                </div>

                <div class="messages">
                    <p
                        v-if="!validPassword && (username || display_name || email || password || passwordConfirmation)"
                        class="alert"
                        role="alert"
                    >{{ error }}</p>
                    <p v-if="authStore.error" class="alert" role="alert">{{ authStore.error }}</p>
                </div>

                <button type="submit" class="submit" :disabled="!termsAccepted || !validPassword">
                    Create account
                </button>

                <p class="switch">
                    Already have an account?
                    <router-link :to="{ name: 'Login' }">Log in</router-link>
                </p>
            </form>
        </div>
    </main>
</template>

<script>
    import { useRouter } from 'vue-router';
    import { useAuthStore } from '../stores/auth';
    import { computed, onUnmounted, ref } from 'vue';

    export default {
        name: "Register",
        setup() {
            const authStore = useAuthStore()
            const router = useRouter()

            const termsAccepted = ref(false)
            const username = ref('')
            const display_name = ref('')
            const bio = ref('')
            const email = ref('')
            const password = ref('')
            const passwordConfirmation = ref('')
            const showPassword = ref(false)
            const error = ref('')

            const togglePassword = () => {
                showPassword.value = !showPassword.value
            }

            const validPassword = computed(() => {
                if (username.value.trim().length <= 4) {
                    error.value = "Username is too short"
                    return false
                }
                if (display_name.value.trim().length <= 4) {
                    error.value = "Display name is too short"
                    return false
                }

                if (!email.value) {
                    error.value = "Enter your email"
                    return false
                }
                if (!password.value) {
                    error.value = "Enter password"
                    return false
                }

                if (password.value !== passwordConfirmation.value) {
                    error.value = "Password is not same as confirmation password"
                    return false
                }

                error.value = null
                return true
            })

            const handleSubmit = async () => {
                if (password.value !== passwordConfirmation.value) {
                    authStore.error = "Password doesn't match confirmation password"
                    passwordConfirmation.value = ''
                    return
                }
                try {
                    const response = await authStore.register({
                        username: username.value,
                        display_name: display_name.value,
                        email: email.value,
                        password: password.value,
                        bio: bio.value
                    })

                    if (response === "error") {
                        return
                    }

                    await authStore.login({
                        email: email.value,
                        password: password.value
                    })

                    router.push({ name: "Home" })
                } catch (err) {
                    console.error(err)
                }
            }

            onUnmounted(() => {
                authStore.error = null
                error.value = null
            })

            return {
                username,
                email,
                password,
                passwordConfirmation,
                showPassword,
                togglePassword,
                termsAccepted,
                error,
                validPassword,
                authStore,
                handleSubmit,
                display_name,
                bio,
            }
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
    --ink: var(--text-primary);
    --muted: var(--text-secondary);
    --line: var(--border);
    --line-strong: var(--border-strong);
    --page-surface: var(--surface);
    --page-danger: var(--danger);
    --page-danger-bg: var(--danger-soft);
    --warn: #a15c00;

    --font-display: 'Bricolage Grotesque', ui-sans-serif, system-ui, sans-serif;
    --font-body: 'DM Sans', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;

    box-sizing: border-box;
    width: 100%;
    height: 100vh;
    height: 100dvh;
    overflow-y: scroll;
    overflow-x: hidden;
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
    max-width: 1040px;
    margin: 0 auto;
    overflow: hidden;
    background: var(--page-surface);
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
    background: var(--surface-secondary);
    border: 2px solid var(--ink);
    border-radius: 6px;
}

.badge {
    position: relative;
    z-index: 1;
    padding: 44px 22px 26px;
    text-align: center;
    background: var(--page-surface);
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
    overflow-wrap: anywhere;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
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

.badge-bio {
    margin: 16px 0 0;
    padding-top: 16px;
    border-top: 2px dashed var(--line);
    color: var(--muted);
    font-size: 0.875rem;
    line-height: 1.5;
    overflow-wrap: anywhere;
    display: -webkit-box;
    -webkit-line-clamp: 4;
    line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
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
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 20px 16px;
    margin-top: 30px;
}

.field--full {
    grid-column: 1 / -1;
}

.field label {
    display: block;
    margin-bottom: 6px;
    font-size: 0.875rem;
    font-weight: 600;
}

.optional {
    color: var(--muted);
    font-weight: 400;
}

.field input,
.field textarea {
    display: block;
    width: 100%;
    height: 46px;
    padding: 0 14px;
    color: var(--ink);
    background: var(--page-surface);
    border: 1.5px solid var(--line);
    border-radius: 8px;
    font: inherit;
    font-size: 0.9375rem;
    outline: none;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.field textarea {
    height: auto;
    min-height: 104px;
    padding: 12px 14px;
    line-height: 1.55;
    resize: vertical;
}

.field textarea::placeholder {
    color: var(--text-muted);
}

.field input:hover,
.field textarea:hover {
    border-color: var(--line-strong);
}

.field input:focus,
.field textarea:focus {
    border-color: var(--cobalt);
    box-shadow: 0 0 0 3px rgba(47, 69, 224, 0.18);
}

.hint {
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 0.8125rem;
}

.bio-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-top: 6px;
    color: var(--muted);
    font-size: 0.8125rem;
}

.counter {
    white-space: nowrap;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
}

.counter.is-near {
    color: var(--warn);
}

/* Password fields */

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
    background: var(--app-bg);
}

.toggle:focus-visible {
    outline: 2px solid var(--cobalt);
    outline-offset: 1px;
}

/* =========================
   TERMS
   ========================= */

.terms {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 24px;
}

.terms input {
    appearance: none;
    -webkit-appearance: none;
    flex: none;
    width: 20px;
    height: 20px;
    margin: 0;
    background: var(--page-surface);
    border: 1.5px solid var(--line-strong);
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.15s ease, border-color 0.15s ease;
}

.terms input:checked {
    background: var(--cobalt) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12.5l4.5 4.5L19 7.5'/%3E%3C/svg%3E") center / 14px no-repeat;
    border-color: var(--cobalt);
}

.terms input:focus-visible {
    outline: 2px solid var(--cobalt);
    outline-offset: 2px;
}

.terms label {
    font-size: 0.875rem;
    cursor: pointer;
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
    color: var(--page-danger);
    background: var(--page-danger-bg);
    border-left: 3px solid var(--page-danger);
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
    margin-top: 22px;
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
    color: var(--text-muted);
    background: var(--border);
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
    background: var(--app-bg);
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

    .fields {
        grid-template-columns: 1fr;
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
    .field input,
    .field textarea {
        transition: none;
    }
}

/* =========================================
   DARK THEME OVERRIDES — POLISHED & ACCESSIBLE
   ========================================= */

:global(html[data-theme="dark"]) .page {
    --ink: #f8fafc;
    --muted: #94a3b8;
    --line: #334155;
    --line-strong: #475569;
    --page-surface: #1e293b;
    --cobalt: #3b82f6;
    --cobalt-deep: #2563eb;
}

/* Fix main container in dark mode */
:global(html[data-theme="dark"]) .shell {
    background: #1e293b;
    border-color: #334155;
    box-shadow: 0 30px 60px -30px rgba(0, 0, 0, 0.7);
}

/* Replace harsh bright yellow background with a rich dark gradient */
:global(html[data-theme="dark"]) .intro {
    background: linear-gradient(160deg, #1e3a8a 0%, #1e293b 100%);
    color: #f8fafc;
}

/* Update lanyard and hanging slot colors */
:global(html[data-theme="dark"]) .strap {
    background: #3b82f6;
    border-color: #0f172a;
}

:global(html[data-theme="dark"]) .clip {
    background: #334155;
    border-color: #0f172a;
}

:global(html[data-theme="dark"]) .slot {
    background: #3b82f6;
    border-color: #0f172a;
}

/* Hanging ID badge card */
:global(html[data-theme="dark"]) .badge {
    background: #0f172a;
    border-color: #334155;
    box-shadow: 0 20px 30px -15px rgba(0, 0, 0, 0.6);
}

:global(html[data-theme="dark"]) .badge-name {
    color: #f8fafc;
}

:global(html[data-theme="dark"]) .badge-handle {
    color: #60a5fa; /* Higher contrast light blue instead of dark blue */
}

:global(html[data-theme="dark"]) .badge-bio {
    color: #cbd5e1;
    border-top-color: #334155;
}

:global(html[data-theme="dark"]) .avatar {
    background: #2563eb;
    border-color: #0f172a;
    color: #ffffff;
}

:global(html[data-theme="dark"]) .intro-text h2,
:global(html[data-theme="dark"]) .intro-text p {
    color: #f8fafc;
}

/* Form inputs & fields */
:global(html[data-theme="dark"]) .field input,
:global(html[data-theme="dark"]) .field textarea {
    background: #172033;
    color: #f8fafc;
    border-color: #334155;
}

:global(html[data-theme="dark"]) .field input:hover,
:global(html[data-theme="dark"]) .field textarea:hover {
    border-color: #475569;
}

:global(html[data-theme="dark"]) .field input:focus,
:global(html[data-theme="dark"]) .field textarea:focus {
    border-color: #60a5fa;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
}

:global(html[data-theme="dark"]) .hint,
:global(html[data-theme="dark"]) .bio-footer,
:global(html[data-theme="dark"]) .optional {
    color: #94a3b8;
}

:global(html[data-theme="dark"]) .toggle {
    color: #94a3b8;
}

:global(html[data-theme="dark"]) .toggle:hover {
    color: #f8fafc;
    background: #334155;
}

/* Terms Checkbox */
:global(html[data-theme="dark"]) .terms label {
    color: #cbd5e1;
}

:global(html[data-theme="dark"]) .terms input[type="checkbox"] {
    accent-color: #3b82f6;
}

/* Submit & Links */
:global(html[data-theme="dark"]) .submit {
    background: #2563eb;
    color: #ffffff;
}

:global(html[data-theme="dark"]) .submit:hover:not(:disabled) {
    background: #1d4ed8;
    box-shadow: 0 8px 20px -6px rgba(37, 99, 235, 0.5);
}

:global(html[data-theme="dark"]) .submit:disabled {
    background: #334155;
    color: #64748b;
    box-shadow: none;
}

:global(html[data-theme="dark"]) .switch a {
    color: #60a5fa;
}

:global(html[data-theme="dark"]) .switch a:hover {
    color: #93c5fd;
}
</style>
