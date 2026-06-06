"""
Bubble Sort visualizer.

    python3 examples/bubble_sort.py
"""
import numpy as np
from sorting_utils import bubble_sort_steps, run_sort_visualization

N = 7
np.random.seed(42)
arr = np.random.permutation(N) + 1

steps = list(bubble_sort_steps(arr))
run_sort_visualization('Bubble Sort', steps, N, interval=300)
