"""
Polymarket API client.

Confirmed working endpoints (no auth required):
  GET https://data-api.polymarket.com/v1/leaderboard
      ?timePeriod=day|week|month|all
      &orderBy=PNL|VOL
      &limit=50
      &offset=0
      &category=overall
    → Returns: rank, proxyWallet, userName, vol, pnl, profileImage

  GET https://data-api.polymarket.com/trades?limit=N
    → Recent global trades (for live ticker)

  GET https://data-api.polymarket.com/activity?user=ADDR&limit=N
    → Trades for a specific wallet (for bettor profiles)
"""
from typing import Optional

import httpx

BASE_URL = "https://data-api.polymarket.com"

TIMEOUT = 15.0


def _blockies_url(address: str) -> str:
    seed = address.lower() if address else "unknown"
    return f"https://api.dicebear.com/7.x/identicon/svg?seed={seed}"


def _normalise_leaderboard_entry(raw: dict) -> dict:
    address = raw.get("proxyWallet") or ""
    name = raw.get("userName") or (address[:10] + "..." if address else "Unknown")
    avatar_url = raw.get("profileImage") or _blockies_url(address)
    vol = float(raw.get("vol") or 0)
    pnl = float(raw.get("pnl") or 0)
    # rank comes as string from API
    rank = int(raw.get("rank") or 0)
    # percentProfitable is a 0-100 value from the API; normalise to 0.0-1.0
    pct_profitable = raw.get("percentProfitable")
    accuracy = round(float(pct_profitable) / 100.0, 4) if pct_profitable is not None else None
    return {
        "rank": rank,
        "address": address,
        "name": name,
        "volume_usd": round(vol, 2),
        "pnl_usd": round(pnl, 2),
        "avatar_url": avatar_url,
        "accuracy": accuracy,
    }


def _normalise_profile(raw: dict, volume: float = 0.0, trade_count: int = 0, pnl_usd: float = 0.0, rank: int = 0) -> dict:
    address = raw.get("proxyWallet") or raw.get("address") or ""
    name = raw.get("userName") or raw.get("name") or raw.get("pseudonym") or (address[:10] + "..." if address else "Unknown")
    avatar_url = raw.get("profileImageOptimized") or raw.get("profileImage") or _blockies_url(address)
    avg_bet = round(volume / trade_count, 2) if trade_count > 0 else 0.0

    return {
        "address": address,
        "name": name,
        "rank": rank,
        "pnl_usd": round(float(pnl_usd), 2),
        "volume_usd": round(float(volume), 2),
        "total_bets": int(raw.get("numTrades") or raw.get("total_bets") or trade_count),
        "avg_bet_usd": avg_bet,
        "avatar_url": avatar_url,
    }


def _normalise_bet(raw: dict) -> dict:
    return {
        "market_id": raw.get("conditionId") or raw.get("market_id") or "",
        "market_question": raw.get("title") or raw.get("question") or raw.get("market_question") or "Unknown Market",
        "outcome": raw.get("outcome") or "",          # "Yes" / "No" — only present on TRADE type
        "amount_usd": round(float(raw.get("usdcSize") or raw.get("size") or 0), 2),
        "timestamp": raw.get("timestamp") or raw.get("createdAt") or "",
        "price": round(float(raw.get("price") or 0), 4),  # entry price 0-1, only on TRADE
        "type": raw.get("side") or "BUY",              # BUY / SELL
        "tx_hash": raw.get("transactionHash") or "",
        "market_icon": raw.get("icon") or "",
        "market_slug": raw.get("eventSlug") or raw.get("slug") or "",
    }


async def get_live_trades(limit: int = 20) -> list[dict]:
    """
    Fetch the most recent global Polymarket trades for the live ticker.
    Returns normalised trade objects with bettor name, market, outcome, and size.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/trades", params={"limit": limit})
            resp.raise_for_status()
            trades = resp.json()
            if not isinstance(trades, list):
                trades = []
        except Exception:
            trades = []

    result = []
    for t in trades:
        addr = t.get("proxyWallet") or ""
        name = t.get("name") or t.get("pseudonym") or (addr[:8] + "..." if addr else "anon")
        market = t.get("title") or t.get("question") or "Unknown Market"
        outcome = t.get("outcome") or t.get("side") or ""
        size = round(float(t.get("usdcSize") or t.get("size") or 0), 2)
        side = (t.get("side") or "").upper()
        result.append({
            "name": name,
            "market": market,
            "outcome": outcome,
            "amount_usd": size,
            "side": side,
            "timestamp": t.get("timestamp") or t.get("createdAt") or "",
            "market_slug": t.get("slug") or t.get("eventSlug") or "",
        })
    return result


async def get_leaderboard(
    sort_by: str = "profit",
    time_period: str = "month",
    limit: int = 100,
) -> list[dict]:
    """
    Fetch the real Polymarket leaderboard from data-api.polymarket.com/v1/leaderboard.
    Returns actual profit (pnl) and volume data — same data Polymarket's own site shows.

    sort_by:    "profit" | "volume"
    time_period: "day" | "week" | "month" | "all"
    limit:      max 50 per page; we paginate to reach requested limit
    """
    order_by = "PNL" if sort_by == "profit" else "VOL"
    page_size = 50
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        offset = 0
        while len(results) < limit:
            try:
                resp = await client.get(
                    f"{BASE_URL}/v1/leaderboard",
                    params={
                        "timePeriod": time_period,
                        "orderBy": order_by,
                        "limit": page_size,
                        "offset": offset,
                        "category": "overall",
                    },
                )
                resp.raise_for_status()
                page = resp.json()
                if not isinstance(page, list) or len(page) == 0:
                    break
                results.extend(page)
                if len(page) < page_size:
                    break
                offset += page_size
            except Exception:
                break

    return [_normalise_leaderboard_entry(r) for r in results[:limit]]


async def get_active_positions(address: str, limit: int = 20) -> list[dict]:
    """
    Fetch ONLY open (still-tradeable) positions for a wallet.

    redeemable=False  → market is still live, price is still moving, user CAN copy this bet
    redeemable=True   → market resolved, position is settled — skip these

    Fetches up to 500 positions to find open ones (settled positions pile up and
    can push open ones far down the list).
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/positions",
                params={"user": address, "sizeThreshold": "0.01", "limit": 500},
            )
            resp.raise_for_status()
            raw = resp.json()
            if not isinstance(raw, list):
                raw = []
        except Exception:
            raw = []

    result = []
    for p in raw:
        # Skip settled/resolved positions — not copyable
        if p.get("redeemable"):
            continue

        event_slug = p.get("eventSlug") or ""
        slug = p.get("slug") or ""
        condition_id = p.get("conditionId") or ""

        # Build the direct Polymarket link
        if event_slug:
            poly_url = f"https://polymarket.com/event/{event_slug}"
        elif slug:
            poly_url = f"https://polymarket.com/event/{slug}"
        else:
            poly_url = "https://polymarket.com"

        cur_price = float(p.get("curPrice") or 0)
        avg_price = float(p.get("avgPrice") or 0)

        # Skip positions with out-of-range prices — resolved markets have price
        # exactly 0 (data missing) or ≥1 (YES outcome settled). Showing these
        # as "copyable" positions would confuse users.
        if cur_price < 0.001 or cur_price > 0.999:
            continue

        # Copy timing signal: how far has price moved since whale entry?
        if avg_price > 0:
            copy_value_pct = round((cur_price - avg_price) / avg_price * 100, 1)
            if copy_value_pct <= 10:
                copy_signal = "good"
            elif copy_value_pct <= 30:
                copy_signal = "fair"
            else:
                copy_signal = "late"
        else:
            copy_value_pct = 0.0
            copy_signal = "good"

        result.append({
            "condition_id": condition_id,
            "market_title": p.get("title") or "Unknown Market",
            "outcome": p.get("outcome") or "",
            "size": round(float(p.get("size") or 0), 4),
            "current_value_usd": round(float(p.get("currentValue") or 0), 2),
            "initial_value_usd": round(float(p.get("initialValue") or 0), 2),
            "avg_price": round(avg_price, 4),
            "cur_price": round(cur_price, 4),
            "copy_value_pct": copy_value_pct,
            "copy_signal": copy_signal,
            "cash_pnl": round(float(p.get("cashPnl") or 0), 2),
            "percent_pnl": round(float(p.get("percentPnl") or 0), 2),
            "end_date": p.get("endDate") or "",
            "poly_url": poly_url,
            "icon": p.get("icon") or "",
        })
    return result


async def get_bettor_profile(address: str) -> dict:
    """Get a specific bettor's profile — merges activity data with leaderboard rank/pnl/volume."""
    import asyncio

    async def _fetch_activity():
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                resp = await client.get(f"{BASE_URL}/activity", params={"user": address, "limit": 50})
                resp.raise_for_status()
                data = resp.json()
                return data if isinstance(data, list) else []
            except Exception:
                return []

    async def _fetch_leaderboard_entry():
        """Look up this bettor in the leaderboard to get authoritative rank/pnl/volume."""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            for offset in range(0, 100, 50):
                try:
                    resp = await client.get(
                        f"{BASE_URL}/v1/leaderboard",
                        params={"timePeriod": "month", "orderBy": "PNL", "limit": 50, "offset": offset, "category": "overall"},
                    )
                    resp.raise_for_status()
                    page = resp.json()
                    if not isinstance(page, list):
                        break
                    for entry in page:
                        if (entry.get("proxyWallet") or "").lower() == address.lower():
                            return entry
                    if len(page) < 50:
                        break
                except Exception:
                    break
        return None

    raw_list, lb_entry = await asyncio.gather(_fetch_activity(), _fetch_leaderboard_entry())

    # Build profile_raw from activity for name/avatar
    first = raw_list[0] if raw_list else {}
    # lb_entry has real leaderboard data only if it contains the `vol` field
    has_lb_data = bool(lb_entry and lb_entry.get("vol") is not None)
    profile_raw = {
        "proxyWallet": address,
        "userName": (lb_entry.get("userName") if has_lb_data else None)
                    or first.get("name") or first.get("pseudonym") or "",
        "profileImage": first.get("profileImageOptimized") or first.get("profileImage")
                        or (lb_entry.get("profileImage") if lb_entry else ""),
    }

    # Use leaderboard data for authoritative volume/pnl/rank (only if real lb entry)
    pnl_usd = float(lb_entry.get("pnl") or 0) if has_lb_data else 0.0
    volume = float(lb_entry.get("vol") or 0) if has_lb_data else sum(float(t.get("usdcSize") or t.get("size") or 0) for t in raw_list)
    rank = int(lb_entry.get("rank") or 0) if has_lb_data else 0
    trade_count = len([t for t in raw_list if t.get("type") == "TRADE"]) or len(raw_list)

    return _normalise_profile(profile_raw, volume=volume, trade_count=trade_count, pnl_usd=pnl_usd, rank=rank)


async def compute_copy_simulator(address: str, limit: int = 10) -> dict:
    """
    Simulate what a user would have made copying this bettor's last N BUY bets at $100 each.

    Strategy:
    - Fetch raw activity (limit=50) including REDEEM transactions.
    - A REDEEM for a conditionId means the whale was paid out → they won that market.
    - For each TRADE BUY (up to `limit`):
        - If conditionId was redeemed → won → simulated_return = $100 * (1/price - 1)
        - Else if bet is >7 days old → assume lost → simulated_return = -$100
        - Else (<7 days, still open) → skip (inconclusive)
    - Returns {simulated_pnl_usd, simulated_roi_pct, bets_analysed}
    """
    import time as _time

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/activity", params={"user": address, "limit": 50})
            resp.raise_for_status()
            raw_list = resp.json()
            if not isinstance(raw_list, list):
                raw_list = []
        except Exception:
            raw_list = []

    # Collect conditionIds that were redeemed (whale cashed out → won)
    redeemed_ids: set[str] = set()
    for item in raw_list:
        if item.get("type") == "REDEEM":
            cid = item.get("conditionId") or ""
            if cid:
                redeemed_ids.add(cid)

    now_ts = _time.time()
    seven_days = 7 * 24 * 3600

    total_pnl = 0.0
    total_invested = 0.0
    bets_analysed = 0

    for item in raw_list:
        if bets_analysed >= limit:
            break
        if item.get("type") == "REDEEM":
            continue
        # Only score BUY trades with a valid price
        side = (item.get("side") or "").upper()
        if side not in ("BUY", ""):  # SELL trades are exits, skip
            continue
        price = float(item.get("price") or 0)
        if price <= 0 or price >= 1:
            continue  # price=0 or price=1 means bad data
        condition_id = item.get("conditionId") or ""

        # Determine timestamp age
        raw_ts = item.get("timestamp") or item.get("createdAt") or ""
        bet_age_secs = seven_days + 1  # default: assume old enough to count as resolved
        if raw_ts:
            try:
                ts_val = float(raw_ts) if str(raw_ts).replace(".", "").isdigit() else None
                if ts_val:
                    bet_age_secs = now_ts - ts_val
                else:
                    from datetime import datetime, timezone
                    dt = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
                    bet_age_secs = now_ts - dt.timestamp()
            except Exception:
                pass

        if condition_id in redeemed_ids:
            # Won — simulate $100 profit at entry price
            simulated_return = 100.0 * (1.0 / price - 1.0)
        elif bet_age_secs > seven_days:
            # Old enough to assume resolved against
            simulated_return = -100.0
        else:
            # Still open — skip
            continue

        total_pnl += simulated_return
        total_invested += 100.0
        bets_analysed += 1

    if bets_analysed == 0:
        return {"simulated_pnl_usd": 0.0, "simulated_roi_pct": 0.0, "bets_analysed": 0}

    roi_pct = round(total_pnl / total_invested * 100, 1)
    return {
        "simulated_pnl_usd": round(total_pnl, 2),
        "simulated_roi_pct": roi_pct,
        "bets_analysed": bets_analysed,
    }


async def get_recent_bets(address: str, limit: int = 20) -> list[dict]:
    """Get recent bets/activity for a specific address."""
    params = {"user": address, "limit": limit}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/activity", params=params)
            resp.raise_for_status()
            raw_list = resp.json()
            if not isinstance(raw_list, list):
                raw_list = raw_list.get("data") or raw_list.get("activity") or []
        except Exception:
            raw_list = []

    # Only include TRADE type — REDEEM is cashing out winnings (no outcome/price data)
    bets = [_normalise_bet(b) for b in raw_list if isinstance(b, dict) and b.get("type") != "REDEEM"]

    # Compute conviction score for each bet relative to this bettor's average bet size
    amounts = [b["amount_usd"] for b in bets if b["amount_usd"] > 0]
    avg = sum(amounts) / len(amounts) if amounts else 0.0
    for b in bets:
        if avg > 0 and b["amount_usd"] > 0:
            score = round(b["amount_usd"] / avg, 1)
        else:
            score = 1.0
        b["conviction_score"] = score
        b["conviction_label"] = "EXTREME" if score >= 10.0 else "HIGH" if score >= 3.0 else ""

    return bets


async def get_consensus_signals(min_whales: int = 3) -> list[dict]:
    """
    Find markets where 3+ top-100 bettors hold the same outcome.

    1. Fetch the top-100 leaderboard to get all bettor addresses.
    2. Fetch open positions for each bettor concurrently (semaphore to respect rate limits).
    3. Group positions by (conditionId, outcome).
    4. Return groups with whale_count >= min_whales, sorted descending by whale_count.

    Each result dict contains:
      market_title, condition_id, outcome, whale_count, avg_entry_price,
      current_price, whale_names (list of bettor names — caller decides whether to expose)
    """
    import asyncio

    # Step 1: Get top-100 bettor addresses
    leaderboard = await get_leaderboard(sort_by="profit", time_period="month", limit=100)
    addresses = [(e["address"], e["name"]) for e in leaderboard if e.get("address")]

    # Step 2: Fetch positions concurrently with a semaphore (max 10 parallel)
    semaphore = asyncio.Semaphore(10)

    async def _fetch_positions(address: str, name: str):
        async with semaphore:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                try:
                    resp = await client.get(
                        f"{BASE_URL}/positions",
                        params={"user": address, "sizeThreshold": "0.01", "limit": 500},
                    )
                    resp.raise_for_status()
                    raw = resp.json()
                    if not isinstance(raw, list):
                        raw = []
                except Exception:
                    raw = []
            result = []
            for p in raw:
                if p.get("redeemable"):
                    continue
                cid = p.get("conditionId") or ""
                outcome = p.get("outcome") or ""
                if not cid or not outcome:
                    continue
                result.append({
                    "condition_id": cid,
                    "outcome": outcome,
                    "market_title": p.get("title") or "Unknown Market",
                    "avg_price": round(float(p.get("avgPrice") or 0), 4),
                    "cur_price": round(float(p.get("curPrice") or 0), 4),
                    "whale_name": name,
                    "whale_address": address,
                    "event_slug": p.get("eventSlug") or p.get("slug") or "",
                })
            return result

    all_results = await asyncio.gather(*[_fetch_positions(addr, name) for addr, name in addresses])

    # Step 3: Group by (condition_id, outcome)
    groups: dict[tuple, dict] = {}
    for positions in all_results:
        for pos in positions:
            key = (pos["condition_id"], pos["outcome"].lower())
            if key not in groups:
                groups[key] = {
                    "condition_id": pos["condition_id"],
                    "outcome": pos["outcome"],
                    "market_title": pos["market_title"],
                    "avg_entry_prices": [],
                    "current_price": pos["cur_price"],
                    "whale_names": [],
                    "whale_addresses": [],
                    "event_slug": pos["event_slug"],
                }
            groups[key]["avg_entry_prices"].append(pos["avg_price"])
            groups[key]["whale_names"].append(pos["whale_name"])
            groups[key]["whale_addresses"].append(pos["whale_address"])

    # Step 4: Filter and sort
    signals = []
    for g in groups.values():
        count = len(g["whale_names"])
        if count < min_whales:
            continue
        # Skip resolved markets — price near 0 or 1 means the market already settled
        cur_price = g["current_price"]
        if cur_price < 0.05 or cur_price > 0.95:
            continue
        avg_entry = round(sum(g["avg_entry_prices"]) / count, 4) if g["avg_entry_prices"] else 0.0
        signals.append({
            "market_title": g["market_title"],
            "condition_id": g["condition_id"],
            "outcome": g["outcome"],
            "whale_count": count,
            "avg_entry_price": avg_entry,
            "current_price": g["current_price"],
            "whale_names": g["whale_names"],
            "whale_addresses": g["whale_addresses"],
            "event_slug": g["event_slug"],
        })

    signals.sort(key=lambda x: x["whale_count"], reverse=True)
    return signals
