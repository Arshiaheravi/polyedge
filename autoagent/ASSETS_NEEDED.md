# Assets Needed

This file is maintained by the agent. When a visual asset is needed that cannot be generated programmatically (SVG, CSS, or NovaBanana API), the agent documents it here for the user to source manually.

---

## How to Get These

- **AI Generate**: Use NovaBanana, Midjourney, DALL-E, or Adobe Firefly
- **Find Free**: Unsplash (photos), Undraw.co (illustrations), Heroicons (icons)
- **Buy**: Envato Elements, Creative Market, Shutterstock

Once you have the asset, drop it in `frontend/assets/` and tell the agent — it will wire it in.

---

## Pending Assets

| Asset | Purpose | Suggested Prompt / Spec | Where to Get | Status |
|-------|---------|------------------------|--------------|--------|
| Hero background | Landing page hero section background — dark, abstract, financial/crypto feel | "Dark abstract financial data visualization, trading charts, deep navy blue, glowing green lines, cinematic" | NovaBanana / Midjourney | ❌ Needed |
| PolyEdge Logo | Replace text logo with a proper mark | "PE monogram logo, minimal, electric green on dark, fintech style" | NovaBanana / Designer | ❌ Needed |
| Empty state illustration | Shown when user has no follows yet | "Person looking at empty screen, minimal line art, dark theme" | Undraw.co (free) | ❌ Needed |
| Trader avatar placeholders | Default avatar for bettors with no profile image | "Abstract geometric avatar, 8 variants, dark background, colorful" | NovaBanana | ❌ Needed |
| Notification illustration | Shown on alerts/settings page | "Phone with notification bell, minimal, dark theme" | Undraw.co (free) | ❌ Needed |

---

## Completed Assets

_(Agent moves items here once they are wired in)_

---

## Notes for the User

- **Undraw.co** — completely free SVG illustrations, dark theme compatible, just pick and download
- **NovaBanana API key** is already in `autoagent/credentials.env` — agent will use it automatically
- Drop any images in `frontend/assets/` — agent will detect and use them
