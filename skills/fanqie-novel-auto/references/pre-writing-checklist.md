# 写作前校验（强制步骤）

## 1. 确认大纲区间
读取 {outline_path}，确认当前章节号落在哪个分卷区间，该分卷的关键事件是什么。

## 2. 确认已有章节
列出 chapters/ 目录下已有的章节文件，确定下一章的编号。

## 3. 确认剧情走向
读取最近2章的实际内容，确认剧情走向是否与大纲一致。

## 4. 纠正偏差
如果大纲要求与已有章节不符，先纠正方向再继续写。

## 5. 本章写作
本章内容必须严格符合大纲中对应章节区间的关键事件。

## 6. 字数统计与标注
每章完成后，必须用Python统计中文字数并替换末尾的字数标注：
```python
import re
with open(path, 'r', encoding='utf-8') as f: content = f.read()
lines = [l for l in content.split('\n') if not l.startswith('【')]
chinese = len(re.findall(r'[\u4e00-\u9fff]', '\n'.join(lines)))
content = re.sub(r'【[^】]*字数[^】]*】', f'【本章字数：{chinese}字】', content)
```
**绝对禁止使用AI估算的字数标注**（如"约3000字"、"XXXX"等全是假的）。

## 7. 验证完成
检查最终标注是否正确、章节内容是否符合大纲。
