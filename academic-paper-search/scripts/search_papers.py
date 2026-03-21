# search_papers.py - 学术论文并行搜索主脚本
# 支持多数据源并行搜索、去重合并、排序输出，输出结构化 JSON

import sys
import os
import io
import re
import json
import argparse
import logging
from typing import List, Dict, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# 确保能导入同目录下的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api_clients import get_client, CLIENT_REGISTRY, BaseClient

logger = logging.getLogger(__name__)

# 默认启用的数据源
DEFAULT_SOURCES = ["arxiv", "semantic_scholar", "openalex", "pwc"]

# 每个数据源的超时时间（秒）
SOURCE_TIMEOUT = 30


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数。

    Returns:
        解析后的参数命名空间
    """
    parser = argparse.ArgumentParser(
        description="学术论文多源并行搜索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python search_papers.py -q "large language model" -n 20
  python search_papers.py -q "transformer" --sources arxiv,openalex
  python search_papers.py -q "LLM" --date-from 2024-01-01 --field cs.AI,cs.CL
  python search_papers.py -q "diffusion model" --sort citations -n 10
        """,
    )
    parser.add_argument(
        "-q", "--query", required=True, help="搜索关键词"
    )
    parser.add_argument(
        "-n", "--num-results", type=int, default=20,
        help="每个数据源的最大返回数量 (默认: 20)",
    )
    parser.add_argument(
        "--sources", default=",".join(DEFAULT_SOURCES),
        help=f"数据源列表，逗号分隔 (默认: {','.join(DEFAULT_SOURCES)})",
    )
    parser.add_argument(
        "--sort", choices=["relevance", "citations", "date"],
        default="relevance", help="排序方式 (默认: relevance)",
    )
    parser.add_argument(
        "--date-from", default=None,
        help="起始日期 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--date-to", default=None,
        help="截止日期 (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--field", default=None,
        help="学科领域过滤，逗号分隔 (如 cs.AI,cs.CL,cs.LG)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="显示详细日志",
    )
    return parser.parse_args()


def _search_single_source(
    client: BaseClient,
    query: str,
    max_results: int,
    date_from: Optional[str],
    date_to: Optional[str],
    fields: Optional[List[str]],
    sort_by: str,
) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
    """搜索单个数据源（供线程池调用）。

    Args:
        client: API 客户端实例
        query: 搜索关键词
        max_results: 最大返回数量
        date_from: 起始日期
        date_to: 截止日期
        fields: 学科领域过滤
        sort_by: 排序方式

    Returns:
        (数据源名称, 论文列表, 错误信息或None)
    """
    try:
        papers = client.search(
            query=query,
            max_results=max_results,
            date_from=date_from,
            date_to=date_to,
            fields=fields,
            sort_by=sort_by,
        )
        return (client.source_name, papers, None)
    except Exception as e:
        error_msg = f"{client.source_name} 搜索失败: {e}"
        logger.warning(error_msg)
        return (client.source_name, [], error_msg)


def search_all_sources(
    query: str,
    sources: List[str],
    max_results: int = 20,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    fields: Optional[List[str]] = None,
    sort_by: str = "relevance",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """使用线程池并行搜索所有数据源。

    Args:
        query: 搜索关键词
        sources: 数据源名称列表
        max_results: 每个数据源的最大返回数量
        date_from: 起始日期 (YYYY-MM-DD)
        date_to: 截止日期 (YYYY-MM-DD)
        fields: 学科领域过滤列表
        sort_by: 排序方式

    Returns:
        (合并后的论文列表, 搜索元信息字典)
    """
    all_papers: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {
        "sources_searched": [],
        "sources_failed": [],
        "errors": [],
        "counts_per_source": {},
    }

    # 创建客户端实例
    clients = []
    for src in sources:
        try:
            clients.append(get_client(src))
        except ValueError as e:
            meta["errors"].append(str(e))
            meta["sources_failed"].append(src)

    # 并行搜索
    with ThreadPoolExecutor(max_workers=len(clients)) as executor:
        futures = {
            executor.submit(
                _search_single_source,
                client, query, max_results,
                date_from, date_to, fields, sort_by,
            ): client.source_name
            for client in clients
        }

        for future in as_completed(futures, timeout=SOURCE_TIMEOUT + 10):
            source_name = futures[future]
            try:
                name, papers, error = future.result(timeout=SOURCE_TIMEOUT)
                if error:
                    meta["sources_failed"].append(name)
                    meta["errors"].append(error)
                else:
                    meta["sources_searched"].append(name)
                meta["counts_per_source"][name] = len(papers)
                all_papers.extend(papers)
            except Exception as e:
                meta["sources_failed"].append(source_name)
                meta["errors"].append(f"{source_name} 超时或异常: {e}")
                meta["counts_per_source"][source_name] = 0

    return all_papers, meta


def _normalize_title(title: str) -> str:
    """标准化论文标题用于去重比较。

    Args:
        title: 原始标题

    Returns:
        标准化后的标题（小写、去标点、去多余空格）
    """
    title = title.lower().strip()
    title = re.sub(r"[^\w\s]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title


def _merge_papers(
    existing: Dict[str, Any], new: Dict[str, Any]
) -> Dict[str, Any]:
    """合并两条重复论文记录，保留信息最完整的字段。

    Args:
        existing: 已有的论文记录
        new: 新的论文记录

    Returns:
        合并后的论文记录
    """
    merged = dict(existing)

    # 合并来源列表
    existing_sources = existing.get("source", "")
    new_source = new.get("source", "")
    if new_source and new_source not in existing_sources:
        merged["source"] = f"{existing_sources},{new_source}"

    # 取最大引用数
    merged["citations"] = max(
        existing.get("citations", 0), new.get("citations", 0)
    )

    # 补充缺失字段
    for key in [
        "abstract", "doi", "arxiv_id", "pdf_url", "code_url",
        "venue", "url", "published_date",
    ]:
        if not existing.get(key) and new.get(key):
            merged[key] = new[key]

    # 补充作者（取更长的列表）
    if len(new.get("authors", [])) > len(existing.get("authors", [])):
        merged["authors"] = new["authors"]

    return merged


def deduplicate_papers(
    papers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """对论文列表进行去重合并。

    去重策略（按优先级）：
    1. DOI 完全匹配
    2. arXiv ID 完全匹配
    3. 标题标准化后完全匹配

    Args:
        papers: 原始论文列表

    Returns:
        去重后的论文列表
    """
    # 索引表：key -> 在结果列表中的位置
    doi_index: Dict[str, int] = {}
    arxiv_index: Dict[str, int] = {}
    title_index: Dict[str, int] = {}
    result: List[Dict[str, Any]] = []

    for paper in papers:
        doi = paper.get("doi", "").strip()
        arxiv_id = paper.get("arxiv_id", "").strip()
        norm_title = _normalize_title(paper.get("title", ""))

        # 查找是否已存在
        existing_idx = None
        if doi and doi in doi_index:
            existing_idx = doi_index[doi]
        elif arxiv_id and arxiv_id in arxiv_index:
            existing_idx = arxiv_index[arxiv_id]
        elif norm_title and norm_title in title_index:
            existing_idx = title_index[norm_title]

        if existing_idx is not None:
            # 合并到已有记录
            result[existing_idx] = _merge_papers(
                result[existing_idx], paper
            )
        else:
            # 新记录
            idx = len(result)
            result.append(paper)
            if doi:
                doi_index[doi] = idx
            if arxiv_id:
                arxiv_index[arxiv_id] = idx
            if norm_title:
                title_index[norm_title] = idx

    logger.info("去重: %d -> %d 篇论文", len(papers), len(result))
    return result


def sort_papers(
    papers: List[Dict[str, Any]], sort_by: str = "relevance"
) -> List[Dict[str, Any]]:
    """按指定方式排序论文列表。

    Args:
        papers: 论文列表
        sort_by: 排序方式 (relevance/citations/date)

    Returns:
        排序后的论文列表
    """
    if sort_by == "citations":
        return sorted(papers, key=lambda p: p.get("citations", 0), reverse=True)
    elif sort_by == "date":
        return sorted(
            papers,
            key=lambda p: p.get("published_date", "") or "",
            reverse=True,
        )
    # relevance: 保持原始顺序（各数据源已按相关性排序）
    return papers


def format_output(
    papers: List[Dict[str, Any]],
    meta: Dict[str, Any],
    query: str,
    sort_by: str,
    date_from: Optional[str],
    date_to: Optional[str],
    fields: Optional[List[str]],
) -> str:
    """将搜索结果格式化为 JSON 字符串输出。

    Args:
        papers: 论文列表
        meta: 搜索元信息
        query: 搜索关键词
        sort_by: 排序方式
        date_from: 起始日期
        date_to: 截止日期
        fields: 学科领域过滤

    Returns:
        格式化的 JSON 字符串
    """
    output = {
        "query": query,
        "sort_by": sort_by,
        "date_range": {
            "from": date_from or "",
            "to": date_to or "",
        },
        "fields": fields or [],
        "total_results": len(papers),
        "sources_searched": meta.get("sources_searched", []),
        "sources_failed": meta.get("sources_failed", []),
        "counts_per_source": meta.get("counts_per_source", {}),
        "errors": meta.get("errors", []),
        "papers": papers,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def main() -> None:
    """主流程：解析参数 -> 并行搜索 -> 去重 -> 排序 -> 输出 JSON。"""
    args = parse_arguments()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    # 解析参数
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    fields = (
        [f.strip() for f in args.field.split(",") if f.strip()]
        if args.field
        else None
    )

    logger.info(
        "开始搜索: query=%s, sources=%s, fields=%s",
        args.query, sources, fields,
    )

    # 并行搜索所有数据源
    all_papers, meta = search_all_sources(
        query=args.query,
        sources=sources,
        max_results=args.num_results,
        date_from=args.date_from,
        date_to=args.date_to,
        fields=fields,
        sort_by=args.sort,
    )

    # 去重合并
    unique_papers = deduplicate_papers(all_papers)

    # 排序
    sorted_papers = sort_papers(unique_papers, args.sort)

    # 格式化输出（确保 Windows 下 UTF-8 输出）
    output = format_output(
        papers=sorted_papers,
        meta=meta,
        query=args.query,
        sort_by=args.sort,
        date_from=args.date_from,
        date_to=args.date_to,
        fields=fields,
    )

    # Windows UTF-8 兼容输出
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
    print(output)


if __name__ == "__main__":
    main()
