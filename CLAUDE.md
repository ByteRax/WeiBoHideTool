# WeiBoHideTool - 项目指引

## 项目概述

微博批量操作 CLI 工具，使用 Python 开发。主要功能是将微博批量设置为仅自己可见。

## 技术栈

- **语言**: Python 3.10+
- **依赖**: requests
- **运行方式**: CLI 交互式

## 目录结构

```
WeiBoHideTool/
├── weibo_tool.py      # 主程序（单文件结构）
├── requirements.txt   # 依赖声明
├── README.md          # 使用说明
└── CLAUDE.md          # 本文件
```

## 核心功能

### API 接口

- `https://weibo.com/ajax/statuses/mymblog` - 获取微博列表
- `https://weibo.com/ajax/statuses/modifyVisible` - 修改可见性

### 代码结构

1. **配置**: UID、Cookie、线程数、请求间隔
2. **获取微博**: `fetch_page()`, `get_weibo_stats()`
3. **修改可见性**: `set_private()`, `batch_set_private()`
4. **多线程**: `ThreadPoolExecutor`, `ThreadSafeCounter`

## 开发规范

- 使用 Python 3.10+ 语法
- 保持单文件结构（适合简单 CLI 工具）
- 函数按功能分组，用注释分隔
- 使用 docstring 注释函数

## 配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| SLEEP | 请求间隔（秒） | 1.5 |
| THREADS | 并发线程数 | 5 |

## 常见任务

### 调整请求频率

修改 `SLEEP` 常量控制请求间隔。

### 调整并发数

修改 `THREADS` 常量控制并发线程数。
