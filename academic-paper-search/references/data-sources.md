# 学术论文搜索数据源参考

## 数据源概览

| 数据源 | 覆盖范围 | 特点 | API 限制 |
|--------|----------|------|----------|
| arXiv | CS/AI 预印本 | 最新研究，分类完善 | 无严格限制，建议间隔 3 秒 |
| Semantic Scholar | 2 亿+论文 | 引用数据丰富 | 100 次/5 分钟（无 key） |
| OpenAlex | 2.5 亿+作品 | 完全免费，无限制 | 无限制（建议提供 mailto） |
| Papers With Code | ML/AI 论文 | 论文+代码+基准 | 无严格限制 |

## arXiv

**覆盖范围：** 计算机科学、物理、数学等领域的预印本论文。

**常用 CS 分类：**
- `cs.AI` - 人工智能
- `cs.CL` - 计算语言学 / NLP
- `cs.LG` - 机器学习
- `cs.CV` - 计算机视觉
- `cs.SE` - 软件工程
- `cs.CR` - 密码学与安全
- `cs.RO` - 机器人学

**搜索语法：**
- 关键词搜索：直接输入关键词
- 分类过滤：`cat:cs.AI`
- 组合查询：`(LLM) AND (cat:cs.CL OR cat:cs.AI)`

**排序选项：** relevance（相关性）、submittedDate（提交日期）

**注意事项：**
- arXiv 是预印本平台，论文未经同行评审
- 搜索结果可能包含不同版本的同一论文

## Semantic Scholar

**覆盖范围：** 2 亿+学术论文，涵盖所有学科。

**API 端点：** `https://api.semanticscholar.org/graph/v1/paper/search`

**可用字段：**
- `title`, `authors`, `year`, `venue`
- `citationCount`, `abstract`, `externalIds`
- `publicationDate`, `url`

**API 限制：**
- 无 API Key：100 次请求/5 分钟
- 有 API Key：可申请更高配额
- 单次最多返回 100 条结果

**排序选项：** `citationCount:desc`（引用数降序）

**注意事项：**
- 引用数据更新有延迟
- 部分论文可能缺少摘要

## OpenAlex

**覆盖范围：** 2.5 亿+学术作品，完全免费开放。

**API 端点：** `https://api.openalex.org/works`

**过滤参数：**
- `from_publication_date` / `to_publication_date` - 日期范围
- `concepts.id` - 概念 ID 过滤

**排序选项：**
- `relevance_score:desc` - 相关性
- `cited_by_count:desc` - 引用数
- `publication_date:desc` - 发表日期

**注意事项：**
- 摘要以倒排索引格式存储，需重建
- 建议在请求中提供 `mailto` 参数以获得更好的服务
- 概念 ID 需要预先映射

## Papers With Code

**覆盖范围：** ML/AI 领域论文，特色是关联代码仓库和基准测试。

**API 端点：** `https://paperswithcode.com/api/v1/papers/`

**搜索参数：**
- `q` - 搜索关键词
- `page` / `items_per_page` - 分页

**特色功能：**
- 论文关联的代码仓库链接
- 基准测试排行榜数据
- 方法和数据集信息

**注意事项：**
- 主要覆盖 ML/AI 领域
- 部分论文可能没有关联代码
- API 不支持排序参数

## 故障排除

**常见问题：**

1. **连接超时：** 检查网络连接，部分 API 可能需要代理访问
2. **429 Too Many Requests：** Semantic Scholar 有速率限制，等待后重试
3. **结果为空：** 尝试简化搜索关键词，或切换数据源
4. **编码错误：** Windows 下设置 `PYTHONIOENCODING=utf-8`
