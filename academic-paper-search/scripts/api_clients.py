# api_clients.py - 学术论文搜索 API 客户端封装
# 封装 arXiv、Semantic Scholar、OpenAlex、Papers With Code 四个数据源的搜索客户端

import re
import logging
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


def _safe_str(value: Any, default: str = "") -> str:
    """安全转换为字符串，处理 None 值。

    Args:
        value: 待转换的值
        default: 默认值

    Returns:
        转换后的字符串
    """
    if value is None:
        return default
    return str(value)


def _safe_int(value: Any, default: int = 0) -> int:
    """安全转换为整数，处理 None 和非数字值。

    Args:
        value: 待转换的值
        default: 默认值

    Returns:
        转换后的整数
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _make_paper_dict(
    title: str = "",
    authors: Optional[List[str]] = None,
    year: int = 0,
    venue: str = "",
    citations: int = 0,
    abstract: str = "",
    url: str = "",
    doi: str = "",
    arxiv_id: str = "",
    source: str = "",
    published_date: str = "",
    pdf_url: str = "",
    code_url: str = "",
) -> Dict[str, Any]:
    """构造统一格式的论文字典。

    Args:
        title: 论文标题
        authors: 作者列表
        year: 发表年份
        venue: 期刊/会议名称
        citations: 引用次数
        abstract: 摘要
        url: 论文链接
        doi: DOI 标识符
        arxiv_id: arXiv ID
        source: 数据来源标识
        published_date: 发表日期 (YYYY-MM-DD)
        pdf_url: PDF 下载链接
        code_url: 代码仓库链接

    Returns:
        统一格式的论文信息字典
    """
    return {
        "title": title,
        "authors": authors or [],
        "year": year,
        "venue": venue,
        "citations": citations,
        "abstract": abstract,
        "url": url,
        "doi": doi,
        "arxiv_id": arxiv_id,
        "source": source,
        "published_date": published_date,
        "pdf_url": pdf_url,
        "code_url": code_url,
    }


class BaseClient(ABC):
    """学术搜索客户端基类，定义统一的搜索接口。"""

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 10,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        fields: Optional[List[str]] = None,
        sort_by: str = "relevance",
    ) -> List[Dict[str, Any]]:
        """搜索论文。

        Args:
            query: 搜索关键词
            max_results: 最大返回数量
            date_from: 起始日期 (YYYY-MM-DD)
            date_to: 截止日期 (YYYY-MM-DD)
            fields: 学科领域过滤列表 (如 cs.AI, cs.CL)
            sort_by: 排序方式 (relevance/citations/date)

        Returns:
            统一格式的论文字典列表
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称。"""
        pass


class ArxivClient(BaseClient):
    """arXiv 搜索客户端，使用 arxiv 库搜索 CS/AI 预印本。"""

    @property
    def source_name(self) -> str:
        """数据源名称。"""
        return "arxiv"

    def search(
        self,
        query: str,
        max_results: int = 10,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        fields: Optional[List[str]] = None,
        sort_by: str = "relevance",
    ) -> List[Dict[str, Any]]:
        """通过 arxiv 库搜索论文。

        Args:
            query: 搜索关键词
            max_results: 最大返回数量
            date_from: 起始日期 (YYYY-MM-DD)
            date_to: 截止日期 (YYYY-MM-DD)
            fields: arXiv 分类过滤 (如 cs.AI, cs.CL, cs.LG)
            sort_by: 排序方式 (relevance/citations/date)

        Returns:
            统一格式的论文字典列表
        """
        import arxiv

        # 构建查询字符串，添加分类过滤
        search_query = query
        if fields:
            cat_filter = " OR ".join(f"cat:{f}" for f in fields)
            search_query = f"({query}) AND ({cat_filter})"

        # 设置排序方式
        sort_criterion = arxiv.SortCriterion.Relevance
        if sort_by == "date":
            sort_criterion = arxiv.SortCriterion.SubmittedDate

        client = arxiv.Client()
        search = arxiv.Search(
            query=search_query,
            max_results=max_results,
            sort_by=sort_criterion,
        )

        papers = []
        for result in client.results(search):
            # 日期过滤
            pub_date = result.published
            if date_from:
                from_dt = datetime.strptime(date_from, "%Y-%m-%d")
                if pub_date.replace(tzinfo=None) < from_dt:
                    continue
            if date_to:
                to_dt = datetime.strptime(date_to, "%Y-%m-%d")
                if pub_date.replace(tzinfo=None) > to_dt:
                    continue

            # 提取 arXiv ID
            aid = _safe_str(result.entry_id).split("/abs/")[-1]

            papers.append(_make_paper_dict(
                title=_safe_str(result.title),
                authors=[a.name for a in (result.authors or [])],
                year=pub_date.year if pub_date else 0,
                venue="arXiv",
                abstract=_safe_str(result.summary),
                url=_safe_str(result.entry_id),
                doi=_safe_str(result.doi),
                arxiv_id=aid,
                source=self.source_name,
                published_date=pub_date.strftime("%Y-%m-%d") if pub_date else "",
                pdf_url=_safe_str(result.pdf_url),
            ))

        logger.info("arXiv 返回 %d 篇论文", len(papers))
        return papers


class SemanticScholarClient(BaseClient):
    """Semantic Scholar 搜索客户端，使用 REST API 搜索 2 亿+论文。"""

    API_BASE = "https://api.semanticscholar.org/graph/v1"

    @property
    def source_name(self) -> str:
        """数据源名称。"""
        return "semantic_scholar"

    def search(
        self,
        query: str,
        max_results: int = 10,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        fields: Optional[List[str]] = None,
        sort_by: str = "relevance",
    ) -> List[Dict[str, Any]]:
        """通过 Semantic Scholar API 搜索论文。

        Args:
            query: 搜索关键词
            max_results: 最大返回数量
            date_from: 起始日期 (YYYY-MM-DD)
            date_to: 截止日期 (YYYY-MM-DD)
            fields: 未使用（Semantic Scholar 不支持分类过滤）
            sort_by: 排序方式 (relevance/citations/date)

        Returns:
            统一格式的论文字典列表
        """
        api_fields = (
            "title,authors,year,venue,citationCount,abstract,"
            "url,externalIds,publicationDate"
        )
        params: Dict[str, Any] = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": api_fields,
        }

        # 日期范围过滤
        if date_from or date_to:
            year_from = date_from[:4] if date_from else ""
            year_to = date_to[:4] if date_to else ""
            params["year"] = f"{year_from}-{year_to}"

        # 排序
        if sort_by == "citations":
            params["sort"] = "citationCount:desc"

        resp = requests.get(
            f"{self.API_BASE}/paper/search",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data.get("data", []):
            ext_ids = item.get("externalIds") or {}
            authors = [
                a.get("name", "") for a in (item.get("authors") or [])
            ]
            pub_date = _safe_str(item.get("publicationDate"))

            papers.append(_make_paper_dict(
                title=_safe_str(item.get("title")),
                authors=authors,
                year=_safe_int(item.get("year")),
                venue=_safe_str(item.get("venue")),
                citations=_safe_int(item.get("citationCount")),
                abstract=_safe_str(item.get("abstract")),
                url=_safe_str(item.get("url")),
                doi=_safe_str(ext_ids.get("DOI")),
                arxiv_id=_safe_str(ext_ids.get("ArXiv")),
                source=self.source_name,
                published_date=pub_date,
            ))

        logger.info("Semantic Scholar 返回 %d 篇论文", len(papers))
        return papers


class OpenAlexClient(BaseClient):
    """OpenAlex 搜索客户端，使用 REST API 搜索 2.5 亿+学术作品，完全免费。"""

    API_BASE = "https://api.openalex.org"

    # OpenAlex 中 CS 子领域概念 ID 映射
    FIELD_CONCEPT_MAP = {
        "cs.AI": "C154945302",   # Artificial intelligence
        "cs.CL": "C204321447",   # Computational linguistics / NLP
        "cs.LG": "C119857082",   # Machine learning
        "cs.CV": "C31972630",    # Computer vision
        "cs.SE": "C71924100",    # Software engineering
        "cs.DB": "C199360897",   # Database
        "cs.CR": "C38652104",    # Cryptography
        "cs.RO": "C90856448",    # Robotics
    }

    @property
    def source_name(self) -> str:
        """数据源名称。"""
        return "openalex"

    def search(
        self,
        query: str,
        max_results: int = 10,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        fields: Optional[List[str]] = None,
        sort_by: str = "relevance",
    ) -> List[Dict[str, Any]]:
        """通过 OpenAlex API 搜索论文。

        Args:
            query: 搜索关键词
            max_results: 最大返回数量
            date_from: 起始日期 (YYYY-MM-DD)
            date_to: 截止日期 (YYYY-MM-DD)
            fields: 学科领域过滤 (如 cs.AI, cs.CL)
            sort_by: 排序方式 (relevance/citations/date)

        Returns:
            统一格式的论文字典列表
        """
        params: Dict[str, Any] = {
            "search": query,
            "per_page": min(max_results, 200),
            "mailto": "academic-search@example.com",
        }

        # 构建过滤条件
        filters = []
        if date_from:
            filters.append(f"from_publication_date:{date_from}")
        if date_to:
            filters.append(f"to_publication_date:{date_to}")
        if fields:
            concept_ids = [
                self.FIELD_CONCEPT_MAP[f]
                for f in fields
                if f in self.FIELD_CONCEPT_MAP
            ]
            if concept_ids:
                filters.append(f"concepts.id:{'|'.join(concept_ids)}")
        if filters:
            params["filter"] = ",".join(filters)

        # 排序
        sort_map = {
            "relevance": "relevance_score:desc",
            "citations": "cited_by_count:desc",
            "date": "publication_date:desc",
        }
        params["sort"] = sort_map.get(sort_by, "relevance_score:desc")

        resp = requests.get(
            f"{self.API_BASE}/works",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data.get("results", []):
            # 提取作者
            authors = []
            for authorship in (item.get("authorships") or []):
                author_info = authorship.get("author") or {}
                name = author_info.get("display_name", "")
                if name:
                    authors.append(name)

            # 提取 DOI
            doi_raw = _safe_str(item.get("doi"))
            doi = doi_raw.replace("https://doi.org/", "") if doi_raw else ""

            # 提取发表场所
            primary_loc = item.get("primary_location") or {}
            source_info = primary_loc.get("source") or {}
            venue = _safe_str(source_info.get("display_name"))

            # 提取 PDF 链接
            best_oa = item.get("best_oa_location") or {}
            pdf_url = _safe_str(best_oa.get("pdf_url"))

            pub_date = _safe_str(item.get("publication_date"))

            papers.append(_make_paper_dict(
                title=_safe_str(item.get("title")),
                authors=authors,
                year=_safe_int(item.get("publication_year")),
                venue=venue,
                citations=_safe_int(item.get("cited_by_count")),
                abstract=self._reconstruct_abstract(
                    item.get("abstract_inverted_index")
                ),
                url=_safe_str(item.get("id")),
                doi=doi,
                source=self.source_name,
                published_date=pub_date,
                pdf_url=pdf_url,
            ))

        logger.info("OpenAlex 返回 %d 篇论文", len(papers))
        return papers

    @staticmethod
    def _reconstruct_abstract(
        inverted_index: Optional[Dict[str, List[int]]],
    ) -> str:
        """从 OpenAlex 的倒排索引重建摘要文本。

        Args:
            inverted_index: OpenAlex 返回的摘要倒排索引 {word: [positions]}

        Returns:
            重建后的摘要文本
        """
        if not inverted_index:
            return ""
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join(w for _, w in word_positions)


class PapersWithCodeClient(BaseClient):
    """HuggingFace Papers 搜索客户端（原 Papers With Code，已迁移至 HuggingFace）。"""

    API_BASE = "https://huggingface.co/api/papers"

    @property
    def source_name(self) -> str:
        """数据源名称。"""
        return "papers_with_code"

    def search(
        self,
        query: str,
        max_results: int = 10,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        fields: Optional[List[str]] = None,
        sort_by: str = "relevance",
    ) -> List[Dict[str, Any]]:
        """通过 HuggingFace Papers API 搜索论文。

        Args:
            query: 搜索关键词
            max_results: 最大返回数量
            date_from: 起始日期 (YYYY-MM-DD)，用于客户端过滤
            date_to: 截止日期 (YYYY-MM-DD)，用于客户端过滤
            fields: 未使用
            sort_by: 未使用

        Returns:
            统一格式的论文字典列表
        """
        resp = requests.get(
            f"{self.API_BASE}/search",
            params={"q": query, "limit": min(max_results, 100)},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data:
            paper_info = item.get("paper") or {}
            # 解析发表日期
            pub_raw = _safe_str(paper_info.get("publishedAt"))
            pub_date = pub_raw[:10] if pub_raw and len(pub_raw) >= 10 else ""
            year = _safe_int(pub_date[:4]) if pub_date else 0

            # 日期过滤
            if date_from and pub_date and pub_date < date_from:
                continue
            if date_to and pub_date and pub_date > date_to:
                continue

            # 提取作者
            authors = [
                _safe_str(a.get("name"))
                for a in (paper_info.get("authors") or [])
                if a.get("name")
            ]

            # 论文 ID 即 arXiv ID
            paper_id = _safe_str(paper_info.get("id"))
            url = f"https://arxiv.org/abs/{paper_id}" if paper_id else ""
            pdf_url = f"https://arxiv.org/pdf/{paper_id}" if paper_id else ""

            # 提取 upvotes 作为引用数的近似
            upvotes = _safe_int(paper_info.get("upvotes"))

            papers.append(_make_paper_dict(
                title=_safe_str(paper_info.get("title")),
                authors=authors,
                year=year,
                abstract=_safe_str(paper_info.get("summary")),
                url=url,
                arxiv_id=paper_id,
                source=self.source_name,
                published_date=pub_date,
                pdf_url=pdf_url,
                citations=upvotes,
            ))

        logger.info("HuggingFace Papers 返回 %d 篇论文", len(papers))
        return papers


# 客户端注册表，用于按名称获取客户端实例
CLIENT_REGISTRY: Dict[str, type] = {
    "arxiv": ArxivClient,
    "semantic_scholar": SemanticScholarClient,
    "openalex": OpenAlexClient,
    "pwc": PapersWithCodeClient,
}


def get_client(source_name: str) -> BaseClient:
    """根据数据源名称获取对应的客户端实例。

    Args:
        source_name: 数据源名称 (arxiv/semantic_scholar/openalex/pwc)

    Returns:
        对应的客户端实例

    Raises:
        ValueError: 未知的数据源名称
    """
    cls = CLIENT_REGISTRY.get(source_name)
    if cls is None:
        raise ValueError(
            f"未知数据源: {source_name}，"
            f"可选: {', '.join(CLIENT_REGISTRY.keys())}"
        )
    return cls()


if __name__ == "__main__":
    # 轻量级自测：验证各客户端能正常实例化和搜索
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    test_query = "transformer"
    print(f"=== API 客户端自测 (查询: {test_query}) ===\n")

    for name, cls in CLIENT_REGISTRY.items():
        print(f"--- 测试 {name} ---")
        try:
            client = cls()
            results = client.search(test_query, max_results=2)
            print(f"  返回 {len(results)} 篇论文")
            if results:
                p = results[0]
                print(f"  第1篇: {p['title'][:60]}...")
                print(f"  作者: {', '.join(p['authors'][:3])}")
                print(f"  年份: {p['year']}, 来源: {p['source']}")
            print()
        except Exception as e:
            print(f"  错误: {e}\n")

    print("=== 自测完成 ===")
