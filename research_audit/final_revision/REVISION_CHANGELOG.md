# Manuscript Revision Changelog: Audit-Driven Corrective Changes

**Document Status**: Complete  
**Date**: October 2026  
**Auditor & Editor**: Independent Scientific Reviewer & Research Co-Author  
**Scope**: Line-by-line and section-by-section record of all corrective modifications between the unvetted original draft (`paper_draft_original_backup.md`) and the audited revised manuscript (`paper_draft_revised.md`).

---

## 1. Overview of Revision Objectives

The primary goal of this revision was to transform an unvetted draft containing promotional language, speculative causal assertions, and ungrounded claims of universal optimality into a scientifically defensible, empirical systems paper.

All changes are categorized by severity:
- **[CRITICAL]**: Fixes claims that would invalidate central conclusions or misrepresent empirical reality.
- **[MAJOR]**: Corrects methodological framing, algorithmic claims, baseline fidelity, or experimental attribution.
- **[MINOR]**: Improves terminological precision, citation metadata, formatting, or consistency.

---

## 2. Section-by-Section Changelog

### Title and Framing
- **Original**: Implied an algorithmic breakthrough with universal adaptive routing dominance.
- **Revised**: *"An Empirical Cross-Scale Study of Filtered Proximity Traversal with a Selectivity-Aware Query Router"*.
- **Classification**: **[MAJOR]**
- **Rationale**: The study is an empirical systems evaluation across 1K and 100K scales with an exploratory query-routing heuristic, not a fundamentally novel proximity graph architecture.

---

### Abstract
- **Change 1 [CRITICAL]**: Removed assertion that $50\times$ candidate overfetching encounters a "fundamental mathematical ceiling" or "topological impossibility limit."
  - *Revised*: Framed as "empirical diminishing returns" under the evaluated configuration ($M=16, efSearch=50, d=4,096$), plateauing at $\text{Recall@}10 \approx 0.5140$.
- **Change 2 [CRITICAL]**: Replaced claim that the adaptive router "dominates static baselines" with an honest disclosure of multi-objective trade-offs.
  - *Revised*: Disclosed that on the highly selective EMIS workload, static `PreFilter` strictly outperforms `AdaptiveRouter_2pct` in both recall ($1.0000$ vs. $0.8918$) and tail latency ($P99 = 265\text{ ms}$ vs. $803\text{ ms}$). Framed the router as a pragmatic mixed-workload compromise.
- **Change 3 [MAJOR]**: Replaced speculative phrase "subgraph isolation" with "traversal expansion under attribute sparsity".
- **Change 4 [MAJOR]**: Re-labeled all paper-inspired heuristic baselines to `ACORN_Heuristic`, `SIEVE_Heuristic`, and `UNIFY_Heuristic`.
- **Change 5 [MINOR]**: Included exact dataset scale ($N=100,000$, $d=4,096$) and primary query count ($N=16,500$) directly in the abstract.

---

### Section 1: Introduction & Contributions
- **Change 1 [CRITICAL]**: Replaced universal superiority framing for the query router with explicit trade-off framing.
  - *Revised*: Stated clearly that adaptive query routing does not universally surpass static methods; rather, it trades recall for throughput on broad filters while mitigating catastrophic graph stalls on selective filters.
- **Change 2 [MAJOR]**: Added explicit disclaimer on baseline fidelity.
  - *Revised*: Clarified that ACORN, SIEVE, and UNIFY evaluations in this work represent educational, paper-inspired heuristic baselines implemented in Python/NumPy, not official C++/CUDA implementations.
- **Change 3 [MAJOR]**: Reframed cross-scale comparison between 1K and 100K corpora.
  - *Revised*: Acknowledged that 1K and 100K benchmarks differ in vector dimensionality, selectivity distributions ($31.9\%$ vs. $15.0\%$), and hardware runtime, qualifying the analysis as descriptive empirical comparison rather than a strictly controlled causal isolation of scale.
- **Change 4 [MINOR]**: Enumerated four realistic, defensible contributions: (1) multi-workload empirical benchmarking; (2) empirical overfetch saturation analysis; (3) index construction parameter ablation ($efC=50$ vs. $efC=100$); (4) lightweight selectivity-aware query routing characterization.

---

### Section 2: Related Work & Verified Foundations
- **Change 1 [MAJOR]**: Audited and corrected citations for foundational papers ([1] HNSW, [2] ACORN, [3] SIEVE, [4] UNIFY, [5] FAISS, [6] ANN-Benchmarks, [7] Zhao et al. survey). Corrected publication venues and publication dates (e.g., distinguishing PVLDB 2025 for UNIFY, SIGMOD 2024 for ACORN, TPAMI 2020 for HNSW).
- **Change 2 [MAJOR]**: Added technical discussion and positioning for enterprise filtered vector search systems:
  - *Filtered-DiskANN* [8] (Gollapudi et al., WWW 2023): Discussed filtered graph indexing with reachability enhancement on SSD-resident graphs.
  - *VBASE* [9] (Zhang et al., OSDI 2023): Discussed unified relational-vector query engines, cost-based query optimization, and hardware acceleration.
  - *Milvus* [10] (Wang et al., SIGMOD 2021): Discussed distributed hybrid search, bitset iterator filtering, and multi-tenant partition routing.
- **Change 3 [MAJOR]**: Verified and cited Penrose's Random Geometric Graphs [11] (2003).
  - *Revised*: Positioned percolation theory strictly as an analogy and theoretical hypothesis for understanding traversal expansion, explicitly avoiding claiming RGG theory proves HNSW behavior.

---

### Section 3: System Architecture & Experimental Methodology
- **Change 1 [MAJOR]**: Documented complete dataset provenance and schema: 100,000 vectors, $d=4,096$, arXiv HEP title/abstract embeddings from `medium_arxiv_embeddings.npy` and metadata from `medium_arxiv_metadata.parquet`.
- **Change 2 [MAJOR]**: Documented HNSW index construction parameters: $M=16$, $efConstruction=50$, $efSearch=50$, metric = cosine similarity / inner product on unit-normalized vectors.
- **Change 3 [CRITICAL]**: Formalized Ground-Truth definition and Recall@10 calculation:
  $$\text{Recall@}10 = \frac{|\mathcal{R}_{\text{retrieved}} \cap \mathcal{R}_{\text{exact}}|}{\min(10, |\mathcal{G}|)}$$
  Documented exclusion handling for empty attribute sets ($|\mathcal{G}| = 0$).
- **Change 4 [MAJOR]**: Described the adaptive routing heuristic mathematically:
  $$\hat{\sigma}(q) = \frac{|\{i \in \mathcal{S} : \mathcal{P}_q(a_i) = \text{True}\}|}{|\mathcal{S}|}, \quad \text{Route}(q) = \begin{cases} \text{PreFilter}, & \text{if } \hat{\sigma}(q) \le \tau \\ \text{InGraphFilter}, & \text{if } \hat{\sigma}(q) > \tau \end{cases}$$
  Documented sampling strategies for exact match, inverted term index, and temporal range filters.

---

### Section 4: Experimental Results & Analysis
- **Change 1 [CRITICAL] Table 1 & Sec 4.1**:
  - Fully audited all metrics ($N=16,500$ queries) across 7 methods.
  - Labeled heuristics with explicit suffix `_Heuristic`.
  - Replaced promotional prose with balanced empirical characterization.
- **Change 2 [CRITICAL] Table 2 & Sec 4.2 (Overfetch Analysis)**:
  - Replaced "asymptotic impossibility ceiling" with "empirical diminishing returns."
  - Explained that at $50\times$ overfetch ($500$ candidates), Recall@10 on EMIS plateaus at $0.5140$ because unfiltered top-500 semantic neighbors contain fewer than 10 valid attributes when attribute selectivity is extremely low ($<1\%$).
  - Resolved PostFilter latency discrepancy: Reconciled Table 1 mean latency ($8.49\text{ ms}$) and Table 2 $1\times$ latency ($7.17\text{ ms}$) in footnote and text as independent process benchmark runs.
- **Change 3 [MAJOR] Table 3 & Sec 4.3 (Construction Parameter Ablation)**:
  - Verified $efConstruction=50$ vs. $efConstruction=100$ ablation across 1,500 queries.
  - Documented that doubling $efC$ increases build time by $+119.8\%$ ($1,770\text{ s} \to 3,892\text{ s}$) with marginal recall gain ($+0.0046$) and $+2.5\%$ higher visited nodes.
  - Replaced "subgraph isolation" with "traversal expansion under attribute sparsity".
- **Change 4 [CRITICAL] Table 4 & Sec 4.4 (Router Head-to-Head Comparison)**:
  - Audited held-out evaluation on 500 queries per workload.
  - Disclosed that on EMIS, PreFilter achieves $1.0000$ recall at $117.80\text{ ms}$ (P99 = $264.9\text{ ms}$), strictly outperforming AdaptiveRouter_2pct ($0.8918$ recall, $185.57\text{ ms}$, P99 = $803.1\text{ ms}$).
  - Characterized the router as a mixed-workload compromise that avoids catastrophic latency on broad filters ($14.11\text{ ms}$ vs. $310.13\text{ ms}$ on EM) while accepting degraded tail latency on selective filters.
- **Change 5 [MAJOR] Table 5 & Sec 4.5 (Threshold Sweep & Generalization)**:
  - Preserved tuning split ($N=1,000$) vs. held-out split ($N=500$) distinction.
  - Replaced claims of universal generalization with cautious wording: $\tau \in [2\%, 5\%]$ serves as an empirical operating window on this benchmark, requiring workload-specific calibration in other settings.
- **Change 6 [MAJOR] Table 6 & Sec 4.6 (Router Overhead Isolation)**:
  - Audited timing breakdown: EM = $0.003\text{ ms}$, Range = $0.227\text{ ms}$, EMIS = $0.003\text{ ms}$.
  - Explained the algorithmic cause of the $0.227\text{ ms}$ Range overhead: vectorized NumPy scan over 100,000 unindexed timestamps, compared to $O(1)$ inverted index lookups for EM and EMIS.

---

### Section 5: Cache Dynamics & Threats to Validity
- **Change 1 [CRITICAL] Table 7 & Sec 5.3 (Controlled Cache Micro-Benchmark)**:
  - Added new empirical micro-benchmark ($N=50$ EMIS diagnostic queries across Conditions A, B, and C).
  - Documented significant OS page-cache warming: PreFilter latency decreases by $-56.7\%$ when preceded by InGraphFilter ($315.99\text{ ms} \to 136.85\text{ ms}$).
  - Documented that interleaved execution yields $110.82\text{ ms}$, matching the full benchmark average of $117.80\text{ ms}$.
  - Disclosed cache order effects as a documented threat to internal validity in dense vector retrieval benchmarking.
- **Change 2 [MAJOR] Sec 5.1 & 5.2 (Systemic Limitations & Baseline Fidelity)**:
  - Explicitly detailed threats to validity: single-node execution, Python interpreter overhead, single dataset domain (arXiv HEP), and lack of memory hierarchy profiling.
  - Clarified that paper-inspired baselines do not reflect official compiled C++/CUDA performance.

---

### Section 6: Conclusion
- **Change 1 [CRITICAL]**: Replaced claims of "production readiness" and "universally optimal routing" with measured scientific conclusions.
- **Change 2 [MAJOR]**: Outlined concrete directions for future work: cost-based optimization integrating vector similarity estimation, hardware cache-aware graph traversal, and evaluation on multi-million scale datasets.

---

## 3. Summary of Deliverables & Revision Matrix

| Artifact | Description | Status |
| :--- | :--- | :--- |
| `paper_draft_original_backup.md` | Byte-for-byte backup of original manuscript | Preserved |
| `CLAIM_AUDIT.md` | Claim-by-claim audit covering Risks A–H | Complete |
| `RELATED_WORK_VERIFICATION.md` | Verified bibliographic metadata & technical context | Complete |
| `cache_microbenchmark.py` | Standalone reproducible cache micro-benchmark | Executed |
| `cache_microbenchmark_results/` | Raw CSVs, summary table, and methodology note | Documented |
| `paper_draft_revised.md` | 11-section revised manuscript draft | Complete |
| `figures/generate_manuscript_figures.py` | Standalone script producing Figures 1–5 (PDF & PNG) | Executed |
| `figures/*.pdf`, `figures/*.png` | 10 vector & high-res raster figure files | Verified |
| `FIGURE_AUDIT.md` | Traceability and visual evidence audit for all figures | Complete |
| `NUMERICAL_CONSISTENCY_AUDIT.md` | Verification of all numbers, sample sizes, and tables | Complete |
| `references.bib` | Verified BibTeX database ([1]–[11]) | Complete |
| `REVISION_CHANGELOG.md` | Detailed changelog of all corrective revisions | Complete |
| `FINAL_READINESS_REPORT.md` | Paper readiness assessment and LaTeX gate verdict | Complete |
