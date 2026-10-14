"""
Experiment 07: Filter-Aware Comparison Benchmark (ACORN, SIEVE, UNIFY).
Evaluates paper-inspired state-of-the-art approximations:
- ACORN-style multi-hop expansion over non-matching routing nodes
- SIEVE-style centroid-guided candidate entry-point selection
- UNIFY-style selectivity-adaptive dynamic efSearch scaling
"""

import argparse
from pathlib import Path
import sys
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dataset_loader import load_fanns_dataset
from src.filters import MetadataIndex, parse_query_filter
from src.hnsw_index import HNSWIndex
from src.filter_aware import ACORNFilterSearcher, SIEVEFilterSearcher, UNIFYFilterSearcher
from src.metrics import (
    QueryEvaluationResult,
    aggregate_query_results,
    compute_recall_at_k,
    results_to_dataframe,
)
from src.timing import PrecisionTimer


def run_filter_aware_benchmark(
    num_eval_queries: int = 500,
    k: int = 10,
    M: int = 16,
    ef_construction: int = 100,
    ef_search: int = 50,
):
    print("=" * 80)
    print(f"EXPERIMENT 07: FILTER-AWARE COMPARISON (ACORN, SIEVE, UNIFY) (K={k}, N={num_eval_queries})")
    print("=" * 80)

    dataset = load_fanns_dataset("data/arxiv-for-fanns-medium", mmap=True)
    meta_idx = MetadataIndex(dataset.database_attributes)

    index_cache = Path("results/hnsw_index_m16_ef100.pkl")
    hnsw = HNSWIndex(dimension=dataset.dimension, metric="l2", M=M, ef_construction=ef_construction, random_seed=42)
    build_time = 0.0

    if index_cache.exists():
        print(f"Loading cached HNSW Index from {index_cache}...")
        hnsw.load_index(index_cache, vectors=dataset.database_vectors)
    else:
        print("Building HNSW Index...")
        t0 = time.perf_counter()
        hnsw.build_index(dataset.database_vectors)
        build_time = time.perf_counter() - t0
        hnsw.save_index(index_cache)

    acorn = ACORNFilterSearcher(hnsw, meta_idx, n_hops=2)
    sieve = SIEVEFilterSearcher(hnsw, meta_idx)
    unify = UNIFYFilterSearcher(hnsw, meta_idx)

    methods = {
        "ACORN_Approx": lambda q, p: acorn.search(q, predicate=p, k=k, ef_search=ef_search),
        "SIEVE_Approx": lambda q, p: sieve.search(q, predicate=p, k=k, ef_search=ef_search),
        "UNIFY_Approx": lambda q, p: unify.search(q, predicate=p, k=k, base_ef_search=ef_search),
    }

    output_dir = Path("results/filter_aware")
    output_dir.mkdir(parents=True, exist_ok=True)

    aggregate_results = []

    for strat_name, search_fn in methods.items():
        print(f"\n--- Strategy: {strat_name} ---")
        for w_name in ["EM", "Range", "EMIS"]:
            workload = dataset.get_workload(w_name)
            q_results = []

            for q_idx in range(min(num_eval_queries, dataset.num_queries)):
                q_vec = dataset.query_vectors[q_idx]
                q_attr = workload.query_attributes[q_idx]
                predicate = parse_query_filter(workload.filter_type, q_attr)
                selectivity = meta_idx.get_selectivity(predicate)
                gt_ids = workload.ground_truth[q_idx]

                timer = PrecisionTimer()
                with timer:
                    pred_ids, pred_dists, cand_count = search_fn(q_vec, predicate)

                recall = compute_recall_at_k(pred_ids, gt_ids, k=k)
                q_results.append(
                    QueryEvaluationResult(
                        query_id=q_idx,
                        filter_type=w_name,
                        selectivity=selectivity,
                        candidate_count=cand_count,
                        k=k,
                        recall_at_k=recall,
                        latency_ms=timer.elapsed_ms,
                    )
                )

            agg = aggregate_query_results(
                method_name=strat_name,
                filter_type=w_name,
                k=k,
                query_results=q_results,
                index_build_time_s=build_time,
                index_memory_mb=hnsw.estimate_memory_mb(),
                parameters={"k": k, "M": M, "ef_construction": ef_construction, "ef_search": ef_search},
            )
            aggregate_results.append(agg)
            print(f"[{w_name:<5}] Recall@{k}: {agg.mean_recall:.4f} | Latency: {agg.mean_latency_ms:.3f} ms | QPS: {agg.qps:.1f} | Mean Visited: {agg.mean_candidate_count:.1f}")

    df = results_to_dataframe(aggregate_results)
    df.to_csv(output_dir / "filter_aware_summary.csv", index=False)
    print(f"\n[OK] Summary saved to {output_dir / 'filter_aware_summary.csv'}")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", type=int, default=500)
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()
    run_filter_aware_benchmark(num_eval_queries=args.queries, k=args.k)
