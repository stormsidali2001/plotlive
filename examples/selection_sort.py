"""
Selection Sort visualizer.

    python3 examples/selection_sort.py
"""
import numpy as np
from sorting_utils import selection_sort_steps, run_sort_visualization

N = 7
np.random.seed(42)
arr = np.random.permutation(N) + 1

steps = list(selection_sort_steps(arr))
run_sort_visualization('Selection Sort', steps, N, interval=300)
