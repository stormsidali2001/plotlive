import numpy as np
import pytest
from plotlive.figure import Figure


def make_fig_ax():
    fig = Figure(figsize=(6.4, 4.8))
    ax = fig.add_subplot(1, 1, 1)
    return fig, ax


def test_plot_returns_list():
    _, ax = make_fig_ax()
    result = ax.plot([1, 2, 3], [4, 5, 6])
    assert isinstance(result, list)
    assert len(result) == 1
    # Idiomatic tuple unpack
    (line,) = ax.plot([0, 1], [0, 1])
    assert line.xdata.tolist() == [0, 1]


def test_hist_returns_tuple():
    _, ax = make_fig_ax()
    data = np.random.randn(100)
    n, edges, patches = ax.hist(data, bins=10)
    assert len(n) == 10
    assert len(edges) == 11
    assert len(patches) == 10
    # Bar patches are added to ax.patches
    assert len(ax.patches) == 10


def test_bar_categorical():
    _, ax = make_fig_ax()
    ax.bar(['a', 'b', 'c'], [1, 2, 3])
    assert ax._xtick_labels == ['a', 'b', 'c']
    assert len(ax.patches) == 3


def test_barh():
    _, ax = make_fig_ax()
    ax.barh(['x', 'y'], [0.4, 0.6])
    assert len(ax.patches) == 2


def test_scatter():
    _, ax = make_fig_ax()
    col = ax.scatter([1, 2, 3], [4, 5, 6], c='red')
    assert col.xdata.tolist() == [1, 2, 3]
    colors = col.resolve_colors()
    assert colors.shape == (3, 4)


def test_imshow():
    _, ax = make_fig_ax()
    data = np.random.rand(5, 5)
    img = ax.imshow(data, cmap='viridis')
    assert img.data.shape == (5, 5)
    assert img.cmap_name == 'viridis'


def test_cla():
    _, ax = make_fig_ax()
    ax.plot([1], [1])
    ax.scatter([1], [1])
    ax.cla()
    assert len(ax.lines) == 0
    assert len(ax.collections) == 0


def test_set_xlim_disables_auto():
    _, ax = make_fig_ax()
    ax.set_xlim(0, 100)
    assert not ax._xlim_auto
    assert ax.get_xlim() == (0.0, 100.0)


def test_subplots_squeeze():
    fig = Figure()
    _, ax = fig.subplots(1, 1, squeeze=True)
    # Should return a single Axes, not an array
    from plotlive.axes import Axes
    assert isinstance(ax, Axes)


def test_subplots_array():
    fig = Figure()
    _, axs = fig.subplots(2, 3, squeeze=False)
    assert axs.shape == (2, 3)


def test_color_cycle():
    _, ax = make_fig_ax()
    lines = [ax.plot([i], [i])[0] for i in range(10)]
    colors = [l.color for l in lines]
    # Colors should cycle (all different within 10)
    assert len(set(colors)) == 10


def test_auto_scale_runs_at_render_time():
    _, ax = make_fig_ax()
    ax.plot([0, 1, 2], [0, 1, 4])
    # xlim_auto is still True after plot
    assert ax._xlim_auto
    # Manually set limit after plotting
    ax.set_xlim(-1, 5)
    assert not ax._xlim_auto
    assert ax.get_xlim() == (-1.0, 5.0)
