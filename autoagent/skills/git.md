# Skill: Git

## TWO SEPARATE REPOS — CRITICAL
- StockCards.ca source code → project repo
- AutoAgent itself → autoagent repo
- autoagent/ is in .gitignore of StockCards.ca — NEVER `git add autoagent/` from project root

## PROJECT REPO (StockCards.ca code changes)
```bash
git -C "C:/Users/arshi/OneDrive/Desktop/StockCards.ca" add src/ frontend/ tests/ requirements.txt
git -C "C:/Users/arshi/OneDrive/Desktop/StockCards.ca" commit -m "agent: <what> — <why>"
git -C "C:/Users/arshi/OneDrive/Desktop/StockCards.ca" push origin main
```

## AUTOAGENT REPO (agent improvements)
```bash
git -C "C:/Users/arshi/OneDrive/Desktop/StockCards.ca/autoagent" add .
git -C "C:/Users/arshi/OneDrive/Desktop/StockCards.ca/autoagent" commit -m "meta: <what>"
git -C "C:/Users/arshi/OneDrive/Desktop/StockCards.ca/autoagent" push origin main
```

## DECISION RULE
Before every commit ask:
- Changed src/, frontend/, tests/? → StockCards repo
- Changed autoagent/? → AutoAgent repo
- Changed both? → TWO commits, one per repo

## COMMIT MESSAGE FORMAT
- Project changes: `agent: add Kelly sizing endpoint — Elite tier upgrade incentive`
- AutoAgent changes: `meta: add database skill file — recurring migration failures`

## BEFORE COMMITTING
1. Run tests — they must be green
2. `git diff --stat` — confirm you changed what you intended
3. Never force push to main
4. Never commit .env files or API keys
