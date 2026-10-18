# FANNS Research: Targeted Follow-Up Experiments

**Audit Document**: `research_audit/FOLLOW_UP_EXPERIMENTS.md`  
**Workspace**: `C:/Users/anime/Desktop/filtered-ann-research-medium`  
**Associated Audit**: [FINAL_EVIDENCE_AUDIT.md](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/FINAL_EVIDENCE_AUDIT.md)  
**Machine-Readable Findings**: [audit_findings.json](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/audit_findings.json)

---

## 1. Principles of Experimental Audit

To prevent wasteful full-benchmark reruns and uphold scientific integrity:
1. **Targeted Subsets Over Full Sweeps**: Resolve specific empirical questions using controlled query subsets ($Q=100$) rather than rerunning all $16,500$ query-strategy evaluations.
2. **Explicit Cost Estimation**: Every computational cost is clearly designated as an **ESTIMATE** rather than a measured historical value.
3. **Strict Priority Hierarchy**: Experiments are ranked by their necessity for defending the paper against skeptical academic peer reviewers.

---

## 2. Ranked List of Recommended Experiments

### Experiment EXP-01: Index Construction Parity Ablation ($ef_{\text{construction}}=50$ vs $100$)
- **Priority**: **ESSENTIAL** (Directly addresses Discrepancy DISC-002)
- **Research Question Answered**: Does building HNSW with $ef_{\text{construction}}=100$ (as suggested by the cache filename) vs $ef_{\text{construction}}=50$ (actual recorded build) significantly alter graph connectivity, in-graph filter recall, or visited node counts on selective workloads?
- **Why Existing Data Cannot Answer It**: The medium repository currently only possesses the serialized index built with $ef_{\text{construction}}=50$. Reviewers may question whether the $335.34\text{ ms}$ EMIS latency or the $88.58\%$ recall was artificially penalized by a lower construction parameter.
- **Controlled Configuration**:
  - Dataset: Official `arxiv-for-fanns-medium` ($N=100,000$, $D=4,096$).
  - Constant Parameters: $M=16$, $k=10$, $ef_{\text{search}}=50$, Random Seed $= 42$.
  - Independent Variable: $ef_{\text{construction}} \in \{50, 100\}$.
  - Query Workloads: 100 queries each from `EM` and `EMIS`.
  - Methods Evaluated: `InGraphFilter`, `HNSW_PostFilter`.
- **Expected Outputs**:
  - Comparison table reporting Recall@10, Mean Latency, and Mean Nodes Visited for $ef_C=50$ vs $ef_C=100$.
  - Verification whether $ef_C=100$ improves EMIS graph connectivity or merely increases build time.
- **Estimated Computational Cost** *(Labelled as Estimate)*:
  - Index Build: $\approx 22\text{ minutes}$ CPU on Ryzen 5 5500U ($\approx 1,300\text{ seconds}$).
  - Query Evaluation: $\approx 3\text{ minutes}$ CPU ($200\text{ queries}$).
  - Total Estimated Compute: $\approx \mathbf{25\text{ minutes}}$.

---

### Experiment EXP-02: Native C++ Traversal Profiling vs. Python Interpreter Overhead
- **Priority**: **RECOMMENDED** (Disentangles algorithmic complexity from language runtime overhead)
- **Research Question Answered**: How much of the $335.34\text{ ms}$ InGraph EMIS latency is algorithmic (evaluating $18,530$ vector distances in $4,096$ dimensions) vs language overhead (Python priority queue management, method dispatch, and object boxing)?
- **Why Existing Data Cannot Answer It**: All benchmark measurements in [all_queries_raw_results.csv](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/results/controlled_benchmark/all_queries_raw_results.csv) capture total Python end-to-end time. Skeptical reviewers may attribute the latency explosion purely to Python overhead rather than graph topology.
- **Controlled Configuration**:
  - Fixed Query Subset: The 50 slowest EMIS queries (which visited $>15,000$ nodes).
  - Profiling Instrumentation: `cProfile` and line-level timing isolating:
    1. Vector Distance GEMV (`np.dot` / cosine).
    2. Bitset Metadata Filter Checking.
    3. Traversal Heap / Priority Queue Management.
    4. Python Loop and Function Call Overhead.
- **Expected Outputs**:
  - Latency breakdown waterfall chart showing the exact fraction of time spent in BLAS vector distance computations vs Python loop overhead.
- **Estimated Computational Cost** *(Labelled as Estimate)*:
  - Evaluation of 50 queries: $\approx \mathbf{2\text{ minutes}}$ CPU.

---

### Experiment EXP-03: Validated Selectivity-Driven Dynamic Router (Hybrid Strategy)
- **Priority**: **RECOMMENDED** (Elevates paper from an empirical audit to a constructive algorithmic contribution)
- **Research Question Answered**: Can a simple, zero-training routing rule (route to `PreFilter` when estimated $\sigma \le 2\%$, and `InGraphFilter` when $\sigma > 2\%$) eliminate the $335\text{ ms}$ tail and outperform all static methods across the entire Pareto frontier?
- **Why Existing Data Cannot Answer It**: `PreFilter` and `InGraphFilter` were only evaluated as static baselines across entire workloads. While stratified data shows a theoretical crossover at $2\%$, no live dynamic router was executed.
- **Controlled Configuration**:
  - Router Rule:
    $$\text{Strategy}(q) = \begin{cases} \text{PreFilter}, & \text{if } |S_q| \le 2,000 \quad (\sigma \le 2\%) \\ \text{InGraphFilter}, & \text{if } |S_q| > 2,000 \quad (\sigma > 2\%) \end{cases}$$
  - Workload: Full 500 queries across `EM`, `Range`, and `EMIS`.
  - Existing serialized index and inverted index reused (zero new index build).
- **Expected Outputs**:
  - Master summary entry for `Adaptive_Router`:
    - Mean Recall: $\approx 0.94 - 0.96$.
    - EMIS Mean Latency: Expected reduction from **$335.34\text{ ms} \to <30\text{ ms}$** by offloading sparse subgraphs to PreFilter.
- **Estimated Computational Cost** *(Labelled as Estimate)*:
  - Execution of 1,500 queries on existing index: $\approx \mathbf{8\text{ minutes}}$ CPU.

---

### Experiment EXP-04: Multi-Threaded SIMD Batch Throughput Scaling
- **Priority**: **OPTIONAL** (Addresses enterprise production deployment questions)
- **Research Question Answered**: How does search throughput (QPS) scale under concurrent multi-client query loads (1, 2, 4, 8 threads) for memory-mapped graphs vs inverted index pre-filtering?
- **Why Existing Data Cannot Answer It**: Current benchmark executed in single-threaded mode ($T=1$).
- **Controlled Configuration**:
  - Thread Counts: $T \in \{1, 2, 4, 8\}$.
  - Batch size: 100 queries concurrent.
  - Workload: EM and EMIS.
- **Expected Outputs**:
  - QPS scalability curves demonstrating RAM memory bandwidth bottlenecks in $D=4,096$ distance calculations.
- **Estimated Computational Cost** *(Labelled as Estimate)*:
  - $\approx \mathbf{15\text{ minutes}}$ CPU.

---

## 3. Summary of Prioritized Action Plan

| Rank | Experiment ID | Title | Priority | Core Objective | Estimated Compute |
|:---:|:---:|:---|:---:|:---|:---:|
| **1** | **EXP-01** | Index Parity Ablation ($ef_C=50$ vs $100$) | **ESSENTIAL** | Disprove index degradation bias | 25 min CPU |
| **2** | **EXP-03** | Validated Adaptive Hybrid Router | **RECOMMENDED** | Deliver a constructive Pareto contribution | 8 min CPU |
| **3** | **EXP-02** | C++ Traversal Profiling vs Python | **RECOMMENDED** | Defend against runtime implementation critique | 2 min CPU |
| **4** | **EXP-04** | Multi-Threaded Throughput Scaling | **OPTIONAL** | Characterize multi-core concurrency | 15 min CPU |

> **Conclusion**: By running **EXP-01** (25 min) and **EXP-03** (8 min), the authors can resolve all reviewer doubts regarding index quality and introduce a validated constructive hybrid router, taking the paper from a pure empirical audit to a top-tier systems contribution in under **35 minutes of total computation**.
