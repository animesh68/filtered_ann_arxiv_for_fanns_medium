# FANNS Medium Dataset Migration & Execution Plan

**Document ID**: `reports/MEDIUM_MIGRATION_PLAN.md`  
**Author**: Senior Research Engineer  
**Date**: October 2026  
**Status**: APPROVED & ACTIVE  
**Target Dataset**: `SPCL/arxiv-for-fanns-medium` (~100,000 vectors, 4,096 dimensions)  
**Reference Repository**: [`https://github.com/animesh68/filtered_ann_arxiv_for_fanns_small`](https://github.com/animesh68/filtered_ann_arxiv_for_fanns_small)  
**Local Reference Path**: `C:\Users\anime\Desktop\filtered-ann-research-small`  
**Workspace Path**: `C:\Users\anime\Desktop\filtered-ann-research-medium`  

---

## 1. Executive Summary & Objective

The objective of this research migration is to scale the **Filtered Approximate Nearest Neighbor Search (FANNS)** benchmarking suite from the 1,000-vector exploratory dataset (`SPCL/arxiv-for-fanns-small`) to the official 100,000-vector benchmark dataset (`SPCL/arxiv-for-fanns-medium`).

This migration preserves exact algorithmic behavior, metric definitions, evaluation protocols, and reporting formats while addressing the severe computational and memory challenges posed by scaling vector data by $100\times$ (from 16.4 MB to 1.64 GB raw float32 vectors) on a resource-constrained local PC (AMD Ryzen 3 5300U, 7.5 GB RAM, integrated graphics).

---

## 2. Reference Implementation & Audited Files

An exhaustive audit of the reference repository `filtered-ann-research-small` was conducted on 2026-10-14. The following files and configurations were inspected:

### 2.1 Core Infrastructure & Modules (`src/`)
- `dataset_loader.py`: Binary parser for standard `.fvecs`, fixed-width `.ivecs`, variable-width `.ivecs`, and JSONL metadata.
- `filters.py`: Implementation of `EMFilterPredicate`, `RangeFilterPredicate`, `EMISFilterPredicate`, and the high-performance inverted `MetadataIndex`.
- `exact_search.py`: Exhaustive filtered distance evaluator used as the mathematical reference ground truth.
- `hnsw_index.py`: Pure Python/NumPy implementation of the Hierarchical Navigable Small World (HNSW) graph with research hooks for filtering.
- `postfilter.py`: Standard HNSW search followed by post-hoc filter candidate discarding.
- `overfetch.py`: Expanded candidate retrieval ($k \cdot \text{multiplier}$) with post-hoc filtering.
- `prefilter.py`: Inverted-index candidate pruning followed by restricted sub-vector distance calculation.
- `ingraph.py`: Single-graph traversal admitting only filter-satisfying candidates into the result pool while navigating all nodes.
- `filter_aware.py`: Implementations of paper-inspired approximations:
  - `ACORNFilterSearcher`: 2-hop relaxed traversal over non-matching routing nodes.
  - `SIEVEFilterSearcher`: Centroid-based localized candidate entry-point selection.
  - `UNIFYFilterSearcher`: Dynamic selectivity-guided $ef_{\text{search}}$ adaptation.
- `metrics.py`: Calculation of `Recall@K`, `mean_latency_ms`, `median_latency_ms`, `p95_latency_ms`, `p99_latency_ms`, `QPS`, candidate counts, and stratified selectivity binning.
- `timing.py`: Nanosecond-precision `time.perf_counter_ns()` measurement harness.

### 2.2 Benchmarking Scripts (`experiments/`)
- `01_dataset_validation.py`: Data type, shape, NaN/inf, and schema validation.
- `02_exact_search.py`: Ground truth validation and baseline exact search timing.
- `03_hnsw_postfilter.py`: Baseline post-filtering degradation evaluation.
- `04_hnsw_overfetch.py`: Multiplier sweep ($1\times, 2\times, 5\times, 10\times, 20\times, 50\times$).
- `05_prefilter.py`: Inverted-index pre-filtering benchmark.
- `06_ingraph.py`: In-graph traversal benchmark.
- `07_filter_aware_comparison.py`: ACORN, SIEVE, and UNIFY comparison.
- `08_controlled_benchmark_all.py`: Consolidated 16,500-query benchmark over 11 strategies and 3 workloads.
- `09_generate_plots_and_tables.py`: Matplotlib publication figure generator.

### 2.3 Existing Small-Dataset Results Inspected
- `results/controlled_benchmark/benchmark_summary.csv`: Measured metrics across 11 strategies for EM, Range, and EMIS at $K=10$, $N=500$ queries/workload.
- `results/controlled_benchmark/all_queries_raw_results.csv`: 16,500 granular query execution rows.
- `results/controlled_benchmark/stratified_selectivity_summary.csv`: Selectivity-bucketed performance.

---

## 3. Experiment Matrix & Method Taxonomy

The medium benchmark will systematically evaluate the exact same 11 strategy configurations identified in the reference repository across all 3 official workloads:

### 3.1 Workloads
1. **Exact Match (EM)**: Point query on integer attribute `number_of_sub_categories == label`.
2. **Range (R)**: Interval predicate on timestamp `range_start <= update_date <= range_end`.
3. **Exact Match In Set (EMIS)**: Set containment on categorical array `label in main_categories`.

### 3.2 Strategy Matrix
| Strategy # | Method Name | Mechanism & Description |
| :--- | :--- | :--- |
| 1 | `ExactSearch` | Mathematical ground-truth baseline; evaluates exact L2 distances over all matching candidates. |
| 2 | `PreFilter` | Inverted index immediately filters candidate IDs; computes exact vector distances only on the valid candidate subset. |
| 3 | `HNSW_PostFilter` | Retrieves top-$k$ from unfiltered HNSW graph; filters candidates post-hoc. Severe recall collapse expected under low selectivity. |
| 4 | `HNSW_Overfetch_2x` | Retrieves $2k$ candidates from unfiltered HNSW; post-filters to top-$k$. |
| 5 | `HNSW_Overfetch_5x` | Retrieves $5k$ candidates from unfiltered HNSW; post-filters to top-$k$. |
| 6 | `HNSW_Overfetch_10x` | Retrieves $10k$ candidates from unfiltered HNSW; post-filters to top-$k$. |
| 7 | `HNSW_Overfetch_20x` | Retrieves $20k$ candidates from unfiltered HNSW; post-filters to top-$k$. |
| 8 | `InGraphFilter` | Traverses HNSW topology utilizing all nodes for navigation, but admits only filter-valid nodes into the result pool. |
| 9 | `ACORN_Approx` | Multi-hop neighbor expansion (2 hops) when traversing non-matching routing nodes to preserve graph connectivity. |
| 10 | `SIEVE_Approx` | Selects entry point at Layer 0 from candidate centroids satisfying the query filter rather than global entry point. |
| 11 | `UNIFY_Approx` | Selectivity-adaptive strategy scaling $ef_{\text{search}}$ (up to $4\times$) and activating multi-hop routing when selectivity $\le 10\%$. |

*Auxiliary Experiment*: 
- Overfetch factor sensitivity sweep evaluating $[1.0\times, 2.0\times, 5.0\times, 10.0\times, 20.0\times, 50.0\times]$ on selective workloads.

---

## 4. Dataset Files & Medium-Scale Specifications

Source: Hugging Face Dataset `SPCL/arxiv-for-fanns-medium`

| File Name | Record Type / Format | Expected Dimensions / Rows | Size on Disk |
| :--- | :--- | :--- | :--- |
| `database_vectors.fvecs` | Binary Float32 Vectors | $100,000 \times 4,096$ | 1,638,800,000 B (~1.64 GB) |
| `query_vectors.fvecs` | Binary Float32 Vectors | $10,000 \times 4,096$ | 163,880,000 B (~163.9 MB) |
| `database_attributes.jsonl` | JSONL Metadata Records | 100,000 records | 40,945,622 B (~39.0 MB) |
| `ground_truth.ivecs` | Binary Int32 (Fixed $k=100$) | $10,000 \times 100$ | 4,040,000 B (~3.85 MB) |
| `em_query_attributes.jsonl` | JSONL Query Attributes | 10,000 records | 130,000 B (~127 KB) |
| `ground_truth_em.ivecs` | Binary Int32 (Variable $k \le 100$) | 10,000 records | 4,038,224 B (~3.85 MB) |
| `r_query_attributes.jsonl` | JSONL Query Attributes | 10,000 records | 430,000 B (~420 KB) |
| `ground_truth_r.ivecs` | Binary Int32 (Variable $k \le 100$) | 10,000 records | 4,040,000 B (~3.85 MB) |
| `emis_query_attributes.jsonl` | JSONL Query Attributes | 10,000 records | 192,387 B (~188 KB) |
| `ground_truth_emis.ivecs` | Binary Int32 (Variable $k \le 100$) | 10,000 records | 4,035,992 B (~3.85 MB) |

**Total Dataset Size**: ~1.85 GB.

---

## 5. Configuration Differences: Small vs. Medium

| Aspect | Small Dataset (`arxiv-for-fanns-small`) | Medium Dataset (`arxiv-for-fanns-medium`) | Impact & Mitigation |
| :--- | :--- | :--- | :--- |
| **Database Vectors ($N$)** | 1,000 | 100,000 | $100\times$ candidate scale; exact search cannot be done trivially per query without chunking. |
| **Vector Memory Footprint** | 16.4 MB | 1,638.8 MB (1.64 GB) | Small fits in CPU L3 cache; medium requires OS memory mapping (`mmap`) to prevent RAM exhaustion. |
| **Metadata Record Count** | 1,000 | 100,000 | Inverted index size increases from ~100 KB to ~15 MB; vectorized boolean masks used. |
| **Exact Search Search Space** | Up to 1,000 vectors | Up to 100,000 vectors | Dot products over 100K 4096-d vectors require chunked matrix-vector products to maintain responsive latency. |
| **HNSW Construction Scale** | $N \log N \approx 10^4$ operations (9.35s) | $N \log N \approx 1.7 \times 10^6$ operations | Requires precomputed vector $L_2$ norms ($\|x\|^2$) and batched neighbor evaluations to avoid tens of hours of Python overhead. |
| **Query Evaluation Count** | 500 per workload (1,500 total queries) | 500 per workload (1,500 total queries) | Evaluated queries kept at 500 per workload for direct, apple-to-apple parity with small benchmark. |

---

## 6. Hardware & Memory Constraints

- **Host OS**: Microsoft Windows 11 (64-bit)
- **CPU**: AMD Ryzen 3 5300U with Radeon Graphics (4 physical cores, 8 logical threads, 2.60 GHz base)
- **Host RAM**: 7,682,164 KB (~7.50 GB visible)
- **Available Free RAM**: ~1.0 GB to 2.5 GB depending on active processes
- **GPU**: Integrated AMD Radeon Graphics (512 MB dedicated VRAM)
- **Python Version**: Python 3.14.6 (64-bit)
- **Disk**: Local Drive C: with ~295 GB free space

### Resource Safety Rules
1. **No Unnecessary Array Copies**: Use read-only memory mapping (`np.memmap`) for the 1.64 GB database vectors.
2. **Precomputed Vector Norms**: Compute an array of 100,000 scalar float32 norms ($\|v_i\|^2$, ~400 KB) so that squared Euclidean distance reduces to $\|q\|^2 + \|v_i\|^2 - 2 \langle q, v_i \rangle$, eliminating intermediate 4096-dim vector allocations.
3. **No GPU VRAM Overflow**: The integrated GPU has only 512 MB VRAM and cannot fit 1.64 GB vectors. Execution is strictly CPU-based.
4. **Resumable / Incremental Checkpointing**: Results will be flushed query-by-query or method-by-method to CSV so that any interruption can be resumed seamlessly without losing progress.

---

## 7. Planned Execution Order

1. **Step 1**: Repository structure and configuration initialization (`configs/medium_benchmark.json`, `.gitignore`, `requirements.txt`).
2. **Step 2**: Dataset acquisition from Hugging Face Hub (`download_dataset.py`).
3. **Step 3**: Data verification and integrity checks (`verify_dataset.py`, `experiments/01_dataset_validation.py`).
4. **Step 4**: Official ground-truth verification on deterministic query sample (`audit_pipeline.py`).
5. **Step 5**: Smoke test on micro-workload (10 queries across all 11 strategies) to verify pipeline correctness.
6. **Step 6**: Comprehensive benchmark execution across all 3 workloads and 11 strategies (`experiments/08_controlled_benchmark_all.py`).
7. **Step 7**: Auxiliary overfetch sweep experiment (`experiments/04_hnsw_overfetch.py`).
8. **Step 8**: Figure and publication table generation (`experiments/09_generate_plots_and_tables.py`).
9. **Step 9**: Comparative analysis documentation (`reports/MEDIUM_VS_SMALL_COMPARISON.md`, `reports/MEDIUM_BENCHMARK_REPORT.md`).
10. **Step 10**: Comprehensive README creation matching the reference repository style.
11. **Step 11**: Independent final scientific audit (`reports/MEDIUM_FINAL_AUDIT.md`).

---

## 8. Known Implementation Limitations & Integrity Disclosures

1. **ACORN-Style Traversal**: Implemented as a research approximation expanding 2 hops over invalid routing nodes. This captures the topological relaxation principle of Patel et al. (SIGMOD 2024) but is not the C++/CUDA ACORN repository.
2. **SIEVE-Style Routing**: Implemented as centroid-based entry-point selection over valid candidate nodes (Gao et al., VLDB 2024).
3. **UNIFY-Style Adaptation**: Implemented as selectivity-adaptive efSearch and multi-hop routing activation (Zhang et al., 2024).
4. **Sampled Workload**: Primary benchmark evaluates 500 queries per workload ($N_{\text{queries}}=1,500$ across 3 workloads) identically to the small-dataset protocol, preserving exact statistical equivalence.
5. **Hardware**: Benchmark runs on commodity laptop CPU (AMD Ryzen 3 5300U) rather than a multi-socket server or HPC cluster. Absolute latencies will reflect this environment and should be interpreted relative to the baselines.
