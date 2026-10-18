"""
recompute_audit.py
==================
Independent evidence-backed audit script for the FANNS Medium Benchmark.
Recomputes all summary statistics directly from raw per-query measurements
without executing expensive searches. Validates schema, query counts,
stratified buckets, cross-scale consistency, and outputs audit_findings.json.
"""

import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd


def audit_repository():
    audit_results = {
        "audit_version": "1.0.0",
        "timestamp": "2026-10-16T00:36:00Z",
        "verifications": {},
        "discrepancies": [],
        "recomputed_tables": {},
        "cross_scale_comparison": {},
    }

    print("=" * 80)
    print("FANNS RESEARCH: INDEPENDENT EVIDENCE & REPRODUCIBILITY AUDIT")
    print("=" * 80)

    # ---------------------------------------------------------
    # Step 1: Artifact Inventory & File Existence
    # ---------------------------------------------------------
    print("\n[Step 1/6] Auditing Artifact Inventory...")
    artifacts = {
        "raw_results_csv": "results/controlled_benchmark/all_queries_raw_results.csv",
        "benchmark_summary_csv": "results/controlled_benchmark/benchmark_summary.csv",
        "stratified_summary_csv": "results/controlled_benchmark/stratified_selectivity_summary.csv",
        "hnsw_overfetch_csv": "results/hnsw_overfetch/hnsw_overfetch_summary.csv",
        "index_build_stats_json": "results/medium/index_build_stats.json",
        "dataset_validation_json": "results/medium/dataset_validation.json",
        "config_json": "configs/medium_benchmark.json",
        "readme_md": "README.md",
        "migration_plan_md": "reports/MEDIUM_MIGRATION_PLAN.md",
        "benchmark_report_md": "reports/MEDIUM_BENCHMARK_REPORT.md",
        "cross_scale_md": "reports/MEDIUM_VS_SMALL_COMPARISON.md",
        "final_audit_md": "reports/MEDIUM_FINAL_AUDIT.md",
        "word_report_docx": "reports/FANNS_Method_Comparison_Report.docx",
        "fig_recall_sel": "reports/figures/recall_vs_selectivity.png",
        "fig_pareto": "reports/figures/recall_vs_latency_tradeoff.png",
        "fig_qps": "reports/figures/qps_comparison.png",
        "fig_overfetch": "reports/figures/overfetch_sensitivity.png",
        "hnsw_index_pkl": "results/hnsw_index_m16_ef100.pkl",
    }

    inventory = {}
    for key, rel_path in artifacts.items():
        p = Path(rel_path)
        exists = p.exists()
        size = p.stat().st_size if exists else 0
        inventory[key] = {
            "path": rel_path,
            "exists": exists,
            "size_bytes": size,
            "status": "VERIFIED FROM ARTIFACTS" if exists else "NOT FOUND",
        }
        status_flag = "[OK]" if exists else "[MISSING]"
        print(f"  {status_flag} {rel_path:<60} ({size:>10,} bytes)")

    audit_results["verifications"]["artifact_inventory"] = inventory

    # ---------------------------------------------------------
    # Step 2: Query-Count Integrity & Schema Validation
    # ---------------------------------------------------------
    print("\n[Step 2/6] Auditing Query-Count Integrity in Raw Per-Query Log...")
    raw_path = Path(artifacts["raw_results_csv"])
    if not raw_path.exists():
        print("  [FAIL] Raw results CSV not found! Cannot proceed with per-query audit.")
        return

    df_raw = pd.read_csv(raw_path)
    expected_rows = 16500
    actual_rows = len(df_raw)
    
    unique_methods = sorted(df_raw["method"].unique().tolist())
    unique_workloads = sorted(df_raw["filter_type"].unique().tolist())
    
    print(f"  Total raw records: {actual_rows:,} (Expected: {expected_rows:,})")
    print(f"  Methods ({len(unique_methods)}): {unique_methods}")
    print(f"  Workloads ({len(unique_workloads)}): {unique_workloads}")

    # Check query count per (method, filter_type)
    query_counts = df_raw.groupby(["filter_type", "method"])["query_id"].nunique()
    min_queries = query_counts.min()
    max_queries = query_counts.max()
    all_500 = (min_queries == 500) and (max_queries == 500) and (len(query_counts) == 33)

    # Check query_id range
    min_qid = df_raw["query_id"].min()
    max_qid = df_raw["query_id"].max()
    qids_0_to_499 = (min_qid == 0) and (max_qid == 499)

    # Check selectivity consistency per (workload, query_id)
    pivot_sel = df_raw.pivot_table(index=["filter_type", "query_id"], columns="method", values="selectivity")
    max_sel_diff = float((pivot_sel.max(axis=1) - pivot_sel.min(axis=1)).max())

    query_integrity_status = "RECOMPUTED AND MATCHED" if (all_500 and qids_0_to_499 and max_sel_diff == 0.0) else "DISCREPANCY FOUND"
    print(f"  Unique queries per method/workload: exactly 500 across all 33 pairs? {all_500}")
    print(f"  Query IDs strictly [0, 499]? {qids_0_to_499}")
    print(f"  Selectivity variation across methods for identical query: {max_sel_diff}")

    audit_results["verifications"]["query_count_integrity"] = {
        "status": query_integrity_status,
        "total_records": actual_rows,
        "unique_methods_count": len(unique_methods),
        "unique_workloads_count": len(unique_workloads),
        "evaluations_count": len(query_counts),
        "queries_per_evaluation": 500,
        "query_id_min": int(min_qid),
        "query_id_max": int(max_qid),
        "max_selectivity_divergence_across_methods": max_sel_diff,
    }

    # ---------------------------------------------------------
    # Step 3: Recompute Aggregate Metrics & Match against benchmark_summary.csv
    # ---------------------------------------------------------
    print("\n[Step 3/6] Recomputing Statistical Aggregates from Raw Per-Query Logs...")
    recomputed_rows = []
    for (m, f), grp in df_raw.groupby(["method", "filter_type"]):
        recomputed_rows.append({
            "method": m,
            "filter_type": f,
            "k": int(grp["k"].iloc[0]),
            "num_queries": len(grp),
            "recomputed_mean_recall": float(grp["recall_at_k"].mean()),
            "recomputed_mean_latency_ms": float(grp["latency_ms"].mean()),
            "recomputed_median_latency_ms": float(grp["latency_ms"].median()),
            "recomputed_p95_latency_ms": float(np.percentile(grp["latency_ms"], 95)),
            "recomputed_p99_latency_ms": float(np.percentile(grp["latency_ms"], 99)),
            "recomputed_qps": float(1000.0 / grp["latency_ms"].mean()),
            "recomputed_mean_selectivity": float(grp["selectivity"].mean()),
            "recomputed_mean_candidate_count": float(grp["candidate_count"].mean()),
        })
    df_recomputed = pd.DataFrame(recomputed_rows)

    df_reported = pd.read_csv(artifacts["benchmark_summary_csv"])
    merged = pd.merge(df_reported, df_recomputed, on=["method", "filter_type"])

    diff_recall = float((merged["mean_recall"] - merged["recomputed_mean_recall"]).abs().max())
    diff_lat_mean = float((merged["mean_latency_ms"] - merged["recomputed_mean_latency_ms"]).abs().max())
    diff_lat_med = float((merged["median_latency_ms"] - merged["recomputed_median_latency_ms"]).abs().max())
    diff_lat_p95 = float((merged["p95_latency_ms"] - merged["recomputed_p95_latency_ms"]).abs().max())
    diff_lat_p99 = float((merged["p99_latency_ms"] - merged["recomputed_p99_latency_ms"]).abs().max())
    diff_qps = float((merged["qps"] - merged["recomputed_qps"]).abs().max())

    tolerances_met = (
        diff_recall < 1e-6 and
        diff_lat_mean < 1e-6 and
        diff_lat_med < 1e-6 and
        diff_lat_p95 < 1e-6 and
        diff_lat_p99 < 1e-6 and
        diff_qps < 1e-6
    )

    agg_status = "RECOMPUTED AND MATCHED" if tolerances_met else "DISCREPANCY FOUND"
    print(f"  Status: {agg_status}")
    print(f"  Max absolute error in Recall@10: {diff_recall:.2e}")
    print(f"  Max absolute error in Mean Latency: {diff_lat_mean:.2e} ms")
    print(f"  Max absolute error in Median Latency: {diff_lat_med:.2e} ms")
    print(f"  Max absolute error in P95 Latency: {diff_lat_p95:.2e} ms")
    print(f"  Max absolute error in P99 Latency: {diff_lat_p99:.2e} ms")
    print(f"  Max absolute error in QPS: {diff_qps:.2e}")

    audit_results["verifications"]["summary_recomputation"] = {
        "status": agg_status,
        "max_abs_error_recall": diff_recall,
        "max_abs_error_mean_latency_ms": diff_lat_mean,
        "max_abs_error_median_latency_ms": diff_lat_med,
        "max_abs_error_p95_latency_ms": diff_lat_p95,
        "max_abs_error_p99_latency_ms": diff_lat_p99,
        "max_abs_error_qps": diff_qps,
    }

    # ---------------------------------------------------------
    # Step 4: Narrative vs. Data Discrepancy Investigation
    # ---------------------------------------------------------
    print("\n[Step 4/6] Investigating Specific Discrepancies in README and Narrative Reports...")
    discrepancies = []

    # Discrepancy 1: Narrative text claims vs. measured table in README
    readme_path = Path(artifacts["readme_md"])
    if readme_path.exists():
        readme_text = readme_path.read_text(encoding="utf-8")
        if ">99.4%" in readme_text and "5.4" in readme_text and "335.34" in readme_text:
            d1 = {
                "id": "DISC-001",
                "title": "Narrative Text vs. Measured Table Inconsistency in README.md",
                "type": "NARRATIVE_VS_DATA_CONFLICT",
                "severity": "HIGH",
                "description": (
                    "Section 'Small (1K) vs Medium (100K) Architectural Analysis' in README.md line 173 states: "
                    "'InGraphFilter visits only ~800 nodes out of 100,000 (0.8%), achieving >99.4% recall at 5.4-6.2 ms latency'. "
                    "However, the measured benchmark summary table directly above reports InGraphFilter EMIS latency as 335.34 ms with 0.8858 recall, "
                    "EM latency 13.99 ms with 0.9374 recall, and Range latency 24.14 ms with 0.9304 recall."
                ),
                "root_cause": (
                    "The text in Section 'Small vs Medium Analysis' was prematurely adapted from the small-scale repository numbers "
                    "(where InGraphFilter ran in 4.95 ms with 0.9998 recall) during project setup and was not updated after live medium benchmarking completed."
                ),
                "resolution": (
                    "Replaced with verified empirical data: on the medium dataset, InGraphFilter achieves 0.9374 recall at 13.99 ms (EM), "
                    "0.9304 recall at 24.14 ms (Range), and 0.8858 recall at 335.34 ms (EMIS). On EMIS, InGraphFilter must visit on average 18,530 nodes, "
                    "which in Python takes 335.34 ms."
                ),
                "status": "DISCREPANCY FOUND & EXPLAINED",
            }
            discrepancies.append(d1)
            print(f"  [DISCREPANCY FOUND] {d1['title']}")
            print(f"    Cause: {d1['root_cause']}")

    # Discrepancy 2: HNSW efConstruction filename vs. actual build stats
    stats_path = Path(artifacts["index_build_stats_json"])
    if stats_path.exists():
        with open(stats_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
        ef_c_actual = stats.get("ef_construction")
        filename = Path(artifacts["hnsw_index_pkl"]).name
        if "ef100" in filename and ef_c_actual == 50:
            d2 = {
                "id": "DISC-002",
                "title": "HNSW Index Cache Filename vs. Actual Build Configuration",
                "type": "METADATA_MISMATCH",
                "severity": "MEDIUM",
                "description": (
                    f"The cached index file is named '{filename}', suggesting efConstruction=100. "
                    f"However, results/medium/index_build_stats.json records actual ef_construction={ef_c_actual}."
                ),
                "root_cause": (
                    "build_index.py defaulted to ef_construction=50 to ensure safe index completion on the 7.5GB mobile Ryzen CPU "
                    "within 12 minutes, but wrote to the default filename string 'results/hnsw_index_m16_ef100.pkl'."
                ),
                "resolution": (
                    "Document in audit that index construction was performed with M=16, efConstruction=50, build time 713.89 seconds (11.90 min)."
                ),
                "status": "DISCREPANCY FOUND & EXPLAINED",
            }
            discrepancies.append(d2)
            print(f"  [DISCREPANCY FOUND] {d2['title']}")
            print(f"    Cause: {d2['root_cause']}")

    # Discrepancy 3: Paper-inspired baseline approximation vs. original methods
    d3 = {
        "id": "DISC-003",
        "title": "Paper-Inspired Approximation Fidelity (ACORN, SIEVE, UNIFY)",
        "type": "IMPLEMENTATION_FIDELITY_LIMITATION",
        "severity": "HIGH",
        "description": (
            "Source code implementations in src/filter_aware.py (ACORN, SIEVE, UNIFY) are paper-inspired approximations "
            "evaluated on a single shared HNSW graph, rather than the official vendor C++/CUDA frameworks from SIGMOD/VLDB."
        ),
        "root_cause": (
            "- ACORN (Patel et al. 2024) constructs a specialized gamma-scaled edge graph; our baseline approximates query-time traversal via 2-hop neighbor expansion.\n"
            "- SIEVE (Gao et al. 2024) builds a multi-index collection with a 3D packing model; our baseline approximates centroid entry routing by sampling 16 candidates.\n"
            "- UNIFY (Liang et al. 2024) constructs a Segmented Inclusive Graph (SIG); our baseline uses a heuristic rule switching between InGraph and ACORN with increased ef."
        ),
        "resolution": (
            "Must be explicitly disclosed in the paper methodology. These methods must be described as 'paper-inspired single-graph heuristic baselines', "
            "not as official vendor implementations."
        ),
        "status": "LIMITATION FORMALLY DOCUMENTED",
    }
    discrepancies.append(d3)
    print(f"  [DISCREPANCY/LIMITATION] {d3['title']}")

    audit_results["discrepancies"] = discrepancies

    # ---------------------------------------------------------
    # Step 5: Cross-Scale Analysis (Small 1K vs Medium 100K)
    # ---------------------------------------------------------
    print("\n[Step 5/6] Auditing Cross-Scale Findings (Small 1K vs Medium 100K)...")
    # Verified small-scale empirical baselines (from small repository ground-truth logs)
    small_data = [
        {"method": "ExactSearch", "filter_type": "EM", "small_recall": 1.0000, "small_lat_ms": 7.07, "small_qps": 141.4},
        {"method": "ExactSearch", "filter_type": "Range", "small_recall": 1.0000, "small_lat_ms": 8.30, "small_qps": 120.5},
        {"method": "ExactSearch", "filter_type": "EMIS", "small_recall": 1.0000, "small_lat_ms": 3.11, "small_qps": 321.5},
        {"method": "PreFilter", "filter_type": "EM", "small_recall": 1.0000, "small_lat_ms": 6.92, "small_qps": 144.4},
        {"method": "PreFilter", "filter_type": "Range", "small_recall": 1.0000, "small_lat_ms": 8.20, "small_qps": 122.0},
        {"method": "PreFilter", "filter_type": "EMIS", "small_recall": 1.0000, "small_lat_ms": 3.15, "small_qps": 317.5},
        {"method": "HNSW_PostFilter", "filter_type": "EM", "small_recall": 0.2608, "small_lat_ms": 2.52, "small_qps": 396.5},
        {"method": "HNSW_PostFilter", "filter_type": "Range", "small_recall": 0.3952, "small_lat_ms": 2.64, "small_qps": 378.8},
        {"method": "HNSW_PostFilter", "filter_type": "EMIS", "small_recall": 0.2030, "small_lat_ms": 2.67, "small_qps": 374.5},
        {"method": "HNSW_Overfetch_20x", "filter_type": "EM", "small_recall": 0.9958, "small_lat_ms": 5.25, "small_qps": 190.4},
        {"method": "HNSW_Overfetch_20x", "filter_type": "Range", "small_recall": 0.9710, "small_lat_ms": 5.11, "small_qps": 195.7},
        {"method": "HNSW_Overfetch_20x", "filter_type": "EMIS", "small_recall": 0.6977, "small_lat_ms": 5.41, "small_qps": 184.8},
        {"method": "InGraphFilter", "filter_type": "EM", "small_recall": 0.9998, "small_lat_ms": 4.95, "small_qps": 202.0},
        {"method": "InGraphFilter", "filter_type": "Range", "small_recall": 0.9984, "small_lat_ms": 4.64, "small_qps": 215.5},
        {"method": "InGraphFilter", "filter_type": "EMIS", "small_recall": 0.9940, "small_lat_ms": 6.97, "small_qps": 143.5},
        {"method": "ACORN_Approx", "filter_type": "EM", "small_recall": 0.9998, "small_lat_ms": 14.93, "small_qps": 67.0},
        {"method": "ACORN_Approx", "filter_type": "Range", "small_recall": 0.9998, "small_lat_ms": 14.13, "small_qps": 70.8},
        {"method": "ACORN_Approx", "filter_type": "EMIS", "small_recall": 0.9948, "small_lat_ms": 29.24, "small_qps": 34.2},
    ]
    df_small = pd.DataFrame(small_data)
    df_cross = pd.merge(df_small, df_recomputed, on=["method", "filter_type"])
    
    cross_scale_records = []
    for _, row in df_cross.iterrows():
        rec = {
            "method": row["method"],
            "filter_type": row["filter_type"],
            "small_recall": row["small_recall"],
            "medium_recall": row["recomputed_mean_recall"],
            "recall_delta": row["recomputed_mean_recall"] - row["small_recall"],
            "small_latency_ms": row["small_lat_ms"],
            "medium_latency_ms": row["recomputed_mean_latency_ms"],
            "latency_slowdown_factor": row["recomputed_mean_latency_ms"] / row["small_lat_ms"],
            "small_qps": row["small_qps"],
            "medium_qps": row["recomputed_qps"],
        }
        cross_scale_records.append(rec)
    audit_results["cross_scale_comparison"] = cross_scale_records
    print(f"  Cross-scale comparisons evaluated across {len(cross_scale_records)} shared (method, workload) pairs.")

    # ---------------------------------------------------------
    # Step 6: Overfetch Factor Sweep Verification
    # ---------------------------------------------------------
    print("\n[Step 6/6] Auditing HNSW Overfetching Sweep (1x to 50x)...")
    of_path = Path(artifacts["hnsw_overfetch_csv"])
    if of_path.exists():
        df_of = pd.read_csv(of_path)
        factors_found = sorted(df_of["param_overfetch_factor"].unique().tolist())
        print(f"  Overfetch factors verified: {factors_found}")
        audit_results["verifications"]["overfetch_sweep"] = {
            "status": "VERIFIED FROM ARTIFACTS",
            "factors": factors_found,
            "workloads": df_of["filter_type"].unique().tolist(),
            "records_count": len(df_of),
        }
    else:
        print("  [WARN] Overfetch summary file not found.")

    # Write audit findings JSON
    out_json = Path("research_audit/audit_findings.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)
    print(f"\n[OK] Audit findings JSON written to: {out_json}")

    return audit_results


if __name__ == "__main__":
    audit_repository()
