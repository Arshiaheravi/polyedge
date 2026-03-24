#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoAgent Launcher — Self-healing wrapper for run.py

Instead of running run.py directly, run this:
    py -X utf8 autoagent/launcher.py --tasks 2

What it does:
  - Starts run.py normally
  - If run.py crashes for ANY reason (SyntaxError, NameError, any bug),
    it automatically asks Claude to fix run.py, then restarts
  - Repeats until run.py finishes cleanly or max retries reached
  - You never need to manually fix bugs — it fixes itself
"""
import io
import os
import subprocess
import sys
import time
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT       = Path(__file__).resolve().parent.parent
AGENT_DIR  = Path(__file__).resolve().parent
RUN_PY     = AGENT_DIR / "run.py"
HEAL_LOG   = AGENT_DIR / "self_heal_log.md"
MAX_RETRIES = 5   # max auto-fix attempts before giving up

npm_bin    = os.path.join(os.environ.get("APPDATA", ""), "npm")
CLAUDE_CMD = os.path.join(npm_bin, "claude.cmd")


def _claude_available() -> bool:
    return os.path.exists(CLAUDE_CMD)


def _ask_claude_to_fix(error_output: str, attempt: int):
    """Call Claude CLI to fix run.py given the error output."""
    if not _claude_available():
        print("  [Launcher] Claude CLI not found — cannot auto-fix.")
        return False

    heal_prompt = f"""You are fixing a bug in an autonomous AI agent file: autoagent/run.py

ERROR THAT CAUSED THE CRASH:
{error_output[:3000]}

YOUR TASK (do all steps):
1. Read the file autoagent/run.py
2. Find the exact cause of this error
3. Fix it with the minimal change needed — do NOT refactor anything else
4. Verify syntax: py -X utf8 -c "import ast; ast.parse(open('autoagent/run.py', encoding='utf-8').read()); print('syntax ok')"
5. If syntax ok, commit the fix:
   cd autoagent && git add run.py && git commit -m "self-heal attempt {attempt}: fix {error_output[:80].strip()}" && git push https://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@github.com/Arshiaheravi/autoagent.git master

RULES:
- Fix ONLY what caused the crash — nothing else
- If you cannot find the root cause, wrap the failing section in try/except so it logs and continues instead of crashing
- The file must be valid Python after your fix
- End your response with either FIXED or COULD_NOT_FIX
"""
    import tempfile
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(heal_prompt)
            tmp = f.name
        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)
        cmd = f'type "{tmp}" | "{CLAUDE_CMD}" --print --dangerously-skip-permissions --max-turns 30'
        print(f"  [Launcher] Asking Claude to fix the bug (attempt {attempt}/{MAX_RETRIES})...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=600,
                                env=env, cwd=str(ROOT))
        output = result.stdout.strip()
        if "FIXED" in output:
            print(f"  [Launcher] Fix applied successfully.")
            return True
        elif "COULD_NOT_FIX" in output:
            print(f"  [Launcher] Claude could not fix this error.")
            return False
        elif output:
            print(f"  [Launcher] Fix attempt completed (no explicit FIXED/COULD_NOT_FIX signal).")
            return True  # assume fixed if there was output
        else:
            print(f"  [Launcher] No output from Claude.")
            return False
    except Exception as e:
        print(f"  [Launcher] Heal attempt failed: {e}")
        return False
    finally:
        if tmp:
            try: os.unlink(tmp)
            except: pass


def _log_heal(error_output: str, attempt: int, fixed: bool):
    from datetime import datetime
    entry = (
        f"\n---\n"
        f"## {datetime.now().strftime('%Y-%m-%d %H:%M')} — Attempt {attempt} — {'FIXED' if fixed else 'FAILED'}\n"
        f"```\n{error_output[:1000]}\n```\n"
    )
    with open(HEAL_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


def _syntax_check() -> tuple[bool, str]:
    """Check if run.py has valid syntax. Returns (ok, error_message)."""
    try:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-c",
             f"import ast; ast.parse(open(r'{RUN_PY}', encoding='utf-8').read()); print('ok')"],
            capture_output=True, text=True, timeout=10
        )
        if "ok" in result.stdout:
            return True, ""
        return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)


def run():
    args = sys.argv[1:]  # pass all args through to run.py (e.g. --tasks 2)
    attempt = 0

    while attempt <= MAX_RETRIES:
        # Syntax check before launching
        ok, syntax_err = _syntax_check()
        if not ok:
            attempt += 1
            print(f"\n  [Launcher] SyntaxError in run.py before launch:")
            print(f"  {syntax_err.strip()}")
            fixed = _ask_claude_to_fix(f"SyntaxError before launch:\n{syntax_err}", attempt)
            _log_heal(syntax_err, attempt, fixed)
            if not fixed:
                print(f"  [Launcher] Could not fix syntax error. Manual intervention needed.")
                sys.exit(1)
            time.sleep(2)
            continue  # retry after fix

        # Launch run.py
        cmd = [sys.executable, "-X", "utf8", str(RUN_PY)] + args
        print(f"\n  [Launcher] Starting run.py (attempt {attempt + 1})...")
        try:
            result = subprocess.run(cmd, cwd=str(ROOT))
            if result.returncode == 0:
                print(f"\n  [Launcher] run.py completed successfully.")
                return  # clean exit
            else:
                # Non-zero exit — something went wrong
                error_msg = f"run.py exited with code {result.returncode}"
                print(f"\n  [Launcher] {error_msg}")
                attempt += 1
                if attempt > MAX_RETRIES:
                    break
                fixed = _ask_claude_to_fix(error_msg, attempt)
                _log_heal(error_msg, attempt, fixed)
                if not fixed:
                    print(f"  [Launcher] Could not fix. Retrying anyway...")
                time.sleep(3)

        except KeyboardInterrupt:
            print("\n  [Launcher] Stopped by user.")
            return
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            print(f"\n  [Launcher] Unexpected crash: {error_msg}")
            attempt += 1
            if attempt > MAX_RETRIES:
                break
            fixed = _ask_claude_to_fix(error_msg, attempt)
            _log_heal(error_msg, attempt, fixed)
            time.sleep(3)

    print(f"\n  [Launcher] Max retries ({MAX_RETRIES}) reached. Please check self_heal_log.md")
    sys.exit(1)


if __name__ == "__main__":
    run()
