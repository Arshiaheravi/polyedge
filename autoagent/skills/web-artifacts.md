# Skill: Web Artifacts Builder

**When to use**: Building self-contained interactive HTML artifacts — dashboards, data visualizers,
calculators, tools that run entirely in the browser with no backend.

## Stack

React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui, bundled into a single HTML file.

## Workflow

```bash
# 1. Initialize project
bash scripts/init-artifact.sh my-artifact

# 2. Develop
cd my-artifact && npm run dev

# 3. Bundle into single self-contained HTML
bash scripts/bundle-artifact.sh my-artifact
# → outputs bundle.html (all JS/CSS embedded, no external deps)
```

## Design rules (from Anthropic)

- Avoid centered layouts, purple gradients, uniform rounded corners, Inter font — these scream AI-generated
- Use shadcn/ui components (40+ pre-installed)
- Dark theme preferred for trading/data tools
- Every component must work without a network connection

## StockCards use cases

- Signal pattern visualizer (interactive chart in a single HTML file)
- Backtesting calculator (run what-if scenarios in browser)
- Pattern recognition tutorial (animated flag/pennant explanation)
- Exportable dashboard (send a standalone HTML to investors)

## Key principle

The output is ONE `.html` file. No CDN links, no external fonts, no API calls — everything embedded.
Share it as a file attachment; it runs in any browser.
