"""
Dataset downloader for SPCL/arxiv-for-fanns-medium dataset from Hugging Face Hub.
Downloads official medium-scale vectors, metadata, query attributes, and ground truth files.
"""

from pathlib import Path
from huggingface_hub import hf_hub_download

DATASET_ID = "SPCL/arxiv-for-fanns-medium"
OUTPUT_DIR = Path("data/arxiv-for-fanns-medium")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "database_vectors.fvecs",
    "database_attributes.jsonl",
    "query_vectors.fvecs",
    "ground_truth.ivecs",
    "em_query_attributes.jsonl",
    "ground_truth_em.ivecs",
    "r_query_attributes.jsonl",
    "ground_truth_r.ivecs",
    "emis_query_attributes.jsonl",
    "ground_truth_emis.ivecs",
]


def download_medium_dataset():
    print("=" * 70)
    print("SPCL/ARXIV-FOR-FANNS-MEDIUM DATASET DOWNLOADER")
    print("=" * 70)
    print(f"Dataset Hub ID: {DATASET_ID}")
    print(f"Target Output:  {OUTPUT_DIR.resolve()}")
    print("-" * 70)

    for idx, filename in enumerate(FILES, start=1):
        target_path = OUTPUT_DIR / filename
        if target_path.exists() and target_path.stat().st_size > 0:
            size_mb = target_path.stat().st_size / (1024 * 1024)
            print(f"[{idx}/{len(FILES)}] Already downloaded: {filename:<32} ({size_mb:>8.2f} MB)")
            continue

        print(f"[{idx}/{len(FILES)}] Downloading: {filename} ...")
        path = hf_hub_download(
            repo_id=DATASET_ID,
            filename=filename,
            repo_type="dataset",
            local_dir=str(OUTPUT_DIR),
        )
        size_mb = Path(path).stat().st_size / (1024 * 1024)
        print(f"       -> Saved: {path} ({size_mb:.2f} MB)")

    print("\n" + "=" * 70)
    print("ALL DATASET FILES VERIFIED ON DISK")
    print("=" * 70)
    for f in sorted(OUTPUT_DIR.iterdir()):
        if f.is_file():
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"{f.name:<35} {size_mb:>10.2f} MB")


if __name__ == "__main__":
    download_medium_dataset()
