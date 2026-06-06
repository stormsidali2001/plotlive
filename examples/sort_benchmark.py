"""
Sorting Algorithm Benchmark

Measures the runtime of all 6 sorting algorithms across increasing input
sizes, then shows an animated line chart that reveals one size at a time
so you can watch how each algorithm scales as N grows.

    cd examples
    python3 sort_benchmark.py
"""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import mathplotgame.pyplot as plt


# ── Pure Python in-place implementations (no C extensions, fair comparison) ───

def _bubble(a):
    a = a.tolist(); n = len(a)
    for i in range(n):
        for j in range(n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]


def _insertion(a):
    a = a.tolist()
    for i in range(1, len(a)):
        key = a[i]; j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]; j -= 1
        a[j + 1] = key


def _selection(a):
    a = a.tolist(); n = len(a)
    for i in range(n):
        m = i
        for j in range(i + 1, n):
            if a[j] < a[m]:
                m = j
        a[i], a[m] = a[m], a[i]


def _heap(a):
    # Pure Python in-place max-heap sort (no heapq — that's a C extension)
    a = a.tolist(); n = len(a)

    def sift(arr, root, end):
        while True:
            child = 2 * root + 1
            if child >= end:
                break
            if child + 1 < end and arr[child] < arr[child + 1]:
                child += 1
            if arr[root] < arr[child]:
                arr[root], arr[child] = arr[child], arr[root]
                root = child
            else:
                break

    for i in range(n // 2 - 1, -1, -1):
        sift(a, i, n)
    for i in range(n - 1, 0, -1):
        a[0], a[i] = a[i], a[0]
        sift(a, 0, i)


def _merge(a):
    def ms(arr):
        if len(arr) <= 1:
            return arr
        m = len(arr) // 2
        left, right = ms(arr[:m]), ms(arr[m:])
        result = []; i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i]); i += 1
            else:
                result.append(right[j]); j += 1
        return result + left[i:] + right[j:]
    ms(a.tolist())


def _quick(a):
    # In-place Hoare partition — avoids creating intermediate lists
    def qs(arr, lo, hi):
        if lo >= hi:
            return
        pivot = arr[(lo + hi) // 2]
        i, j = lo, hi
        while i <= j:
            while arr[i] < pivot: i += 1
            while arr[j] > pivot: j -= 1
            if i <= j:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1; j -= 1
        qs(arr, lo, j)
        qs(arr, i, hi)
    arr = a.tolist()
    qs(arr, 0, len(arr) - 1)


ALGOS = [
    ('Bubble Sort',    _bubble),
    ('Insertion Sort', _insertion),
    ('Selection Sort', _selection),
    ('Heap Sort',      _heap),
    ('Merge Sort',     _merge),
    ('Quick Sort',     _quick),
]

COLORS = ['#E74C3C', '#E67E22', '#2980B9', '#27AE60', '#8E44AD', '#E91E63']
#          red        orange      blue        green       purple      pink

SIZES   = [10, 25, 50, 100, 200, 350, 500]
REPEATS = 3   # runs averaged per (algorithm, size) pair


# ── Benchmark (runs before the window opens) ──────────────────────────────────

print('Benchmarking sorting algorithms — this takes a few seconds...')
rng = np.random.default_rng(42)
timings = {}   # {algo_name: [ms, ms, ...]}  one value per size

for name, fn in ALGOS:
    print(f'  {name}...', end=' ', flush=True)
    row = []
    for n in SIZES:
        arr = rng.integers(1, n * 10, size=n).astype(float)
        total = 0.0
        for _ in range(REPEATS):
            t0 = time.perf_counter()
            fn(arr)
            total += time.perf_counter() - t0
        row.append(total / REPEATS * 1000)   # convert to ms
    timings[name] = row
    print('done')

print('Opening comparison chart...\n')

y_min_all = min(v for row in timings.values() for v in row if v > 0)
y_max_all = max(v for row in timings.values() for v in row) * 2.0


# ── Single-panel animated chart with log Y scale ──────────────────────────────
# Log scale keeps all 6 algorithms visible at the same time — O(n²) lines curve
# upward while O(n log n) lines stay nearly flat.

fig, ax = plt.subplots(figsize=(11, 6))

fig.suptitle(
    f'Runtime averaged over {REPEATS} runs each  (log scale)'
    '   |   Space: play / pause   <- ->: step   R: restart'
)


def update(frame):
    k = frame + 1
    xs = SIZES[:k]

    ax.cla()
    ax.set_yscale('log')
    ax.grid()

    for (name, _), color in zip(ALGOS, COLORS):
        ys = timings[name][:k]
        ax.plot(xs, ys, color=color, marker='o',
                linewidth=2, markersize=7, label=name)

    ax.set_xlabel('Input size  N')
    ax.set_ylabel('Time  (ms, log scale)')
    ax.set_xlim(-10, SIZES[-1] * 1.08)
    ax.set_ylim(y_min_all * 0.5, y_max_all)
    ax.set_title(f'Sorting Algorithm Runtime Comparison  —  N = {SIZES[k - 1]}')
    ax.legend()


plt.animate(update, frames=len(SIZES), interval=900)
plt.show()
