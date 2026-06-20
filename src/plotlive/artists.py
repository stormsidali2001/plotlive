from __future__ import annotations
import numpy as np
from .colors import to_rgba, get_cmap, DEFAULT_CYCLE


class Artist:
    def __init__(self):
        self.label: str = '_nolegend_'
        self.visible: bool = True
        self.alpha: float = 1.0
        self.zorder: float = 1.0

    def get_xdata(self) -> np.ndarray | None:
        return None

    def get_ydata(self) -> np.ndarray | None:
        return None

    def get_label(self) -> str:
        return self.label


class Line2D(Artist):
    def __init__(self, xdata: np.ndarray, ydata: np.ndarray, **kwargs):
        super().__init__()
        self.xdata = np.asarray(xdata, dtype=float)
        self.ydata = np.asarray(ydata, dtype=float)
        color = kwargs.get('color', kwargs.get('c', 'C0'))
        self.color: tuple = to_rgba(color)
        self.linewidth: float = float(kwargs.get('linewidth', kwargs.get('lw', 1.5)))
        self.linestyle: str = kwargs.get('linestyle', kwargs.get('ls', '-'))
        self.marker: str | None = kwargs.get('marker', None)
        self.markersize: float = float(kwargs.get('markersize', kwargs.get('ms', 6.0)))
        self.markerfacecolor = kwargs.get('markerfacecolor', None)
        self.label = kwargs.get('label', '_nolegend_')
        self.alpha = float(kwargs.get('alpha', 1.0))

    def get_xdata(self) -> np.ndarray:
        return self.xdata

    def get_ydata(self) -> np.ndarray:
        return self.ydata

    def set_xdata(self, x) -> None:
        self.xdata = np.asarray(x, dtype=float)

    def set_ydata(self, y) -> None:
        self.ydata = np.asarray(y, dtype=float)


class PathCollection(Artist):
    """Stores data for a scatter plot."""

    def __init__(self, xdata: np.ndarray, ydata: np.ndarray, **kwargs):
        super().__init__()
        self.xdata = np.asarray(xdata, dtype=float).ravel()
        self.ydata = np.asarray(ydata, dtype=float).ravel()
        s = kwargs.get('s', 20.0)
        self.sizes = np.broadcast_to(
            np.atleast_1d(np.asarray(s, dtype=float)), self.xdata.shape
        ).copy()
        self._c_raw = kwargs.get('c', kwargs.get('color', 'C0'))
        self.cmap_name: str = kwargs.get('cmap', 'viridis')
        self.vmin: float | None = kwargs.get('vmin', None)
        self.vmax: float | None = kwargs.get('vmax', None)
        self.marker: str = kwargs.get('marker', 'o')
        self.linewidths: float = float(kwargs.get('linewidths', 0.0))
        self.edgecolors = kwargs.get('edgecolors', 'none')
        self.label = kwargs.get('label', '_nolegend_')
        self.alpha = float(kwargs.get('alpha', 1.0))
        self._colors_resolved: np.ndarray | None = None

    def get_xdata(self) -> np.ndarray:
        return self.xdata

    def get_ydata(self) -> np.ndarray:
        return self.ydata

    def resolve_colors(self) -> np.ndarray:
        """Return (N, 4) uint8 RGBA array."""
        if self._colors_resolved is not None:
            return self._colors_resolved

        c = self._c_raw
        n = len(self.xdata)
        result = np.zeros((n, 4), dtype=np.uint8)

        # Try to interpret c as an array of floats (for cmap mapping)
        try:
            c_arr = np.asarray(c, dtype=float)
            if c_arr.ndim == 1 and c_arr.shape[0] == n and n > 1:
                # It's a per-point scalar for colormap
                vmin = self.vmin if self.vmin is not None else float(c_arr.min())
                vmax = self.vmax if self.vmax is not None else float(c_arr.max())
                cmap = get_cmap(self.cmap_name)
                span = vmax - vmin if vmax != vmin else 1.0
                t = (c_arr - vmin) / span
                rgba = cmap(t)
                result[:] = rgba[:, :4]
                self._colors_resolved = result
                return result
        except (TypeError, ValueError):
            pass

        # Single color broadcast
        try:
            rgba = to_rgba(c, self.alpha)
        except Exception:
            rgba = to_rgba(DEFAULT_CYCLE[0], self.alpha)
        result[:] = rgba
        self._colors_resolved = result
        return result


class Rectangle(Artist):
    def __init__(self, x: float, y: float, width: float, height: float, **kwargs):
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        color = kwargs.get('color', kwargs.get('facecolor', 'C0'))
        self.facecolor: tuple = to_rgba(color, float(kwargs.get('alpha', 1.0)))
        ec = kwargs.get('edgecolor', kwargs.get('ec', 'black'))
        self.edgecolor: tuple = to_rgba(ec) if ec not in ('none', 'None', None) else (0, 0, 0, 0)
        self.linewidth: float = float(kwargs.get('linewidth', kwargs.get('lw', 1.0)))
        self.label = kwargs.get('label', '_nolegend_')
        self.alpha = float(kwargs.get('alpha', 1.0))
        self._horizontal: bool = kwargs.get('_horizontal', False)


class BarContainer:
    def __init__(self, patches: list[Rectangle], label: str = ''):
        self.patches = patches
        self.label = label

    def __iter__(self):
        return iter(self.patches)

    def __len__(self):
        return len(self.patches)

    def __getitem__(self, idx):
        return self.patches[idx]


class Polygon(Artist):
    """Filled polygon — used by fill_between, violinplot, pie, stackplot."""

    def __init__(self, xy: np.ndarray, **kwargs):
        super().__init__()
        self.xy = np.asarray(xy, dtype=float)   # (N, 2): columns [x, y]
        color = kwargs.get('color', kwargs.get('facecolor', 'C0'))
        alpha = float(kwargs.get('alpha', 0.5))
        self.facecolor: tuple = to_rgba(color, alpha)
        ec = kwargs.get('edgecolor', kwargs.get('ec', 'none'))
        self.edgecolor: tuple = (to_rgba(ec)
                                 if ec not in ('none', 'None', None)
                                 else (0, 0, 0, 0))
        self.linewidth: float = float(kwargs.get('linewidth', kwargs.get('lw', 1.0)))
        self.label = kwargs.get('label', '_nolegend_')
        self.alpha = alpha


class ErrorBar(Artist):
    """Central line + whiskers — used by errorbar()."""

    def __init__(self, x, y, yerr=None, xerr=None, **kwargs):
        super().__init__()
        self.xdata = np.asarray(x, dtype=float).ravel()
        self.ydata = np.asarray(y, dtype=float).ravel()
        n = len(self.xdata)

        def _norm(err):
            if err is None:
                return None
            e = np.asarray(err, float)
            if e.ndim <= 1:
                e = np.stack([e * np.ones(n), e * np.ones(n)])
            return np.broadcast_to(e, (2, n)).copy()

        self.yerr = _norm(yerr)
        self.xerr = _norm(xerr)
        color = kwargs.get('color', kwargs.get('c', 'C0'))
        self.color: tuple = to_rgba(color)
        self.linewidth: float = float(kwargs.get('linewidth', kwargs.get('lw', 1.5)))
        self.capsize: float = float(kwargs.get('capsize', 4))
        self.marker: str = kwargs.get('marker', 'o')
        self.markersize: float = float(kwargs.get('markersize', kwargs.get('ms', 5.0)))
        self.linestyle: str = kwargs.get('linestyle', kwargs.get('ls', '-'))
        self.label = kwargs.get('label', '_nolegend_')
        self.alpha: float = float(kwargs.get('alpha', 1.0))


class AxesImage(Artist):
    def __init__(self, data: np.ndarray, **kwargs):
        super().__init__()
        self.data = np.asarray(data)
        self.cmap_name: str = kwargs.get('cmap', 'viridis')
        self.vmin: float | None = kwargs.get('vmin', None)
        self.vmax: float | None = kwargs.get('vmax', None)
        self.origin: str = kwargs.get('origin', 'upper')
        self.aspect: str = kwargs.get('aspect', 'equal')
        self.extent: tuple | None = kwargs.get('extent', None)
        self.label = kwargs.get('label', '_nolegend_')
        self._surface_cache = None
        self._cache_key = None
