#!/usr/bin/env python3
"""批量修复所有章节末尾的字数标注为Python统计的真实数字。

用法:
  python3 fix_word_counts.py                          # 扫描所有书
  python3 fix_word_counts.py --fix                    # 修复所有书
  python3 fix_word_counts.py --fix --book book3_xxx   # 只修复指定书

注意: 统计排除以【开头的元数据行，只统计中文字符(u4e00-u9fff)。
"""

import argparse
import glob
import os
import re
import sys


def count_chinese_chars(content: str) -> int:
    """统计中文字符数（排除元数据行）。"""
    lines = [l for l in content.split('\n') if not l.startswith('【')]
    text = '\n'.join(lines)
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def scan_book(chapters_dir: str) -> list:
    """扫描一书的章节，返回字数统计列表。"""
    results = []
    if not os.path.isdir(chapters_dir):
        return results
    
    for f in sorted(os.listdir(chapters_dir)):
        if not f.endswith('.md'):
            continue
        path = os.path.join(chapters_dir, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        chinese = count_chinese_chars(content)
        
        # 检查是否有字数标注
        has_wc = any('字数' in line and '【' in line for line in content.split('\n'))
        
        # 检查格式是否统一
        formatted_correctly = False
        for line in content.split('\n'):
            stripped = line.strip()
            if '字数' in stripped and '【' in stripped:
                if re.match(r'^【本章字数：\d+字】$', stripped):
                    formatted_correctly = True
        
        status = "OK" if chinese >= 6000 else ("WARN" if chinese >= 3000 else "LOW")
        flag = "" if formatted_correctly else " ✗格式不统一"
        results.append({
            'file': f,
            'path': path,
            'chinese': chinese,
            'status': status,
            'has_wc': has_wc,
            'formatted': formatted_correctly,
            'flag': flag,
        })
    
    return results


def fix_book(chapters_dir: str) -> int:
    """修复一书的字数标注，返回修复数量。"""
    fixed = 0
    if not os.path.isdir(chapters_dir):
        return 0
    
    for f in sorted(os.listdir(chapters_dir)):
        if not f.endswith('.md'):
            continue
        path = os.path.join(chapters_dir, f)
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
        
        chinese = count_chinese_chars(content)
        new_marker = f'【本章字数：{chinese}字】'
        
        # 替换所有字数标注行
        old_pattern = r'【[^】]*字数[^】]*】'
        new_content = re.sub(old_pattern, new_marker, content)
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(new_content)
            fixed += 1
    
    return fixed


def main():
    parser = argparse.ArgumentParser(description='批量修复小说章节字数标注')
    parser.add_argument('--fix', action='store_true', help='执行修复而非仅扫描')
    parser.add_argument('--book', type=str, default=None, help='只处理指定书目录')
    args = parser.parse_args()
    
    base = "/home/ka/桌面/fanqie-novel/books/"
    book_dirs = sorted(glob.glob(os.path.join(base, "book*")))
    
    if args.book:
        book_dirs = [d for d in book_dirs if os.path.basename(d) == args.book]
    
    total_chapters = 0
    total_fixed = 0
    
    for book_dir in book_dirs:
        name = os.path.basename(book_dir)
        chapters_dir = os.path.join(book_dir, "chapters")
        results = scan_book(chapters_dir)
        
        if not results:
            continue
        
        ok = sum(1 for r in results if r['status'] == 'OK')
        warn = sum(1 for r in results if r['status'] == 'WARN')
        low = sum(1 for r in results if r['status'] == 'LOW')
        bad_format = sum(1 for r in results if not r['formatted'])
        
        print(f"\n{'='*60}")
        print(f"  {name} ({len(results)} 章)")
        print(f"  OK(≥6000): {ok}  WARN(3000-5999): {warn}  LOW(<3000): {low}")
        if bad_format > 0:
            print(f"  ⚠️ 格式不统一: {bad_format} 章")
            for r in results:
                if not r['formatted']:
                    print(f"    {r['file']}: {r['chinese']}字")
        
        if args.fix and bad_format > 0:
            fixed = fix_book(chapters_dir)
            if fixed > 0:
                print(f"  ✅ 已修复 {fixed} 章")
                total_fixed += fixed
        
        total_chapters += len(results)
    
    print(f"\n{'='*60}")
    print(f"  总计: {total_chapters} 章, 修复 {total_fixed} 章")


if __name__ == '__main__':
    main()
