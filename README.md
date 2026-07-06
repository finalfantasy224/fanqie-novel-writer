# Fanqie-Novel-Writer: AI-Powered Tomato Novel Writing Pipeline

An automated novel writing pipeline for [Tomato Novel](https://fanqienovel.com) (番茄小说), using a multi-agent orchestrator to write, evaluate, and rewrite chapters with quality gates.

## Why This Project

| Feature | Traditional AI Writing | This Project |
|---------|----------------------|-----------------------------|
| Quality Gate | Discover drift after writing | Auto-score every chapter, auto-rewrite if below threshold |
| Context Window | Read all history (54KB+) | Last chapter + 2 summaries (~10KB) |
| Word Count | AI estimates off by 50%+ | Python regex exact count, dynamic config.env |
| Outline Alignment | Drifts after a few chapters | 30% score weight on outline adherence, post-volume correction |
| Multi-Book | Messy management | Independent book dirs, shared scripts |
| Setup | Build from scratch | One-command init, ready in 5 minutes |

**Core philosophy:** Let AI do what it's good at (writing), let humans do what they're good at (reviewing), and use automation to maintain stable quality.

## Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Writer     │────▶│  Evaluator   │────▶│  Pass?      │────▶│  Next Chapter│
│  Agent      │     │  Agent       │     │  (≥7/10)    │     │              │
│  (write)    │◀────│  (score)     │     │             │     └──────────────┘
└─────────────┘     └──────────────┘     └─────────────┘
       ▲                     │                   │
       │                     ▼                   │
       │              ┌──────────────┐           │
       └──────────────│  Rewriter    │           │
                      │  Agent       │           │
                      │  (rewrite)   │           │
                      └──────────────┘           │
                                                 │
                                    (fail < 7/10, retry ≤2x)
```

**Key design principles:**
- One chapter per run — strict outline alignment, stable quality
- Quality gate before moving on — evaluate on 7 dimensions, auto-rewrite if below threshold
- Dynamic configuration — word counts, thresholds all from `config.env`, never hardcoded
- Token-efficient — Writer Agent receives only last chapter + 2 chapter summaries (~10KB vs ~54KB)

## Quick Start

### Installation

```bash
# Clone the project
git clone https://github.com/yourusername/fanqie-novel-writer.git
cd fanqie-novel-writer

# Install skills (so AI knows how to use this project)
hermes skills install skills/fanqie-novel-auto
hermes skills install skills/novel-outline-discipline
```

### Complete Workflow

```
1. Init ──→ 2. AI writes outline ──→ 3. AI writes characters ──→ 4. Write chapters ──→ 5. Publish
   init.sh       outline.md            characters.md              orchestrator         publish_fanqie.py
```

#### Step 1: Initialize a new novel

```bash
bash templates/init.sh "My Cultivation Family" "xianxia" "Li Xuan" "male"
```

This creates the `novels/` directory structure with config.env, empty outline, and empty characters.

#### Step 2: Have AI write the outline and characters

Send `novels/your-book/outline.md` and `novels/your-book/characters.md` to your AI agent to fill in the content based on the book title and genre.

See `references/prompts/orchestrator.md` for outline quality standards.

#### Step 3: Configure

Edit `novels/your-book/config.env`:
- `TOMATO_COOKIE` — Browser F12 → Network → copy Cookie value
- `BOOK_ID` — Number after `bookId=` in the work management page URL
- `CURRENT_VOLUME_ID` — Number after `volumeId=` in the volume creation URL
- `CURRENT_VOLUME_NAME` — Volume name

See `templates/publish_guide.md` for detailed instructions.

#### Step 4: Write chapters

Each chapter auto-executes: Writer → Evaluator → (Rewriter if needed) → Next chapter

See `references/prompts/orchestrator.md` for details.

#### Step 5: Publish

After finishing the first volume (30 chapters), refer to `templates/publish_guide.md`.

---

### 1. Project Structure

```
fanqie-novel-writer/
├── novels/
│   └── bookN_<slug>/          # One directory per novel (private, gitignored)
│       ├── config.env          # Novel-specific configuration
│       ├── outline.md          # Chapter-by-chapter outline
│       ├── characters.md       # Character profiles
│       ├── chapters/           # Generated chapter files
│   └── scripts/
│           ├── gen_writer_goal.py           # Generate Writer Agent goal from config
│           ├── update_outline_status.py     # Auto-update outline status markers
│           └── evaluate_chapter.sh          # Prepare evaluation material
├── references/prompts/
│   ├── orchestrator.md      # Orchestrator scheduling logic
│   ├── writer-agent.md      # Writer Agent prompt template
│   ├── evaluator-agent.md   # Evaluator Agent prompt template (7 dimensions)
│   └── rewriter-agent.md    # Rewriter Agent prompt template
├── scripts/                           # Public scripts (CWD-based)
│   ├── gen_writer_goal.py            # Generate Writer Agent goal from config
│   ├── update_outline_status.py      # Auto-update outline status markers
│   ├── evaluate_chapter.sh           # Prepare evaluation material
│   └── publish_fanqie.py             # Chapter publishing script (API 3-step flow)
├── templates/
│   ├── init.sh
│   └── publish_guide.md
├── skills/                         # AI skills (install via hermes skills install)
│   ├── fanqie-novel-auto/
│   └── novel-outline-discipline/
└── README.md
```

### 2. Initialize a Novel

```bash
# Initialize a new book (use init.sh)
bash templates/init.sh "My New Novel" "genre" "Protagonist" "gender"
```

### 3. Write a Chapter (Manual)

```bash
cd novels/book5_cultivation_family

# Step 1: Generate Writer Agent goal
python3 ../../scripts/gen_writer_goal.py . 10

# Step 2: Write chapter 10 (via orchestrator / delegate_task)

# Step 3: Update outline status
python3 ../../scripts/update_outline_status.py 10 .

# Step 4: Evaluate
bash ../../scripts/evaluate_chapter.sh 10

# Step 5: Publish (if passes)
python3 ../../scripts/publish_fanqie.py chapters/ch010_*.md
```

### 4. Automated Pipeline (Cron Job)

The recommended approach is to use the orchestrator as a cron job, which triggers the full Write→Evaluate→Rewrite cycle:

```
cronjob (triggered daily)
  → Orchestrator Agent reads orchestrator.md
  → Spawns Writer Agent (delegate_task)
  → Runs evaluate_chapter.sh
  → Spawns Evaluator Agent (delegate_task)
  → If fail: spawns Rewriter Agent (delegate_task)
  → Continues to next chapter
```

See `references/prompts/orchestrator.md` for the full orchestration logic.

## Configuration

### config.env Fields

| Field | Description | Example |
|-------|-------------|---------|
| `NOVEL_TITLE` | Novel title | `""` |
| `GENRE` | Genre/tag | `"仙侠家族"` |
| `PROTAGONIST_NAME` | Protagonist name | `"李玄"` |
| `MIN_WORDS` | Minimum chapter word count | `2000` |
| `MAX_WORDS` | Maximum chapter word count | `3500` |
| `CHAPTER_WORDS_TARGET` | Target word count | `2500` |
| `EVAL_THRESHOLD` | Evaluation pass threshold | `7` |
| `EVAL_MAX_RETRIES` | Max rewrite attempts | `2` |
| `TOMATO_COOKIE` | Tomato Novel API cookie | `...` |
| `BOOK_ID` | Novel ID from Tomato backend | `...` |
| `CURRENT_VOLUME_ID` | Current volume ID | `...` |
| `CURRENT_VOLUME_NAME` | Current volume name | `""` |
| `VOLUMES` | Multi-volume config | `1:id1:卷1,31:id2:卷2` |

### Word Count Standards

Tomato Novel chapters: **2000-3500 words**, target **2500 words**.

Word count is calculated using Python regex: `re.findall(r'[\u4e00-\u9fff]', content)` — counts pure Chinese characters only. AI estimates are unreliable (50%+ deviation possible).

## Evaluation System

Chapters are scored on 7 dimensions (1-10 each), weighted:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| 大纲对齐度 | 30% | Does the chapter follow the outline? Any plot drift? |
| 字数达标 | 15% | Word count within 2000-3500 range? |
| 人物一致性 | 20% | Character behavior consistent with profiles? No OOC? |
| 开篇钩子 | 10% | Conflict/suspense in first 200 words? |
| 结尾钩子 | 10% | Cliffhanger ending tied to next chapter? |
| 爽点密度 | 15% | Face-slapping/counterattack/surprise moments? |
| 连贯性 | 10% | Consistent with previous chapters? No contradictions? |

**Pass threshold:** Weighted total ≥ 7/10. Below threshold → auto-rewrite with feedback (up to `EVAL_MAX_RETRIES` times).

## Publishing

Three-step API flow via `publish_fanqie.py`:

1. **new_article** — Create draft chapter, returns `item_id`
2. **cover_article** — Save draft with content, `volume_id`, `volume_name`
3. **publish_article** — Confirm publication (`publish_status=1`)

The script includes exponential backoff retry (3 attempts, 2s/4s/8s delays), automatic volume resolution for multi-volume novels, and UTF-8 BOM handling.

```bash
cd novels/bookN && python3 ../../scripts/publish_fanqie.py chapters/ch001_*.md
```

## Multi-Agent Architecture

### Agent Roles

| Agent | Responsibility | Prompt Template |
|-------|---------------|-----------------|
| **Orchestrator** | Flow control only — spawns other agents, checks results | `orchestrator.md` |
| **Writer** | Writes one chapter based on outline + context | `writer-agent.md` |
| **Evaluator** | Scores chapter on 7 dimensions, outputs JSON | `evaluator-agent.md` |
| **Rewriter** | Rewrites chapter with evaluation feedback | `rewriter-agent.md` |

### Context Optimization

The Writer Agent receives a **minimal context window**:
- Last chapter full content (for continuity)
- First 200 chars of 2 preceding chapters (for tone/style)
- Outline snippet for current chapter
- First 500 chars of characters.md (key character traits)

This replaces the old approach of reading all previous chapters (~54KB) with just ~10KB, saving significant tokens.

## Pitfalls & Gotchas

- **Cookie expiry:** Tomato Novel cookies expire after 1-2 months. Refresh periodically.
- **Word count hardcoding:** Never hardcode word limits in `delegate_task` goals. Always read from `config.env` via `gen_writer_goal.py`.
- **File naming:** Strictly use `chNNN_第N章 标题.md` format. Scripts use glob patterns to find files.
- **Bash→Python Chinese filenames:** Use `export VAR=value` + `os.environ['VAR']`, not heredoc interpolation.
- **AI word count lies:** AI estimates can be off by 50%+. Always use Python regex after writing.
- **Outline drift:** AI may deviate from outline. Always verify outline alignment before writing.
- **Template endings:** Ban generic closing phrases like "充满了信心" or "才刚刚开始". Each ending must have a specific plot hook.

## Requirements

- Python 3.11+
- Bash (for shell scripts)
- Access to Tomato Novel author backend (for API cookies and book IDs)

## License

MIT
