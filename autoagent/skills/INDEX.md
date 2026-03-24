# Skill Library — Quick Reference

Read this first to find the right skill file before starting any task.

## When to use each skill

| Task type | Skill file | Key workflow it provides |
|---|---|---|
| Every session — agent meta-rules | `agent-patterns.md` | Failure modes, planning, verification contract, self-critique |
| Writing Python backend code | `coding.md` | Evidence-first, minimal change, route/service/model patterns |
| Debugging a bug or test failure | `debugging.md` | 5-step systematic process: read → reproduce → isolate → fix → verify |
| Security review / input validation | `security.md` | OWASP checklist, SQL injection, secrets, admin auth, user input |
| Slow route / performance issue | `performance.md` | N+1 queries, async blocking, caching, parallel fetches |
| Writing tests or fixing test failures | `testing.md` | Test-first spec, patching rules, what "tests pass" means |
| Git commits and pushes | `git.md` | Two-repo protocol, commit message format, pre-commit checks |
| Frontend HTML/CSS/JS changes | `coding.md` | Frontend patterns section |
| Playwright UI checks | `playwright.md` | How to run checks, pass/fail criteria, recon-then-action pattern |
| Research and web search tasks | `research.md` | Search strategy, evaluation criteria |
| UI/UX design changes | `design.md` | Dark theme rules, card aesthetic patterns, anti-AI-slop principles |
| Building Claude API features | `claude_api.md` | Model selection, streaming, tool use, common pitfalls |
| Pre-commit quality audit | `audit.md` | 8-person virtual senior dev team review — security, UX, performance, compliance |
| Excel / spreadsheet output | `xlsx.md` | openpyxl formulas, pandas export, financial color coding, zero error rules |
| PDF generation or reading | `pdf.md` | pypdf merge/split, pdfplumber extract, reportlab create, FileResponse return |
| Word document (.docx) | `docx.md` | docx-js creation, unpack/edit XML, critical page size + table rules |
| PowerPoint presentation (.pptx) | `pptx.md` | PptxgenJS creation, unpack/repack XML, design principles |
| MCP server development | `mcp-builder.md` | 4-phase workflow, TypeScript SDK, tool naming, evaluation |
| Self-contained HTML artifact | `web-artifacts.md` | React+Tailwind+shadcn bundle into single HTML file |
| Visual themes for docs/slides | `theme-factory.md` | 10 preset themes, apply consistently, custom theme generation |
| Generative / algorithmic art | `algorithmic-art.md` | p5.js, seeded randomness, parameter controls, single HTML output |
| Long-form document writing | `doc-coauthoring.md` | 3-stage co-authoring, section-by-section, reader testing |
| Internal team updates | `internal-comms.md` | 3P updates, incident reports, status reports, formatted templates |
| Brand color + font system | `brand-guidelines.md` | StockCards palette, Anthropic palette, CSS variable rules |
| Animated GIFs for Slack | `slack-gif.md` | PIL + imageio, emoji/message sizes, animation techniques |
| Creating new skill files | `skill-creator.md` | Skill file format, quality checklist, when to create vs reuse |
| Visual art / posters / design images | `canvas-design.md` | 2-phase: philosophy (.md) then canvas (.png/.pdf), 90% visual 10% text |

## Common task workflows (already proven)

**Add a new scoring function:**
1. Write function in `services/analysis.py` (pure — no I/O)
2. Write tests for ALL branches immediately (see testing.md)
3. Wire through: `signals.py` param → `dashboard.py` call → `StockSignal` field → frontend

**Add a new API endpoint:**
1. Create route in `src/stockcards/routes/newroute.py`
2. Register with `app.include_router()` in `src/stockcards/app.py`
3. Write 3 tests: happy path, not-found, error case

**Add a frontend-only feature:**
1. Edit `frontend/index.html` for HTML structure
2. Edit `frontend/app.js` for behavior
3. Edit `frontend/styles.css` for styling
4. Run Playwright check (see playwright.md)

**Fix a broken test:**
1. Run `py -m pytest tests/ --collect-only -q` — check for import errors first
2. Read the assertion error literally — it usually names the cause
3. Patch at the namespace where the name is looked up (see testing.md)
