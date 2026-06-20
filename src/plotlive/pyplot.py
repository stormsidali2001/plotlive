"""
plotlive.pyplot — drop-in state machine API for matplotlib.pyplot.
"""
from __future__ import annotations
import numpy as np
from .figure import Figure
from .animation import FuncAnimation
from .events import InteractionState, draw_help_overlay
from .renderer import FigureRenderer, AxesRenderer

# ------------------------------------------------------------------
# Global state (mirrors matplotlib._pylab_helpers)
# ------------------------------------------------------------------
_figures: list[Figure] = []
_current_figure: Figure | None = None
_current_axes = None  # Axes | None


# ------------------------------------------------------------------
# Figure / Axes management
# ------------------------------------------------------------------

def figure(num=None, figsize=(6.4, 4.8), dpi=100, facecolor='white',
           edgecolor='white', **kwargs) -> Figure:
    """Create a new figure and make it current.

    Args:
        figsize: Width and height in inches. Default is ``(6.4, 4.8)``.
        facecolor: Background colour. Default is ``'white'``.

    Returns:
        The new `Figure` instance.
    """
    global _current_figure, _current_axes
    fig = Figure(figsize=figsize, facecolor=facecolor)
    _figures.append(fig)
    _current_figure = fig
    _current_axes = None
    return fig


def gcf() -> Figure:
    """Return the current figure, creating one if none exists."""
    global _current_figure
    if _current_figure is None:
        _current_figure = figure()
    return _current_figure


def gca(**kwargs):
    """Return the current axes, creating one if none exists."""
    global _current_axes
    if _current_axes is None:
        fig = gcf()
        if fig.axes:
            _current_axes = fig.axes[-1]
        else:
            _current_axes = fig.add_subplot(1, 1, 1)
    return _current_axes


def sca(ax):
    """Set *ax* as the current axes and return it."""
    global _current_axes, _current_figure
    _current_axes = ax
    _current_figure = ax._figure
    return ax


def subplots(nrows=1, ncols=1, squeeze=True, figsize=(6.4, 4.8),
             sharex=False, sharey=False, **kwargs):
    """Create a figure with a grid of subplots.

    Args:
        nrows: Number of rows. Default is ``1``.
        ncols: Number of columns. Default is ``1``.
        squeeze: If ``True``, a single subplot is returned as a bare ``Axes``
            rather than a 1-element array. Default is ``True``.
        figsize: Width and height in inches.

    Returns:
        Tuple of ``(Figure, axes)`` where *axes* is a bare ``Axes`` for
        a 1×1 grid, a 1-D ndarray for a single row/column, or a 2-D ndarray
        otherwise — matching matplotlib's squeeze behaviour.

    Example:
        ```python
        fig, axs = plt.subplots(2, 3, figsize=(12, 6))
        axs[0, 0].plot(x, y)
        ```
    """
    global _current_figure, _current_axes
    fig = Figure(figsize=figsize)
    _figures.append(fig)
    _current_figure = fig
    _, axs = fig.subplots(nrows, ncols, squeeze=squeeze)
    if isinstance(axs, np.ndarray):
        first = axs.flat[0]
    else:
        first = axs
    _current_axes = first
    return fig, axs


def subplot(nrows=1, ncols=1, index=1, **kwargs):
    """Add a subplot to the current figure and make it current."""
    global _current_axes
    fig = gcf()
    ax = fig.add_subplot(nrows, ncols, index, **kwargs)
    _current_axes = ax
    return ax


def clf() -> None:
    """Clear the current figure — removes all axes and the suptitle."""
    fig = gcf()
    fig.axes.clear()
    fig._suptitle = ''


def cla() -> None:
    """Clear the current axes — removes all artists and resets axis state."""
    gca().cla()


def close(fig=None) -> None:
    """Remove *fig* (or the current figure) from the figure list.

    Args:
        fig: Figure to close. Defaults to the current figure.
    """
    global _figures, _current_figure, _current_axes
    if fig is None:
        fig = _current_figure
    if fig in _figures:
        _figures.remove(fig)
    if _current_figure is fig:
        _current_figure = _figures[-1] if _figures else None
        _current_axes = None


# ------------------------------------------------------------------
# Delegation to current axes
# ------------------------------------------------------------------

def plot(*args, **kwargs):
    """Plot lines and/or markers on the current axes.

    Accepts the same arguments as ``matplotlib.pyplot.plot``, including
    format strings (``'r--'``, ``'bo-'``) and keyword arguments
    (``color``, ``linewidth``, ``label``, …).

    Returns:
        List of `Line2D` artists.

    Example:
        ```python
        plt.plot(x, y, 'b--', label='train', linewidth=2)
        ```
    """
    return gca().plot(*args, **kwargs)

def scatter(x, y, **kwargs):
    """Plot a scatter of points on the current axes.

    Args:
        x: X coordinates.
        y: Y coordinates.
        c: Colour(s) or array of values mapped through *cmap*.
        s: Marker size(s) in points².
        cmap: Colormap name. Default is ``'viridis'``.
        alpha: Opacity, 0–1.

    Returns:
        `PathCollection` artist.
    """
    return gca().scatter(x, y, **kwargs)

def hist(x, **kwargs):
    """Plot a histogram on the current axes.

    Args:
        x: Data array.
        bins: Number of bins or bin edges. Default is ``10``.
        color: Bar fill colour.
        edgecolor: Bar edge colour.

    Returns:
        Tuple of ``(counts, bin_edges, patches)``.
    """
    return gca().hist(x, **kwargs)

def bar(x, height, **kwargs):
    """Plot vertical bars on the current axes.

    Args:
        x: Bar positions.
        height: Bar heights.

    Returns:
        `BarContainer` (list of `Rectangle` patches).
    """
    return gca().bar(x, height, **kwargs)

def barh(y, width, **kwargs):
    """Plot horizontal bars on the current axes.

    Args:
        y: Bar positions.
        width: Bar widths.

    Returns:
        `BarContainer` (list of `Rectangle` patches).
    """
    return gca().barh(y, width, **kwargs)

def imshow(X, **kwargs):
    """Display an image or 2-D array on the current axes.

    Args:
        X: 2-D array ``(H, W)`` or RGB array ``(H, W, 3)``.
        cmap: Colormap name for scalar arrays. Default is ``'viridis'``.
        vmin: Lower clamp value for colormap scaling.
        vmax: Upper clamp value for colormap scaling.
        origin: ``'upper'`` puts row 0 at the top (default, suits confusion
            matrices). ``'lower'`` puts row 0 at the bottom.

    Returns:
        `AxesImage` artist.
    """
    return gca().imshow(X, **kwargs)

def xlabel(s, **kwargs):
    """Set the x-axis label on the current axes."""
    gca().set_xlabel(s, **kwargs)

def ylabel(s, **kwargs):
    """Set the y-axis label on the current axes."""
    gca().set_ylabel(s, **kwargs)

def title(s, **kwargs):
    """Set the title on the current axes."""
    gca().set_title(s, **kwargs)

def legend(*args, **kwargs):
    """Add a legend to the current axes using labelled artists."""
    return gca().legend(*args, **kwargs)

def grid(visible=True, **kwargs):
    """Show or hide the grid on the current axes.

    Args:
        visible: ``True`` to show, ``False`` to hide. Default is ``True``.
    """
    gca().grid(visible, **kwargs)

def xlim(*args, **kwargs):
    """Get or set the x-axis limits of the current axes.

    Call with no arguments to get the current limits, or pass
    ``(left, right)`` to set them.

    Returns:
        ``(left, right)`` when called with no arguments.
    """
    if args:
        return gca().set_xlim(*args, **kwargs)
    return gca().get_xlim()

def ylim(*args, **kwargs):
    """Get or set the y-axis limits of the current axes.

    Call with no arguments to get the current limits, or pass
    ``(bottom, top)`` to set them.

    Returns:
        ``(bottom, top)`` when called with no arguments.
    """
    if args:
        return gca().set_ylim(*args, **kwargs)
    return gca().get_ylim()

def xscale(value, **kwargs):
    """Set the x-axis scale. Use ``'log'`` for logarithmic scale."""
    gca().set_xscale(value, **kwargs)

def yscale(value, **kwargs):
    """Set the y-axis scale. Use ``'log'`` for logarithmic scale."""
    gca().set_yscale(value, **kwargs)

def xticks(ticks=None, labels=None, **kwargs):
    """Get or set x-axis tick positions and labels.

    Args:
        ticks: Tick positions. If ``None``, returns current ticks.
        labels: Tick labels. Defaults to string representation of *ticks*.
    """
    if ticks is None:
        return gca().get_xticks()
    gca().set_xticks(ticks, labels, **kwargs)

def yticks(ticks=None, labels=None, **kwargs):
    """Get or set y-axis tick positions and labels.

    Args:
        ticks: Tick positions. If ``None``, returns current ticks.
        labels: Tick labels. Defaults to string representation of *ticks*.
    """
    if ticks is None:
        return gca().get_yticks()
    gca().set_yticks(ticks, labels, **kwargs)

def tight_layout(**kwargs):
    """Adjust subplot spacing to prevent label overlap."""
    gcf().tight_layout(**kwargs)

def suptitle(t, **kwargs):
    """Set a centred title for the whole figure (above all subplots)."""
    gcf().suptitle(t, **kwargs)

def colorbar(mappable=None, ax=None, **kwargs):
    """Draw a colour scale bar next to an image plot.

    Args:
        mappable: The `AxesImage` to attach the colourbar to. Defaults to
            the most recent image on the target axes.
        ax: Target axes. Defaults to the current axes.
    """
    target_ax = ax or gca()
    if mappable is not None and hasattr(mappable, 'cmap_name'):
        target_ax._colorbar_image = mappable
    elif target_ax.images:
        target_ax._colorbar_image = target_ax.images[-1]

def axhline(y=0, xmin=0, xmax=1, **kwargs):
    """Draw a horizontal line across the current axes at *y*.

    Args:
        y: Data-space y position. Default is ``0``.
        xmin: Left extent in axes fraction (0–1). Default is ``0``.
        xmax: Right extent in axes fraction (0–1). Default is ``1``.
    """
    ax = gca()
    xlim = ax.get_xlim()
    x0 = xlim[0] + xmin * (xlim[1] - xlim[0])
    x1 = xlim[0] + xmax * (xlim[1] - xlim[0])
    return ax.plot([x0, x1], [y, y], **kwargs)

def axvline(x=0, ymin=0, ymax=1, **kwargs):
    """Draw a vertical line across the current axes at *x*.

    Args:
        x: Data-space x position. Default is ``0``.
        ymin: Bottom extent in axes fraction (0–1). Default is ``0``.
        ymax: Top extent in axes fraction (0–1). Default is ``1``.
    """
    ax = gca()
    ylim = ax.get_ylim()
    y0 = ylim[0] + ymin * (ylim[1] - ylim[0])
    y1 = ylim[0] + ymax * (ylim[1] - ylim[0])
    return ax.plot([x, x], [y0, y1], **kwargs)

def savefig(fname: str, **kwargs):
    """Save the current figure to *fname* (PNG, based on extension).

    Args:
        fname: Output file path, e.g. ``'output.png'``.
    """
    gcf().savefig(fname, **kwargs)

def fill_between(x, y1, y2=0, **kwargs):
    """Fill the area between two horizontal curves.

    Args:
        x: X coordinates.
        y1: Upper (or first) curve values.
        y2: Lower (or second) curve values. Default is ``0``.
        alpha: Opacity. Default is ``1.0``.
    """
    return gca().fill_between(x, y1, y2, **kwargs)

def errorbar(x, y, **kwargs):
    """Plot points with error bars.

    Args:
        x: X positions.
        y: Y positions.
        yerr: Y error values (symmetric scalar, array, or ``(lower, upper)``).
        xerr: X error values.
        fmt: Format string for the data points. Default is ``''``.
        capsize: Length of error bar caps in points.
    """
    return gca().errorbar(x, y, **kwargs)

def boxplot(data, **kwargs):
    """Draw a box-and-whisker plot for one or more datasets.

    Args:
        data: Array or list of arrays. Each array is one box.
        labels: Tick labels for each box.
    """
    return gca().boxplot(data, **kwargs)

def violinplot(data, **kwargs):
    """Draw a violin plot for one or more datasets.

    Args:
        data: Array or list of arrays.
        positions: X positions for each violin. Default is ``[1, 2, …]``.
        widths: Width of each violin. Default is ``0.5``.
    """
    return gca().violinplot(data, **kwargs)

def pie(x, **kwargs):
    """Draw a pie chart.

    Args:
        x: Wedge sizes (need not sum to 1; normalised automatically).
        labels: Sequence of wedge labels.
        startangle: Starting angle in degrees, counter-clockwise from x-axis.
    """
    return gca().pie(x, **kwargs)

def stackplot(x, *ys, **kwargs):
    """Draw a stacked area chart.

    Args:
        x: X coordinates shared by all series.
        *ys: One array per series.
        labels: Legend labels for each series.
        alpha: Opacity. Default is ``1.0``.
    """
    return gca().stackplot(x, *ys, **kwargs)

# ------------------------------------------------------------------
# Animation
# ------------------------------------------------------------------

def save_animation(filename: str, fps: int | None = None,
                   fig: Figure | None = None) -> None:
    """Export the current figure's animation to a file.

    Renders all frames off-screen — no window opens. Resets to frame 0
    afterwards so a subsequent `show()` starts from the beginning.

    Args:
        filename: Output path. Extension determines format:
            ``.gif`` (requires Pillow), ``.mp4`` / ``.mov`` / ``.avi``
            (requires imageio + ffmpeg).
        fps: Frames per second. Defaults to ``1000 / interval``.
        fig: Figure to export. Defaults to the current figure.

    Raises:
        RuntimeError: If no animation has been registered on the figure.

    Example:
        ```python
        plt.animate(update, frames=60, interval=100)
        plt.save_animation('output.gif')
        plt.show()  # opens interactive window at frame 0
        ```
    """
    f = fig if fig is not None else gcf()
    if f._animation is None:
        raise RuntimeError(
            'No animation on the current figure. Call plt.animate() first.'
        )
    f._animation.save(filename, fps=fps)


def animate(update_fn, frames=None, interval: int = 200,
            repeat: bool = True, fig: Figure | None = None,
            fargs=None, save_count: int | None = None) -> FuncAnimation:
    """Create and register an animation on the current figure.

    Shorthand for constructing a `~plotlive.animation.FuncAnimation` and
    attaching it to the figure. For the full parameter set, construct
    `~plotlive.animation.FuncAnimation` directly.

    Args:
        update_fn: Called as ``update_fn(frame)`` each step.
        frames: Number of frames (int), explicit frame values (list), a
            generator, or ``None`` (defaults to 100).
        interval: Milliseconds between frames. Default is ``200``.
        repeat: Loop when finished. Default is ``True``.
        fig: Figure to attach to. Defaults to the current figure.
        fargs: Extra positional arguments forwarded to *update_fn*.
        save_count: Frame count when *frames* is ``None`` or a generator.

    Returns:
        The registered `~plotlive.animation.FuncAnimation` instance.

    Example:
        ```python
        def update(frame):
            plt.cla()
            plt.plot(x[:frame], y[:frame])

        plt.animate(update, frames=100, interval=50)
        plt.show()
        ```
    """
    if fig is None:
        fig = gcf()
    anim = FuncAnimation(fig, update_fn, frames=frames, interval=interval,
                         repeat=repeat, fargs=fargs, save_count=save_count)
    fig._animation = anim
    return anim

# ------------------------------------------------------------------
# Main event loop
# ------------------------------------------------------------------

def show(block: bool = True) -> None:
    """Open pygame window (non-Jupyter) or display inline (Jupyter notebook)."""
    global _current_figure, _current_axes
    import pygame

    if not _figures:
        return

    # ----- Jupyter / IPython inline display -----
    from . import _jupyter
    if _jupyter.is_jupyter():
        if not pygame.get_init():
            pygame.init()

        def _set_current(fig):
            global _current_figure, _current_axes
            _current_figure = fig
            _current_axes = fig.axes[0] if fig.axes else None

        for fig in list(_figures):
            if fig._animation is not None:
                _jupyter.show_animation(fig, _set_current)
            else:
                _jupyter.show_figure(fig)
        _figures.clear()
        _current_figure = None
        _current_axes = None
        return

    fig = _current_figure or _figures[0]

    if not pygame.get_init():
        pygame.init()

    screen = pygame.display.set_mode(fig.pixel_size, pygame.RESIZABLE)
    pygame.display.set_caption('plotlive')
    clock = pygame.time.Clock()
    state = InteractionState(fig)

    # Animation starts PAUSED — user presses Space to begin
    anim_event_id = fig._animation.event_id if fig._animation else None

    dirty = True
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif anim_event_id and event.type == anim_event_id:
                if fig._animation:
                    dirty |= fig._animation._on_timer()
            else:
                dirty |= state.handle_event(event, screen=screen)

        if dirty:
            fig_surface = FigureRenderer(fig).render()
            screen.blit(fig_surface, (0, 0))

            # Hover tooltip overlay
            hits = state.get_hover_hits()
            if hits:
                r = AxesRenderer(fig.axes[0], 0, 0)
                r._draw_tooltip(screen, hits, pygame.mouse.get_pos())

            # Help panel overlay
            if state.show_help:
                draw_help_overlay(screen)

            pygame.display.flip()
            dirty = False

        clock.tick(60)

    if fig._animation:
        fig._animation.pause()
    pygame.quit()

    # Reset state so the library can be used again
    _figures.clear()
    _current_figure = None
    _current_axes = None
