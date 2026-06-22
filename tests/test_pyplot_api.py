"""Tests for the pyplot state-machine API and axes decoration methods."""
import os
import numpy as np
import pytest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import plotlive.pyplot as plt
from plotlive.axes import Axes
from plotlive.figure import Figure


# ── Helpers ───────────────────────────────────────────────────────────────────

def fresh():
    """Reset pyplot globals and return a fresh figure+axes."""
    plt._figures.clear()
    plt._current_figure = None
    plt._current_axes = None
    fig = plt.figure(figsize=(6, 4))
    return fig


# ── State machine basics ──────────────────────────────────────────────────────

class TestStateMachine:
    def setup_method(self):
        fresh()

    def test_gcf_creates_figure(self):
        fig = plt.gcf()
        assert isinstance(fig, Figure)

    def test_gca_creates_axes(self):
        ax = plt.gca()
        assert isinstance(ax, Axes)

    def test_gcf_returns_same(self):
        f1 = plt.gcf()
        f2 = plt.gcf()
        assert f1 is f2

    def test_figure_adds_to_registry(self):
        count_before = len(plt._figures)
        plt.figure()
        assert len(plt._figures) == count_before + 1

    def test_plot_delegates_to_gca(self):
        lines = plt.plot([1, 2, 3], [4, 5, 6])
        assert len(lines) == 1
        ax = plt.gca()
        assert len(ax.lines) == 1

    def test_scatter_delegates(self):
        plt.scatter([1, 2], [3, 4])
        assert len(plt.gca().collections) == 1

    def test_xlabel_ylabel_title(self):
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.title('T')
        ax = plt.gca()
        assert ax._xlabel == 'X'
        assert ax._ylabel == 'Y'
        assert ax._title == 'T'

    def test_xlim_ylim(self):
        plt.xlim(0, 5)
        plt.ylim(-1, 1)
        ax = plt.gca()
        assert ax.get_xlim() == (0.0, 5.0)
        assert ax.get_ylim() == (-1.0, 1.0)

    def test_xlim_get_returns_current(self):
        plt.plot([0, 10], [0, 10])
        # Before manual set, auto is True
        assert plt.gca()._xlim_auto is True
        result = plt.xlim()
        # returns current limits without setting
        assert len(result) == 2

    def test_grid_enables(self):
        plt.grid(True)
        assert plt.gca()._grid is True

    def test_grid_disables(self):
        plt.grid(True)
        plt.grid(False)
        assert plt.gca()._grid is False

    def test_legend_makes_visible(self):
        plt.plot([1], [1], label='a')
        plt.legend()
        assert plt.gca()._legend_visible is True

    def test_xscale_yscale(self):
        plt.xscale('log')
        plt.yscale('log')
        ax = plt.gca()
        assert ax._xscale == 'log'
        assert ax._yscale == 'log'

    def test_xticks_yticks(self):
        plt.xticks([0, 1, 2], ['a', 'b', 'c'])
        plt.yticks([0, 0.5, 1])
        ax = plt.gca()
        assert ax._xticks_manual == [0, 1, 2]
        assert ax._xtick_labels_manual == ['a', 'b', 'c']
        assert ax._yticks_manual == [0, 0.5, 1]

    def test_subplots_returns_figure_and_ax(self):
        fig2, ax2 = plt.subplots()
        assert isinstance(fig2, Figure)
        assert isinstance(ax2, Axes)

    def test_subplots_2x2(self):
        fig2, axs = plt.subplots(2, 2)
        assert axs.shape == (2, 2)

    def test_subplots_1xN_squeeze(self):
        _, axs = plt.subplots(1, 3)
        assert axs.shape == (3,)

    def test_cla_clears_gca(self):
        plt.plot([1, 2], [3, 4])
        plt.cla()
        assert len(plt.gca().lines) == 0

    def test_savefig_creates_file(self):
        import tempfile
        plt.plot([0, 1], [0, 1])
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
        try:
            plt.savefig(path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 500
        finally:
            os.unlink(path)


# ── Axes decoration methods ───────────────────────────────────────────────────

class TestAxesDecoration:
    def setup_method(self):
        fresh()

    def test_axhline_adds_line(self):
        plt.axhline(y=0.5, color='k')
        ax = plt.gca()
        assert len(ax.lines) == 1
        line = ax.lines[0]
        # y-data should be constant at 0.5
        assert all(v == pytest.approx(0.5) for v in line.ydata)

    def test_axvline_adds_line(self):
        plt.axvline(x=1.0, color='r')
        ax = plt.gca()
        assert len(ax.lines) == 1
        line = ax.lines[0]
        assert all(v == pytest.approx(1.0) for v in line.xdata)

    def test_fill_between_adds_polygon(self):
        x = np.linspace(0, 1, 10)
        plt.fill_between(x, x * 0.5, x, alpha=0.3)
        ax = plt.gca()
        assert len(ax.patches) > 0

    def test_hist_bins(self):
        data = np.random.randn(200)
        n, edges, patches = plt.hist(data, bins=15)
        assert len(n) == 15
        assert len(edges) == 16
        assert sum(n) == 200

    def test_bar_returns_patches(self):
        plt.bar([1, 2, 3], [4, 5, 6])
        ax = plt.gca()
        assert len(ax.patches) == 3

    def test_barh_returns_patches(self):
        plt.barh(['a', 'b'], [0.3, 0.7])
        ax = plt.gca()
        assert len(ax.patches) == 2

    def test_imshow_stored(self):
        data = np.random.rand(4, 4)
        plt.imshow(data, cmap='Blues')
        ax = plt.gca()
        assert len(ax.images) == 1
        assert ax.images[0].data.shape == (4, 4)

    def test_errorbar_stored(self):
        plt.errorbar([1, 2, 3], [1, 2, 3], yerr=[0.1, 0.2, 0.1])
        ax = plt.gca()
        assert len(ax.errorbars) == 1

    def test_boxplot_adds_patches(self):
        data = [np.random.randn(50), np.random.randn(50)]
        plt.boxplot(data)
        ax = plt.gca()
        # boxplot uses lines and patches
        assert len(ax.lines) > 0

    def test_violinplot_adds_patches(self):
        data = [np.random.randn(50), np.random.randn(50)]
        plt.violinplot(data, positions=[1, 2])
        ax = plt.gca()
        assert len(ax.patches) > 0

    def test_pie_adds_patches(self):
        plt.pie([30, 50, 20], labels=['A', 'B', 'C'])
        ax = plt.gca()
        assert len(ax.patches) == 3

    def test_stackplot_adds_polygons(self):
        x = np.arange(5)
        plt.stackplot(x, [1, 2, 3, 4, 5], [2, 1, 2, 1, 2])
        ax = plt.gca()
        assert len(ax.patches) == 2

    def test_plot_fmt_string(self):
        lines = plt.plot([0, 1, 2], [0, 1, 0], 'r--')
        line = lines[0]
        assert line.linestyle == '--'

    def test_plot_multiple_segments(self):
        x = [0, 1]
        lines = plt.plot(x, [0, 1], 'r-', x, [1, 0], 'b--')
        assert len(lines) == 2

    def test_suptitle(self):
        fig = plt.gcf()
        plt.suptitle('Overall')
        assert fig._suptitle == 'Overall'


# ── Rendering smoke test ──────────────────────────────────────────────────────

class TestRendering:
    def setup_method(self):
        fresh()

    def test_savefig_all_plot_types(self):
        """Render one figure with every artist type and write PNG without crashing."""
        import tempfile
        import pygame
        if not pygame.get_init():
            pygame.init()

        np.random.seed(42)
        fig, axs = plt.subplots(2, 3, figsize=(12, 8))

        # row 0
        x = np.linspace(0, 2 * np.pi, 50)
        axs[0, 0].plot(x, np.sin(x), 'b-', label='sin')
        axs[0, 0].plot(x, np.cos(x), 'r--', label='cos')
        axs[0, 0].set_title('Lines'); axs[0, 0].legend(); axs[0, 0].grid()

        X = np.random.randn(40, 2)
        axs[0, 1].scatter(X[:, 0], X[:, 1], c=X[:, 0], cmap='viridis', s=30)
        axs[0, 1].set_title('Scatter')

        axs[0, 2].hist(np.random.randn(200), bins=15, color='steelblue')
        axs[0, 2].set_title('Histogram')

        # row 1
        axs[1, 0].bar(['A', 'B', 'C'], [3, 7, 5])
        axs[1, 0].set_title('Bar')

        cm = np.array([[10, 2], [1, 8]])
        im = axs[1, 1].imshow(cm, cmap='Blues')
        axs[1, 1].set_title('Imshow')

        axs[1, 2].boxplot([np.random.randn(30), np.random.randn(30) + 1])
        axs[1, 2].set_title('Boxplot')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
        try:
            plt.savefig(path)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 1000
        finally:
            os.unlink(path)

    def test_render_fill_between_and_errorbar(self):
        import tempfile
        import pygame
        if not pygame.get_init():
            pygame.init()

        x = np.linspace(0, 10, 30)
        mean = np.sin(x)
        plt.plot(x, mean, 'b-')
        plt.fill_between(x, mean - 0.3, mean + 0.3, alpha=0.3)
        plt.errorbar(x[::5], mean[::5], yerr=0.2, fmt='o', capsize=4)
        plt.axhline(y=0, color='k', linewidth=0.5)
        plt.axvline(x=np.pi, color='r', linewidth=0.5)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
        try:
            plt.savefig(path)
            assert os.path.getsize(path) > 500
        finally:
            os.unlink(path)

    def test_render_log_scale(self):
        import tempfile
        import pygame
        if not pygame.get_init():
            pygame.init()

        x = np.logspace(0, 3, 30)
        plt.plot(x, x ** 2)
        plt.xscale('log')
        plt.yscale('log')

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
        try:
            plt.savefig(path)
            assert os.path.getsize(path) > 500
        finally:
            os.unlink(path)
