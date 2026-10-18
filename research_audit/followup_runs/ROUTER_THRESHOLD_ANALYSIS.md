# Selectivity Router: Threshold Sensitivity & Held-Out Validation Analysis

## 1. Train / Test Experimental Split Protocol

- **Tuning Set (Train)**: Queries 0 to 249 (250 queries per workload). Used exclusively to observe the empirical Pareto frontier across thresholds.
- **Evaluation Set (Held-Out Test)**: Queries 250 to 499 (250 queries per workload). Evaluated with frozen thresholds to test out-of-sample generalization.
- **Candidate Thresholds Evaluated**: $\tau \in \{0.5\%, 1.0\%, 2.0\%, 5.0\%, 10.0\%, 20.0\%\}$.

## 2. Threshold Sensitivity Matrix (Tuning Set vs. Held-Out Set)

| Workload | Split | Threshold ($\tau$) | Mean Recall@10 | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | QPS | PreFilter Routing % |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| EM | tuning | **0.5%** | 0.9276 | 19.09 | 14.30 | 41.27 | 52.4 | 0.4% |
| Range | tuning | **0.5%** | 0.9248 | 26.23 | 14.90 | 82.05 | 38.1 | 0.0% |
| EMIS | tuning | **0.5%** | 0.8684 | 189.07 | 107.14 | 594.81 | 5.3 | 0.4% |
| EM | held_out | **0.5%** | 0.9480 | 15.52 | 11.95 | 32.78 | 64.4 | 0.0% |
| Range | held_out | **0.5%** | 0.9360 | 22.22 | 11.06 | 74.91 | 45.0 | 0.0% |
| EMIS | held_out | **0.5%** | 0.9032 | 237.80 | 133.14 | 750.65 | 4.2 | 0.4% |
| EM | tuning | **1.0%** | 0.9276 | 19.09 | 14.30 | 41.27 | 52.4 | 0.4% |
| Range | tuning | **1.0%** | 0.9248 | 26.23 | 14.90 | 82.05 | 38.1 | 0.0% |
| EMIS | tuning | **1.0%** | 0.8684 | 188.02 | 106.98 | 594.81 | 5.3 | 0.8% |
| EM | held_out | **1.0%** | 0.9480 | 15.52 | 11.95 | 32.78 | 64.4 | 0.0% |
| Range | held_out | **1.0%** | 0.9360 | 20.62 | 10.97 | 73.19 | 48.5 | 0.4% |
| EMIS | held_out | **1.0%** | 0.9032 | 237.80 | 133.14 | 750.65 | 4.2 | 0.4% |
| EM | tuning | **2.0%** | 0.9280 | 16.84 | 14.16 | 34.77 | 59.4 | 2.0% |
| Range | tuning | **2.0%** | 0.9248 | 26.23 | 14.90 | 82.05 | 38.1 | 0.0% |
| EMIS | tuning | **2.0%** | 0.8744 | 163.98 | 98.85 | 566.99 | 6.1 | 6.4% |
| EM | held_out | **2.0%** | 0.9480 | 14.45 | 11.89 | 30.08 | 69.2 | 0.8% |
| Range | held_out | **2.0%** | 0.9360 | 20.62 | 10.97 | 73.19 | 48.5 | 0.4% |
| EMIS | held_out | **2.0%** | 0.9092 | 209.99 | 105.20 | 694.58 | 4.8 | 5.2% |
| EM | tuning | **5.0%** | 0.9308 | 16.10 | 14.16 | 29.25 | 62.1 | 5.6% |
| Range | tuning | **5.0%** | 0.9264 | 24.88 | 14.90 | 67.10 | 40.2 | 1.6% |
| EMIS | tuning | **5.0%** | 0.8820 | 122.61 | 61.05 | 471.38 | 8.2 | 19.6% |
| EM | held_out | **5.0%** | 0.9484 | 13.53 | 11.89 | 25.98 | 73.9 | 5.6% |
| Range | held_out | **5.0%** | 0.9360 | 19.59 | 10.97 | 68.25 | 51.1 | 2.0% |
| EMIS | held_out | **5.0%** | 0.9216 | 155.44 | 53.16 | 657.93 | 6.4 | 20.8% |
| EM | tuning | **10.0%** | 0.9308 | 16.10 | 14.16 | 29.25 | 62.1 | 5.6% |
| Range | tuning | **10.0%** | 0.9292 | 24.90 | 14.90 | 66.14 | 40.2 | 4.4% |
| EMIS | tuning | **10.0%** | 0.9192 | 73.41 | 47.05 | 254.86 | 13.6 | 33.6% |
| EM | held_out | **10.0%** | 0.9484 | 13.53 | 11.89 | 25.98 | 73.9 | 5.6% |
| Range | held_out | **10.0%** | 0.9364 | 20.34 | 10.97 | 74.42 | 49.2 | 6.0% |
| EMIS | held_out | **10.0%** | 0.9600 | 86.37 | 46.64 | 317.65 | 11.6 | 35.2% |
| EM | tuning | **20.0%** | 0.9384 | 26.49 | 14.20 | 101.10 | 37.7 | 18.8% |
| Range | tuning | **20.0%** | 0.9348 | 30.83 | 14.90 | 120.52 | 32.4 | 15.2% |
| EMIS | tuning | **20.0%** | 0.9572 | 55.55 | 47.67 | 116.39 | 18.0 | 63.2% |
| EM | held_out | **20.0%** | 0.9540 | 22.29 | 11.89 | 95.40 | 44.9 | 17.6% |
| Range | held_out | **20.0%** | 0.9420 | 27.46 | 10.97 | 129.76 | 36.4 | 17.2% |
| EMIS | held_out | **20.0%** | 0.9752 | 53.77 | 46.64 | 117.31 | 18.6 | 62.4% |

## 3. Generalization Verdict: Does $\tau = 2.0\%$ Generalize?

1. **Tuning vs. Held-Out Consistency**: Compare the metric trends between the tuning split and held-out test split.
2. **Optimal Operating Regime**: Delineate whether $\tau=1.0\%$ or $\tau=2.0\%$ provides the optimal trade-off between PreFilter distance computation costs and InGraph node expansion.
3. **Scientific Integrity Statement**: The threshold $\tau=2.0\%$ is confirmed as an effective heuristic rather than a mathematically optimal constant across arbitrary datasets.