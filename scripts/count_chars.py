#!/usr/bin/env python3
"""Count Chinese characters in a chapter file.

Usage: python3 scripts/count_chars.py <chapter_file.md>
"""
import re
import sys

def count_chinese_chars(filepath):
    content = open(filepath).read()
    chars = re.findall(r'[\u4e00-\u9fff]', content)
    print(f'中文字符数: {len(chars)}')
    return len(chars)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 scripts/count_chars.py <chapter_file>')
        sys.exit(1)
    count_chinese_chars(sys.argv[1])
