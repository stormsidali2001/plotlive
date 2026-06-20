"""
plotlive — Interactive matplotlib-compatible graphs rendered with pygame.

Usage:
    import plotlive.pyplot as plt
    import numpy as np

    plt.plot([1, 2, 3], [4, 5, 6], label='data')
    plt.legend()
    plt.show()
"""
from .figure import Figure
from .axes import Axes
from . import pyplot
from .pyplot import show, figure, subplots

__all__ = ['Figure', 'Axes', 'pyplot', 'show', 'figure', 'subplots']
__version__ = '0.1.0'
