# CLAUDE.md — PolyEdge Project Instructions

## What is this project?

PolyEdge is a fintech SaaS platform that tracks the top 100 most profitable Polymarket bettors, lets users subscribe to specific bettors, and fires instant notifications (Telegram + web push) the moment a followed bettor places a new bet — so users can copy the bet immediately.

## Architecture

```
backend/app/
  main.py            → FastAPI app factory, CORS, startup/shutdown lifespan
  database.py        → SQLAlchemy engine, Base, get_db dependency
  models.py          → User, BettorFollow, AlertSetting, BetEvent
  config.py          → Pydantic Settings (reads from .env)
  auth.py            → JWT encode/decode, password hashing, get_current_user
  routes/
    auth.py          → POST /auth/register, /auth/login, GET /auth/me
    bettors.py       → GET /bettors, GET /bettors/{address}
    follows.py       → GET/POST/DELETE /follows
    alerts.py        → GET/PUT /alerts/settings, POST /alerts/telegram/*
    payments.py      → POST /payments/checkout, /payments/webhook, GET /payments/portal
    admin.py         → GET /admin/stats (header auth)
  services/
    polymarket.py    → httpx client for Polymarket data API
    notifications.py → Telegram sendMessage + web push dispatcher
    stripe_service.py → Stripe checkout, billing portal, webhook handling
    scheduler.py     → APScheduler: polls bets every 30s, fires notifications

frontend/
  index.html         → Full SPA — all CSS and JS inline
```

## How to Run

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your keys

# 3. Run backend
uvicorn app.main:app --reload --port 8001

# 4. Run frontend (separate terminal)
python3 -m http.server 3000 --directory ../frontend

# Or use the combined run script from project root:
bash run.sh
```

The backend auto-creates the SQLite database (`polyedge.db`) on first startup.

## API Endpoints

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/register | No | Create account, returns JWT |
| POST | /auth/login | No | Login, returns JWT |
| GET | /auth/me | JWT | Current user info |

### Bettors
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /bettors | Optional | Leaderboard. `?sort=profit|accuracy|volume&limit=100` |
| GET | /bettors/{address} | Optional | Bettor profile + recent 20 bets |

### Follows
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /follows | JWT | List user's follows |
| POST | /follows | JWT | Add follow (tier limits enforced) |
| DELETE | /follows/{address} | JWT | Unfollow |

### Alerts
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /alerts/settings | JWT | Get notification settings |
| PUT | /alerts/settings | JWT | Update web_push_enabled, telegram_enabled, push_subscription |
| POST | /alerts/telegram/start | JWT | Generate verification code |
| POST | /alerts/telegram/verify | JWT | Verify code to link Telegram |

### Payments
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /payments/checkout | JWT | Create Stripe checkout session |
| POST | /payments/webhook | No (Stripe sig) | Handle Stripe events |
| GET | /payments/portal | JWT | Billing portal URL |

### Admin
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /admin/stats | Header: `x-admin-password` | Platform stats + MRR estimate |

## 3-Tier Subscription Model

| Tier | Price | Follow Limit | Notifications |
|------|-------|-------------|---------------|
| Free | $0 | 0 follows | None |
| Basic | $4.99/mo | 5 bettors | Web push + Telegram |
| VIP | $14.99/mo | Unlimited | Web push + Telegram + SMS + Priority speed |

Tier enforcement is in `routes/follows.py`. The `TIER_LIMITS` dict controls the cap. Stripe webhook upgrades/downgrades the `subscription_tier` column on the `User` model.

## Key Conventions

- Backend: snake_case (Python)
- Frontend: camelCase (JavaScript)
- API responses: consistent `{"key": value}` JSON, no bare arrays
- All external API calls (Polymarket, Stripe, Telegram) are in the `services/` layer
- Routes import services. Services do not import routes. One-way dependency.
- Database: SQLite for simplicity. Replace `database_url` in `.env` for PostgreSQL in production.
- JWT stored in `localStorage` as `pe_token`
- Protected routes return 401 with `{"detail": "..."}` — frontend redirects to login

## Scheduler

`services/scheduler.py` runs an APScheduler `AsyncIOScheduler` job every 30 seconds:
1. Query unique bettor addresses from `BettorFollow` table
2. Fetch recent bets from Polymarket per address
3. Compare timestamps against `_last_check`
4. Save new `BetEvent` rows, fire `dispatch_bet_notification()` for each follower
5. Update `_last_check`

## Environment Variables

See `backend/.env.example` for all keys. Required for full functionality:
- `JWT_SECRET_KEY` — any random string, keep secret
- `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + price IDs — for payments
- `TELEGRAM_BOT_TOKEN` — create a bot via @BotFather

## Polymarket API

Base: `https://data-api.polymarket.com`

- `GET /profiles?limit=100&sortBy=profit` — leaderboard
- `GET /profiles/{address}` — single bettor
- `GET /activity?user={address}&limit=20` — recent bets

All responses are normalised in `services/polymarket.py` before being returned to routes.

## What NOT to Do

- Do not add `print()` debugging in production — use `logging`
- Do not store raw passwords — always use `auth.hash_password()`
- Do not call Polymarket API inside route handlers — use the service layer
- Do not hardcode price IDs — they live in `.env` via `config.py`
- Do not bypass Stripe webhook signature verification in production
