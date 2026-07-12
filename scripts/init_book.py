#!/usr/bin/env python3
"""新书初始化脚本 — 跨平台（Python 3.11+）。

用法:
    python3 scripts/init_book.py <书名> <类型> <主角名> <主角性别>

示例:
    python3 scripts/init_book.py "我的修仙家族" "仙侠家族" "李玄" "男"

输出: 在 novels/<slug>/ 下创建完整目录结构
"""
import os
import re
import sys


def generate_slug(title):
    """生成 slug：小写 + 连字符，保留中文字符和英文数字。"""
    s = title.lower()
    # 保留 CJK 字符
    s = re.sub(r"[\u4e00-\u9fff]", lambda m: m.group(0), s)
    # 其他非字母数字替换为 -
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "-", s)
    # 合并多个连字符
    s = re.sub(r"-{2,}", "-", s)
    # 去掉首尾连字符
    s = s.strip("-")
    return s or "unnovel"


# --- 参数检查 ---
if len(sys.argv) != 5:
    print(
        f"用法: {sys.argv[0]} <书名> <类型> <主角名> <主角性别>", file=sys.stderr
    )
    print(f"示例: {sys.argv[0]} \"我的小说\" \"题材类型\" \"主角名\" \"男\"", file=sys.stderr)
    sys.exit(1)

book_title = sys.argv[1]
book_type = sys.argv[2]
protagonist_name = sys.argv[3]
protagonist_sex = sys.argv[4]

slug = generate_slug(book_title)
book_dir = os.path.join("novels", f"{book_title}_{slug}")

print("=" * 44)
print("  新书初始化")
print(f"  书名: {book_title}")
print(f"  类型: {book_type}")
print(f"  主角: {protagonist_name} ({protagonist_sex})")
print(f"  目录: {book_dir}/")
print("=" * 44)

# --- 创建目录结构 ---
os.makedirs(os.path.join(book_dir, "chapters"), exist_ok=True)
os.makedirs(os.path.join(book_dir, ".temp"), exist_ok=True)

# --- config.env ---
config_content = f"""NOVEL_TITLE="{book_title}"
GENRE="{book_type}"
PROTAGONIST_NAME="{protagonist_name}"
PROTAGONIST_SEX="{protagonist_sex}"
MIN_WORDS=2000
MAX_WORDS=3500
CHAPTER_WORDS_TARGET=2500
EVAL_THRESHOLD=7
EVAL_MAX_RETRIES=2
TOMATO_COOKIE=""
BOOK_ID=""
CURRENT_VOLUME_ID=""
CURRENT_VOLUME_NAME=""
VOLUMES=""
"""
with open(os.path.join(book_dir, "config.env"), "w", encoding="utf-8") as f:
    f.write(config_content)

# --- outline.md ---
outline_content = f"""# 大纲 - {book_title}

## 书名
{book_title}

## 一句话简介
（待填写：用一句话概括全书核心看点）

## 核心设定

### 世界观
（待填写：修炼体系、势力分布、资源体系等）

### 主角人设
- 姓名：{protagonist_name}
- 性别：{protagonist_sex}
- 年龄：
- 身份：
- 性格：
- 说话风格：
- 能力/金手指：
- 核心动机：
- 限制：
- 弱点：

### 主要配角
（待填写：每个角色的姓名、身份、性格、作用）

### 反派势力
（待填写：敌对势力、关键反派）

## 分卷大纲

### 第一卷（第1-30章）

#### 卷名
（待填写）

#### 一句话简介
（待填写）

#### 关键事件
- 第1章：（待填写）
- 第2章：（待填写）
- ...

## 章节记录表

| 章节号 | 标题 | 关键情节 | 状态 |
|--------|------|----------|------|
| 第1章 | （待填写） | （待填写） | ⏳待写 |
| 第2章 | （待填写） | （待填写） | ⏳待写 |
| ... | ... | ... | ... |
| 第30章 | （待填写） | （待填写） | ⏳待写 |
"""
with open(os.path.join(book_dir, "outline.md"), "w", encoding="utf-8") as f:
    f.write(outline_content)

# --- characters.md ---
characters_content = f"""# 角色设定 - {book_title}

## 主角
- 姓名：{protagonist_name}
- 性别：{protagonist_sex}
- 年龄：
- 身份：
- 性格：
- 说话风格：
- 能力/金手指：
- 核心动机：
- 限制：
- 弱点：

## 主要配角
（待填写）

## 反派势力
（待填写）
"""
with open(os.path.join(book_dir, "characters.md"), "w", encoding="utf-8") as f:
    f.write(characters_content)

# --- 完成提示 ---
print()
print("=" * 44)
print("  初始化完成！")
print("  下一步：")
print("  1. 用 AI 帮忙完善 outline.md 和 characters.md")
print("  2. 填写 config.env 中的 TOMATO_COOKIE 和 BOOK_ID")
print("  3. 开始写作！")
print("=" * 44)
