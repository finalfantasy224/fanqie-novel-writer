---
name: fanqie-novel-auto
description: 番茄小说自动创作与发布 — 多agent orchestrator流水线（写→评→改）、番茄后台发布、config.env配置。触发词：番茄/番茄小说/fanqie/番茄作家后台/番茄作者/番茄发布/番茄上传/番茄投稿/自动写小说/番茄签到/番茄全勤/番茄签约/番茄审核/番茄数据。
related_skills: [novel-outline-discipline]
---

# 番茄小说自动化写作与发布

## 何时使用

当用户提到番茄小说自动创作、AI写小说、番茄发布章节、番茄后台API、番茄全勤、番茄签约、番茄投稿、自动写小说等需求时，使用本技能。

## 项目结构

```
fanqie-novel-writer/          ← Engine (公开, tracked in git)
├── references/prompts/    # Agent 提示词模板（供 delegate_task 加载）
│   ├── orchestrator.md
│   ├── writer-agent.md
│   ├── evaluator-agent.md
│   ├── rewriter-agent.md
│   ├── de-ai-agent.md
│   └── sign-assessment-agent.md
├── references/guides/     # 参考文档（非 prompt，供人类阅读）
│   ├── reality-entity-compliance.md
│   └── volume1-postmortem.md
├── scripts/               # 共享脚本（所有书共用，Python 实现）
│   ├── gen_writer_goal.py           # 从config.env生成Writer Agent goal
│   ├── update_outline_status.py     # 自动更新outline状态
│   ├── eval_material.py             # 准备评价素材 → .temp/.eval_material_NNN.md
│   ├── deai_material.py             # 去AI润色素材 → .temp/.deai_material_NNN.md
│   ├── sign_assess.py               # 签约评估素材 → .temp/.sign_assess.md
│   ├── init_book.py                 # 新书初始化脚本
│   └── publish_fanqie.py            # 章节发布脚本
├── templates/
│   └── publish_guide.md   # 发布指南
└── README.md

novels/                  ← Novel Data (私有, gitignored)
└── bookN_<slug>/
    ├── config.env       # 含 Cookie，绝不上 git
    ├── outline.md
    ├── characters.md
    ├── chapters/        # 章节正文 chNNN_第N章 标题.md
    └── .temp/           # 临时文件（素材、报告、结果JSON等）
```

- Engine 层是通用代码，可以公开到 GitHub
- Novels 层是用户的私人创作数据，`.gitignore` 忽略整个 `novels/`
- 每个 book 目录通过 `cd` 进入后运行脚本，不依赖绝对路径
- 新建小说: `python3 scripts/init_book.py "书名" "类型" "主角名" "性别"`

## 字数标准（番茄平台）

- **单章目标**: 2000-3500 字，目标 2500 字
- **config.env**: `MIN_WORDS=2000`, `MAX_WORDS=3500`, `CHAPTER_WORDS_TARGET=2500`
- **统计方法**: Python正则 `re.findall(r'[\u4e00-\u9fff]', content)` 统计纯中文字符
- **严禁AI估算字数**（偏差可达50%+）

## 多Agent Orchestrator 流水线（核心流程）

**流程**: 一个 orchestrator agent 串行调度三个专业 agent——Writer（写）→ Evaluator（评）→ Rewriter（改），完成"写一章→评价→不达标重写→继续下一章"。

**步骤**:
```
1. python3 scripts/gen_writer_goal.py <book_dir> <chapter_num>
   → 从config.env读取字数配置，生成Writer Agent goal模板

2. delegate_task → Writer Agent
   → 传入精简上下文：上一章完整内容 + 最近2章开头各200字 + 大纲片段 + 角色设定前500字
   → 产出: chapters/chNNN_第N章 标题.md

3. python3 scripts/update_outline_status.py <chapter_num> <book_dir>
   → 将outline.md中该章标记为 ✅已完成

4. python3 scripts/eval_material.py <chapter_num>
   → 生成 .temp/.eval_material_NNN.md 评价素材

5. delegate_task → Evaluator Agent
   → 读取 .temp/.eval_material_NNN.md，输出JSON评分
   → 7维度：大纲对齐度(30%)、字数达标(15%)、人物一致性(20%)、开篇钩子(10%)、结尾钩子(10%)、爽点密度(15%)、连贯性(10%)

6. 判定: weighted_total >= EVAL_THRESHOLD(7)?
   → YES → 继续下一章
   → NO  → delegate_task → Rewriter Agent（带反馈重写，最多EVAL_MAX_RETRIES=2次）
           → 回到步骤3（重新评价）
```

**评分JSON格式**:
```json
{
  "scores": [d1, d2, d3, d4, d5, d6, d7],
  "weights": [0.30, 0.15, 0.20, 0.10, 0.10, 0.15, 0.10],
  "weighted_total": X.X,
  "pass": true/false,
  "suggestion": "具体问题和建议",
  "detail": { "dimension_1": "...", ... }
}
```

**错误处理**:
- Writer产出文件不存在 → 重试1次
- 重试MAX_RETRIES次仍不达标 → 标记"待人工审核"，继续下一章
- 任何agent调用失败 → 记录错误，跳过该章

## 发布流程（三步）

1. **new_article**: POST 创建章节草稿 → 返回 item_id
2. **cover_article**: POST 存草稿（带 volume_id, volume_name）
3. **publish_article**: POST 确认发布（publish_status=1）

publish_fanqie.py 已实现完整三步流程，自动从章节文件名提取章节号，内置指数退避重试（3次）。

## config.env 关键字段

```
NOVEL_TITLE="书名"
GENRE="类型"
PROTAGONIST_NAME="主角名"
MIN_WORDS=2000
MAX_WORDS=3500
CHAPTER_WORDS_TARGET=2500
EVAL_THRESHOLD=7
EVAL_MAX_RETRIES=2
TOMATO_COOKIE="..."
BOOK_ID=""
CURRENT_VOLUME_ID=""
CURRENT_VOLUME_NAME=""
```

## Pitfalls

- **脚本统一在根目录**: 所有共享脚本（gen_writer_goal.py, update_outline_status.py, eval_material.py, deai_material.py, sign_assess.py, init_book.py, publish_fanqie.py）放在根 `scripts/`，每本书通过 CWD 调用。不要在各书目录下放副本。
- **CWD 感知**: `eval_material.py` 从 `$PWD`（当前工作目录）查找 `config.env`，必须在书目录下运行。
- **脚本精简**: 每本书 scripts/ 下只保留必要的个人脚本。根目录 scripts/ 下的共享脚本通过 CWD 调用。不要在各书目录下放副本。
- **字数硬编码**: delegate_task 的 goal 中字数必须从 config.env 动态读取，不能写死
- **outline状态**: 写完必须用 update_outline_status.py 更新，否则 publish 时不知道哪些已写完
- **连贯性检查**: Evaluator 新增第7维度"连贯性"，检查与前文矛盾、角色状态一致性、重复事件
- **不要跨书引用**: 每本书的 prompt 只能引用本书内容，禁止提到其他书
- **publish_article不需要title**: 但 new_article 和 cover_article 需要 title 参数
- **章节末尾不写字数标注**: 番茄后台自动识别章节内容。字数标注是流水线内部使用的元数据，不应出现在正文文件中。每章完成后用Python正则验证字数即可，不要写入【本章字数：XXXX字】到章节文件。
- **现实实体名替换**: 签约审核严格，所有现实地名/公司名/媒体名必须替换为虚构名称。具体规则见 `{BOOK_DIR}/entities_mapping.md`。
- **时代错误检测**: 2005年背景不能出现超越设定年代的术语（抖音、拼多多、等保三级认证、ICP许可证、德勤审计等）。写作和去AI时必须逐条检查。
- **Writer容易过度分割段落**: 每段1-2句导致字数超标。Writer/Rewriter prompt中需明确"每段不超过3行"。超过3500字时用Rewriter压缩而非重写。
- **去AI痕迹报告独立存储**: .deai_report_NNN.md 必须与章节正文分离，不能混入章节文件。任何元数据泄露到章节正文都是致命错误——番茄2026年对AI内容审核极严，元数据泄露直接拒签。

## Related Files

- `scripts/init_book.py` — 新书初始化脚本
- `templates/publish_guide.md` — 发布指南
