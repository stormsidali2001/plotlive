"""
Quick Sort visualizer.

    python3 examples/quick_sort.py
"""
import numpy as np
from sorting_utils import quick_sort_steps, run_sort_visualization

N = 7
np.random.seed(42)
arr = np.random.permutation(N) + 1

steps = quick_sort_steps(arr)
run_sort_visualization('Quick Sort', steps, N, interval=300)
