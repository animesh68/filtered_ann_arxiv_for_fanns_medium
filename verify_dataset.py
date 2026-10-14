"""
Quick standalone verification of SPCL/arxiv-for-fanns-medium dataset.
Checks file existence, file sizes, vector dimensions, and sample ground-truth bounds.
"""

from pathlib import Path
import json
import numpy as np

DATA_DIR = Path("data/arxiv-for-fanns-medium")
EXPECTED_DIMENSION = 4096
EXPECTED_DATABASE_SIZE = 100000
EXPECTED_QUERY_SIZE = 10000

print("=" * 70)
print("ARXIV-FOR-FANNS MEDIUM DATASET QUICK VERIFICATION")
print("=" * 70)

if not DATA_DIR.exists():
    print(f"\n[ERROR] Dataset directory does not exist: {DATA_DIR.resolve()}")
    print("Run: python download_dataset.py")
    raise SystemExit(1)

print(f"\nDataset directory: {DATA_DIR.resolve()}\n")

required_files = [
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

print("-" * 70)
print("1. CHECKING REQUIRED FILES ON DISK")
print("-" * 70)

missing_files = []
for filename in required_files:
    path = DATA_DIR / filename
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"[OK]      {filename:<35} {size_mb:>10.2f} MB")
    else:
        print(f"[MISSING] {filename}")
        missing_files.append(filename)

if missing_files:
    print(f"\n[ERROR] Missing {len(missing_files)} file(s).")
    raise SystemExit(1)

print("\n" + "-" * 70)
print("2. VERIFYING VECTOR SIZES AND DIMENSIONS")
print("-" * 70)

# Check database vectors
with open(DATA_DIR / "database_vectors.fvecs", "rb") as f:
    dim = int(np.frombuffer(f.read(4), dtype=np.int32)[0])
db_size = (DATA_DIR / "database_vectors.fvecs").stat().st_size
db_rec_size = (dim + 1) * 4
db_count = db_size // db_rec_size

print(f"Database Vectors: {db_count:,} (expected {EXPECTED_DATABASE_SIZE:,}) | Dim: {dim} (expected {EXPECTED_DIMENSION})")
assert db_count == EXPECTED_DATABASE_SIZE, f"DB size mismatch: {db_count} != {EXPECTED_DATABASE_SIZE}"
assert dim == EXPECTED_DIMENSION, f"DB dimension mismatch: {dim} != {EXPECTED_DIMENSION}"

# Check query vectors
with open(DATA_DIR / "query_vectors.fvecs", "rb") as f:
    q_dim = int(np.frombuffer(f.read(4), dtype=np.int32)[0])
q_size = (DATA_DIR / "query_vectors.fvecs").stat().st_size
q_rec_size = (q_dim + 1) * 4
q_count = q_size // q_rec_size

print(f"Query Vectors:    {q_count:,} (expected {EXPECTED_QUERY_SIZE:,}) | Dim: {q_dim} (expected {EXPECTED_DIMENSION})")
assert q_count == EXPECTED_QUERY_SIZE, f"Query size mismatch: {q_count} != {EXPECTED_QUERY_SIZE}"
assert q_dim == EXPECTED_DIMENSION, f"Query dimension mismatch: {q_dim} != {EXPECTED_DIMENSION}"

print("\n" + "=" * 70)
print("QUICK VERIFICATION PASSED")
print("=" * 70)
