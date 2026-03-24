# AutoAgent — Autonomous AI Development Intelligence

> A self-growing, self-improving AI agent team that works on any project, forever, without human intervention.
> You define the goal. The agents build toward it, learn from every session, improve their own brain, and get smarter every day.

---

## What is AutoAgent?

AutoAgent is not a coding assistant. It is not a chatbot. It does not wait for you to ask it anything.

It is a **team of autonomous AI specialists** that wakes up on a schedule, reads your project, decides what will move your goal forward the most, builds it, tests it, ships it, and then improves itself so it does the same thing better next time.

You fill in two files. Then you run one command. Everything else happens automatically — while you sleep, while you work, while you do anything else.

### The team

| Agent | Role |
|---|---|
| **Orchestrator** | CEO brain. Measures the goal, diagnoses the bottleneck, assigns work to specialists |
| **Engineer** | Builds features, fixes bugs, writes tests, refactors code |
| **Researcher** | Searches the web, finds competitors, discovers new ideas, generates tasks you never thought of |
| **Designer** | Improves UI/UX, takes Playwright screenshots, implements better interfaces |
| **Strategist** | Analyzes whether the current plan will actually hit the goal. Can propose a full pivot. |
| **QA** | Tests everything, runs E2E browser tests, blocks bad commits |
| **Meta-Agent** | Studies the agent team itself. Finds weaknesses. Improves prompts, tools, and workflows. Makes the whole team smarter. |

### What makes it different from ChatGPT, Claude, Cursor

Every other AI tool waits for you. You type. It responds. You close it. It forgets everything.

AutoAgent:
- **Starts itself** — runs on a schedule, no human needed
- **Remembers everything** — knowledge, failures, lessons, experiments — all persisted forever
- **Measures impact** — checks if its work actually moved the goal, not just if code was written
- **Improves itself** — the meta-agent rewrites the team's own prompts and workflows every 3 hours
- **Thinks independently** — generates its own tasks, researches its own ideas, challenges your plan if the data says it won't work
- **Never repeats failures** — every failure is logged, analyzed, and turned into a rule

---

## Requirements

### Option 1 — VS Code Mode (Free, recommended)

Uses Claude Code CLI with your Claude Pro subscription. Zero API cost.

**Step 1 — Install Node.js**
Download from: https://nodejs.org (LTS version)

**Step 2 — Install Claude Code CLI**
```bash
npm install -g @anthropic-ai/claude-code
```

**Step 3 — Activate Claude Code**
```bash
claude
```
Follow the login prompt. Sign in with your Anthropic account (Claude Pro required).
Once logged in, close that terminal. The CLI is now activated.

**Step 4 — Install Python dependencies**
```bash
py autoagent/setup.py
```

That's it. No API key needed. No billing. Uses your existing Claude Pro subscription.

---

### Option 2 — Anthropic API Mode (Pay per use)

Uses the Anthropic API directly. You pay per token. Budget is enforced automatically.

**Step 1 — Get an API key**
Go to: https://console.anthropic.com
Create an account → API Keys → Create Key

**Step 2 — Add the key**
Create a file called `.env` in your project root:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx
```

**Step 3 — Install Python dependencies**
```bash
py autoagent/setup.py
```

**Step 4 — Set your daily budget in `config.json`**
```json
{
  "daily_limit_usd": 10.0
}
```
The agent will stop automatically when the daily limit is reached and resume the next day.

---

## Quick Start

### Step 1 — Fill in PROJECT.md

Copy the template and fill it in:
```bash
cp autoagent/PROJECT.example.md autoagent/PROJECT.md
```

Open `autoagent/PROJECT.md` and answer:
- What is this project? What problem does it solve?
- How do you run it? (exact commands)
- What is the tech stack?
- How does it make money?
- What are the top 3 goals right now?

The more detail you give, the better the agent understands your project. If you skip this, the agent will explore your codebase and write it for you automatically.

### Step 2 — Fill in NORTH_STAR.md

Copy the template and fill it in:
```bash
cp autoagent/NORTH_STAR.example.md autoagent/NORTH_STAR.md
```

Open `autoagent/NORTH_STAR.md` and define:

```markdown
# North Star Metric

Goal: Get to $500/month recurring revenue

Command: curl -s http://localhost:8001/api/revenue | python -c "import sys,json; print(json.load(sys.stdin).get('monthly_usd', 0))"

Target: 500

Reason: At $500/month the product is profitable and proven.
```

**The command must output a single number.** If you can't measure the goal yet, write `echo 0` — the agent will build the measurement system as its first task.

### Step 3 — Run it

```bash
py -X utf8 autoagent/run.py
```

First run asks: **Mode 1 (VS Code — free) or Mode 2 (API — paid)?**
Pick one. It saves your choice. Never asks again.

---

## All Commands

### Main agent

```bash
# DEFAULT — best option, use this
# Starts main agent + meta-agent in parallel, runs forever
py -X utf8 autoagent/run.py

# Test one session before committing to running forever
py -X utf8 autoagent/run.py --once

# Run exactly N sessions then stop
py -X utf8 autoagent/run.py --tasks 3

# Main agent only, no meta-agent
py -X utf8 autoagent/run.py --solo

# Show today's activity and spend
py -X utf8 autoagent/run.py --status
```

### Meta-agent (brain improvement — runs automatically in default mode)

```bash
# Run forever (every 3 hours)
py -X utf8 autoagent/meta/run.py

# One session then exit
py -X utf8 autoagent/meta/run.py --once

# Exactly N sessions then exit
py -X utf8 autoagent/meta/run.py --tasks 3
```

### Reset mode choice

```bash
# Forces the mode selection prompt on next run
del autoagent\backend_mode.json
```

---

## Config Reference

File: `autoagent/config.json`

**This file is fully optional.** Delete it entirely and AutoAgent still works with smart defaults. Only add settings you want to override.

```json
{
  "_comment": "Every field is optional. Agent picks smart defaults for anything not set.",

  "model":           "claude-opus-4-6",
  "daily_limit_usd": 15.0,
  "interval_hours":  2,

  "git": {
    "auto_commit":   true,
    "auto_push":     false,
    "auto_pull":     false,
    "token":         "",
    "repo_url":      "",
    "branch":        "auto",
    "commit_prefix": "agent"
  }
}
```

### All settings

| Setting | Default | Description |
|---|---|---|
| `model` | `claude-sonnet-4-6` | AI model. Options: `claude-haiku-4-5-20251001` / `claude-sonnet-4-6` / `claude-opus-4-6` |
| `daily_limit_usd` | `15.0` | Max API spend per day (API mode only — VS Code mode is always free) |
| `interval_hours` | `2` | Hours between sessions in continuous mode |
| `session_max_turns` | `50` | Max steps per session |
| `frontend_url` | auto-detected | Agent scans your project and probes ports automatically |
| `backend_url` | auto-detected | Agent scans your project and probes ports automatically |
| `git.auto_commit` | `true` | Commit locally after each logical step |
| `git.auto_push` | `false` | Push to remote (requires token + repo_url) |
| `git.auto_pull` | `false` | Pull before each session (requires token + repo_url) |
| `git.token` | `""` | GitHub Personal Access Token |
| `git.repo_url` | `""` | e.g. `https://github.com/yourname/repo.git` |
| `git.branch` | `auto` | Auto-detects current branch, or set `"main"` / `"dev"` |
| `git.commit_prefix` | `"agent"` | Commit messages: `agent: add feature X` |

### Model guide

| Model | Speed | Cost | Best for |
|---|---|---|---|
| `claude-haiku-4-5-20251001` | Fastest | Cheapest | Research, reading, simple tasks |
| `claude-sonnet-4-6` | Fast | Medium | Most tasks (good default) |
| `claude-opus-4-6` | Slower | Most expensive | Complex architecture, deep thinking |

The agent switches models automatically based on task complexity.

### Git presets

**Local only (default — safest):**
No config needed. Agent commits locally, nothing goes to GitHub.

**Full GitHub sync:**
```json
"git": {
  "token":    "ghp_xxxxxxxxxxxxxxxxxxxx",
  "repo_url": "https://github.com/yourname/repo.git"
}
```
Add these two lines and the agent automatically pulls before every session, pushes after every commit.

**How to get a GitHub token:**
GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → New token → select `repo` scope → Generate

**Agent makes changes, you review and commit yourself:**
```json
"git": { "auto_commit": false, "auto_push": false }
```

---

## Files You Manage

These files are **gitignored** — they belong to your project instance, not the reusable framework. Copy from the `.example.md` templates to get started.

| File | Required | Purpose |
|---|---|---|
| `PROJECT.md` | Recommended | What the project is, how to run it, goals. Copy from `PROJECT.example.md`. |
| `NORTH_STAR.md` | Recommended | ONE goal + ONE measurement command. Copy from `NORTH_STAR.example.md`. |
| `KEYS_NEEDED.md` | No | API keys the agent needs. Copy from `KEYS_NEEDED.example.md`. Agent updates this automatically. |
| `config.json` | No | Override any default. Copy from `config.example.json`. Delete entirely and defaults kick in. |
| `memory/backlog.md` | No | Starting tasks. Agent generates its own if empty or missing. |
| `memory/knowledge.md` | No | Pre-seed with project gotchas, known issues, commands that work. |

---

## Files the Agent Manages

Do not edit these manually — the agent owns them. All runtime files live in `memory/` and are gitignored.

| File | Purpose |
|---|---|
| `memory/activity_log.md` | Full history of every session |
| `memory/current_task.md` | Active task — auto-resumed if agent is restarted mid-task |
| `memory/backlog.md` | Agent reads, marks done, adds new tasks it invents |
| `memory/done.md` | Completed tasks log |
| `memory/knowledge.md` | Lessons learned — grows every session automatically |
| `memory/north_star.md` | Live metric measurement history (copy of NORTH_STAR.md for quick reference) |
| `memory/project_root.md` | Absolute path to the project root on this machine |
| `growth_metrics.json` | Sessions, cost, categories, self-improvement log |
| `backend_mode.json` | Saved mode choice (VS Code or API) |
| `sessions.json` | Session counter |
| `experiment_results.tsv` | Hypothesis test results — what worked, what didn't |
| `skills/` | Reusable code patterns the agent saves and reuses |
| `reports/` | Daily session reports (gitignored) |
| `shared/hypotheses.md` | Active / confirmed / rejected theories |
| `shared/debates.md` | Where specialists disagreed and how it was resolved |
| `shared/decisions.md` | Every major pivot and architectural decision |
| `shared/mission_brief.md` | Orchestrator's brief for specialists each session |
| `meta/findings.md` | Everything the meta-agent has discovered about making agents smarter |
| `meta/backlog.md` | Meta-agent's own improvement queue (self-managed) |
| `meta/benchmarks/` | Daily quality scores — tracks whether the brain is improving |
| `meta/experiments/` | A/B test results for every prompt or workflow change |

---

## How a Session Works

### Main agent (every 2 hours by default)

```
START
  → Pull latest (if git configured)
  → Measure North Star metric (run your command, get the number)
  → Diagnose: why isn't the number higher?
  → Assemble specialist team for this session
  → Research: web_search before touching any code
  → Read every file that will be touched
  → Implement the highest-leverage task
  → Run tests — fix failures before committing
  → Run E2E browser test if UI was changed (Playwright)
  → Commit and push (if git configured)
  → Write lesson to knowledge.md
  → Update BACKLOG.md — mark done, add new ideas
  → Improve own SYSTEM_PROMPT if a better approach was found
END
```

### Meta-agent (every 3 hours, parallel window)

```
START
  → Read all session logs — find failures, retries, stuck points
  → Score the last sessions: completion rate, retry rate, commit quality
  → Web search: latest AI agent research, better prompting techniques
  → Diagnose: what is the single biggest weakness in the agent team right now?
  → Form hypothesis: what change will improve the quality score most?
  → Record baseline before touching anything
  → Implement the improvement (edits run.py, agent prompts, specialist files)
  → Measure after — did the score improve?
  → Write result to meta/experiments/
  → Update meta/findings.md with what was learned
  → Update meta/backlog.md with next improvement ideas
  → Commit improvements
END
```

---

## How the Agent Grows Over Time

**Day 1**
Agent reads your project, generates a backlog, starts building features.

**Week 1**
Agent has 30+ sessions of history. Knows what works in your codebase. Has saved reusable skills. Meta-agent has improved the prompts 20+ times.

**Month 1**
Agent notices no users are signing up. Stops building features. Researches why. Finds the landing page converts at 0.1%. Redesigns it. Measures. Builds email capture. Measures again.

**Month 2**
Meta-agent has run 200+ improvement cycles. The agent that exists now is completely different from day 1 — faster, smarter, more accurate about your specific project. It has a library of skills, a research archive, and a pattern library of what works.

**Month 3**
Agent finds a Reddit thread where your target users complain about something your competitors don't solve. Adds it to the backlog. Builds it. Measures if it moved the North Star. Doubles down if it did.

This is not a linear improvement. It compounds.

---

## The North Star System

The North Star is the ONE number that matters most. Everything the agent does is measured against it.

Every session:
1. Agent runs your measurement command → gets current number
2. Diagnoses the gap: "We're at $47/month. Need $500. Gap = $453. Why?"
3. Searches for what's blocking it (bad landing page? missing feature? wrong price?)
4. Picks the action most likely to move the number
5. Executes that action
6. Measures: did the number move?
7. If number hasn't moved in 3 sessions → **PIVOT MODE**: agent rewrites the entire BACKLOG with a different strategy

### Example North Stars

**SaaS product:**
```
Goal: $500/month recurring revenue
Command: curl -s http://localhost:8001/api/revenue | python -c "import sys,json; print(json.load(sys.stdin).get('mrr', 0))"
Target: 500
```

**Consumer app:**
```
Goal: 1000 daily active users
Command: python -c "import pymongo; c=pymongo.MongoClient(); print(c.mydb.sessions.count_documents({'date': __import__('datetime').date.today().isoformat()}))"
Target: 1000
```

**Can't measure yet:**
```
Goal: Get first 10 paying customers
Command: echo 0
Target: 10
```
Agent's first job will be to build the measurement system.

---

## Troubleshooting

**"claude.cmd not found"**
Run: `npm install -g @anthropic-ai/claude-code`
Then: `claude` and log in.

**"Rate limit reached"**
Normal in VS Code mode. Agent detects it, saves the retry time, sleeps automatically, and resumes when the limit resets. No action needed.

**Agent is doing the wrong things**
Edit `memory/backlog.md` — remove tasks you don't want, add tasks you do want. Agent picks up changes on next session.

**Agent keeps failing the same thing**
Check `memory/knowledge.md` — add the fix as a rule so the agent never repeats the mistake.

**Want to start fresh**
```bash
del autoagent\backend_mode.json
del autoagent\memory\current_task.md
del autoagent\memory\activity_log.md
```

**Switch from VS Code to API mode (or back)**
```bash
del autoagent\backend_mode.json
py -X utf8 autoagent/run.py
```

---

## Project Structure

```
autoagent/
  run.py                      ← Master runner — start here
  setup.py                    ← One-time dependency installer
  e2e_check.py                ← Playwright browser smoke test

  ── Templates (committed — copy these to get started) ──
  PROJECT.example.md          ← Copy → PROJECT.md and fill in
  NORTH_STAR.example.md       ← Copy → NORTH_STAR.md and fill in
  KEYS_NEEDED.example.md      ← Copy → KEYS_NEEDED.md (agent manages)
  config.example.json         ← Copy → config.json (optional overrides)

  ── Your project files (gitignored — not committed) ──
  PROJECT.md                  ← What the project is, how to run it
  NORTH_STAR.md               ← ONE goal + ONE measurement command
  KEYS_NEEDED.md              ← API keys the agent needs
  config.json                 ← Optional overrides

  ── Runtime memory (gitignored — agent manages these) ──
  memory/
    README.md                 ← Explains every file in this directory
    backlog.md                ← Task queue (agent manages, you can seed)
    current_task.md           ← Active task — auto-resumed on restart
    done.md                   ← Completed tasks log
    activity_log.md           ← Session-by-session history
    knowledge.md              ← Lessons learned — grows every session
    north_star.md             ← Live metric history copy
    project_root.md           ← Absolute path to project root

  agents/
    orchestrator.py           ← CEO brain
    engineer.py               ← Builds code
    researcher.py             ← Web research + independent ideation
    designer.py               ← UI/UX + screenshots
    strategist.py             ← Business strategy + pivot detection
    qa.py                     ← Testing + quality gate

  shared/
    hypotheses.md             ← Theory log
    debates.md                ← Specialist disagreements
    decisions.md              ← Major decisions log
    mission_brief.md          ← Orchestrator's brief each session

  meta/
    run.py                    ← Meta-agent runner
    MISSION.md                ← Meta-agent charter
    findings.md               ← What makes agents smarter (gitignored)
    backlog.md                ← Meta-agent's own improvement queue (gitignored)
    benchmarks/               ← Daily quality scores (gitignored)
    experiments/              ← A/B test results

  skills/
    INDEX.md                  ← Index of saved patterns
    *.md                      ← Reusable skill files

  reports/                    ← Daily session reports (gitignored)
```

---

## Philosophy

Most AI tools make you faster at doing what you were already going to do.

AutoAgent does what you weren't going to do — the research you'd skip, the tests you'd defer, the refactor you'd put off, the competitor analysis you'd never get to. It does all of it, measures whether it worked, learns from the result, and does it again tomorrow, better.

The goal is not automation. The goal is compounding intelligence — a system that is meaningfully smarter and more capable on day 100 than it was on day 1, without you having to do anything to make that happen.

You define the destination. The agents find the way.
