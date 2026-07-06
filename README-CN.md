# Fanqie-Novel-Writer: 番茄小说 AI 写作流水线

一个面向 [番茄小说](https://fanqienovel.com) 的自动化写作系统，通过多 Agent 编排实现"写一章→评价→不达标重写→继续下一章"的完整流水线。

## 为什么选择这个项目

| 特性 | 传统 AI 写小说 | 本项目 |
|------|--------------|--------|
| 质量保障 | 写完才发现跑题 | 每章自动评分，不达标立即重写 |
| 上下文控制 | 读取全部历史章节（54KB+） | 只读上一章+最近2章摘要（10KB） |
| 字数达标 | AI 估算偏差可达 50% | Python 正则精确统计，config.env 动态配置 |
| 大纲一致性 | 写到后面完全脱节 | 每章评分30%权重对齐大纲，卷完结反推修正 |
| 跨书管理 | 多本书混乱 | 每本书独立目录，公共脚本复用 |
| 开箱即用 | 从零搭建 | 初始化脚本一键创建，5分钟上手 |

**核心理念：** 让 AI 做它擅长的事（写），让人工审核做它擅长的事（评），用自动化流水线保证质量稳定。

## 核心流程

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│  Writer     │────▶│  Evaluator   │────▶│  通过?      │────▶│  下一章       │
│  Agent      │     │  Agent       │     │  (≥7/10)    │     │              │
│  (写作)     │◀────│  (评分)      │     │             │     └──────────────┘
└─────────────┘     └──────────────┘     └─────────────┘
       ▲                     │                   │
       │                     ▼                   │
       │              ┌──────────────┐           │
       └──────────────│  Rewriter    │           │
                      │  Agent       │           │
                      │  (重写)      │           │
                      └──────────────┘           │
                                                 │
                                    (低于7分重试，最多2次)
```

**设计理念：**
- 每次只写一章 —— 严格对齐大纲，质量稳定
- 写完即评 —— 7维度评分，不达标自动重写
- 配置动态化 —— 字数、阈值全部来自 `config.env`，绝不硬编码
- 上下文精简 —— Writer Agent 只接收上一章+最近2章摘要（约10KB，而非54KB）

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/fanqie-novel-writer.git
cd fanqie-novel-writer

# 安装技能（让 AI 知道如何使用本项目）
hermes skills install skills/fanqie-novel-auto
hermes skills install skills/novel-outline-discipline
```

### 完整使用流程

```
1. 初始化 ──→  2. AI 写大纲 ──→  3. AI 写角色 ──→  4. 逐章写作 ──→  5. 发布
   init.sh       outline.md        characters.md     orchestrator       publish_fanqie.py
```

#### 第一步：初始化新书

```bash
bash templates/init.sh "书名" "类型" "主角名" "性别"
# 例: bash templates/init.sh "我的修仙家族" "仙侠家族" "李玄" "男"
```

这会创建 `novels/` 目录结构 + config.env + 空 outline + 空 characters。

#### 第二步：让 AI 写大纲和角色

把 `novels/你的书/outline.md` 和 `novels/你的书/characters.md` 发给 AI，让它根据书名和类型填充内容。

参考 `references/prompts/orchestrator.md` 中的 outline 质量标准。

#### 第三步：配置

编辑 `novels/你的书/config.env`：
- `TOMATO_COOKIE` — 浏览器 F12 → Network → 复制 Cookie 值
- `BOOK_ID` — 作品管理页 URL 中 `bookId=` 后面的数字
- `CURRENT_VOLUME_ID` — 创建卷后 URL 中 `volumeId=` 后面的数字
- `CURRENT_VOLUME_NAME` — 卷名

详细获取方法见 `templates/publish_guide.md`。

#### 第四步：逐章写作

每章自动执行：Writer → Evaluator → (Rewriter if needed) → 下一张

详见 `references/prompts/orchestrator.md`。

#### 第五步：发布

第一卷写完（30章）后，参考 `templates/publish_guide.md` 发布章节。

---

### 项目结构

```
fanqie-novel-writer/
├── novels/                          # 小说内容（私有，gitignored）
│   └── bookN_<slug>/               # 每本书一个目录
│       ├── config.env              # 书籍配置
│       ├── outline.md              # 大纲
│       ├── characters.md           # 角色设定
│       └── chapters/               # 章节文件
├── references/prompts/             # Agent 提示词模板
│   ├── orchestrator.md             # 调度逻辑
│   ├── writer-agent.md             # 写作模板
│   ├── evaluator-agent.md          # 评分模板（7维度）
│   └── rewriter-agent.md           # 重写模板
├── scripts/                           # 公共脚本（每本书通过 CWD 引用）
│   ├── gen_writer_goal.py            # 动态生成Writer Agent目标
│   ├── update_outline_status.py      # 自动更新大纲状态
│   ├── evaluate_chapter.sh           # 准备评价素材
│   └── publish_fanqie.py             # 章节发布脚本
├── templates/                      # 模板和指南
│   ├── init.sh                     # 新书初始化脚本
│   └── publish_guide.md            # 发布指南
├── skills/                         # AI 技能（hermes skills install 安装）
│   ├── fanqie-novel-auto/
│   └── novel-outline-discipline/
├── README.md
└── README-CN.md

#### 手动写一章（示例）

```bash
cd novels/book5_cultivation_family

# 生成 Writer Agent 目标
python3 ../../scripts/gen_writer_goal.py . 10

# 通过 orchestrator 写第10章

# 更新大纲状态
python3 ../../scripts/update_outline_status.py 10 .

# 准备评价素材
bash ../../scripts/evaluate_chapter.sh 10

# 发布（通过评价后）
python3 ../../scripts/publish_fanqie.py chapters/ch010_*.md
```

### 4. 自动化流水线（推荐）

通过 cron job 触发 orchestrator，自动执行完整的写→评→改流程：

```
cronjob (每日触发)
  → Orchestrator Agent 读取 orchestrator.md
  → 调用 Writer Agent (delegate_task)
  → 运行 evaluate_chapter.sh
  → 调用 Evaluator Agent (delegate_task)
  → 如果不通过：调用 Rewriter Agent (delegate_task)
  → 继续下一章
```

详见 `references/prompts/orchestrator.md`。

## 配置说明

### config.env 字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `NOVEL_TITLE` | 书名 | `"我的修仙家族"` |
| `GENRE` | 分类/标签 | `"仙侠家族"` |
| `PROTAGONIST_NAME` | 主角名 | `"李玄"` |
| `MIN_WORDS` | 最少字数 | `2000` |
| `MAX_WORDS` | 最多字数 | `3500` |
| `CHAPTER_WORDS_TARGET` | 目标字数 | `2500` |
| `EVAL_THRESHOLD` | 评分通过阈值 | `7` |
| `EVAL_MAX_RETRIES` | 最大重写次数 | `2` |
| `TOMATO_COOKIE` | 番茄后台 Cookie | `...` |
| `BOOK_ID` | 作品ID | `...` |
| `CURRENT_VOLUME_ID` | 当前卷ID | `...` |
| `CURRENT_VOLUME_NAME` | 当前卷名 | `""` |
| `VOLUMES` | 多卷配置 | `1:id1:卷1,31:id2:卷2` |

### 字数标准

番茄小说单章：**2000-3500 字**，目标 **2500 字**。

字数统计使用 Python 正则：`re.findall(r'[\u4e00-\u9fff]', content)`，仅统计纯中文字符。AI 估算不可靠（偏差可达50%+）。

## 评分系统

章节按 7 个维度评分（每项 1-10 分），加权计算：

| 维度 | 权重 | 说明 |
|------|------|------|
| 大纲对齐度 | 30% | 是否写了大纲要求的剧情？有无跑题？ |
| 字数达标 | 15% | 是否在 2000-3500 字范围内？ |
| 人物一致性 | 20% | 角色行为是否符合设定？有无OOC？ |
| 开篇钩子 | 10% | 前200字是否有冲突/悬念/反转？ |
| 结尾钩子 | 10% | 是否留了悬念？与下一章关联？ |
| 爽点密度 | 15% | 是否有打脸/逆袭/旁衬等爽点？ |
| 连贯性 | 10% | 与前文是否矛盾？角色状态是否一致？ |

**通过标准：** 加权总分 ≥ 7/10。不通过则自动重写（最多 `EVAL_MAX_RETRIES` 次）。

## 发布流程

通过 `publish_fanqie.py` 实现三步发布：

1. **new_article** — 创建章节草稿，返回 `item_id`
2. **cover_article** — 保存草稿内容（含 `volume_id`, `volume_name`）
3. **publish_article** — 确认发布（`publish_status=1`）

脚本内置指数退避重试（3次，2s/4s/8s）、多卷自动切换、UTF-8 BOM 处理。

```bash
cd novels/bookN && python3 scripts/publish_fanqie.py chapters/ch001_*.md
```

## 多 Agent 架构

### Agent 职责

| Agent | 职责 | 提示词模板 |
|-------|------|-----------|
| **Orchestrator** | 流程控制 — 调度其他 Agent，检查结果 | `orchestrator.md` |
| **Writer** | 根据大纲和上下文撰写单章 | `writer-agent.md` |
| **Evaluator** | 7维度评分，输出 JSON | `evaluator-agent.md` |
| **Rewriter** | 根据评分反馈重写章节 | `rewriter-agent.md` |

### 上下文优化

Writer Agent 接收**最小上下文窗口**：
- 上一章完整内容（保持情节连贯）
- 最近2章开头各200字（了解人物语气和近期事件）
- 当前章节的大纲片段
- characters.md 前500字（关键角色设定）

替代了旧方案中读取所有章节的方式（~54KB → ~10KB），大幅节省 Token。

## 注意事项

- **Cookie 过期**：番茄后台 Cookie 约1-2个月失效，需定期刷新
- **字数硬编码**：`delegate_task` 的 goal 中字数必须从 `config.env` 动态读取，不能写死
- **文件名格式**：严格使用 `chNNN_第N章 标题.md`，脚本用 glob 通配符查找
- **bash→Python 传参**：用 `export VAR=value` + `os.environ['VAR']`，不要用 heredoc 内嵌字符串
- **AI 字数造假**：AI 估算偏差可达50%+，写完后必须用 Python 重新统计
- **大纲漂移**：AI 可能偏离大纲，写作前必须校验大纲区间
- **模板化结尾**：禁止反复使用"充满了信心""才刚刚开始"等空洞结尾，每章结尾必须有具体剧情钩子

## 环境要求

- Python 3.11+
- Bash（用于 shell 脚本）
- 番茄小说作者后台访问权限（获取 Cookie 和 Book ID）

## 许可证

MIT
