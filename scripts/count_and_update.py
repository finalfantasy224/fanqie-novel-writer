#!/usr/bin/env python3
"""统计章节字数并自动更新文件中的【本章字数：XXX字】标记。

用法: python3 scripts/count_and_update.py <chapter_file.md>
      python3 scripts/count_and_update.py chapters/ch001_xxx.md

统计方式: re.findall(r'[\u4e00-\u9fff]', content)
排除以【开头的元数据行。
"""
import re
import sys


def count_and_update(filepath):
    """统计中文字符数，更新文件中的字数标记。"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # 排除元数据行后统计
    lines = [l for l in content.split('\n') if not l.startswith('【')]
    text = '\n'.join(lines)
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))

    # 替换字数标记（支持 XXX、旧数字等格式）
    new_marker = f'【本章字数：{chinese}字】'
    old_pattern = r'【[^】]*字数[^】]*】'
    new_content = re.sub(old_pattern, new_marker, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    print(f'{filepath}: {chinese} 字')
    return chinese


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 scripts/count_and_update.py <chapter_file>', file=sys.stderr)
        sys.exit(1)
    count_and_update(sys.argv[1])
