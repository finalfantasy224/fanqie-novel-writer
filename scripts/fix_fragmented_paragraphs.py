#!/usr/bin/env python3
"""
批量修复章节段落碎片化问题。
简单策略：逐行扫描，将相邻短句合并为正常段落（80-200中文字）。
保留场景分隔符（---）和结束标记不变。

用法:
    python3 scripts/fix_fragmented_paragraphs.py <book_dir>
    python3 scripts/fix_fragmented_paragraphs.py .          # 当前书目录
    python3 scripts/fix_fragmented_paragraphs.py           # 默认 novels/ 下所有书
"""
import os, re, glob, sys


def count_cn(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def fix_chapter(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题
    header_match = re.match(r'(#[^\n]+\n)', content)
    header = header_match.group(0) if header_match else ''
    body = content[len(header):] if header_match else content
    
    # 提取结尾标记
    marker_pattern = r'\*\*（第\d+章 完）\*\*$'
    has_marker = bool(re.search(marker_pattern, body))
    marker = None
    if has_marker:
        m = re.search(marker_pattern, body)
        marker = m.group(0)
        body = body[:m.start()].rstrip()
    
    # 按行处理
    lines = body.split('\n')
    
    PARA_MIN = 60   # 段落最小字数
    PARA_MAX = 200  # 段落最大字数
    
    result_blocks = []  # list of str or ('sep',) tuple
    current_lines = []
    current_cn = 0
    
    def flush():
        nonlocal current_lines, current_cn
        if current_lines:
            result_blocks.append(' '.join(current_lines))
            current_lines = []
            current_cn = 0
    
    for line in lines:
        stripped = line.strip()
        
        # 空行跳过
        if not stripped:
            continue
        
        # 场景分隔符
        if stripped == '---':
            flush()
            result_blocks.append(('sep',))
            continue
        
        # 结束标记
        if '**（第' in stripped and '章 完）**' in stripped:
            flush()
            result_blocks.append(stripped)
            continue
        
        line_cn = count_cn(stripped)
        if line_cn == 0:
            continue
        
        # 判断是否追加到当前段落
        if current_cn == 0:
            current_lines.append(stripped)
            current_cn = line_cn
        elif current_cn + line_cn <= PARA_MAX:
            current_lines.append(stripped)
            current_cn += line_cn
            # 达到最小长度后继续收集，直到超过MAX才flush
        else:
            # 超过最大长度，flush并开始新段
            flush()
            current_lines.append(stripped)
            current_cn = line_cn
    
    flush()
    
    # 重建正文
    parts = []
    for block in result_blocks:
        if isinstance(block, tuple):
            parts.append('---')
            parts.append('')
        else:
            parts.append(block)
            parts.append('')
    
    new_body = '\n'.join(parts).strip()
    
    # 重新添加结尾格式
    if marker:
        new_body = new_body.rstrip() + '\n\n---\n\n' + marker
    
    result = header + new_body
    
    # 验证
    total_cn = count_cn(result)
    all_paras = [p.strip() for p in result.split('\n\n') if len(p.strip()) > 10]
    short_count = sum(1 for p in all_paras if count_cn(p) < 30)
    para_count = len(all_paras)
    short_ratio = short_count / para_count * 100 if para_count else 0
    avg_len = total_cn / para_count if para_count else 0
    
    return result, total_cn, para_count, short_count, short_ratio, avg_len


def find_chapters(directory):
    """在指定目录下查找所有章节文件。"""
    chapters_dir = os.path.join(directory, "chapters")
    if not os.path.isdir(chapters_dir):
        return []
    return sorted(glob.glob(os.path.join(chapters_dir, "ch*.md")))


def process_book(book_dir):
    """处理一本书的所有章节。"""
    files = find_chapters(book_dir)
    if not files:
        print(f"  ⚠ 未找到章节文件: {book_dir}/chapters/")
        return 0
    
    fixed = 0
    print(f"\n=== {os.path.basename(book_dir)} ({len(files)} 章) ===\n")
    
    for filepath in files:
        bn = os.path.basename(filepath)
        
        result, cn, para_count, short_count, short_ratio, avg_len = fix_chapter(filepath)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result)
        
        status = "OK" if 2000 <= cn <= 3500 else "OVER/LOW"
        para_status = "✓" if short_ratio <= 40 else "⚠"
        fixed += 1
        
        print(f"  {bn}")
        print(f"    字数: {cn} [{status}]")
        print(f"    段落: {para_count} (短段{short_count}, 占比{short_ratio:.0f}%) 平均{avg_len:.0f}字 {para_status}")
    
    return fixed


def main():
    if len(sys.argv) > 2:
        print(f"用法: {sys.argv[0]} [<book_dir>]", file=sys.stderr)
        print(f"示例: python3 {sys.argv[0]} .")
        print(f"      python3 {sys.argv[0]} /path/to/novels")
        sys.exit(1)
    
    if len(sys.argv) == 2:
        target = sys.argv[1]
        if os.path.isdir(target):
            # 如果传入的是目录，检查是否是 novels 父目录（含多本书）
            sub_books = [d for d in os.listdir(target) if os.path.isdir(os.path.join(target, d))]
            if sub_books:
                total = 0
                for sub in sorted(sub_books):
                    total += process_book(os.path.join(target, sub))
                print(f"\n共处理 {total} 章")
                return
            else:
                # 单本书目录
                process_book(target)
                return
    
    # 默认：扫描 novels/ 下所有书
    novels_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'novels')
    if not os.path.isdir(novels_dir):
        print(f"[错误] 未找到 novels/ 目录: {novels_dir}", file=sys.stderr)
        sys.exit(1)
    
    books = [d for d in os.listdir(novels_dir) if os.path.isdir(os.path.join(novels_dir, d))]
    total = 0
    for book in sorted(books):
        total += process_book(os.path.join(novels_dir, book))
    print(f"\n共处理 {total} 章")


if __name__ == '__main__':
    main()
