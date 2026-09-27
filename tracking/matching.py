"""
Data association and bipartite matching for Multi-Object Tracking.
Computes IoU distance matrices and solves optimal assignment via linear_sum_assignment (Hungarian method).
"""

from __future__ import annotations
from typing import List, Tuple
import numpy as np

try:
    from scipy.optimize import linear_sum_assignment
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def calculate_iou_matrix(
    boxes_a: np.ndarray,
    boxes_b: np.ndarray
) -> np.ndarray:
    """
    Calculate pairwise Intersection over Union (IoU) between two sets of bounding boxes.

    Args:
        boxes_a: Array of shape (N, 4) with [x1, y1, x2, y2]
        boxes_b: Array of shape (M, 4) with [x1, y1, x2, y2]

    Returns:
        IoU matrix of shape (N, M) with values in [0.0, 1.0]
    """
    if len(boxes_a) == 0 or len(boxes_b) == 0:
        return np.zeros((len(boxes_a), len(boxes_b)), dtype=np.float32)

    boxes_a = np.asarray(boxes_a, dtype=np.float32)
    boxes_b = np.asarray(boxes_b, dtype=np.float32)

    # Compute areas
    area_a = (boxes_a[:, 2] - boxes_a[:, 0]) * (boxes_a[:, 3] - boxes_a[:, 1])
    area_b = (boxes_b[:, 2] - boxes_b[:, 0]) * (boxes_b[:, 3] - boxes_b[:, 1])

    # Broadcast coordinates
    # (N, 1, 2) vs (1, M, 2) -> (N, M, 2)
    top_left = np.maximum(boxes_a[:, None, :2], boxes_b[None, :, :2])
    bottom_right = np.minimum(boxes_a[:, None, 2:], boxes_b[None, :, 2:])

    intersection_wh = np.maximum(0.0, bottom_right - top_left)
    intersection_area = intersection_wh[:, :, 0] * intersection_wh[:, :, 1]

    union_area = area_a[:, None] + area_b[None, :] - intersection_area
    union_area = np.maximum(union_area, 1e-6)

    return intersection_area / union_area


def greedy_assignment(
    cost_matrix: np.ndarray,
    max_cost: float
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    Greedy assignment fallback when scipy is not available or for sparse matching.
    """
    if cost_matrix.size == 0:
        return [], list(range(cost_matrix.shape[0])), list(range(cost_matrix.shape[1]))

    num_rows, num_cols = cost_matrix.shape
    matched_rows = set()
    matched_cols = set()
    matches = []

    # Sort flattened indices by cost ascending
    flat_indices = np.argsort(cost_matrix, axis=None)
    for idx in flat_indices:
        r = idx // num_cols
        c = idx % num_cols
        cost = cost_matrix[r, c]

        if cost > max_cost:
            break

        if r not in matched_rows and c not in matched_cols:
            matched_rows.add(r)
            matched_cols.add(c)
            matches.append((int(r), int(c)))

    unmatched_rows = [r for r in range(num_rows) if r not in matched_rows]
    unmatched_cols = [c for c in range(num_cols) if c not in matched_cols]

    return matches, unmatched_rows, unmatched_cols


def linear_assignment(
    cost_matrix: np.ndarray,
    max_cost: float
) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    Solve optimal bipartite matching using the Hungarian algorithm (linear sum assignment).

    Args:
        cost_matrix: Cost matrix (e.g. 1.0 - IoU) of shape (N, M)
        max_cost: Maximum allowable cost for a valid assignment (e.g. 1.0 - min_iou)

    Returns:
        (matches, unmatched_rows, unmatched_cols)
        - matches: list of (row_idx, col_idx) tuples with cost <= max_cost
        - unmatched_rows: list of row indices without valid matches
        - unmatched_cols: list of col indices without valid matches
    """
    if cost_matrix.size == 0:
        return [], list(range(cost_matrix.shape[0])), list(range(cost_matrix.shape[1]))

    if not HAS_SCIPY:
        return greedy_assignment(cost_matrix, max_cost)

    row_indices, col_indices = linear_sum_assignment(cost_matrix)

    matches = []
    unmatched_rows = list(range(cost_matrix.shape[0]))
    unmatched_cols = list(range(cost_matrix.shape[1]))

    for r, c in zip(row_indices, col_indices):
        if cost_matrix[r, c] <= max_cost:
            matches.append((int(r), int(c)))
            if r in unmatched_rows:
                unmatched_rows.remove(r)
            if c in unmatched_cols:
                unmatched_cols.remove(c)

    return matches, unmatched_rows, unmatched_cols
