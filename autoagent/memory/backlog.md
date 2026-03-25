# Backlog

---

## HIGH PRIORITY — UI/UX Tasks (doable in current UI/UX-only mode)

- [ ] Generate hero background image using Nano Banana API (nanobananaapi.ai, key in credentials.env) — read `autoagent/skills/novabana.md` for exact endpoint + code; prompt: "Dark cinematic background, financial trading platform, glowing green neon data streams, deep navy blue, abstract, premium fintech aesthetic, no text, no people", save to `frontend/assets/hero-bg.jpg`; wire into hero section CSS as `background-image: url('assets/hero-bg.jpg')` with gradient fallback; also attempt logo generation: "PE monogram logo, minimal, electric green on dark, fintech style", save to `frontend/assets/logo.png`, replace any text-only logo in the nav
- [ ] Bettor card rank badge + leaderboard card visual overhaul — (1) add gold/silver/bronze rank badge pill to top-3 cards, green accent for 4-10, subdued for 11+; (2) add hover lift + glow effect on all leaderboard cards; (3) add "Last active X mins ago" relative timestamp to each card using bet timestamp data; (4) make Follow button on each card more prominent with animated pulse on hover
- [ ] Empty state illustrations + modal polish — (1) when follows tab is empty show centered card: inline SVG bell icon + "You're not following anyone yet" + "Browse Leaderboard →" CTA; (2) add `backdrop-filter: blur(4px)` to all modal overlays; (3) add Escape key to close any open modal; (4) add pricing tier tooltip on hover of locked features ("Unlock with Basic →"); (5) animate hero social proof counter from 800→847 on page load
- [ ] Keyboard accessibility — add `document.addEventListener('keydown', e => { if (e.key === 'Escape') closeUpgradeModal() })` and wire it to any open modal overlay. Also add `Enter` key support for the primary action button in any open modal. Catches WAI-ARIA pattern for dialogs.

---

## BACKEND PENDING (blocked — current mission is UI/UX-only; pick when backend mode resumes)

- [ ] Win Rate computation — compute from activity data in `polymarket.py` (profitable bets / total bets from last 20 records), expose as `win_rate_pct` in bettor profile API, render in the 2×2 leaderboard card slot currently showing "—".
- [ ] Empowerment-framed bet notification copy — change `dispatch_bet_notification()` in `services/notifications.py` from "0xABCD placed a bet on [Market]" to "Top bettor you follow just moved on [Market] — 68% win rate this month".
- [ ] @lru_cache on get_settings() — add `@functools.lru_cache()` to `get_settings()` in `backend/app/config.py`. 2-line change, zero risk.
- [ ] Per-bettor notification budget — add `max_alerts_per_bettor_per_day` to `AlertSetting` model; scheduler skips if daily limit reached per bettor.
- [ ] WebSocket real-time notifications — replace 30s APScheduler polling with Polymarket's `/v1/ws/markets` WebSocket. Reduces detection latency from ~30s to ~1s; key VIP differentiator. Change in `scheduler.py`.

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
