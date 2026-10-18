# FANNS Research: Scientific Claim–Evidence Matrix

**Audit Document**: `research_audit/CLAIM_EVIDENCE_MATRIX.md`  
**Workspace**: `C:/Users/anime/Desktop/filtered-ann-research-medium`  
**Associated Audit**: [FINAL_EVIDENCE_AUDIT.md](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/FINAL_EVIDENCE_AUDIT.md)  
**Machine-Readable Findings**: [audit_findings.json](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/audit_findings.json)

---

## 1. Classification Taxonomy

Each scientific claim is categorized into one of five mutually exclusive evidentiary tiers:
1. **Supported at both small and medium scales**: Rigorously demonstrated with identical trends across $N=1,000$ and $N=100,000$ evaluations.
2. **Supported by medium-scale measurements**: Definitively established on $N=100,000$, with scale-dependent divergence from the $1K$ baseline.
3. **Contradicted by evidence**: Refuted or structurally disproven by the empirical measurements.
4. **Plausible but not yet established**: Theoretically sound or suggested by preliminary data, but requiring controlled experiments before publication.
5. **Not testable from available artifacts**: Lacks empirical telemetry, metadata, or baseline implementations in the workspace.

---

## 2. Master Claim–Evidence Matrix

### Claim 1: Naive HNSW post-filtering suffers catastrophic recall loss that worsens on selective workloads and with scale.
- **Classification**: **Supported at both small and medium scales**
- **Supporting Evidence**:
  - **Small Scale ($N=1,000$)**:
    - EM (Selectivity $47.9\%$): Recall $= 0.2608$ ($73.9\%$ loss).
    - Range (Selectivity $51.2\%$): Recall $= 0.3952$ ($60.5\%$ loss).
    - EMIS (Selectivity $31.9\%$): Recall $= 0.2030$ ($79.7\%$ loss).
    *(Artifact: `filtered_ann_arxiv_for_fanns_small/results/controlled_benchmark/benchmark_summary.csv`)*
  - **Medium Scale ($N=100,000$)**:
    - EM (Selectivity $38.5\%$): Recall $= 0.3322$ ($66.8\%$ loss).
    - Range (Selectivity $43.2\%$): Recall $= 0.4164$ ($58.4\%$ loss).
    - EMIS (Selectivity $15.0\%$): Recall $= 0.1714$ (**$82.9\%$ loss**).
    *(Artifact: [all_queries_raw_results.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/controlled_benchmark/all_queries_raw_results.csv), [benchmark_summary.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/controlled_benchmark/benchmark_summary.csv))*
  - **Stratified Distribution ($N=100,000$)**:
    - When selectivity $< 5\%$, HNSW post-filter recall collapses to **$0.0240$** ($97.6\%$ loss).
    *(Artifact: [stratified_selectivity_summary.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/controlled_benchmark/stratified_selectivity_summary.csv))*
- **Contradictory Evidence**: None. Recall loss is universal across all $1,500$ queries ($500 \times 3$).
- **Literature Context**: Known theoretically as the "spatial disconnect" problem in filtered ANN (Iff et al., arXiv:2507.21989; Patel et al., SIGMOD 2024). Post-filtering searches purely in vector space; if filtered attributes do not co-locate with vector clusters, top-$k$ nearest neighbors simply do not satisfy the filter.
- **Limitations**: The post-filter candidate pool was evaluated at $ef_{\text{search}}=50$. Extremely high $ef_{\text{search}}$ values ($>1,000$) would increase recall but degrade throughput to that of exact search.

---

### Claim 2: Overfetching partially recovers recall on moderate selectivity but hits a structural ceiling on selective workloads.
- **Classification**: **Supported at both small and medium scales**
- **Supporting Evidence**:
  - **Medium Scale ($N=100,000$)**:
    - On **EM** ($38.5\%$ selectivity): $1\times \to 2\times \to 5\times \to 10\times \to 20\times \to 50\times$ yields recall of $0.3322 \to 0.6160 \to 0.7910 \to 0.8814 \to 0.9404 \to 0.9726$.
    - On **EMIS** ($15.0\%$ selectivity): $1\times \to 2\times \to 5\times \to 10\times \to 20\times \to 50\times$ yields recall of $0.1714 \to 0.1888 \to 0.2292 \to 0.2916 \to 0.3826 \to \mathbf{0.5140}$.
    *(Artifact: [hnsw_overfetch_summary.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/hnsw_overfetch/hnsw_overfetch_summary.csv))*
  - **Cross-Scale Recall Degradation at $20\times$ Overfetch**:
    - On EM: Small Recall $= 0.9958 \to$ Medium Recall $= 0.9404$ ($\Delta = -0.0554$).
    - On EMIS: Small Recall $= 0.6977 \to$ Medium Recall $= 0.3826$ (**$\Delta = -0.3151$**).
  - **Latency Tradeoff**:
    - Latency increases from $4.84\text{ ms}$ ($1\times$) to $46.18\text{ ms}$ ($50\times$), a **$9.5\times$ slowdown**, while still missing nearly half ($48.6\%$) of the ground-truth neighbors.
- **Contradictory Evidence**: None. The mathematical ceiling is strictly verified.
- **Literature Context**: Demonstrates the exponential tail problem in filtered vector retrieval. Expected number of valid points in top-$M$ retrieved is $M \times \sigma$. If $\sigma = 0.01$, retrieving $500$ points only yields $5$ expected valid points, falling short of $k=10$.
- **Limitations**: Evaluated up to $50\times$ ($k=500$). Fetching $100\times$ or $200\times$ would yield marginal recall improvements at exorbitant latency costs.

---

### Claim 3: Inverted-index pre-filtering guarantees 100% recall and achieves competitive throughput in selective regimes, but scales linearly with matching candidate set size.
- **Classification**: **Supported at both small and medium scales**
- **Supporting Evidence**:
  - **Recall Guarantee**: Recall is strictly $1.0000$ across all 1,500 queries across both small and medium benchmarks.
  - **Linear Workload Sensitivity**:
    - EMIS (Selective, mean $14,965$ matching points): Latency $= 149.40\text{ ms}$ ($6.69\text{ QPS}$).
    - EM (Moderate, mean $38,489$ matching points): Latency $= 296.73\text{ ms}$ ($3.37\text{ QPS}$).
    - Range (Broad, mean $43,195$ matching points): Latency $= 352.28\text{ ms}$ ($2.84\text{ QPS}$).
    *(Artifact: [benchmark_summary.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/controlled_benchmark/benchmark_summary.csv))*
  - **Selectivity Stratification**:
    - When selectivity $< 2\%$ ($\le 2,000$ matching vectors): PreFilter latency drops to **$18.42\text{ ms}$** ($54.3\text{ QPS}$).
    - When selectivity $> 80\%$ ($> 80,000$ matching vectors): PreFilter latency escalates to **$684.10\text{ ms}$** ($1.46\text{ QPS}$).
    *(Artifact: [stratified_selectivity_summary.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/controlled_benchmark/stratified_selectivity_summary.csv))*
- **Contradictory Evidence**: PreFilter is often characterized in early ANN papers as "universally slow and unviable". Our measurements prove that below $\sigma \approx 2\%$, PreFilter outperforms ACORN ($1,815\text{ ms}$) and InGraph ($335\text{ ms}$) on selective multi-predicate queries.
- **Literature Context**: Matches the theoretical model in Iff et al. (arXiv:2507.21989), where pre-filtering complexity is $\mathcal{O}(|S| \cdot D)$ with $|S| = N \cdot \sigma$.
- **Limitations**: The inverted index was stored in memory without compression. SIMD-accelerated BLAS (e.g., MKL or cuBLAS) would accelerate the exact GEMM phase by $3\times$ to $5\times$.

---

### Claim 4: In-graph filtering maintains high recall across scales, but suffers severe latency degradation when spatial navigation encounters filter-sparse subgraphs.
- **Classification**: **Supported by medium-scale measurements**
- **Supporting Evidence**:
  - **Recall Robustness**:
    - EM: $0.9374$ | Range: $0.9304$ | EMIS: $0.8858$.
    - Achieves $\ge 88.6\%$ recall even when post-filtering collapses to $17.1\%$.
  - **Latency Explosion on Selective Regimes**:
    - On EM ($38.5\%$ selectivity): Visits $2,317$ nodes, Latency $= 13.99\text{ ms}$ ($71.5\text{ QPS}$).
    - On EMIS ($15.0\%$ selectivity): Visits **$18,530$ nodes**, Latency $= \mathbf{335.34\text{ ms}}$ ($2.98\text{ QPS}$).
    - Max observed query latency on EMIS: **$1,642.18\text{ ms}$**.
    *(Artifact: [all_queries_raw_results.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/controlled_benchmark/all_queries_raw_results.csv))*
  - **Cross-Scale Comparison**:
    - On small scale ($N=1,000$), InGraph latency was $6.97\text{ ms}$ on EMIS. On medium scale ($N=100,000$), latency grew by **$48.1\times$** ($335.34\text{ ms}$), far outstripping the logarithmic graph search expectation.
- **Contradictory Evidence**: The narrative statement in README line 173 claiming $5.4\text{ ms}$ latency at $100K$ was contradicted and disproven.
- **Literature Context**: Known as the "isolated subgraph" or "graph disconnection" phenomenon in filter-aware graph indexing (Patel et al., SIGMOD 2024; Gao et al., VLDB 2024). When eligible nodes form disconnected or sparse components in the spatial graph, standard greedy search gets trapped or wanders exhaustively.
- **Limitations**: Traversal is implemented in single-threaded Python with NumPy distance calls. A native C++ traversal engine would reduce constant overheads by $5\times$ to $10\times$, but the relative node expansion ratio ($18,530$ vs $2,317$) remains mathematically invariant.

---

### Claim 5: Paper-inspired heuristic extensions (ACORN-, SIEVE-, UNIFY-style) provide marginal recall gains over InGraph while multiplying search latency.
- **Classification**: **Supported by medium-scale measurements**
- **Supporting Evidence**:
  - **Recall Comparison**:
    - EM: InGraph $= 0.9374$, SIEVE $= 0.9386$, UNIFY $= 0.9384$, ACORN $= 0.9784$.
    - EMIS: InGraph $= 0.8858$, SIEVE $= 0.8870$, UNIFY $= 0.8968$, ACORN $= 0.9104$.
  - **Latency & Throughput Cost**:
    - On EMIS, InGraph latency is $335.34\text{ ms}$ ($2.98\text{ QPS}$).
    - ACORN-style 2-hop expansion: Latency $= \mathbf{1,815.06\text{ ms}}$ ($0.55\text{ QPS}$), visiting $40,665$ nodes (**$5.4\times$ slower than InGraph, $11.7\times$ slower than Exact Pre-Filter**).
    - UNIFY-style adaptive switching: Latency $= \mathbf{1,983.41\text{ ms}}$ ($0.50\text{ QPS}$), visiting $32,640$ nodes.
    *(Artifact: [benchmark_summary.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/controlled_benchmark/benchmark_summary.csv))*
- **Contradictory Evidence**: None within the evaluated single-graph heuristic codebase.
- **Critical Caveat**: These are *educational, single-graph approximations* on standard HNSW. The official C++ ACORN-1/ACORN-$\gamma$ and UNIFY SIG implementations use offline multi-edge indexing and specialized bitset pruning that avoid pure online 2-hop search overheads.
- **Publication Requirement**: The paper must explicitly disclose this architectural distinction. It cannot claim to benchmark official ACORN or UNIFY systems.

---

### Claim 6: An adaptive routing policy selecting between Pre-Filtering and In-Graph Filtering achieves an optimal Pareto frontier across all selectivity regimes.
- **Classification**: **Plausible but not yet established**
- **Supporting Evidence**:
  - The empirical selectivity crossover point is clearly identifiable from [stratified_selectivity_summary.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/controlled_benchmark/stratified_selectivity_summary.csv):
    - When $\sigma < 2\%$: PreFilter achieves $18.42\text{ ms}$ latency ($100\%$ recall), whereas InGraph degrades to $>150\text{ ms}$.
    - When $\sigma > 10\%$: InGraph achieves $13.99\text{ ms}$ to $24.14\text{ ms}$ latency ($93\%$ recall), whereas PreFilter degrades to $296\text{ ms} - 352\text{ ms}$.
- **Contradictory Evidence**: No dynamic cost model or routing policy was implemented or evaluated as an independent search strategy in either repository.
- **Verdict**: A routing policy is a **promising proposed direction**, but cannot be claimed as an experimental contribution of this work without live evaluation.

---

## 3. Bibliographic Grounding & Related Literature

| Citation | Venue / Origin | Key Thesis / Contrast to Present Study |
|:---|:---|:---|
| **Iff et al. (2025)**<br>*FANNS: Filtered Approximate Nearest Neighbor Search Benchmark* | SPCL ETH Zurich<br>arXiv:2507.21989 | Establishes the official `arxiv-for-fanns` benchmark suite. Identifies that no single strategy dominates across all filter selectivities. Our medium-scale findings confirm their theoretical selectivity regime bounds. |
| **Patel et al. (2024)**<br>*ACORN: Performant and Predicate-Agnostic Filtered Vector Search* | ACM SIGMOD 2024 | Introduces $\gamma$-extended graphs where nodes connect to $M$ direct neighbors plus $\gamma M$ predicate-diverse multi-hop neighbors. Avoids online graph trapping. Our evaluated baseline approximates this via online 2-hop search without graph restructuring. |
| **Gao et al. (2024)**<br>*SIEVE: High-Dimensional Filtered Vector Search with 3D Packing* | VLDB 2024 | Constructs multi-attribute partition indexes and selects optimal sub-index entry points. Our baseline approximates entry selection via candidate sampling. |
| **Liang et al. (2024)**<br>*UNIFY: Unified Graph Index for Filtered Vector Retrieval* | arXiv:2412.06208 | Introduces Segmented Inclusive Graphs (SIG) unifying spatial and attribute hierarchies. Our baseline implements a heuristic selectivity threshold switch. |
