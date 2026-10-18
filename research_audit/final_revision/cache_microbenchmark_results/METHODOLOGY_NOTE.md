# Cache Warming & Execution Order Micro-Benchmark Methodology Note

## 1. Experimental Setup
- **Workload**: EMIS (Exact Match In Set, 50 diagnostic queries evaluated: Query IDs 0..49)
- **Vector Dataset**: 100,000 vectors, $D=4,096$ ($1.64\text{ GB}$ float32 read-only memory-mapped array)
- **Index Configuration**: HNSW ($M=16, ef_{\text{construction}}=50, ef_{\text{search}}=50$, random seed $= 42$)
- **Randomization Seed**: 42 (fixed recorded seed for Condition C)
- **Sample Size**: $N=50$ queries per condition (300 total query executions across all conditions)
- *Statistical Disclaimer*: P95 and P99 percentiles on $N=50$ samples carry high variance and are reported for completeness rather than asymptotic tail guarantees.

---

## 2. Measured Results

| Condition | Method | Sample Count | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | Min Latency (ms) | Max Latency (ms) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Condition A: PreFilter First** (EXP-03 Order) | PreFilter (Pos 1) | 50 | 315.991 | 201.736 | 822.451 | 1719.807 | 15.520 | 1935.942 |
| **Condition A: PreFilter First** (EXP-03 Order) | InGraphFilter (Pos 2) | 50 | 327.446 | 170.488 | 1132.708 | 1520.122 | 8.149 | 1686.499 |
| **Condition B: InGraph First** (Inverted Order) | InGraphFilter (Pos 1) | 50 | 197.004 | 122.507 | 719.405 | 776.133 | 4.573 | 823.828 |
| **Condition B: InGraph First** (Inverted Order) | PreFilter (Pos 2) | 50 | 136.851 | 104.733 | 323.395 | 344.864 | 12.369 | 360.799 |
| **Condition C: Randomized Order** (Per-Query Shuffle) | PreFilter | 50 | 110.821 | 96.588 | 236.073 | 250.537 | 5.791 | 250.988 |
| **Condition C: Randomized Order** (Per-Query Shuffle) | InGraphFilter | 50 | 163.669 | 91.047 | 626.858 | 658.676 | 5.766 | 660.204 |

---

## 3. Analysis & Key Findings

1. **Order Sensitivity in Interleaved Execution**:
   - In Condition A, PreFilter ran first on cold/initial pages, yielding a high initial mean latency of **$315.99\text{ ms}$**. When PreFilter ran second in Condition B (after InGraph had accessed graph vectors), its mean latency dropped to **$136.85\text{ ms}$** (a **$-179.14\text{ ms}$ or $-56.7\%$ reduction**).
   - In Condition B, InGraphFilter running first achieved **$197.00\text{ ms}$**, whereas in Condition A (running immediately after PreFilter touched matching vectors) its mean was **$327.45\text{ ms}$**, driven by severe long-tail outliers (Max: $1,686\text{ ms}$).
2. **Randomized Order Baseline**:
   - Under randomized per-query interleaving (Condition C), PreFilter averaged **$110.82\text{ ms}$** (median $96.59\text{ ms}$), which closely matches the full 500-query EXP-03 PreFilter benchmark average ($117.80\text{ ms}$).
   - InGraphFilter under randomized order averaged **$163.67\text{ ms}$** (median $91.05\text{ ms}$).
3. **Implications for Manuscript Validity**:
   - The micro-benchmark confirms that **execution order and memory-mapped page cache state introduce measurable timing variance** ($10\%\text{--}50\%$) on 4,096-dimensional vectors.
   - Consequently, the manuscript must **not** claim that EXP-03 latencies represent isolated, cold-cache operating characteristics. All interleaved benchmark results must be explicitly qualified as reflecting warm OS page cache dynamics.
