# Engine vs Novel Data Separation

## 架构原则

将**通用引擎代码**（公开）与**私人创作数据**（私有）严格隔离：

```
fanqie-novel-writer/          ← Engine (公开, tracked in git)
├── references/prompts/    # Agent 提示词模板
├── scripts/               # 共享脚本
├── templates/             # 新建小说的模板
└── README.md

novels/                  ← Novel Data (私有, gitignored)
└── bookN_<slug>/
    ├── config.env       # 含 Cookie，绝不上 git
    ├── outline.md
    ├── characters.md
    └── chapters/
```

## 为什么要分离

1. **安全性**: `config.env` 包含番茄后台 Cookie，绝不能上传到 GitHub
2. **通用性**: 引擎代码是通用工具，可以分享给他人
3. **简洁性**: Git 仓库只包含代码，不包含几百章的小说内容

## 关键设计

- **相对路径**: 所有脚本通过 `cd` 到书目录后运行，不依赖绝对路径
- **CWD 感知**: `eval_material.py` 从 `$PWD`（当前工作目录）查找 `config.env`
- **模板化**: 新建小说用 `cp -r templates/ novels/bookN_newname/` 快速初始化

## .gitignore

```
# Novel data (private, not tracked in git)
novels/
```

## 迁移注意事项

当项目目录重命名（如 `books/` → `novels/`）或脚本位置变更时：
1. 引擎代码通常不需修改（因为是相对路径）
2. 需要更新: `.gitignore`、README、skill 文档、任何硬编码路径引用
3. 必须验证所有脚本在新结构下仍能正常运行
