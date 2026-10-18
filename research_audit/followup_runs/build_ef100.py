"""
Build fresh HNSW Index with efConstruction=100 for EXP-01 Ablation Study.
Controls:
- M=16, efConstruction=100, random_seed=42, metric='l2'
- Database: 100,000 vectors x 4,096 dimensions
- Output: research_audit/followup_runs/hnsw_index_m16_ef100.pkl
- Stats: research_audit/followup_runs/hnsw_ef100_build_stats.json
- Checkpoint: research_audit/followup_runs/hnsw_ef100_checkpoint.pkl (saved every 10,000 vectors)
"""

import json
from pathlib import Path
import sys
import time
import numpy as np
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.dataset_loader import load_fanns_dataset
from src.hnsw_index import HNSWIndex


def main():
    print("=" * 80)
    print("BUILDING FRESH HNSW INDEX: 100,000 VECTORS (M=16, efConstruction=100, seed=42)")
    print("=" * 80)

    out_dir = Path("research_audit/followup_runs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hnsw_index_m16_ef100.pkl"
    stats_path = out_dir / "hnsw_ef100_build_stats.json"
    ckpt_path = out_dir / "hnsw_ef100_checkpoint.pkl"

    dataset = load_fanns_dataset("data/arxiv-for-fanns-medium", mmap=True)
    num_vectors = dataset.num_database
    dim = dataset.dimension

    process = psutil.Process()
    ram_before = process.memory_info().rss / (1024 * 1024)
    print(f"Dataset: {num_vectors:,} vectors x {dim} dimensions")
    print(f"Process RAM before build: {ram_before:.2f} MB")

    hnsw = HNSWIndex(
        dimension=dim,
        metric="l2",
        M=16,
        ef_construction=100,
        random_seed=42,
    )

    # Check for existing checkpoint
    start_idx = 0
    t_prior = 0.0
    if ckpt_path.exists():
        print(f"\n[Checkpoint Found] Resuming from checkpoint {ckpt_path}...")
        hnsw.load_index(ckpt_path, vectors=dataset.database_vectors)
        start_idx = len(hnsw.node_layers)
        print(f"[OK] Resuming from vector {start_idx:,} / {num_vectors:,}")
    else:
        hnsw.set_vectors(dataset.database_vectors)
        hnsw.layers = []
        hnsw.node_layers = []

    t0 = time.perf_counter()
    checkpoint_interval = 10000

    print(f"\n[Inserting Vectors] Starting insertion from index {start_idx} to {num_vectors}...")
    for i in range(start_idx, num_vectors):
        hnsw._insert_point(i)

        if (i + 1) % checkpoint_interval == 0 or (i + 1) == num_vectors:
            elapsed = time.perf_counter() - t0
            rate = (i + 1 - start_idx) / elapsed if elapsed > 0 else 0
            rem = (num_vectors - (i + 1)) / rate if rate > 0 else 0
            print(f"[Progress] {i + 1:,} / {num_vectors:,} ({(i + 1)/num_vectors*100:.1f}%) | "
                  f"Rate: {rate:.1f} it/s | Elapsed: {elapsed:.1f}s | ETA: {rem/60:.1f} min")
            if (i + 1) < num_vectors:
                hnsw.save_index(ckpt_path)

    total_build_time = time.perf_counter() - t0

    ram_after = process.memory_info().rss / (1024 * 1024)
    mem_est = hnsw.estimate_memory_mb()

    print("\n" + "-" * 80)
    print(f"[OK] HNSW efConstruction=100 Built in {total_build_time:.2f} seconds ({total_build_time/60:.2f} minutes)")
    print(f"[OK] Estimated Index RAM: {mem_est:.2f} MB | Peak Process RSS: {ram_after:.2f} MB")
    print(f"[OK] Layers count: {len(hnsw.layers)} | Max layer: {hnsw.max_layer} | Entry point: {hnsw.enter_point}")
    print("-" * 80)

    hnsw.save_index(out_path)
    file_size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"[OK] Saved final index to {out_path} ({file_size_mb:.2f} MB)")

    # Clean up checkpoint file
    if ckpt_path.exists():
        ckpt_path.unlink()

    stats = {
        "num_vectors": num_vectors,
        "dimension": dim,
        "metric": "l2",
        "M": 16,
        "ef_construction": 100,
        "random_seed": 42,
        "build_time_seconds": round(total_build_time, 2),
        "build_time_minutes": round(total_build_time / 60, 2),
        "index_memory_mb": round(mem_est, 2),
        "peak_rss_mb": round(ram_after, 2),
        "num_layers": len(hnsw.layers),
        "max_layer": hnsw.max_layer,
        "enter_point": hnsw.enter_point,
        "file_size_mb": round(file_size_mb, 2),
    }

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(f"[OK] Saved build stats to {stats_path}")


if __name__ == "__main__":
    main()
