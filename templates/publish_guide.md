# 番茄小说发布指南

## 发布前准备

1. 第一卷（30章）全部写完并通过评价（≥7分）
2. 更新 outline.md 中所有章节状态为 ✅已完成
3. 在番茄作者后台创建作品
4. 获取以下配置值（见下方详细说明）
5. 更新 novels/bookN/config.env

---

## 配置值获取方法

### 1. TOMATO_COOKIE

1. 浏览器打开 https://fanqienovel.com/main/writer/home 并登录
2. 按 F12 打开开发者工具
3. 点击 **Network** 标签
4. 刷新页面
5. 在请求列表中找到任意一个 `/api/author/` 开头的请求
6. 点击它，在右侧找到 **Request Headers**
7. 复制 `Cookie` 的完整值，粘贴到 config.env

### 2. BOOK_ID

1. 浏览器打开 https://fanqienovel.com/main/writer/home
2. 点击你的作品进入作品管理页
3. 查看浏览器地址栏 URL，格式类似：
   ```
   https://fanqienovel.com/main/writer/article/manage?bookId=1234567890
   ```
4. `bookId=` 后面的数字就是 BOOK_ID

### 3. CURRENT_VOLUME_ID（创建卷时获得）

1. 在作品管理页，点击"新建卷"
2. 输入卷名（如"第一卷：初入修仙界"）
3. 创建成功后，浏览器地址栏 URL 格式类似：
   ```
   https://fanqienovel.com/main/writer/article/chapter?itemId=9876543210&volumeId=1111111111
   ```
4. `volumeId=` 后面的数字就是 CURRENT_VOLUME_ID

### 4. CURRENT_VOLUME_NAME

就是你在后台创建的卷名，如"第一卷：初入修仙界"

### 5. VOLUMES（多卷配置，可选）

如果有多卷，格式为：
```
VOLUMES="1:卷1ID:第一卷,31:卷2ID:第二卷,61:卷3ID:第三卷"
```
含义：第1章起用卷1，第31章起用卷2，第61章起用卷3

---

## 发布步骤

### 方法一：逐章发布（推荐）

进入书目录，对每章执行：

```bash
cd novels/你的书名

# 发布第1章
python3 ../../scripts/publish_fanqie.py chapters/ch001_第1章*.md

# 发布第2章
python3 ../../scripts/publish_fanqie.py chapters/ch002_第2章*.md

# ... 以此类推
```

### 方法二：批量发布

```bash
cd novels/你的书名

for ch in chapters/ch???_第*.md; do
    echo "发布: $ch"
    python3 ../../scripts/publish_fanqie.py "$ch"
done
```

### 方法三：发布指定章节

如果只想发布某些章节（比如存稿30章后一次性发布前10章）：

```bash
cd novels/你的书名

# 只发布第1-10章
for i in $(seq -w 1 10); do
    python3 ../../scripts/publish_fanqie.py "chapters/ch${i}_第${i}章*.md"
done
```

---

## 发布流程说明

publish_fanqie.py 内部执行三步 API 调用：

1. **new_article** — 创建草稿，返回 item_id
2. **cover_article** — 存草稿（带 volume_id, volume_name）
3. **publish_article** — 确认发布

脚本会自动：
- 从 config.env 读取 Cookie 和 Book ID
- 根据章节号自动匹配卷（resolve_volume）
- 指数退避重试（3次）
- 记录日志到 logs/publish.log

---

## 常见问题

### Cookie 过期

番茄 Cookie 约1-2个月失效。重新获取：
1. 浏览器登录 https://fanqienovel.com/main/writer/home
2. F12 → Network → 任意请求
3. 复制 Cookie 值，更新 config.env

### 发布失败

检查：
1. config.env 中 BOOK_ID 和 TOMATO_COOKIE 是否正确
2. CURRENT_VOLUME_ID 是否已设置
3. 查看 logs/publish.log 的错误信息
4. 章节文件名是否符合 chNNN_第N章 标题.md 格式

### 多卷切换

在 config.env 中配置 VOLUMES：
```
VOLUMES="1:卷1ID:第一卷,31:卷2ID:第二卷"
```
脚本会根据章节号自动切换到对应卷。
