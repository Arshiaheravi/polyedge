# Skill: Click-Path Audit (PolyEdge Vanilla JS)

## When to use this skill

Use when:
- Users report a button "does nothing" but the function appears to be wired correctly
- A state indicator (status dot, badge, count) shows the wrong value after user interaction
- After any refactor that touches `showView()`, `showTab()`, or global state variables (`alertSettings`, `_bettorCache`, `_disclosureCache`)
- A Playwright check passes but the UI feels broken in manual testing

**Source**: Adapted from affaan-m/everything-claude-code `click-path-audit` skill (2026-03-22). Original designed for React/Zustand — this version is adapted for PolyEdge's vanilla JS global state.

---

## The Problem This Solves

Static code reading checks:
- Is the function wired to the button? (event handler exists)
- Does it crash? (runtime errors)
- Does it return the right value? (data flow)

It does NOT check:
- **Does function B silently undo what function A just did?**
- **Does shared global state have side effects that cancel the intended action?**
- **Does the final UI state match what the button promises?**

Real PolyEdge example risk: `loadAlertSettings()` overwrites `alertSettings` global — if called after a toggle, it resets user's in-flight toggle state. Both functions work individually; combined, the toggle is silently reverted.

---

## PolyEdge Global State Map

Before auditing any button, build a side-effect map of PolyEdge's global state variables:

| Variable | Owned by | Side effects if overwritten |
|---|---|---|
| `alertSettings` | `loadAlertSettings()` | Resets all toggle states to API values |
| `_bettorCache` | `loadLeaderboard()` | Map of address → bettor data for fast profile loads |
| `_disclosureCache` | `toggleLbCardExpand()` | Cached market titles per address |
| `_seenBetIds` | `refreshFollowsActivity()` | Set of already-shown bet IDs — cleared on follows tab reload |
| `currentFollows` | `loadMyFollows()` | Array of followed bettor addresses |

---

## Audit Steps

### Step 1: Identify the touchpoint

For the button/toggle being audited:
```
TOUCHPOINT: [Button label] in [JS function name, line approx]
Handler: [function name called on click/change]
```

### Step 2: Trace every function call in order

```
For each function call in the handler:
  a. What global state does it READ?
  b. What global state does it WRITE/OVERWRITE?
  c. Does it call fetch() → does the callback overwrite state?
  d. Does it reset any state as a side effect?
```

### Step 3: Check for cancellation bugs

```
CANCELLATION CHECK:
- Does any later call RESET a value set by an earlier call?
- Does any async fetch callback overwrite state set synchronously before the await?
- Does updateChannelStatus() or updateAlertsNoneState() re-read DOM correctly AFTER this handler finishes?
```

### Step 4: Verify final UI state

```
EXPECTED FINAL STATE: [what the user expects to see]
ACTUAL FINAL STATE: [trace what the code produces]
MATCH: yes / no
```

---

## Common PolyEdge Cancellation Patterns to Check

1. **Toggle + reload race**: Toggle sets DOM class → fetch API to save → callback calls `loadAlertSettings()` → overwrites DOM back to saved state. Fix: only update DOM from API response, not pre-emptively.

2. **Follow + cache stale**: `POST /follows` succeeds → `loadMyFollows()` refetches → `_bettorCache` still has old rank data → follow card shows stale rank. Fix: update `_bettorCache` from leaderboard refresh or profile call.

3. **Tab switch + pending fetch**: `showTab('follows')` → `loadMyFollows()` async → user clicks back to leaderboard → follows fetch completes and writes to DOM that's now hidden. Fix: add a tab-guard check `if (currentTab !== 'follows') return` in the callback.

4. **Disclosure cache invalidation**: `toggleLbCardExpand()` reads `_disclosureCache` → returns cached data → bettor profile was updated server-side → stale markets shown. Fix: `_disclosureCache` TTL or invalidate on leaderboard reload.

---

## Output Format

```
CLICK-PATH AUDIT: [button/feature name]
---
TOUCHPOINT: [label] / [handler function]

TRACE:
1. [functionA()] → reads: [...] writes: [...]
2. fetch('/api/...') → callback writes: [...]
3. [functionB()] → reads: [...] writes: [...]

CANCELLATION RISKS:
- [describe any found, or "none"]

FINAL STATE:
- Expected: [what user expects]
- Actual: [what code produces]
- Match: yes / no

FIX (if no match):
- [concrete 1-line fix]
```
