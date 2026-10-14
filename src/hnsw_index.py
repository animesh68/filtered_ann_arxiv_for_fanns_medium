"""
High-Performance Hierarchical Navigable Small World (HNSW) Index Implementation.
Designed for FANNS research: provides full visibility and hooks for post-filtering,
in-graph filtering, ACORN hybrid routing, SIEVE entry-points, and UNIFY graph traversal.
Optimized for medium-scale (100,000 vectors x 4,096 dims) with precomputed L2 norms,
batch distance evaluation, and disk serialization/caching.
"""

import heapq
import math
import pickle
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import numpy as np


class HNSWIndex:
    """
    Hierarchical Navigable Small World (HNSW) Graph Index.
    Implements Malkov & Yashunin (2018) algorithm with research hooks for metadata filtering.
    """
    def __init__(
        self,
        dimension: int,
        metric: str = "l2",
        M: int = 16,
        ef_construction: int = 100,
        random_seed: int = 42,
    ):
        self.dimension = dimension
        self.metric = metric.lower()
        self.M = M
        self.M0 = 2 * M  # Max connections for layer 0
        self.ef_construction = ef_construction
        self.random_seed = random_seed
        self.mL = 1.0 / math.log(M) if M > 1 else 1.0

        self.rng = np.random.RandomState(random_seed)
        self.vectors: Optional[np.ndarray] = None
        self.norms: Optional[np.ndarray] = None
        self.num_nodes: int = 0
        self.enter_point: Optional[int] = None
        self.max_layer: int = -1

        # Multi-layer adjacency lists: layers[lc][node_id] = list of neighbor IDs
        self.layers: List[Dict[int, List[int]]] = []
        self.node_layers: List[int] = []

    def set_vectors(self, vectors: np.ndarray, norms: Optional[np.ndarray] = None):
        """Attaches vector matrix and precomputed L2 norms."""
        self.vectors = vectors
        self.num_nodes = vectors.shape[0]
        if norms is not None:
            self.norms = norms
        elif self.metric == "l2":
            # Compute norms in chunks to stay memory safe
            self.norms = np.zeros(self.num_nodes, dtype=np.float32)
            chunk = 5000
            for start in range(0, self.num_nodes, chunk):
                end = min(start + chunk, self.num_nodes)
                sub = self.vectors[start:end]
                self.norms[start:end] = np.einsum('ij,ij->i', sub, sub)
        else:
            self.norms = None

    def _dist(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Fallback compute distance between two arbitrary vectors."""
        if self.metric == "l2":
            diff = vec_a - vec_b
            return float(np.dot(diff, diff))
        elif self.metric in ("ip", "cosine"):
            return float(-np.dot(vec_a, vec_b))
        else:
            diff = vec_a - vec_b
            return float(np.dot(diff, diff))

    def _dist_node_query(self, node_id: int, query_vec: np.ndarray, q_norm: Optional[float] = None) -> float:
        """Fast L2 distance between node_id in index and query_vec."""
        if self.metric == "l2" and self.norms is not None:
            if q_norm is None:
                q_norm = float(np.dot(query_vec, query_vec))
            dot = float(np.dot(self.vectors[node_id], query_vec))
            d = self.norms[node_id] + q_norm - 2.0 * dot
            return max(0.0, d)
        elif self.metric in ("ip", "cosine"):
            return float(-np.dot(self.vectors[node_id], query_vec))
        else:
            diff = self.vectors[node_id] - query_vec
            return float(np.dot(diff, diff))

    def _dist_node_node(self, node_a: int, node_b: int) -> float:
        """Fast L2 distance between two nodes in index."""
        if self.metric == "l2" and self.norms is not None:
            dot = float(np.dot(self.vectors[node_a], self.vectors[node_b]))
            d = self.norms[node_a] + self.norms[node_b] - 2.0 * dot
            return max(0.0, d)
        elif self.metric in ("ip", "cosine"):
            return float(-np.dot(self.vectors[node_a], self.vectors[node_b]))
        else:
            diff = self.vectors[node_a] - self.vectors[node_b]
            return float(np.dot(diff, diff))

    def _get_random_layer(self) -> int:
        """Select node max level using exponential distribution."""
        return int(-math.log(self.rng.uniform(1e-9, 1.0)) * self.mL)

    def build_index(self, vectors: np.ndarray, progress_bar: bool = True):
        """Build HNSW graph over dataset vectors."""
        self.set_vectors(vectors)
        self.layers = []
        self.node_layers = []

        iterable = range(self.num_nodes)
        if progress_bar:
            try:
                from tqdm import tqdm
                iterable = tqdm(iterable, desc="Building HNSW Index", total=self.num_nodes)
            except ImportError:
                pass

        for i in iterable:
            self._insert_point(i)

    def _insert_point(self, point_id: int):
        """Insert a single point into the hierarchical graph."""
        vec = self.vectors[point_id]
        vec_norm = float(self.norms[point_id]) if self.norms is not None else float(np.dot(vec, vec))
        level = self._get_random_layer()
        self.node_layers.append(level)

        while len(self.layers) <= level:
            self.layers.append({})

        if self.enter_point is None:
            self.enter_point = point_id
            self.max_layer = level
            for lc in range(level + 1):
                self.layers[lc][point_id] = []
            return

        curr_ep = self.enter_point
        curr_dist = self._dist_node_query(curr_ep, vec, vec_norm)

        # 1. Greedy routing down to level + 1
        for lc in range(self.max_layer, level, -1):
            changed = True
            while changed:
                changed = False
                for neighbor in self.layers[lc].get(curr_ep, []):
                    d = self._dist_node_query(neighbor, vec, vec_norm)
                    if d < curr_dist:
                        curr_dist = d
                        curr_ep = neighbor
                        changed = True

        # 2. Search and connect from min(max_layer, level) down to layer 0
        top_l = min(self.max_layer, level)
        ep_set = [curr_ep]

        for lc in range(top_l, -1, -1):
            candidates = self._search_layer_base(
                vec, ep_set, ef=self.ef_construction, lc=lc, q_norm=vec_norm
            )
            m_max = self.M0 if lc == 0 else self.M
            selected_neighbors = self._select_heuristic(candidates, m_max)

            self.layers[lc][point_id] = selected_neighbors

            for neighbor in selected_neighbors:
                n_list = self.layers[lc].setdefault(neighbor, [])
                n_list.append(point_id)
                if len(n_list) > m_max:
                    if self.norms is not None:
                        n_arr = np.array(n_list, dtype=np.int32)
                        dots = np.dot(self.vectors[n_arr], self.vectors[neighbor])
                        dists = self.norms[n_arr] + self.norms[neighbor] - 2.0 * dots
                        part = np.argpartition(dists, m_max)[:m_max]
                        sub_sort = np.argsort(dists[part])
                        self.layers[lc][neighbor] = n_arr[part[sub_sort]].tolist()
                    else:
                        cand_n = [(self._dist_node_node(neighbor, n_id), n_id) for n_id in n_list]
                        self.layers[lc][neighbor] = self._select_heuristic(cand_n, m_max)

            ep_set = [c[1] for c in candidates]

        if level > self.max_layer:
            self.max_layer = level
            self.enter_point = point_id

    def _select_heuristic(
        self, candidates: List[Tuple[float, int]], max_m: int
    ) -> List[int]:
        """Simple greedy neighbor selection."""
        sorted_cand = sorted(candidates, key=lambda x: x[0])
        return [cand_id for _, cand_id in sorted_cand[:max_m]]

    def _search_layer_base(
        self,
        query_vec: np.ndarray,
        entry_points: List[int],
        ef: int,
        lc: int,
        q_norm: Optional[float] = None,
    ) -> List[Tuple[float, int]]:
        """Beam search at layer lc."""
        if q_norm is None and self.metric == "l2":
            q_norm = float(np.dot(query_vec, query_vec))

        visited = set(entry_points)
        candidates = []
        w = []

        for ep in entry_points:
            d = self._dist_node_query(ep, query_vec, q_norm)
            heapq.heappush(candidates, (d, ep))
            heapq.heappush(w, (-d, ep))

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)
            furthest_w_dist = -w[0][0]

            if c_dist > furthest_w_dist and len(w) >= ef:
                break

            neighbors = self.layers[lc].get(c_id, [])
            unvisited = [n for n in neighbors if n not in visited]
            if not unvisited:
                continue

            for n in unvisited:
                visited.add(n)

            if self.norms is not None and self.metric == "l2":
                u_arr = np.array(unvisited, dtype=np.int32)
                dots = np.dot(self.vectors[u_arr], query_vec)
                dists = self.norms[u_arr] + q_norm - 2.0 * dots
                for idx, neighbor in enumerate(unvisited):
                    d_n = max(0.0, float(dists[idx]))
                    furthest_w_dist = -w[0][0]
                    if d_n < furthest_w_dist or len(w) < ef:
                        heapq.heappush(candidates, (d_n, neighbor))
                        heapq.heappush(w, (-d_n, neighbor))
                        if len(w) > ef:
                            heapq.heappop(w)
            else:
                for neighbor in unvisited:
                    d_n = self._dist_node_query(neighbor, query_vec, q_norm)
                    furthest_w_dist = -w[0][0]
                    if d_n < furthest_w_dist or len(w) < ef:
                        heapq.heappush(candidates, (d_n, neighbor))
                        heapq.heappush(w, (-d_n, neighbor))
                        if len(w) > ef:
                            heapq.heappop(w)

        return [(-d, node_id) for d, node_id in w]

    def search_unfiltered(
        self,
        query_vec: np.ndarray,
        k: int = 10,
        ef_search: int = 50,
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """Standard unfiltered HNSW search."""
        if self.enter_point is None or self.num_nodes == 0:
            return np.empty(0, dtype=np.int32), np.empty(0, dtype=np.float32), 0

        q_norm = float(np.dot(query_vec, query_vec)) if self.metric == "l2" else None
        curr_ep = self.enter_point
        curr_dist = self._dist_node_query(curr_ep, query_vec, q_norm)
        visited_count = 1

        for lc in range(self.max_layer, 0, -1):
            changed = True
            while changed:
                changed = False
                for neighbor in self.layers[lc].get(curr_ep, []):
                    visited_count += 1
                    d = self._dist_node_query(neighbor, query_vec, q_norm)
                    if d < curr_dist:
                        curr_dist = d
                        curr_ep = neighbor
                        changed = True

        ef = max(ef_search, k)
        visited = {curr_ep}
        candidates = [(curr_dist, curr_ep)]
        w = [(-curr_dist, curr_ep)]

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)
            furthest_w_dist = -w[0][0]

            if c_dist > furthest_w_dist and len(w) >= ef:
                break

            neighbors = self.layers[0].get(c_id, [])
            unvisited = [n for n in neighbors if n not in visited]
            if not unvisited:
                continue

            for n in unvisited:
                visited.add(n)

            if self.norms is not None and self.metric == "l2":
                u_arr = np.array(unvisited, dtype=np.int32)
                dots = np.dot(self.vectors[u_arr], query_vec)
                dists = self.norms[u_arr] + q_norm - 2.0 * dots
                for idx, neighbor in enumerate(unvisited):
                    d_n = max(0.0, float(dists[idx]))
                    furthest_w_dist = -w[0][0]
                    if d_n < furthest_w_dist or len(w) < ef:
                        heapq.heappush(candidates, (d_n, neighbor))
                        heapq.heappush(w, (-d_n, neighbor))
                        if len(w) > ef:
                            heapq.heappop(w)
            else:
                for neighbor in unvisited:
                    d_n = self._dist_node_query(neighbor, query_vec, q_norm)
                    furthest_w_dist = -w[0][0]
                    if d_n < furthest_w_dist or len(w) < ef:
                        heapq.heappush(candidates, (d_n, neighbor))
                        heapq.heappush(w, (-d_n, neighbor))
                        if len(w) > ef:
                            heapq.heappop(w)

        sorted_results = sorted([(-d, node_id) for d, node_id in w], key=lambda x: x[0])[:k]
        topk_ids = np.array([x[1] for x in sorted_results], dtype=np.int32)
        topk_dists = np.array([x[0] for x in sorted_results], dtype=np.float32)
        return topk_ids, topk_dists, len(visited)

    def search_ingraph(
        self,
        query_vec: np.ndarray,
        valid_mask: np.ndarray,
        k: int = 10,
        ef_search: int = 50,
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """In-Graph Filtered Search."""
        if self.enter_point is None or self.num_nodes == 0:
            return np.empty(0, dtype=np.int32), np.empty(0, dtype=np.float32), 0

        q_norm = float(np.dot(query_vec, query_vec)) if self.metric == "l2" else None
        curr_ep = self.enter_point
        curr_dist = self._dist_node_query(curr_ep, query_vec, q_norm)
        visited_count = 1

        for lc in range(self.max_layer, 0, -1):
            changed = True
            while changed:
                changed = False
                for neighbor in self.layers[lc].get(curr_ep, []):
                    visited_count += 1
                    d = self._dist_node_query(neighbor, query_vec, q_norm)
                    if d < curr_dist:
                        curr_dist = d
                        curr_ep = neighbor
                        changed = True

        ef = max(ef_search, k)
        visited = {curr_ep}
        candidates = [(curr_dist, curr_ep)]
        w = []

        if valid_mask[curr_ep]:
            heapq.heappush(w, (-curr_dist, curr_ep))

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)
            furthest_w_dist = -w[0][0] if len(w) >= ef else float('inf')

            if c_dist > furthest_w_dist and len(w) >= ef:
                break

            neighbors = self.layers[0].get(c_id, [])
            unvisited = [n for n in neighbors if n not in visited]
            if not unvisited:
                continue

            for n in unvisited:
                visited.add(n)

            if self.norms is not None and self.metric == "l2":
                u_arr = np.array(unvisited, dtype=np.int32)
                dots = np.dot(self.vectors[u_arr], query_vec)
                dists = self.norms[u_arr] + q_norm - 2.0 * dots
                for idx, neighbor in enumerate(unvisited):
                    d_n = max(0.0, float(dists[idx]))
                    furthest_w_dist = -w[0][0] if len(w) >= ef else float('inf')
                    heapq.heappush(candidates, (d_n, neighbor))
                    if valid_mask[neighbor]:
                        if d_n < furthest_w_dist or len(w) < ef:
                            heapq.heappush(w, (-d_n, neighbor))
                            if len(w) > ef:
                                heapq.heappop(w)
            else:
                for neighbor in unvisited:
                    d_n = self._dist_node_query(neighbor, query_vec, q_norm)
                    furthest_w_dist = -w[0][0] if len(w) >= ef else float('inf')
                    heapq.heappush(candidates, (d_n, neighbor))
                    if valid_mask[neighbor]:
                        if d_n < furthest_w_dist or len(w) < ef:
                            heapq.heappush(w, (-d_n, neighbor))
                            if len(w) > ef:
                                heapq.heappop(w)

        sorted_results = sorted([(-d, node_id) for d, node_id in w], key=lambda x: x[0])[:k]
        topk_ids = np.array([x[1] for x in sorted_results], dtype=np.int32)
        topk_dists = np.array([x[0] for x in sorted_results], dtype=np.float32)
        return topk_ids, topk_dists, len(visited)

    def search_acorn_style(
        self,
        query_vec: np.ndarray,
        valid_mask: np.ndarray,
        k: int = 10,
        ef_search: int = 50,
        n_hops: int = 2,
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """ACORN-style Filtered Traversal (Paper-inspired approximation)."""
        if self.enter_point is None or self.num_nodes == 0:
            return np.empty(0, dtype=np.int32), np.empty(0, dtype=np.float32), 0

        q_norm = float(np.dot(query_vec, query_vec)) if self.metric == "l2" else None
        curr_ep = self.enter_point
        curr_dist = self._dist_node_query(curr_ep, query_vec, q_norm)

        for lc in range(self.max_layer, 0, -1):
            changed = True
            while changed:
                changed = False
                for neighbor in self.layers[lc].get(curr_ep, []):
                    d = self._dist_node_query(neighbor, query_vec, q_norm)
                    if d < curr_dist:
                        curr_dist = d
                        curr_ep = neighbor
                        changed = True

        ef = max(ef_search, k)
        visited = {curr_ep}
        candidates = [(curr_dist, curr_ep)]
        w = []

        if valid_mask[curr_ep]:
            heapq.heappush(w, (-curr_dist, curr_ep))

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)
            furthest_w_dist = -w[0][0] if len(w) >= ef else float('inf')

            if c_dist > furthest_w_dist and len(w) >= ef:
                break

            neighbors_to_check = set(self.layers[0].get(c_id, []))
            if not valid_mask[c_id] and n_hops > 1:
                for n1 in list(neighbors_to_check):
                    for n2 in self.layers[0].get(n1, []):
                        if n2 not in visited:
                            neighbors_to_check.add(n2)

            unvisited = [n for n in neighbors_to_check if n not in visited]
            if not unvisited:
                continue

            for n in unvisited:
                visited.add(n)

            if self.norms is not None and self.metric == "l2":
                u_arr = np.array(unvisited, dtype=np.int32)
                dots = np.dot(self.vectors[u_arr], query_vec)
                dists = self.norms[u_arr] + q_norm - 2.0 * dots
                for idx, neighbor in enumerate(unvisited):
                    d_n = max(0.0, float(dists[idx]))
                    furthest_w_dist = -w[0][0] if len(w) >= ef else float('inf')
                    heapq.heappush(candidates, (d_n, neighbor))
                    if valid_mask[neighbor]:
                        if d_n < furthest_w_dist or len(w) < ef:
                            heapq.heappush(w, (-d_n, neighbor))
                            if len(w) > ef:
                                heapq.heappop(w)
            else:
                for neighbor in unvisited:
                    d_n = self._dist_node_query(neighbor, query_vec, q_norm)
                    furthest_w_dist = -w[0][0] if len(w) >= ef else float('inf')
                    heapq.heappush(candidates, (d_n, neighbor))
                    if valid_mask[neighbor]:
                        if d_n < furthest_w_dist or len(w) < ef:
                            heapq.heappush(w, (-d_n, neighbor))
                            if len(w) > ef:
                                heapq.heappop(w)

        sorted_results = sorted([(-d, node_id) for d, node_id in w], key=lambda x: x[0])[:k]
        topk_ids = np.array([x[1] for x in sorted_results], dtype=np.int32)
        topk_dists = np.array([x[0] for x in sorted_results], dtype=np.float32)
        return topk_ids, topk_dists, len(visited)

    def save_index(self, filepath: Union[str, Path]):
        """Serializes HNSW graph topology (layers, enter_point, node_layers) to disk."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "dimension": self.dimension,
            "metric": self.metric,
            "M": self.M,
            "M0": self.M0,
            "ef_construction": self.ef_construction,
            "enter_point": self.enter_point,
            "max_layer": self.max_layer,
            "layers": self.layers,
            "node_layers": self.node_layers,
            "num_nodes": self.num_nodes,
        }
        with open(filepath, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def load_index(self, filepath: Union[str, Path], vectors: np.ndarray, norms: Optional[np.ndarray] = None):
        """Loads serialized HNSW graph topology and attaches vector matrix."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Index file not found: {filepath}")
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        self.dimension = data["dimension"]
        self.metric = data["metric"]
        self.M = data["M"]
        self.M0 = data["M0"]
        self.ef_construction = data["ef_construction"]
        self.enter_point = data["enter_point"]
        self.max_layer = data["max_layer"]
        self.layers = data["layers"]
        self.node_layers = data["node_layers"]
        self.set_vectors(vectors, norms=norms)

    def estimate_memory_mb(self) -> float:
        """Estimate total RAM consumption in Megabytes."""
        bytes_total = 0
        if self.vectors is not None:
            bytes_total += self.vectors.nbytes
        if self.norms is not None:
            bytes_total += self.norms.nbytes
        for layer in self.layers:
            for k, v in layer.items():
                bytes_total += sys.getsizeof(k) + sys.getsizeof(v) + len(v) * 4
        return bytes_total / (1024 * 1024)
