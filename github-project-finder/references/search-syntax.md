# 多源搜索语法参考

本文档详细说明 GitHub 项目搜索 Skill 使用的各种搜索源的语法和用法。

## 1. GitHub API 搜索语法

### 基础 URL

```
https://api.github.com/search/repositories
```

### 查询参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `q` | 搜索查询字符串 | `q=web+framework` |
| `sort` | 排序字段 | `sort=stars` / `sort=forks` / `sort=updated` |
| `order` | 排序顺序 | `order=desc` / `order=asc` |
| `per_page` | 每页结果数 | `per_page=20`（最大 100） |
| `page` | 页码 | `page=1` |

### 查询语法

#### 关键词搜索

```bash
# 基础关键词搜索
q=machine+learning

# 多关键词（AND 关系）
q=web+framework+python

# 精确短语匹配
q="web framework"
```

#### 语言筛选

```bash
# 单一语言
q=cli+language:python

# 多语言（OR 关系）
q=cli+language:python+language:go
```

#### Star 数筛选

```bash
# 大于指定值
q=framework+stars:>1000

# 大于等于
q=framework+stars:>=1000

# 范围
q=framework+stars:100..1000

# 小于
q=framework+stars:<100
```

#### 时间筛选

```bash
# 最后推送时间
q=framework+pushed:>2024-01-01

# 创建时间
q=framework+created:>2023-01-01

# 时间范围
q=framework+pushed:2024-01-01..2024-06-01
```

#### Topic 筛选

```bash
# 单一 topic
q=topic:machine-learning

# 多 topic
q=topic:cli+topic:terminal
```

#### 其他筛选

```bash
# 按 fork 数
q=framework+forks:>100

# 按仓库大小（KB）
q=framework+size:>1000

# 是否有 README
q=framework+in:readme

# 在名称中搜索
q=framework+in:name

# 在描述中搜索
q=framework+in:description

# 按许可证
q=framework+license:mit

# 是否归档
q=framework+archived:false

# 是否为模板
q=framework+is:template
```

### 完整示例

```bash
# 搜索 Python Web 框架，star > 1000，6个月内有更新
curl -s "https://api.github.com/search/repositories?q=web+framework+language:python+stars:>1000+pushed:>2024-07-01&sort=stars&order=desc&per_page=20"

# 搜索 CLI 工具，按 topic
curl -s "https://api.github.com/search/repositories?q=topic:cli+topic:terminal+stars:>500&sort=stars&per_page=20"
```

### 限流说明

- 无 Token：60 次/小时
- 有 Token：30 次/分钟（搜索 API 特殊限制）
- 检查限流：查看响应头 `X-RateLimit-Remaining`

---

## 2. WebSearch 搜索模式

### Awesome 列表发现

```
# 标准 awesome 列表
awesome-{keyword} github

# 示例
awesome-python github
awesome-react github
awesome-cli-apps github
```

### 年度推荐

```
# 年度最佳
best {keyword} libraries 2024

# 示例
best python web frameworks 2024
best react state management 2024
```

### 技术博客搜索

```
# Dev.to
site:dev.to {keyword} best libraries

# Medium
site:medium.com {keyword} recommendations

# Hacker News
site:news.ycombinator.com {keyword} library

# Reddit
site:reddit.com {keyword} best library
```

### 对比文章

```
# 对比搜索
{keyword} vs comparison github

# 示例
fastapi vs flask comparison 2024
react vs vue comparison 2024
```

### 组合搜索

```
# 综合搜索
"{keyword}" "github" "stars" best 2024

# 示例
"python orm" "github" "stars" best 2024
```

---

## 3. GitHub Topics 搜索

### 浏览 Topics 页面

```
https://github.com/topics/{topic-name}
```

### 通过 API 搜索 Topics

```bash
# 搜索带有特定 topic 的仓库
curl -s "https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&per_page=20"

# 多 topic 组合
curl -s "https://api.github.com/search/repositories?q=topic:python+topic:cli&sort=stars"
```

### 常用 Topics

| 领域 | 常用 Topics |
|------|-------------|
| Web 开发 | `web`, `frontend`, `backend`, `api`, `rest-api` |
| CLI 工具 | `cli`, `terminal`, `command-line`, `shell` |
| 机器学习 | `machine-learning`, `deep-learning`, `ai`, `neural-network` |
| 数据处理 | `data-science`, `data-analysis`, `pandas`, `numpy` |
| DevOps | `docker`, `kubernetes`, `ci-cd`, `devops` |
| 数据库 | `database`, `sql`, `nosql`, `orm` |

---

## 4. Sourcegraph 搜索语法

### 基础语法

```
# 仓库范围搜索
repo:^github\.com/owner/repo$ {pattern}

# 跨仓库搜索
repo:^github\.com/.*$ {pattern}

# 语言筛选
lang:python {pattern}
```

### 搜索类型

```
# 文件搜索
type:file {pattern}

# 符号搜索（函数、类等）
type:symbol {pattern}

# 仅返回仓库列表
select:repo {pattern}

# 路径搜索
type:path {pattern}
```

### 正则表达式

```
# 函数定义
def\s+{function_name}

# 类定义
class\s+{class_name}

# 导入语句
import\s+{module}
```

### 组合查询

```
# Python 中的 async 函数
repo:^github\.com/.*$ lang:python async def

# 特定仓库中的测试文件
repo:^github\.com/owner/repo$ type:path test

# 查找特定 API 用法
repo:^github\.com/.*$ lang:python requests.get
```

### Sourcegraph 搜索 URL

```
https://sourcegraph.com/search?q={encoded_query}
```

---

## 5. 搜索策略组合

### 综合发现策略

```
第一步：GitHub API 关键词搜索
  → 获取 star 排序的前 20 个项目

第二步：WebSearch 发现
  → 搜索 awesome 列表
  → 搜索技术博客推荐

第三步：Topics 扩展
  → 从第一步结果中提取 topics
  → 搜索相关 topics 下的热门项目

第四步：结果整合
  → 按 owner/repo 去重
  → 记录每个项目的来源数量
```

### 特定场景策略

| 场景 | 推荐策略 |
|------|----------|
| 找热门框架 | GitHub API (stars 排序) + awesome 列表 |
| 找最佳实践 | WebSearch (博客) + Sourcegraph (代码) |
| 找替代方案 | WebSearch (对比文章) + Topics (相关项目) |
| 技术调研 | 全部搜索源并行 |

---

## 6. 常见问题

### Q: 如何处理 API 限流？

1. 检查 `X-RateLimit-Remaining` 响应头
2. 限流时切换到 WebSearch
3. 等待限流重置（查看 `X-RateLimit-Reset`）

### Q: 搜索结果太少怎么办？

1. 放宽 star 要求
2. 尝试相关关键词
3. 使用 WebSearch 发现 awesome 列表
4. 扩展 topics 搜索

### Q: 如何提高搜索精度？

1. 使用精确短语匹配 `"exact phrase"`
2. 组合多个筛选条件
3. 使用 `in:name` 或 `in:description` 限定搜索范围
