# FANNS Medium Dataset Validation Report

**Dataset**: `SPCL/arxiv-for-fanns-medium`  
**Validation Timestamp**: 2026-10-14 16:54:15  
**Overall Status**: **PASSED**  
**Verification Duration**: 11.46 seconds  

---

## 1. Dataset Dimensions & Characteristics

- **Database Vectors**: 100,000 vectors
- **Query Vectors**: 10,000 vectors
- **Vector Dimension**: 4096 dimensions
- **Vector Data Type**: `float32` (IEEE 754 single-precision)
- **Vector Value Range**: `[-0.1058, 0.0988]`
- **NaN / Inf Anomalies**: 0 detected
- **Database Metadata Rows**: 100,000 JSONL records

## 2. File Inventory & Disk Footprint

| File Name | Format / Encoding | Size on Disk | Status |
| :--- | :--- | :--- | :--- |
| `database_vectors.fvecs` | Binary / JSONL | 1562.88 MB | PASSED |
| `database_attributes.jsonl` | Binary / JSONL | 39.05 MB | PASSED |
| `query_vectors.fvecs` | Binary / JSONL | 156.29 MB | PASSED |
| `ground_truth.ivecs` | Binary / JSONL | 3.85 MB | PASSED |
| `em_query_attributes.jsonl` | Binary / JSONL | 0.12 MB | PASSED |
| `ground_truth_em.ivecs` | Binary / JSONL | 3.85 MB | PASSED |
| `r_query_attributes.jsonl` | Binary / JSONL | 0.41 MB | PASSED |
| `ground_truth_r.ivecs` | Binary / JSONL | 3.85 MB | PASSED |
| `emis_query_attributes.jsonl` | Binary / JSONL | 0.18 MB | PASSED |
| `ground_truth_emis.ivecs` | Binary / JSONL | 3.85 MB | PASSED |

## 3. Workloads & Empirical Filter Selectivity

| Workload | Filter Semantics | Mean Selectivity | Median Selectivity | Selectivity Range | Mean Matching Candidates |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EM** | Exact Match (`number_of_sub_categories`) | 38.47% | 52.82% | [0.00%, 52.82%] | 38,469.6 |
| **Range** | Range Interval (`update_date`) | 44.55% | 43.79% | [0.25%, 95.09%] | 44,552.4 |
| **EMIS** | Set Membership (`main_categories`) | 15.24% | 13.23% | [0.02%, 27.64%] | 15,242.9 |

## 4. Ground Truth Integrity

| Workload | GT Format | Queries | Length / $k$ | ID Range | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `unfiltered` | `fixed_width_ivecs` | 10,000 | Fixed $k=100$ | `[3, 99991]` | VALID |
| `EM` | `variable_width_ivecs` | 10,000 | Variable (mean 100.0) | `[3, 99991]` | VALID |
| `Range` | `variable_width_ivecs` | 10,000 | Variable (mean 100.0) | `[2, 99989]` | VALID |
| `EMIS` | `variable_width_ivecs` | 10,000 | Variable (mean 99.9) | `[2, 99997]` | VALID |

---
## 5. Verification Conclusion

All 10 required dataset files are intact, non-corrupted, and mathematically valid. Database and query vector dimensions agree exactly at 4,096. Vector values are free of NaN and infinity. Ground truth candidate IDs fall strictly within valid database bounds `[0, 99999]`. The dataset is approved for full benchmark execution.
