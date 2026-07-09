#!/usr/bin/env bash
# ============================================================
# 去AI痕迹润色 - 素材准备脚本
# 生成去AI润色所需的素材包，供 AI agent 读取后润色
# 用法: bash scripts/de_ai_rewrite.sh [章节号]
#   不传参数 → 润色最新一章
#   传参数   → 润色指定章节
# 输出: 生成 .deai_material_NNN.md 素材文件
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$PWD"
CONFIG_FILE="$BASE_DIR/config.env"
CHAPTERS_DIR="$BASE_DIR/chapters"
MATERIAL_FILE=""

# 加载配置
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "[错误] 找不到 config.env"
    exit 1
fi
source "$CONFIG_FILE"

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
        echo "[错误] 还没有章节可润色"
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

# 用 Python 生成去AI润色素材
MATERIAL_FILE="$BASE_DIR/.deai_material_${PADDED_NUM}.md"

export DEAI_CHAPTER_FILE="$CHAPTER_FILE"
export DEAI_MATERIAL_FILE="$MATERIAL_FILE"
export DEAI_CHAPTER_NUM="$CHAPTER_NUM"
export DEAI_CHAPTERS_DIR="$CHAPTERS_DIR"

python3 << 'PYEOF'
import os, re, glob

chapter_file = os.environ['DEAI_CHAPTER_FILE']
material_file = os.environ['DEAI_MATERIAL_FILE']
chapter_num = int(os.environ['DEAI_CHAPTER_NUM'])
chapters_dir = os.environ['DEAI_CHAPTERS_DIR']

# 读取章节内容（去掉之前的 de-AI 注释块）
with open(chapter_file, 'r', encoding='utf-8-sig') as f:
    raw_content = f.read()

# 去掉已有的 de-AI 注释块
content = re.sub(r'<!-- de-AI 润色报告 -->.*?<!-- 字数统计：.*?-->', '', raw_content, flags=re.DOTALL).strip()

# 统计字数
word_count = len(re.findall(r'[\u4e00-\u9fff]', content))

# 读取最近3章（用于风格一致）
recent_chaps = []
all_chapters = sorted(
    [f for f in os.listdir(chapters_dir) if re.match(r'ch\d+_第\d+章.*\.md$', f)],
    key=lambda x: int(re.search(r'ch(\d+)', x).group(1))
)
for fname in reversed(all_chapters[-3:]):
    if fname == os.path.basename(chapter_file):
        continue
    fpath = os.path.join(chapters_dir, fname)
    with open(fpath, 'r', encoding='utf-8-sig') as f:
        chap_content = f.read()
    # 去掉注释块
    chap_content = re.sub(r'<!-- de-AI 润色报告 -->.*?<!-- 字数统计：.*?-->', '', chap_content, flags=re.DOTALL)
    title = fname.replace('.md', '').split('_', 1)[1] if '_' in fname else fname
    recent_chaps.append(f"---\n章节: {title}\n{chap_content[:3000]}\n---")

# 生成素材文件
with open(material_file, 'w', encoding='utf-8') as f:
    f.write("# 去AI痕迹润色素材包\n\n")
    f.write(f"## 基本信息\n")
    f.write(f"- 章节号: 第{chapter_num}章\n")
    f.write(f"- 文件: {os.path.basename(chapter_file)}\n")
    f.write(f"- 中文字数: {word_count} 字\n")
    f.write(f"- 润色目标: 消除AI痕迹，使文字更接近真人作者风格\n\n")

    f.write(f"## 待润色章节内容\n")
    f.write(f"```\n{content}\n```\n\n")

    f.write(f"## 最近章节（风格一致参考）\n")
    f.write(f"{''.join(recent_chaps)}\n\n")

    f.write(f"## AI痕迹检测清单\n\n")
    f.write(f"以下特征会被识别为AI生成，必须消除：\n\n")

    f.write(f"### 1. 模板化开头\n")
    f.write(f"- ❌ 'XX睁开眼睛，映入眼帘的是...'\n")
    f.write(f"- ❌ 'XX感觉头痛欲裂，缓缓睁开眼睛...'\n")
    f.write(f"- ❌ 'XX猛地从床上坐起，大口喘着粗气...'\n")
    f.write(f"- ❌ 'XX发现自己穿越了，大脑一片空白...'\n")
    f.write(f"- ✅ 改成：直接从具体动作或对话切入\n\n")

    f.write(f"### 2. 万能套话\n")
    f.write(f"- ❌ '心中涌起一股暖流'\n")
    f.write(f"- ❌ '眼神变得坚定'\n")
    f.write(f"- ❌ '嘴角露出一丝微笑'\n")
    f.write(f"- ❌ '拳头不自觉地握紧'\n")
    f.write(f"- ❌ '脑海中闪过无数个念头'\n")
    f.write(f"- ❌ '深吸一口气，平复心情'\n")
    f.write(f"- ✅ 改成：用具体动作/表情/环境来表现情绪\n\n")

    f.write(f"### 3. 情绪平铺\n")
    f.write(f"- ❌ '他很生气' / '她感到非常悲伤' / '内心充满了恐惧'\n")
    f.write(f"- ✅ 改成：通过动作、表情、语言、环境来表现情绪\n")
    f.write(f"  例：不说'他很生气'，说'他把杯子重重摔在地上，碎片溅了一地'\n\n")

    f.write(f"### 4. 对话不自然\n")
    f.write(f"- ❌ 人物对话像说明书，过于书面化\n")
    f.write(f"- ❌ 所有角色说话风格一样\n")
    f.write(f"- ❌ 对话中大量使用完整句子\n")
    f.write(f"- ✅ 改成：加入语气词、省略句、口语化表达\n\n")

    f.write(f"### 5. 场景描写空洞\n")
    f.write(f"- ❌ 只有视觉描写，缺少其他感官\n")
    f.write(f"- ❌ 描写都是通用模板\n")
    f.write(f"- ✅ 改成：加入气味、温度、触感、声音等具体细节\n\n")

    f.write(f"### 6. 结构雷同\n")
    f.write(f"- ❌ 每章节奏模式一模一样\n")
    f.write(f"- ❌ 每章都以相同方式结尾\n")
    f.write(f"- ✅ 改成：不同章节采用不同结构\n\n")

    f.write(f"### 7. 重复句式\n")
    f.write(f"- ❌ 多章使用相同的句式结构\n")
    f.write(f"- ❌ 每段都以主语开头\n")
    f.write(f"- ✅ 改成：变换句式，长短句交替\n\n")

    f.write(f"## 去AI痕迹改写规则\n\n")
    f.write(f"1. **保留剧情不变** — 事件、对话内容、角色行为不动\n")
    f.write(f"2. **只改表达方式** — 把'AI腔'换成'真人腔'\n")
    f.write(f"3. **加入感官细节** — 气味、温度、触感、声音\n")
    f.write(f"4. **对话口语化** — 加入语气词、省略句\n")
    f.write(f"5. **情绪用行动表现** — 不说'他很生气'，写他摔东西的动作\n")
    f.write(f"6. **打破句式重复** — 长短句交替，有时省略主语\n")
    f.write(f"7. **加入个性化表达** — 不同角色有不同的说话习惯\n")
    f.write(f"8. **删掉废话** — AI喜欢凑字数，真人作者不废话\n\n")

    f.write(f"## 输出格式\n\n")
    f.write(f"直接输出润色后的完整章节内容。\n")
    f.write(f"在文件开头添加 de-AI 润色报告注释块。\n")
    f.write(f"在文件末尾添加字数统计注释块。\n")

print(f"[OK] 去AI润色素材已生成: {material_file}")
print(f"[OK] 章节: 第{chapter_num}章 ({word_count}字)")
PYEOF

echo "============================================"
echo "  去AI润色素材已生成"
echo "  章节: 第${CHAPTER_NUM}章"
echo "  素材文件: $MATERIAL_FILE"
echo "  请让 AI agent 读取此文件进行润色"
echo "============================================"
