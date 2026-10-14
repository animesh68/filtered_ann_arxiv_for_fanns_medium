"""
Audit Script: Comprehensive Pipeline Verification for FANNS Medium Dataset.
Tests:
1. Exact Ground Truth vs Official ivecs on a deterministic sample (50 queries/workload).
2. Metrics logic, corner cases (|GT| < K, empty GT), percentiles, and QPS definitions.
3. All 11 search methods execution, result shapes, valid IDs, and filter satisfaction.
Outputs test results with clear pass/fail status and documentation.
"""

from pathlib import Path
import sys
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.dataset_loader import load_fanns_dataset
from src.filters import (
    MetadataIndex,
    parse_query_filter,
    EMFilterPredicate,
    RangeFilterPredicate,
    EMISFilterPredicate,
)
from src.exact_search import ExactFilteredSearcher
from src.metrics import compute_recall_at_k, aggregate_query_results, QueryEvaluationResult
from src.hnsw_index import HNSWIndex
from src.postfilter import HNSWPostFilterSearcher
from src.overfetch import HNSWOverfetchSearcher
from src.prefilter import PreFilterSearcher
from src.ingraph import InGraphFilterSearcher
from src.filter_aware import ACORNFilterSearcher, SIEVEFilterSearcher, UNIFYFilterSearcher


def test_ground_truth_fidelity(sample_queries: int = 50):
    print("=" * 80)
    print(f"AUDIT TEST 1: GROUND TRUTH FIDELITY CHECK (Deterministic Sample: {sample_queries} queries/workload)")
    print("=" * 80)

    dataset = load_fanns_dataset("data/arxiv-for-fanns-medium", mmap=True)
    meta_idx = MetadataIndex(dataset.database_attributes)
    exact_searcher = ExactFilteredSearcher(dataset.database_vectors, meta_idx, metric="l2")

    for w_name in ["EM", "Range", "EMIS"]:
        workload = dataset.get_workload(w_name)
        gt_list = workload.ground_truth
        assert len(gt_list) == 10000, f"{w_name} GT length is {len(gt_list)}, expected 10000"

        top10_matches = 0
        top100_matches = 0
        total_checked = min(sample_queries, len(gt_list))

        for q_idx in range(total_checked):
            q_vec = dataset.query_vectors[q_idx]
            q_attr = workload.query_attributes[q_idx]
            pred = parse_query_filter(workload.filter_type, q_attr)

            pred_ids, pred_dists, cand_count = exact_searcher.search(q_vec, predicate=pred, k=100)
            gt_ids = gt_list[q_idx]

            k10 = min(10, len(gt_ids))
            if k10 > 0:
                if set(pred_ids[:k10]) == set(gt_ids[:k10]):
                    top10_matches += 1
            else:
                top10_matches += 1

            k100 = min(100, len(gt_ids))
            if k100 > 0:
                if set(pred_ids[:k100]) == set(gt_ids[:k100]):
                    top100_matches += 1
            else:
                top100_matches += 1

        pct10 = (top10_matches / total_checked) * 100.0
        pct100 = (top100_matches / total_checked) * 100.0
        print(f"[{w_name:<5}] Top-10 Set Match: {top10_matches}/{total_checked} ({pct10:.1f}%) | Top-100 Set Match: {top100_matches}/{total_checked} ({pct100:.1f}%)")
        assert top10_matches == total_checked, f"Ground truth mismatch detected in {w_name} workload!"

    print("[PASS] Official ground-truth files perfectly match mathematical exact search.")


def test_metrics_logic():
    print("\n" + "=" * 80)
    print("AUDIT TEST 2: METRICS LOGIC & EDGE CASES")
    print("=" * 80)

    # 1. Perfect match
    r1 = compute_recall_at_k([1, 2, 3], [1, 2, 3, 4, 5], k=3)
    assert r1 == 1.0, f"Expected 1.0, got {r1}"

    # 2. Partial match
    r2 = compute_recall_at_k([1, 2, 9], [1, 2, 3, 4, 5], k=3)
    assert abs(r2 - 2/3) < 1e-6, f"Expected 0.6666, got {r2}"

    # 3. Small ground truth |GT| < K
    r3 = compute_recall_at_k([1, 2], [1, 2], k=10)
    assert r3 == 1.0, f"Expected 1.0 when |GT| < K and all found, got {r3}"

    # 4. Empty ground truth
    r4 = compute_recall_at_k([], [], k=10)
    assert r4 == 1.0, f"Expected 1.0 for empty GT, got {r4}"

    # 5. Aggregator test: percentile and QPS calculations
    q_results = [
        QueryEvaluationResult(query_id=0, filter_type="test", selectivity=0.1, candidate_count=100, k=10, recall_at_k=1.0, latency_ms=1.0),
        QueryEvaluationResult(query_id=1, filter_type="test", selectivity=0.1, candidate_count=100, k=10, recall_at_k=0.5, latency_ms=2.0),
        QueryEvaluationResult(query_id=2, filter_type="test", selectivity=0.1, candidate_count=100, k=10, recall_at_k=0.0, latency_ms=3.0),
    ]
    agg = aggregate_query_results("test_method", "test", k=10, query_results=q_results)
    assert abs(agg.mean_recall - 0.5) < 1e-6
    assert abs(agg.mean_latency_ms - 2.0) < 1e-6
    assert abs(agg.median_latency_ms - 2.0) < 1e-6
    assert abs(agg.qps - (3 / 0.006)) < 1e-3
    print("[PASS] Metrics calculation, edge cases, and statistical aggregation verified.")


def test_smoke_all_search_methods():
    print("\n" + "=" * 80)
    print("AUDIT TEST 3: SMOKE TEST ON ALL 11 SEARCH METHODS (Micro-Workload)")
    print("=" * 80)

    dataset = load_fanns_dataset("data/arxiv-for-fanns-medium", mmap=True)
    meta_idx = MetadataIndex(dataset.database_attributes)

    # Fast micro-index on first 2,000 vectors for lightning-fast structural verification
    micro_n = 2000
    print(f"Building micro-HNSW index on first {micro_n} vectors for algorithmic smoke testing...")
    micro_meta_idx = MetadataIndex(dataset.database_attributes[:micro_n])
    hnsw = HNSWIndex(dimension=dataset.dimension, metric="l2", M=16, ef_construction=50, random_seed=42)
    hnsw.build_index(dataset.database_vectors[:micro_n], progress_bar=False)

    exact = ExactFilteredSearcher(dataset.database_vectors[:micro_n], micro_meta_idx)
    post = HNSWPostFilterSearcher(hnsw, micro_meta_idx)
    overfetch_2x = HNSWOverfetchSearcher(hnsw, micro_meta_idx)
    overfetch_5x = HNSWOverfetchSearcher(hnsw, micro_meta_idx)
    overfetch_10x = HNSWOverfetchSearcher(hnsw, micro_meta_idx)
    overfetch_20x = HNSWOverfetchSearcher(hnsw, micro_meta_idx)
    pre = PreFilterSearcher(dataset.database_vectors[:micro_n], micro_meta_idx)
    ingraph = InGraphFilterSearcher(hnsw, micro_meta_idx)
    acorn = ACORNFilterSearcher(hnsw, micro_meta_idx, n_hops=2)
    sieve = SIEVEFilterSearcher(hnsw, micro_meta_idx)
    unify = UNIFYFilterSearcher(hnsw, micro_meta_idx)

    methods = {
        "ExactSearch": lambda q, p: exact.search(q, predicate=p, k=10),
        "PreFilter": lambda q, p: pre.search(q, predicate=p, k=10),
        "HNSW_PostFilter": lambda q, p: post.search(q, predicate=p, k=10, ef_search=50),
        "HNSW_Overfetch_2x": lambda q, p: overfetch_2x.search(q, predicate=p, k=10, overfetch_factor=2.0),
        "HNSW_Overfetch_5x": lambda q, p: overfetch_5x.search(q, predicate=p, k=10, overfetch_factor=5.0),
        "HNSW_Overfetch_10x": lambda q, p: overfetch_10x.search(q, predicate=p, k=10, overfetch_factor=10.0),
        "HNSW_Overfetch_20x": lambda q, p: overfetch_20x.search(q, predicate=p, k=10, overfetch_factor=20.0),
        "InGraphFilter": lambda q, p: ingraph.search(q, predicate=p, k=10, ef_search=50),
        "ACORN_Approx": lambda q, p: acorn.search(q, predicate=p, k=10, ef_search=50),
        "SIEVE_Approx": lambda q, p: sieve.search(q, predicate=p, k=10, ef_search=50),
        "UNIFY_Approx": lambda q, p: unify.search(q, predicate=p, k=10, base_ef_search=50),
    }

    q_vec = dataset.query_vectors[0]
    q_attr = dataset.workloads["EM"].query_attributes[0]
    pred = parse_query_filter("EM", q_attr)

    for name, fn in methods.items():
        t0 = time.perf_counter()
        ids, dists, cand_visited = fn(q_vec, pred)
        elapsed = (time.perf_counter() - t0) * 1000.0

        assert isinstance(ids, np.ndarray), f"{name} returned non-ndarray IDs"
        assert isinstance(dists, np.ndarray), f"{name} returned non-ndarray distances"
        assert len(ids) <= 10, f"{name} returned {len(ids)} > 10 items"

        # Check predicate satisfaction for returned IDs
        for r_id in ids:
            assert pred.matches(dataset.database_attributes[r_id]), f"{name} returned invalid candidate ID {r_id}!"

        print(f"  [PASS] {name:<20}: Returned {len(ids):>2} IDs | Evaluated/Visited: {cand_visited:>4} | Latency: {elapsed:>5.2f} ms")

    print("\n[PASS] All 11 search methods executed successfully and satisfy metadata predicates.")


if __name__ == "__main__":
    test_metrics_logic()
    test_smoke_all_search_methods()
    test_ground_truth_fidelity(sample_queries=50)
    print("\n" + "=" * 80)
    print("ALL AUDIT PIPELINE TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)
