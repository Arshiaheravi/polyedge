# Skill: Nano Banana Image Generation (nanobananaapi.ai)

CONFIRMED WORKING. API key is valid. Use this skill for all image generation tasks.

API Docs: https://docs.nanobananaapi.ai/quickstart
Base URL: https://api.nanobananaapi.ai/api/v1/nanobanana

---

## API Key

```
NANO_BANANA_API_KEY=458ef44f91c6cbcc614a31573b7f15fe
```

Auth header: `Authorization: Bearer 458ef44f91c6cbcc614a31573b7f15fe`

---

## Generate an Image (Python)

```python
import httpx, time, os

API_KEY = "458ef44f91c6cbcc614a31573b7f15fe"
BASE = "https://api.nanobananaapi.ai/api/v1/nanobanana"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def generate_image(prompt: str, save_path: str) -> str:
    """Generate image and save to save_path. Returns save_path on success."""

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # STEP 1 — Submit job
    resp = httpx.post(
        f"{BASE}/generate",
        headers=HEADERS,
        json={
            "prompt": prompt,
            "type": "TEXTTOIAMGE",   # note: their typo, must be exactly this
            "numImages": 1,
            "callBackUrl": "http://localhost:3000"  # required field, dummy ok
        },
        timeout=30
    )
    resp.raise_for_status()
    task_id = resp.json()["data"]["taskId"]

    # STEP 2 — Poll for result (correct endpoint: record-info?taskId=...)
    for _ in range(30):
        time.sleep(3)
        poll = httpx.get(
            f"{BASE}/record-info?taskId={task_id}",
            headers=HEADERS,
            timeout=15
        )
        data = poll.json().get("data", {})
        flag = data.get("successFlag")
        if flag == 1:
            image_url = data.get("response", {}).get("resultImageUrl")
            if image_url:
                # Download and save
                img = httpx.get(image_url, timeout=30)
                with open(save_path, "wb") as f:
                    f.write(img.content)
                return save_path
        elif flag in (2, 3):
            raise RuntimeError(f"Generation failed (flag={flag}): {data}")

    raise RuntimeError("Timed out waiting for image generation")
```

---

## Check Task Status

```python
# Poll endpoint — check until successFlag == 1
GET https://api.nanobananaapi.ai/api/v1/nanobanana/record-info?taskId={taskId}
Authorization: Bearer 458ef44f91c6cbcc614a31573b7f15fe

# successFlag values: 0=generating, 1=success, 2=creation failed, 3=generation failed
# Image URL is in: data.response.resultImageUrl
```

---

## Prompts for PolyEdge Assets

| Asset | Prompt | Save Path |
|-------|--------|-----------|
| Hero background | "Dark cinematic background, financial trading platform, glowing green neon data streams, deep navy blue, abstract, premium fintech aesthetic, no text, no people" | `frontend/assets/hero-bg.jpg` |
| Logo mark | "PE monogram logo, minimal geometric, electric green on dark background, fintech crypto style, clean vector look, square format" | `frontend/assets/logo.png` |
| Empty state — no follows | "Person at desk looking at empty screen, minimal flat illustration, dark blue theme, subtle green accent" | `frontend/assets/empty-follows.png` |
| Notification illustration | "Smartphone with glowing notification bell, minimal flat art, dark theme, green glow accent" | `frontend/assets/notif-illustration.png` |

---

## Rules

- `"type": "TEXTTOIAMGE"` — this is their typo in the API, use it exactly or you get 400
- `callBackUrl` is required — use `"http://localhost:3000"` as dummy value
- Poll every 3 seconds, up to 30 tries (90 seconds max)
- Save all images to `frontend/assets/` — never hotlink remote URLs
- Always add CSS fallback gradient in case image fails to load:
  ```css
  background-image: url('assets/hero-bg.jpg');
  background: linear-gradient(135deg, #0a1628 0%, #0d2137 100%); /* fallback */
  ```

---

## CSS Avatar Alternative (zero API credits)

For bettor avatars — CSS gradient circles are faster and look great:
```javascript
function getAvatarStyle(address) {
    const palettes = [
        ['#00FF88','#00AAFF'], ['#FF6B35','#FF1744'],
        ['#7C4DFF','#00BCD4'], ['#FFD740','#FF6D00']
    ];
    const idx = parseInt(address.slice(2,4), 16) % palettes.length;
    return `background:linear-gradient(135deg,${palettes[idx][0]},${palettes[idx][1]})`;
}
// Usage: <div class="avatar" style="${getAvatarStyle(bettor.address)}">
//          ${bettor.address.slice(2,4).toUpperCase()}
//        </div>
```
