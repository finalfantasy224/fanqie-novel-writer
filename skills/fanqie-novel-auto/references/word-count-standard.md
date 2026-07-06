# 番茄平台标准字数

## 单章字数标准（2026-07-06确立）

**番茄热门小说单章标准字数为2000-2500字。** 这是由平台免费阅读+广告分成模式决定的：
- 章节不宜过长，方便广告插入
- 适合读者碎片化阅读（手机场景）
- 过长的章节（5000+字）阅读压力大，跳出率高

## 配置标准

```
MIN_WORDS=2000        # 低于此判定为太短
MAX_WORDS=3500        # 超过此判定为太长
CHAPTER_WORDS_TARGET=2500  # AI写作目标字数
```

## 历史数据

2026-07-06之前配置为 MIN_WORDS=6000, MAX_WORDS=12000, CHAPTER_WORDS_TARGET=8000。
实测book1（30章）平均5074字，book2（30章）平均6084字，全部超出新标准。
已完成的章节不会被自动修改。

## 多agent流程中的字数生效

### 关键陷阱：delegate_task 的 goal 参数必须动态读取 config.env

用 `delegate_task` 调用 Writer Agent 时，**字数要求不能硬编码在 goal 参数里**。

**错误做法**：
```
goal: "- 字数：6000字以上（硬性要求）"
```
（修改 config.env 对此无任何影响）

**正确做法**：
1. 从 config.env 读取 MIN_WORDS/MAX_WORDS/CHAPTER_WORDS_TARGET
2. 拼接到 goal 中：`"- 字数：2500字左右（目标范围 2000-3500）"`

### 辅助工具

每本书的 `scripts/gen_writer_goal.py <book_dir> <chapter_num>` 可从 config.env 自动生成写作模板，包含正确的字数要求，输出到 `.writer_goal_template.md`。

### 一致性检查

Writer Agent 的目标字数和 Evaluator Agent 的达标判断必须使用同一套标准。

## 字数统计准确性

- ✅ 正确：Python正则 `re.findall(r'[\u4e00-\u9fff]', content)` 统计纯中文字符
- ❌ 错误：`wc -c` 字节数（UTF-8下中文占3字节）
- ❌ 错误：AI自己估算（偏差可达50%+，曾有"约12500字"实际5819字的案例）

## 相关脚本更新

- write_chapter.sh: prompt中字数指令已更新
- evaluate_chapter.sh: 字数达标判断已更新
- config.env: 5本书统一更新
