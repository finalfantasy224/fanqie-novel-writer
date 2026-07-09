#!/usr/bin/env bash
# ============================================================
# 章节质量评价 - 素材准备脚本
# 生成评分所需的完整素材包，供 AI agent 读取后评分
# 用法: bash scripts/evaluate_chapter.sh [章节号]
#   不传参数 → 准备最新一章的评分素材
#   传参数   → 准备指定章节的评分素材
# 输出: 生成 .eval_material_${PADDED}.md 文件
# ============================================================

set -euo pipefail

# Use CWD (book directory) instead of SCRIPT_DIR for book-relative paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="${CWD:-$PWD}"
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

THRESHOLD="${EVAL_THRESHOLD:-7}"
MIN_WORDS_VAL="2000"

# 获取章节号（默认最新章节）
CHAPTER_NUM="${1:-0}"
if [[ "$CHAPTER_NUM" == "0" ]]; then
    CHAPTER_NUM=$(python3 -c "
import os, re, glob
chapters_dir = '$CHAPTERS_DIR'
files = glob.glob(os.path.join(chapters_dir, 'ch[0-9][0-9][0-9]_*章*.md'))
if not files:
    print(0)
else:
    nums = [int(re.search(r'ch(\d+)', os.path.basename(f)).group(1)) for f in files if re.search(r'ch(\d+)', os.path.basename(f))]
    print(max(nums) if nums else 0)
")
    CHAPTER_NUM=$((CHAPTER_NUM - 1))
    if (( CHAPTER_NUM < 1 )); then
        echo "[错误] 还没有章节可评价"
        exit 1
    fi
fi

PADDED_NUM=$(printf "%03d" "$CHAPTER_NUM")

# 查找章节文件
CHAPTER_FILE=$(python3 -c "
import os, glob, re
pattern = os.path.join('$CHAPTERS_DIR', 'ch${PADDED_NUM}_第${CHAPTER_NUM}章*.md')
files = glob.glob(pattern)
print(files[0] if files else '')
")

if [[ -z "$CHAPTER_FILE" ]] || [[ ! -f "$CHAPTER_FILE" ]]; then
    echo "[错误] 找不到章节文件: ch${PADDED_NUM}_第${CHAPTER_NUM}章*.md"
    exit 1
fi

# 用 Python 生成完整素材包
MATERIAL_FILE="$BASE_DIR/.eval_material_${PADDED_NUM}.md"

export EVAL_CHAPTER_FILE="$CHAPTER_FILE"
export EVAL_OUTLINE_FILE="$OUTLINE_FILE"
export EVAL_CHARACTERS_FILE="$CHARACTERS_FILE"
export EVAL_MATERIAL_FILE="$MATERIAL_FILE"
export EVAL_THRESHOLD="$THRESHOLD"
export EVAL_MIN_WORDS="$MIN_WORDS_VAL"
export EVAL_CHAPTER_NUM="$CHAPTER_NUM"
export EVAL_CHAPTERS_DIR="$CHAPTERS_DIR"

python3 << 'PYEOF'
import os, re

chapter_file = os.environ['EVAL_CHAPTER_FILE']
outline_file = os.environ['EVAL_OUTLINE_FILE']
characters_file = os.environ['EVAL_CHARACTERS_FILE']
material_file = os.environ['EVAL_MATERIAL_FILE']
threshold = int(os.environ['EVAL_THRESHOLD'])
min_words = int(os.environ['EVAL_MIN_WORDS'])
chapter_num = int(os.environ['EVAL_CHAPTER_NUM'])
chapters_dir = os.environ['EVAL_CHAPTERS_DIR']

# 统计字数
with open(chapter_file, 'r', encoding='utf-8') as f:
    chapter_content = f.read()
word_count = len(re.findall(r'[\u4e00-\u9fff]', chapter_content))

# 读取最近章节（连贯性参考）
# 前10章各取500字（快速扫描），最近3章各取2000字（详细检查）
recent_chaps = []
all_chapters = sorted(
    [f for f in os.listdir(chapters_dir) if re.match(r'ch\d+_第\d+章.*\.md$', f)],
    key=lambda x: int(re.search(r'ch(\d+)', x).group(1))
)
# 排除当前评价的章节
other_chapters = [f for f in all_chapters if f != os.path.basename(chapter_file)]
for i, fname in enumerate(reversed(other_chapters)):
    fpath = os.path.join(chapters_dir, fname)
    # 最近3章取完整2000字，更早的只取500字
    read_len = 2000 if i < 3 else 500
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read(read_len)
    title = fname.replace('.md', '').split('_', 1)[1] if '_' in fname else fname
    marker = "[详细]" if i < 3 else "[摘要]"
    recent_chaps.append(f"{marker} {title}\n{content}\n---")
    # 最多取10章前文，避免素材过大导致截断
    if i >= 9:
        break

# 提取大纲对应章节
outline_snippet = ""
if os.path.exists(outline_file):
    with open(outline_file, 'r', encoding='utf-8') as f:
        outline_content = f.read()
    for m in re.finditer(r'([\u4e00-\u9fff].*?)（第(\d+)-(\d+)章）(.+?)(?=\n\n|\Z)', outline_content, re.DOTALL):
        title = m.group(1)
        start, end = int(m.group(2)), int(m.group(3))
        desc = m.group(4)
        if start <= chapter_num <= end:
            outline_snippet = f"{title}\n{desc.strip()}"
            break
    if not outline_snippet:
        outline_snippet = "(未在大纲中找到精确匹配的章节区间)\n使用完整大纲供参考\n" + outline_content[:3000]

# 读取角色设定
characters_content = ""
if os.path.exists(characters_file):
    with open(characters_file, 'r', encoding='utf-8') as f:
        characters_content = f.read()

# 生成素材文件
with open(material_file, 'w', encoding='utf-8') as f:
    f.write("# 章节质量评价素材包\n\n")
    f.write(f"## 基本信息\n")
    f.write(f"- 章节号: 第{chapter_num}章\n")
    f.write(f"- 文件: {os.path.basename(chapter_file)}\n")
    f.write(f"- 中文字数: {word_count} 字\n")
    f.write(f"- 达标要求: >= {min_words} 字\n")
    f.write(f"- 阈值: {threshold}/10\n\n")
    f.write(f"## 大纲要求（第{chapter_num}章应发生的事）\n---\n{outline_snippet}\n---\n\n")
    f.write(f"## 角色设定\n---\n{characters_content}\n---\n\n")
    f.write(f"## 最近章节（连贯性参考）\n---\n{''.join(recent_chaps)}\n---\n\n")
    f.write(f"## 待评价章节内容\n---\n{chapter_content}\n---\n\n")
    f.write(f"## 评分维度\n")
    f.write(f"1. 大纲对齐度（权重30%）: 是否写了大纲要求的剧情？有无跑题？\n")
    f.write(f"2. 字数达标（权重15%）: 是否 >= {min_words} 字？\n")
    f.write(f"3. 人物一致性（权重20%）: 角色行为是否符合设定？有无OOC？\n")
    f.write(f"4. 开篇钩子（权重10%）: 前200字是否有冲突/悬念/反转？\n")
    f.write(f"5. 结尾钩子（权重10%）: 是否留了悬念？禁止模板化结尾。\n")
    f.write(f"6. 爽点密度（权重15%）: 是否有打脸/逆袭/装逼/反转？旁衬到位？\n\n")
    f.write(f"## 输出格式\n")
    f.write(f"评分: d1,d2,d3,d4,d5,d6\n")
    f.write(f"加权总分: X.X\n")
    f.write(f"改进建议: 具体问题和建议\n")

print(f"[OK] 素材已生成: {material_file}")
print(f"[OK] 章节: 第{chapter_num}章 ({word_count}字)")
PYEOF

echo "============================================"
echo "  评价素材已生成"
echo "  章节: 第${CHAPTER_NUM}章"
echo "  素材文件: $MATERIAL_FILE"
echo "  请让 AI agent 读取此文件进行评分"
echo "============================================"
