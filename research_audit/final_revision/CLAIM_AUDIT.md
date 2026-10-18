# Comprehensive Scientific Claim Audit (Phase A)

**Document Under Audit**: `research_audit/final_revision/paper_draft_original_backup.md`  
**Working Directory**: `research_audit/final_revision/`  
**Auditor**: Independent Scientific Co-Author & Systems Experimental Auditor  
**Date**: October 2026  

---

## 1. Audit Framework & Classification

This document traces every key numerical, methodological, causal, and novelty claim in `paper_draft.md` directly to primary raw CSV outputs, benchmark configurations, or official audit artifacts. Each finding is classified under:

- **Critical**: Invalidates a major conclusion or a central result; asserts unproven topological properties, claims universal dominance contradicted by raw evidence, or presents confounded cross-scale comparisons as pure causal effects.
- **Major**: Materially affects correctness, interpretation, reproducibility, or novelty; overstates an empirical trend as a mathematical impossibility, frames hand-tuned heuristics as novel query planners, or omits baseline superiority.
- **Minor**: Clarity, technical terminology, reporting variance, or citation improvements.

---

## 2. In-Depth Investigation of Targeted Risk Areas

### Risk A: Overfetch and Empirical Saturation
- **Claim & Location**:
  - Abstract (Line 14): *"candidate overfetching hits a structural ceiling, where expanding the retrieval candidate pool by $50\times$ only recovers recall to $0.5140$ at a $9.5\times$ latency penalty."*
  - Section 6.1 (Line 145): *"This empirically confirms that overfetching encounters an impassable saturation ceiling when filtered attributes do not co-locate with vector clusters."*
  - Section 10 (Line 279): *"candidate overfetching hits a rigid mathematical saturation ceiling ($51.4\%$ recall at $50\times$)."*
- **Evidence Source**:
  - `results/hnsw_overfetch/hnsw_overfetch_summary.csv` (Row 19): `HNSW_Overfetch_50.0x, EMIS, k=10, num_queries=500, mean_recall=0.514, mean_latency_ms=46.1825`.
  - Naive PostFilter latency: $4.84\text{ ms}$ (in `benchmark_summary.csv`) or $7.17\text{ ms}$ (in `hnsw_overfetch_summary.csv`).
- **Verdict**: **PARTIALLY SUPPORTED (OVERSTATED LANGUAGE)**.
  - The number ($0.5140$ Recall@10 at $50\times$ on EMIS) is verified from raw data.
  - However, labeling this as an *"impassable saturation ceiling"* or *"rigid mathematical saturation ceiling"* is scientifically indefensible. The experiment evaluated only a single parameter sweep ($\omega \in [1, 50]$) on a single index ($M=16, ef_C=50, ef_S=\max(50, 500)$). If $\omega=200$ ($k_{\text{fetch}}=2,000$) or an index with $M=64$ were tested, recall would continue to rise.
- **Required Correction**:
  - Replace *"impassable mathematical saturation ceiling"* with *"empirical diminishing returns were observed up to $50\times$ overfetch under the evaluated configuration ($M=16, ef_{\text{search}}=\max(50, k_{\text{fetch}})$)"*.
  - Disclose that higher overfetch multipliers or alternative graph construction topologies were not exhaustively evaluated.
- **Additional Experiments Needed**: None required if language is strictly qualified.

---

### Risk B: Adaptive Router Performance & PreFilter Dominance
- **Claim & Location**:
  - Abstract (Line 16): *"the router improves recall from $0.8858$ to $0.8918$, reduces mean latency by $13.5\%$ ($214.4\text{ ms} \to 185.6\text{ ms}$), and compresses P99 tail latency by $127.1\text{ ms}$ ($929.95\text{ ms} \to 802.85\text{ ms}$)"*
  - Section 8.3 (Lines 206–224, Table 4): Reports PreFilter, InGraph, and Router across EM, Range, and EMIS.
- **Evidence Source**:
  - `research_audit/followup_runs/EXP03_SUMMARY.csv`, `research_audit/followup_runs/EXP03_RAW.csv`.
  - Audited Values:
    - **EM**: PreFilter Recall = $1.0000$, Mean Latency = $310.13\text{ ms}$; Router Recall = $0.9380$, Mean Latency = $14.11\text{ ms}$.
    - **Range**: PreFilter Recall = $1.0000$, Mean Latency = $337.45\text{ ms}$; Router Recall = $0.9304$, Mean Latency = $23.64\text{ ms}$.
    - **EMIS**: PreFilter Recall = **$1.0000$**, Mean Latency = **$117.80\text{ ms}$**, P95 = **$227.74\text{ ms}$**, P99 = **$265.20\text{ ms}$**;  
      Router Recall = **$0.8918$**, Mean Latency = **$185.57\text{ ms}$**, P95 = **$661.60\text{ ms}$**, P99 = **$802.85\text{ ms}$**.
- **Verdict**: **PARTIALLY SUPPORTED (MISLEADING FRAMING — CRITICAL)**.
  - The arithmetic values in Table 4 are 100% accurate.
  - However, the manuscript framing compares the router almost exclusively against `InGraphFilter`, celebrating tail compression ($929.95 \to 802.85\text{ ms}$) while obscuring that **static `PreFilter` strictly dominates the router on EMIS across every single objective** (PreFilter has $1.0000$ recall, is $57\%$ faster on average, and has a $3.0\times$ lower P99 tail!).
  - Furthermore, on threshold selection, Table 5 shows that for EMIS, $\tau=10\%$ or $20\%$ yields higher recall ($0.96\text{--}0.97$) and lower latency ($54\text{--}86\text{ ms}$). The choice of $\tau=2\%\text{--}5\%$ is a hand-tuned global compromise to avoid latency regressions on EM and Range.
- **Required Correction**:
  - Do not claim the router dominates every static method. Explicitly document PreFilter's dominance on selective EMIS queries.
  - Describe the router as an operational mixed-workload compromise: it avoids PreFilter's severe latency penalty ($>300\text{ ms}$) on broad filters while capturing modest tail reductions on ultra-selective queries.
  - Adopt cautious threshold language: *"We evaluate $\tau = 2\%\text{--}5\%$ as a conservative operating window for balancing latency across the tested workloads. This range may preserve performance on broader filters while capturing some benefits of pre-filtering on selective workloads. Higher thresholds can improve certain selective workloads but may increase latency on broader filters. The appropriate threshold depends on the expected workload mix and requires workload-specific validation."*
- **Additional Experiments Needed**: Cache micro-benchmark (Phase D) to determine whether execution order biased EXP-03 latencies.

---

### Risk C: Graph Traversal and Topology
- **Claim & Location**:
  - Abstract (Line 14), Section 2 (Line 27), Section 7 Title & Section 7.1 (Lines 158–169), Section 10 (Line 279): Uses *"subgraph isolation"* to describe traversal expansion.
- **Evidence Source**:
  - `results/controlled_benchmark/all_queries_raw_results.csv`: InGraph visited nodes: mean $2,316.73$ (EM) vs. $18,530.28$ (EMIS).
- **Verdict**: **UNSUPPORTED TOPOLOGICAL DIAGNOSIS (CRITICAL)**.
  - The measured data records `candidate_count` / `nodes_visited`. It shows that beam search explores $18.5\%$ of the entire index on EMIS.
  - The project did **not** perform graph connectivity analysis (no connected component counts, diameter, or edge cuts of $G[\mathcal{S}_{\mathcal{P}}]$). Claiming the graph is "isolated" or "disconnected" is unproven speculation.
- **Required Correction**:
  - Replace *"subgraph isolation"* with *"traversal expansion under attribute sparsity"*.
  - Clearly distinguish observed telemetry (visited node counts and latency) from hypothesized navigation dynamics (beam search wandering through low-distance invalid nodes).
- **Additional Experiments Needed**: None required if speculative claims are retracted to match telemetry.

---

### Risk D: Cross-Scale Comparison
- **Claim & Location**:
  - Abstract (Line 12), Section 2 (Line 33), Section 5 / Table 1 (Lines 111–134): Compares $1K$ and $100K$ scale performance and attributes degradation to dataset scaling.
- **Evidence Source**:
  - Small repository `stratified_selectivity_summary.csv` vs. Medium `results/controlled_benchmark/stratified_selectivity_summary.csv`.
  - Mean Selectivity:
    - **EM**: $47.9\%$ (1K) vs. $38.5\%$ (100K)
    - **Range**: $51.2\%$ (1K) vs. $43.2\%$ (100K)
    - **EMIS**: **$31.9\%$ (1K) vs. $15.0\%$ (100K)** (over $2\times$ more selective; $34.4\%$ of medium EMIS queries have $\sigma \le 10\%$).
- **Verdict**: **PARTIALLY SUPPORTED (CONFOUNDED COMPARISON — CRITICAL)**.
  - The numerical results for 1K and 100K are accurately reported.
  - However, attributing the collapse of overfetching ($0.6977 \to 0.3826$) or the latency expansion of InGraph ($6.97 \to 335.34\text{ ms}$) solely to dataset size $N$ is invalid: the 100K query workload is twice as selective as the 1K workload!
- **Required Correction**:
  - Present cross-scale comparisons as *descriptive empirical evidence*, not controlled causal evidence of dataset size alone.
  - Disclose that workload selectivity drift compounds the difficulty of traversal at 100K scale.

---

### Risk E: Router Overhead Accounting
- **Claim & Location**:
  - Section 8.3 (Line 216, Table 4): Reports dispatch overhead as $0.002\text{ ms}$ (EM), $0.003\text{ ms}$ (EMIS), and $0.227\text{ ms}$ (Range).
- **Evidence Source**:
  - `research_audit/followup_runs/run_exp03.py` (Lines 105–118, 206–220).
- **Verdict**: **SUPPORTED WITH METHODOLOGICAL DETAIL (MINOR)**.
  - In `run_exp03.py`, routing overhead measures the execution time of estimating selectivity $\hat{\sigma}(\mathcal{P})$ via `meta_idx.get_selectivity(predicate)`.
  - For EM (`label == val`) and EMIS (`label in set`), selectivity estimation queries a dictionary/inverted index in $O(1)$ time ($0.002\text{--}0.003\text{ ms}$).
  - For Range (`start <= date <= end`), `meta_idx.get_selectivity` evaluates a vectorized NumPy comparison over 100,000 integer timestamps: `np.sum((self.dates >= start) & (self.dates <= end)) / 100000`, taking $0.227\text{ ms}$.
- **Required Correction**:
  - Explicitly explain the timing boundaries: routing overhead is the exact duration of predicate selectivity estimation prior to dispatch.
  - Explain why Range takes $0.227\text{ ms}$ (linear scan over 100K NumPy array) vs. $O(1)$ dictionary lookups for EM/EMIS.

---

### Risk F: Construction Parameter Ablation ($ef_C=50$ vs. $100$)
- **Claim & Location**:
  - Section 7.2 (Lines 171–185, Table 3): Reports build times ($713.89\text{ s}$ vs. $994.39\text{ s}$), recall, latency, and visited nodes ($15,860.7$ vs. $15,921.1$).
- **Evidence Source**:
  - `research_audit/followup_runs/EXP01_CONFIG.json`, `EXP01_RAW.csv`, `EXP01_SUMMARY.csv`, `hnsw_ef50_build_stats.json`, `hnsw_ef100_build_stats.json`.
- **Verdict**: **SUPPORTED BUT OVERGENERALIZED (MAJOR)**.
  - Build times, visited nodes, recall deltas, and configurations are verified.
  - Primary baseline index parameters: $M=16, ef_{\text{construction}}=50, ef_{\text{search}}=50$, seed $42$. (Note: disk cache was misnamed `hnsw_index_m16_ef100.pkl`, but official build stats confirm $ef_C=50$).
  - However, concluding that this *"definitively proves traversal expansion is a fundamental limitation of spatial proximity topologies"* from an ablation of two parameter points on 100 queries is an unscientific overreach. Moreover, $ef_C=100$ actually improved EMIS recall by $+4.2\%$ ($0.882 \to 0.924$).
- **Required Correction**:
  - Acknowledge the $+4.2\%$ recall gain from $ef_C=100$.
  - Describe the experiment as a limited ablation on the tested ArXiv embeddings and query subset. Do not claim universal structural proof across all graph topologies.

---

### Risk G: Baseline Implementation Fidelity
- **Claim & Location**:
  - Section 3.3 (Lines 79–80), Section 9 (Line 251): Labels ACORN, SIEVE, and UNIFY.
- **Evidence Source**:
  - `experiments/07_filter_aware_comparison.py`, `src/filter_aware.py`.
- **Verdict**: **NEEDS STRICT TERMINOLOGICAL REVISION (MAJOR)**.
  - The manuscript contains a disclosure in Section 3, but the methods are frequently referred to informally as "ACORN", "SIEVE", and "UNIFY".
  - The underlying code implements online 2-hop neighbor expansion (`ACORN_Approx`), sampled entry points (`SIEVE_Approx`), and dynamic $ef_{\text{search}}$ switching (`UNIFY_Approx`) on standard HNSW graphs. They do not implement the original authors' offline C++/CUDA indexing structures.
- **Required Correction**:
  - Consistently label them in all prose, tables, figures, captions, and checklists as `ACORN_Heuristic`, `SIEVE_Heuristic`, and `UNIFY_Heuristic`.
  - Reiterate that official C++/CUDA implementations and their specialized offline graph construction algorithms were not benchmarked.

---

### Risk H: Latency Discrepancy (8.58 ms vs. 7.17 ms)
- **Claim & Location**:
  - Table 1 reports PostFilter EMIS latency as **$8.58\text{ ms}$**.
  - Table 2 reports Overfetch $1\times$ EMIS latency as **$7.17\text{ ms}$**.
- **Evidence Source**:
  - `results/controlled_benchmark/benchmark_summary.csv` (Line 21): `HNSW_PostFilter, EMIS, mean_latency_ms = 8.577398`.
  - `results/hnsw_overfetch/hnsw_overfetch_summary.csv` (Line 4): `HNSW_Overfetch_1.0x, EMIS, mean_latency_ms = 7.1733438`.
- **Root Cause Analysis**:
  1. *Algorithm Parity*: As audited in `src/postfilter.py` and `src/overfetch.py`, both methods execute the exact same call: `hnsw.search_unfiltered(q_vec, k=10, ef_search=50)`.
  2. *Execution Context*:
     - `8.58 ms` was produced by `experiments/08_controlled_benchmark_all.py`, where `HNSW_PostFilter` ran inside a monolithic 11-strategy benchmark loop.
     - `7.17 ms` was produced by `experiments/04_hnsw_overfetch.py`, where `HNSW_Overfetch_1.0x` ran as the first condition in a dedicated overfetch sweep.
  3. *Conclusion*: The $1.41\text{ ms}$ discrepancy is caused by independent benchmark script executions under differing process lifetimes and system states.
- **Required Correction**:
  - Add a clear footnote to Table 2 explicitly explaining that Table 1 and Table 2 originate from separate benchmark script runs, accounting for the $1.41\text{ ms}$ execution timing variance.

---

## 3. Summary Audit Matrix of All Manuscript Claims

| Finding ID | Section & Location | Claim Topic | Classification | Audit Status | Required Action / Correction |
|:---|:---|:---|:---:|:---:|:---|
| **CLM-01** | Abstract (L14) | Overfetch 50x "structural ceiling" | **Major** | Overstated | Reframe as empirical diminishing returns up to 50x under tested config. |
| **CLM-02** | Abstract (L14), Sec 7 | "Subgraph isolation" | **Critical** | Unsupported | Replace with "traversal expansion under sparsity"; no connectivity measured. |
| **CLM-03** | Abstract (L15), Sec 7.2 | Construction ablation "proves" graph limit | **Major** | Overstated | Reframe as limited ablation; note +4.2% recall gain; visited nodes flat. |
| **CLM-04** | Abstract (L16), Sec 8 | Router Pareto dominance | **Critical** | Misleading | Disclose PreFilter's dominance on EMIS across recall (1.0 vs 0.89) and P99 tail. |
| **CLM-05** | Intro (L33), Sec 5 | Cross-scale causal attribution to scale N | **Critical** | Confounded | Disclose workload selectivity drift (31.9% at 1K vs 15.0% at 100K). |
| **CLM-06** | Intro (L36), Sec 8.2 | Novel "query planner" contribution | **Major** | Overstated | Frame as empirical crossover study, not a novel indexing algorithm. |
| **CLM-07** | Sec 3.3, Sec 9 | Baseline heuristic fidelity | **Major** | Needs Precision | Consistently label `ACORN_Heuristic`, `SIEVE_Heuristic`, `UNIFY_Heuristic`. |
| **CLM-08** | Table 1 vs Table 2 | PostFilter latency discrepancy (8.58 vs 7.17) | **Minor** | Resolved | Add footnote explaining independent benchmark executions. |
| **CLM-09** | Table 4, Sec 9 | EXP-03 execution-order caching | **Critical** | Confounded | Disclose warm page cache threat; run Phase D cache micro-benchmark. |
| **CLM-10** | Sec 8.4, Table 5 | Universal threshold optimality (2-5%) | **Major** | Overstated | Reframe as conservative mixed-workload operating window, not universal optimum. |
| **CLM-11** | Sec 8.3 | Routing overhead explanation (Range 0.227 ms)| **Minor** | Verified | Explain linear scan over 100K integer array vs O(1) hash lookups. |
| **CLM-12** | Sec 4.3 | Primary HNSW index parameters | **Minor** | Verified | Confirm M=16, efC=50, efS=50 despite misleading filename. |
