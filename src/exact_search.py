"""
Exact Filtered and Unfiltered Nearest Neighbor Search Baseline.
Acts as the mathematical ground-truth correctness reference.
Optimized for medium-scale (100,000 vectors x 4,096 dimensions) via chunked BLAS matrix-vector evaluation.
"""

from typing import List, Optional, Tuple, Union
import numpy as np

from .filters import FilterPredicate, MetadataIndex


class ExactFilteredSearcher:
    """
    Exact Nearest Neighbor Search with metadata predicate filtering.
    Computes exact Euclidean L2 distances (or Inner Product) over valid candidates.
    Uses chunked BLAS evaluation to minimize RAM usage and prevent memory spikes.
    """
    def __init__(
        self,
        database_vectors: np.ndarray,
        metadata_index: MetadataIndex,
        metric: str = "l2",
        chunk_size: int = 5000,
    ):
        self.database_vectors = database_vectors  # Can be memory-mapped ndarray
        self.metadata_index = metadata_index
        self.metric = metric.lower()
        self.chunk_size = chunk_size
        self.num_vectors, self.dim = self.database_vectors.shape

        # Precompute L2 norms for database vectors in chunks to keep memory low
        if self.metric == "l2":
            self.db_norms = np.zeros(self.num_vectors, dtype=np.float32)
            for start in range(0, self.num_vectors, self.chunk_size):
                end = min(start + self.chunk_size, self.num_vectors)
                sub = self.database_vectors[start:end]
                self.db_norms[start:end] = np.einsum('ij,ij->i', sub, sub)
        else:
            self.db_norms = None

    def search(
        self,
        query_vector: np.ndarray,
        predicate: Optional[FilterPredicate] = None,
        k: int = 10
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """
        Executes exact search over candidate vectors satisfying predicate.
        Returns:
            (top_k_indices, top_k_distances, candidate_count)
        """
        candidate_ids = self.metadata_index.get_matching_ids(predicate)
        candidate_count = len(candidate_ids)

        if candidate_count == 0:
            return np.empty(0, dtype=np.int32), np.empty(0, dtype=np.float32), 0

        target_k = min(k, candidate_count)
        q_vec = np.ascontiguousarray(query_vector, dtype=np.float32)

        # For small candidate sets (<= chunk_size), evaluate directly
        if candidate_count <= self.chunk_size:
            cand_vecs = self.database_vectors[candidate_ids]
            if self.metric == "l2":
                q_norm = float(np.dot(q_vec, q_vec))
                cand_norms = self.db_norms[candidate_ids] if self.db_norms is not None else np.einsum('ij,ij->i', cand_vecs, cand_vecs)
                dists = cand_norms + q_norm - 2.0 * np.dot(cand_vecs, q_vec)
            elif self.metric in ("ip", "cosine", "inner_product"):
                dists = -np.dot(cand_vecs, q_vec)
            else:
                diff = cand_vecs - q_vec
                dists = np.einsum('ij,ij->i', diff, diff)

            if candidate_count <= target_k:
                sorted_local = np.argsort(dists)
                return candidate_ids[sorted_local], dists[sorted_local].astype(np.float32), candidate_count

            part = np.argpartition(dists, target_k)[:target_k]
            sub_sort = np.argsort(dists[part])
            best_idx = part[sub_sort]
            return candidate_ids[best_idx], dists[best_idx].astype(np.float32), candidate_count

        # For large candidate sets (> chunk_size), evaluate in chunks with a top-k buffer
        q_norm = float(np.dot(q_vec, q_vec)) if self.metric == "l2" else 0.0
        best_ids_list: List[int] = []
        best_dists_list: List[float] = []

        for c_start in range(0, candidate_count, self.chunk_size):
            c_end = min(c_start + self.chunk_size, candidate_count)
            chunk_cids = candidate_ids[c_start:c_end]
            cand_sub = self.database_vectors[chunk_cids]

            if self.metric == "l2":
                c_norms = self.db_norms[chunk_cids] if self.db_norms is not None else np.einsum('ij,ij->i', cand_sub, cand_sub)
                chunk_dists = c_norms + q_norm - 2.0 * np.dot(cand_sub, q_vec)
            elif self.metric in ("ip", "cosine"):
                chunk_dists = -np.dot(cand_sub, q_vec)
            else:
                diff = cand_sub - q_vec
                chunk_dists = np.einsum('ij,ij->i', diff, diff)

            # Keep top target_k of this chunk
            if len(chunk_cids) <= target_k:
                best_ids_list.extend(chunk_cids.tolist())
                best_dists_list.extend(chunk_dists.tolist())
            else:
                part = np.argpartition(chunk_dists, target_k)[:target_k]
                best_ids_list.extend(chunk_cids[part].tolist())
                best_dists_list.extend(chunk_dists[part].tolist())

        # Global top-k reduction across chunk winners
        all_cand_ids = np.array(best_ids_list, dtype=np.int32)
        all_cand_dists = np.array(best_dists_list, dtype=np.float32)

        if len(all_cand_ids) <= target_k:
            order = np.argsort(all_cand_dists)
            return all_cand_ids[order], all_cand_dists[order], candidate_count

        global_part = np.argpartition(all_cand_dists, target_k)[:target_k]
        global_sort = np.argsort(all_cand_dists[global_part])
        final_idx = global_part[global_sort]

        return all_cand_ids[final_idx], all_cand_dists[final_idx], candidate_count
