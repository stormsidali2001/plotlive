"""
Heap Sort visualizer.

    python3 examples/heap_sort.py
"""
import numpy as np
from sorting_utils import heap_sort_steps, run_sort_visualization

N = 7
np.random.seed(42)
arr = np.random.permutation(N) + 1

steps = heap_sort_steps(arr)
run_sort_visualization('Heap Sort', steps, N, interval=300)
