# Fanqie-Novel-Writer: AI-Powered Tomato Novel Writing Pipeline

An automated novel writing pipeline for [Tomato Novel](https://fanqienovel.com) (番茄小说), using a multi-agent orchestrator to write, evaluate, de-AI, and rewrite chapters with quality gates.

## Why This Project

| Feature | Traditional AI Writing | This Project |
|---------|----------------------|-----------------------------|
| Quality Gate | Discover drift after writing | Auto-score every chapter, auto-rewrite if below threshold |
| AI Trace Detection | Hidden AI patterns, easy to reject | De-AI step after every chapter, 6-dimension evaluation |
| Context Window | Read all history (54KB+) | Last chapter + 2 summaries (~10KB) |
| Word Count | AI estimates off by 50%+ | Python regex exact count, dynamic config.env |
| Outline Alignment | Drifts after a few chapters | 30% score weight on outline adherence, post-volume correction |
| Multi-Book | Messy management | Independent book dirs, shared scripts |
| Setup | Build from scratch | One-command init, ready in 5 minutes |

**Core philosophy:** Let AI do what it's good at (writing), let humans do what they're good at (reviewing), and use automation to maintain stable quality.

## Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
|  Writer     │────▶│  De-AI       │────▶│  Evaluator   │────▶│  Pass?       │
│  Agent      │     │  Agent       │     │  Agent       │     │  (≥threshold)│
│  (write)    │     │  (de-AI)     │     │  (score)     │     │              │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                       │                │
                                                       ▼                │
                                                 ┌──────────────┐       │
                                                 │  Rewriter    │◀──────┘
                                                 │  Agent       │
                                                 │  (rewrite)   │
                                                 └──────────────┘
```

**关键改动（2026-07-20）：**
- 去AI润色在评价之前执行——Evaluator 评的是最终稿，不是原文
- 第3章完成后触发人工审核门控，开篇质量不过关不继续写作
- 签约评估提前到约1.2万字（第5章），不再等2万字

**Key design principles:**
- One chapter per run — strict outline alignment, stable quality
- Quality gate before moving on — evaluate on 7 dimensions, auto-rewrite if below threshold
- **De-AI after every chapter** — eliminate AI traces immediately, not at sign-off
- Dynamic configuration — word counts, thresholds all from `config.env`, never hardcoded
- Token-efficient — Writer Agent receives only last chapter + 2 chapter summaries (~10KB vs ~54KB)

## Quick Start

### Installation

```bash
# Clone the project
git clone https://github.com/finalfantasy224/fanqie-novel-writer.git
cd fanqie-novel-writer

# Install skills (so AI knows how to use this project)
hermes skills install skills/fanqie-novel-auto
hermes skills install skills/novel-outline-discipline
```

### Complete Workflow

```
1. Init ──→ 2. AI writes outline ──→ 3. AI writes characters ──→ 4. Write chapters ──→ 5. Sign-off ──→ 6. Publish
   init_book.py        outline.md            characters.md              orchestrator       at 20k words    publish_fanqie.py
```

#### Step 1: Initialize a new novel

```bash
python3 scripts/init_book.py "My Cultivation Family" "xianxia" "Li Xuan" "male"
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

Each chapter auto-executes: Writer → Evaluator → (Rewriter if needed) → De-AI → Next chapter

See `references/prompts/orchestrator.md` for details.

#### Step 5: Sign-off assessment (at ~20k words)

When word count reaches `SIGN_WORDS` (default 20,000), the orchestrator triggers a sign-off assessment on the entire manuscript.

#### Step 6: Publish

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
│       ├── .deai_report_NNN.md # De-AI reports (per chapter)
├── references/prompts/
│   ├── orchestrator.md      # Orchestrator scheduling logic
│   ├── writer-agent.md      # Writer Agent prompt template (with de-AI rules)
│   ├── evaluator-agent.md   # Evaluator Agent prompt template (7 dimensions)
│   ├── rewriter-agent.md    # Rewriter Agent prompt template
│   ├── de-ai-agent.md       # De-AI Agent prompt template
│   └── sign-assessment-agent.md  # Sign-off assessment prompt (6 dimensions)
├── scripts/                           # Shared scripts (CWD-based)
│   ├── gen_writer_goal.py            # Generate Writer Agent goal from config
│   ├── update_outline_status.py      # Auto-update outline status markers
│   ├── eval_material.py              # Prepare evaluation material → .temp/.eval_material_NNN.md
│   ├── deai_material.py              # Prepare de-AI material → .temp/.deai_material_NNN.md
│   ├── sign_assess.py                # Prepare sign-off assessment material → .temp/.sign_assess.md
│   ├── init_book.py                  # Initialize a new novel
│   └── publish_fanqie.py             # Chapter publishing script (API 3-step flow)
├── templates/
│   └── publish_guide.md
├── skills/                         # AI skills (install via hermes skills install)
│   ├── fanqie-novel-auto/
│   └── novel-outline-discipline/
└── README.md
```

### 2. Initialize a Novel

```bash
# Initialize a new book (use init_book.py)
python3 scripts/init_book.py "My New Novel" "genre" "Protagonist" "gender"
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
python3 ../../scripts/eval_material.py 10

# Step 5: De-AI (after evaluation passes)
python3 ../../scripts/deai_material.py 10

# Step 6: Publish (if passes)
python3 ../../scripts/publish_fanqie.py chapters/ch010_*.md
```

### 4. Automated Pipeline (Cron Job)

The recommended approach is to use the orchestrator as a cron job, which triggers the full Write→Evaluate→(Rewrite if needed)→De-AI cycle:

```
cronjob (triggered daily)
  → Orchestrator Agent reads orchestrator.md
  → Spawns Writer Agent (delegate_task)
  → Runs eval_material.py
  → Spawns Evaluator Agent (delegate_task)
  → If pass (≥ threshold): runs deai_material.py + spawns De-AI Agent
  → If fail (< threshold): spawns Rewriter Agent (delegate_task), re-evaluate
  → If word count reaches SIGN_WORDS: triggers sign-off assessment
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
| `SIGN_WORDS` | Sign-off word threshold | `20000` |
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

## De-AI Traces Removal

After every chapter passes evaluation, a De-AI agent runs to eliminate AI-generated patterns.

### What gets removed:
- Template openings ("XX opened eyes, white ceiling appeared before him")
- Universal clichés ("warmth surged in his heart", "took a deep breath")
- Emotion dumping (saying "he was angry" instead of showing it)
- Uniform dialogue style (all characters sound the same)
- Empty scene descriptions (only visual, no sensory details)
- Repetitive sentence structures
- Formulaic chapter endings

### How it works:
1. `deai_material.py` aggregates the chapter + recent chapters
2. De-AI Agent reads `de-ai-agent.md` prompt template
3. Agent modifies the chapter file in-place
4. De-AI report saved to `.deai_report_NNN.md` (separate from chapter)
5. Score must be ≥ 7/10 to pass

### Writer Agent de-AI rules
The Writer Agent itself is trained to write naturally — no AI clichés, no template openings, emotion shown through action not adjectives. This reduces the De-AI workload significantly.

## Sign-off Assessment (at ~20k words)

When word count reaches `SIGN_WORDS` (default 20,000), a comprehensive assessment runs:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| 开篇质量 | 25% | First 3 chapters hook quality |
| 主线清晰度 | 20% | Story line clarity |
| 爽点密度 | 15% | Satisfaction moment density |
| 人物辨识度 | 10% | Character memorability |
| 文笔自然度 | 15% | Natural writing style |
| AI痕迹检测 | 15% | AI trace detection |
| 现实合规 | N/A | Not separately scored — reality entity errors and era mistakes directly lower other dimension scores |

**Pass threshold:** Weighted total ≥ 7.5/10. AI trace score < 5.0 → must rewrite heavily. Reality entity errors or era mistakes flagged as "must fix before submission".

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
| **Writer** | Writes one chapter based on outline + context, applies de-AI rules | `writer-agent.md` |
| **Evaluator** | Scores chapter on 7 dimensions, outputs JSON | `evaluator-agent.md` |
| **Rewriter** | Rewrites chapter with evaluation feedback, applies de-AI rules | `rewriter-agent.md` |
| **De-AI** | Removes AI traces from polished chapter | `de-ai-agent.md` |
| **Sign-off Evaluator** | Full manuscript assessment at 20k words | `sign-assessment-agent.md` |

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
- **Chinese filenames in glob:** Use `glob.glob()` with proper patterns to find chapter files.
- **AI word count lies:** AI estimates can be off by 50%+. Always use Python regex after writing.
- **Outline drift:** AI may deviate from outline. Always verify outline alignment before writing.
- **Template endings:** Ban generic closing phrases like "充满了信心" or "才刚刚开始". Each ending must have a specific plot hook.
- **De-AI report is separate:** Reports go to `.deai_report_NNN.md`, chapter files stay clean.
- **Temporary files:** `.eval_*.md`, `.deai_material_*.md`, `.sign_assess.md` go into the book's `.temp/` directory and are gitignored.
- **Chapter over 3500 words:** If Writer exceeds MAX_WORDS, use Rewriter to compress rather than rewriting — keep core plot and key dialogue, remove repetitive conversations and redundant inner monologue.
- **Evaluation Order:** The pipeline is Writer → De-AI → Evaluator → (Rewriter if needed), not Evaluator → De-AI. De-AI runs before evaluation so the Evaluator scores the final polished version, matching what the sign-off editor will see.
- **Sign-off threshold:** Evaluation threshold for per-chapter scoring is configurable (`EVAL_THRESHOLD`). Sign-off assessment has a higher bar: weighted total ≥ 7.5/10 with AI trace score < 5.0 requiring heavy rewrite.
- **No word count tags in chapter files:** Chapter files should NOT contain `【本章字数：XXX字】` or `【下一章预告：XXX】` at the end. These are pipeline metadata, not story content. The pipeline scripts verify word counts separately.
- **Reality entity names:** All real place names, company names, media outlets, and universities MUST be replaced with fictional equivalents. See `{BOOK_DIR}/entities_mapping.md` for the full list and replacement rules. Tomato's 2026 review is extremely strict about this.
- **Era errors:** 2005-era stories cannot mention brands/terms that didn't exist yet (抖音, 拼多多, 等保三级认证, ICP许可证, etc.). The de-AI agent and Writer Agent both have era-check rules built in.
- **Mid-volume pacing boost:** When sign-off assessment flags "low satisfaction density in middle chapters", the most effective fix is inserting a mid-level face-slapping scene around chapters 10-20. The phone-call counterattack pattern works best (see below).

## Requirements

- Python 3.11+
- Access to Tomato Novel author backend (for API cookies and book IDs)

## License

MIT
