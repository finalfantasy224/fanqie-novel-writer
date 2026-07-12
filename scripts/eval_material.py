#!/usr/bin/env python3
"""生成章节质量评价素材包，供 AI agent 读取后评分。

用法:
    python3 scripts/eval_material.py [章节号]
      不传参数 → 准备最新一章的评分素材
      传参数   → 准备指定章节的评分素材

输出: 生成 .temp/.eval_material_NNN.md 文件

依赖: Python 3.11+, 当前目录需有 config.env
"""
import os
import re
import sys


def load_config(config_path):
    """从 config.env 加载配置."""
    config = {}
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            config[key.strip()] = val.strip().strip('"')
    return config


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
    outline_file = os.path.join(base_dir, "outline.md")
    characters_file = os.path.join(base_dir, "characters.md")

    if not os.path.isfile(config_path):
        print("[错误] 找不到 config.env，请确保在小说目录下运行", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    threshold = int(config.get("EVAL_THRESHOLD", "7"))
    min_words = 2000

    # 确定章节号
    if chapter_num == 0:
        all_chaps = find_chapter_files(chapters_dir)
        if not all_chaps:
            print("[错误] 还没有章节可评价", file=sys.stderr)
            sys.exit(1)
        chapter_num = max(num for num, _ in all_chaps) - 1
        if chapter_num < 1:
            print("[错误] 还没有章节可评价", file=sys.stderr)
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

    # --- 读取内容 ---
    with open(chapter_file, "r", encoding="utf-8") as f:
        chapter_content = f.read()
    word_count = len(re.findall(r"[\u4e00-\u9fff]", chapter_content))

    # 最近章节（连贯性参考）
    recent_chaps = []
    all_chaps = find_chapter_files(chapters_dir)
    other_chaps = [(n, fn) for n, fn in all_chaps if fn != chapter_fname]
    other_chaps.reverse()  # 从新到旧

    for i, (num, fname) in enumerate(other_chaps):
        fpath = os.path.join(chapters_dir, fname)
        read_len = 2000 if i < 3 else 500
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read(read_len)
        title = fname.replace(".md", "").split("_", 1)[1] if "_" in fname else fname
        marker = "[详细]" if i < 3 else "[摘要]"
        recent_chaps.append(f"{marker} {title}\n{content}\n---")
        if i >= 9:
            break

    # 大纲对应章节
    outline_snippet = ""
    if os.path.exists(outline_file):
        with open(outline_file, "r", encoding="utf-8") as f:
            outline_content = f.read()
        for m in re.finditer(
            r"([\u4e00-\u9fff].*?)（第(\d+)-(\d+)章）(.+?)(?=\n\n|\Z)",
            outline_content,
            re.DOTALL,
        ):
            title = m.group(1)
            start, end = int(m.group(2)), int(m.group(3))
            desc = m.group(4)
            if start <= chapter_num <= end:
                outline_snippet = f"{title}\n{desc.strip()}"
                break
        if not outline_snippet:
            outline_snippet = (
                "(未在大纲中找到精确匹配的章节区间)\n使用完整大纲供参考\n"
                + outline_content[:3000]
            )

    # 角色设定
    characters_content = ""
    if os.path.exists(characters_file):
        with open(characters_file, "r", encoding="utf-8") as f:
            characters_content = f.read()

    # --- 生成素材文件 ---
    os.makedirs(temp_dir, exist_ok=True)
    material_file = os.path.join(temp_dir, f".eval_material_{padded}.md")

    with open(material_file, "w", encoding="utf-8") as f:
        f.write("# 章节质量评价素材包\n\n")
        f.write(f"## 基本信息\n")
        f.write(f"- 章节号: 第{chapter_num}章\n")
        f.write(f"- 文件: {chapter_fname}\n")
        f.write(f"- 中文字数: {word_count} 字\n")
        f.write(f"- 达标要求: >= {min_words} 字\n")
        f.write(f"- 阈值: {threshold}/10\n\n")
        f.write(
            f"## 大纲要求（第{chapter_num}章应发生的事）\n---\n{outline_snippet}\n---\n\n"
        )
        f.write(f"## 角色设定\n---\n{characters_content}\n---\n\n")
        f.write(f"## 最近章节（连贯性参考）\n---\n{''.join(recent_chaps)}\n---\n\n")
        f.write(f"## 待评价章节内容\n---\n{chapter_content}\n---\n\n")
        f.write("## 评分维度\n")
        f.write("1. 大纲对齐度（权重30%）: 是否写了大纲要求的剧情？有无跑题？\n")
        f.write("2. 字数达标（权重15%）: 是否 >= 2000 字？\n")
        f.write("3. 人物一致性（权重20%）: 角色行为是否符合设定？有无OOC？\n")
        f.write("4. 开篇钩子（权重10%）: 前200字是否有冲突/悬念/反转？\n")
        f.write("5. 结尾钩子（权重10%）: 是否留了悬念？禁止模板化结尾。\n")
        f.write("6. 爽点密度（权重15%）: 是否有打脸/逆袭/装逼/反转？旁衬到位？\n\n")
        f.write("## 输出格式\n")
        f.write("评分: d1,d2,d3,d4,d5,d6\n")
        f.write("加权总分: X.X\n")
        f.write("改进建议: 具体问题和建议\n")

    print(f"[OK] 素材已生成: {material_file}")
    print(f"[OK] 章节: 第{chapter_num}章 ({word_count}字)")


if __name__ == "__main__":
    main()
