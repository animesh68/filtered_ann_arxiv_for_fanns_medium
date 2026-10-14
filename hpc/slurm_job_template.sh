#!/bin/bash
# ==============================================================================
# Slurm Job Script: Scaled Filtered ANN Search (FANNS) Benchmark (Medium Dataset)
# ==============================================================================

#SBATCH --job-name=fanns_medium_benchmark
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --partition=standard
#SBATCH --output=reports/slurm_logs/fanns_%j.out
#SBATCH --error=reports/slurm_logs/fanns_%j.err

echo "======================================================================"
echo "Starting FANNS Benchmark Job ID: $SLURM_JOB_ID on $(hostname)"
echo "Start Time: $(date)"
echo "Allocated Cores: $SLURM_CPUS_PER_TASK, Allocated Memory: $SLURM_MEM_PER_NODE"
echo "======================================================================"

# 1. Environment Setup
mkdir -p reports/slurm_logs results/controlled_benchmark reports/figures
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export PYTHONUNBUFFERED=1

# 2. Activate Virtual Environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# 3. Dataset Verification
echo "Verifying medium dataset..."
python3 experiments/01_dataset_validation.py

# 4. Build HNSW Index (if not already cached)
if [ ! -f "results/hnsw_index_m16_ef100.pkl" ]; then
    echo "Building HNSW Graph on 100K vectors..."
    python3 build_index.py
fi

# 5. Execute Controlled Benchmark
echo "Executing controlled benchmark across 11 strategies and 3 workloads..."
python3 experiments/08_controlled_benchmark_all.py

# 6. Generate Visualizations & Tables
echo "Generating publication plots..."
python3 experiments/09_generate_plots_and_tables.py

echo "======================================================================"
echo "FANNS Medium Benchmark Completed: $(date)"
echo "======================================================================"
