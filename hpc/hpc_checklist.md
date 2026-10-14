# HPC & Supercomputer Deployment Readiness Checklist for FANNS (Medium to Large Scale)

## 1. Workload & Memory Scaling Estimation

| Dataset Scale | Vectors | Dimensions | Precision | Raw Vector RAM | HNSW Graph RAM (M=16) | Total Expected RAM | Feasibility (Local PC) | Supercomputer Requirement |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Small** | 1,000 | 4,096 | Float32 | ~16.4 MB | ~1 MB | **~25 MB** | Feasible (L3 cache resident) | Single Core / Debug |
| **Medium (Current)** | 100,000 | 4,096 | Float32 | ~1.64 GB | ~50 MB | **~2.2 GB** | Feasible via mmap & BLAS batching | 1 Node (4-8 Cores, 16GB RAM) |
| **Large (1M)** | 1,000,000 | 4,096 | Float32 | ~16.4 GB | ~500 MB | **~25-32 GB** | Exceeds Laptop RAM (OOM) | **HPC Compute Node (64GB+ RAM)** |
| **Full ArXiv (2.7M+)**| 2,700,000 | 4,096 | Float32 | ~44.3 GB | ~1.5 GB | **~64-80 GB** | Severe Disk Swapping / Crash | **High-Mem Node (128GB+ RAM, 32 Cores)** |

---

## 2. Supercomputer Cluster Checklist

### Hardware Specifications
- [ ] **Node Architecture**: x86_64 (e.g., AMD EPYC 7763 / 9654 or Intel Xeon Platinum 8480+)
- [ ] **RAM Allocation**: Minimum 64 GB per job for 1M vectors; 128 GB for 2.7M full dataset
- [ ] **CPU Cores**: 16 to 32 dedicated physical cores per job
- [ ] **Local Scratch Storage**: High-speed NVMe `/tmp` or Lustre/GPFS parallel file system (>100 GB free)

### Software & Environment
- [ ] **Operating System**: Linux (CentOS/RHEL 8/9, Rocky Linux, or Ubuntu 22.04 LTS)
- [ ] **Scheduler**: Slurm Workload Manager (`sbatch`, `srun`)
- [ ] **Python Version**: Python 3.10+ (with OpenBLAS/MKL and NumPy SIMD support)
- [ ] **Environment Isolation**: Python virtual environment or Conda module (`module load python/3.11`)

---

## 3. Recommended Slurm Job Parameters

```bash
#SBATCH --job-name=fanns_benchmark_medium
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --partition=standard
#SBATCH --output=reports/slurm_logs/fanns_%j.out
#SBATCH --error=reports/slurm_logs/fanns_%j.err
```
