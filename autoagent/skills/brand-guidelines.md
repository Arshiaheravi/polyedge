# Skill: Brand Guidelines

**When to use**: Creating branded documents, presentations, or artifacts that should follow
a consistent visual identity. Use for StockCards brand materials or Anthropic-branded outputs.

## StockCards brand (primary — use for all app/marketing work)

| Element | Value |
|---------|-------|
| Background | `#0a0a0a` |
| Card surface | `#141414` |
| PLAY green | `#00c896` |
| WATCH yellow | `#f0b429` |
| DECK blue | `#4da6ff` |
| PASS gray | `#666666` |
| Text primary | `#ffffff` |
| Text secondary | `#999999` |
| Font (numbers) | Monospace |
| Font (headings) | System sans-serif or defined in CSS variables |

**Never add a new raw hex value** — always add to `:root` CSS variables first.

## Anthropic brand (use only for Anthropic-branded artifacts)

| Element | Value |
|---------|-------|
| Primary text | `#141413` |
| Background | `#faf9f5` |
| Accent orange | `#d97757` |
| Accent blue | `#6a9bcc` |
| Accent green | `#788c5d` |
| Heading font | Poppins (24pt+), fallback Arial |
| Body font | Lora, fallback Georgia |

## Rules

- Apply the brand system that matches the context (StockCards app vs external document)
- Never mix the two brand systems in one artifact
- Maintain contrast ratio ≥ 4.5:1 for body text
- Use CSS variables for colors — never hardcode hex values in component code
