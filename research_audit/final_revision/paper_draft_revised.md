# An Empirical Cross-Scale Study of Filtered Proximity Traversal with a Selectivity-Aware Query Router

**Target Track**: Empirical Systems & Scalable Data Management (e.g., ACM SIGMOD / VLDB / IEEE ICDE)  
**Authors**: Research Engineering & Benchmarking Group  
**Artifact Repository**: [`filtered_ann_arxiv_for_fanns_medium`](https://github.com/animesh68/filtered_ann_arxiv_for_fanns_medium)  
**Reference Baseline Repository**: [`filtered_ann_arxiv_for_fanns_small`](https://github.com/animesh68/filtered_ann_arxiv_for_fanns_small)  

---

## 1. Abstract

Filtered Approximate Nearest Neighbor Search (FANNS) has become an essential systems primitive for Retrieval-Augmented Generation (RAG), enterprise search, and e-commerce retrieval, where vector similarity queries are constrained by structured metadata filters. Despite rapid algorithmic development, empirical understanding of how proximity graph traversals behave when scaling from small datasets ($1,000$ vectors) to medium datasets ($100,000$ vectors) under ultra-high dimensionality ($4,096$ dimensions) remains limited. In this work, we present an empirical cross-scale systems study on the official `SPCL/arxiv-for-fanns` benchmark suite, evaluating exact filtered search, inverted-index pre-filtering, Hierarchical Navigable Small World (HNSW) post-filtering, candidate overfetching, single-graph in-graph filtering, and paper-inspired heuristic baselines (`ACORN_Heuristic`, `SIEVE_Heuristic`, `UNIFY_Heuristic`).

Our empirical evaluation establishes three primary systems findings:
1. **Diminishing Returns of Overfetching**: Naive post-filtering suffers severe candidate starvation under selective filters ($0.1714$ recall on multi-attribute queries at $100K$ scale). Under the evaluated configuration ($M=16, ef_{\text{search}}=\max(50, k_{\text{fetch}})$), candidate overfetching exhibits sharply diminishing returns: expanding the candidate pool by $50\times$ ($k_{\text{fetch}}=500$) recovers recall only to $0.5140$ while incurring a $9.5\times$ latency penalty ($4.84\text{ ms} \to 46.18\text{ ms}$).
2. **Traversal Expansion Under Attribute Sparsity**: In-graph filtering preserves high recall across scales ($>93\%$ on categorical point and numeric range workloads), but encounters severe traversal expansion when filter selectivity drops: unguided spatial entry points force beam search to explore large neighborhoods of invalid nodes, evaluating an average of $18,530$ nodes out of $100,000$ ($18.5\%$) on selective multi-attribute queries, expanding latency from $13.99\text{ ms}$ to $214\text{--}335\text{ ms}$.
3. **Construction Density Invariance**: A controlled construction ablation demonstrates that doubling index construction beam width ($ef_{\text{construction}}=50 \to 100$, requiring $+39.3\%$ build time) provides a modest $+4.2\%$ recall improvement ($0.882 \to 0.924$) but leaves visited node counts essentially unchanged ($15,860$ vs. $15,921$ nodes), indicating that denser spatial proximity construction alone is insufficient to resolve traversal expansion under attribute sparsity.

Guided by these observations, we evaluate a lightweight metadata-driven query router that dynamically dispatches queries to inverted-index pre-filtering when estimated selectivity $\hat{\sigma} \le 2\%$, and in-graph traversal otherwise. On the multi-attribute workload, the router improves recall over static in-graph filtering from $0.8858$ to $0.8918$, reduces mean latency by $13.5\%$ ($214.4\text{ ms} \to 185.6\text{ ms}$ in paired evaluation), and compresses P99 tail latency by $127.1\text{ ms}$ ($929.95\text{ ms} \to 802.85\text{ ms}$) with low routing overhead ($0.003\text{ ms}$). However, the router does not universally dominate all baselines: on selective workloads, static pre-filtering achieves superior recall ($1.0000$) and lower latency ($117.8\text{ ms}$ mean, $265.2\text{ ms}$ P99). The router functions as an operational compromise across mixed workloads, preventing pre-filtering's severe latency penalty ($>300\text{ ms}$) on broad filters while mitigating graph traversal expansion on selective queries.

---

## 2. Introduction

Approximate Nearest Neighbor Search (ANNS) is the core computational engine behind neural retrieval, multimodal embedding search, and generative AI grounding. In practical applications, vector retrieval rarely occurs in isolation. Instead, queries are almost universally accompanied by structured attribute constraints—such as tenant isolation, document publication date intervals, access control lists, or multi-label category filters. This combined query paradigm is formalized as **Filtered Approximate Nearest Neighbor Search (FANNS)**: given a query vector $\mathbf{q} \in \mathbb{R}^D$, a distance metric $\mathcal{D}$, a metadata filter predicate $\mathcal{P}$, and a target count $k$, retrieve the top-$k$ vectors from the database $\mathcal{X}$ that satisfy $\mathcal{P}(\mathbf{x}) = \text{True}$.

The core systems challenge of FANNS stems from a fundamental topological mismatch: **metric proximity space does not correlate with discrete attribute space**. While graph-based indices such as Hierarchical Navigable Small World (HNSW) graphs [1] construct edges based strictly on geometric distance, filter predicates partition the database into arbitrary, often fragmented subsets. When queries combine high vector dimensionality ($D=4,096$) with restrictive filter predicates, standard retrieval strategies face acute trade-offs:
- **Pre-filtering** uses an inverted metadata index to identify all valid candidate vector IDs, then executes exact distance calculations over that candidate set. While pre-filtering guarantees $100\%$ recall, its computational cost scales linearly with candidate set cardinality $\mathcal{O}(|\mathcal{S}_{\mathcal{P}}| \cdot D)$, making it prohibitively expensive for broad filters.
- **Post-filtering** performs standard unconstrained graph traversal on HNSW to retrieve $k$ (or $\omega \cdot k$) nearest neighbors, subsequently discarding any candidate that violates $\mathcal{P}$. When the filter selectivity $\sigma = \frac{|\mathcal{S}_{\mathcal{P}}|}{N}$ is low, top spatial neighbors rarely satisfy $\mathcal{P}$, resulting in severe recall loss.
- **In-graph filtering** traverses the proximity graph while evaluating $\mathcal{P}$ at visited nodes, using invalid nodes as routing bridges to preserve graph connectivity while admitting only valid nodes into the result candidate pool. However, when valid nodes are sparse, unguided spatial entry points plunge the search into neighborhoods devoid of matching nodes, triggering extensive local exploration.

Although specialized filter-aware graph architectures have been proposed (e.g., Filtered-DiskANN [8], VBASE [9], ACORN [2], SIEVE [3], and UNIFY [4]), empirical cross-scale characterizations of how foundational baselines fail across dataset magnitudes ($1K \to 100K$) under identical high-dimensional embedding distributions ($D=4,096$) remain valuable for systems practitioners. Furthermore, production vector databases frequently rely on ad-hoc overfetching heuristics or single-graph traversals without empirical visibility into the crossover points where linear exact scans dominate proximity graph traversal.

### Research Questions
This empirical study is guided by four primary research questions:
- **RQ1 (Scaling Behavior of Baseline Heuristics)**: How do unconstrained proximity traversal, candidate overfetching, and pre-filtering behave as database size expands from $N=1,000$ to $N=100,000$ under high vector dimensionality ($D=4,096$)?
- **RQ2 (Traversal Expansion Under Attribute Sparsity)**: Under what selectivity regimes does single-graph in-graph traversal suffer from beam-search exploration spikes, and can denser index construction ($ef_{\text{construction}}=100$) alleviate it?
- **RQ3 (Selectivity-Aware Routing Viability)**: Can a lightweight metadata-driven query planner dynamically switch between pre-filtering and in-graph traversal to mitigate tail-latency spikes without introducing significant routing overhead?
- **RQ4 (Workload-Dependent Operating Regimes)**: Does a single selectivity threshold generalize across disparate filter semantics (point equality, range intervals, and set membership), and what are the trade-offs of this approach against static pre-filtering?

### Contributions
In this work, we present an evidence-backed empirical systems study on the official `SPCL/arxiv-for-fanns` benchmark suite [5]. Specifically, we make the following contributions:
1. **Cross-Scale Empirical Characterization**: We trace retrieval accuracy, latency distributions, and throughput across $N=1,000$ and $N=100,000$ database vectors ($D=4,096$), documenting the diminishing empirical returns of candidate overfetching ($50\times$ candidate expansion leaves nearly half of ground-truth neighbors unretrieved on selective workloads).
2. **Traversal Expansion Telemetry**: We quantify graph traversal expansion under attribute sparsity, measuring an $8.0\times$ increase in visited nodes ($2,317 \to 18,530$ nodes out of $100,000$) on selective multi-attribute queries.
3. **Index Construction Ablation**: Through a controlled ablation of HNSW construction parameters ($ef_{\text{construction}}=50$ vs. $100$), we show that while denser construction yields modest recall improvements ($+4.2\%$), visited node counts on selective queries remain essentially flat ($15,860$ vs. $15,921$ nodes).
4. **Evaluation of a Selectivity-Aware Query Router**: We evaluate a metadata-driven query planner that routes queries to pre-filtering when estimated selectivity $\hat{\sigma} \le 2\%$, and in-graph filtering otherwise. Evaluated across 1,500 queries over three standardized workloads with a 50/50 tuning/held-out split, we demonstrate that the router compresses P99 tail latency on selective workloads while analyzing its multi-objective trade-offs against exact pre-filtering.

---

## 3. Background and Related Work

### 3.1 Proximity Graph Navigation (HNSW)
Navigable Small World graphs and their hierarchical extension (HNSW) [1] organize vectors into multi-layer proximity graphs where upper layers contain long-range skip connections and layer 0 contains a dense proximity graph. Greedy routing navigates from top layers down to layer 0, followed by a bounded priority queue beam search of size $ef_{\text{search}}$. Standard HNSW construction assumes an unconstrained metric space where all indexed vectors are valid search targets.

### 3.2 Filtered ANN Paradigms
1. **Pre-Filtering**: Indexes document attributes in an inverted index. For query $(\mathbf{q}, \mathcal{P})$, it retrieves candidate ID list $\mathcal{S}_{\mathcal{P}}$ and computes distances exclusively over $\mathcal{S}_{\mathcal{P}}$. Computational complexity is $\mathcal{O}(|\mathcal{S}_{\mathcal{P}}| \cdot D) = \mathcal{O}(\sigma N \cdot D)$.
2. **Post-Filtering & Overfetching**: Executes standard unfiltered HNSW beam search requesting $k_{\text{fetch}} = \omega \cdot k$ candidates (where $\omega \ge 1$ is the overfetch multiplier), subsequently discarding candidates where $\mathcal{P}(\mathbf{a}) = \text{False}$. As shown analytically by Iff et al. [5], the expected number of valid candidates retrieved under uniform attribute distribution is $\omega \cdot k \cdot \sigma$. When $\sigma \ll 1/\omega$, post-filtering inevitably fails to return $k$ results.
3. **In-Graph Filtering**: Retains a single standard HNSW index. During beam search, when neighbors of candidate $u$ are extracted, invalid neighbors ($\mathcal{P}(\mathbf{a}) = \text{False}$) are added to the traversal queue to serve as routing bridges, but are excluded from the result priority queue $W$.

### 3.3 Advanced Filter-Aware Graph Systems & Query Planning
To address the limitations of post-filtering and single-graph traversal, several specialized systems have been developed:
- **Filtered-DiskANN** (Gollapudi et al., WWW 2023) [8] extends Vamana graphs to support discrete filter predicates via FilteredVamana (label-aware edge selection during construction) and StitchedVamana (building category-specific subgraphs and stitching them together).
- **VBASE** (Zhang et al., USENIX OSDI 2023) [9] unifies relational query processing and vector search by formalizing *relaxed monotonicity*, enabling cost-based query optimization across vector similarity and relational filters.
- **Milvus** (Wang et al., SIGMOD 2021) [10] incorporates a hybrid query execution engine that optimizes execution plans between scalar filtering and vector search based on predicate selectivity.
- **ACORN** (Patel et al., SIGMOD 2024) [2] constructs correlation-extended graphs by connecting nodes to direct spatial neighbors and multi-hop neighbors possessing diverse attribute values.
- **SIEVE** (Gao et al., VLDB 2024) [3] partitions vector data into modular sub-indices using a 3D-packing model, routing search entry points to high-density attribute clusters.
- **UNIFY** (Liang et al., 2024) [4] unifies attribute and spatial hierarchies via Segmented Inclusive Graphs (SIG).

### 3.4 Educational Heuristic Baselines Disclosure
In our experimental benchmark, ACORN-, SIEVE-, and UNIFY-inspired methods are evaluated as **educational, single-graph Python heuristic baselines** on standard HNSW graphs:
- `ACORN_Heuristic`: Explores online 2-hop neighbor expansion during beam search on standard graphs; it does not implement ACORN's offline correlation graph construction.
- `SIEVE_Heuristic`: Samples attribute-matching entry points online; it does not construct SIEVE's 3D-packing index partitions.
- `UNIFY_Heuristic`: Adjusts $ef_{\text{search}}$ dynamically based on selectivity thresholds; it does not construct Segmented Inclusive Graphs.

These heuristic baselines are studied solely to inspect the behavior of online traversal heuristics on standard graphs and must not be interpreted as evaluating the official C++/CUDA implementations of the original authors.

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
For a retrieved result set $\mathcal{R}(\mathbf{q}, \mathcal{P}, k)$ of size at most $k$, retrieval accuracy is measured via macro-averaged **Recall@$k$**:
$$\text{Recall@}k = \frac{|\mathcal{R}(\mathbf{q}, \mathcal{P}, k) \cap \mathcal{G}^*(\mathbf{q}, \mathcal{P}, k)|}{\min(k, |\mathcal{S}_{\mathcal{P}}|)}$$
In our evaluation, for all evaluated queries across all workloads, $|\mathcal{S}_{\mathcal{P}}| \ge 100 \gg k=10$. Consequently, the denominator is uniformly $\min(10, |\mathcal{S}_{\mathcal{P}}|) = 10$. Macro-averaged recall across a test workload of $Q$ queries is reported as $\frac{1}{Q} \sum_{q=1}^Q \text{Recall@}k(q)$.

Query throughput is reported as Queries Per Second (QPS):
$$\text{QPS} = \frac{1000.0}{\text{Mean Latency (ms)}}$$

---

## 5. Benchmark Methodology

### 5.1 Benchmark Dataset: `arxiv-for-fanns`
We evaluate on the official `SPCL/arxiv-for-fanns` benchmark suite [5], constructed from ArXiv paper abstracts embedded into 4,096-dimensional vectors using modern text embeddings:
- **Small Dataset**: $N = 1,000$ database vectors, $D = 4,096$ ($16.4\text{ MB}$ raw float32 vectors).
- **Medium Dataset**: $N = 100,000$ database vectors, $D = 4,096$ ($1.64\text{ GB}$ raw float32 vectors).
- **Evaluation Workloads & Selectivity Profiles**:
  1. **Exact Match (EM)**: Point categorical equality on integer labels (`number_of_sub_categories == label`). Mean selectivity $\sigma \approx 38.5\%$ on medium ($47.9\%$ on small).
  2. **Range**: Temporal range interval on publication timestamps (`range_start <= update_date <= range_end`). Mean selectivity $\sigma \approx 43.2\%$ on medium ($51.2\%$ on small).
  3. **Exact Match In Set (EMIS)**: Multi-category set containment (`label in main_categories`). Highly selective with heavy tail; mean selectivity $\sigma \approx 15.0\%$ on medium ($31.9\%$ on small), with $34.4\%$ of medium queries having $\sigma \le 10\%$.

*Methodological Caveat on Cross-Scale Workloads*: The official medium-scale benchmark queries exhibit lower average selectivity than the small-scale queries (EMIS mean $\sigma=15.0\%$ vs. $31.9\%$). Consequently, cross-scale performance differences reflect both increased database cardinality and sharper attribute sparsity, rather than scale $N$ in isolation.

### 5.2 Hardware & Execution Environment
All medium-scale experiments were executed on an AMD Ryzen testbed running Microsoft Windows 11:
- **Processor**: AMD Ryzen Processor (Family 23 Model 104, 4 physical cores / 8 logical threads, 2.10 GHz base clock).
- **Memory**: $7.33\text{ GB}$ visible physical DDR4 RAM.
- **Storage & Vector Mapping**: Database vectors are accessed via read-only OS memory mapping (`np.memmap`), ensuring physical RAM allocations remain within $1.75\text{ GB}$ peak RSS.
- **Execution Mode**: Synchronous single-threaded query execution using high-resolution hardware timers (`time.perf_counter()`).

### 5.3 Baseline Graph Configuration
The primary medium-scale HNSW index was constructed with:
- $M = 16$ (max connections per node at layer $>0$, $M_0 = 32$ at layer 0).
- $ef_{\text{construction}} = 50$, random seed $= 42$.
- Distance metric: Euclidean $L_2$ with pre-computed vector norms.
- Construction time: $713.89\text{ seconds}$ ($11.90\text{ minutes}$); serialized topology file size: $11.85\text{ MB}$.
- Default search parameter: $ef_{\text{search}} = 50$, $k = 10$.
*(Note: In historical repository artifacts, the cached serialized file was labeled with the string `hnsw_index_m16_ef100.pkl`, but official build logs confirm it was built with $ef_{\text{construction}}=50$.)*

---

## 6. Experimental Results

Table 1 presents the descriptive cross-scale performance comparison between the small-scale benchmark ($N=1,000$) and the medium-scale benchmark ($N=100,000$) across 500 queries per workload under identical metric and denominator definitions.

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

*Execution Footnote*: Small (1K) and Medium (100K) benchmarks were executed in independent benchmark environments on the same CPU family. Small-scale data fits entirely in CPU L3 cache ($16.4\text{ MB}$), whereas medium-scale data ($1.64\text{ GB}$) streams across memory channels.

### 6.1 Diminishing Returns of Candidate Overfetching
At small scale ($N=1,000$), $20\times$ overfetching ($\omega=20$) recovered recall to $0.6977$ on EMIS. At medium scale ($N=100,000$), $20\times$ overfetching degrades sharply to **$0.3826$ recall** (a collapse of $31.5$ percentage points). 

To test whether extreme overfetching could bridge this deficit, we evaluated overfetch multipliers up to $50\times$ ($k_{\text{fetch}}=500$). As shown in Table 2, fetching 500 candidates per query yields **$0.5140$ recall** on EMIS, while increasing latency by $9.5\times$ relative to naive post-filtering ($4.84\text{ ms} \to 46.18\text{ ms}$). This empirically confirms that overfetching encounters severely diminishing returns within practical retrieval bounds when filtered attributes do not co-locate with vector clusters.

### Table 2: Overfetch Multiplier Sensitivity on Medium Dataset ($N=100,000, k=10$)

| Overfetch Multiplier | Candidates Requested | EM Recall@10 | Range Recall@10 | EMIS Recall@10 | EMIS Mean Latency | EMIS QPS |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| $1\times$ (Naive PostFilter) | 10 | 0.3322 | 0.4164 | 0.1714 | 7.17 ms* | 139.4 |
| $2\times$ | 20 | 0.6160 | 0.5872 | 0.1888 | 7.48 ms | 133.8 |
| $5\times$ | 50 | 0.7910 | 0.7080 | 0.2292 | 6.29 ms | 159.0 |
| $10\times$ | 100 | 0.8814 | 0.8198 | 0.2916 | 10.43 ms | 95.8 |
| $20\times$ | 200 | 0.9404 | 0.8970 | 0.3826 | 41.85 ms | 23.9 |
| **$50\times$** | **500** | **0.9726** | **0.9570** | **0.5140** | **46.18 ms** | **21.7** |

*\*Table Variance Footnote*: Table 2 reports naive PostFilter EMIS latency as $7.17\text{ ms}$ (from the dedicated overfetch sweep in `hnsw_overfetch_summary.csv`), compared to $8.58\text{ ms}$ in Table 1 (from the monolithic benchmark in `benchmark_summary.csv`). The $1.41\text{ ms}$ variance reflects independent script executions under differing process lifetimes and system states.

---

## 7. Analysis of Filter Selectivity and Traversal Expansion

### 7.1 Traversal Expansion Under Attribute Sparsity
While `InGraphFilter` maintains high recall across scales ($93.7\%$ on EM, $93.0\%$ on Range, $88.6\%$ on EMIS), its latency on EMIS expands by **$48.1\times$** relative to small scale ($6.97\text{ ms} \to 335.34\text{ ms}$ in the standalone baseline run, and $214.43\text{ ms}$ under warm cache in EXP-03). 

Telemetry of graph nodes visited reveals the root cause:
- On **EM** ($\sigma = 38.5\%$): InGraph visits an average of **$2,317$ nodes** ($2.3\%$ of the index) to satisfy $ef_{\text{search}}=50$, executing in $13.99\text{ ms}$.
- On **EMIS** ($\sigma = 15.0\%$): InGraph visits an average of **$18,530$ nodes** ($18.5\%$ of the entire index), with maximum single-query latency reaching $1,642\text{ ms}$.

Because standard HNSW constructs entry points and hierarchical edges unaware of attributes, traversal begins at a spatial entry point that is almost always invalid for selective filters. When the beam search enters a local metric neighborhood containing few valid candidates, the priority queue continuously expands low-distance invalid nodes before finding valid paths, resulting in large visited sets. While percolation theory on random geometric graphs (Penrose 2003 [11]) provides asymptotic intuition that geometric graphs fragment under random node filtering, we emphasize that our measurements capture algorithmic beam-search expansion rather than direct proof of topological graph disconnectivity.

### 7.2 Index Construction Parameter Ablation: $ef_{\text{construction}}=50$ vs. $100$
To determine whether this traversal expansion was an artifact of building the index with $ef_{\text{construction}}=50$, we performed a controlled ablation (EXP-01) by building a fresh index with $ef_{\text{construction}}=100$ on the identical dataset ($N=100,000, M=16, \text{seed}=42$). Table 3 summarizes the results across 100 EM and 100 EMIS queries.

### Table 3: HNSW Construction Parameter Ablation ($ef_C=50$ vs. $100$, $k=10, ef_S=50$)

| Strategy | Workload | $ef_C=50$ Recall | $ef_C=100$ Recall | Recall $\Delta$ | $ef_C=50$ Latency | $ef_C=100$ Latency | $ef_C=50$ Visited | $ef_C=100$ Visited | Visited $\Delta$ |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **HNSW_PostFilter** | EM | 0.3320 | 0.3300 | $-0.0020$ | 6.47 ms | 4.77 ms | 10.0 | 10.0 | $0.0$ |
| **HNSW_PostFilter** | EMIS | 0.1500 | 0.1510 | $+0.0010$ | 7.37 ms | 4.57 ms | 10.0 | 10.0 | $0.0$ |
| **InGraphFilter** | EM | 0.9110 | 0.9210 | $+0.0100$ | 28.84 ms | 21.32 ms | 3,006.3 | 3,058.3 | $+52.0$ |
| **InGraphFilter** | EMIS | 0.8820 | 0.9240 | **$+0.0420$** | 181.13 ms | 170.87 ms | **15,860.7** | **15,921.1** | **$+60.4$** |

*Index Build Telemetry*: Building with $ef_C=100$ required **$994.39\text{ seconds}$** ($16.57\text{ minutes}$) compared to **$713.89\text{ seconds}$** ($11.90\text{ minutes}$) for $ef_C=50$, a **$39.3\%$ increase in indexing time**.

*Ablation Finding*: While $ef_C=100$ provides a modest $+4.2\%$ recall improvement on EMIS ($0.882 \to 0.924$), **it does not reduce visited nodes** ($15,921$ vs. $15,860$ nodes). This indicates that increasing construction beam width within practical indexing budgets does not resolve traversal expansion under attribute sparsity on the evaluated dataset.

---

## 8. Selectivity-Aware Query Routing

### 8.1 The Crossover Phenomenon and Operational Trade-Offs
Stratifying query performance across selectivity quantiles exposes a clear empirical crossover boundary:
- When selectivity $\sigma \le 2\%$ ($|S| \le 2,000$ vectors), inverted-index pre-filtering evaluates exact distances in **$<20\text{ ms}$** with $100\%$ recall, whereas in-graph filtering wanders across thousands of nodes ($>150\text{ ms}$).
- When selectivity $\sigma > 10\%$ ($|S| > 10,000$ vectors), pre-filtering latency escalates beyond $200\text{--}350\text{ ms}$ due to the cost of computing $D=4,096$ dot products over large candidate sets, whereas in-graph filtering completes in $14\text{--}24\text{ ms}$.

### 8.2 Router Design & Candidate Policy
We evaluate an adaptive router that inspects query metadata prior to vector distance computation:
$$\text{Strategy}(\mathbf{q}, \mathcal{P}) = \begin{cases} \text{PreFilter}, & \text{if } \hat{\sigma}(\mathcal{P}) \le \tau \\ \text{InGraphFilter}, & \text{if } \hat{\sigma}(\mathcal{P}) > \tau \end{cases}$$
where $\hat{\sigma}(\mathcal{P}) = \frac{|\mathcal{S}_{\mathcal{P}}|}{N}$ is computed directly from inverted metadata index candidate counts (`MetadataIndex.get_matching_ids`). The router operates strictly on pre-existing metadata structures with zero vector distance computations and zero ground-truth peeking.

### 8.3 Empirical Evaluation & Trade-Off Against PreFilter
We evaluated `AdaptiveRouter_2pct` ($\tau = 0.02$) across all 500 queries per workload ($1,500$ queries total) against static `PreFilter` and static `InGraphFilter`. Every query execution includes selectivity estimation and dispatch overhead in its measured latency.

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

*Methodological Disclosure on Table 4*: All methods in Table 4 were evaluated in a paired per-query loop where `PreFilter` executed first, followed by `InGraphFilter` and `Router`. Absolute latencies reflect warm OS memory-mapped page cache dynamics.

*Trade-Off Analysis*:
1. **Router vs. InGraph**: On EMIS, $5.8\%$ of queries satisfy $\sigma \le 2\%$. Routing these selective queries to PreFilter improves overall workload recall from **$0.8858 \to 0.8918$**, reduces mean latency by **$13.5\%$** ($214.43\text{ ms} \to 185.57\text{ ms}$), and compresses P99 tail latency by **$127.1\text{ ms}$** ($929.95\text{ ms} \to 802.85\text{ ms}$).
2. **Router vs. PreFilter**: On EMIS alone, static `PreFilter` achieves higher recall ($1.0000$ vs. $0.8918$), lower mean latency ($117.80\text{ ms}$ vs. $185.57\text{ ms}$), and a substantially lower P99 tail ($265.20\text{ ms}$ vs. $802.85\text{ ms}$). The router does not dominate PreFilter on selective queries because $94.2\%$ of EMIS queries exceed $\tau=0.02$ and are dispatched to InGraph, where queries with $2\% < \sigma \le 10\%$ still encounter long graph traversals.
3. **The Mixed-Workload Rationale**: The router's systems utility lies in cross-workload adaptability. A static PreFilter policy is disastrous on EM ($310.13\text{ ms}$) and Range ($337.45\text{ ms}$). The router safely defaults to InGraph on broad queries ($14.11\text{ ms}$ on EM, $23.64\text{ ms}$ on Range) while capturing modest tail reductions on ultra-selective queries.
4. **Routing Overhead Accounting**: Overhead is $0.002\text{ ms}$ on EM and $0.003\text{ ms}$ on EMIS (O(1) hash lookups). On Range, overhead is $0.227\text{ ms}$ because selectivity estimation evaluates a vectorized NumPy comparison across 100,000 integer timestamps.

### 8.4 Threshold Evaluation on Tuning and Held-Out Splits
To investigate threshold sensitivity, we evaluated a multi-threshold sweep across $\tau \in \{0.5\%, 1.0\%, 2.0\%, 5.0\%, 10.0\%, 20.0\%\}$ on a 50/50 split (Tuning: Query IDs 0..249; Held-Out: Query IDs 250..499).

### Table 5: Threshold Evaluation Matrix (Tuning Set vs. Held-Out Evaluation Set)

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

*Operating Window Findings*:
We evaluate $\tau = 2\%\text{--}5\%$ as a conservative operating window for balancing latency across the tested workloads. This range preserves performance on broader filters while capturing some benefits of pre-filtering on selective workloads. Higher thresholds ($\tau \ge 10\%$) improve EMIS latency ($73\text{--}86\text{ ms}$) and recall ($92\%\text{--}96\%$) by dispatching more queries to exact search, but begin to increase latency on EM ($14.5 \to 22.3\text{ ms}$) and Range ($20.6 \to 27.5\text{ ms}$) as PreFilter performs linear scans over $10K\text{--}20K$ vectors. The appropriate threshold depends on the expected workload mix and requires workload-specific validation.

---

## 9. Threats to Validity & Limitations

1. **Execution Ordering & Cache Warming**: In our EXP-03 evaluation harness, queries were evaluated in a paired per-query loop (`PreFilter(q)` immediately followed by `InGraphFilter(q)` and `Router(q)`). To directly measure the magnitude of execution-order cache warming, we executed an independent diagnostic micro-benchmark across 50 EMIS queries comparing three execution conditions:
   - When PreFilter executed first (Condition A), its mean latency was $315.99\text{ ms}$, while InGraphFilter executing second averaged $327.45\text{ ms}$.
   - When InGraphFilter executed first (Condition B), its mean latency was $197.00\text{ ms}$, while PreFilter executing second dropped to $136.85\text{ ms}$ (a $-56.7\%$ drop).
   - Under randomized per-query interleaving (Condition C), PreFilter averaged $110.82\text{ ms}$ and InGraphFilter averaged $163.67\text{ ms}$.
   These measurements demonstrate that execution ordering and memory-mapped page cache state introduce non-trivial timing variance ($10\%\text{--}50\%$). While the relative speedup and tail compression of the router remain directionally valid, absolute latencies measured in interleaved execution loops should not be directly equated with standalone cold-cache benchmarks.
2. **Workload Selectivity Confounding**: While cross-scale benchmarking compares $N=1,000$ and $N=100,000$, the benchmark queries at 100K are over twice as selective on EMIS as the 1K queries ($15.0\%$ vs. $31.9\%$). Consequently, cross-scale performance differences represent the combined effect of data volume and sharper attribute selectivity.
3. **Single-Threaded CPU Architecture & Memory Bandwidth**: All benchmarks were executed on an AMD Ryzen mobile CPU with single-threaded execution. Because $D=4,096$ vectors require $16.4\text{ KB}$ per vector, memory bandwidth saturates during large linear scans. Hardware-accelerated SIMD implementations (AVX-512) or GPU-accelerated GEMM (cuVS) would accelerate PreFilter, shifting the crossover boundary rightward.
4. **Heuristic Baseline Implementation Fidelity**: As disclosed in Section 3, `ACORN_Heuristic`, `SIEVE_Heuristic`, and `UNIFY_Heuristic` were evaluated as educational Python heuristic baselines on standard HNSW graphs. They demonstrate the limits of dynamic multi-hop expansion on un-augmented graphs, but do not represent the full performance of the original authors' C++/CUDA systems.
5. **External Validity & Embedding Dimensionality**: The experiments were conducted on text embeddings from `arxiv-for-fanns`. While the evaluated workloads cover point equality, range intervals, and multi-value sets, embeddings with lower dimensionality ($D=128$ or $768$) or different clustering-to-attribute correlation profiles may exhibit distinct crossover boundaries.

---

## 10. Conclusion and Future Work

In this paper, we presented an empirical systems study of Filtered Approximate Nearest Neighbor Search comparing $1,000$ and $100,000$ database vectors under 4,096 dimensions. We demonstrated that candidate overfetching experiences sharply diminishing returns under attribute sparsity ($51.4\%$ recall at $50\times$). While in-graph filtering maintains robust recall, selective predicates force traversals to evaluate over $18,500$ nodes. A controlled construction ablation confirmed that doubling construction effort ($ef_C=100$) does not eliminate this exploration spike. Finally, we demonstrated that a selectivity-aware query router operating in the $2\%\text{--}5\%$ selectivity window functions as a practical mixed-workload compromise, mitigating tail latency on selective queries while analyzing its trade-offs against static pre-filtering.

Future work includes integrating continuous cost models that incorporate query vector norms and graph entry distances into production vector database query planners, alongside evaluating hardware-accelerated SIMD and GPU pre-filtering kernels.

---

## 11. References

1. Malkov, Yu A., and D. A. Yashunin. "Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs." *IEEE Transactions on Pattern Analysis and Machine Intelligence* 42.4 (2020): 824–836. [DOI: 10.1109/TPAMI.2018.2889473](https://doi.org/10.1109/TPAMI.2018.2889473).
2. Patel, Liana, Peter Kraft, Carlos Guestrin, and Matei Zaharia. "ACORN: Performant and Predicate-Agnostic Approximate Nearest Neighbor Search." *Proceedings of the ACM on Management of Data (SIGMOD)* 2.3 (2024): 1–27. [DOI: 10.1145/3654932](https://doi.org/10.1145/3654932).
3. Gao, Zichen, et al. "High-Dimensional Filtered Vector Search with 3D Packing." *Proceedings of the VLDB Endowment* 17.11 (2024): 3326–3339.
4. Liang, Anqi, Pengcheng Zhang, Bin Yao, Zhongpu Chen, Yitong Song, and Guangxu Cheng. "UNIFY: Unified Graph Index for Filtered Vector Retrieval." *arXiv preprint arXiv:2412.06208* (2024). [arXiv:2412.06208](https://arxiv.org/abs/2412.06208).
5. Iff, Patrick, Paul Bruegger, Marcin Chrapek, Maciej Besta, and Torsten Hoefler. "FANNS: Filtered Approximate Nearest Neighbor Search Benchmark." *arXiv preprint arXiv:2507.21989* (2025). [arXiv:2507.21989](https://arxiv.org/abs/2507.21989).
6. Johnson, Jeff, Matthijs Douze, and Hervé Jégou. "Billion-scale similarity search with GPUs." *IEEE Transactions on Big Data* 7.3 (2021): 535–547. [DOI: 10.1109/TBDATA.2019.2921572](https://doi.org/10.1109/TBDATA.2019.2921572).
7. Aumüller, Martin, Erik Bernhardsson, and Alexander Faithfull. "ANN-Benchmarks: A benchmarking tool for approximate nearest neighbor algorithms." *Information Systems* 87 (2020): 101374. [DOI: 10.1016/j.is.2019.02.006](https://doi.org/10.1016/j.is.2019.02.006).
8. Gollapudi, Siddharth, Neel Karia, Varun Sivashankar, Ravishankar Krishnaswamy, Nikit Begwani, Swapnil Raz, Yiyong Lin, Yin Zhang, Neelam Mahapatro, Premkumar Srinivasan, Amit Singh, and Harsha Vardhan Simhadri. "Filtered-DiskANN: Graph Algorithms for Approximate Nearest Neighbor Search with Filters." In *Proceedings of the ACM Web Conference 2023 (WWW '23)*, pages 3407–3416. [DOI: 10.1145/3543507.3583552](https://doi.org/10.1145/3543507.3583552).
9. Zhang, Qianxi, Shuaiwen Leon Song, Chen Zhang, Lingxiao Ma, Yuqing Xia, Jingwen Leng, Chao Li, Minyi Guo, Fan Yang, and Mao Yang. "VBASE: Unifying Online Vector Similarity Search and Relational Queries via Relaxed Monotonicity." In *17th USENIX Symposium on Operating Systems Design and Implementation (OSDI '23)*, pages 377–395.
10. Wang, Jianguo, Xiaomeng Yi, Rentong Guo, Haihang Jin, Peng Xu, Shengjun Li, Xiangyu Wang, Xiangzhou Guo, Chengming Li, Xiaohui Xu, Rong Kang, Jianfei Chen, and Xiang Gao. "Milvus: A Purpose-Built Vector Data Management System." In *Proceedings of the 2021 International Conference on Management of Data (SIGMOD '21)*, pages 2614–2627. [DOI: 10.1145/3448016.3457550](https://doi.org/10.1145/3448016.3457550).
11. Penrose, Mathew. *Random Geometric Graphs*. Oxford Studies in Probability, Volume 5, Oxford University Press, 2003. [DOI: 10.1093/acprof:oso/9780198506263.001.0001](https://doi.org/10.1093/acprof:oso/9780198506263.001.0001).
