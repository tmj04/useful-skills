# Sourcegraph 使用指南

Sourcegraph 是一个强大的代码搜索引擎，支持跨仓库搜索代码。本指南介绍如何在 GitHub 项目搜索中使用 Sourcegraph。

## 概述

**Sourcegraph 的优势：**
- 跨仓库代码搜索
- 支持正则表达式
- 代码级别的精确匹配
- 无需克隆仓库即可搜索

**适用场景：**
- 验证项目代码质量
- 查找特定 API 用法
- 发现实现特定功能的项目
- 代码模式搜索

---

## 访问方式

### Web 界面

```
https://sourcegraph.com/search
```

### 搜索 URL 格式

```
https://sourcegraph.com/search?q={encoded_query}&patternType=regexp
```

---

## 搜索语法

### 基础搜索

```
# 简单关键词搜索
fastapi

# 精确短语
"async def"

# 正则表达式
def\s+\w+\(
```

### 仓库范围

```
# 指定仓库
repo:^github\.com/tiangolo/fastapi$

# 仓库模式匹配
repo:^github\.com/.*fastapi.*$

# 排除仓库
-repo:^github\.com/fork/.*$

# 多仓库
repo:^github\.com/(owner1|owner2)/.*$
```

### 语言筛选

```
# 单一语言
lang:python

# 多语言
lang:python OR lang:go

# 排除语言
-lang:markdown
```

### 文件路径

```
# 路径包含
file:src/

# 路径模式
file:.*_test\.py$

# 排除路径
-file:vendor/
-file:node_modules/
```

### 搜索类型

```
# 文件内容搜索（默认）
type:file pattern

# 符号搜索（函数、类、变量）
type:symbol ClassName

# 仅返回仓库
select:repo pattern

# 路径搜索
type:path pattern

# 提交搜索
type:commit pattern

# Diff 搜索
type:diff pattern
```

---

## 常用搜索模式

### 1. 查找函数定义

```
# Python 函数
lang:python type:symbol ^def\s+{function_name}

# JavaScript 函数
lang:javascript type:symbol function\s+{function_name}

# Go 函数
lang:go type:symbol func\s+{function_name}
```

### 2. 查找类定义

```
# Python 类
lang:python type:symbol ^class\s+{class_name}

# TypeScript 类
lang:typescript type:symbol class\s+{class_name}
```

### 3. 查找 API 用法

```
# requests 库用法
lang:python requests\.(get|post|put|delete)\(

# axios 用法
lang:javascript axios\.(get|post|put|delete)\(
```

### 4. 查找配置模式

```
# Docker Compose
file:docker-compose\.yml

# GitHub Actions
file:\.github/workflows/.*\.yml$

# pytest 配置
file:pytest\.ini OR file:pyproject\.toml \[tool\.pytest
```

### 5. 查找测试代码

```
# Python 测试
lang:python file:test_ def test_

# JavaScript 测试
lang:javascript file:\.test\. (describe|it|test)\(
```

---

## 项目发现策略

### 策略 1：按功能实现搜索

```
# 查找实现 WebSocket 的 Python 项目
lang:python websocket select:repo count:20

# 查找使用 FastAPI 的项目
lang:python "from fastapi import" select:repo count:20
```

### 策略 2：按代码模式搜索

```
# 查找实现 CLI 的项目
lang:python (argparse|click|typer) select:repo count:20

# 查找使用 async/await 的项目
lang:python "async def" select:repo count:20
```

### 策略 3：按项目结构搜索

```
# 查找有完整测试的项目
file:test_ lang:python select:repo count:20

# 查找有 CI 配置的项目
file:\.github/workflows/ select:repo count:20
```

---

## 代码质量验证

### 检查测试覆盖

```
# 检查项目是否有测试
repo:^github\.com/{owner}/{repo}$ file:test

# 检查测试文件数量
repo:^github\.com/{owner}/{repo}$ file:test_ type:path count:all
```

### 检查文档

```
# 检查 README
repo:^github\.com/{owner}/{repo}$ file:README

# 检查 docstring
repo:^github\.com/{owner}/{repo}$ lang:python """
```

### 检查代码风格

```
# 检查类型注解
repo:^github\.com/{owner}/{repo}$ lang:python def.*\(.*:.*\).*->

# 检查错误处理
repo:^github\.com/{owner}/{repo}$ lang:python try:.*except
```

---

## 搜索结果处理

### 提取仓库列表

使用 `select:repo` 获取仓库列表：

```
lang:python fastapi select:repo count:50
```

返回格式：
```
github.com/owner1/repo1
github.com/owner2/repo2
...
```

### 统计匹配数量

使用 `count:all` 获取匹配总数：

```
repo:^github\.com/{owner}/{repo}$ lang:python count:all
```

---

## 与其他搜索源配合

### 工作流程

```
1. GitHub API 搜索
   → 获取候选项目列表

2. Sourcegraph 验证
   → 检查代码质量
   → 验证功能实现
   → 评估测试覆盖

3. 综合评分
   → 结合 API 数据和代码分析
```

### 验证示例

```python
def verify_with_sourcegraph(owner: str, repo: str) -> dict:
    """
    使用 Sourcegraph 验证项目代码质量。

    参数:
        owner: 仓库所有者
        repo: 仓库名称

    返回:
        dict: 验证结果
    """
    checks = {
        "has_tests": f"repo:^github\\.com/{owner}/{repo}$ file:test",
        "has_ci": f"repo:^github\\.com/{owner}/{repo}$ file:\\.github/workflows/",
        "has_types": f"repo:^github\\.com/{owner}/{repo}$ lang:python def.*->",
    }

    results = {}
    for check_name, query in checks.items():
        # 执行 Sourcegraph 搜索
        # results[check_name] = search_sourcegraph(query)
        pass

    return results
```

---

## 限制和注意事项

### 限制

1. **索引延迟**：新仓库可能需要时间才能被索引
2. **私有仓库**：默认只搜索公开仓库
3. **大文件**：超大文件可能不被索引
4. **速率限制**：频繁搜索可能被限流

### 最佳实践

1. **精确查询**：使用具体的仓库范围减少搜索时间
2. **合理使用正则**：复杂正则可能影响性能
3. **结合其他源**：Sourcegraph 适合代码级验证，不适合发现新项目
4. **缓存结果**：对同一仓库的多次检查可以缓存

---

## 快速参考

### 常用查询模板

```
# 发现实现特定功能的项目
lang:{language} "{keyword}" select:repo count:20

# 验证项目有测试
repo:^github\.com/{owner}/{repo}$ file:test

# 检查代码风格
repo:^github\.com/{owner}/{repo}$ lang:{language} {pattern}

# 查找 API 用法示例
lang:{language} "{api_call}" -repo:official count:10
```

### 搜索修饰符速查

| 修饰符 | 说明 | 示例 |
|--------|------|------|
| `repo:` | 仓库范围 | `repo:^github\.com/.*$` |
| `lang:` | 语言筛选 | `lang:python` |
| `file:` | 文件路径 | `file:test_` |
| `type:` | 搜索类型 | `type:symbol` |
| `select:` | 结果类型 | `select:repo` |
| `count:` | 结果数量 | `count:20` |
| `-` | 排除 | `-file:vendor/` |
