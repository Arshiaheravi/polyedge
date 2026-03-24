# Skill: Design / Frontend (PolyEdge)

## CRITICAL: PolyEdge File Structure
- **One file only**: `frontend/index.html` — ALL CSS is in `<style>` tags, ALL JS is in `<script>` tags
- NO separate styles.css, NO app.js, NO build step — edit `frontend/index.html` only
- CSS variables are defined at `:root` level near the top of the `<style>` block

## RULES
- Dark theme always — deep navy/charcoal, never pure black (#000)
- Mobile-first: test at 375px mentally before committing
- No emojis in UI text
- XSS: any API-sourced data (bettor names, market names, messages) in `innerHTML` MUST use `escapeHtml()` — run `grep -n 'innerHTML.*\${' frontend/index.html` before every commit

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

## AVOID (AI slop patterns in copy-trading UIs)
- Generic purple gradients without purpose
- 3-column grids with no visual hierarchy
- "No data available" empty states — write context copy
- Overanimating on page load
- Tables for data that should be cards
- Hardcoded colors instead of CSS variables

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

### Pricing page: Most Popular tier elevation
- Apply `transform: translateY(-8px)` to the Basic ($4.99) card
- Add `box-shadow: 0 0 0 2px var(--accent)` glowing border
- Add "Most Popular" badge: `position: absolute; top: -12px`
- Research: elevating middle tier increases that tier's conversion 20-30%
- Add inline under CTA buttons: "Cancel anytime · No credit card for Free tier"

## AFTER FRONTEND CHANGES
1. Check layout at 375px (mobile), 768px (tablet), 1280px (desktop) mentally
2. Run `grep -n 'innerHTML.*\${' frontend/index.html` — verify all API-sourced data uses `escapeHtml()`
3. Run test suite: `cd backend && py -m pytest tests/ -q`
4. Run Playwright check: `py autoagent/tmp_check.py` (follow playwright.md)
