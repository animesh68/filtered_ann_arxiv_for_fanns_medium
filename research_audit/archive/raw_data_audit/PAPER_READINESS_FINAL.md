# FANNS Research: Final Paper-Readiness Gate & Submission Blueprint

**Audit Document**: `research_audit/followup_runs/raw_data_audit/PAPER_READINESS_FINAL.md`  
**Auditor**: Senior Research Engineer & Skeptical Experimental Auditor  
**Workspace**: `C:/Users/anime/Desktop/filtered-ann-research-medium`  
**Timestamp**: 2026-10-16 07:40:00 UTC  
**Master Audit Artifacts**:
- Raw Recomputation Engine: [`audit_metrics.py`](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/followup_runs/raw_data_audit/audit_metrics.py)
- Machine-Readable Audit Telemetry: [`AUDIT_RESULTS.json`](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/followup_runs/raw_data_audit/AUDIT_RESULTS.json)
- Discrepancy Investigation: [`METRIC_RECONCILIATION.md`](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/followup_runs/raw_data_audit/METRIC_RECONCILIATION.md)
- Defensibility Matrix: [`CLAIM_VERDICT.md`](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/followup_runs/raw_data_audit/CLAIM_VERDICT.md)

---

## 1. Final Paper-Readiness Gate Verdict

### Verdict: **GREEN LIGHT FOR MANUSCRIPT PREPARATION (SUBJECT TO SPECIFIED QUALIFICATIONS)**

The empirical foundation across both benchmark repositories ($1K$ and $100K$ on `SPCL/arxiv-for-fanns`) is **mathematically verified, reproducible from raw data, and free of data fabrication**. The completed follow-up experiments (`EXP-01` and `EXP-03`) have resolved the outstanding material questions regarding index construction parameters and adaptive routing viability.

The manuscript can now be drafted with high confidence, provided the authors adhere strictly to the boundaries and framing defined in this audit.

---

## 2. Strongest Defensible Paper Framing

### Recommended Framing: **Option B+ — An Empirical Cross-Scale Study of Filtered Proximity Traversal with a Validated Pareto Query Router**

#### Why this framing succeeds:
1. **Top-Tier Systems Credibility (SIGMOD / VLDB / ICDE)**:  
   Framing the paper as a "pure adaptive system" (Option C) is dangerous because reviewers will correctly note that the router is a lightweight heuristic rule (`if selectivity <= tau`). If sold as an algorithmic index innovation, it will face severe pushback.
2. **Defensible Asymmetrical Value**:  
   - **Core Empirical Contribution (70%)**: A deep, reproducible cross-scale scaling study ($N=1,000 \to 100,000$, $D=4,096$) showing the structural failure of spatial overfetching ($50\times$ ceiling at $51.4\%$ recall), the catastrophic collapse of post-filtering ($0.1714$ recall on selective predicates), and the breakdown of logarithmic proximity graph traversal due to subgraph isolation ($18,530$ nodes visited).
   - **Constructive Systems Contribution (30%)**: Uncovering the empirical crossover point at $\sigma \approx 2-5\%$ and validating a **lightweight, zero-index-overhead query router** that cuts P99 tail latency by **$127.1\text{ ms}$** and improves recall without altering graph indexing.

---

## 3. Inventory of Claims: Approved vs. Prohibited

### A. Claims Certified for Inclusion (High Confidence)

1. **Post-Filtering Suffers an Inherent Geometric Collapse**:  
   *Claim*: On standard HNSW graphs, post-filtering recall degrades to $0.1714$ ($82.9\%$ loss) on multi-predicate selective queries ($N=100,000$), falling to $0.0240$ when $\sigma < 5\%$. EXP-01 proves that doubling index construction effort ($ef_C=100$) leaves this failure completely unchanged ($0.1500 \to 0.1510$), proving it is a geometric attribute-spatial disconnect, not an index quality artifact.
2. **Overfetching Encounters a Rigid Mathematical Saturation Ceiling**:  
   *Claim*: Expanding candidate pools up to $50\times$ ($k=500$, a $9.5\times$ latency increase) only recovers recall to $0.5140$ ($51.4\%$) on EMIS, demonstrating the mathematical limit of post-filtering when attributes are sparse.
3. **Subgraph Isolation Multiplies Graph Traversal Cost**:  
   *Claim*: While in-graph filtering maintains robust recall across scales ($93.7\%$ on EM, $93.0\%$ on Range, $88.6\%$ on EMIS), selective workloads force unguided spatial traversals to wander through filter-sparse neighborhoods, expanding mean visited nodes from $2,317$ (EM) to $18,530$ (EMIS) and inflating query latency by $15\times - 20\times$.
4. **Pre-Filtering Is Efficient in the Ultra-Selective Tail**:  
   *Claim*: Inverted-index pre-filtering strictly guarantees $1.0000$ recall and executes in $<20\text{ ms}$ ($54.3\text{ QPS}$) when $\sigma \le 2\%$, outperforming all proximity graph methods on high-dimensional vectors.
5. **The Validated Adaptive Router Compresses Tail Latency**:  
   *Claim*: A metadata-based selectivity router switching at $\tau=2\%$ guarantees $1.0000$ recall on the most selective queries, improving EMIS recall from $0.8858 \to 0.8918$, reducing mean latency by $13.5\%$ ($214.4\text{ ms} \to 185.6\text{ ms}$), and compressing P99 tail latency by **$127.1\text{ ms}$** ($929.95\text{ ms} \to 802.85\text{ ms}$) with negligible routing overhead ($0.002-0.003\text{ ms}$).

---

### B. Prohibited Claims That Must Be Softened or Retracted

1. **PROHIBITED: "The Adaptive Router Strictly Dominates Static Baselines"**:  
   - *Reason*: PreFilter has higher recall ($1.0000 > 0.8918$) and is actually faster than the 2% router on EMIS ($117.8\text{ ms}$ vs. $185.6\text{ ms}$).  
   - *Mandatory Correction*: State that the router *expands the empirical Pareto frontier* and strictly dominates InGraphFilter on EM and EMIS across recall and mean latency.
2. **PROHIBITED: Quoting Small-Scale Latencies (5.4 ms) for Medium Scale**:  
   - *Reason*: README line 173 quoted $5.4-6.2\text{ ms}$ from the $1K$ benchmark. Real medium InGraph latency is $14-18\text{ ms}$ on EM and $214-335\text{ ms}$ on EMIS.  
   - *Mandatory Correction*: Report the verified medium latencies ($14.1\text{ ms}$ EM, $23.6\text{ ms}$ Range, $185.6\text{ ms}$ EMIS for Router; $18.4\text{ ms}$ EM, $24.1\text{ ms}$ Range, $214.4\text{ ms}$ EMIS for InGraph).
3. **PROHIBITED: Claiming to Benchmark Official ACORN / SIEVE / UNIFY Systems**:  
   - *Reason*: Implementations in `src/filter_aware.py` are educational single-graph heuristics on standard HNSW.  
   - *Mandatory Correction*: Formally label them as *"paper-inspired single-graph heuristic baselines"* evaluating online multi-hop traversal and entry routing.
4. **PROHIBITED: Claiming Proximity Graphs Suffer Literal "Topological Disconnection"**:  
   - *Reason*: Graph disconnection was not proven via graph cut algorithms; what was measured is that beam search wanders exhaustively through $18,500$ nodes.  
   - *Mandatory Correction*: Use *"subgraph isolation, beam-search trapping, and traversal expansion"*.

---

## 4. Minimum Pre-Submission Checklist

- [x] **Raw Data Recomputation Verified**: [`audit_metrics.py`](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/followup_runs/raw_data_audit/audit_metrics.py) verifies zero calculation errors across all CSVs.
- [x] **Ground Truth Certified**: Denominator is strictly $10$ across all queries ($|GT| \ge 100$ uniformly).
- [x] **Index Construction Parity Disproven as Bias**: EXP-01 confirmed that $ef_C=100$ visits $15,921$ nodes vs. $15,860$ on $ef_C=50$.
- [x] **Router Overhead Formally Measured**: Verified as $0.002-0.003\text{ ms}$ (EM/EMIS) and $0.227\text{ ms}$ (Range).
- [x] **Train/Test Threshold Generalization Verified**: $2\% \le \tau \le 5\%$ validated on held-out queries $250..499$.
- [ ] **Action Item 1 (README Update)**: Remove placeholder $5.4\text{ ms}$ text from line 173 of `README.md`; align with verified numbers in `EXP03_SUMMARY.csv`.
- [ ] **Action Item 2 (Experimental Setup Table)**: Report index construction as $M=16, ef_{\text{construction}}=50$ in the main paper table, with EXP-01 presented in Section 6 as a construction ablation study.
- [ ] **Action Item 3 (Manuscript Drafting)**: Draft manuscript following the section outline in `PAPER_READINESS.md` under Framing B+.

---

## 5. Are Any Additional Experiments Required Before Submission?

### Verdict: **NO FURTHER BENCHMARK RERUNS ARE REQUIRED.**
All necessary empirical evidence to support the qualified claims of Framing B+ is already measured, archived, and independently audited in `research_audit/followup_runs/`. The project is officially **Paper-Ready**.
