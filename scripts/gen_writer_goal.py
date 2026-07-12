#!/usr/bin/env python3
"""
生成 delegate_task 的 goal 参数模板。
从 config.env 读取所有配置，动态生成写作指令。
用法: python3 scripts/gen_writer_goal.py <book_dir> <chapter_num> [prev_chapter_content]
输出: 打印 goal 内容到 stdout，同时保存到 .writer_goal.md

字数统计：
- 从 config.env 读取 MIN_WORDS/MAX_WORDS/CHAPTER_WORDS_TARGET
- 在 goal 中明确字数范围，避免硬编码
- 强制使用 Python 正则统计，禁止 AI 估算
"""
import sys
import os
import re


def load_config(config_path):
    config = {}
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip().strip('"')
            config[key] = val
    return config


def main():
    if len(sys.argv) < 3:
        print(f"用法: {sys.argv[0]} <book_dir> <chapter_num>", file=sys.stderr)
        sys.exit(1)

    book_dir = sys.argv[1]
    chapter_num = int(sys.argv[2])
    config_path = os.path.join(book_dir, 'config.env')

    if not os.path.exists(config_path):
        print(f"错误: 找不到 {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)

    novel_title = config.get('NOVEL_TITLE', '未命名小说')
    protagonist = config.get('PROTAGONIST_NAME', '主角')
    genre = config.get('GENRE', '')
    min_words = int(config.get('MIN_WORDS', '2000'))
    max_words = int(config.get('MAX_WORDS', '3500'))
    target_words = int(config.get('CHAPTER_WORDS_TARGET', '2500'))
    eval_threshold = int(config.get('EVAL_THRESHOLD', '7'))
    eval_max_retries = int(config.get('EVAL_MAX_RETRIES', '2'))

    padded = f"{chapter_num:03d}"

    # Build goal template
    goal_lines = [
        f"撰写《{novel_title}》第{chapter_num}章。",
        "",
        "## 文件保存",
        f"保存到: {book_dir}/chapters/",
        f"文件名格式: ch{padded}_第{chapter_num}章 {{标题}}.md",
        f"其中 padded = {padded}（三位数补零）",
        "",
        "## 字数要求（从 config.env 读取）",
        f"- 目标字数: {target_words} 字",
        f"- 允许范围: {min_words}-{max_words} 字",
        "- 这是硬性要求，写完后必须用 Python 统计真实字数",
        "- 严禁使用 AI 估算的字数（偏差可达 50%+）",
        "",
        "## 写作要求",
        "- 风格：快节奏、强冲突、爽点密集",
        "- 语言：简体中文，口语化，适合移动端阅读",
        "- 开篇钩子：前200字必须有冲突/悬念/反转",
        "- 每段不超过3行，方便手机阅读",
        "- 直接输出纯文本，段落之间空一行。不要用<p>标签，不要用markdown代码块。",
        "- 禁止概括式叙述，每个事件必须展开为具体场景——有对话、有动作、有心理描写、有旁人反应",
        "- 结尾要留钩子，与下一章直接相关",
        "",
        "## 输出格式",
        f"# 第{chapter_num}章 {{标题}}",
        "",
        "（正文内容）",
        "",
        "**注意：章节文件末尾不写字数标注或下一章预告。** 字数由流水线脚本验证。",
    ]
    goal = "\n".join(goal_lines) + "\n"

    # Output to file
    output_file = os.path.join(book_dir, '.temp', '.writer_goal.md')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(goal)

    # Also print to stdout
    print(goal)
    print(f"\n[OK] 已保存到: {output_file}", file=sys.stderr)
    print(f"     书名: {novel_title}", file=sys.stderr)
    print(f"     字数: {min_words}-{max_words} (目标 {target_words})", file=sys.stderr)


if __name__ == '__main__':
    main()
