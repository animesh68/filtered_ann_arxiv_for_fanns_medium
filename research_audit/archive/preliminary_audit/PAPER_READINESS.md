# FANNS Research: Paper-Readiness Assessment & Strategic Framing

**Audit Document**: `research_audit/PAPER_READINESS.md`  
**Workspace**: `C:/Users/anime/Desktop/filtered-ann-research-medium`  
**Associated Audit**: [FINAL_EVIDENCE_AUDIT.md](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/FINAL_EVIDENCE_AUDIT.md)  
**Machine-Readable Findings**: [audit_findings.json](file:///C:/Users/anime/Desktop/filtered-ann-research-medium/research_audit/audit_findings.json)

---

## 1. Paper Framing & Strategic Positioning

### Recommended Framing: **Option B — A Cross-Scale Empirical Study of Filtered Proximity Traversal Under Attribute Sparsity**
The current empirical body of work is **best positioned as an in-depth empirical systems and algorithmic scaling paper**. 

#### Why NOT Framing C (Study with a Validated Adaptive Strategy)?
- **Scientific Integrity Mandate**: An adaptive routing strategy was hypothesized based on selectivity strata, but **no live adaptive router was evaluated as an independent search strategy** in the benchmark suite. Promoting an un-implemented concept to a paper's primary contribution is a fatal flaw during peer review.
- Instead, the cross-scale Pareto crossover analysis should be presented as the **empirical motivation and design blueprint** for future hybrid engines.

#### Why Framing B is Strong and High-Impact:
- Top systems conferences (SIGMOD, VLDB, ICDE, EDBT) value rigorous, honest empirical evaluations that debunk widespread myths and expose hidden bottlenecks in production vector retrieval architectures.
- The 100x dataset scaling ($N=1,000 \to 100,000$) with ultra-high dimensionality ($D=4,096$) reveals profound algorithmic transitions:
  1. The complete collapse of overfetching on selective workloads.
  2. The failure of logarithmic graph search when navigating filter-sparse subgraphs.
  3. The exact mathematical crossover point where pre-filtering overtakes graph traversal.

---

## 2. Inventory of Claims: Safe vs. Prohibited

### A. Claims Safe to Include in the Paper (High Confidence)
1. **The Spatial-Disconnect Collapse of Post-Filtering**: Naive post-filtering on standard HNSW graphs loses $58.4\%$ to $82.9\%$ of true nearest neighbors, collapsing to $0.1714$ recall on multi-predicate selective queries ($N=100,000$). At selectivities $<5\%$, recall degrades to $0.0240$ ($97.6\%$ loss).
2. **The Hard Overfetch Ceiling on Selective Predicates**: Expanding the candidate pool up to $50\times$ ($k=500$) only recovers recall to $0.5140$ ($51.4\%$) on EMIS, while increasing latency by $9.5\times$ ($46.18\text{ ms}$). This empirically confirms the mathematical impossibility of spatial overfetching under attribute sparsity.
3. **Pre-Filtering Is Efficient in the Ultra-Selective Tail**: Inverted-index pre-filtering guarantees $1.0000$ recall and scales strictly as $\mathcal{O}(|S| \cdot D)$. At selectivities $<2\%$, pre-filtering achieves $18.42\text{ ms}$ latency ($54.3\text{ QPS}$), outperforming all graph traversal methods ($150\text{ ms} - 1,815\text{ ms}$) on high-dimensional data.
4. **Graph-Aware Traversal Preserves Recall but Degrades in Sparse Subgraphs**: In-graph filtering maintains robust recall across scales ($93.7\%$ on EM, $93.0\%$ on Range, $88.6\%$ on EMIS). However, query latency exhibits massive tail expansion on selective queries (mean $335.34\text{ ms}$, P99 $1,446.69\text{ ms}$), visiting an average of $18,530$ nodes due to unguided spatial entry points wandering through filter-invalid neighborhoods.
5. **Single-Graph Online Multi-Hop Expansion Multiplies Latency**: Online 2-hop neighbor expansion (ACORN-style approximation) on standard HNSW yields minor recall gains ($+2.5\%$ on EMIS) at devastating latency costs ($1,815.06\text{ ms}$, visiting $40,665$ nodes), proving that filter-aware index augmentation must occur offline rather than dynamically during traversal.

---

### B. Claims That Must Be Softened or Omitted (High Risk)
1. **OMIT: InGraph 5.4 ms Medium-Scale Latency**:
   - *Prohibited*: "InGraphFilter achieves >99.4% recall at 5.4–6.2 ms latency on 100K vectors."
   - *Reason*: This was an unedited placeholder copied from the $1K$ report. Real medium latency is $13.99\text{ ms}$ (EM) and $335.34\text{ ms}$ (EMIS).
   - *Corrected Statement*: "InGraphFilter achieves $93.7\%$ recall at $13.99\text{ ms}$ on moderate workloads, but degrades to $335.34\text{ ms}$ on selective workloads due to subgraph isolation."
2. **SOFTEN: Evaluation of ACORN, SIEVE, and UNIFY**:
   - *Prohibited*: "We benchmarked ACORN (SIGMOD'24), SIEVE (VLDB'24), and UNIFY."
   - *Reason*: The implementations are educational, single-graph heuristics on standard HNSW, not official C++/CUDA vendor engines.
   - *Corrected Statement*: "We evaluate single-graph heuristic baselines inspired by the traversal principles of ACORN, SIEVE, and UNIFY to examine the limits of dynamic neighbor expansion and entry selection on standard proximity graphs."
3. **OMIT: Novel Adaptive Routing Engine**:
   - *Prohibited*: "We contribute a novel adaptive router that unifies pre-filtering and in-graph search."
   - *Reason*: No router was implemented as an evaluated benchmark method.
   - *Corrected Statement*: "Our stratified selectivity analysis reveals a distinct Pareto crossover at $\sigma \approx 2\%$, delineating the operating boundaries for future hybrid execution engines."
4. **SOFTEN: Universality Across Vector Dimensions**:
   - *Prohibited*: "These findings define filtered ANN performance across all embedding models."
   - *Reason*: Evaluated on a single dataset (`arxiv-for-fanns`) with high-dimensional vectors ($D=4,096$). Lower-dimensional datasets ($D=128$ or $D=768$) may exhibit different distance calculation to index lookup cost ratios.

---

## 3. Recommended Academic Paper Structure

### Title Options:
- **Option 1**: *The Reality of Filtered ANN at Scale: A 100K-Vector Empirical Benchmark and Architectural Audit*
- **Option 2**: *Traversing Sparse Subgraphs: A Cross-Scale Empirical Study of Filtered Proximity Graphs*

### Detailed Section-by-Section Outline:

```
1. INTRODUCTION
   1.1 The rise of filtered vector retrieval in RAG and enterprise search
   1.2 The fundamental conflict: Metric space topology vs. attribute predicates
   1.3 The reproducibility crisis: Discrepancies between theory, small benchmarks, and scale
   1.4 Core contributions of this empirical study

2. BACKGROUND & TAXONOMY OF FILTERED RETRIEVAL
   2.1 Proximity Graph Navigation (HNSW foundations)
   2.2 Post-Filtering & Candidate Pool Overfetching
   2.3 Inverted Index Pre-Filtering
   2.4 Filter-Aware Graph Navigation (InGraph, ACORN, SIEVE, UNIFY concepts)

3. BENCHMARK METHODOLOGY & EXPERIMENTAL SETUP
   3.1 The SPCL arxiv-for-fanns Benchmark Suite (D=4,096, N=1,000 and N=100,000)
   3.2 Workload Taxonomy: Exact Match (EM), Numeric Range, Multi-Predicate (EMIS)
   3.3 Ground-Truth Formulation, Denominator Semantics, and Metric Averaging
   3.4 Rigorous Execution Telemetry & Timing Boundary Isolation
   3.5 Implementation Disclosure: Defining the Single-Graph Heuristic Baselines

4. CROSS-SCALE EMPIRICAL FINDINGS
   4.1 The Collapse of Naive Post-Filtering Across Scales
   4.2 Overfetch Saturation: Why 50x Overfetching Hits a Ceiling on Selective Predicates
   4.3 The Pre-Filter Linear Frontier: When Exact Search Dominates Graphs
   4.4 In-Graph Filtering: High Recall at the Cost of Severe Tail Latency
   4.5 The Breakdown of Online Multi-Hop Expansion (ACORN/UNIFY Heuristics)

5. DEEP DIVE: SUBGRAPH ISOLATION & TAIL EXPANSION
   5.1 Measuring Visited Nodes vs. Selectivity (2,317 vs. 18,530 nodes)
   5.2 The Spatial Entry Point Bottleneck
   5.3 High-Dimensional (D=4,096) Distance Evaluation Overhead in Proximity Searches

6. PARETO OPTIMIZATION & ARCHITECTURAL IMPLICATIONS
   6.1 Mapping the Empirical Pareto Frontier (Recall vs. Latency)
   6.2 The 2% Selectivity Crossover: A Blueprint for Hybrid Query Planners
   6.3 Guidelines for Enterprise Vector Database Architectures

7. THREATS TO VALIDITY & REPRODUCIBILITY AUDIT
   7.1 Index Construction Parameters (efConstruction=50 vs. efConstruction=100)
   7.2 Language Runtime Overheads (Python/NumPy vs. Native C++)
   7.3 Dataset Specifics and Generalization Limits

8. CONCLUSION & FUTURE WORK
```

---

## 4. Minimum Requirements Checklist Before Paper Submission

- [x] **Audit Passed**: Recomputation engine verifies all 16,500 records match summary tables to machine precision.
- [x] **Ground Truth Certified**: Verified that $|GT| \ge 10$ for $100\%$ of queries; denominator semantics are strictly $10$.
- [x] **Discrepancy DISC-001 Resolved**: Narrative text in README line 173 identified and corrected.
- [ ] **Action Item 1**: Correct index parameter in experimental configuration table: explicitly state $M=16, ef_{\text{construction}}=50$.
- [ ] **Action Item 2**: Formally qualify ACORN-, SIEVE-, and UNIFY-style baselines in Section 3 as *educational, single-graph approximations*.
- [ ] **Action Item 3**: Execute Experiment EXP-01 (C++ InGraph engine) or EXP-02 ($ef_C=100$ parity ablation) if submitting to a tier-1 systems conference.
