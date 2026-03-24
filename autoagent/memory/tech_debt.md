# Tech Debt Log

Issues logged here were too large or risky to fix during the session that found them.
Format: [DATE] [FILE] [TEAM MEMBER] — [issue description]

---

[2026-03-24] CLAUDE.md [Leo] — VIP price shown as $14.99 but admin.py uses 9.99. PROJECT.md also says $9.99. CLAUDE.md needs updating. Low urgency — no user-facing page reads from CLAUDE.md.
[2026-03-24] backend/app/routes/follows.py [Ama] — _activity_cache grows unboundedly (no max-size eviction, just TTL on access). At scale with many users this leaks memory. Fix: add maxsize cap or use an LRU cache (functools.lru_cache won't work for this pattern — use a simple OrderedDict with max entries).
