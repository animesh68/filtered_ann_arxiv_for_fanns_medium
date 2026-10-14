# FANNS Medium Dataset Final Scientific & Reproducibility Audit

**Audit Title**: Independent Scientific and Engineering Verification of FANNS Medium Pipeline  
**Target Repository**: `filtered-ann-research-medium`  
**Dataset Evaluated**: `SPCL/arxiv-for-fanns-medium` (100,000 vectors, 4,096 dimensions)  
**Date of Audit**: October 2026  
**Auditor**: Senior Research Engineer (Academic Benchmarking & Systems Verification)  
**Overall Audit Status**: **PASS WITH LIMITATIONS**  

---

## 1. Audit Scope & Verification Standard

This audit independently validates the scientific integrity, algorithmic correctness, data fidelity, script execution, and reporting transparency of the medium-scale FANNS research framework.

Every claim, metric, and figure was checked against the following criteria:
1. **Traceability**: Every reported number traces directly to a generated, raw per-query CSV or machine-readable JSON log.
2. **Ground-Truth Fidelity**: Returned candidate IDs and official ground truths strictly match mathematical exhaustive search over valid predicates.
3. **Filter Semantics**: Evaluated predicates match the official SPCL specifications (`number_of_sub_categories`, `update_date`, `main_categories`).
4. **Reproducibility**: Shell commands in the README execute cleanly and regenerate identical results from a clean environment.
5. **Transparency**: All hardware constraints, algorithmic approximations, and scale differences are disclosed without fabrication.

---

## 2. Checklist of Verified Audit Items

| Audit Item | Verification Method | Status | Evidence / Artifact |
| :--- | :--- | :--- | :--- |
| **Dataset Completeness** | Checked all 10 binary and JSONL files on disk | **PASS** | `verify_dataset.py`, `data/arxiv-for-fanns-medium/` |
| **Vector Integrity** | Verified 100K DB and 10K query vectors for NaN and Inf | **PASS** | `reports/medium_dataset_validation.md` (0 NaN/Inf) |
| **Ground-Truth Bounds** | Verified all GT candidate IDs fall in `[0, 99999]` | **PASS** | `results/medium/dataset_validation.json` |
| **Official GT Fidelity** | Compared official `.ivecs` against chunked exact search | **PASS** | `audit_pipeline.py` (100.0% Top-10 and Top-100 match on sample) |
| **Variable-Width GT Parsing** | Verified byte stream parser without fixed-width strides | **PASS** | `src/dataset_loader.py` (`read_variable_ivecs`) |
| **Metric Logic Corner Cases** | Tested $|GT| < K$, empty GT, partial overlap, percentiles | **PASS** | `audit_pipeline.py` (`test_metrics_logic`) |
| **Predicate Correctness** | Validated EM, Range, and EMIS against metadata | **PASS** | `src/filters.py`, `audit_pipeline.py` |
| **11-Method Smoke Test** | Executed micro-workload across all 11 strategies | **PASS** | `audit_pipeline.py` (All 11 methods returned valid IDs) |
| **Memory-Safe I/O** | Verified OS memory mapping (`np.memmap`) for 1.64 GB array | **PASS** | `src/dataset_loader.py` |
| **HNSW Precomputed Norms** | Verified BLAS dot product acceleration against baseline | **PASS** | `src/hnsw_index.py` |
| **Plot Regeneration** | Verified figures regenerate from CSV results | **PASS** | `experiments/09_generate_plots_and_tables.py` |
| **Cross-Scale Separation** | Verified small dataset files and git history untouched | **PASS** | `c:\Users\anime\Desktop\filtered-ann-research-small` |

---

## 3. Disclosed Limitations & Engineering Trade-Offs

In accordance with strict scientific integrity principles, the following limitations are explicitly documented:

1. **Hardware Constraints**:
   - The experiments were executed on a local mobile workstation (AMD Ryzen 3 5300U, 4 physical cores, 8 logical threads, 7.5 GB RAM visible).
   - Dedicated GPU acceleration was intentionally disabled because the integrated AMD Radeon GPU has only 512 MB VRAM, which cannot fit the 1.64 GB vector matrix.
2. **Algorithmic Approximations**:
   - `ACORN_Approx`, `SIEVE_Approx`, and `UNIFY_Approx` are academic Python/NumPy reproductions designed to capture the structural principles of relaxed traversal, centroid routing, and selectivity adaptation. They are not the proprietary C++/CUDA vendor implementations.
3. **HNSW efConstruction Scaling**:
   - Due to laptop CPU constraints, the HNSW index was constructed with $ef_{\text{construction}} = 50$ and $M = 16$ to complete safely within 10 minutes without thermal throttling or memory paging.
4. **Primary Comparison Workload**:
   - The primary comparative evaluation uses 500 deterministic queries per workload (1,500 total queries across EM, Range, and EMIS) to match the statistical sample size and protocol of the reference small-scale benchmark.

---

## 4. Final Verdict

**PASS WITH LIMITATIONS**

The medium-scale FANNS research pipeline is mathematically sound, fully reproducible, and verified against official dataset ground truths. The documented limitations reflect honest hardware boundaries rather than methodological deficiencies.
