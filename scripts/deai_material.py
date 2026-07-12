#!/usr/bin/env python3
"""生成去AI痕迹润色素材包，供 AI agent 读取后润色。

用法:
    python3 scripts/deai_material.py [章节号]
      不传参数 → 润色最新一章
      传参数   → 润色指定章节

输出: 生成 .temp/.deai_material_NNN.md 素材文件

依赖: Python 3.11+, 当前目录需有 config.env
"""
import os
import re
import sys


def find_chapter_files(chapters_dir):
    """返回按章节号排序的所有章节文件名列表."""
    files = []
    for fname in os.listdir(chapters_dir):
        if re.match(r"ch\d+_第\d+章.*\.md$", fname):
            m = re.search(r"ch(\d+)", fname)
            if m:
                num = int(m.group(1))
                files.append((num, fname))
    files.sort(key=lambda x: x[0])
    return files


def strip_deai_comments(content):
    """去掉已有的 de-AI 注释块."""
    return re.sub(
        r"<!-- de-AI 润色报告 -->.*?<!-- 字数统计：.*?-->",
        "",
        content,
        flags=re.DOTALL,
    ).strip()


DEAI_CHECKLIST = """以下特征会被识别为AI生成，必须消除：

### 1. 模板化开头
- ❌ 'XX睁开眼睛，映入眼帘的是...'
- ❌ 'XX感觉头痛欲裂，缓缓睁开眼睛...'
- ❌ 'XX猛地从床上坐起，大口喘着粗气...'
- ❌ 'XX发现自己穿越了，大脑一片空白...'
- ✅ 改成：直接从具体动作或对话切入

### 2. 万能套话
- ❌ '心中涌起一股暖流'
- ❌ '眼神变得坚定'
- ❌ '嘴角露出一丝微笑'
- ❌ '拳头不自觉地握紧'
- ❌ '脑海中闪过无数个念头'
- ❌ '深吸一口气，平复心情'
- ✅ 改成：用具体动作/表情/环境来表现情绪

### 3. 情绪平铺
- ❌ '他很生气' / '她感到非常悲伤' / '内心充满了恐惧'
- ✅ 改成：通过动作、表情、语言、环境来表现情绪
  例：不说'他很生气'，说'他把杯子重重摔在地上，碎片溅了一地'

### 4. 对话不自然
- ❌ 人物对话像说明书，过于书面化
- ❌ 所有角色说话风格一样
- ❌ 对话中大量使用完整句子
- ✅ 改成：加入语气词、省略句、口语化表达

### 5. 场景描写空洞
- ❌ 只有视觉描写，缺少其他感官
- ❌ 描写都是通用模板
- ✅ 改成：加入气味、温度、触感、声音等具体细节

### 6. 结构雷同
- ❌ 每章节奏模式一模一样
- ❌ 每章都以相同方式结尾
- ✅ 改成：不同章节采用不同结构

### 7. 重复句式
- ❌ 多章使用相同的句式结构
- ❌ 每段都以主语开头
- ✅ 改成：变换句式，长短句交替

## 去AI痕迹改写规则

1. **保留剧情不变** — 事件、对话内容、角色行为不动
2. **只改表达方式** — 把'AI腔'换成'真人腔'
3. **加入感官细节** — 气味、温度、触感、声音
4. **对话口语化** — 加入语气词、省略句
5. **情绪用行动表现** — 不说'他很生气'，写他摔东西的动作
6. **打破句式重复** — 长短句交替，有时省略主语
7. **加入个性化表达** — 不同角色有不同的说话习惯
8. **删掉废话** — AI喜欢凑字数，真人作者不废话

## 输出格式

直接输出润色后的完整章节内容。
在文件开头添加 de-AI 润色报告注释块。
在文件末尾添加字数统计注释块。
"""


def main():
    if len(sys.argv) > 2:
        print(f"用法: {sys.argv[0]} [章节号]", file=sys.stderr)
        sys.exit(1)

    # --- 参数解析 ---
    chapter_num_arg = sys.argv[1] if len(sys.argv) == 2 else "0"
    try:
        chapter_num = int(chapter_num_arg)
    except ValueError:
        print(f"错误: 章节号必须是整数，收到 '{chapter_num_arg}'", file=sys.stderr)
        sys.exit(1)

    base_dir = os.getcwd()
    config_path = os.path.join(base_dir, "config.env")
    chapters_dir = os.path.join(base_dir, "chapters")
    temp_dir = os.path.join(base_dir, ".temp")

    if not os.path.isfile(config_path):
        print("[错误] 找不到 config.env，请确保在小说目录下运行", file=sys.stderr)
        sys.exit(1)

    # 确定章节号
    all_chaps = find_chapter_files(chapters_dir)
    if not all_chaps:
        print("[错误] 还没有章节可润色", file=sys.stderr)
        sys.exit(1)

    if chapter_num == 0:
        max_num = max(num for num, _ in all_chaps)
        chapter_num = max_num - 1
    if chapter_num < 1:
        print("[错误] 还没有章节可润色", file=sys.stderr)
        sys.exit(1)

    padded = f"{chapter_num:03d}"

    # 查找章节文件
    pattern = os.path.join(chapters_dir, f"ch{padded}_第{chapter_num}章*.md")
    import glob

    matches = glob.glob(pattern)
    if not matches:
        print(
            f"[错误] 找不到章节文件: ch{padded}_第{chapter_num}章*.md", file=sys.stderr
        )
        sys.exit(1)

    chapter_file = matches[0]
    chapter_fname = os.path.basename(chapter_file)

    # --- 读取章节内容（去掉之前的 de-AI 注释块） ---
    with open(chapter_file, "r", encoding="utf-8-sig") as f:
        raw_content = f.read()
    content = strip_deai_comments(raw_content)
    word_count = len(re.findall(r"[\u4e00-\u9fff]", content))

    # 读取最近3章（用于风格一致）
    recent_chaps = []
    other_chaps = [(n, fn) for n, fn in all_chaps if fn != chapter_fname]
    last_3 = list(reversed(other_chaps))[:3]

    for num, fname in last_3:
        fpath = os.path.join(chapters_dir, fname)
        with open(fpath, "r", encoding="utf-8-sig") as f:
            chap_content = f.read()
        chap_content = strip_deai_comments(chap_content)
        title = fname.replace(".md", "").split("_", 1)[1] if "_" in fname else fname
        recent_chaps.append(f"---\n章节: {title}\n{chap_content[:3000]}\n---")

    # --- 生成素材文件 ---
    os.makedirs(temp_dir, exist_ok=True)
    material_file = os.path.join(temp_dir, f".deai_material_{padded}.md")

    with open(material_file, "w", encoding="utf-8") as f:
        f.write("# 去AI痕迹润色素材包\n\n")
        f.write(f"## 基本信息\n")
        f.write(f"- 章节号: 第{chapter_num}章\n")
        f.write(f"- 文件: {chapter_fname}\n")
        f.write(f"- 中文字数: {word_count} 字\n")
        f.write(f"- 润色目标: 消除AI痕迹，使文字更接近真人作者风格\n\n")
        f.write(f"## 待润色章节内容\n")
        f.write(f"```\n{content}\n```\n\n")
        f.write(f"## 最近章节（风格一致参考）\n")
        f.write(f"{''.join(recent_chaps)}\n\n")
        f.write("## AI痕迹检测清单\n\n")
        f.write(DEAI_CHECKLIST)

    print(f"[OK] 去AI润色素材已生成: {material_file}")
    print(f"[OK] 章节: 第{chapter_num}章 ({word_count}字)")


if __name__ == "__main__":
    main()
