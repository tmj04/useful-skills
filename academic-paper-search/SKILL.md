---
name: academic-paper-search
description: >-
  搜索学术论文的工具，覆盖 arXiv、Semantic Scholar、OpenAlex、Papers With Code 等数据源。
  当用户要求搜索论文、查找文献、文献调研、找最新研究、论文推荐、学术搜索时使用。
  触发词：搜索论文、找论文、文献检索、文献调研、最新研究、论文推荐、paper search、find papers。
---

# 学术论文搜索

通过多个免费学术 API 并行搜索 CS/AI 领域论文，生成结构化 Markdown 报告。

## 工作流程

### 1. 理解用户查询
- 提取搜索关键词（英文效果最佳）
- 确定时间范围、领域过滤、排序方式
- 如果用户用中文描述，翻译为英文关键词搜索

### 2. 运行搜索脚本
```bash
PYTHONIOENCODING=utf-8 python "C:\Users\Administrator\.claude\skills\academic-paper-search\scripts\search_papers.py" \
  -q "<关键词>" -n <数量> \
  --sources arxiv,semantic_scholar,openalex,pwc \
  --sort <relevance|citations|date> \
  --date-from <YYYY-MM-DD> --date-to <YYYY-MM-DD> \
  --field <cs.AI,cs.CL,cs.LG>
```

**参数说明：**
- `-q`：搜索关键词（必需，英文）
- `-n`：每个数据源返回数量（默认 20）
- `--sources`：数据源，逗号分隔（默认全部：arxiv,semantic_scholar,openalex,pwc）
- `--sort`：排序（relevance 相关性 / citations 引用数 / date 日期）
- `--date-from/--date-to`：日期范围 YYYY-MM-DD
- `--field`：arXiv 分类过滤（cs.AI, cs.CL, cs.LG, cs.CV 等）

### 3. 解析 JSON 输出并格式化报告

脚本输出 JSON 到 stdout，解析后按以下模板生成 Markdown 报告。

### 4. WebSearch 补充（可选）

以下情况使用 WebSearch 补充：
- 脚本搜索结果不足 3 篇
- 用户需要最新（1 周内）的研究动态
- 需要特定会议/期刊的论文（如 NeurIPS 2024 best paper）
- 需要中文论文或非 CS 领域论文

## 报告模板

```markdown
# 学术论文搜索报告

**搜索关键词：** {query} | **时间范围：** {date_range} | **排序方式：** {sort_by}
**数据源：** {sources} | **去重后结果：** {total} 篇

## 论文列表

| # | 标题 | 作者 | 年份 | 发表场所 | 引用数 | 来源 |
|---|------|------|------|----------|--------|------|
| 1 | [标题](url) | 作者1, 作者2 等 | 2024 | NeurIPS | 150 | arxiv,s2 |

## 重点论文详情

### 1. 论文标题
- **作者：** 完整作者列表
- **发表：** 会议/期刊, 年份
- **引用：** N 次
- **摘要：** 论文摘要内容
- **链接：** [论文](url) | [PDF](pdf_url) | [代码](code_url)

## 搜索建议
- 相关关键词推荐
- 可进一步探索的方向
```

**格式化规则：**
- 论文列表展示所有结果，作者超过 3 人时用"等"省略
- 重点论文详情展示引用数最高的前 5 篇（或用户指定数量）
- 如有代码链接，在详情中标注
- 来源字段用缩写：arxiv, s2(Semantic Scholar), oa(OpenAlex), pwc

## 常见搜索场景

| 场景 | 推荐参数 |
|------|----------|
| 找某主题最新论文 | `--sort date --date-from 2024-01-01` |
| 找高引经典论文 | `--sort citations` |
| 找特定领域论文 | `--field cs.AI,cs.CL` |
| 找有代码的论文 | `--sources pwc` |
| 快速概览 | `-n 5 --sources arxiv,semantic_scholar` |

## Resources

### scripts/
- `search_papers.py` - 主搜索脚本，并行调用多个 API，去重合并，输出 JSON
- `api_clients.py` - API 客户端封装（arXiv, Semantic Scholar, OpenAlex, Papers With Code）

### references/
- `data-sources.md` - 各数据源的详细说明、API 限制、搜索语法参考
