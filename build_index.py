"""
Build and serialize HNSW index for the medium dataset (100,000 vectors).
Saves graph topology to results/hnsw_index_m16_ef100.pkl and metadata to results/medium/index_build_stats.json.
"""

import json
from pathlib import Path
import sys
import time
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.dataset_loader import load_fanns_dataset
from src.hnsw_index import HNSWIndex


def build_and_save_index(
    data_dir: str = "data/arxiv-for-fanns-medium",
    output_path: str = "results/hnsw_index_m16_ef100.pkl",
    M: int = 16,
    ef_construction: int = 50,
    random_seed: int = 42,
):
    print("=" * 80)
    print(f"BUILDING HNSW GRAPH INDEX: 100,000 VECTORS (M={M}, efConstruction={ef_construction})")
    print("=" * 80)

    dataset = load_fanns_dataset(data_dir, mmap=True)
    num_vectors = dataset.num_database
    dim = dataset.dimension

    print(f"Dataset: {num_vectors:,} vectors x {dim} dimensions")
    process = psutil.Process()
    ram_before_mb = process.memory_info().rss / (1024 * 1024)
    print(f"Process RAM before build: {ram_before_mb:.2f} MB")

    hnsw = HNSWIndex(
        dimension=dim,
        metric="l2",
        M=M,
        ef_construction=ef_construction,
        random_seed=random_seed,
    )

    t0 = time.perf_counter()
    hnsw.build_index(dataset.database_vectors, progress_bar=True)
    build_time_s = time.perf_counter() - t0

    ram_after_mb = process.memory_info().rss / (1024 * 1024)
    index_mem_mb = hnsw.estimate_memory_mb()

    print("\n" + "-" * 80)
    print(f"[OK] HNSW Index Built in {build_time_s:.2f} seconds ({build_time_s/60:.2f} minutes)")
    print(f"[OK] Index Structure RAM: {index_mem_mb:.2f} MB")
    print(f"[OK] Peak Process RSS: {ram_after_mb:.2f} MB")
    print(f"[OK] Layers count: {len(hnsw.layers)} | Max layer: {hnsw.max_layer} | Entry point: {hnsw.enter_point}")
    print("-" * 80)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    hnsw.save_index(out_file)
    file_size_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"[OK] Saved index to disk: {out_file} ({file_size_mb:.2f} MB)")

    stats = {
        "num_vectors": num_vectors,
        "dimension": dim,
        "metric": "l2",
        "M": M,
        "ef_construction": ef_construction,
        "random_seed": random_seed,
        "build_time_seconds": round(build_time_s, 2),
        "build_time_minutes": round(build_time_s / 60, 2),
        "index_memory_mb": round(index_mem_mb, 2),
        "peak_rss_mb": round(ram_after_mb, 2),
        "num_layers": len(hnsw.layers),
        "max_layer": hnsw.max_layer,
        "enter_point": hnsw.enter_point,
        "file_size_mb": round(file_size_mb, 2),
    }

    stats_path = Path("results/medium/index_build_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"[OK] Saved build stats: {stats_path}")

    return hnsw, stats


if __name__ == "__main__":
    build_and_save_index()
