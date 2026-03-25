# Current Task: Hero Section Polish
Steps: 4 total | 4 remaining
- [ ] Step 1: Bigger headline — bump `.hero h1` font size clamp from (40px, 6.5vw, 80px) → (50px, 7.5vw, 96px)
- [ ] Step 2: Animated value-prop subtext — replace static `<p>` in hero with `.hero-cycle` container cycling 3 value props via CSS `@keyframes heroTextCycle`
- [ ] Step 3: Pulsing CTA button — add `@keyframes ctaGlowPulse` (box-shadow glow in/out) to `.btn-hero`
- [ ] Step 4: Live stat counter — add `.hero-live-stats` compact bar below social proof line; add 2 animateCounter() calls (hlstat-traders: 100, hlstat-profit: 2.4) to runLandingCounters()

Done condition: all 4 visual elements visible in browser, 2 new Playwright checks pass, tests green.
