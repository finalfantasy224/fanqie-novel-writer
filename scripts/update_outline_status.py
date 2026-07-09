#!/usr/bin/env python3
"""
更新 outline.md 中指定章节的状态标记。
用法: python3 scripts/update_outline_status.py <chapter_num> <book_dir>

功能：
- 查找 outline.md 中对应章节的行
- 将状态从 ⏳待写 更新为 ✅已完成
- 如果该行没有状态标记，自动添加 ✅已完成
- 同时更新表格行的状态列
"""
import sys
import os
import re

def main():
    if len(sys.argv) < 3:
        print(f"用法: {sys.argv[0]} <chapter_num> <book_dir>", file=sys.stderr)
        sys.exit(1)
    
    chapter_num = int(sys.argv[1])
    book_dir = sys.argv[2]
    outline_path = os.path.join(book_dir, 'outline.md')
    
    if not os.path.exists(outline_path):
        print(f"错误: 找不到 {outline_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(outline_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配两种格式：
    # 1. Markdown 表格行: | 第N章 | 标题 | 描述 | ⏳待写 |
    # 2. 大纲标题行: ### 第N章 标题 或 ## 第N章 标题
    
    updated = False
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # 匹配表格行：| 第N章 | ... | （加 (?!\d) 防止匹配第10章等）
        table_match = re.match(r'^\|\s*第\s*' + str(chapter_num) + r'\s*章(?!\d)\s*\|', line)
        if table_match:
            # 检查是否已有状态标记
            if '✅' in line or '已完成' in line:
                new_lines.append(line)  # 已更新，跳过
            elif '⏳' in line or '待写' in line:
                # 替换状态标记
                new_line = re.sub(r'⏳待写', '✅已完成', line)
                new_line = re.sub(r'待写$', '✅已完成', new_line)
                new_lines.append(new_line)
                updated = True
                print(f"[OK] 已更新 outline 状态: 第{chapter_num}章 → ✅已完成", file=sys.stderr)
            else:
                # 没有状态标记，添加
                new_lines.append(line.rstrip() + ' | ✅已完成 |')
                updated = True
                print(f"[OK] 已添加状态标记: 第{chapter_num}章 → ✅已完成", file=sys.stderr)
            continue
        
        # 匹配大纲标题行: ### 第N章 标题 或 ## 第N章 标题
        heading_match = re.match(r'^(#{2,3})\s*第\s*' + str(chapter_num) + r'\s*章\s+', line)
        if heading_match:
            # 检查后面是否已有状态标记
            if '✅' in line or '已完成' in line:
                new_lines.append(line)
            else:
                new_lines.append(line.rstrip() + ' ✅')
                updated = True
                print(f"[OK] 已添加状态标记: 第{chapter_num}章 → ✅已完成", file=sys.stderr)
            continue
        
        new_lines.append(line)
    
    if updated:
        with open(outline_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
    else:
        print(f"[WARN] 未在 outline 中找到第{chapter_num}章的记录", file=sys.stderr)
        print(f"  请确认章节号是否正确，或 outline 格式是否匹配", file=sys.stderr)

if __name__ == '__main__':
    main()
