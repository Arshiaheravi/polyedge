# Skill: Nano Banana (nanobnana.com) Image Generation

Nano Banana is Google Gemini-powered AI image generation.
Docs: https://nanobnana.com/docs/api/v2-generate

---

## API Key

Read from credentials.env:
```
NANO_BANANA_API_KEY=458ef44f91c6cbcc614a31573b7f15fe
```

All requests use: `Authorization: Bearer 458ef44f91c6cbcc614a31573b7f15fe`

---

## Generate an Image (Python)

```python
import httpx, time, os

API_KEY = "458ef44f91c6cbcc614a31573b7f15fe"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def generate_image(prompt: str, aspect_ratio: str = "1:1", save_path: str = None) -> str:
    """Generate image with Nano Banana. Returns image URL or saves to save_path."""

    # STEP 1 — Submit generation job (async)
    resp = httpx.post(
        "https://nanobnana.com/api/v2/generate",
        headers=HEADERS,
        json={
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,   # "1:1", "2:3", "3:2", "16:9", "9:16"
            "mode": "sync"                  # use "sync" for simplicity
        },
        timeout=60
    )
    resp.raise_for_status()
    data = resp.json()

    # STEP 2 — If sync, image URL is in response directly
    image_url = data.get("image_url") or data.get("url")

    # STEP 3 — If async (task_id), poll until done
    if not image_url and "task_id" in data:
        task_id = data["task_id"]
        for _ in range(30):  # poll up to 30 times (60 seconds)
            time.sleep(2)
            poll = httpx.get(
                f"https://nanobnana.com/api/v2/task/{task_id}",
                headers=HEADERS,
                timeout=15
            )
            poll_data = poll.json()
            if poll_data.get("status") == "completed":
                image_url = poll_data.get("image_url") or poll_data.get("url")
                break

    if not image_url:
        raise RuntimeError(f"Image generation failed or timed out: {data}")

    # STEP 4 — Optionally download and save
    if save_path:
        img_resp = httpx.get(image_url, timeout=30)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(img_resp.content)
        return save_path

    return image_url


# Example usage:
# generate_image(
#     prompt="Dark cinematic hero background, crypto trading platform, glowing green data lines, deep navy blue",
#     aspect_ratio="16:9",
#     save_path="frontend/assets/hero-bg.jpg"
# )
```

---

## Prompts for PolyEdge Assets

| Asset | Prompt | Aspect Ratio | Save Path |
|-------|--------|-------------|-----------|
| Hero background | "Dark cinematic background, financial trading platform, glowing green neon data streams, deep navy blue, abstract, premium fintech aesthetic, no text" | 16:9 | `frontend/assets/hero-bg.jpg` |
| Logo mark | "PE monogram logo, minimal geometric, electric green on dark, fintech crypto style, clean vector look" | 1:1 | `frontend/assets/logo.png` |
| Empty state — no follows | "Person at desk looking at empty screen, minimal flat illustration, dark blue theme, subtle green accent" | 4:3 | `frontend/assets/empty-follows.png` |
| Trader avatar (x8 variants) | "Abstract geometric avatar for crypto trader, colorful gradient, dark background, minimal, variant N" | 1:1 | `frontend/assets/avatar-N.png` |
| Notification illustration | "Smartphone with glowing notification bell, minimal flat art, dark theme, green glow" | 4:3 | `frontend/assets/notif-illustration.png` |

---

## Rules

- **Each generation costs 24 credits** — don't generate unnecessarily. Generate once, save file, reuse.
- **Always save to `frontend/assets/`** — never use remote URLs directly in production HTML
- **Always provide CSS fallback** — gradient background in case image fails:
  ```css
  background-image: url('assets/hero-bg.jpg');
  background: linear-gradient(135deg, #0a1628 0%, #0d2137 100%); /* fallback */
  ```
- **Use `loading="lazy"` on all `<img>` tags**
- **If the API call fails** — log to ASSETS_NEEDED.md and use CSS fallback. Never crash the UI.

---

## CSS-Only Alternatives (zero credits)

For bettor avatars — CSS gradient circles are often better than generated images:
```javascript
function getAvatarStyle(address) {
    const colors = [
        ['#00FF88', '#00AAFF'], ['#FF6B35', '#FF1744'],
        ['#7C4DFF', '#00BCD4'], ['#FFD740', '#FF6D00']
    ];
    const idx = parseInt(address.slice(2, 4), 16) % colors.length;
    return `background: linear-gradient(135deg, ${colors[idx][0]}, ${colors[idx][1]})`;
}
```

Sources:
- [Nano Bnana API Documentation](https://nanobnana.com/docs)
- [Nano Bnana Pro Generate API (V2)](https://nanobnana.com/docs/api/v2-generate)
