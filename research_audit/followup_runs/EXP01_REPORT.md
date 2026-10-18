# EXP-01: HNSW Construction-Parameter Ablation Report

**Date**: 2026-10-16 06:42:15 UTC  
**System**: Windows-11-10.0.26200-SP0 | CPU: AMD64 Family 23 Model 104 Stepping 1, AuthenticAMD (4C/8T) | RAM: 7.33 GB  
**Dataset**: Official 100K-vector, 4096-dim `SPCL/arxiv-for-fanns-medium`  
**Queries Evaluated**: 100 EM queries (IDs 0..99) and 100 EMIS queries (IDs 0..99)  
**Fixed Parameters**: M=16, k=10, efSearch=50, random_seed=42  

## 1. Index Construction Telemetry

| Parameter | efConstruction = 50 | efConstruction = 100 | Absolute Delta | Relative Change |
|:---|:---:|:---:|:---:|:---:|
| **Build Time (s)** | 713.89s | 994.39s | +280.50s | +39.3% |
| **Build Time (min)** | 11.90 min | 16.57 min | +4.67 min | - |
| **Graph Topology Size** | 11.85 MB | 11.86 MB | +0.01 MB | +0.1% |
| **Layers Count** | 5 | 5 | 0 | 0.0% |
| **Max Layer** | 4 | 4 | 0 | 0.0% |
| **Enter Point ID** | 2902 | 2902 | - | Identical Seed Entry |

## 2. Master Evaluation Summary Table

| Condition | Method | Workload | Mean Recall@10 | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | P99 Latency (ms) | QPS | Mean Nodes Visited |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| efC=50 | HNSW_PostFilter | EM | 0.3320 | 6.47 | 5.87 | 11.12 | 21.57 | 154.5 | 10.0 |
| efC=50 | HNSW_PostFilter | EMIS | 0.1500 | 7.37 | 6.68 | 14.14 | 16.24 | 135.7 | 10.0 |
| efC=50 | InGraphFilter | EM | 0.9110 | 28.84 | 14.36 | 51.45 | 391.34 | 34.7 | 3006.3 |
| efC=50 | InGraphFilter | EMIS | 0.8820 | 181.13 | 106.54 | 643.84 | 831.52 | 5.5 | 15860.7 |
| efC=100 | HNSW_PostFilter | EM | 0.3300 | 4.77 | 4.59 | 6.26 | 6.65 | 209.6 | 10.0 |
| efC=100 | HNSW_PostFilter | EMIS | 0.1510 | 4.57 | 4.42 | 6.17 | 6.36 | 218.9 | 10.0 |
| efC=100 | InGraphFilter | EM | 0.9210 | 21.32 | 11.98 | 45.36 | 141.37 | 46.9 | 3058.3 |
| efC=100 | InGraphFilter | EMIS | 0.9240 | 170.87 | 113.40 | 545.62 | 814.40 | 5.9 | 15921.1 |

## 3. Paired Ablation Analysis (efC=50 vs. efC=100)

| Method | Workload | Recall (ef50) | Recall (ef100) | Recall Delta | Mean Latency (ef50) | Mean Latency (ef100) | Latency Ratio | Visited (ef50) | Visited (ef100) | Visited Delta |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **InGraphFilter** | EM | 0.9110 | 0.9210 | **+0.0100** | 28.84 ms | 21.32 ms | 0.74x | 3006.3 | 3058.3 | +52.0 |
| **InGraphFilter** | EMIS | 0.8820 | 0.9240 | **+0.0420** | 181.13 ms | 170.87 ms | 0.94x | 15860.7 | 15921.1 | +60.4 |
| **HNSW_PostFilter** | EM | 0.3320 | 0.3300 | **-0.0020** | 6.47 ms | 4.77 ms | 0.74x | 10.0 | 10.0 | +0.0 |
| **HNSW_PostFilter** | EMIS | 0.1500 | 0.1510 | **+0.0010** | 7.37 ms | 4.57 ms | 0.62x | 10.0 | 10.0 | +0.0 |

## 4. Key Scientific Conclusions

1. **Recall Impact**: Assess whether efConstruction=100 produced a statistically meaningful recall increase.
2. **Latency & Visited Nodes**: Assess whether graph connectivity improvements reduced nodes visited during InGraph traversal.
3. **Paper Implications**: State whether reporting efConstruction=50 in the medium benchmark compromised retrieval quality.

*(Full per-query raw data available in `EXP01_RAW.csv`)*