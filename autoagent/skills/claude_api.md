# Skill: Claude API / Anthropic SDK

## WHEN TO USE THIS SKILL
Read this before building any feature that calls the Anthropic API or uses the Agent SDK.
StockCards already has: `src/stockcards/services/chat.py` (chat integration), `src/stockcards/routes/chat.py`.

## MODEL SELECTION (2026-03-20)

| Task complexity | Model | Why |
|---|---|---|
| Simple Q&A, classification | `claude-haiku-4-5-20251001` | Cheapest, fastest |
| Most tasks | `claude-sonnet-4-6` | Best price/quality ratio |
| Complex reasoning, agent work | `claude-opus-4-6` | Highest capability |

**Default to `claude-opus-4-6` for new agent features unless cost is a concern.**
**Note: Claude Haiku 3 (`claude-3-haiku-20240307`) retires April 19, 2026 — migrate any code using it.**

## THINKING / EFFORT

- `claude-opus-4-6` and `claude-sonnet-4-6`: Use `thinking: {type: "adaptive"}` for complex tasks
- Do NOT use `budget_tokens` on Opus 4.6 or Sonnet 4.6 — deprecated
- Use `output_config: {effort: "low"|"medium"|"high"|"max"}` for effort control. Default = `high`
- `max` effort is Opus 4.6 only

## STREAMING

Always stream when:
- Input or output may be long
- `max_tokens` is high
- Response feeds a UI (chat, signal commentary)

```python
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        yield text
    final = stream.get_final_message()
```

## PYTHON SDK PATTERNS

```python
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Standard call
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}],
)

# With thinking
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=8096,
    thinking={"type": "adaptive"},
    messages=[{"role": "user", "content": "..."}],
)
```

## TOOL USE

- Always parse tool inputs with `json.loads()` — never raw string match
- Don't reimplement SDK helpers — use built-in tool loop patterns
- Don't define custom types for SDK data structures — SDK exports them all

## COMMON PITFALLS

- Opus 4.6 does NOT support assistant message prefills → returns 400; use structured outputs instead
- Don't use `output_format` parameter — deprecated; use `output_config: {format: {...}}`
- Don't truncate inputs silently — log a warning and handle gracefully
- Keep `ANTHROPIC_API_KEY` in `.env`, never hardcode

## SURFACE SELECTION

| Use case | Surface |
|---|---|
| Single response (chat, commentary) | Claude API direct |
| Multi-step pipeline you control | Claude API + tool use |
| Agent with file/web/terminal access | Agent SDK |

## SKILL CREATOR PRINCIPLES (from skill-creator SKILL.md)
When writing new agent skill files:
- Make the description **pushy** — passive descriptions cause undertriggering
- Explain the **why** (theory of mind) instead of rigid ALL-CAPS demands
- Keep prompts lean — remove unproductive instructions
- Generalize from feedback rather than overfitting to examples
- Three-level loading: metadata always loaded, SKILL.md on trigger, resources as needed
