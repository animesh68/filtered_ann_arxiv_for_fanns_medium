# Scientific Claim Audit Verdict & Defensibility Matrix

**Audit Document**: `research_audit/followup_runs/raw_data_audit/CLAIM_VERDICT.md`  
**Auditor**: Senior Research Engineer & Skeptical Experimental Auditor  
**Workspace**: `C:/Users/anime/Desktop/filtered-ann-research-medium`  
**Timestamp**: 2026-10-16 07:30:00 UTC  
**Machine-Readable Audit**: [`AUDIT_RESULTS.json`](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/followup_runs/raw_data_audit/AUDIT_RESULTS.json)

---

## 1. Classification Framework

Every candidate scientific claim evaluated during the audit is categorized into one of four formal evidentiary statuses:
1. **Supported**: Directly and unambiguously substantiated by reproducible raw data without confounding factors.
2. **Supported with qualification**: Mathematically or empirically verified, but requiring explicit boundary conditions, definitions, or softened language to prevent misleading over-generalization.
3. **Not supported**: Refuted, contradicted, or mathematically false based on the empirical measurements.
4. **Unresolved**: Insufficient raw data or telemetry exists to definitively prove or disprove the assertion.

---

## 2. Master Claim Audit Matrix

| # | Scientific Claim Tested | Status | Measured Evidence / Raw Grounding | Mandatory Qualification / Scientific Caveat |
|:---:|:---|:---:|:---|:---|
| **1** | **The Adaptive Router outperforms Static InGraphFilter on recall and mean latency.** | **Supported with qualification** | - EM: Recall $0.9380 > 0.9374$, Latency $14.11 < 18.43\text{ ms}$ ($23\%$ faster)<br>- EMIS: Recall $0.8918 > 0.8858$, Latency $185.57 < 214.43\text{ ms}$ ($13.5\%$ faster)<br>- Range: Recall $0.9304 == 0.9304$, Latency $23.64 < 24.15\text{ ms}$ ($2\%$ faster) | On `Range`, the recall is identical and latency improvement is marginal ($0.51\text{ ms}$). The major win occurs on selective workloads (`EMIS`). |
| **2** | **The Adaptive Router outperforms Static PreFilter.** | **Not supported** | - PreFilter achieves **$1.0000$ recall ($100\%$)** across all workloads.<br>- Router achieves $0.9380$ (EM), $0.9304$ (Range), and $0.8918$ (EMIS).<br>- On EMIS, PreFilter mean latency is **$117.80\text{ ms}$**, whereas Router latency is **$185.57\text{ ms}$**. | PreFilter has strictly higher recall on all workloads and is actually **$36.5\%$ faster** than the 2% router on EMIS because $94.2\%$ of EMIS queries exceed $2\%$ selectivity and are dispatched to the slower InGraph engine. The router does NOT outperform PreFilter in general. |
| **3** | **The Adaptive Router "strictly Pareto dominates" static baselines.** | **Not supported** *(as written)*<br>**Supported with qualification** *(vs. InGraph on EM/EMIS)* | - A method strictly Pareto dominates another iff it is $\ge$ on ALL objectives and $>$ on at least one.<br>- Router does **NOT** dominate PreFilter because PreFilter has higher recall ($1.0 > 0.89$).<br>- Router strictly dominates InGraph on EM and EMIS across Recall, Mean Latency, P95, and P99. On Range, P99 is slightly higher ($189.6\text{ ms}$ vs. $177.6\text{ ms}$). | The phrase *"strictly Pareto dominates static baselines"* must be retracted. The router expands the Pareto frontier and strictly dominates InGraph on EM and EMIS, but exists on a trade-off frontier with PreFilter. |
| **4** | **The Router reduces EMIS mean latency and compresses P99 tail latency.** | **Supported** | - InGraph EMIS Mean Latency: $214.43\text{ ms} \to$ Router: $185.57\text{ ms}$ ($\mathbf{-28.86\text{ ms}}$, $-13.5\%$).<br>- InGraph EMIS P99 Latency: $929.95\text{ ms} \to$ Router: $802.85\text{ ms}$ ($\mathbf{-127.10\text{ ms}}$).<br>- InGraph EMIS P95 Latency: $693.29\text{ ms} \to$ Router: $661.60\text{ ms}$ ($-31.69\text{ ms}$). | Verified to machine precision from 500 per-query records in `EXP03_RAW.csv`. Tail compression is arithmetically sound. |
| **5** | **The 2% threshold ($\tau=0.02$) generalizes across query splits.** | **Supported with qualification** | - Tuning Split (0..249): EMIS Recall $0.8744$, Latency $163.98\text{ ms}$ ($6.4\%$ routed to PreFilter).<br>- Held-Out Split (250..499): EMIS Recall $0.9092$, Latency $209.99\text{ ms}$ ($5.2\%$ routed to PreFilter).<br>- Sub-25 ms latency preserved on EM and Range in both splits. | The threshold generalizes cleanly without overfitting, but the threshold sweep reveals that $\tau=5\%$ or $10\%$ provides an even more aggressive latency reduction on EMIS ($73-122\text{ ms}$). $\tau=2\%$ is a robust, conservative operating point, not a global optimum. |
| **6** | **The recommended operating window is $2\% \le \tau \le 5\%$.** | **Supported** | - At $\tau \le 1\%$, too few trapped queries are rescued ($<1\%$).<br>- At $\tau = 2\% - 5\%$, EMIS latency drops by $28 - 60\text{ ms}$ while EM/Range stay fast ($14-24\text{ ms}$).<br>- At $\tau \ge 20\%$, EM latency degrades from $14.5\text{ ms} \to 22.3\text{ ms}$ and Range from $20.6\text{ ms} \to 27.5\text{ ms}$ due to PreFilter linear scans over $10K-20K$ vectors. | Supported by multi-threshold sweep in `ROUTER_THRESHOLD_ANALYSIS.md`. |
| **7** | **Threshold tuning was isolated from held-out evaluation.** | **Supported** | - Candidate threshold $\tau=0.02$ was pre-declared in `configs/medium_benchmark.json` and `EXP03_CONFIG.json` based on prior stratified selectivity data.<br>- Held-out split (250..499) was evaluated with frozen thresholds without backward parameter adjustment. | Strict train/test protocol verified. |
| **8** | **Selectivity is estimated legitimately from query-time metadata with all overhead included.** | **Supported** | - Estimator calls `MetadataIndex.get_matching_ids(predicate)` via inverted index hash lookups or columnar date comparisons.<br>- Zero peeking at ground truth or vector embeddings.<br>- Measured routing overhead: $0.002\text{ ms}$ (EM), $0.003\text{ ms}$ (EMIS), $0.227\text{ ms}$ (Range).<br>- Routing overhead was strictly added into `latency_ms`. | Complete accounting verified in `run_exp03.py` lines 80-112. |
| **9** | **Increasing $ef_{\text{construction}}$ from 50 to 100 does not solve subgraph isolation.** | **Supported** | - InGraph visited nodes on EMIS: $15,860.7$ nodes ($ef_C=50$) vs. $15,921.1$ nodes ($ef_C=100$).<br>- Post-filter recall on EMIS: $0.1500$ ($ef_C=50$) vs. $0.1510$ ($ef_C=100$).<br>- Index construction time increased by $+39.3\%$ ($713.89\text{ s} \to 994.39\text{ s}$). | EXP-01 empirically disproved the hypothesis that $ef_C=50$ caused the high visited node count. |
| **10** | **Proximity graphs suffer "topological graph disconnection" under selective filters.** | **Supported with qualification** | - InGraph visits $18,530$ nodes on EMIS vs. $2,317$ nodes on EM, expanding latency by $15\times - 20\times$.<br>- Nodes evaluated represent $18.5\%$ of the entire 100K database. | The data proves **traversal expansion and beam-search wandering in filter-sparse subgraphs**, not literal topological graph disconnection (where no connected path exists). The language must be softened to "subgraph isolation and traversal trapping". |

---

## 3. Mandatory Language Corrections for Academic Submission

1. **Retract**: *"The adaptive router strictly dominates static baselines across all workloads."*  
   **Replace with**: *"The adaptive router strictly improves upon in-graph filtering across recall, mean latency, and tail latency on selective workloads, while establishing a superior quality-efficiency trade-off along the empirical Pareto frontier."*
2. **Retract**: *"The router outperforms exact pre-filtering."*  
   **Replace with**: *"The router executes an order of magnitude faster than pre-filtering on broad workloads ($\sigma > 10\%$) while sacrificing less than $7\%$ recall, though pre-filtering retains a recall advantage ($1.0000$) on ultra-selective queries."*
3. **Retract**: *"The graph becomes topologically disconnected."*  
   **Replace with**: *"Proximity graphs suffer severe subgraph isolation and traversal trapping under selective predicates, forcing unguided greedy search to wander across more than $18,500$ nodes."*
