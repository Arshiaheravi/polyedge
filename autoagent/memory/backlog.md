# Backlog

---

## HIGH PRIORITY — Tier 1 Money-Making Features

### Tier Access Rules
- **Free** (1 follow): See Whale Consensus (top 3 markets, read-only, no whale names), Copy Simulator on profile (teaser: shows result but blurred/locked with "Upgrade to Basic")
- **Basic** ($4.99, 5 follows): Conviction Score in notifications, Smart Entry Timing on position cards, Copy Simulator fully unlocked
- **VIP** ($9.99, unlimited): Everything in Basic + Exit Alerts + full Whale Consensus (all markets, whale names visible) + priority notification speed

---


- [ ] Copy Portfolio Simulator — on GET /bettors/{address} add simulated_copy_pnl field: take recent_bets (TRADE type only), for each bet compute simulated_return = amount_usd * (1/price - 1) if outcome matches bettor's side and market resolved correctly (use price as proxy — if price > 0.9 at time of our check it likely resolved YES); sum returns for $100-per-bet simulation; return {simulated_pnl_usd, simulated_roi_pct, bets_analysed}. TIER GATE: return full data for Basic/VIP users. For Free users return {simulated_pnl_usd: null, simulated_roi_pct: null, bets_analysed: 0, locked: true}. Frontend renders on profile page: Basic/VIP → "Copy simulator: $100/bet on last 10 → +$347 (+34.7%)"; Free → blurred card "?? profit" with "Upgrade to Basic to unlock" CTA.

- [ ] Exit Alerts — in scheduler.py maintain _last_positions dict per bettor address; each poll compare current positions to previous; if a conditionId that existed last poll is now gone or size reduced by >50%, it is an exit; call dispatch_bet_notification() with type="EXIT" and message "⚡ [BettorName] EXITING [Market] — consider taking profit". TIER GATE: only send EXIT notifications to VIP users (tier == "vip"). Store exit events as BetEvent with type="EXIT" for all tiers (for future analytics).

- [ ] Copy Ratio Setting — let users set a per-bettor copy ratio multiplier (0.1x, 0.25x, 0.5x, 1x) stored in BettorFollow table; show on follow cards as "Copy at 0.5x"; include copy_ratio in notification messages: "🔥 EXTREME conviction — Copy at 0.5x = $X". TIER GATE: Basic/VIP only (Free always shows full bet size, no ratio setting). Rationale: PolyGun (leading competitor) offers 0.1x-1x ratio as core differentiator — without it, PolyEdge users have to manually scale down each copy trade.

- [ ] Insider Score — for each bettor in the top-100, compute a 0-100 confidence score estimating information-edge: factors are (win_rate × profit_usd × avg_conviction × bet_count / 50). Display as a colored badge on leaderboard cards (green >70, yellow 40-70, gray <40). Merge with Edge Score composite metric already in backlog. TIER GATE: visible badge for all tiers; numeric score shown only for Basic/VIP. Rationale: Polywhaler is only competitor offering an insider score — PolyEdge can build this with data we already have.

---

## MEDIUM PRIORITY — Tier 2 Money-Making Features

- [ ] Bettor Category Specialization — analyse recent_bets market_question text for each top bettor; classify into categories using keyword matching (Politics: election/president/congress, Sports: win/match/championship/game, Crypto: bitcoin/eth/price, Finance: fed/rate/inflation); compute category_win_rate from bets where we can infer outcome (price > 0.85 at detection = likely correct prediction); add top_category and category_win_rate to bettor profile and leaderboard card display

- [ ] Market Momentum Score — scheduler tracks how many unique top-100 bettors entered each market in rolling 7-day window; add momentum_score = unique_whales_7d * avg_conviction to market data; expose on GET /markets/consensus and bettor position cards; show "🚀 5 whales entered this week" badge on high-momentum markets

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
