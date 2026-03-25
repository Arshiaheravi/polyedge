#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoAgent — Fully Autonomous, Self-Improving Project Agent

Usage:
    py -X utf8 autoagent/launcher.py                        # run forever
    py -X utf8 autoagent/launcher.py --tasks 5              # run 5 sessions then stop
    py -X utf8 autoagent/launcher.py --once                 # run 1 session then stop
    py -X utf8 autoagent/launcher.py --once --type meta     # force a meta session
    py -X utf8 autoagent/launcher.py --once --type brain    # force a brain session
    py -X utf8 autoagent/launcher.py --status               # show today's spend
"""
import io, json, os, subprocess, sys, time, webbrowser
from datetime import date, datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    # Suppress Windows "drive not found" / "critical error" pop-up dialogs.
    # SEM_FAILCRITICALERRORS (1) | SEM_NOOPENFILEERRORBOX (2) = 3
    import ctypes
    ctypes.windll.kernel32.SetErrorMode(3)

ROOT      = Path(__file__).resolve().parent.parent
AGENT_DIR = Path(__file__).resolve().parent
npm_bin   = os.path.join(os.environ.get("APPDATA", ""), "npm")
CLAUDE    = os.path.join(npm_bin, "claude.cmd")

# ── Paths ──────────────────────────────────────────────────────
PROMPT_FILE   = AGENT_DIR / "PROMPT.md"
PROJECT_FILE  = AGENT_DIR / "PROJECT.md"
SKILLS_DIR    = AGENT_DIR / "skills"
MEMORY_DIR    = AGENT_DIR / "memory"
META_DIR      = AGENT_DIR / "meta"
BUDGET_FILE   = AGENT_DIR / "daily_budget.json"
SKILLS_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

# ── Config ─────────────────────────────────────────────────────
def load_config() -> dict:
    defaults = {"mode": "cli", "daily_limit_usd": 15.0, "interval_hours": 2,
                "session_max_turns": 50, "model": "claude-opus-4-6",
                "git": {"project": {"token": "", "repo_url": "", "branch": "main", "commit_prefix": "agent"},
                        "autoagent": {"token": "", "repo_url": "", "branch": "main", "commit_prefix": "meta"}}}
    cfg_file = AGENT_DIR / "config.json"
    if cfg_file.exists():
        try:
            saved = json.loads(cfg_file.read_text(encoding="utf-8"))
            if "git" in saved:
                git = saved.pop("git")
                if "project" in git:   defaults["git"]["project"].update(git["project"])
                if "autoagent" in git: defaults["git"]["autoagent"].update(git["autoagent"])
            defaults.update(saved)
        except Exception: pass
    return defaults

cfg = load_config()

# ── Budget ─────────────────────────────────────────────────────
def budget_ok() -> bool:
    today = str(date.today())
    if not BUDGET_FILE.exists(): return True
    try:
        data = json.loads(BUDGET_FILE.read_text())
        return data.get(today, 0.0) < cfg["daily_limit_usd"]
    except Exception: return True

def log_cost(usd: float):
    today = str(date.today())
    data = {}
    if BUDGET_FILE.exists():
        try: data = json.loads(BUDGET_FILE.read_text())
        except Exception: pass
    data[today] = round(data.get(today, 0.0) + usd, 4)
    BUDGET_FILE.write_text(json.dumps(data, indent=2))

# ── Session type ───────────────────────────────────────────────
def get_session_type(session_num: int) -> str:
    if session_num % 20 == 0: return "deep"
    if session_num % 10 == 0: return "brain"
    if session_num % 5  == 0: return "meta"
    return "work"

# ── Build prompt ───────────────────────────────────────────────
def build_prompt(session_type: str) -> str:
    def tail(path, chars=1500):
        if not Path(path).exists(): return ""
        return Path(path).read_text(encoding="utf-8", errors="replace")[-chars:]

    base    = PROMPT_FILE.read_text(encoding="utf-8") if PROMPT_FILE.exists() else ""
    project = PROJECT_FILE.read_text(encoding="utf-8") if PROJECT_FILE.exists() else ""

    skills_list = ", ".join(p.name for p in SKILLS_DIR.glob("*.md")) if SKILLS_DIR.exists() else ""

    memory = (
        f"\n\n## RECENT SESSIONS\n{tail(MEMORY_DIR/'activity_log.md', 800)}"
        f"\n\n## BACKLOG\n{tail(MEMORY_DIR/'backlog.md', 1200)}"
        f"\n\n## KNOWLEDGE\n{tail(MEMORY_DIR/'knowledge.md', 1500)}"
    )

    if session_type == "work":
        skills_note = f"\nAVAILABLE SKILLS: {skills_list}\nRead relevant skill files before starting your task." if skills_list else ""
        return project + "\n\n" + base + skills_note + memory

    if session_type == "meta":
        meta_prompt = (META_DIR / "PROMPT.md").read_text(encoding="utf-8") if (META_DIR / "PROMPT.md").exists() else ""
        return meta_prompt + memory

    if session_type in ("brain", "deep"):
        brain_prompt = (META_DIR / "BRAIN_PROMPT.md").read_text(encoding="utf-8") if (META_DIR / "BRAIN_PROMPT.md").exists() else ""
        meta_prompt  = (META_DIR / "PROMPT.md").read_text(encoding="utf-8") if (META_DIR / "PROMPT.md").exists() else ""
        if session_type == "deep":
            return brain_prompt + "\n\n" + meta_prompt + memory
        return brain_prompt + memory

    return base + memory

# ── Run one session ────────────────────────────────────────────
def run_session(session_type: str, session_num: int) -> bool:
    if not os.path.exists(CLAUDE):
        print("  [AutoAgent] Claude CLI not found at:", CLAUDE); return False

    prompt = build_prompt(session_type)
    print(f"\n  [AutoAgent] Session #{session_num} — {session_type.upper()} — {datetime.now().strftime('%H:%M')}")

    # Short boot prompt — Claude reads its own instruction files
    boot_prompt = (
        f"Read autoagent/PROMPT.md for your instructions. "
        f"Read autoagent/PROJECT.md for project-specific rules, codebase conventions, git paths, and test commands. "
        f"Read autoagent/NORTH_STAR.md for the mission and success metrics. "
        f"Read autoagent/memory/activity_log.md, autoagent/memory/backlog.md, "
        f"autoagent/memory/knowledge.md, autoagent/memory/current_task.md for context. "
        f"Available skills: {', '.join(p.name for p in SKILLS_DIR.glob('*.md'))}. "
        f"Session type: {session_type.upper()}. "
        + ("Read autoagent/meta/PROMPT.md for this session's instructions." if session_type == "meta" else "")
        + ("Read autoagent/meta/BRAIN_PROMPT.md for this session's instructions." if session_type in ("brain", "deep") else "")
        + " Follow the instructions exactly."
    )
    proc = None
    try:
        # stream-json streams each event live so user sees progress in real time
        proc = subprocess.Popen(
            [CLAUDE, "-p", boot_prompt,
             "--output-format", "stream-json",
             "--verbose",
             "--dangerously-skip-permissions",
             "--max-turns", str(cfg.get("session_max_turns", 50))],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace"
        )
        import json as _json
        for raw in proc.stdout:
            raw = raw.strip()
            if not raw: continue
            try:
                ev = _json.loads(raw)
                t = ev.get("type", "")
                if t == "assistant":
                    for block in ev.get("message", {}).get("content", []):
                        if block.get("type") == "text" and block.get("text","").strip():
                            print(block["text"].strip(), flush=True)
                        elif block.get("type") == "tool_use":
                            inp = block.get("input", {})
                            name = block.get("name", "")
                            if name == "Read":
                                print(f"  → reading {inp.get('file_path','')}", flush=True)
                            elif name == "Write":
                                print(f"  → writing {inp.get('file_path','')}", flush=True)
                            elif name == "Bash":
                                print(f"  → running: {str(inp.get('command',''))[:80]}", flush=True)
                            elif name == "Edit":
                                print(f"  → editing {inp.get('file_path','')}", flush=True)
                            else:
                                print(f"  → {name}", flush=True)
                elif t == "result":
                    if cfg.get("mode") == "api":
                        cost = ev.get("cost_usd") or ev.get("total_cost_usd") or 0.0
                        if isinstance(cost, (int, float)) and cost > 0:
                            log_cost(cost)
                            print(f"\n  [Session complete] API cost: ${cost:.4f}", flush=True)
                        else:
                            print(f"\n  [Session complete]", flush=True)
                    else:
                        print(f"\n  [Session complete]", flush=True)
            except Exception:
                if raw and not raw.startswith("{"):
                    print(raw, flush=True)
        proc.wait()
        return proc.returncode == 0
    except KeyboardInterrupt:
        print("\n  [AutoAgent] Stopping session... (task steps saved in current_task.md — will resume next run)")
        if proc:
            proc.terminate()
            try: proc.wait(timeout=5)
            except: proc.kill()
        raise

# ── Dashboard tab management ───────────────────────────────────
_dashboard_opened = False

def _open_dashboard_once(path: str):
    """Open the dashboard in a browser tab the first time, then just update the file.
    Subsequent sessions update dashboard.html in place — the browser tab auto-refreshes
    if the user has it open, without spawning a new tab each session."""
    global _dashboard_opened
    if not _dashboard_opened:
        webbrowser.open(path)
        _dashboard_opened = True
    # After first open: file is already updated by generate_dashboard(),
    # browser will reflect changes on next manual refresh — no new tab opened.

# ── Dashboard ──────────────────────────────────────────────────
def generate_dashboard():
    sessions_file = AGENT_DIR / "sessions.json"
    template_file = AGENT_DIR / "dashboard.template.html"
    out_file      = AGENT_DIR / "dashboard.html"
    if not sessions_file.exists() or not template_file.exists():
        return
    try:
        sessions_data = sessions_file.read_text(encoding="utf-8")
        template = template_file.read_text(encoding="utf-8")
        out_file.write_text(template.replace("__SESSIONS_DATA__", sessions_data), encoding="utf-8")
        print(f"  [AutoAgent] Dashboard updated → autoagent/dashboard.html")
    except Exception as e:
        print(f"  [AutoAgent] Dashboard update failed: {e}")

# ── Status ─────────────────────────────────────────────────────
def show_status():
    today = str(date.today())
    spent = 0.0
    if BUDGET_FILE.exists():
        try: spent = json.loads(BUDGET_FILE.read_text()).get(today, 0.0)
        except Exception: pass
    log = MEMORY_DIR / "activity_log.md"
    print(f"\n  Today's spend: ${spent:.4f} / ${cfg['daily_limit_usd']}")
    if log.exists():
        lines = log.read_text(encoding="utf-8").splitlines()
        print("  Recent activity:")
        for l in lines[-10:]: print("   ", l)

# ── Ask mode ───────────────────────────────────────────────────
def ask_mode() -> str:
    print("\n  ┌─────────────────────────────────────┐")
    print("  │         AutoAgent — Mode Select     │")
    print("  ├─────────────────────────────────────┤")
    print("  │  1  CLI  (free, recommended)        │")
    print("  │  2  API  (paid, debug-friendly)     │")
    print("  └─────────────────────────────────────┘")
    while True:
        choice = input("  Choose [1/2]: ").strip()
        if choice == "1": return "cli"
        if choice == "2": return "api"
        print("  Please enter 1 or 2.")

# ── Main loop ──────────────────────────────────────────────────
def run():
    args = sys.argv[1:]

    if "--status" in args:
        show_status(); return

    if "--test" in args:
        print("\n  [AutoAgent] DRY RUN — building prompt without calling Claude...")
        prompt = build_prompt("work")
        print(f"  Prompt length : {len(prompt)} chars (~{len(prompt)//4} tokens)")
        print(f"  Session type  : WORK")
        print(f"  Skills found  : {', '.join(p.name for p in SKILLS_DIR.glob('*.md'))}")
        print(f"  Memory files  : {', '.join(p.name for p in MEMORY_DIR.glob('*.md'))}")
        print(f"  Claude CLI    : {'FOUND' if os.path.exists(CLAUDE) else 'NOT FOUND — install: npm install -g @anthropic-ai/claude-code'}")
        print("\n  Everything looks good. Run without --test to start.\n")
        return

    # Always ask mode at startup
    cfg["mode"] = ask_mode()
    print(f"\n  [AutoAgent] Mode: {cfg['mode'].upper()}")

    tasks_limit = None
    if "--once" in args: tasks_limit = 1
    if "--tasks" in args:
        idx = args.index("--tasks")
        if idx + 1 < len(args):
            tasks_limit = int(args[idx + 1])

    # Optional forced session type: --type work|meta|brain|deep
    forced_type = None
    if "--type" in args:
        idx = args.index("--type")
        if idx + 1 < len(args):
            forced_type = args[idx + 1]
            if forced_type not in ("work", "meta", "brain", "deep"):
                print(f"  [AutoAgent] Unknown session type '{forced_type}'. Use: work|meta|brain|deep"); return

    # Load session counter from budget file to persist across restarts
    counter_file = AGENT_DIR / "session_counter.json"
    session_num = 1
    if counter_file.exists():
        try: session_num = json.loads(counter_file.read_text()).get("count", 1)
        except Exception: pass

    work_done = 0

    while True:
        if tasks_limit and work_done >= tasks_limit:
            print(f"\n  [AutoAgent] Done. {work_done} work sessions completed.")
            break

        if not budget_ok():
            print(f"\n  [AutoAgent] Daily budget hit. Sleeping until tomorrow...")
            time.sleep(3600); continue

        stype = forced_type if forced_type else get_session_type(session_num)
        success = run_session(stype, session_num)

        if stype == "work" and success:
            work_done += 1

        generate_dashboard()
        if (AGENT_DIR / "dashboard.html").exists():
            _open_dashboard_once(str(AGENT_DIR / "dashboard.html"))

        # Save counter
        counter_file.write_text(json.dumps({"count": session_num + 1}))
        session_num += 1

        if tasks_limit and work_done >= tasks_limit:
            print(f"\n  [AutoAgent] Done. {work_done} work sessions completed.")
            break

        try:
            if tasks_limit:
                # --tasks mode: no wait, run sessions back to back
                pass
            else:
                # forever mode: 10 min between sessions
                print(f"\n  [AutoAgent] Sleeping 10min until next session...")
                time.sleep(600)
        except KeyboardInterrupt:
            print("\n  [AutoAgent] Stopped."); break

if __name__ == "__main__":
    run()
