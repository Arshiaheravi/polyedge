# PolyEdge

[![CI](https://github.com/Arshiaheravi/polyedge/actions/workflows/ci.yml/badge.svg)](https://github.com/Arshiaheravi/polyedge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11 | 3.12](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)

Copy the top Polymarket bettors in real-time.

PolyEdge tracks the 100 most profitable bettors on Polymarket and sends you instant notifications — web push, Telegram — the moment they place a new bet, so you can copy it before the market moves.

## What it does

- **Live leaderboard** of the top 100 Polymarket bettors ranked by profit, accuracy, or volume
- **1-click follow** any bettor to start monitoring them
- **30-second polling** — new bets are detected within half a minute
- **Instant alerts** via web push and Telegram
- **Tiered subscriptions** — Free / Basic ($4.99/mo) / VIP ($14.99/mo)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy, SQLite |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Payments | Stripe Checkout + Webhooks |
| Alerts | Telegram Bot API, Web Push API |
| Scheduler | APScheduler (async, 30s interval) |
| Data | Polymarket Data API (`data-api.polymarket.com`) |
| Frontend | Single HTML/CSS/JS file, no build step |

## Setup

### 1. Clone and install

```bash
git clone <repo>
cd PolyEdge/backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
JWT_SECRET_KEY=your-long-random-secret
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_BASIC_PRICE_ID=price_...
STRIPE_VIP_PRICE_ID=price_...
TELEGRAM_BOT_TOKEN=123456:ABC-...
FRONTEND_URL=http://localhost:8003
ADMIN_PASSWORD=change-me
```

### 3. Run

```bash
# From project root
bash run.sh
```

Or manually:

```bash
cd backend
uvicorn app.main:app --reload --port 8003
```

FastAPI serves both the API and the single-page frontend, so one server is all
you need. Open `http://localhost:8003` in your browser.

API docs available at `http://localhost:8003/docs`.

## Tests

The suite is ~550 tests (unit, integration, property-based via Hypothesis).
The default run is fully offline and deterministic:

```bash
cd backend
pip install -r requirements.txt
pytest
```

Tests that hit the live Polymarket API are marked `@pytest.mark.live` and are
skipped by default. Run them explicitly with:

```bash
pytest -m live
```

CI runs the offline suite on Python 3.11 and 3.12 (see
[`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Configuring Stripe

1. Create a Stripe account at https://stripe.com
2. Create two recurring products in the Stripe Dashboard:
   - **Basic** — $4.99/month recurring
   - **VIP** — $14.99/month recurring
3. Copy the Price IDs (`price_...`) into your `.env`
4. For webhooks (local testing), install the Stripe CLI:
   ```bash
   stripe listen --forward-to localhost:8003/payments/webhook
   ```
5. Copy the webhook signing secret (`whsec_...`) into `.env`

Events handled: `checkout.session.completed`, `customer.subscription.deleted`, `customer.subscription.updated`

## Configuring Telegram

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the bot token into `.env` as `TELEGRAM_BOT_TOKEN`
4. Users link their account via the **Alerts** tab in the dashboard:
   - Click "Generate Verification Code"
   - Send the code to your bot: `/verify XXXXXXXX`
   - Click Verify in the dashboard

Note: For the `/verify` command to work, your bot needs a webhook or polling loop that reads messages and calls `POST /alerts/telegram/verify` on behalf of the user. A minimal bot implementation can be added to `services/scheduler.py`.

## Admin

Check platform stats:

```bash
curl -H "x-admin-password: your-admin-password" http://localhost:8003/admin/stats
```

Returns: total users by tier, follows count, bet events, and estimated MRR.

## Subscription Tiers

| Tier | Price | Follow Limit | Alerts |
|------|-------|-------------|--------|
| Free | $0 | 1 bettor | None |
| Basic | $4.99/mo | 5 bettors | Web push + Telegram |
| VIP | $14.99/mo | Unlimited | Web push + Telegram + SMS + Priority |

## Project Structure

```
PolyEdge/
  backend/
    app/
      main.py          # FastAPI app + lifespan
      database.py      # SQLAlchemy + get_db
      models.py        # ORM models
      config.py        # Pydantic settings
      auth.py          # JWT + password utils
      routes/          # Route handlers
      services/        # Business logic
    requirements.txt
    .env.example
      tests/           # ~550 tests (unit, integration, property-based)
  frontend/
    index.html         # Full SPA (CSS + JS inline), served by FastAPI at /
  run.sh
  README.md
```

## License

MIT
