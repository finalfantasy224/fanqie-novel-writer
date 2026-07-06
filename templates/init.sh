#!/usr/bin/env bash
# ============================================================
# 新书初始化脚本
# 用法: bash templates/init.sh <书名> <类型> <主角名> <主角性别>
# 示例: bash templates/init.sh "我的修仙家族" "仙侠家族" "李玄" "男"
# ============================================================

set -euo pipefail

BOOK_SLUG="${1:?用法: bash templates/init.sh <书名> <类型> <主角名> <主角性别>}"
BOOK_TYPE="${2:?}"
PROTAGONIST_NAME="${3:?}"
PROTAGONIST_SEX="${4:?}"

# Generate slug (lowercase + hyphens, replace non-alphanumeric with hyphen)
SLUG=$(echo "$BOOK_SLUG" | sed 's/[[:space:]]/-/g' | sed 's/[^a-zA-Z0-9\u4e00-\u9fff]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
BOOK_DIR="novels/${BOOK_SLUG}_${SLUG}"

echo "============================================"
echo "  新书初始化"
echo "  书名: $BOOK_SLUG"
echo "  类型: $BOOK_TYPE"
echo "  主角: $PROTAGONIST_NAME ($PROTAGONIST_SEX)"
echo "  目录: $BOOK_DIR/"
echo "============================================"

# 创建目录结构
mkdir -p "$BOOK_DIR/chapters"
mkdir -p "$BOOK_DIR/scripts"

# 创建 config.env
cat > "$BOOK_DIR/config.env" << EOF
NOVEL_TITLE="$BOOK_SLUG"
GENRE="$BOOK_TYPE"
PROTAGONIST_NAME="$PROTAGONIST_NAME"
PROTAGONIST_SEX="$PROTAGONIST_SEX"
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
EOF

# 创建空 outline 框架
cat > "$BOOK_DIR/outline.md" << EOF
# 大纲 - $BOOK_SLUG

## 书名
$BOOK_SLUG

## 一句话简介
（待填写：用一句话概括全书核心看点）

## 核心设定

### 世界观
（待填写：修炼体系、势力分布、资源体系等）

### 主角人设
- 姓名：$PROTAGONIST_NAME
- 性别：$PROTAGONIST_SEX
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
EOF

# 创建空 characters 框架
cat > "$BOOK_DIR/characters.md" << EOF
# 角色设定 - $BOOK_SLUG

## 主角
- 姓名：$PROTAGONIST_NAME
- 性别：$PROTAGONIST_SEX
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
EOF

# 创建 scripts 目录下的脚本（symlink 到公共脚本）
# 注意：这里不创建 symlink，因为 novles/ 是 gitignored
# 用户需要手动从根目录 scripts/ 复制或使用绝对路径

echo ""
echo "============================================"
echo "  初始化完成！"
echo "  下一步："
echo "  1. 用 AI 帮忙完善 outline.md 和 characters.md"
echo "  2. 填写 config.env 中的 TOMATO_COOKIE 和 BOOK_ID"
echo "  3. 开始写作！"
echo "============================================"
