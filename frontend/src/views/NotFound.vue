<template>
  <main class="page">
    <div class="card">
      <header class="banner">
        <div class="address">
          <span class="code">404</span>
          <span class="path">{{ $route.fullPath }}</span>
        </div>
        <p class="banner-note">No page lives at this address.</p>
      </header>

      <section class="content">
        <h1>We can't find that page.</h1>
        <p class="lead">Double-check the address, or jump back in from here.</p>

        <div class="actions">
          <template v-if="authStore.isAuthenticated">
            <router-link :to="{ name: 'Home' }" class="btn btn--primary">Back to home</router-link>
          </template>
          <template v-else>
            <router-link :to="{ name: 'Login' }" class="btn btn--primary">Log in</router-link>
            <router-link :to="{ name: 'Register' }" class="btn btn--secondary">Create account</router-link>
          </template>
        </div>
      </section>
    </div>
  </main>
</template>

<script>
import { useAuthStore } from '../stores/auth';

    export default {
        name: "NotFound",
        setup() {
            const authStore = useAuthStore()

            return { authStore }
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
   CARD
   ========================= */

.card {
    max-width: 720px;
    margin: 0 auto;
    overflow: hidden;
    background: var(--page-surface);
    border: 1px solid var(--line);
    border-radius: 28px;
    box-shadow: 0 30px 60px -34px rgba(31, 36, 48, 0.4);
    text-align: left;
}

/* =========================
   BANNER: THE ADDRESS
   ========================= */

.banner {
    padding: 64px 48px 48px;
    background: var(--saffron);
}

.address {
    display: flex;
    align-items: center;
    gap: 14px;
    width: fit-content;
    min-width: min(100%, 320px);
    max-width: 100%;
    padding: 10px 28px 10px 10px;
    background: var(--page-surface);
    border: 2px solid var(--ink);
    border-radius: 999px;
    box-shadow: 0 16px 24px -14px rgba(90, 60, 0, 0.55);
    animation: nudge 0.6s ease-in-out 0.35s both;
}

/* A quick "nope" shake, once, when the page loads */
@keyframes nudge {
    0%, 100% { transform: translateX(0); }
    15%      { transform: translateX(-9px); }
    30%      { transform: translateX(9px); }
    45%      { transform: translateX(-6px); }
    60%      { transform: translateX(5px); }
    75%      { transform: translateX(-3px); }
    90%      { transform: translateX(2px); }
}

.code {
    display: grid;
    flex: none;
    place-items: center;
    width: 44px;
    height: 44px;
    color: #ffffff;
    background: var(--cobalt);
    border: 2px solid var(--ink);
    border-radius: 50%;
    font-family: var(--font-display);
    font-size: 0.85rem;
    font-weight: 800;
    letter-spacing: -0.02em;
}

.path {
    min-width: 0;
    /* overflow:hidden (needed for the ellipsis) clips anything outside the box,
       and the wavy underline sits below the text. The extra bottom padding gives it
       room; the matching negative margin keeps the text vertically centred. */
    padding-bottom: 10px;
    margin-bottom: -10px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 1.125rem;
    font-weight: 600;
    text-decoration: underline wavy var(--page-danger);
    text-decoration-thickness: 1.5px;
    text-underline-offset: 6px;
}

.banner-note {
    margin: 18px 0 0 6px;
    font-size: 0.95rem;
    font-weight: 500;
}

/* =========================
   CONTENT
   ========================= */

.content {
    padding: 40px 48px 44px;
}

.content h1 {
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(1.9rem, 3.2vw, 2.5rem);
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.08;
}

.lead {
    max-width: 44ch;
    margin: 14px 0 0;
    color: var(--muted);
    font-size: 1rem;
    line-height: 1.55;
}

.actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 30px;
}

.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 170px;
    height: 50px;
    padding: 0 28px;
    border: 1.5px solid transparent;
    border-radius: 10px;
    font-size: 0.9375rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: background-color 0.15s ease, border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.btn:focus-visible {
    outline: 2px solid var(--cobalt);
    outline-offset: 3px;
}

.btn--primary {
    color: #ffffff;
    background: var(--cobalt);
}

.btn--primary:hover {
    background: var(--cobalt-deep);
    transform: translateY(-1px);
    box-shadow: 0 10px 18px -8px rgba(47, 69, 224, 0.55);
}

.btn--primary:active {
    transform: translateY(0);
    box-shadow: none;
}

.btn--secondary {
    color: var(--ink);
    background: var(--page-surface);
    border-color: var(--line-strong);
}

.btn--secondary:hover {
    background: var(--app-bg);
    border-color: var(--ink);
}

/* =========================
   RESPONSIVE
   ========================= */

@media (max-width: 560px) {
    .page {
        padding: 16px 12px;
    }

    .card {
        border-radius: 20px;
    }

    .banner {
        padding: 40px 24px 32px;
    }

    .path {
        font-size: 1rem;
    }

    .content {
        padding: 28px 24px 28px;
    }

    .btn {
        flex: 1 1 100%;
    }
}

@media (prefers-reduced-motion: reduce) {
    .address {
        animation: none;
    }

    .btn {
        transition: none;
    }
}
</style>
