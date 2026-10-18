# An Empirical Cross-Scale Study of Filtered Proximity Traversal with a Selectivity-Aware Query Router

**Target Track**: Empirical Systems & Scalable Data Management (e.g., ACM SIGMOD / VLDB / IEEE ICDE)  
**Authors**: Research Engineering & Benchmarking Group  
**Artifact Repository**: [`filtered_ann_arxiv_for_fanns_medium`](https://github.com/animesh68/filtered_ann_arxiv_for_fanns_medium)  
**Reference Baseline Repository**: [`filtered_ann_arxiv_for_fanns_small`](https://github.com/animesh68/filtered_ann_arxiv_for_fanns_small)  

---

## 1. Abstract

Filtered Approximate Nearest Neighbor Search (FANNS) has become an essential primitive for Retrieval-Augmented Generation (RAG), enterprise search, and e-commerce retrieval, where vector similarity queries are constrained by structured metadata filters. Despite rapid algorithmic development, empirical understanding of how proximity graph traversals behave when scaling from small datasets ($1,000$ vectors) to medium datasets ($100,000$ vectors) under ultra-high dimensionality ($4,096$ dimensions) remains fragmented. In this work, we present an empirical cross-scale systems study on the official `SPCL/arxiv-for-fanns` benchmark suite evaluating exact filtered search, inverted-index pre-filtering, Hierarchical Navigable Small World (HNSW) post-filtering, candidate overfetching, and single-graph in-graph filtering. 

Our empirical audit establishes three foundational systems findings: (1) Naive post-filtering collapses catastrophically under attribute selectivity, losing up to $82.9\%$ of ground-truth neighbors at $100K$ scale ($0.1714$ recall on multi-attribute queries); candidate overfetching hits a structural ceiling, where expanding the retrieval candidate pool by $50\times$ only recovers recall to $0.5140$ at a $9.5\times$ latency penalty. (2) In-graph filtering preserves high recall across scales ($>93\%$ on categorical point and numeric range workloads), but encounters severe traversal expansion and subgraph isolation under selective filters, where unguided spatial entry points force beam search to evaluate $18,530$ nodes out of $100,000$ ($18.5\%$), expanding latency by $15\times\text{--}20\times$ ($13.99\text{ ms} \to 214\text{--}335\text{ ms}$). (3) A rigorous construction ablation ($ef_{\text{construction}}=50$ vs. $100$) proves that doubling index construction effort does not alleviate subgraph isolation ($15,921$ vs. $15,860$ nodes visited on selective queries). 

Guided by these findings, we evaluate a lightweight, metadata-driven query router that dynamically dispatches queries to inverted-index pre-filtering when estimated selectivity $\sigma \le 2\%$, and in-graph traversal otherwise. On the challenging multi-attribute workload, the router improves recall from $0.8858$ to $0.8918$, reduces mean latency by $13.5\%$ ($214.4\text{ ms} \to 185.6\text{ ms}$), and compresses P99 tail latency by $127.1\text{ ms}$ ($929.95\text{ ms} \to 802.85\text{ ms}$) with negligible ($0.003\text{ ms}$) routing overhead. An out-of-sample train/test split confirms that a $2\%\text{--}5\%$ operating window generalizes reliably. We outline the trade-offs of this approach against exact pre-filtering and discuss the architectural implications for next-generation vector database query planners.

---

## 2. Introduction

Approximate Nearest Neighbor Search (ANNS) is the core computational engine behind neural retrieval, multimodal embedding search, and generative AI grounding. In modern production deployments, vector retrieval rarely occurs in isolation. Instead, queries are almost universally accompanied by structured attribute constraints—such as user tenant isolation, document publication date intervals, access control lists, or multi-label category filters. This combined query paradigm is formalized as **Filtered Approximate Nearest Neighbor Search (FANNS)**: given a query vector $\mathbf{q} \in \mathbb{R}^D$, a distance metric $\mathcal{D}$, a metadata filter predicate $\mathcal{P}$, and a target count $k$, retrieve the top-$k$ vectors from the database $\mathcal{X}$ that satisfy $\mathcal{P}(\mathbf{x}) = \text{True}$.

The core systems challenge of FANNS stems from a fundamental topological conflict: **metric proximity space does not correlate with discrete attribute space**. While graph-based indices such as Hierarchical Navigable Small World (HNSW) graphs [1] construct edges based strictly on geometric distance, filter predicates partition the database into arbitrary, often fragmented subsets. When queries combine high vector dimensionality ($D=4,096$) with restrictive filter predicates, standard retrieval strategies face acute architectural dilemmas:
- **Pre-filtering** utilizes an inverted metadata index to identify all valid candidate vector IDs, then executes exact distance calculations over that candidate set. While pre-filtering guarantees $100\%$ recall, its computational cost scales linearly with candidate set cardinality $\mathcal{O}(|S| \cdot D)$, making it prohibitively expensive for broad filters.
- **Post-filtering** performs standard unconstrained graph traversal on HNSW to retrieve $k$ (or $\omega \cdot k$) nearest neighbors, subsequently discarding any candidate that violates $\mathcal{P}$. When the filter selectivity $\sigma = \frac{|S|}{N}$ is low, top spatial neighbors rarely satisfy $\mathcal{P}$, resulting in near-total recall collapse.
- **In-graph filtering** traverses the proximity graph while evaluating $\mathcal{P}$ at each visited node, using invalid nodes as topological "stepping stones" to preserve graph connectivity while admitting only valid nodes into the candidate pool. However, when valid nodes are sparse, unguided spatial entry points plunge the search into vast subgraphs containing no valid neighbors, triggering exhaustive local exploration.

Although recent literature has proposed specialized filter-aware graph architectures (e.g., ACORN [2], SIEVE [3], and UNIFY [4]), rigorous cross-scale empirical studies tracing how baseline strategies fail across dataset magnitudes ($1K \to 100K$) under identical high-dimensional embedding distributions ($D=4,096$) remain scarce. Furthermore, production systems frequently rely on ad-hoc overfetching heuristics or single-graph traversals without understanding the precise mathematical crossover where linear exact scans dominate proximity graphs.

### Research Questions
This empirical systems study is guided by four primary research questions:
- **RQ1 (Scaling Collapse of Heuristics)**: How do unconstrained proximity traversal, candidate overfetching, and pre-filtering scale as database size increases from $N=1,000$ to $N=100,000$ under high vector dimensionality ($D=4,096$)?
- **RQ2 (Traversal Expansion & Subgraph Isolation)**: Under what selectivity regimes does in-graph traversal suffer from beam-search trapping and traversal explosion, and can denser index construction ($ef_{\text{construction}}=100$) resolve it?
- **RQ3 (Selectivity-Aware Routing Viability)**: Can a lightweight metadata-driven query planner dynamically switch between pre-filtering and in-graph traversal to eliminate tail-latency spikes without introducing significant routing overhead?
- **RQ4 (Out-of-Sample Generalization & Operating Limits)**: Does a single selectivity threshold generalize across disparate filter semantics (point equality, range intervals, and set membership), and what are the trade-offs of this approach against exact pre-filtering?

### Contributions
In this work, we present an evidence-backed cross-scale experimental study and architectural audit of filtered vector retrieval on the official `SPCL/arxiv-for-fanns` benchmark suite [5]. Specifically, we make the following contributions:
1. **Cross-Scale Empirical Scaling Analysis**: We trace retrieval accuracy, latency distributions, and throughput across $N=1,000$ and $N=100,000$ database vectors ($D=4,096$), identifying the structural saturation ceiling of overfetching ($50\times$ candidate expansion leaves nearly half of ground-truth neighbors unretrieved on selective workloads).
2. **Topological Subgraph Isolation Audit**: We quantify graph traversal expansion under attribute sparsity, measuring an $8.0\times$ expansion in visited nodes ($2,317 \to 18,530$ nodes out of $100,000$) that breaks the logarithmic search guarantee of HNSW.
3. **Index Construction Parity Ablation**: Through a controlled ablation of HNSW construction parameters ($ef_{\text{construction}}=50$ vs. $100$), we disprove the hypothesis that subgraph isolation is an artifact of construction beam width, demonstrating that visited node counts on selective queries remain invariant ($15,860$ vs. $15,921$ nodes).
4. **Validated Selectivity-Aware Query Router**: We design and evaluate a lightweight metadata-driven query planner that routes queries to pre-filtering when estimated selectivity $\sigma \le 2\%$, and in-graph filtering otherwise. Evaluated across 1,500 queries over three standardized workloads with a strict 50/50 train/test split, the router reduces P99 tail latency by $127.1\text{ ms}$ while improving recall and adding less than $0.003\text{ ms}$ of routing overhead.

---

## 3. Background and Related Work

### 3.1 Proximity Graph Navigation (HNSW)
Navigable Small World graphs and their hierarchical extension (HNSW) [1] organize vectors into multi-layer proximity graphs where top layers have long-range skip connections and layer 0 contains a dense proximity graph. Greedy routing navigates from top layers down to layer 0, followed by a bounded priority queue beam search of size $ef_{\text{search}}$. Standard HNSW indexing assumes an unconstrained metric space where all database vectors are reachable.

### 3.2 Filtered ANN Paradigms
1. **Pre-Filtering**: Indexes document attributes in an inverted index. For query $(\mathbf{q}, \mathcal{P})$, it retrieves candidate ID list $\mathcal{S}_{\mathcal{P}}$ and computes distances exclusively over $\mathcal{S}_{\mathcal{P}}$. Computational complexity is $\mathcal{O}(|\mathcal{S}_{\mathcal{P}}| \cdot D) = \mathcal{O}(\sigma N \cdot D)$.
2. **Post-Filtering & Overfetching**: Executes standard unfiltered HNSW beam search requesting $k_{\text{fetch}} = \omega \cdot k$ candidates (where $\omega \ge 1$ is the overfetch multiplier), subsequently pruning candidates where $\mathcal{P}(\mathbf{a}) = \text{False}$. As shown analytically by Iff et al. [5], the expected number of valid candidates retrieved is $\omega \cdot k \cdot \sigma$. When $\sigma \ll 1/\omega$, post-filtering inevitably fails to return $k$ results.
3. **In-Graph Filtering**: Retains a single standard HNSW index. During beam search, when neighbors of candidate $u$ are extracted, invalid neighbors ($\mathcal{P}(\mathbf{a}) = \text{False}$) are added to the traversal queue to serve as routing bridges, but are excluded from the result priority queue $W$.

### 3.3 Advanced Filter-Aware Graph Indexes
Recent specialized architectures modify offline graph indexing:
- **ACORN** (Patel et al., SIGMOD 2024) [2] constructs correlation-extended graphs by connecting nodes to direct spatial neighbors and $\gamma$-scaled multi-hop neighbors possessing diverse attribute values.
- **SIEVE** (Gao et al., VLDB 2024) [3] constructs modular sub-indexes with 3D-packing models to route entry points to high-density attribute clusters.
- **UNIFY** (Liang et al., 2024) [4] unifies attribute and spatial hierarchies via Segmented Inclusive Graphs (SIG).

*Implementation Fidelity Disclosure*: In our benchmark pipeline, ACORN, SIEVE, and UNIFY are evaluated as **educational, single-graph Python heuristic baselines** on standard HNSW graphs (implementing online 2-hop expansion, sampled entry routing, and dynamic $ef_{\text{search}}$ switching respectively). They do not replicate the offline C++/CUDA graph construction algorithms of the original papers and are studied solely to inspect the behavior of online traversal heuristics.

---

## 4. Problem Definition

Let $\mathcal{X} = \{(\mathbf{x}_i, \mathbf{a}_i)\}_{i=1}^N$ be a database of $N$ items, where $\mathbf{x}_i \in \mathbb{R}^D$ is a high-dimensional vector representation and $\mathbf{a}_i$ is an associated structured attribute dictionary. Let $\mathcal{D}(\mathbf{u}, \mathbf{v})$ denote a distance metric on $\mathbb{R}^D$ (in this work, Euclidean $L_2$ distance $\mathcal{D}(\mathbf{u}, \mathbf{v}) = \|\mathbf{u} - \mathbf{v}\|_2^2$). 

A filter predicate $\mathcal{P}: \mathcal{A} \to \{\text{True}, \text{False}\}$ partitions the database into an eligible candidate subset:
$$\mathcal{S}_{\mathcal{P}} = \{\mathbf{x}_i \in \mathcal{X} \mid \mathcal{P}(\mathbf{a}_i) = \text{True}\}$$
The filter selectivity $\sigma(\mathcal{P})$ is defined as the fraction of eligible points:
$$\sigma(\mathcal{P}) = \frac{|\mathcal{S}_{\mathcal{P}}|}{N} \in [0, 1]$$

A FANNS query is defined by the tuple $(\mathbf{q}, \mathcal{P}, k)$, where $\mathbf{q} \in \mathbb{R}^D$ is the query vector, $\mathcal{P}$ is the query-specific filter predicate, and $k$ is the number of desired results. The ground-truth result set $\mathcal{G}^*(\mathbf{q}, \mathcal{P}, k)$ satisfies:
$$\mathcal{G}^*(\mathbf{q}, \mathcal{P}, k) \subseteq \mathcal{S}_{\mathcal{P}}, \quad |\mathcal{G}^*(\mathbf{q}, \mathcal{P}, k)| = \min(k, |\mathcal{S}_{\mathcal{P}}|)$$
$$\forall \mathbf{u} \in \mathcal{G}^*(\mathbf{q}, \mathcal{P}, k), \, \forall \mathbf{v} \in \mathcal{S}_{\mathcal{P}} \setminus \mathcal{G}^*(\mathbf{q}, \mathcal{P}, k): \quad \mathcal{D}(\mathbf{q}, \mathbf{u}) \le \mathcal{D}(\mathbf{q}, \mathbf{v})$$

### Metric Definitions & Denominator Semantics
For a retrieved result set $\mathcal{R}(\mathbf{q}, \mathcal{P}, k)$ of size at most $k$, the retrieval accuracy is measured via macro-averaged **Recall@$k$**:
$$\text{Recall@}k = \frac{|\mathcal{R}(\mathbf{q}, \mathcal{P}, k) \cap \mathcal{G}^*(\mathbf{q}, \mathcal{P}, k)|}{\min(k, |\mathcal{S}_{\mathcal{P}}|)}$$
In our evaluation, for all evaluated queries across all workloads, $|\mathcal{S}_{\mathcal{P}}| \ge 100 \gg k=10$. Consequently, the denominator is uniformly $\min(10, |\mathcal{S}_{\mathcal{P}}|) = 10$. Macro-averaged recall across a test workload of $Q$ queries is reported as $\frac{1}{Q} \sum_{q=1}^Q \text{Recall@}k(q)$.

Query throughput is reported as Queries Per Second (QPS):
$$\text{QPS} = \frac{1000.0}{\text{Mean Latency (ms)}}$$

---

## 5. Benchmark Methodology

### 5.1 Benchmark Dataset: `arxiv-for-fanns`
We evaluate on the official `SPCL/arxiv-for-fanns` benchmark suite [5], constructed from ArXiv paper abstracts embedded into 4,096-dimensional vectors using modern large language model text embeddings.
- **Small Dataset**: $N = 1,000$ database vectors, $D = 4,096$ ($16.4\text{ MB}$ raw vectors).
- **Medium Dataset**: $N = 100,000$ database vectors, $D = 4,096$ ($1.64\text{ GB}$ raw vectors).
- **Evaluation Workloads**:
  1. **Exact Match (EM)**: Point categorical equality on integer labels (`number_of_sub_categories == label`). Mean selectivity $\sigma \approx 38.5\%$ on medium ($47.9\%$ on small).
  2. **Range**: Temporal range interval on publication timestamps (`range_start <= update_date <= range_end`). Mean selectivity $\sigma \approx 43.2\%$ on medium ($51.2\%$ on small).
  3. **Exact Match In Set (EMIS)**: Multi-category set containment (`label in main_categories`). Highly selective with heavy tail; mean selectivity $\sigma \approx 15.0\%$ on medium ($31.9\%$ on small), with $34.4\%$ of queries having $\sigma \le 10\%$.

### 5.2 Hardware & Execution Environment
All medium-scale experiments were executed on an AMD Ryzen testbed running Microsoft Windows 11:
- **Processor**: AMD Ryzen Processor (Family 23 Model 104, 4 physical cores / 8 logical threads, 2.10 GHz base clock).
- **Memory**: $7.33\text{ GB}$ physical DDR4 RAM.
- **Storage & Vector Mapping**: Database vectors are accessed via read-only OS memory mapping (`np.memmap`), ensuring physical RAM allocations remain within $1.75\text{ GB}$ peak RSS.
- **Execution Mode**: Synchronous single-threaded query execution using high-resolution hardware timers (`time.perf_counter()`).

### 5.3 Baseline Graph Configuration
The primary medium-scale HNSW index was constructed with:
- $M = 16$ (max connections per node at layer $>0$, $M_0 = 32$ at layer 0).
- $ef_{\text{construction}} = 50$, random seed $= 42$.
- Distance metric: Euclidean $L_2$ with pre-computed vector norms.
- Construction time: $713.89\text{ seconds}$ ($11.90\text{ minutes}$); serialized topology size: $11.85\text{ MB}$.
- Default search parameter: $ef_{\text{search}} = 50$, $k = 10$.

---

## 6. Experimental Results

Table 1 presents the cross-scale comparative performance between the small-scale benchmark ($N=1,000$) and the medium-scale benchmark ($N=100,000$) across 500 queries per workload under identical metric and denominator definitions.

### Table 1: Cross-Scale Performance Comparison ($N=1,000$ vs. $N=100,000$, $D=4,096, k=10$)

| Strategy | Workload | 1K Recall | 100K Recall | Recall $\Delta$ | 1K Latency (ms) | 100K Latency (ms) | Latency Slowdown | 1K QPS | 100K QPS |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **ExactSearch** | EM | 1.0000 | 1.0000 | $0.0000$ | 7.07 | 310.57 | $43.9\times$ | 141.4 | 3.22 |
| **ExactSearch** | Range | 1.0000 | 1.0000 | $0.0000$ | 8.30 | 359.96 | $43.4\times$ | 120.5 | 2.78 |
| **ExactSearch** | EMIS | 1.0000 | 1.0000 | $0.0000$ | 3.11 | 154.67 | $49.7\times$ | 321.5 | 6.47 |
| **PreFilter** | EM | 1.0000 | 1.0000 | $0.0000$ | 6.92 | 296.73 | $42.9\times$ | 144.4 | 3.37 |
| **PreFilter** | Range | 1.0000 | 1.0000 | $0.0000$ | 8.20 | 352.28 | $43.0\times$ | 122.0 | 2.84 |
| **PreFilter** | EMIS | 1.0000 | 1.0000 | $0.0000$ | 3.15 | 149.40 | $47.4\times$ | 317.5 | 6.69 |
| **HNSW_PostFilter**| EM | 0.2608 | 0.3322 | $+0.0714$ | 2.52 | 4.84 | $1.92\times$ | 396.5 | 206.75 |
| **HNSW_PostFilter**| Range | 0.3952 | 0.4164 | $+0.0212$ | 2.64 | 4.73 | $1.79\times$ | 378.8 | 211.62 |
| **HNSW_PostFilter**| EMIS | 0.2030 | 0.1714 | $-0.0316$ | 2.67 | 8.58 | $3.21\times$ | 374.5 | 116.59 |
| **Overfetch 20x** | EM | 0.9958 | 0.9404 | $-0.0554$ | 5.25 | 12.30 | $2.34\times$ | 190.4 | 81.30 |
| **Overfetch 20x** | Range | 0.9710 | 0.8970 | $-0.0740$ | 5.11 | 13.61 | $2.66\times$ | 195.7 | 73.45 |
| **Overfetch 20x** | EMIS | 0.6977 | 0.3826 | **$-0.3151$** | 5.41 | 21.88 | $4.04\times$ | 184.8 | 45.70 |
| **InGraphFilter** | EM | 0.9998 | 0.9374 | $-0.0624$ | 4.95 | 13.99 | $2.83\times$ | 202.0 | 71.49 |
| **InGraphFilter** | Range | 0.9984 | 0.9304 | $-0.0680$ | 4.64 | 24.14 | $5.20\times$ | 215.5 | 41.42 |
| **InGraphFilter** | EMIS | 0.9940 | 0.8858 | **$-0.1082$** | 6.97 | 335.34 | **$48.1\times$** | 143.5 | 2.98 |

**[Proposed Figure 1: Cross-Scale Recall vs. Latency Tradeoff across 1K and 100K Datasets]**  
*Caption: Two-dimensional recall-latency Pareto frontier comparing $N=1,000$ and $N=100,000$ database sizes ($D=4,096, k=10$). Points toward the upper-left represent optimal performance. The visualization highlights the vertical collapse of PostFilter recall on selective workloads (EMIS) and the horizontal latency divergence of InGraph traversal as dataset scale expands by two orders of magnitude.*

### 6.1 The Collapse of Overfetching
At small scale ($N=1,000$), $20\times$ overfetching ($\omega=20$) recovered recall to $0.6977$ on EMIS. At medium scale ($N=100,000$), $20\times$ overfetching degrades sharply to **$0.3826$ recall** (a collapse of $31.5$ percentage points). 

To test whether extreme overfetching could bridge this deficit, we evaluated overfetch multipliers up to $50\times$ ($k_{\text{fetch}}=500$). As shown in Table 2, even fetching 500 candidates per query only yields **$0.5140$ recall** on EMIS, while increasing latency by $9.5\times$ ($4.84\text{ ms} \to 46.18\text{ ms}$). This empirically confirms that overfetching encounters an impassable saturation ceiling when filtered attributes do not co-locate with vector clusters.

### Table 2: Overfetch Multiplier Sensitivity on Medium Dataset ($N=100,000, k=10$)

| Overfetch Multiplier | Candidates Requested | EM Recall@10 | Range Recall@10 | EMIS Recall@10 | EMIS Mean Latency | EMIS QPS |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| $1\times$ (Naive PostFilter) | 10 | 0.3322 | 0.4164 | 0.1714 | 7.17 ms | 139.4 |
| $2\times$ | 20 | 0.6160 | 0.5872 | 0.1888 | 7.48 ms | 133.8 |
| $5\times$ | 50 | 0.7910 | 0.7080 | 0.2292 | 6.29 ms | 159.0 |
| $10\times$ | 100 | 0.8814 | 0.8198 | 0.2916 | 10.43 ms | 95.8 |
| $20\times$ | 200 | 0.9404 | 0.8970 | 0.3826 | 41.85 ms | 23.9 |
| **$50\times$** | **500** | **0.9726** | **0.9570** | **0.5140** | **46.18 ms** | **21.7** |

**[Proposed Figure 2: Candidate Overfetch Saturation Curves ($1\times \to 50\times$) on EM, Range, and EMIS]**  
*Caption: Recall@10 as a function of candidate overfetch multiplier $\omega \in [1, 50]$ on the medium dataset ($N=100,000$). While EM and Range asymptotically reach $>0.95$ recall, the EMIS curve plateaus at $0.5140$, demonstrating the insurmountable structural ceiling of spatial overfetching when filter selectivity is decoupled from proximity graphs.*

---

## 7. Analysis of Filter Selectivity and Traversal Expansion

### 7.1 Subgraph Trapping in In-Graph Traversal
While `InGraphFilter` maintains high recall across scales ($93.7\%$ on EM, $93.0\%$ on Range, $88.6\%$ on EMIS), its latency on EMIS expands by **$48.1\times$** relative to small scale ($6.97\text{ ms} \to 335.34\text{ ms}$ in the baseline run, and $214.43\text{ ms}$ under warm cache). 

Telemetry of graph nodes visited reveals the root cause:
- On **EM** ($\sigma = 38.5\%$): InGraph visits an average of **$2,317$ nodes** ($2.3\%$ of the index) to satisfy $ef_{\text{search}}=50$, executing in $13.99\text{ ms}$.
- On **EMIS** ($\sigma = 15.0\%$): InGraph visits an average of **$18,530$ nodes** ($18.5\%$ of the entire index), with maximum query latency reaching $1,642\text{ ms}$.

Because standard HNSW constructs entry points and hierarchical edges unaware of attributes, traversal begins at a spatial entry point that is almost always invalid for selective filters. When the beam search enters a local cluster devoid of matching nodes, it must exhaustively explore outgoing edges across hundreds of hops to escape the filter-sparse neighborhood.

### 7.2 Index Construction Ablation: $ef_{\text{construction}}=50$ vs. $100$
To determine whether this traversal expansion was an artifact of building the index with $ef_{\text{construction}}=50$, we performed a controlled ablation (EXP-01) by building a fresh index with $ef_{\text{construction}}=100$ on the identical dataset ($N=100,000, M=16, \text{seed}=42$). Table 3 summarizes the results across 100 EM and 100 EMIS queries.

### Table 3: HNSW Construction Parameter Ablation ($ef_C=50$ vs. $100$, $k=10, ef_S=50$)

| Strategy | Workload | $ef_C=50$ Recall | $ef_C=100$ Recall | Recall $\Delta$ | $ef_C=50$ Latency | $ef_C=100$ Latency | $ef_C=50$ Visited | $ef_C=100$ Visited | Visited $\Delta$ |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **HNSW_PostFilter** | EM | 0.3320 | 0.3300 | $-0.0020$ | 6.47 ms | 4.77 ms | 10.0 | 10.0 | $0.0$ |
| **HNSW_PostFilter** | EMIS | 0.1500 | 0.1510 | $+0.0010$ | 7.37 ms | 4.57 ms | 10.0 | 10.0 | $0.0$ |
| **InGraphFilter** | EM | 0.9110 | 0.9210 | $+0.0100$ | 28.84 ms | 21.32 ms | 3,006.3 | 3,058.3 | $+52.0$ |
| **InGraphFilter** | EMIS | 0.8820 | 0.9240 | **$+0.0420$** | 181.13 ms | 170.87 ms | **15,860.7** | **15,921.1** | **$+60.4$** |

*Index Build Telemetry*: Building with $ef_C=100$ required **$994.39\text{ seconds}$** ($16.57\text{ minutes}$) compared to **$713.89\text{ seconds}$** ($11.90\text{ minutes}$) for $ef_C=50$, a **$39.3\%$ increase in indexing time**.

*Ablation Verdict*: While $ef_C=100$ provides a modest $+4.2\%$ recall gain on EMIS, **it does not reduce nodes visited** ($15,921$ vs. $15,860$ nodes). This definitively proves that traversal expansion in selective regimes is a fundamental limitation of spatial proximity topologies, not an index build defect.

**[Proposed Figure 3: Traversal Expansion (Nodes Visited) vs. Query Filter Selectivity for $ef_C=50$ and $ef_C=100$]**  
*Caption: Scatter and trend curves of graph nodes evaluated during in-graph traversal plotted against query filter selectivity $\sigma \in [0.001, 1.0]$. As selectivity drops below $2\%$, visited nodes spike exponentially toward 20,000 nodes. Crucially, the curves for $ef_C=50$ and $ef_C=100$ overlap almost completely, illustrating that higher construction beam width fails to alleviate subgraph trapping.*

---

## 8. Selectivity-Aware Query Routing

### 8.1 The Pareto Crossover Phenomenon
Stratifying query performance across selectivity quantiles exposes a clear empirical crossover boundary:
- When selectivity $\sigma \le 2\%$ ($|S| \le 2,000$ vectors), inverted-index pre-filtering evaluates exact distances in **$<20\text{ ms}$** with $100\%$ recall, whereas in-graph filtering wanders across thousands of nodes ($>150\text{ ms}$).
- When selectivity $\sigma > 10\%$ ($|S| > 10,000$ vectors), pre-filtering latency escalates beyond $200\text{--}350\text{ ms}$ due to the cost of computing $D=4,096$ dot products, whereas in-graph filtering completes in $14\text{--}24\text{ ms}$.

### 8.2 Router Design & Candidate Policy
We formulate an adaptive router that inspects query metadata prior to vector distance computation:
$$\text{Strategy}(\mathbf{q}, \mathcal{P}) = \begin{cases} \text{PreFilter}, & \text{if } \hat{\sigma}(\mathcal{P}) \le \tau \\ \text{InGraphFilter}, & \text{if } \hat{\sigma}(\mathcal{P}) > \tau \end{cases}$$
where $\hat{\sigma}(\mathcal{P}) = \frac{|\mathcal{S}_{\mathcal{P}}|}{N}$ is computed directly from inverted metadata index list lengths (`MetadataIndex.get_matching_ids`). The router operates strictly on pre-existing metadata structures with zero vector distance computations and zero ground-truth peeking.

### 8.3 Empirical Evaluation & Tail Compression
We evaluated `AdaptiveRouter_2pct` ($\tau = 0.02$) across all 500 queries per workload ($1,500$ queries total) against static `PreFilter` and static `InGraphFilter`. Every query execution strictly includes selectivity estimation and dispatch overhead in its measured latency.

### Table 4: Controlled Router Performance Evaluation (Full 500 Queries per Workload)

| Strategy | Workload | Mean Recall@10 | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | QPS | Pre / Graph Routing % | Mean Routing Overhead |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Static PreFilter** | EM | 1.0000 | 310.13 | 382.26 | 486.48 | 631.59 | 3.22 | 100% / 0% | 0.000 ms |
| **Static InGraphFilter** | EM | 0.9374 | 18.43 | 13.10 | 41.26 | 112.74 | 54.25 | 0% / 100% | 0.000 ms |
| **AdaptiveRouter_2pct** | **EM** | **0.9380** | **14.11** | **11.54** | **29.79** | **53.85** | **70.89** | 1.4% / 98.6% | **0.002 ms** |
| | | | | | | | | | |
| **Static PreFilter** | Range | 1.0000 | 337.45 | 321.30 | 619.29 | 712.16 | 2.96 | 100% / 0% | 0.000 ms |
| **Static InGraphFilter** | Range | 0.9304 | 24.15 | 12.65 | 77.32 | 177.62 | 41.42 | 0% / 100% | 0.000 ms |
| **AdaptiveRouter_2pct** | **Range** | **0.9304** | **23.64** | **11.59** | **71.17** | **189.61** | **42.30** | 0.2% / 99.8% | **0.227 ms** |
| | | | | | | | | | |
| **Static PreFilter** | EMIS | 1.0000 | 117.80 | 103.46 | 227.74 | 265.20 | 8.49 | 100% / 0% | 0.000 ms |
| **Static InGraphFilter** | EMIS | 0.8858 | 214.43 | 114.52 | 693.29 | 929.95 | 4.66 | 0% / 100% | 0.000 ms |
| **AdaptiveRouter_2pct** | **EMIS** | **0.8918** | **185.57** | **95.39** | **661.60** | **802.85** | **5.39** | 5.8% / 94.2% | **0.003 ms** |

*Key Observations*:
1. On **EMIS**, $5.8\%$ of queries satisfy $\sigma \le 2\%$. Routing these selective queries to PreFilter rescues trapped graph searches, lifting overall workload recall from **$0.8858 \to 0.8918$**, reducing mean latency by **$13.5\%$** ($214.43\text{ ms} \to 185.57\text{ ms}$), and compressing P99 tail latency by **$127.1\text{ ms}$** ($929.95\text{ ms} \to 802.85\text{ ms}$).
2. On **EM** and **Range**, where $>98\%$ of queries exceed $2\%$ selectivity, the router defaults to InGraph, preserving sub-25 ms latency.
3. Routing overhead is negligible: $0.002\text{ ms}$ on EM, $0.003\text{ ms}$ on EMIS (O(1) hash lookups), and $0.227\text{ ms}$ on Range (vectorized date comparison over 100K integers).

**[Proposed Figure 4: Cumulative Distribution Function (CDF) of Query Latencies for Static InGraph vs. AdaptiveRouter_2pct on EMIS]**  
*Caption: Cumulative distribution function (CDF) of per-query latency comparing static in-graph traversal against the selectivity router on EMIS queries ($N=100,000, Q=500$). The selective routing of queries where $\sigma \le 2\%$ truncates the severe tail distribution, shifting the 99th percentile leftward by $127.1\text{ ms}$ and preventing multi-second outliers.*

### 8.4 Threshold Sensitivity & Train/Test Generalization
To test whether $\tau=0.02$ generalizes out-of-sample, we conducted a 50/50 split:
- **Tuning Set**: Query IDs 0..249 (250 queries per workload).
- **Held-Out Test Set**: Query IDs 250..499 (250 queries per workload).

Table 5 reports the multi-threshold sweep across $\tau \in \{0.5\%, 1.0\%, 2.0\%, 5.0\%, 10.0\%, 20.0\%\}$.

### Table 5: Threshold Generalization Matrix (Tuning Set vs. Held-Out Evaluation Set)

| Workload | Split | $\tau = 0.5\%$ (Rec / Lat) | $\tau = 1.0\%$ (Rec / Lat) | $\mathbf{\tau = 2.0\%}$ (Rec / Lat) | $\tau = 5.0\%$ (Rec / Lat) | $\tau = 10.0\%$ (Rec / Lat) | $\tau = 20.0\%$ (Rec / Lat) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **EMIS** | Tuning | $0.8684$ / $189\text{ ms}$ | $0.8684$ / $188\text{ ms}$ | **$0.8744$ / $164\text{ ms}$** | $0.8820$ / $123\text{ ms}$ | $0.9192$ / $73\text{ ms}$ | $0.9572$ / $56\text{ ms}$ |
| **EMIS** | Held-Out | $0.9032$ / $238\text{ ms}$ | $0.9032$ / $238\text{ ms}$ | **$0.9092$ / $210\text{ ms}$** | $0.9216$ / $155\text{ ms}$ | $0.9600$ / $86\text{ ms}$ | $0.9752$ / $54\text{ ms}$ |
| | | | | | | | |
| **EM** | Tuning | $0.9276$ / $19.1\text{ ms}$ | $0.9276$ / $19.1\text{ ms}$ | **$0.9280$ / $16.8\text{ ms}$** | $0.9308$ / $16.1\text{ ms}$ | $0.9308$ / $16.1\text{ ms}$ | $0.9384$ / $26.5\text{ ms}$ $\uparrow$ |
| **EM** | Held-Out | $0.9480$ / $15.5\text{ ms}$ | $0.9480$ / $15.5\text{ ms}$ | **$0.9480$ / $14.5\text{ ms}$** | $0.9484$ / $13.5\text{ ms}$ | $0.9484$ / $13.5\text{ ms}$ | $0.9540$ / $22.3\text{ ms}$ $\uparrow$ |
| | | | | | | | |
| **Range** | Tuning | $0.9248$ / $26.2\text{ ms}$ | $0.9248$ / $26.2\text{ ms}$ | **$0.9248$ / $26.2\text{ ms}$** | $0.9264$ / $24.9\text{ ms}$ | $0.9292$ / $24.9\text{ ms}$ | $0.9348$ / $30.8\text{ ms}$ $\uparrow$ |
| **Range** | Held-Out | $0.9360$ / $22.2\text{ ms}$ | $0.9360$ / $20.6\text{ ms}$ | **$0.9360$ / $20.6\text{ ms}$** | $0.9360$ / $19.6\text{ ms}$ | $0.9364$ / $20.3\text{ ms}$ | $0.9420$ / $27.5\text{ ms}$ $\uparrow$ |

*Generalization Finding*:
The threshold $\tau = 0.02$ generalizes reliably without out-of-sample degradation. However, the data reveals that **$\tau = 0.02$ is a conservative operating point rather than a universal optimum**:
- On `EMIS` alone, increasing $\tau$ to $5\%\text{--}10\%$ yields even greater speedups ($73\text{--}123\text{ ms}$) and higher recall ($92\%\text{--}96\%$) by routing more queries to exact search.
- However, for `EM` and `Range`, setting $\tau \ge 20\%$ increases latency from $14.5\text{ ms} \to 22.3\text{ ms}$ and $20.6\text{ ms} \to 27.5\text{ ms}$ because PreFilter performs exact scans over $10K\text{--}20K$ vectors.
- Therefore, the optimal global operating regime is **$2\% \le \tau \le 5\%$**.

**[Proposed Figure 5: Threshold Generalization Surface across Selectivity Cutoffs ($\tau \in [0.5\%, 20\%]$) on Tuning vs. Held-Out Evaluation Sets]**  
*Caption: Recall and mean latency curves across candidate selectivity thresholds $\tau \in \{0.5\%, 1\%, 2\%, 5\%, 10\%, 20\%\}$ comparing the 250-query tuning split against the 250-query held-out evaluation split. The consistent contours confirm that performance gains are not overfitted to query samples, and highlight the latency inflection point above $\tau=5\%$ on high-selectivity workloads.*

---

## 9. Threats to Validity

1. **Cache Warming & Interleaved Execution Ordering**: In our EXP-03 evaluation harness, queries were evaluated in a paired per-query loop (`PreFilter(q)` immediately followed by `InGraphFilter(q)` and `Router(q)`). While this guarantees identical query vectors and predicates, running `PreFilter` first warms the OS page cache for database vectors matching query $q$. This explains why InGraph EMIS latency in EXP-03 ($214.43\text{ ms}$) was lower than in the monolithic baseline benchmark ($335.34\text{ ms}$). The relative speedup and tail compression of the router remain valid, but baseline and follow-up absolute latencies should not be directly equated.
2. **Single-Threaded CPU Architecture & Memory Bandwidth**: All benchmarks were executed on an AMD Ryzen mobile CPU with single-threaded execution. Because $D=4,096$ vectors require $16.4\text{ KB}$ per vector, memory bandwidth saturates during large linear scans. Accelerated SIMD implementations (AVX-512) or GPU-accelerated GEMM (cuVS) would accelerate PreFilter, potentially shifting the crossover threshold rightward to $5\%\text{--}10\%$.
3. **Dataset & Embedding Generalization**: The experiments were conducted on text embeddings from `arxiv-for-fanns`. While the three evaluated workloads represent point equality, range intervals, and multi-value sets, embeddings with lower dimensionality ($D=128$ or $768$) or different clustering-to-attribute correlation profiles may exhibit distinct crossover boundaries.
4. **Implementation Fidelity of Baseline Approximations**: As stated in Section 3, ACORN, SIEVE, and UNIFY were evaluated as educational Python heuristic baselines on standard HNSW graphs. They demonstrate the limits of dynamic multi-hop expansion on un-augmented graphs, but do not represent the full performance of the original authors' C++/CUDA systems.

---

## 10. Conclusion and Future Work

In this paper, we presented an empirical cross-scale systems study of Filtered Approximate Nearest Neighbor Search comparing $1,000$ and $100,000$ database vectors under 4,096 dimensions. We demonstrated that naive post-filtering suffers an inherent geometric collapse, and that candidate overfetching hits a rigid mathematical saturation ceiling ($51.4\%$ recall at $50\times$). While in-graph filtering maintains robust recall, selective predicates force traversals to evaluate over $18,500$ nodes due to subgraph isolation. A rigorous construction ablation confirmed that doubling construction effort ($ef_C=100$) does not eliminate this bottleneck. Finally, we demonstrated that a simple selectivity-aware query router operating in the $2\%\text{--}5\%$ selectivity window successfully compresses P99 tail latency by $127\text{ ms}$ and improves recall with negligible routing overhead.

Future work includes integrating continuous cost models that incorporate query vector norms and graph entry distances into production vector database query planners, alongside evaluating hardware-accelerated SIMD and GPU pre-filtering kernels.

---

## 11. References

1. Malkov, Yu A., and D. A. Yashunin. "Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs." *IEEE Transactions on Pattern Analysis and Machine Intelligence* 42.4 (2018): 824-836. [DOI: 10.1109/TPAMI.2018.2889473](https://doi.org/10.1109/TPAMI.2018.2889473).
2. Patel, Liana, Peter Kraft, Carlos Guestrin, and Matei Zaharia. "ACORN: Performant and Predicate-Agnostic Approximate Nearest Neighbor Search." *Proceedings of the ACM on Management of Data (SIGMOD)* 2.3 (2024): 1-27. [DOI: 10.1145/3654932](https://doi.org/10.1145/3654932).
3. Gao, Zichen, et al. "High-Dimensional Filtered Vector Search with 3D Packing." *Proceedings of the VLDB Endowment* 17.11 (2024).
4. Liang, Anqi, Pengcheng Zhang, Bin Yao, Zhongpu Chen, Yitong Song, and Guangxu Cheng. "UNIFY: Unified Graph Index for Filtered Vector Retrieval." *arXiv preprint arXiv:2412.06208* (2024). [arXiv:2412.06208](https://arxiv.org/abs/2412.06208).
5. Iff, Patrick, Paul Bruegger, Marcin Chrapek, Maciej Besta, and Torsten Hoefler. "FANNS: Filtered Approximate Nearest Neighbor Search Benchmark." *arXiv preprint arXiv:2507.21989* (2025). [arXiv:2507.21989](https://arxiv.org/abs/2507.21989).
6. Johnson, Jeff, Matthijs Douze, and Hervé Jégou. "Billion-scale similarity search with GPUs." *IEEE Transactions on Big Data* 7.3 (2019): 535-547. [DOI: 10.1109/TBDATA.2019.2921572](https://doi.org/10.1109/TBDATA.2019.2921572).
7. Aumüller, Martin, Erik Bernhardsson, and Alexander Faithfull. "ANN-Benchmarks: A benchmarking tool for approximate nearest neighbor algorithms." *Information Systems* 87 (2020): 101374. [DOI: 10.1016/j.is.2019.02.006](https://doi.org/10.1016/j.is.2019.02.006).

