from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
from .axes import Axes

if TYPE_CHECKING:
    from .animation import FuncAnimation

_DPI = 100
_DEFAULT_LEFT   = 0.125
_DEFAULT_RIGHT  = 0.900
_DEFAULT_BOTTOM = 0.110
_DEFAULT_TOP    = 0.880
_DEFAULT_WSPACE = 0.200
_DEFAULT_HSPACE = 0.200


class Figure:
    """Top-level container. Owns all Axes and the pygame surface."""

    def __init__(self, figsize: tuple[float, float] = (6.4, 4.8),
                 facecolor='white', **kwargs):
        self.figsize = figsize
        self.pixel_size = (int(figsize[0] * _DPI), int(figsize[1] * _DPI))
        self.facecolor = facecolor
        self.axes: list[Axes] = []
        self._suptitle: str = ''
        self._animation: FuncAnimation | None = None
        self._focused_ax = None   # Axes | None — which subplot is in focus mode
        self._dirty: bool = True

    def add_axes(self, rect: tuple[float, float, float, float], **kwargs) -> Axes:
        """Add axes at rect=(left, bottom, width, height) in normalized [0,1] coords."""
        ax = Axes(self, rect_norm=rect)
        self.axes.append(ax)
        return ax

    def add_subplot(self, nrows: int, ncols: int, index: int, **kwargs) -> Axes:
        """Add subplot at 1-based index in nrows×ncols grid."""
        rect = self._compute_subplot_rect(nrows, ncols, index)
        ax = Axes(self, rect_norm=rect)
        self.axes.append(ax)
        return ax

    def _compute_subplot_rect(
        self, nrows: int, ncols: int, index: int,
        wspace: float = _DEFAULT_WSPACE,
        hspace: float = _DEFAULT_HSPACE,
    ) -> tuple[float, float, float, float]:
        row = (index - 1) // ncols
        col = (index - 1) % ncols
        total_w = _DEFAULT_RIGHT - _DEFAULT_LEFT
        total_h = _DEFAULT_TOP - _DEFAULT_BOTTOM
        # wspace/hspace are fractions of subplot size (matplotlib convention)
        subplot_w = total_w / (ncols + (ncols - 1) * wspace)
        subplot_h = total_h / (nrows + (nrows - 1) * hspace)
        left   = _DEFAULT_LEFT + col * subplot_w * (1 + wspace)
        bottom = _DEFAULT_BOTTOM + (nrows - 1 - row) * subplot_h * (1 + hspace)
        return (left, bottom, subplot_w, subplot_h)

    def subplots(
        self, nrows: int = 1, ncols: int = 1, squeeze: bool = True, **kwargs
    ) -> tuple['Figure', np.ndarray | Axes]:
        axs = np.empty((nrows, ncols), dtype=object)
        for r in range(nrows):
            for c in range(ncols):
                idx = r * ncols + c + 1
                axs[r, c] = self.add_subplot(nrows, ncols, idx, **kwargs)
        if squeeze:
            axs = axs.squeeze()
            if axs.ndim == 0:
                return self, axs.item()
        return self, axs

    def set_size_inches(self, w: float, h: float) -> None:
        self.figsize = (w, h)
        self.pixel_size = (int(w * _DPI), int(h * _DPI))

    def suptitle(self, t: str, **kwargs) -> None:
        self._suptitle = t

    def tight_layout(self, **kwargs) -> None:
        pass  # MVP: no-op; generous default margins handle most cases

    def savefig(self, fname: str, dpi: int = 100, **kwargs) -> None:
        import pygame
        if not pygame.get_init():
            pygame.init()
        surface = self._render_to_surface()
        pygame.image.save(surface, fname)

    def _render_to_surface(self):
        from .renderer import FigureRenderer
        return FigureRenderer(self).render()
