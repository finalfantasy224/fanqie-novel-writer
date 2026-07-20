#!/usr/bin/env python3
"""检查章节内容是否与已写章节有重复段落。

用法:
    python3 scripts/check_repetition.py <book_dir> <CHAPTER_NUM>

输出:
    如果检测到重复 → 返回 exit code 1
    如果没有重复 → 返回 exit code 0

检测逻辑:
    - 将每章拆分为非空段落（按空行分隔）
    - 对每个段落，提取前80字作为指纹
    - 如果两个不同章节有相同指纹且正文≥50字连续相同 → 标记为重复
"""
import os
import re
import sys


def extract_paragraphs(content):
    """提取章节中的所有非空段落，返回 (段落文本, 段落长度) 列表。"""
    # 去掉标题行和结束标记
    lines = content.split('\n')
    clean_lines = []
    for line in lines:
        if line.startswith('# ') or line.strip() in ('---', '**（第' + ''.join([c for c in line.strip() if not c.isdigit()]) + '章 完）**'):
            continue
        if line.strip().startswith('**（第') and '章 完' in line:
            continue
        clean_lines.append(line)
    
    text = '\n'.join(clean_lines)
    # 按空行分割段落
    blocks = re.split(r'\n\s*\n', text.strip())
    paragraphs = []
    for block in blocks:
        block = block.strip()
        if len(block) >= 50:  # 只关心50字以上的段落
            paragraphs.append(block)
    return paragraphs


def find_repetitions(chapter_num, book_dir):
    """查找指定章节与之前章节的重复段落。"""
    chapters_dir = os.path.join(book_dir, 'chapters')
    if not os.path.exists(chapters_dir):
        print(f"[ERROR] 找不到目录: {chapters_dir}", file=sys.stderr)
        return False
    
    # 找到当前章节文件
    padded = f"{chapter_num:03d}"
    pattern = os.path.join(chapters_dir, f"ch{padded}_第{chapter_num}章*.md")
    import glob
    matches = glob.glob(pattern)
    if not matches:
        print(f"[ERROR] 找不到章节文件: ch{padded}_第{chapter_num}章*.md", file=sys.stderr)
        return False
    
    current_file = matches[0]
    with open(current_file, 'r', encoding='utf-8') as f:
        current_content = f.read()
    
    current_paras = extract_paragraphs(current_content)
    if not current_paras:
        print("[OK] 当前章节没有足够长的段落可检测", file=sys.stderr)
        return False
    
    # 遍历所有之前的章节
    all_files = sorted(glob.glob(os.path.join(chapters_dir, "ch*_第*章*.md")))
    found_duplicates = []
    
    for other_file in all_files:
        if other_file == current_file:
            continue
        
        with open(other_file, 'r', encoding='utf-8') as f:
            other_content = f.read()
        
        other_paras = extract_paragraphs(other_content)
        other_basename = os.path.basename(other_file)
        
        # 检查是否有完全相同的段落
        for cp in current_paras:
            for op in other_paras:
                # 精确匹配
                if cp == op:
                    found_duplicates.append((other_basename, cp[:80] + "..."))
                    break
                # 近似匹配（去除空白后比较）
                cp_norm = re.sub(r'\s+', '', cp)
                op_norm = re.sub(r'\s+', '', op)
                if cp_norm == op_norm and len(cp) >= 50:
                    found_duplicates.append((other_basename, cp[:80] + "..."))
                    break
    
    if found_duplicates:
        print("[FAIL] 检测到重复内容！\n", file=sys.stderr)
        for other_file, sample in found_duplicates:
            print(f"  与 {other_file} 重复:", file=sys.stderr)
            print(f"    \"{sample}\"", file=sys.stderr)
        print("\n建议：让 Rewriter Agent 重写本章，消除重复段落。", file=sys.stderr)
        return True
    else:
        print("[OK] 未检测到重复内容", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 3:
        print(f"用法: {sys.argv[0]} <book_dir> <CHAPTER_NUM>", file=sys.stderr)
        sys.exit(1)
    
    book_dir = sys.argv[1]
    chapter_num = int(sys.argv[2])
    
    has_duplicates = find_repetitions(chapter_num, book_dir)
    sys.exit(1 if has_duplicates else 0)


if __name__ == "__main__":
    main()
