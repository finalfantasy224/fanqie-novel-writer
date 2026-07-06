# 多Agent Orchestrator 上下文优化指南

## 背景

在番茄小说自动化写作流程中，Writer Agent 需要足够的上下文来保持章节连贯性，但过多上下文会浪费大量 token。

## 优化前的问题

Writer Agent 自行读取所有章节文件（前6章×9KB≈54KB），导致：
- 大量 token 浪费在无关内容上
- Writer Agent 可能读取到过时或冲突的信息
- 每个章节独立生成，不需要历史全量上下文

## 优化后方案

Orchestrator 预先准备精简上下文，传入 delegate_task 的 goal/context：

| 内容 | 大小 | 用途 |
|------|------|------|
| 上一章完整内容 | ~9KB | 保持情节连贯 |
| 最近2章开头各200字 | ~400字 | 了解人物语气和近期事件 |
| outline.md 对应章节片段 | ~200字 | 本章剧情方向 |
| characters.md 前500字 | ~500字 | 角色关键设定 |
| **总计** | **~10KB** | 比原来节省80%+ |

## 实现方式

### writer-agent.md 模板关键指令

```markdown
### 上下文（严格限制，不要自行读取其他文件）
- **上一章完整内容**（见下方）— 保持情节连贯
- **最近2章摘要**（各200字）— 了解人物语气和近期事件
- 不要读取其他章节文件！只需要以上信息就够了
```

### orchestrator.md 中步骤2的说明

```markdown
### 步骤2：准备 Writer Agent 上下文（关键优化）
**不要**让 Writer Agent 自己读取所有章节文件。orchestrator 应该：
1. 读取上一章完整内容（ch{上一章号}.md）
2. 读取最近2章的开头各200字
3. 读取 outline.md 中对应章节的大纲片段
4. 读取 characters.md 的前500字
5. 将这些信息打包传入 delegate_task 的 goal/context 中
```

## 收益

- Token 节省：从 ~54KB 降到 ~10KB，节省 80%+
- 速度提升：上下文越小，Writer Agent 响应越快
- 质量稳定：只传必要信息，避免无关干扰
