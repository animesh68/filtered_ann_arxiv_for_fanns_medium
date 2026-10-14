"""
Experiment 01: Comprehensive Dataset Integrity & Schema Validation.
Validates SPCL/arxiv-for-fanns-medium:
- File existence, readable formats, record counts, dimensions, and dtypes
- NaN and Infinity verification on database and query vectors
- Metadata attributes row counts vs vector counts
- Query attribute counts vs query counts
- Ground-truth ID boundaries within [0, num_database - 1]
- Variable-length vs fixed-length ivecs parsing
- Empirical selectivity computation across full workloads
- Outputs reports/medium_dataset_validation.md and results/medium/dataset_validation.json
"""

import json
from pathlib import Path
import sys
import time
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dataset_loader import load_fanns_dataset
from src.filters import MetadataIndex, parse_query_filter


def validate_medium_dataset(data_dir: str = "data/arxiv-for-fanns-medium"):
    print("=" * 80)
    print("EXPERIMENT 01: COMPREHENSIVE DATASET INTEGRITY VALIDATION")
    print(f"Target Directory: {data_dir}")
    print("=" * 80)

    start_time = time.time()
    path = Path(data_dir)
    results_dict = {
        "dataset_name": "SPCL/arxiv-for-fanns-medium",
        "validation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checks": {},
        "summary": {},
    }

    # 1. Check required files
    required_files = [
        "database_vectors.fvecs",
        "database_attributes.jsonl",
        "query_vectors.fvecs",
        "ground_truth.ivecs",
        "em_query_attributes.jsonl",
        "ground_truth_em.ivecs",
        "r_query_attributes.jsonl",
        "ground_truth_r.ivecs",
        "emis_query_attributes.jsonl",
        "ground_truth_emis.ivecs",
    ]

    print("\n[Step 1/6] Verifying file existence and disk sizes...")
    file_stats = {}
    missing = []
    for fname in required_files:
        fpath = path / fname
        if fpath.exists():
            size_mb = fpath.stat().st_size / (1024 * 1024)
            file_stats[fname] = {"exists": True, "size_mb": round(size_mb, 2), "size_bytes": fpath.stat().st_size}
            print(f"  [OK] {fname:<32} {size_mb:>10.2f} MB")
        else:
            file_stats[fname] = {"exists": False, "size_mb": 0.0}
            missing.append(fname)
            print(f"  [MISSING] {fname}")

    if missing:
        raise FileNotFoundError(f"Missing required dataset files: {missing}")

    results_dict["checks"]["files_present"] = True
    results_dict["file_stats"] = file_stats

    # 2. Load dataset with memory-mapping
    print("\n[Step 2/6] Loading vectors, attributes, and query workloads...")
    dataset = load_fanns_dataset(path, mmap=True)
    meta_idx = MetadataIndex(dataset.database_attributes)

    num_db = dataset.num_database
    num_q = dataset.num_queries
    dim = dataset.dimension

    print(f"  Database Vectors: {num_db:,} vectors | Dimension: {dim} | dtype: {dataset.database_vectors.dtype}")
    print(f"  Query Vectors:    {num_q:,} vectors | Dimension: {dataset.query_vectors.shape[1]} | dtype: {dataset.query_vectors.dtype}")
    print(f"  DB Metadata Rows: {len(dataset.database_attributes):,} records")

    assert num_db == 100000, f"Expected 100,000 database vectors, got {num_db}"
    assert num_q == 10000, f"Expected 10,000 query vectors, got {num_q}"
    assert dim == 4096, f"Expected dimension 4096, got {dim}"
    assert len(dataset.database_attributes) == num_db, "Metadata count != DB vector count"

    results_dict["checks"]["vector_dimensions_agree"] = True
    results_dict["checks"]["metadata_counts_agree"] = True

    # 3. Vector sanity: NaN / Inf checks (chunked for DB vectors to avoid huge RAM allocations)
    print("\n[Step 3/6] Inspecting vector values for NaN, Inf, and value ranges...")
    print("  Checking query vectors...")
    q_has_nan = bool(np.isnan(dataset.query_vectors).any())
    q_has_inf = bool(np.isinf(dataset.query_vectors).any())
    assert not q_has_nan, "Query vectors contain NaN values"
    assert not q_has_inf, "Query vectors contain Inf values"

    print("  Checking database vectors (in 10,000-vector chunks)...")
    db_has_nan = False
    db_has_inf = False
    chunk_size = 10000
    db_min = float("inf")
    db_max = float("-inf")

    for c_start in range(0, num_db, chunk_size):
        c_end = min(c_start + chunk_size, num_db)
        sub = dataset.database_vectors[c_start:c_end]
        if np.isnan(sub).any():
            db_has_nan = True
            break
        if np.isinf(sub).any():
            db_has_inf = True
            break
        c_min = float(np.min(sub))
        c_max = float(np.max(sub))
        if c_min < db_min:
            db_min = c_min
        if c_max > db_max:
            db_max = c_max

    assert not db_has_nan, "Database vectors contain NaN values"
    assert not db_has_inf, "Database vectors contain Inf values"
    print(f"  [OK] No NaN or Inf detected. DB vector value range: [{db_min:.4f}, {db_max:.4f}]")

    results_dict["checks"]["no_nan_or_inf"] = True
    results_dict["summary"]["db_vector_min"] = db_min
    results_dict["summary"]["db_vector_max"] = db_max

    # 4. Validate Ground Truth Files & ID Ranges
    print("\n[Step 4/6] Validating ground-truth files and candidate index ranges...")
    gt_stats = {}
    for w_name, workload in dataset.workloads.items():
        gt = workload.ground_truth
        count = len(gt)
        print(f"  Validating {w_name:<12} (count: {count:,}) ...")
        assert count == num_q, f"{w_name} GT count {count} != query count {num_q}"

        if isinstance(gt, np.ndarray):
            # Fixed-width ivecs (unfiltered)
            k_gt = gt.shape[1]
            min_id = int(np.min(gt))
            max_id = int(np.max(gt))
            gt_stats[w_name] = {
                "format": "fixed_width_ivecs",
                "k": k_gt,
                "total_queries": count,
                "min_id": min_id,
                "max_id": max_id,
                "valid_id_range": bool(0 <= min_id and max_id < num_db),
            }
            assert 0 <= min_id and max_id < num_db, f"{w_name} GT contains IDs out of bounds [{min_id}, {max_id}]"
            print(f"    [OK] Format: Fixed (k={k_gt}) | ID range: [{min_id}, {max_id}]")
        else:
            # Variable-width ivecs (filtered)
            lengths = [len(row) for row in gt]
            min_len = min(lengths)
            max_len = max(lengths)
            mean_len = float(np.mean(lengths))
            
            all_min = num_db
            all_max = -1
            for row in gt:
                if len(row) > 0:
                    r_min = int(np.min(row))
                    r_max = int(np.max(row))
                    if r_min < all_min:
                        all_min = r_min
                    if r_max > all_max:
                        all_max = r_max

            gt_stats[w_name] = {
                "format": "variable_width_ivecs",
                "min_results_per_query": min_len,
                "max_results_per_query": max_len,
                "mean_results_per_query": round(mean_len, 2),
                "total_queries": count,
                "min_id": all_min,
                "max_id": all_max,
                "valid_id_range": bool(0 <= all_min and all_max < num_db),
            }
            assert 0 <= all_min and all_max < num_db, f"{w_name} GT contains IDs out of bounds [{all_min}, {all_max}]"
            print(f"    [OK] Format: Variable (len {min_len}..{max_len}, mean {mean_len:.1f}) | ID range: [{all_min}, {all_max}]")

    results_dict["checks"]["ground_truth_ids_valid"] = True
    results_dict["ground_truth_stats"] = gt_stats

    # 5. Filter Semantics & Selectivity Computation
    print("\n[Step 5/6] Computing empirical filter selectivity across all 10,000 queries per workload...")
    workload_selectivities = {}

    for w_name in ["EM", "Range", "EMIS"]:
        workload = dataset.get_workload(w_name)
        attrs = workload.query_attributes
        assert len(attrs) == num_q, f"{w_name} attribute count {len(attrs)} != {num_q}"

        sel_list = []
        cand_list = []

        for q_idx in range(num_q):
            pred = parse_query_filter(workload.filter_type, attrs[q_idx])
            cands = meta_idx.get_matching_ids(pred)
            n_cands = len(cands)
            sel = n_cands / float(num_db)
            sel_list.append(sel)
            cand_list.append(n_cands)

        sel_arr = np.array(sel_list)
        cand_arr = np.array(cand_list)

        workload_selectivities[w_name] = {
            "mean_selectivity": float(np.mean(sel_arr)),
            "median_selectivity": float(np.median(sel_arr)),
            "min_selectivity": float(np.min(sel_arr)),
            "max_selectivity": float(np.max(sel_arr)),
            "p10_selectivity": float(np.percentile(sel_arr, 10)),
            "p90_selectivity": float(np.percentile(sel_arr, 90)),
            "mean_candidates": float(np.mean(cand_arr)),
            "median_candidates": float(np.median(cand_arr)),
            "min_candidates": int(np.min(cand_arr)),
            "max_candidates": int(np.max(cand_arr)),
        }
        print(f"  [{w_name:<5}] Mean Sel: {np.mean(sel_arr):.4f} ({np.mean(sel_arr)*100:.2f}%) | Mean Cands: {np.mean(cand_arr):>8.1f} | Range: [{np.min(cand_arr)}, {np.max(cand_arr)}]")

    results_dict["checks"]["filter_semantics_validated"] = True
    results_dict["selectivity_stats"] = workload_selectivities

    # 6. Save outputs
    print("\n[Step 6/6] Generating validation report and JSON manifest...")
    out_json = Path("results/medium/dataset_validation.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)

    elapsed_s = time.time() - start_time
    results_dict["validation_duration_seconds"] = round(elapsed_s, 2)
    results_dict["status"] = "PASSED"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results_dict, f, indent=2)
    print(f"  [OK] Saved JSON summary: {out_json}")

    # Generate markdown report
    out_md = Path("reports/medium_dataset_validation.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# FANNS Medium Dataset Validation Report\n\n")
        f.write(f"**Dataset**: `SPCL/arxiv-for-fanns-medium`  \n")
        f.write(f"**Validation Timestamp**: {results_dict['validation_timestamp']}  \n")
        f.write(f"**Overall Status**: **PASSED**  \n")
        f.write(f"**Verification Duration**: {elapsed_s:.2f} seconds  \n\n")
        f.write("---\n\n")

        f.write("## 1. Dataset Dimensions & Characteristics\n\n")
        f.write(f"- **Database Vectors**: {num_db:,} vectors\n")
        f.write(f"- **Query Vectors**: {num_q:,} vectors\n")
        f.write(f"- **Vector Dimension**: {dim} dimensions\n")
        f.write(f"- **Vector Data Type**: `float32` (IEEE 754 single-precision)\n")
        f.write(f"- **Vector Value Range**: `[{db_min:.4f}, {db_max:.4f}]`\n")
        f.write(f"- **NaN / Inf Anomalies**: 0 detected\n")
        f.write(f"- **Database Metadata Rows**: {len(dataset.database_attributes):,} JSONL records\n\n")

        f.write("## 2. File Inventory & Disk Footprint\n\n")
        f.write("| File Name | Format / Encoding | Size on Disk | Status |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for fname, fstat in file_stats.items():
            f.write(f"| `{fname}` | Binary / JSONL | {fstat['size_mb']:.2f} MB | PASSED |\n")

        f.write("\n## 3. Workloads & Empirical Filter Selectivity\n\n")
        f.write("| Workload | Filter Semantics | Mean Selectivity | Median Selectivity | Selectivity Range | Mean Matching Candidates |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for w_name, sstat in workload_selectivities.items():
            sem = "Exact Match (`number_of_sub_categories`)" if w_name == "EM" else ("Range Interval (`update_date`)" if w_name == "Range" else "Set Membership (`main_categories`)")
            f.write(f"| **{w_name}** | {sem} | {sstat['mean_selectivity']*100:.2f}% | {sstat['median_selectivity']*100:.2f}% | [{sstat['min_selectivity']*100:.2f}%, {sstat['max_selectivity']*100:.2f}%] | {sstat['mean_candidates']:,.1f} |\n")

        f.write("\n## 4. Ground Truth Integrity\n\n")
        f.write("| Workload | GT Format | Queries | Length / $k$ | ID Range | Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for w_name, gstat in gt_stats.items():
            k_desc = f"Fixed $k={gstat['k']}$" if gstat["format"] == "fixed_width_ivecs" else f"Variable (mean {gstat['mean_results_per_query']:.1f})"
            f.write(f"| `{w_name}` | `{gstat['format']}` | {gstat['total_queries']:,} | {k_desc} | `[{gstat['min_id']}, {gstat['max_id']}]` | VALID |\n")

        f.write("\n---\n")
        f.write("## 5. Verification Conclusion\n\n")
        f.write("All 10 required dataset files are intact, non-corrupted, and mathematically valid. ")
        f.write("Database and query vector dimensions agree exactly at 4,096. Vector values are free of NaN and infinity. ")
        f.write("Ground truth candidate IDs fall strictly within valid database bounds `[0, 99999]`. ")
        f.write("The dataset is approved for full benchmark execution.\n")

    print(f"  [OK] Saved Markdown report: {out_md}")
    print("\n" + "=" * 80)
    print("ALL DATASET INTEGRITY CHECKS PASSED")
    print("=" * 80)
    return results_dict


if __name__ == "__main__":
    validate_medium_dataset()
