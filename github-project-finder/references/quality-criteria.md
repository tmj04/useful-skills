# 项目质量评估标准

本文档定义 GitHub 项目质量评估的详细标准和评分算法。

## 评分公式

```
总分 = Stars(25%) + 活跃度(20%) + 多源验证(15%)
     + 文档质量(15%) + 维护状态(15%) + 社区(10%)
     + 加分项
```

**满分：100 分 + 加分项（最高 20 分）**

---

## 评分维度详解

### 1. Star 数（25%，满分 25 分）

Star 数反映项目的受欢迎程度和社区认可度。

**评分方法：** 使用对数函数平滑处理

```
score = min(25, log10(stars + 1) * 10)
```

| Star 数 | 得分 | 等级 |
|---------|------|------|
| < 100 | 0-10 | 新兴项目 |
| 100-999 | 10-15 | 有一定关注 |
| 1,000-9,999 | 15-20 | 热门项目 |
| 10,000+ | 20-25 | 明星项目 |

### 2. 活跃度（20%，满分 20 分）

基于最后推送时间（pushed_at）评估项目活跃程度。

**评分方法：**

| 最后更新时间 | 得分 | 说明 |
|--------------|------|------|
| 1 个月内 | 20 | 非常活跃 |
| 1-3 个月 | 16 | 活跃 |
| 3-6 个月 | 12 | 较活跃 |
| 6-12 个月 | 8 | 一般 |
| 1-2 年 | 4 | 不活跃 |
| 2 年以上 | 0 | 可能已废弃 |

**计算公式：**

```python
days_since_update = (now - pushed_at).days

if days_since_update <= 30:
    score = 20
elif days_since_update <= 90:
    score = 16
elif days_since_update <= 180:
    score = 12
elif days_since_update <= 365:
    score = 8
elif days_since_update <= 730:
    score = 4
else:
    score = 0
```

### 3. 多源验证（15%，满分 15 分）

被多个搜索源发现的项目通常质量更高。

**评分方法：**

| 来源数量 | 得分 | 说明 |
|----------|------|------|
| 1 个来源 | 5 | 基础分 |
| 2 个来源 | 10 | 有交叉验证 |
| 3+ 个来源 | 15 | 高度认可 |

**来源类型：**
- GitHub API 搜索
- WebSearch（awesome 列表）
- WebSearch（博客推荐）
- GitHub Topics
- Sourcegraph

### 4. 文档质量（15%，满分 15 分）

良好的文档是项目可用性的重要指标。

**评估要素：**

| 要素 | 分值 | 检查方法 |
|------|------|----------|
| 有 README | 5 | 检查文件存在 |
| README 长度 > 500 字符 | 3 | 检查内容长度 |
| 有安装说明 | 2 | 搜索 "install" 关键词 |
| 有使用示例 | 3 | 搜索代码块 |
| 有文档站点 | 2 | 检查 homepage 字段 |

**简化评估（基于 API 数据）：**

```python
score = 0

# 有描述
if description and len(description) > 20:
    score += 5

# 有主页（通常是文档站点）
if homepage:
    score += 5

# 有 wiki
if has_wiki:
    score += 2

# 有 GitHub Pages
if has_pages:
    score += 3
```

### 5. 维护状态（15%，满分 15 分）

评估项目的维护质量和响应速度。

**评估要素：**

| 要素 | 分值 | 计算方法 |
|------|------|----------|
| Issues 响应率 | 10 | closed / (open + closed) |
| 有 CI/CD | 5 | 检查 Actions 或配置文件 |

**Issues 响应率评分：**

```python
if open_issues == 0:
    # 没有 issues 或全部已关闭
    score = 10
else:
    # 估算响应率（需要额外 API 调用获取 closed issues）
    # 简化方法：基于 open_issues 数量
    if open_issues < 10:
        score = 10
    elif open_issues < 50:
        score = 7
    elif open_issues < 200:
        score = 4
    else:
        score = 2
```

### 6. 社区活跃度（10%，满分 10 分）

评估项目的社区参与度。

**评估要素：**

| 要素 | 分值 | 说明 |
|------|------|------|
| Fork 数 | 5 | 反映项目被复用程度 |
| 贡献者数量 | 5 | 需要额外 API 调用 |

**Fork 数评分：**

```python
if forks >= 1000:
    score = 5
elif forks >= 100:
    score = 4
elif forks >= 50:
    score = 3
elif forks >= 10:
    score = 2
else:
    score = 1
```

---

## 加分项（最高 20 分）

| 加分项 | 分值 | 条件 |
|--------|------|------|
| 出现在 awesome 列表 | +5 | WebSearch 发现 |
| 有明确 LICENSE | +5 | license 字段非空 |
| 有 CI/CD 配置 | +3 | 检查 .github/workflows |
| 有完整文档站点 | +5 | homepage 指向文档 |
| 有 Discussions | +2 | has_discussions = true |

---

## 综合评分示例

### 示例项目：FastAPI

```
基础数据：
- Stars: 75,000
- 最后更新: 3 天前
- 来源: GitHub API + awesome-python + 博客推荐
- 有完整文档站点
- License: MIT
- Open Issues: 500
- Forks: 6,000

评分计算：
- Stars: log10(75000) * 10 = 48.75 → 25 (上限)
- 活跃度: 3天内更新 → 20
- 多源验证: 3个来源 → 15
- 文档质量: 有描述+有主页+有wiki → 12
- 维护状态: issues较多但活跃 → 8
- 社区: forks 6000 → 5

基础分: 25 + 20 + 15 + 12 + 8 + 5 = 85

加分项:
- awesome 列表: +5
- MIT License: +5
- 文档站点: +5

总分: 85 + 15 = 100
```

---

## 评分等级

| 总分 | 等级 | 推荐程度 |
|------|------|----------|
| 90+ | ⭐⭐⭐⭐⭐ | 强烈推荐 |
| 75-89 | ⭐⭐⭐⭐ | 推荐 |
| 60-74 | ⭐⭐⭐ | 可以考虑 |
| 45-59 | ⭐⭐ | 谨慎选择 |
| < 45 | ⭐ | 不推荐 |

---

## 快速评估方法

当无法获取完整数据时，使用简化评估：

```python
def quick_score(repo):
    """
    快速评估项目质量。

    参数:
        repo: 仓库信息字典

    返回:
        int: 评估分数（0-100）
    """
    score = 0

    # Stars (25%)
    stars = repo.get("stars", 0)
    score += min(25, math.log10(stars + 1) * 10)

    # 活跃度 (20%)
    pushed_at = repo.get("pushed_at", "")
    if pushed_at:
        days = (datetime.now() - parse_date(pushed_at)).days
        if days <= 30:
            score += 20
        elif days <= 90:
            score += 16
        elif days <= 180:
            score += 12
        elif days <= 365:
            score += 8

    # 文档 (15%)
    if repo.get("description"):
        score += 5
    if repo.get("homepage"):
        score += 10

    # 维护 (15%)
    open_issues = repo.get("open_issues", 0)
    if open_issues < 50:
        score += 15
    elif open_issues < 200:
        score += 10
    else:
        score += 5

    # 社区 (10%)
    forks = repo.get("forks", 0)
    score += min(10, forks / 100)

    # 加分项
    if repo.get("license"):
        score += 5

    return min(100, int(score))
```

---

## 注意事项

1. **数据时效性**：评分基于搜索时的数据，项目状态可能变化
2. **领域差异**：不同领域的项目 star 数差异较大，需要相对评估
3. **新项目**：新项目 star 数低但可能质量很高，需要综合判断
4. **维护模式**：有些项目进入"维护模式"，更新少但稳定可用
