"""
Filtered Approximate Nearest Neighbor Search (FANNS) Research Package.
Supports medium-scale benchmarks on SPCL/arxiv-for-fanns-medium dataset.
"""

from .dataset_loader import load_fanns_dataset, FANNSDataset, FANNSWorkload
from .filters import (
    FilterPredicate,
    EMFilterPredicate,
    RangeFilterPredicate,
    EMISFilterPredicate,
    MetadataIndex,
    parse_query_filter,
)
from .exact_search import ExactFilteredSearcher
from .hnsw_index import HNSWIndex
from .postfilter import HNSWPostFilterSearcher
from .overfetch import HNSWOverfetchSearcher
from .prefilter import PreFilterSearcher
from .ingraph import InGraphFilterSearcher
from .filter_aware import (
    ACORNFilterSearcher,
    SIEVEFilterSearcher,
    UNIFYFilterSearcher,
)
from .metrics import (
    QueryEvaluationResult,
    AggregateBenchmarkResult,
    compute_recall_at_k,
    aggregate_query_results,
    results_to_dataframe,
)
from .timing import PrecisionTimer, benchmark_callable

__all__ = [
    "load_fanns_dataset",
    "FANNSDataset",
    "FANNSWorkload",
    "FilterPredicate",
    "EMFilterPredicate",
    "RangeFilterPredicate",
    "EMISFilterPredicate",
    "MetadataIndex",
    "parse_query_filter",
    "ExactFilteredSearcher",
    "HNSWIndex",
    "HNSWPostFilterSearcher",
    "HNSWOverfetchSearcher",
    "PreFilterSearcher",
    "InGraphFilterSearcher",
    "ACORNFilterSearcher",
    "SIEVEFilterSearcher",
    "UNIFYFilterSearcher",
    "QueryEvaluationResult",
    "AggregateBenchmarkResult",
    "compute_recall_at_k",
    "aggregate_query_results",
    "results_to_dataframe",
    "PrecisionTimer",
    "benchmark_callable",
]
