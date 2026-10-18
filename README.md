# Filtered Approximate Nearest Neighbor Search (FANNS) Benchmark & Research Framework (Medium Dataset)

An academic-grade, reproducible research and benchmarking pipeline for **Filtered Approximate Nearest Neighbor Search (FANNS)** on high-dimensional vector embeddings with metadata predicates on the official **SPCL/arxiv-for-fanns-medium (100,000 vectors, 4,096 dimensions)** dataset.

---

## 📌 Project Overview & Research Goals
This repository investigates empirical performance trade-offs between retrieval accuracy (Recall@K), query latency, throughput (QPS), and memory consumption across diverse metadata filtering regimes:
- **Exact Match (EM)**: Categorical point equality filters (`number_of_sub_categories == label`)
- **Range (R)**: Continuous interval predicates on publication timestamps (`range_start <= update_date <= range_end`)
- **Exact Match In Set (EMIS)**: Set containment / multi-value categorical membership (`label in main_categories`)

We systematically evaluate and compare 11 search strategies:
1. **Exact Filtered Search** (Mathematical ground-truth reference via chunked BLAS evaluation)
2. **Inverted-Index Pre-Filtering** (Selective candidate pruning followed by exact sub-distance search)
3. **Naive HNSW Post-Filtering** (Unconstrained geometric graph search followed by post-hoc discarding)
4. **HNSW Overfetching ($2\times, 5\times, 10\times, 20\times$)** (Candidate pool expansion prior to post-hoc filtering)
5. **In-Graph Filtered Traversal** (Single-graph traversal using non-matching nodes as topological navigation bridges)
6. **ACORN-Style Filter Traversal** (*Paper-inspired approximation: 2-hop neighborhood expansion on invalid nodes*)
7. **SIEVE-Style Entry-Point Routing** (*Paper-inspired approximation: centroid-guided localized entry point*)
8. **UNIFY-Style Selectivity-Adaptive Traversal** (*Paper-inspired approximation: selectivity-guided $ef_{\text{search}}$ adaptation*)

---

## 📂 Repository Structure

```
filtered-ann-research-medium/
├── data/
│   └── arxiv-for-fanns-medium/         # Official benchmark dataset (100K vectors, 10K queries)
│       ├── database_vectors.fvecs       # 100,000 float32 vectors (4,096 dims) [1.64 GB]
│       ├── database_attributes.jsonl    # 100,000 ArXiv paper metadata records [39 MB]
│       ├── query_vectors.fvecs          # 10,000 float32 query vectors (4,096 dims) [164 MB]
│       ├── ground_truth.ivecs           # Unfiltered ground truth (10,000 x 100 int32)
│       ├── em_query_attributes.jsonl    # Exact Match query predicates
│       ├── ground_truth_em.ivecs        # Variable-width EM filtered ground truth
│       ├── r_query_attributes.jsonl     # Range interval query predicates
│       ├── ground_truth_r.ivecs         # Variable-width Range filtered ground truth
│       ├── emis_query_attributes.jsonl  # Set-containment query predicates
│       └── ground_truth_emis.ivecs      # Variable-width EMIS filtered ground truth
├── src/
│   ├── dataset_loader.py                # Memory-mapped fvecs/ivecs/JSONL loader
│   ├── filters.py                       # Filter predicates & inverted metadata index
│   ├── exact_search.py                  # Chunked BLAS exact ground-truth searcher
│   ├── hnsw_index.py                    # Modular HNSW Graph with research hooks & serialization
│   ├── postfilter.py                    # Naive post-filtering strategy
│   ├── overfetch.py                     # Overfetching candidate multiplier strategy
│   ├── prefilter.py                     # Inverted-index pre-filtering strategy
│   ├── ingraph.py                       # In-graph single-traversal strategy
│   ├── filter_aware.py                  # ACORN, SIEVE, and UNIFY approximations
│   ├── metrics.py                       # Recall@K, percentiles, QPS, logging harness
│   ├── timing.py                        # Nanosecond-precision timing context manager
│   └── __init__.py
├── experiments/
│   ├── 01_dataset_validation.py         # Full dataset integrity, dimension, and NaN checks
│   ├── 02_exact_search.py               # Exact search benchmark
│   ├── 03_hnsw_postfilter.py            # Naive post-filtering baseline
│   ├── 04_hnsw_overfetch.py             # Overfetching multiplier sweep (1x to 50x)
│   ├── 05_prefilter.py                  # Inverted-index pre-filtering benchmark
│   ├── 06_ingraph.py                    # In-graph filtering benchmark
│   ├── 07_filter_aware_comparison.py    # ACORN, SIEVE, UNIFY comparison
│   ├── 08_controlled_benchmark_all.py   # Consolidated 16,500-query comparative benchmark
│   └── 09_generate_plots_and_tables.py  # Publication figure generator (300 DPI)
├── configs/
│   └── medium_benchmark.json            # Centralized experimental configuration snapshot
├── results/
│   ├── medium/                          # Machine-readable validation JSON and summaries
│   ├── controlled_benchmark/            # Per-query CSV logs and aggregate summaries
│   └── hnsw_index_m16_ef100.pkl         # Serialized HNSW graph topology
├── reports/
│   ├── MEDIUM_MIGRATION_PLAN.md         # Initial audit and migration specification
│   ├── medium_dataset_validation.md     # Comprehensive dataset verification report
│   ├── MEDIUM_BENCHMARK_REPORT.md       # Comprehensive academic research report
│   ├── MEDIUM_VS_SMALL_COMPARISON.md    # Small (1K) vs Medium (100K) cross-scale comparison
│   ├── MEDIUM_FINAL_AUDIT.md            # Independent reproducibility audit
│   ├── FANNS_Method_Comparison_Report.docx # Formatted Word comparison report
│   └── figures/                         # High-resolution benchmark plots
├── figures/medium/                      # Benchmark plots mirror
├── research_audit/
│   ├── final_revision/                  # Camera-ready manuscript & audited evidence
│   │   ├── paper_draft_revised.md       # Canonical 11-section revised research paper
│   │   ├── references.bib               # Verified BibTeX bibliography
│   │   ├── FINAL_READINESS_REPORT.md    # Paper readiness assessment & LaTeX gate
│   │   ├── figures/                     # Manuscript vector PDFs & 300 DPI PNGs
│   │   └── cache_microbenchmark_results/# Controlled cache-order diagnostic data
│   ├── followup_runs/                   # EXP-01 & EXP-03 raw data, logs, and indexes
│   └── archive/                         # Preserved preliminary audit & reconciliation notes
├── hpc/
│   ├── hpc_checklist.md                 # Supercomputer memory sizing & deployment checklist
│   └── slurm_job_template.sh            # Slurm batch script for cluster execution
├── build_index.py                       # Standalone HNSW index builder
├── verify_dataset.py                    # Standalone quick dataset verifier
├── audit_pipeline.py                    # Integrity test suite (metrics, smoke test, GT fidelity)
├── requirements.txt                     # Python dependencies
└── README.md
```

---

## 🚀 Quickstart & Reproduction Guide

### 1. Environment Setup
```powershell
# Clone or navigate to workspace
cd filtered-ann-research-medium

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # On Windows
# source venv/bin/activate # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Official Medium Dataset
```powershell
python download_dataset.py
```

### 3. Verify Dataset Integrity
```powershell
# Quick sanity check:
python verify_dataset.py

# Comprehensive validation (NaN, infinity, bounds, selectivity):
python experiments/01_dataset_validation.py
```

### 4. Run Pipeline Audit Suite
```powershell
python audit_pipeline.py
```

### 5. Build HNSW Graph Index (One-Time Execution)
```powershell
python build_index.py
```

### 6. Run Consolidated Controlled Benchmark
```powershell
python experiments/08_controlled_benchmark_all.py --queries 500 --k 10
```

### 7. Generate Publication Figures & Tables
```powershell
python experiments/09_generate_plots_and_tables.py
```

---

## 📊 Measured Benchmark Results (100,000 Vectors, K=10, 500 Queries/Workload)

All numbers below reflect actual measured performance on the local AMD Ryzen CPU testbed (4 physical cores / 8 logical threads, 7.33 GB visible RAM) across 16,500 evaluated queries.
- **HNSW Parameters**: $M=16, ef_{\text{construction}}=50, ef_{\text{search}}=50$, metric $=$ L2, random seed $= 42$.
- **Index Construction Ablation**: A separate controlled ablation evaluated $ef_{\text{construction}}=100$ (build time $994.39\text{ s}$ vs. $713.89\text{ s}$), confirming that doubling construction effort yields $+4.2\%$ recall on EMIS ($0.882 \to 0.924$) but does not reduce visited nodes ($15,921$ vs. $15,860$ nodes). Full report: [`research_audit/followup_runs/EXP01_REPORT.md`](research_audit/followup_runs/EXP01_REPORT.md).
- **Implementation Fidelity Notice**: ACORN-, SIEVE-, and UNIFY-style methods in this repository are educational Python heuristic baselines evaluating online multi-hop traversal and entry routing on standard HNSW graphs, not official C++/CUDA implementations from the original authors.

| Strategy | EM Recall@10 | EM Latency | Range Recall@10 | Range Latency | EMIS Recall@10 | EMIS Latency | Mean Throughput |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **ExactSearch** | **1.0000** | 310.57 ms | **1.0000** | 359.96 ms | **1.0000** | 154.67 ms | 4.2 QPS |
| **PreFilter** | **1.0000** | 296.73 ms | **1.0000** | 352.28 ms | **1.0000** | 149.40 ms | 4.3 QPS |
| **HNSW_PostFilter** | 0.3322 | 4.84 ms | 0.4164 | 4.73 ms | 0.1714 | 8.58 ms | 178.3 QPS |
| **HNSW_Overfetch_2x** | 0.6160 | 4.55 ms | 0.5872 | 4.46 ms | 0.1888 | 7.74 ms | 191.0 QPS |
| **HNSW_Overfetch_5x** | 0.7910 | 4.42 ms | 0.7080 | 4.64 ms | 0.2292 | 8.36 ms | 187.1 QPS |
| **HNSW_Overfetch_10x** | 0.8814 | 6.85 ms | 0.8198 | 7.45 ms | 0.2916 | 12.62 ms | 119.8 QPS |
| **HNSW_Overfetch_20x** | 0.9404 | 12.30 ms | 0.8970 | 13.61 ms | 0.3826 | 21.88 ms | 66.8 QPS |
| **InGraphFilter** | **0.9374** | **13.99 ms** | **0.9304** | **24.14 ms** | **0.8858** | **335.34 ms** | **38.6 QPS** |
| **ACORN_Approx** | **0.9784** | 175.23 ms | **0.9662** | 202.74 ms | **0.9104** | 1815.06 ms | 3.7 QPS |
| **SIEVE_Approx** | 0.9386 | 18.75 ms | 0.9282 | 36.81 ms | 0.8870 | 347.45 ms | 27.8 QPS |
| **UNIFY_Approx** | 0.9384 | 106.55 ms | 0.9312 | 108.71 ms | 0.8968 | 1983.41 ms | 6.4 QPS |

*Note on Overfetch 50x (evaluated in `experiments/04_hnsw_overfetch.py`)*: Even expanding candidates to $k_{fetch}=500$ ($50\times$) only recovers EMIS recall to **0.5140** (at 46.18 ms latency), highlighting the fundamental recall ceiling of post-filtering when queries contain restrictive metadata constraints.

---

## 🔀 Validated Selectivity-Aware Query Router (`EXP-03`)

A lightweight dynamic router switching between PreFilter (when estimated selectivity $\sigma \le 2\%$) and InGraphFilter (when $\sigma > 2\%$) was empirically validated across all 500 queries per workload ([`research_audit/followup_runs/EXP03_REPORT.md`](research_audit/followup_runs/EXP03_REPORT.md)):
- **EM**: $0.9380$ recall at $14.11\text{ ms}$ ($70.9\text{ QPS}$), $0.002\text{ ms}$ routing overhead.
- **Range**: $0.9304$ recall at $23.64\text{ ms}$ ($42.3\text{ QPS}$), $0.227\text{ ms}$ routing overhead.
- **EMIS**: $0.8918$ recall ($+0.60\%$ over InGraph) at $185.57\text{ ms}$ ($13.5\%$ faster than InGraph's $214.43\text{ ms}$ in EXP-03), compressing P99 tail latency by **$127.1\text{ ms}$** ($929.95\text{ ms} \to 802.85\text{ ms}$).
- **Generalization**: Validated on a 50/50 Train/Test split; operating range of $2\% \le \tau \le 5\%$ generalizes out-of-sample ([`research_audit/followup_runs/ROUTER_THRESHOLD_ANALYSIS.md`](research_audit/followup_runs/ROUTER_THRESHOLD_ANALYSIS.md)).

---

## 📈 Visualizations & Trade-Off Curves
Generated plots are saved at 300 DPI under `reports/figures/` and `figures/medium/`:
1. `recall_vs_selectivity.png`: Recall@10 stratified across selectivity quantiles.
2. `recall_vs_latency_tradeoff.png`: Pareto frontier on the challenging EMIS set-containment workload.
3. `qps_comparison.png`: Throughput comparison across methods and filter regimes.
4. `overfetch_sensitivity.png`: Recall recovery vs. latency cost across overfetch multipliers ($1\times$ to $50\times$).

---

## 🔍 Small (1K) vs Medium (100K) Architectural Analysis

1. **L3 Cache Cliff**: Small-scale (1,000 vectors / 16.4 MB) fits inside the CPU cache hierarchy. Medium-scale (100,000 vectors / 1.64 GB) requires streaming from main DDR4 memory, exposing the true I/O and memory-bandwidth cost of linear pre-filtering.
2. **Shift of the Selectivity Crossover**: On the small dataset, pre-filtering was faster than graph traversal up to $20\%$ selectivity. At 100K scale, a $20\%$ selectivity filter evaluates 20,000 candidates ($328 \text{ MB}$), causing the crossover point to shift leftward to **$\approx 2\%\text{--}5\%$ selectivity**.
3. **Graph Traversal Scalability & Subgraph Isolation**: On the medium dataset, `InGraphFilter` maintains high recall across workloads ($0.9374$ on EM, $0.9304$ on Range, $0.8858$ on EMIS). However, on selective workloads (EMIS), unguided entry points force traversal to explore filter-sparse neighborhoods, visiting an average of **$18,530$ nodes out of 100,000 ($18.5\%$)** and expanding mean query latency to **$335.34\text{ ms}$** (or $214.43\text{ ms}$ under warm cache in EXP-03), demonstrating the breakdown of logarithmic scaling under attribute sparsity.

---

## ⚙️ Hardware Environment & Measured Specifications
- **CPU**: AMD Ryzen Processor (Family 23 Model 104, 4 physical cores, 8 logical threads, 2.10 GHz base)
- **RAM**: 7,682,164 KB (~7.33 GB visible physical RAM)
- **Vector Storage**: Read-only OS memory mapping (`np.memmap`)
- **Peak RSS**: ~1.75 GB during full exact-distance matrix operations
- **Execution Architecture**: Strictly CPU-based (integrated GPU dedicated VRAM is 512 MB, insufficient for 1.64 GB vectors)

---

## 📝 Scientific Integrity & Audit Trail
- Working Revised Manuscript: [`research_audit/final_revision/paper_draft_revised.md`](research_audit/final_revision/paper_draft_revised.md)
- Final Readiness & Verification Report: [`research_audit/final_revision/FINAL_READINESS_REPORT.md`](research_audit/final_revision/FINAL_READINESS_REPORT.md)
- Claim-by-Claim Audit: [`research_audit/final_revision/CLAIM_AUDIT.md`](research_audit/final_revision/CLAIM_AUDIT.md)
- Numerical Consistency Audit: [`research_audit/final_revision/NUMERICAL_CONSISTENCY_AUDIT.md`](research_audit/final_revision/NUMERICAL_CONSISTENCY_AUDIT.md)
- Cache Micro-Benchmark Methodology: [`research_audit/final_revision/cache_microbenchmark_results/METHODOLOGY_NOTE.md`](research_audit/final_revision/cache_microbenchmark_results/METHODOLOGY_NOTE.md)
- Follow-Up Experiments Report: [`research_audit/followup_runs/FOLLOWUP_EXPERIMENTS_VERDICT.md`](research_audit/followup_runs/FOLLOWUP_EXPERIMENTS_VERDICT.md)
- Historical Audit Archive: [`research_audit/archive/`](research_audit/archive/)

---

## 📚 Citations & References
- Malkov, Yu A., and D. A. Yashunin. "Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs." *IEEE Transactions on Pattern Analysis and Machine Intelligence* 42.4 (2018): 824-836. [DOI: 10.1109/TPAMI.2018.2889473](https://doi.org/10.1109/TPAMI.2018.2889473).
- Iff, Patrick, Paul Bruegger, Marcin Chrapek, Maciej Besta, and Torsten Hoefler. "FANNS: Filtered Approximate Nearest Neighbor Search Benchmark." *arXiv preprint arXiv:2507.21989* (2025). [arXiv:2507.21989](https://arxiv.org/abs/2507.21989).
- Patel, Liana, Peter Kraft, Carlos Guestrin, and Matei Zaharia. "ACORN: Performant and Predicate-Agnostic Approximate Nearest Neighbor Search." *Proceedings of the ACM on Management of Data (SIGMOD)* 2.3 (2024): 1-27. [DOI: 10.1145/3654932](https://doi.org/10.1145/3654932).
- Gao, Zichen, et al. "High-Dimensional Filtered Vector Search with 3D Packing." *Proceedings of the VLDB Endowment* 17.11 (2024).
- Liang, Anqi, Pengcheng Zhang, Bin Yao, Zhongpu Chen, Yitong Song, and Guangxu Cheng. "UNIFY: Unified Graph Index for Filtered Vector Retrieval." *arXiv preprint arXiv:2412.06208* (2024). [arXiv:2412.06208](https://arxiv.org/abs/2412.06208).
