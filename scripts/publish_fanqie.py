#!/usr/bin/env python3
"""番茄小说章节发布脚本

用法:
    cd /path/to/bookN && python3 scripts/publish_fanqie.py chapters/ch001_xxx.md

或:
    python3 scripts/publish_fanqie.py /path/to/chapters/ch001_xxx.md

从当前工作目录读取 config.env，支持多本书独立配置。
"""
import os
import sys
import time
import json
import logging
import urllib.parse
import urllib.request

# ===== 日志配置 =====
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, 'publish.log'), encoding='utf-8'),
    ]
)
log = logging.getLogger('publish_fanqie')


# ===== 工具函数 =====

def retry_with_backoff(func, max_retries=3, base_delay=2.0, label="请求"):
    """带指数退避的重试装饰器"""
    for attempt in range(1, max_retries + 1):
        try:
            result = func()
            if result is not None:
                return result
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                log.warning("%s 返回空结果，%ds 后重试 (%d/%d)", label, delay, attempt, max_retries)
                time.sleep(delay)
        except Exception as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                log.warning("%s 异常: %s，%ds 后重试 (%d/%d)", label, e, delay, attempt, max_retries)
                time.sleep(delay)
            else:
                log.error("%s 最终失败 (%d 次重试): %s", label, max_retries, e)
                raise
    return None


def http_post_json(url, data, headers, max_retries=3, label="请求"):
    """发送 POST 请求，带重试"""
    def _do_request():
        payload = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode('utf-8')
            result = json.loads(body)
            # 如果 code != 0 返回 None 触发重试
            if result.get('code') != 0:
                log.warning("%s 返回 code=%s: %s", label, result.get('code'), result.get('message', ''))
                return None
            return result
    return retry_with_backoff(_do_request, max_retries=max_retries, label=label)


def load_config():
    """从当前工作目录加载 config.env
    
    支持 symlink 调用时正确读取对应书的配置。
    """
    config = {}
    # 优先从当前工作目录读取（兼容 symlink 调用）
    config_path = os.path.join(os.getcwd(), 'config.env')
    if not os.path.exists(config_path):
        # 回退：从脚本所在目录的父目录查找
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.env')
    
    if not os.path.exists(config_path):
        log.error("未找到 config.env: %s", config_path)
        return config
    
    with open(config_path, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                log.warning("config.env 第%d行格式错误: %s", line_no, line[:50])
                continue
            key, value = line.split('=', 1)
            config[key.strip()] = value.strip().strip('"')
    
    log.info("已加载配置: BOOK_ID=%s, CURRENT_VOLUME_ID=%s, CURRENT_VOLUME_NAME=%s",
             config.get('BOOK_ID', ''), config.get('CURRENT_VOLUME_ID', ''), config.get('CURRENT_VOLUME_NAME', ''))
    return config


def resolve_volume(config, chapter_num):
    """根据章节号确定当前卷的 volume_id 和 volume_name
    
    从 config.env 的 VOLUMES 字段解析卷列表，按章节范围匹配。
    如果没有匹配的卷，回退到 CURRENT_VOLUME_ID/VOLUME_NAME。
    
    返回值: (volume_id, volume_name)
    """
    current_vid = config.get('CURRENT_VOLUME_ID', '')
    current_vname = config.get('CURRENT_VOLUME_NAME', '')
    
    volumes_str = config.get('VOLUMES', '')
    if not volumes_str:
        log.debug("未配置 VOLUMES，使用默认卷: %s", current_vname)
        return current_vid, current_vname
    
    # 解析卷列表: "1:id1:卷1名,31:id2:卷2名"
    volumes = []
    for entry in volumes_str.split(','):
        entry = entry.strip()
        if not entry or ':' not in entry:
            continue
        parts = entry.split(':', 2)
        if len(parts) != 3:
            continue
        try:
            start_ch = int(parts[0].lstrip('=').strip())
            vid = parts[1].strip()
            vname = parts[2].strip()
            volumes.append((start_ch, vid, vname))
        except ValueError:
            continue
    
    if not volumes:
        log.debug("VOLUMES 格式无效，使用默认卷: %s", current_vname)
        return current_vid, current_vname
    
    # 按起始章节排序，从大到小匹配
    volumes.sort(key=lambda x: x[0], reverse=True)
    
    for start_ch, vid, vname in volumes:
        if chapter_num >= start_ch:
            log.info("章节 #%d -> 匹配卷: %s (volume_id=%s)", chapter_num, vname, vid)
            return vid, vname
    
    # 都不匹配，用第一卷
    log.debug("章节 #%d 未匹配任何卷，使用默认卷: %s", chapter_num, current_vname)
    return current_vid, current_vname


def get_csrf_token(cookie, max_retries=3):
    """从 API 响应头获取 csrf_token"""
    def _do_request():
        url = 'https://fanqienovel.com/api/author/verify/check_user_status/v0?aid=2503&app_name=muye_novel'
        headers = {'Cookie': cookie, 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
            token = resp.headers.get('X-Secsdk-Csrf-Token', '')
            if token:
                return token
            return None
    token = retry_with_backoff(_do_request, max_retries=max_retries, label="获取CSRF Token")
    return token or ''


def parse_chapter_file(filepath):
    """解析章节文件，返回 (title, content_body, pure_text_paragraphs)"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:  # utf-8-sig 自动处理 BOM
        content = f.read()
    
    lines = content.split('\n')
    
    # 标题：第一个非空行，去掉 # 前缀
    title = ''
    first_content_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            title = stripped.lstrip('#').strip()
            first_content_start = i + 1
            break
    
    if not title:
        log.error("无法从文件提取标题: %s", filepath)
        return None, None, None
    
    # 正文：从第一个非空行之后的所有内容
    content_body = '\n'.join(lines[first_content_start:]).strip()
    
    # 提取纯文本段落
    paragraphs = []
    for line in content_body.split('\n'):
        line = line.strip()
        # 跳过元数据行
        if not line or line.startswith('---') or line.startswith('【本章') or line.startswith('【下一章'):
            continue
        # 跳过字数统计标记
        if line.startswith('【本章字数') or line.startswith('【字数统计'):
            continue
        paragraphs.append(line)
    
    # 合并连续空行为单个段落（防止多余空行）
    merged = []
    prev_empty = False
    for p in paragraphs:
        if not p:
            prev_empty = True
            continue
        merged.append(p)
        prev_empty = False
    
    return title, content_body, merged


def mark_published(chapter_file, item_id):
    """在章节文件头部添加发布标记"""
    with open(chapter_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    lines = content.split('\n')
    # 在文件开头插入发布标记
    published_line = f"# published: true | item_id: {item_id} | published_at: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    lines.insert(0, published_line)
    
    with open(chapter_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    log.info("已标记章节为已发布: %s", chapter_file)


def update_outline(title, char_count, chapter_num):
    """更新 outline.md 中的发布记录"""
    # 找 outline.md：先查当前目录，再查脚本父目录
    outline_path = 'outline.md'
    if not os.path.exists(outline_path):
        outline_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'outline.md')
    
    if not os.path.exists(outline_path):
        log.warning("未找到 outline.md，跳过大纲更新")
        return
    
    with open(outline_path, 'a', encoding='utf-8') as f:
        f.write(f"\n| {chapter_num} | {title} | {char_count} | 已发布 | {time.strftime('%Y-%m-%d %H:%M')} |\n")
    
    log.info("已更新大纲记录: 第%s章 %s", chapter_num, title)


# ===== API 调用 =====

def create_draft(book_id, volume_id, title, cookie, csrf_token):
    """创建章节草稿，返回 item_id"""
    url = f'https://fanqienovel.com/api/author/article/new_article/v0/?aid=2503&app_name=muye_novel&book_id={book_id}'
    
    def _do_request():
        data = {'aid': '2503', 'app_name': 'muye_novel', 'book_id': book_id, 'volume_id': volume_id, 'title': title}
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Cookie': cookie,
            'x-secsdk-csrf-token': csrf_token,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
            'Referer': 'https://fanqienovel.com/main/writer/chapter-manage/',
        }
        return http_post_json(url, data, headers, label="创建草稿")
    
    result = _do_request()
    if result and result.get('data', {}).get('item_id'):
        return result['data']['item_id']
    return None


def publish_chapter(book_id, item_id, volume_id, volume_name, title, html_content, cookie, csrf_token):
    """发布章节到草稿箱"""
    url = f'https://fanqienovel.com/api/author/article/cover_article/v0/?aid=2503&app_name=muye_novel&book_id={book_id}'
    
    def _do_request():
        data = {
            'aid': '2503', 'app_name': 'muye_novel',
            'book_id': book_id, 'item_id': item_id,
            'title': title, 'content': html_content,
            'volume_name': volume_name, 'volume_id': volume_id,
            'is_public': '1',
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Cookie': cookie,
            'x-secsdk-csrf-token': csrf_token,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
            'Referer': f'https://fanqienovel.com/main/writer/{book_id}/publish/{item_id}/?enter_from=modifydraft',
            'Origin': 'https://fanqienovel.com',
        }
        return http_post_json(url, data, headers, label="发布章节")
    
    result = _do_request()
    return result


def confirm_publish(book_id, item_id, volume_id, volume_name, html_content, cookie, csrf_token):
    """确认发布章节（正式发表）"""
    url = f'https://fanqienovel.com/api/author/publish_article/v0/?aid=2503&app_name=muye_novel&book_id={book_id}'
    
    def _do_request():
        data = {
            'aid': '2503', 'app_name': 'muye_novel',
            'item_id': item_id, 'book_id': book_id,
            'content': html_content,
            'timer_status': '0', 'need_pay': '0',
            'volume_name': volume_name, 'volume_id': volume_id,
            'timer_time': '', 'publish_status': '1',
            'device_platform': 'pc', 'speak_type': '0',
            'use_ai': '2', 'timer_chapter_preview': '[]',
            'has_chapter_ad': 'false', 'chapter_ad_types': '',
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Cookie': cookie,
            'x-secsdk-csrf-token': csrf_token,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
            'Referer': f'https://fanqienovel.com/main/writer/{book_id}/publish/{item_id}/?enter_from=modifydraft',
            'Origin': 'https://fanqienovel.com',
        }
        return http_post_json(url, data, headers, label="确认发布")
    
    result = _do_request()
    return result


# ===== 主流程 =====

def main():
    if len(sys.argv) < 2:
        print("用法: python publish_fanqie.py <章节文件路径>")
        print("示例: cd /path/to/book1 && python3 scripts/publish_fanqie.py chapters/ch001_xxx.md")
        sys.exit(1)
    
    chapter_file = os.path.abspath(sys.argv[1])
    if not os.path.exists(chapter_file):
        log.error("章节文件不存在: %s", chapter_file)
        sys.exit(1)
    
    log.info("=" * 60)
    log.info("开始发布章节: %s", os.path.basename(chapter_file))
    log.info("=" * 60)
    
    # 0. 解析章节文件
    title, content_body, paragraphs = parse_chapter_file(chapter_file)
    if not title:
        log.error("章节文件解析失败")
        sys.exit(1)
    
    html_content = '<p>' + '</p><p>'.join(paragraphs) + '</p>'
    char_count = len(content_body)
    log.info("标题: %s | 字数: %d | 段落数: %d", title, char_count, len(paragraphs))
    
    # 1. 加载配置
    config = load_config()
    cookie = config.get('TOMATO_COOKIE', '')
    book_id = config.get('BOOK_ID', '')
    
    if not cookie or not book_id:
        log.error("配置不完整: BOOK_ID=%s, COOKIE=%s", book_id, 'yes' if cookie else 'no')
        sys.exit(1)
    
    # 2. 获取 CSRF Token
    log.info("[准备] 获取 CSRF Token...")
    csrf_token = get_csrf_token(cookie)
    if not csrf_token:
        log.warning("未能自动获取 CSRF Token，尝试使用默认值...")
        csrf_token = '000100000001c2536c2e208675b8e7d915b2fe564eb8f8072ac8f62e7ea2f4a2d6f1f1f2aeb218be2fba13cb58e0'
    log.info("CSRF Token: %s...", csrf_token[:20])
    
    # 3. 从文件名解析章节号，用于卷切换
    # 格式: chNNN_第X章 标题.md
    basename = os.path.basename(chapter_file)
    ch_prefix = basename.split('_')[0]
    chapter_num = int(ch_prefix.lstrip('ch').lstrip('Ch').lstrip('CH'))
    
    # 4. 根据章节号自动选择卷
    volume_id, volume_name = resolve_volume(config, chapter_num)
    if not volume_id:
        log.error("未找到有效的 volume_id，请检查 config.env 中的 CURRENT_VOLUME_ID")
        sys.exit(1)
    log.info("使用卷: %s (volume_id=%s)", volume_name, volume_id)
    
    # 5. 创建草稿
    log.info("\n[1/4] 创建章节草稿...")
    item_id = create_draft(book_id, volume_id, title, cookie, csrf_token)
    if not item_id:
        log.error("创建草稿失败，终止发布")
        sys.exit(1)
    log.info("草稿创建成功，item_id: %s", item_id)
    
    # 6. 发布章节（存草稿）
    log.info("\n[2/4] 发布章节到草稿箱...")
    result = publish_chapter(book_id, item_id, volume_id, volume_name, title, html_content, cookie, csrf_token)
    if not result:
        log.error("发布到草稿箱失败，终止发布")
        sys.exit(1)
    log.info("草稿发布成功！")
    
    # 7. 确认发布（正式发表）
    log.info("\n[3/4] 确认发布（正式发表）...")
    result = confirm_publish(book_id, item_id, volume_id, volume_name, html_content, cookie, csrf_token)
    if not result:
        log.error("确认发布失败，章节仅保存在草稿箱")
        # 不退出，仍然标记和记录
    else:
        log.info("章节已正式发表！")
    
    # 8. 标记章节文件
    log.info("\n[4/4] 标记章节为已发布...")
    mark_published(chapter_file, item_id)
    
    # 9. 更新大纲
    update_outline(title, char_count, chapter_num)
    
    log.info("\n" + "=" * 60)
    log.info("发布完成！章节: %s (第%d章) | 卷: %s", title, chapter_num, volume_name)
    log.info("=" * 60)


if __name__ == '__main__':
    main()
