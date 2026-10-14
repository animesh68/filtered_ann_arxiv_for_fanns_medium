"""
Experiment 08: Comprehensive Controlled Comparative Benchmark.
Executes the full FANNS benchmark matrix across all 11 search strategies and 3 filter workloads (EM, Range, EMIS)
under standardized evaluation parameters: K=10, 500 queries per workload (16,500 total query evaluations).

Features:
- Incremental per-method checkpointing and resumability
- Full metric logging: Recall@10, Mean/Median/P95/P99 latency, QPS, Candidates, Peak RAM
- Stratified selectivity binning (<2%, 2-10%, 10-30%, >30%)
- Pre-built index serialization to avoid redundant graph construction
"""

import argparse
import json
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
import psutil

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dataset_loader import load_fanns_dataset
from src.filters import MetadataIndex, parse_query_filter
from src.hnsw_index import HNSWIndex
from src.exact_search import ExactFilteredSearcher
from src.postfilter import HNSWPostFilterSearcher
from src.overfetch import HNSWOverfetchSearcher
from src.prefilter import PreFilterSearcher
from src.ingraph import InGraphFilterSearcher
from src.filter_aware import ACORNFilterSearcher, SIEVEFilterSearcher, UNIFYFilterSearcher
from src.metrics import (
    QueryEvaluationResult,
    aggregate_query_results,
    compute_recall_at_k,
    results_to_dataframe,
)
from src.timing import PrecisionTimer


def run_controlled_benchmark(
    config_path: str = "configs/medium_benchmark.json",
    num_eval_queries: int = 500,
    k: int = 10,
    M: int = 16,
    ef_construction: int = 100,
    ef_search: int = 50,
):
    print("=" * 80)
    print("EXPERIMENT 08: COMPREHENSIVE CONTROLLED BENCHMARK (MEDIUM DATASET)")
    print(f"Parameters: K={k}, Queries/Workload={num_eval_queries}, M={M}, efC={ef_construction}, efS={ef_search}")
    print("=" * 80)

    # Output directories
    out_dir_cb = Path("results/controlled_benchmark")
    out_dir_cb.mkdir(parents=True, exist_ok=True)
    out_dir_med = Path("results/medium")
    out_dir_med.mkdir(parents=True, exist_ok=True)

    raw_csv_path = out_dir_cb / "all_queries_raw_results.csv"
    summary_csv_path = out_dir_cb / "benchmark_summary.csv"
    strat_csv_path = out_dir_cb / "stratified_selectivity_summary.csv"

    # Check existing checkpoint
    completed_runs = set()
    existing_records = []
    if raw_csv_path.exists():
        df_existing = pd.read_csv(raw_csv_path)
        existing_records = df_existing.to_dict("records")
        for (m, f), grp in df_existing.groupby(["method", "filter_type"]):
            if len(grp) >= num_eval_queries:
                completed_runs.add((m, f))
        print(f"[Checkpoint] Found existing raw log with {len(df_existing)} records. Completed (method, workload) pairs: {len(completed_runs)}")

    print("\n[Step 1/4] Loading dataset with memory-mapping...")
    dataset = load_fanns_dataset("data/arxiv-for-fanns-medium", mmap=True)
    meta_idx = MetadataIndex(dataset.database_attributes)
    print(f"[OK] Loaded {dataset.num_database:,} DB vectors, {dataset.num_queries:,} queries.")

    # Shared HNSW Index: check if pre-built graph exists on disk
    index_cache_path = Path("results/hnsw_index_m16_ef100.pkl")
    hnsw = HNSWIndex(dimension=dataset.dimension, metric="l2", M=M, ef_construction=ef_construction, random_seed=42)

    build_time = 0.0
    if index_cache_path.exists():
        print(f"\n[Step 2/4] Loading pre-built HNSW Graph from {index_cache_path}...")
        t0 = time.perf_counter()
        hnsw.load_index(index_cache_path, vectors=dataset.database_vectors)
        load_time = time.perf_counter() - t0
        index_mem = hnsw.estimate_memory_mb()
        print(f"[OK] Index loaded in {load_time:.2f}s | Estimated RAM: {index_mem:.2f} MB")
    else:
        print(f"\n[Step 2/4] Building Shared HNSW Graph (M={M}, efConstruction={ef_construction})...")
        t0 = time.perf_counter()
        hnsw.build_index(dataset.database_vectors, progress_bar=True)
        build_time = time.perf_counter() - t0
        index_mem = hnsw.estimate_memory_mb()
        print(f"[OK] Index built in {build_time:.2f}s | Estimated RAM: {index_mem:.2f} MB")
        hnsw.save_index(index_cache_path)
        print(f"[OK] Saved index cache to {index_cache_path}")

    # Instantiate searchers
    exact_searcher = ExactFilteredSearcher(dataset.database_vectors, meta_idx, metric="l2", chunk_size=5000)
    post_searcher = HNSWPostFilterSearcher(hnsw, meta_idx)
    overfetch_2x = HNSWOverfetchSearcher(hnsw, meta_idx)
    overfetch_5x = HNSWOverfetchSearcher(hnsw, meta_idx)
    overfetch_10x = HNSWOverfetchSearcher(hnsw, meta_idx)
    overfetch_20x = HNSWOverfetchSearcher(hnsw, meta_idx)
    pre_searcher = PreFilterSearcher(dataset.database_vectors, meta_idx, metric="l2", chunk_size=5000, precomputed_norms=exact_searcher.db_norms)
    ingraph_searcher = InGraphFilterSearcher(hnsw, meta_idx)
    acorn_searcher = ACORNFilterSearcher(hnsw, meta_idx, n_hops=2)
    sieve_searcher = SIEVEFilterSearcher(hnsw, meta_idx)
    unify_searcher = UNIFYFilterSearcher(hnsw, meta_idx)

    # Strategy map
    strategies = {
        "ExactSearch": lambda q, p: exact_searcher.search(q, predicate=p, k=k),
        "PreFilter": lambda q, p: pre_searcher.search(q, predicate=p, k=k),
        "HNSW_PostFilter": lambda q, p: post_searcher.search(q, predicate=p, k=k, ef_search=ef_search),
        "HNSW_Overfetch_2x": lambda q, p: overfetch_2x.search(q, predicate=p, k=k, overfetch_factor=2.0),
        "HNSW_Overfetch_5x": lambda q, p: overfetch_5x.search(q, predicate=p, k=k, overfetch_factor=5.0),
        "HNSW_Overfetch_10x": lambda q, p: overfetch_10x.search(q, predicate=p, k=k, overfetch_factor=10.0),
        "HNSW_Overfetch_20x": lambda q, p: overfetch_20x.search(q, predicate=p, k=k, overfetch_factor=20.0),
        "InGraphFilter": lambda q, p: ingraph_searcher.search(q, predicate=p, k=k, ef_search=ef_search),
        "ACORN_Approx": lambda q, p: acorn_searcher.search(q, predicate=p, k=k, ef_search=ef_search),
        "SIEVE_Approx": lambda q, p: sieve_searcher.search(q, predicate=p, k=k, ef_search=ef_search),
        "UNIFY_Approx": lambda q, p: unify_searcher.search(q, predicate=p, k=k, base_ef_search=ef_search),
    }

    all_query_records = list(existing_records)
    aggregate_summaries = []

    print(f"\n[Step 3/4] Executing Benchmark across Workloads & Methods (Queries: {num_eval_queries})...")
    process = psutil.Process()

    for w_name in ["EM", "Range", "EMIS"]:
        workload = dataset.get_workload(w_name)
        print(f"\n==================== Workload: {w_name} ====================")

        for strat_name, search_fn in strategies.items():
            if (strat_name, w_name) in completed_runs:
                print(f"[SKIP] {strat_name:<20} | {w_name} already completed in previous run.")
                continue

            strat_q_results = []
            new_rows = []

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

                q_res = QueryEvaluationResult(
                    query_id=q_idx,
                    filter_type=w_name,
                    selectivity=selectivity,
                    candidate_count=cand_count,
                    k=k,
                    recall_at_k=recall,
                    latency_ms=timer.elapsed_ms,
                )
                strat_q_results.append(q_res)

                row_dict = {
                    "method": strat_name,
                    "filter_type": w_name,
                    "query_id": q_idx,
                    "k": k,
                    "selectivity": selectivity,
                    "candidate_count": cand_count,
                    "recall_at_k": recall,
                    "latency_ms": timer.elapsed_ms,
                }
                new_rows.append(row_dict)

            all_query_records.extend(new_rows)
            completed_runs.add((strat_name, w_name))

            # Incremental save of raw per-query data
            pd.DataFrame(all_query_records).to_csv(raw_csv_path, index=False)
            pd.DataFrame(all_query_records).to_csv(out_dir_med / "all_queries_raw_results.csv", index=False)

            agg = aggregate_query_results(
                method_name=strat_name,
                filter_type=w_name,
                k=k,
                query_results=strat_q_results,
                index_build_time_s=build_time if "HNSW" in strat_name or "Graph" in strat_name or "ACORN" in strat_name or "SIEVE" in strat_name or "UNIFY" in strat_name else 0.0,
                index_memory_mb=hnsw.estimate_memory_mb() if "HNSW" in strat_name or "Graph" in strat_name or "ACORN" in strat_name or "SIEVE" in strat_name or "UNIFY" in strat_name else 0.0,
                parameters={"k": k, "M": M, "ef_construction": ef_construction, "ef_search": ef_search},
            )
            aggregate_summaries.append(agg)
            rss_mb = process.memory_info().rss / (1024 * 1024)
            print(f"[{strat_name:<20} | {w_name}] Recall@{k}: {agg.mean_recall:.4f} | Latency: {agg.mean_latency_ms:>6.3f} ms | QPS: {agg.qps:>6.1f} | Mean Cand: {agg.mean_candidate_count:>7.1f} | RSS: {rss_mb:.1f} MB")

    # Final summary tables
    print("\n[Step 4/4] Generating consolidated aggregate summary & stratified tables...")
    df_all_raw = pd.DataFrame(all_query_records)
    
    # Compute aggregate summary over all records
    full_summaries = []
    for (m, f), grp in df_all_raw.groupby(["method", "filter_type"]):
        q_results = [
            QueryEvaluationResult(
                query_id=int(r["query_id"]),
                filter_type=str(r["filter_type"]),
                selectivity=float(r["selectivity"]),
                candidate_count=int(r["candidate_count"]),
                k=int(r["k"]),
                recall_at_k=float(r["recall_at_k"]),
                latency_ms=float(r["latency_ms"]),
            )
            for _, r in grp.iterrows()
        ]
        agg = aggregate_query_results(
            method_name=m,
            filter_type=f,
            k=k,
            query_results=q_results,
            index_build_time_s=build_time if "HNSW" in m or "Graph" in m or "ACORN" in m or "SIEVE" in m or "UNIFY" in m else 0.0,
            index_memory_mb=hnsw.estimate_memory_mb() if "HNSW" in m or "Graph" in m or "ACORN" in m or "SIEVE" in m or "UNIFY" in m else 0.0,
            parameters={"k": k, "M": M, "ef_construction": ef_construction, "ef_search": ef_search},
        )
        full_summaries.append(agg)

    df_summary = results_to_dataframe(full_summaries)
    df_summary.to_csv(summary_csv_path, index=False)
    df_summary.to_csv(out_dir_med / "benchmark_summary.csv", index=False)
    print(f"[OK] Summary table saved: {summary_csv_path}")

    # Stratified selectivity analysis
    df_all_raw["selectivity_bucket"] = pd.cut(
        df_all_raw["selectivity"],
        bins=[-0.001, 0.02, 0.10, 0.30, 1.0],
        labels=["Ultra-Low (<2%)", "Low (2-10%)", "Medium (10-30%)", "High (>30%)"],
    )
    strat_grouped = df_all_raw.groupby(["method", "filter_type", "selectivity_bucket"], observed=False).agg(
        mean_recall=("recall_at_k", "mean"),
        mean_latency_ms=("latency_ms", "mean"),
        median_latency_ms=("latency_ms", "median"),
        p95_latency_ms=("latency_ms", lambda x: float(np.percentile(x, 95)) if len(x) > 0 else 0.0),
        query_count=("query_id", "count"),
    ).reset_index()

    strat_grouped.to_csv(strat_csv_path, index=False)
    strat_grouped.to_csv(out_dir_med / "stratified_selectivity_summary.csv", index=False)
    print(f"[OK] Stratified summary saved: {strat_csv_path}")

    return df_summary, strat_grouped


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FANNS controlled benchmark on medium dataset")
    parser.add_argument("--queries", type=int, default=500, help="Number of queries to evaluate per workload")
    parser.add_argument("--k", type=int, default=10, help="Top-K value")
    args = parser.parse_args()

    run_controlled_benchmark(num_eval_queries=args.queries, k=args.k)
