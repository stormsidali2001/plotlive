"""
Shared utilities for sorting algorithm visualizations.

Each step generator yields: (array_snapshot, comparisons, swaps, sorted_indices)
  - array_snapshot : np.ndarray  — current state of the array
  - comparisons    : set of int  — indices highlighted in orange (being compared)
  - swaps          : set of int  — indices highlighted in red (being swapped/moved)
  - sorted_indices : set of int  — indices highlighted in green (final position)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import mathplotgame.pyplot as plt
from mathplotgame.artists import Rectangle
from mathplotgame.colors import to_rgba

# ── Color palette ─────────────────────────────────────────────────────────────
C_DEFAULT = '#4C72B0'   # unsorted
C_COMPARE = '#FF8C00'   # comparing
C_SWAP    = '#E74C3C'   # swapping / moving
C_PIVOT   = '#9B59B6'   # pivot element (quicksort)
C_SORTED  = '#2ECC71'   # confirmed sorted

_LEGEND_ENTRIES = [
    (C_DEFAULT, 'Unsorted'),
    (C_COMPARE, 'Comparing'),
    (C_SWAP,    'Swapping'),
    (C_SORTED,  'Sorted'),
]


def make_colors(n, compare=(), swap=(), sorted_idx=(), pivot=None):
    colors = []
    for i in range(n):
        if i in swap:
            colors.append(C_SWAP)
        elif pivot is not None and i == pivot:
            colors.append(C_PIVOT)
        elif i in compare:
            colors.append(C_COMPARE)
        elif i in sorted_idx:
            colors.append(C_SORTED)
        else:
            colors.append(C_DEFAULT)
    return colors


# ── Step generators ───────────────────────────────────────────────────────────

def bubble_sort_steps(arr):
    a = arr.copy(); n = len(a); done = set()
    yield a.copy(), set(), set(), done.copy()
    for i in range(n):
        for j in range(0, n - i - 1):
            yield a.copy(), {j, j+1}, set(), done.copy()
            if a[j] > a[j+1]:
                a[j], a[j+1] = a[j+1], a[j]
                yield a.copy(), set(), {j, j+1}, done.copy()
        done.add(n - 1 - i)
        yield a.copy(), set(), set(), done.copy()
    yield a.copy(), set(), set(), set(range(n))


def insertion_sort_steps(arr):
    a = arr.copy(); n = len(a); done = {0}
    yield a.copy(), set(), set(), done.copy()
    for i in range(1, n):
        key = a[i]; j = i - 1
        yield a.copy(), {i}, set(), done.copy()
        while j >= 0 and a[j] > key:
            yield a.copy(), {j, j+1}, set(), done.copy()
            a[j+1] = a[j]
            yield a.copy(), set(), {j, j+1}, done.copy()
            j -= 1
        a[j+1] = key
        done.add(j+1)
        yield a.copy(), set(), set(), done.copy()
    yield a.copy(), set(), set(), set(range(n))


def selection_sort_steps(arr):
    a = arr.copy(); n = len(a); done = set()
    yield a.copy(), set(), set(), done.copy()
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            yield a.copy(), {min_idx, j}, set(), done.copy()
            if a[j] < a[min_idx]:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]
            yield a.copy(), set(), {i, min_idx}, done.copy()
        done.add(i)
        yield a.copy(), set(), set(), done.copy()
    yield a.copy(), set(), set(), set(range(n))


def heap_sort_steps(arr):
    a = arr.copy(); n = len(a); steps = []

    def heapify(arr, size, i):
        largest = i
        l, r = 2*i + 1, 2*i + 2
        steps.append((arr.copy(), {i, l} if l < size else {i}, set(), set()))
        if l < size and arr[l] > arr[largest]:
            largest = l
        steps.append((arr.copy(), {i, r} if r < size else {i}, set(), set()))
        if r < size and arr[r] > arr[largest]:
            largest = r
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            steps.append((arr.copy(), set(), {i, largest}, set()))
            heapify(arr, size, largest)

    steps.append((a.copy(), set(), set(), set()))
    for i in range(n // 2 - 1, -1, -1):
        heapify(a, n, i)

    done = set()
    for i in range(n - 1, 0, -1):
        a[0], a[i] = a[i], a[0]
        done.add(i)
        steps.append((a.copy(), set(), {0, i}, done.copy()))
        heapify(a, i, 0)
    done.add(0)
    steps.append((a.copy(), set(), set(), set(range(n))))
    return steps


def merge_sort_steps(arr):
    a = arr.copy(); steps = []
    steps.append((a.copy(), set(), set(), set()))

    def merge_sort(arr, l, r):
        if l >= r:
            return
        mid = (l + r) // 2
        merge_sort(arr, l, mid)
        merge_sort(arr, mid + 1, r)
        left = arr[l:mid+1].copy()
        right = arr[mid+1:r+1].copy()
        i = j = 0; k = l
        while i < len(left) and j < len(right):
            steps.append((arr.copy(), {l+i, mid+1+j}, set(), set()))
            if left[i] <= right[j]:
                arr[k] = left[i]; i += 1
            else:
                arr[k] = right[j]; j += 1
            steps.append((arr.copy(), set(), {k}, set()))
            k += 1
        while i < len(left):
            arr[k] = left[i]; i += 1; k += 1
            steps.append((arr.copy(), set(), {k-1}, set()))
        while j < len(right):
            arr[k] = right[j]; j += 1; k += 1
            steps.append((arr.copy(), set(), {k-1}, set()))

    merge_sort(a, 0, len(a) - 1)
    steps.append((a.copy(), set(), set(), set(range(len(a)))))
    return steps


def quick_sort_steps(arr):
    a = arr.copy(); steps = []
    steps.append((a.copy(), set(), set(), set()))

    def partition(arr, low, high):
        pivot_val = arr[high]
        steps.append((arr.copy(), {high}, set(), set()))
        i = low - 1
        for j in range(low, high):
            steps.append((arr.copy(), {high, j}, set(), set()))
            if arr[j] <= pivot_val:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                steps.append((arr.copy(), {high}, {i, j}, set()))
        arr[i+1], arr[high] = arr[high], arr[i+1]
        steps.append((arr.copy(), set(), {i+1, high}, set()))
        return i + 1

    def quick_sort(arr, low, high):
        if low < high:
            pi = partition(arr, low, high)
            quick_sort(arr, low, pi - 1)
            quick_sort(arr, pi + 1, high)

    quick_sort(a, 0, len(a) - 1)
    steps.append((a.copy(), set(), set(), set(range(len(a)))))
    return steps


# ── Shared runner ─────────────────────────────────────────────────────────────

def _add_legend_patches(ax, steps_total, current_step):
    """Append zero-size legend-only patches so the legend shows all color categories."""
    for color_hex, label in _LEGEND_ENTRIES:
        dummy = Rectangle(0, 0, 0, 0, color=color_hex, edgecolor='none', label=label)
        ax.patches.append(dummy)
    ax.legend()


def run_sort_visualization(title, steps, n, interval=40):
    """
    Launch a standalone sorting visualization window.

    title    : window / plot title
    steps    : list of (array, compare_set, swap_set, sorted_set)
    n        : number of elements (used for ylim)
    interval : milliseconds between frames
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    def update(frame):
        i = min(frame, len(steps) - 1)
        state, compare, swap, sorted_idx = steps[i]
        colors = make_colors(len(state), compare, swap, sorted_idx)

        ax.cla()
        ax.bar(range(len(state)), state, color=colors,
               edgecolor='white', linewidth=0.5, width=0.7)

        # Show the current value under each bar as an x-tick label
        ax.set_xticks(range(n), [str(int(v)) for v in state])
        ax.set_ylim(0, n + 1)
        ax.set_xlim(-0.5, n - 0.5)
        ax.set_yticks(range(1, n + 1), [str(k) for k in range(1, n + 1)])

        ax.set_xlabel('Array position  (number below bar = current value)')
        ax.set_ylabel('Value')

        # Describe what is happening at this step
        if compare:
            action = f'Comparing positions {sorted(compare)}'
        elif swap:
            action = f'Swapping positions {sorted(swap)}'
        elif sorted_idx == set(range(n)):
            action = 'Sorted!'
        else:
            action = 'Scanning...'
        ax.set_title(f'Step {i + 1} / {len(steps)}  —  {action}')

        # Legend entries for color categories
        _add_legend_patches(ax, len(steps), i)

    fig.suptitle(
        f'{title}   ({n} elements, {len(steps)} steps)'
        f'   |   Space: play/pause   <- ->: step   S: save'
    )

    plt.animate(update, frames=len(steps), interval=interval)
    plt.show()
