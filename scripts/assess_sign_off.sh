#!/usr/bin/env bash
# ============================================================
# 签约评估 - 综合评估已有章节是否符合番茄小说签约要求
# 生成签约评估素材包，供 AI agent 评估
# 用法: bash scripts/assess_sign_off.sh
# 输出: 生成 .sign_assess.md 签约评估素材文件
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$PWD"
CONFIG_FILE="$BASE_DIR/config.env"
CHAPTERS_DIR="$BASE_DIR/chapters"
OUTLINE_FILE="$BASE_DIR/outline.md"
CHARACTERS_FILE="$BASE_DIR/characters.md"
MATERIAL_FILE=""

# 加载配置
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "[错误] 找不到 config.env"
    exit 1
fi
source "$CONFIG_FILE"

SIGN_WORDS="${SIGN_WORDS:-20000}"
MIN_WORDS_VAL="${MIN_WORDS:-2000}"
NOVEL_TITLE="${NOVEL_TITLE:-未知书名}"
GENRE="${GENRE:-未知类型}"

# 导出环境变量供 Python 读取
export BASE_DIR
export NOVEL_TITLE
export GENRE
export SIGN_WORDS
export MIN_WORDS_VAL

# 用 Python 生成签约评估素材
python3 << 'PYEOF'
import os, re, glob, sys

base_dir = os.environ.get('BASE_DIR', os.getcwd())
chapters_dir = os.path.join(base_dir, 'chapters')
outline_file = os.path.join(base_dir, 'outline.md')
characters_file = os.path.join(base_dir, 'characters.md')
config_file = os.path.join(base_dir, 'config.env')
material_file = os.path.join(base_dir, '.sign_assess.md')

novel_title = os.environ.get('NOVEL_TITLE', '未知书名')
genre = os.environ.get('GENRE', '未知类型')
sign_words = int(os.environ.get('SIGN_WORDS', '20000'))
min_words = int(os.environ.get('MIN_WORDS', '2000'))

# 收集所有章节
chapters = sorted(
    glob.glob(os.path.join(chapters_dir, 'ch*.md')),
    key=lambda x: int(re.search(r'ch(\d+)', os.path.basename(x)).group(1))
)

if not chapters:
    print("[错误] 没有找到章节文件")
    sys.exit(1)

# 统计总字数和每章信息
total_words = 0
chapter_info = []
for cpath in chapters:
    fname = os.path.basename(cpath)
    with open(cpath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    wc = len(re.findall(r'[\u4e00-\u9fff]', content))
    total_words += wc
    # 提取章节号
    m = re.search(r'ch(\d+)_第(\d+)章', fname)
    chap_num = int(m.group(2)) if m else 0
    chapter_info.append({
        'file': cpath,
        'name': fname,
        'num': chap_num,
        'words': wc,
        'content': content
    })

# 读取大纲
outline_content = ""
if os.path.exists(outline_file):
    with open(outline_file, 'r', encoding='utf-8') as f:
        outline_content = f.read()

# 读取角色设定
characters_content = ""
if os.path.exists(characters_file):
    with open(characters_file, 'r', encoding='utf-8') as f:
        characters_content = f.read()

# 提取前3章（开篇评估）
opening_chapters = [c for c in chapter_info if c['num'] <= 3]
# 提取最近10章（节奏评估）
recent_chapters = chapter_info[-10:] if len(chapter_info) > 10 else chapter_info

# 生成素材文件
with open(material_file, 'w', encoding='utf-8') as f:
    f.write("# 番茄小说签约评估素材包\n\n")
    f.write(f"## 基本信息\n")
    f.write(f"- 书名: {novel_title}\n")
    f.write(f"- 类型: {genre}\n")
    f.write(f"- 已写章节: {len(chapter_info)} 章\n")
    f.write(f"- 总字数: {total_words} 字\n")
    f.write(f"- 签约门槛: {sign_words} 字\n")
    f.write(f"- 字数达标: {'是' if total_words >= sign_words else f'否（还需 {sign_words - total_words} 字）'}\n")
    f.write(f"- 单章最低要求: {min_words} 字\n")
    f.write(f"- 未达标章节数: {sum(1 for c in chapter_info if c['words'] < min_words)}\n\n")

    # 章节列表
    f.write(f"## 章节列表\n")
    f.write(f"| 章号 | 文件名 | 字数 | 达标 |\n")
    f.write(f"|------|--------|------|------|\n")
    for c in chapter_info:
        flag = "是" if c['words'] >= min_words else "否"
        f.write(f"| 第{c['num']}章 | {c['name']} | {c['words']} | {flag} |\n")
    f.write(f"\n")

    # 开篇评估（前3章）
    f.write(f"## 开篇章节内容（第1-{min(3, len(chapter_info))}章）\n")
    f.write(f"开篇决定编辑第一印象，以下为核心评估材料：\n\n")
    for c in opening_chapters:
        f.write(f"### 第{c['num']}章 ({c['words']}字)\n")
        f.write(f"```\n{c['content'][:5000]}\n```\n\n")

    # 最近章节摘要（节奏评估）
    f.write(f"## 最近章节摘要（节奏与质量评估）\n")
    for c in recent_chapters:
        # 只取每章前2000字作为摘要
        preview = c['content'][:2000]
        f.write(f"### 第{c['num']}章 ({c['words']}字)\n")
        f.write(f"```\n{preview}\n```\n\n")

    # 大纲
    f.write(f"## 完整大纲\n")
    f.write(f"```\n{outline_content[:8000]}\n```\n\n")

    # 角色设定
    f.write(f"## 角色设定\n")
    f.write(f"```\n{characters_content[:5000]}\n```\n\n")

    # 评估维度
    f.write(f"## 签约评估维度\n\n")
    f.write(f"### 1. 题材匹配度（权重20%）\n")
    f.write(f"- 题材是否为番茄热门类型？\n")
    f.write(f"- 标签是否准确？\n")
    f.write(f"- 是否符合平台内容规范（无违规内容）？\n\n")

    f.write(f"### 2. 开篇质量（权重25%）\n")
    f.write(f"- 第1章是否有冲突/悬念/反转？\n")
    f.write(f"- 前3章是否快速建立主角形象和核心矛盾？\n")
    f.write(f"- 代入感是否强？读者能否快速进入故事？\n")
    f.write(f"- 是否有流水账/慢热问题？\n\n")

    f.write(f"### 3. 人物设定（权重15%）\n")
    f.write(f"- 主角是否有记忆点/辨识度？\n")
    f.write(f"- 角色行为是否一致？\n")
    f.write(f"- 配角是否有存在感？\n\n")

    f.write(f"### 4. 节奏与主线（权重20%）\n")
    f.write(f"- 主线是否清晰？读者能否理解故事在讲什么？\n")
    f.write(f"- 节奏是否紧凑？有无拖沓章节？\n")
    f.write(f"- 是否有足够的爽点/冲突/反转？\n")
    f.write(f"- 每3-5章是否有小高潮？\n\n")

    f.write(f"### 5. 文笔与表达（权重10%）\n")
    f.write(f"- 语言是否流畅？\n")
    f.write(f"- 对话是否自然？\n")
    f.write(f"- 是否有大量错别字/语病？\n")
    f.write(f"- 叙述视角是否一致？\n\n")

    f.write(f"### 6. 字数与更新潜力（权重10%）\n")
    f.write(f"- 总字数是否达到 {sign_words} 字？\n")
    f.write(f"- 大纲是否有足够的扩展性写到10万字+？\n")
    f.write(f"- 当前章节质量能否支撑持续更新？\n\n")

    f.write("## 输出格式（严格遵守JSON）\n\n")
    f.write("```\n")
    f.write("{\n")
    f.write(f'  "total_words": {total_words},\n')
    f.write(f'  "chapter_count": {len(chapter_info)},\n')
    f.write(f'  "sign_threshold_met": {"true" if total_words >= sign_words else "false"},\n')
    f.write(f'  "scores": {{\n')
    f.write('    "开篇质量": X/10,\n')
    f.write('    "主线清晰度": X/10,\n')
    f.write('    "爽点密度": X/10,\n')
    f.write('    "人物辨识度": X/10,\n')
    f.write('    "文笔自然度": X/10,\n')
    f.write('    "AI痕迹检测": X/10\n')
    f.write('  }},\n')
    f.write('  "weights": {{\n')
    f.write('    "开篇质量": 0.25,\n')
    f.write('    "主线清晰度": 0.20,\n')
    f.write('    "爽点密度": 0.15,\n')
    f.write('    "人物辨识度": 0.10,\n')
    f.write('    "文笔自然度": 0.15,\n')
    f.write('    "AI痕迹检测": 0.15\n')
    f.write('  }},\n')
    f.write('  "weighted_total": X.X,\n')
    f.write('  "ai_trace_detected": true/false,\n')
    f.write('  "ai_trace_details": ["具体AI痕迹1", "具体AI痕迹2"],\n')
    f.write('  "recommend_sign": true/false,\n')
    f.write('  "issues": ["具体问题1", "具体问题2"],\n')
    f.write('  "suggestions": ["改进建议1", "改进建议2"],\n')
    f.write('  "can_submit_now": true/false,\n')
    f.write('  "priority_fixes": [\n')
    f.write('    {"issue": "...", "action": "...", "urgency": "高/中/低"}\n')
    f.write('  ]\n')
    f.write("}\n")
    f.write("```\n\n")
    f.write(f"## 判定规则\n\n")
    f.write(f"- weighted_total >= 7.0 且 can_submit_now = true → 建议提交签约\n")
    f.write(f"- weighted_total < 6.0 → 不建议提交，需重大修改\n")
    f.write(f"- 6.0 <= weighted_total < 7.0 → 有条件建议提交，需针对性修改\n")
    f.write("- 即使总分达标，如果开篇质量低于5.0，也必须先修改前3章\n")
    f.write("- 字数未达标时 can_submit_now 为 false，但可给出质量评估\n")

print(f"[OK] 签约评估素材已生成: {material_file}")
print(f"[OK] 总字数: {total_words} 字 / {sign_words} 字门槛")
print(f"[OK] 章节数: {len(chapter_info)} 章")
PYEOF

echo "============================================"
echo "  签约评估素材已生成"
echo "  书名: ${NOVEL_TITLE}"
echo "  章节: $(python3 -c "import glob,os; print(len(glob.glob(os.path.join('$CHAPTERS_DIR','ch*.md'))))") 章"
echo "  素材文件: $MATERIAL_FILE"
echo "  请让 AI agent 读取此文件进行签约评估"
echo "============================================"
