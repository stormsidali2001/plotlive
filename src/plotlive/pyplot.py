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
    global _current_figure, _current_axes
    fig = Figure(figsize=figsize, facecolor=facecolor)
    _figures.append(fig)
    _current_figure = fig
    _current_axes = None
    return fig


def gcf() -> Figure:
    global _current_figure
    if _current_figure is None:
        _current_figure = figure()
    return _current_figure


def gca(**kwargs):
    global _current_axes
    if _current_axes is None:
        fig = gcf()
        if fig.axes:
            _current_axes = fig.axes[-1]
        else:
            _current_axes = fig.add_subplot(1, 1, 1)
    return _current_axes


def sca(ax):
    global _current_axes, _current_figure
    _current_axes = ax
    _current_figure = ax._figure
    return ax


def subplots(nrows=1, ncols=1, squeeze=True, figsize=(6.4, 4.8),
             sharex=False, sharey=False, **kwargs):
    global _current_figure, _current_axes
    fig = Figure(figsize=figsize)
    _figures.append(fig)
    _current_figure = fig
    _, axs = fig.subplots(nrows, ncols, squeeze=squeeze)
    # Set current axes to the first one
    if isinstance(axs, np.ndarray):
        first = axs.flat[0]
    else:
        first = axs
    _current_axes = first
    return fig, axs


def subplot(nrows=1, ncols=1, index=1, **kwargs):
    global _current_axes
    fig = gcf()
    ax = fig.add_subplot(nrows, ncols, index, **kwargs)
    _current_axes = ax
    return ax


def clf() -> None:
    fig = gcf()
    fig.axes.clear()
    fig._suptitle = ''


def cla() -> None:
    gca().cla()


def close(fig=None) -> None:
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
    return gca().plot(*args, **kwargs)

def scatter(x, y, **kwargs):
    return gca().scatter(x, y, **kwargs)

def hist(x, **kwargs):
    return gca().hist(x, **kwargs)

def bar(x, height, **kwargs):
    return gca().bar(x, height, **kwargs)

def barh(y, width, **kwargs):
    return gca().barh(y, width, **kwargs)

def imshow(X, **kwargs):
    return gca().imshow(X, **kwargs)

def xlabel(s, **kwargs):
    gca().set_xlabel(s, **kwargs)

def ylabel(s, **kwargs):
    gca().set_ylabel(s, **kwargs)

def title(s, **kwargs):
    gca().set_title(s, **kwargs)

def legend(*args, **kwargs):
    return gca().legend(*args, **kwargs)

def grid(visible=True, **kwargs):
    gca().grid(visible, **kwargs)

def xlim(*args, **kwargs):
    if args:
        return gca().set_xlim(*args, **kwargs)
    return gca().get_xlim()

def ylim(*args, **kwargs):
    if args:
        return gca().set_ylim(*args, **kwargs)
    return gca().get_ylim()

def xscale(value, **kwargs):
    gca().set_xscale(value, **kwargs)

def yscale(value, **kwargs):
    gca().set_yscale(value, **kwargs)

def xticks(ticks=None, labels=None, **kwargs):
    if ticks is None:
        return gca().get_xticks()
    gca().set_xticks(ticks, labels, **kwargs)

def yticks(ticks=None, labels=None, **kwargs):
    if ticks is None:
        return gca().get_yticks()
    gca().set_yticks(ticks, labels, **kwargs)

def tight_layout(**kwargs):
    gcf().tight_layout(**kwargs)

def suptitle(t, **kwargs):
    gcf().suptitle(t, **kwargs)

def colorbar(mappable=None, ax=None, **kwargs):
    """Associate a colorbar with the current (or specified) axes image."""
    target_ax = ax or gca()
    if mappable is not None and hasattr(mappable, 'cmap_name'):
        target_ax._colorbar_image = mappable
    elif target_ax.images:
        target_ax._colorbar_image = target_ax.images[-1]

def axhline(y=0, xmin=0, xmax=1, **kwargs):
    ax = gca()
    xlim = ax.get_xlim()
    x0 = xlim[0] + xmin * (xlim[1] - xlim[0])
    x1 = xlim[0] + xmax * (xlim[1] - xlim[0])
    return ax.plot([x0, x1], [y, y], **kwargs)

def axvline(x=0, ymin=0, ymax=1, **kwargs):
    ax = gca()
    ylim = ax.get_ylim()
    y0 = ylim[0] + ymin * (ylim[1] - ylim[0])
    y1 = ylim[0] + ymax * (ylim[1] - ylim[0])
    return ax.plot([x, x], [y0, y1], **kwargs)

def savefig(fname: str, **kwargs):
    gcf().savefig(fname, **kwargs)

def fill_between(x, y1, y2=0, **kwargs):
    return gca().fill_between(x, y1, y2, **kwargs)

def errorbar(x, y, **kwargs):
    return gca().errorbar(x, y, **kwargs)

def boxplot(data, **kwargs):
    return gca().boxplot(data, **kwargs)

def violinplot(data, **kwargs):
    return gca().violinplot(data, **kwargs)

def pie(x, **kwargs):
    return gca().pie(x, **kwargs)

def stackplot(x, *ys, **kwargs):
    return gca().stackplot(x, *ys, **kwargs)

# ------------------------------------------------------------------
# Animation
# ------------------------------------------------------------------

def save_animation(filename: str, fps: int | None = None,
                   fig: Figure | None = None) -> None:
    """Export the current figure's animation to a GIF or video file."""
    f = fig if fig is not None else gcf()
    if f._animation is None:
        raise RuntimeError(
            'No animation on the current figure. Call plt.animate() first.'
        )
    f._animation.save(filename, fps=fps)


def animate(update_fn, frames=None, interval: int = 200,
            repeat: bool = True, fig: Figure | None = None,
            fargs=None, save_count: int | None = None) -> FuncAnimation:
    """
    Convenience wrapper — create and register an animation on the current figure.

    For full matplotlib compatibility, construct FuncAnimation directly::

        from plotlive.animation import FuncAnimation
        anim = FuncAnimation(fig, update, frames=50, interval=200)
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
