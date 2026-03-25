# Skill: Design / Frontend (PolyEdge)

## CRITICAL: PolyEdge File Structure
- **One file only**: `frontend/index.html` — ALL CSS is in `<style>` tags, ALL JS is in `<script>` tags
- NO separate styles.css, NO app.js, NO build step — edit `frontend/index.html` only
- CSS variables are defined at `:root` level near the top of the `<style>` block

## RULES
- Dark theme always — deep navy/charcoal, never pure black (#000)
- Mobile-first: test at 375px mentally before committing
- No emojis in UI text

### XSS PREVENTION — apply at the point of WRITING, not just at audit
Every time you write a template literal `` `...${var}...` `` that will end up in innerHTML (directly or via a variable):
1. Ask: does `var` come from API data or user input? (bettor name, market question, avatar URL, message, address display, any server string)
2. If yes → wrap it: `escapeHtml(var)`. No exceptions.
3. Attribute injections are equally dangerous: `src="${escapeHtml(url)}"` not `src="${url}"` — even inside a template literal assigned to innerHTML.
4. Only safe unescaped: hex wallet addresses (0x... never contains HTML), integer/float numbers.
5. **The audit grep will catch obvious cases but MISSES two-line patterns** where a template literal builds a string into a variable and that variable is later assigned to innerHTML. Do not rely on the grep — apply escapeHtml() at write time.

Run before every commit: `grep -n 'innerHTML.*\${' frontend/index.html` AND `grep -n 'innerHTML\s*=\s*[a-zA-Z_]' frontend/index.html` (second grep catches variable-assigned innerHTML — trace each variable to its definition and verify API-sourced `${}` uses escapeHtml).

## COLOR SYSTEM (PolyEdge — actual `:root` values)
CSS variables defined at `:root` in `frontend/index.html` (line ~13):
- `--bg`: `#09090b` (near-black base)
- `--bg2`: `#111113`, `--card`: `#18181b`, `--card2`: `#1f1f23`, `--card3`: `#27272a`
- `--border`: `#2d2d32`, `--border2`: `#3f3f46`
- `--accent` / `--green`: `#00c97a` (main green — profit, CTAs, positive P&L)
- `--accent2` / `--green2`: `#34d399`, `--accent3`: `#059669`
- `--red`: `#f03e3e`, `--gold`: `#f59e0b`, `--gold2`: `#fbbf24`
- `--text`: `#fafafa`, `--text2`: `#a1a1aa`, `--text3`: `#8c8c99`
- `--glow`: `0 0 40px rgba(0,201,122,0.18)` — green card hover glow
- Fonts: `--font-display: 'Space Grotesk'`, `--font-body: 'DM Sans'`
- Spacing grid: `--sp-1: 4px` through `--sp-20: 80px` (8px base)
- Radius: `--radius: 14px`, `--radius-sm: 9px`, `--radius-xs: 6px`
- **NEVER add a new raw hex color — always add as a CSS variable in `:root` first**
- **Icons: use inline SVG only — never external icon fonts (causes flash/load issues)**

## CARD ANATOMY (PolyEdge leaderboard cards)
Current card class: `.lb-card`
Key elements: `.lb-rank-badge`, `.lb-card-name`, `.lb-stat`, follow button
When modifying any card: check `renderBettorCard()` in the `<script>` block — highest-leverage function for leaderboard UX.

## ANIMATION RULES (PolyEdge)
High-impact only:
- Counter animations: `countUp()` on hero stats (count from 0 to final value on scroll/load)
- CTA shimmer: CSS `::after` pseudo-element sweep on primary button
- Hover lift: `transform: translateY(-2px)` + `box-shadow` glow on cards
- Green flash on new bet detection
- Number ticker: incrementing live stat every 8s

Avoid:
- Animating elements that appear on every page load (except initial counter animation)
- Heavy JS animation libs — CSS transitions only
- Spinners on every element — use skeleton cards instead

## CONVERSION/UX PRINCIPLES (fintech copy-trading)
- Every screen has ONE clear primary action
- Social proof above the fold: "Join 847+ traders", live stat count
- Free-tier paywalls: show value first, then the lock — never just error
- Empty states: illustration + context-specific copy + action button
- Loading: skeleton cards, never blank white flash

## POLYEDGE SCREENS
| Screen | Key element | Primary action |
|--------|-------------|----------------|
| Hero | Stats strip + live ticker | Sign Up CTA |
| Leaderboard | `.lb-grid` card grid | Follow button |
| Bettor Profile | Stats + recent bets | Follow/Unfollow CTA |
| Follows | Active positions | View profile |
| Alerts/Settings | Toggle switches | Save |
| Pricing | 3 cards (Free/Basic/VIP) | Upgrade CTA |
| Login/Register | Modal form | Submit |

## PRE-DESIGN CHECKLIST (from Anthropic frontend-design skill)
Before writing any CSS/JS for a new section, answer:
1. **Purpose**: What decision does this UI help the user make? (e.g., "follow a bettor", "upgrade to VIP")
2. **Differentiation**: What's the ONE thing a visitor will remember about this section?
3. **Tone**: PolyEdge is dark/precision/urgency — like a Bloomberg terminal for prediction markets. Every element should feel authoritative and fast.

**For backgrounds and visual depth** (not just solid colors):
- Gradient meshes: `background: radial-gradient(ellipse at 20% 50%, rgba(0,201,122,0.08) 0%, transparent 50%)`
- Noise texture overlays for depth (SVG filter or CSS)
- Grain overlay on hero sections
- Layered transparencies with `backdrop-filter: blur()` on cards

**Motion rules** (Anthropic frontend-design skill):
- One well-orchestrated page load (staggered `animation-delay`) > scattered micro-interactions
- CSS-only animations preferred (no JS animation libs)
- Hover states that surprise: scale + glow is expected; try color shift + border reveal instead

## VISUAL AUDIT CHECKLIST (run before committing any UI change)
Score each dimension pass/fail — from ECC design-system/SKILL.md (2026-03-23):

1. **Color consistency** — are all colors CSS variables from `:root`? No raw hex values?
2. **Typography hierarchy** — clear visual step from heading → subhead → body → caption?
3. **Spacing rhythm** — consistent 8px-grid spacing? No arbitrary px values?
4. **Component consistency** — do similar elements (cards, badges, buttons) look the same?
5. **Responsive behavior** — fluid at 375px/768px/1280px? No overflow or clipped content?
6. **Animation** — purposeful only? No scroll-triggered animations on every element?
7. **Accessibility** — interactive elements have focus outlines? Touch targets ≥ 44×44px?
8. **Information density** — clean scan path? No more than 3-4 data points per card?
9. **Empty states** — every list/section has a designed empty state (not blank)?
10. **Loading states** — skeleton cards, not blank white flashes?

Any dimension that fails = fix before committing. Log issues that require a full session to `autoagent/memory/tech_debt.md`.

## LAYOUT TRAPS (prevent wasted turns)

### Connector arrows between flex-column items
When building a "steps with connector arrows" layout (e.g. How It Works section):
- **WRONG**: put step cards inside a CSS grid, connector arrows as siblings outside the grid — grid handles placement internally, you can't inject elements between grid cells
- **RIGHT**: put ALL step cards AND connector divs as direct children of a single `display:flex; flex-direction:row` container — connectors are siblings of the cards, not nested inside a grid wrapper
- Pattern: `.steps-flow { display:flex; align-items:flex-start }` → `[card] [connector] [card] [connector] [card]` all as flex children
- Connectors need `padding-top: 56px` (approx) to vertically center against the card icon, not the card top edge
- On mobile: change flex-direction to `column` and hide connectors (`display:none`)

(Source: PolyEdge session 84 — first attempt used grid wrapper, connectors couldn't interleave. Fix: remove grid, use flat flex)

## AVOID (AI slop patterns in copy-trading UIs)
- Generic purple gradients without purpose
- 3-column grids with no visual hierarchy
- "No data available" empty states — write context copy
- Overanimating on page load — especially scroll-triggered animations on every card
- Tables for data that should be cards
- Hardcoded colors instead of CSS variables
- Glass morphism cards with no structural purpose (backdrop-filter on content that doesn't need layering)
- Rounded corners on things that shouldn't be rounded (data tables, stat numbers, badges)
- Generic hero with centered headline text over a stock gradient — add depth (dot grid, ambient glow)
- Excessive box-shadows on dark backgrounds — kills legibility; prefer border elevation instead

(Source: ECC skills/design-system/SKILL.md Mode 3 AI Slop Detector, 2026-03-23)

## FINTECH UX PATTERNS (copy-trading specific — 2026 research)

### Semantic color tokens (STRICT rule)
- `--green` / `--accent`: ONLY for positive P&L, profit numbers, YES outcomes, and primary CTAs
- `--red`: ONLY for negative P&L, losses, NO outcomes, and destructive actions
- **NEVER use these colors for decorative elements, badges, or status indicators** — breaks trader scan pattern
- Pair with subtle background tint: `color: var(--green); background: rgba(0,201,122,0.08)`

### Card progressive disclosure
- Default card state: name, profit %, follow button only
- Expand on click: full stats (win rate, volume, recent markets) via CSS `max-height` transition
- Pattern: `max-height: 0` → `max-height: 200px` with `overflow: hidden`
- Reduces cognitive load on leaderboard scan (etoro/Bybit Copy pattern)

### Staggered entrance animations
- Apply `animation-delay` in 150–200ms increments to leaderboard cards
- `.lb-card:nth-child(n) { animation-delay: calc((n - 1) * 150ms); }`
- Creates "live feed" feel — signals real-time activity
- Use CSS `@keyframes fadeInUp` (translate + opacity)

### Pricing page: Most Popular tier elevation + 2026 CRO patterns
- Apply `transform: translateY(-8px)` to the Basic ($4.99) card (permanent elevation, not just hover)
- Add `box-shadow: 0 0 0 2px var(--accent)` + animated glow border: `@keyframes pricing-glow-pulse`
- Add "Most Popular" badge: `position: absolute; top: -12px; background: var(--accent); color: #000`
- Research: elevating middle tier increases that tier's conversion 20-30% (PolyEdge design.md data)
- **Lead with outcomes, not features**: "Get alerted within 30s when top traders bet" beats "Telegram notifications enabled". Pages leading with outcomes convert 34% better. (InfluenceFlow 2026)
- **Explicit feature comparisons**: Use checkmarks ✓ and ✗ per tier (NOT vague bullets). "Explicit comparisons reduce support inquiries by 31%." ✓ Web Push, ✓ Telegram, ✗ SMS for Basic.
- **Mobile pricing stack**: Stack cards vertically on mobile (not horizontal scroll). Mobile-optimized pricing converts 2.3x better. Already handled by flexbox wrapping.
- **Social proof on the pricing page**: Add "Join 847+ traders" or live count near the CTA buttons — not just on the hero. "Visible social proof increases conversion 15-25%." (InfluenceFlow 2026)
- Add inline under CTA buttons: "Cancel anytime · No credit card for Free tier"
- **Annual billing toggle** (backlog task): Monthly/Annual pill toggle above cards; default Monthly. When Annual selected, show BOTH "Save 17%" badge AND "Save $10/yr" on Basic/VIP cards. Pure CSS toggle — no backend needed in UI/UX mode. Implementation: `<div class="billing-toggle"><span data-period="monthly" class="active">Monthly</span><span data-period="annual">Annual</span></div>` — JS updates card prices on click.
(Source: InfluenceFlow SaaS Pricing Page Best Practices 2026, Aimers CRO Trends 2026, PipelineRoad SaaS Pricing 2026)

## TOAST NOTIFICATION STACK (vanilla JS — Emil Kowalski / Sonner pattern)
For the "toast notification stack" backlog task. No libraries — pure CSS + JS.

**Collapsed state (newest toast on top):**
```css
.toast:nth-child(n) {
  transform: translateY(calc(-14px * var(--index))) scale(calc(1 - 0.05 * var(--index)));
}
```

**Expanded state (on hover, shows full heights):**
```javascript
// accumulate real heights to offset each toast
const heights = Array.from(toasts).map(t => t.getBoundingClientRect().height);
toasts.forEach((t, i) => {
  const offset = heights.slice(0, i).reduce((a, h) => a + h, 0) + i * 8;
  t.style.setProperty('--offset', offset + 'px');
  t.style.transform = `translateY(calc(-1 * var(--offset)))`;
});
```

**Entry animation (interruptible — use data attribute, NOT @keyframes):**
```css
.toast[data-mounted="false"] { transform: translateY(100%) scale(0.95); opacity: 0; }
.toast[data-mounted="true"]  { transform: translateY(0); opacity: 1; transition: transform 400ms ease, opacity 200ms; }
```
Set `data-mounted="false"` on insert, flip to `"true"` in next animation frame. This allows interrupting mid-animation.

**Auto-dismiss:** `setTimeout(() => removeToast(id), 5000)`. Pause timer on hover.

**Toast types:** success (green left border), info (blue), error (red). Use `--toast-color` CSS variable.

(Source: emilkowal.ski/ui/building-a-toast-component — the Sonner pattern, 2026)

## PROBABILITY CHIP / YES–NO PILL (inline on bet rows)
For the "bet activity feed enhancements" backlog task.

**CSS for YES/NO outcome badge on a bet row:**
```css
.bet-outcome {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 8px; border-radius: 9999px;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em;
  cursor: default;
}
.bet-outcome.yes {
  background: rgba(0,201,122,0.12); color: #4ade80;
  border: 1px solid rgba(0,201,122,0.4);
}
.bet-outcome.no {
  background: rgba(240,62,62,0.12); color: #f87171;
  border: 1px solid rgba(240,62,62,0.4);
}
.bet-price { opacity: 0.75; font-size: 0.7rem; }
```

**HTML pattern:** `<span class="bet-outcome yes">YES <span class="bet-price">72¢</span></span>`

**Rule:** Direction (YES/NO) and price stay in one atomic pill — don't split into two separate elements.

(Source: 2026 fintech dark-mode research; badges-vs-chips pattern analysis)

## FOLLOWS TAB DASHBOARD FEEL (summary strip + richer cards)
For the "Follows tab dashboard feel" backlog task.

**Summary strip (pinned above follow cards):**
```html
<div class="follows-summary-strip">
  <div class="follows-stat">
    <span class="follows-stat-value" id="follows-count">0</span>
    <span class="follows-stat-label">Following</span>
  </div>
  <div class="follows-stat">
    <span class="follows-stat-value" id="active-bets-count">0</span>
    <span class="follows-stat-label">Active bets 24h</span>
  </div>
  <div class="follows-stat pnl-positive" id="follows-pnl">
    <span class="follows-stat-value">+$0</span>
    <span class="follows-stat-label">Cumulative P&L</span>
  </div>
</div>
```
```css
.follows-summary-strip {
  display: flex; gap: 16px; padding: 12px 16px;
  background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
  margin-bottom: 16px;
}
.follows-stat { display: flex; flex-direction: column; gap: 2px; }
.follows-stat-value { font-size: 1.25rem; font-weight: 700; color: var(--text); }
.follows-stat-label { font-size: 0.7rem; color: var(--text3); text-transform: uppercase; letter-spacing: 0.06em; }
.follows-stat.pnl-positive .follows-stat-value { color: var(--green); }
.follows-stat.pnl-negative .follows-stat-value { color: var(--red); }
```

**Rules:**
- Cumulative P&L must be computed from the bettor cards' profit data (sum of followed bettor profits). Do NOT show fake static numbers.
- If no follows: hide the strip entirely (show empty state instead)
- "Active bets 24h" = count of bettors who had activity in last 24h; derive from `followed_at` or last seen bet timestamp if available

## EXTERNAL ASSET APIS (NovaBanana, Unsplash, etc.)
Before calling any third-party media/image API:
1. Check `backend/.env` — verify the key is present and non-placeholder (not `REPLACE_ME` / `xxx`)
2. If key is missing or placeholder: add a row to `autoagent/ASSETS_NEEDED.md` immediately, then skip the API call and implement the fallback (CSS gradient / inline SVG)
3. Do NOT spend turns attempting the API call if the key is unconfigured — it will always fail

(Source: Session 64 — NovaBanana returned 401 because key was not configured; turned into a wasted turn + ASSETS_NEEDED.md doc)

## AFTER FRONTEND CHANGES
1. Check layout at 375px (mobile), 768px (tablet), 1280px (desktop) mentally
2. Run `grep -n 'innerHTML.*\${' frontend/index.html` — verify all API-sourced data uses `escapeHtml()`
3. Run test suite: `cd backend && py -m pytest tests/ -q`
4. Run Playwright check: `py autoagent/tmp_check.py` (follow playwright.md)
