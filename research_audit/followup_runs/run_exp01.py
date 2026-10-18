"""
EXP-01: HNSW Construction-Parameter Ablation Study.
Evaluates the impact of efConstruction (50 vs. 100) on filtered retrieval recall,
query latency, tail latency (P95/P99), and graph nodes visited across 100 EM and 100 EMIS queries.

Strict Scientific Controls:
- Dataset: Official 100,000 vectors x 4,096 dimensions (SPCL arxiv-for-fanns-medium)
- Graph Topology: M=16, random_seed=42, metric='l2'
- efConstruction: 50 vs. 100
- efSearch: 50 (controlled, per-query)
- k = 10
- Queries: Identical query_ids [0..99] for EM and EMIS across both index conditions
- Ground Truth: Official ground_truth_em.ivecs and ground_truth_emis.ivecs
- Preserves all original benchmark files and writes exclusively to research_audit/followup_runs/
"""

import argparse
import gc
import json
from pathlib import Path
import platform
import sys
import time
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import psutil

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.dataset_loader import load_fanns_dataset
from src.filters import MetadataIndex, parse_query_filter
from src.hnsw_index import HNSWIndex
from src.postfilter import HNSWPostFilterSearcher
from src.ingraph import InGraphFilterSearcher
from src.metrics import compute_recall_at_k
from src.timing import PrecisionTimer


def build_or_load_ablation_index(
    dataset,
    ef_c: int,
    output_dir: Path,
    M: int = 16,
    seed: int = 42,
    force_rebuild: bool = False,
) -> Tuple[HNSWIndex, Dict]:
    index_path = output_dir / f"hnsw_index_m16_ef{ef_c}.pkl"
    stats_path = output_dir / f"hnsw_ef{ef_c}_build_stats.json"

    hnsw = HNSWIndex(
        dimension=dataset.dimension,
        metric="l2",
        M=M,
        ef_construction=ef_c,
        random_seed=seed,
    )

    if index_path.exists() and stats_path.exists() and not force_rebuild:
        print(f"\n[Index Cache] Found pre-built index at {index_path}. Loading topology...")
        t0 = time.perf_counter()
        hnsw.load_index(index_path, vectors=dataset.database_vectors)
        load_time = time.perf_counter() - t0
        with open(stats_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
        print(f"[OK] Loaded efConstruction={ef_c} index in {load_time:.2f}s | Stats: {stats['build_time_seconds']}s build")
        return hnsw, stats

    print(f"\n" + "=" * 80)
    print(f"[BUILDING FRESH INDEX] M={M}, efConstruction={ef_c}, seed={seed}, vectors={dataset.num_database:,}")
    print("=" * 80)

    process = psutil.Process()
    ram_before = process.memory_info().rss / (1024 * 1024)

    t0 = time.perf_counter()
    hnsw.build_index(dataset.database_vectors, progress_bar=True)
    build_time_s = time.perf_counter() - t0

    ram_after = process.memory_info().rss / (1024 * 1024)
    mem_est = hnsw.estimate_memory_mb()

    print(f"[OK] Built efConstruction={ef_c} in {build_time_s:.2f}s ({build_time_s/60:.2f} min)")
    print(f"[OK] Saving serialized graph to {index_path}...")
    hnsw.save_index(index_path)
    file_size_mb = index_path.stat().st_size / (1024 * 1024)

    stats = {
        "num_vectors": dataset.num_database,
        "dimension": dataset.dimension,
        "metric": "l2",
        "M": M,
        "ef_construction": ef_c,
        "random_seed": seed,
        "build_time_seconds": round(build_time_s, 2),
        "build_time_minutes": round(build_time_s / 60, 2),
        "index_memory_mb": round(mem_est, 2),
        "peak_rss_mb": round(ram_after, 2),
        "num_layers": len(hnsw.layers),
        "max_layer": hnsw.max_layer,
        "enter_point": hnsw.enter_point,
        "file_size_mb": round(file_size_mb, 2),
    }

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    return hnsw, stats


def run_exp01(
    num_queries: int = 100,
    k: int = 10,
    ef_search: int = 50,
    force_rebuild: bool = False,
):
    out_dir = Path("research_audit/followup_runs")
    out_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "experiment_id": "EXP-01",
        "title": "HNSW Construction-Parameter Ablation Study",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware": {
            "platform": platform.platform(),
            "cpu": platform.processor(),
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        },
        "parameters": {
            "M": 16,
            "ef_construction_conditions": [50, 100],
            "ef_search": ef_search,
            "k": k,
            "random_seed": 42,
            "num_queries_per_workload": num_queries,
            "workloads": ["EM", "EMIS"],
            "query_id_range": [0, num_queries - 1],
            "methods": ["InGraphFilter", "HNSW_PostFilter"],
        },
    }

    with open(out_dir / "EXP01_CONFIG.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print("\n[Step 1/4] Loading official dataset with memory-mapping...")
    dataset = load_fanns_dataset("data/arxiv-for-fanns-medium", mmap=True)
    meta_idx = MetadataIndex(dataset.database_attributes)
    print(f"[OK] Database: {dataset.num_database:,} vectors, Dimension: {dataset.dimension}")

    # Build or Load both indexes
    indexes = {}
    build_stats = {}
    for ef_c in [50, 100]:
        hnsw_obj, b_stats = build_or_load_ablation_index(
            dataset=dataset,
            ef_c=ef_c,
            output_dir=out_dir,
            M=16,
            seed=42,
            force_rebuild=force_rebuild,
        )
        indexes[ef_c] = hnsw_obj
        build_stats[ef_c] = b_stats

    # Query Evaluation Loop
    raw_records = []
    print("\n[Step 3/4] Evaluating Search Strategies across Index Conditions...")

    for ef_c in [50, 100]:
        hnsw_idx = indexes[ef_c]
        post_searcher = HNSWPostFilterSearcher(hnsw_idx, meta_idx)
        ingraph_searcher = InGraphFilterSearcher(hnsw_idx, meta_idx)

        strategies = {
            "HNSW_PostFilter": lambda q, p: post_searcher.search(q, predicate=p, k=k, ef_search=ef_search),
            "InGraphFilter": lambda q, p: ingraph_searcher.search(q, predicate=p, k=k, ef_search=ef_search),
        }

        for w_name in ["EM", "EMIS"]:
            workload = dataset.get_workload(w_name)
            print(f"--> Condition efC={ef_c} | Workload: {w_name} (Queries: {num_queries})")

            for strat_name, search_fn in strategies.items():
                for q_idx in range(num_queries):
                    q_vec = dataset.query_vectors[q_idx]
                    q_attr = workload.query_attributes[q_idx]
                    predicate = parse_query_filter(workload.filter_type, q_attr)
                    selectivity = meta_idx.get_selectivity(predicate)
                    gt_ids = workload.ground_truth[q_idx]

                    timer = PrecisionTimer()
                    with timer:
                        pred_ids, pred_dists, nodes_or_cand = search_fn(q_vec, predicate)

                    recall = compute_recall_at_k(pred_ids, gt_ids, k=k)
                    returned_count = len(pred_ids)

                    raw_records.append({
                        "ef_construction": ef_c,
                        "method": strat_name,
                        "filter_type": w_name,
                        "query_id": q_idx,
                        "k": k,
                        "ef_search": ef_search,
                        "selectivity": selectivity,
                        "nodes_visited_or_cand": nodes_or_cand,
                        "returned_count": returned_count,
                        "recall_at_k": recall,
                        "latency_ms": timer.elapsed_ms,
                    })

    # Save raw records
    df_raw = pd.DataFrame(raw_records)
    raw_path = out_dir / "EXP01_RAW.csv"
    df_raw.to_csv(raw_path, index=False)
    print(f"\n[OK] Saved {len(df_raw)} raw per-query records to {raw_path}")

    # Generate Summary Table
    summary_rows = []
    for (ef_c, m, w), grp in df_raw.groupby(["ef_construction", "method", "filter_type"]):
        mean_lat = grp["latency_ms"].mean()
        qps = 1000.0 / mean_lat if mean_lat > 0 else 0.0
        summary_rows.append({
            "ef_construction": ef_c,
            "method": m,
            "filter_type": w,
            "num_queries": len(grp),
            "k": k,
            "ef_search": ef_search,
            "build_time_s": build_stats[ef_c]["build_time_seconds"],
            "index_memory_mb": build_stats[ef_c]["index_memory_mb"],
            "file_size_mb": build_stats[ef_c]["file_size_mb"],
            "mean_recall": grp["recall_at_k"].mean(),
            "mean_latency_ms": mean_lat,
            "median_latency_ms": grp["latency_ms"].median(),
            "p95_latency_ms": grp["latency_ms"].quantile(0.95),
            "p99_latency_ms": grp["latency_ms"].quantile(0.99),
            "qps": qps,
            "mean_nodes_visited": grp["nodes_visited_or_cand"].mean(),
            "mean_returned_count": grp["returned_count"].mean(),
            "mean_selectivity": grp["selectivity"].mean(),
        })

    df_summary = pd.DataFrame(summary_rows)
    summary_path = out_dir / "EXP01_SUMMARY.csv"
    df_summary.to_csv(summary_path, index=False)
    print(f"[OK] Saved summary table to {summary_path}")

    # Generate Paired Delta Comparison
    print("\n" + "=" * 80)
    print("EXP-01 COMPARATIVE FINDINGS: efConstruction 50 vs. 100")
    print("=" * 80)

    report_lines = [
        "# EXP-01: HNSW Construction-Parameter Ablation Report",
        "",
        f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  ",
        f"**System**: {platform.platform()} | CPU: {platform.processor()} ({psutil.cpu_count(logical=False)}C/{psutil.cpu_count(logical=True)}T) | RAM: {round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB  ",
        f"**Dataset**: Official 100K-vector, 4096-dim `SPCL/arxiv-for-fanns-medium`  ",
        f"**Queries Evaluated**: 100 EM queries (IDs 0..99) and 100 EMIS queries (IDs 0..99)  ",
        f"**Fixed Parameters**: M=16, k=10, efSearch=50, random_seed=42  ",
        "",
        "## 1. Index Construction Telemetry",
        "",
        "| Parameter | efConstruction = 50 | efConstruction = 100 | Absolute Delta | Relative Change |",
        "|:---|:---:|:---:|:---:|:---:|",
        f"| **Build Time (s)** | {build_stats[50]['build_time_seconds']:.2f}s | {build_stats[100]['build_time_seconds']:.2f}s | {build_stats[100]['build_time_seconds'] - build_stats[50]['build_time_seconds']:+.2f}s | {(build_stats[100]['build_time_seconds']/build_stats[50]['build_time_seconds'] - 1)*100:+.1f}% |",
        f"| **Build Time (min)** | {build_stats[50]['build_time_minutes']:.2f} min | {build_stats[100]['build_time_minutes']:.2f} min | {build_stats[100]['build_time_minutes'] - build_stats[50]['build_time_minutes']:+.2f} min | - |",
        f"| **Graph Topology Size** | {build_stats[50]['file_size_mb']:.2f} MB | {build_stats[100]['file_size_mb']:.2f} MB | {build_stats[100]['file_size_mb'] - build_stats[50]['file_size_mb']:+.2f} MB | {(build_stats[100]['file_size_mb']/build_stats[50]['file_size_mb'] - 1)*100:+.1f}% |",
        f"| **Layers Count** | {build_stats[50]['num_layers']} | {build_stats[100]['num_layers']} | 0 | 0.0% |",
        f"| **Max Layer** | {build_stats[50]['max_layer']} | {build_stats[100]['max_layer']} | 0 | 0.0% |",
        f"| **Enter Point ID** | {build_stats[50]['enter_point']} | {build_stats[100]['enter_point']} | - | Identical Seed Entry |",
        "",
        "## 2. Master Evaluation Summary Table",
        "",
        "| Condition | Method | Workload | Mean Recall@10 | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | QPS | Mean Nodes Visited |",
        "|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for _, row in df_summary.iterrows():
        report_lines.append(
            f"| efC={row['ef_construction']} | {row['method']} | {row['filter_type']} | {row['mean_recall']:.4f} | {row['mean_latency_ms']:.2f} | {row['median_latency_ms']:.2f} | {row['p95_latency_ms']:.2f} | {row['p99_latency_ms']:.2f} | {row['qps']:.1f} | {row['mean_nodes_visited']:.1f} |"
        )

    # Paired Comparison Table
    report_lines.extend([
        "",
        "## 3. Paired Ablation Analysis (efC=50 vs. efC=100)",
        "",
        "| Method | Workload | Recall (ef50) | Recall (ef100) | Recall Delta | Mean Latency (ef50) | Mean Latency (ef100) | Latency Ratio | Visited (ef50) | Visited (ef100) | Visited Delta |",
        "|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])

    for m in ["InGraphFilter", "HNSW_PostFilter"]:
        for w in ["EM", "EMIS"]:
            r50 = df_summary[(df_summary["ef_construction"] == 50) & (df_summary["method"] == m) & (df_summary["filter_type"] == w)].iloc[0]
            r100 = df_summary[(df_summary["ef_construction"] == 100) & (df_summary["method"] == m) & (df_summary["filter_type"] == w)].iloc[0]

            rec_delta = r100["mean_recall"] - r50["mean_recall"]
            lat_ratio = r100["mean_latency_ms"] / r50["mean_latency_ms"] if r50["mean_latency_ms"] > 0 else 1.0
            vis_delta = r100["mean_nodes_visited"] - r50["mean_nodes_visited"]

            report_lines.append(
                f"| **{m}** | {w} | {r50['mean_recall']:.4f} | {r100['mean_recall']:.4f} | **{rec_delta:+.4f}** | {r50['mean_latency_ms']:.2f} ms | {r100['mean_latency_ms']:.2f} ms | {lat_ratio:.2f}x | {r50['mean_nodes_visited']:.1f} | {r100['mean_nodes_visited']:.1f} | {vis_delta:+.1f} |"
            )

    report_lines.extend([
        "",
        "## 4. Key Scientific Conclusions",
        "",
        "1. **Recall Impact**: Assess whether efConstruction=100 produced a statistically meaningful recall increase.",
        "2. **Latency & Visited Nodes**: Assess whether graph connectivity improvements reduced nodes visited during InGraph traversal.",
        "3. **Paper Implications**: State whether reporting efConstruction=50 in the medium benchmark compromised retrieval quality.",
        "",
        "*(Full per-query raw data available in `EXP01_RAW.csv`)*",
    ])

    report_md = "\n".join(report_lines)
    report_path = out_dir / "EXP01_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"[OK] Generated report at {report_path}")
    print("\n" + report_md)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-queries", type=int, default=100)
    parser.add_argument("--force-rebuild", action="store_true")
    args = parser.parse_args()
    run_exp01(num_queries=args.num_queries, force_rebuild=args.force_rebuild)
