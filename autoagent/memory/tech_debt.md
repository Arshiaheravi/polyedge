# Tech Debt Log

Issues logged here were too large or risky to fix during the session that found them.
Format: [DATE] [FILE] [TEAM MEMBER] — [issue description]

---

[2026-03-24] CLAUDE.md [Leo] — VIP price shown as $14.99 but admin.py uses 9.99. PROJECT.md also says $9.99. CLAUDE.md needs updating. Low urgency — no user-facing page reads from CLAUDE.md.
[2026-03-24] backend/app/routes/follows.py [Ama] — _activity_cache grows unboundedly (no max-size eviction, just TTL on access). At scale with many users this leaks memory. Fix: add maxsize cap or use an LRU cache (functools.lru_cache won't work for this pattern — use a simple OrderedDict with max entries).
~~[2026-03-24] frontend/index.html [Ama/Priya] — _disclosureCache TTL~~ FIXED session 98 — entries now store `{titles, ts}` with 5-min TTL (`_DISCLOSURE_TTL_MS = 300000`).
[2026-03-26] backend/app/routes/alerts.py [Marcus] — POST /alerts/telegram/webhook has no secret token verification. Telegram supports setWebhook with a `secret_token` param; the backend should check `X-Telegram-Bot-Api-Secret-Token` header. Without this, an attacker who knows a valid verify code could POST a forged webhook to link their own chat_id. Fix: add `TELEGRAM_WEBHOOK_SECRET` to config; reject requests with missing/wrong `X-Telegram-Bot-Api-Secret-Token` header.
