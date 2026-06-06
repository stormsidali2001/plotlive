from __future__ import annotations
import numpy as np

_EPS = 1e-300  # floor for log scale to avoid log(0)


def _log(v):
    return np.log10(np.maximum(np.asarray(v, float), _EPS))


class Transform:
    """
    Bidirectional mapping between data coordinates and screen pixel coordinates.
    Single source of truth for zoom/pan state per Axes.
    Supports 'linear' and 'log' scales independently on each axis.
    """

    def __init__(self):
        self.xlim: tuple[float, float] = (0.0, 1.0)
        self.ylim: tuple[float, float] = (0.0, 1.0)
        # (left, top, width, height) in screen pixels — set by renderer before each draw
        self.axes_rect: tuple[int, int, int, int] = (0, 0, 100, 100)
        self._home_xlim: tuple[float, float] = (0.0, 1.0)
        self._home_ylim: tuple[float, float] = (0.0, 1.0)
        self.xscale: str = 'linear'
        self.yscale: str = 'linear'

    # ------------------------------------------------------------------
    # Internal: normalised position [0, 1] along each axis
    # ------------------------------------------------------------------

    def _x_norm(self, x) -> np.ndarray:
        x = np.asarray(x, float)
        xmin, xmax = self.xlim
        if self.xscale == 'log':
            lx = _log(x); lmin = _log(xmin); lmax = _log(xmax)
            span = lmax - lmin if lmax != lmin else 1.0
            return (lx - lmin) / span
        span = xmax - xmin if xmax != xmin else 1.0
        return (x - xmin) / span

    def _y_norm(self, y) -> np.ndarray:
        y = np.asarray(y, float)
        ymin, ymax = self.ylim
        if self.yscale == 'log':
            ly = _log(y); lmin = _log(ymin); lmax = _log(ymax)
            span = lmax - lmin if lmax != lmin else 1.0
            return (ly - lmin) / span
        span = ymax - ymin if ymax != ymin else 1.0
        return (y - ymin) / span

    # ------------------------------------------------------------------
    # Forward transform: data → screen
    # ------------------------------------------------------------------

    def data_to_screen(
        self, x: float | np.ndarray, y: float | np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Convert data (x, y) to screen (sx, sy). Y is flipped."""
        left, top, w, h = self.axes_rect
        sx = left + self._x_norm(x) * w
        sy = top + h - self._y_norm(y) * h   # Y flip
        return sx, sy

    def data_x_to_screen(self, x: float | np.ndarray) -> np.ndarray:
        left, _, w, _ = self.axes_rect
        return left + self._x_norm(x) * w

    def data_y_to_screen(self, y: float | np.ndarray) -> np.ndarray:
        _, top, _, h = self.axes_rect
        return top + h - self._y_norm(y) * h

    # ------------------------------------------------------------------
    # Inverse transform: screen → data
    # ------------------------------------------------------------------

    def screen_to_data(self, sx: float, sy: float) -> tuple[float, float]:
        """Convert screen pixel (sx, sy) to data coordinates."""
        left, top, w, h = self.axes_rect
        xmin, xmax = self.xlim
        ymin, ymax = self.ylim

        tx = (sx - left) / w if w else 0.0
        ty = (top + h - sy) / h if h else 0.0   # Y flip

        if self.xscale == 'log':
            lmin = _log(xmin); lmax = _log(xmax)
            x = float(10 ** (lmin + tx * (lmax - lmin)))
        else:
            x = float(xmin + tx * (xmax - xmin))

        if self.yscale == 'log':
            lmin = _log(ymin); lmax = _log(ymax)
            y = float(10 ** (lmin + ty * (lmax - lmin)))
        else:
            y = float(ymin + ty * (ymax - ymin))

        return x, y

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------

    def zoom(self, sx: float, sy: float, factor: float) -> None:
        """Zoom by factor centered on screen point (sx, sy). factor<1 = zoom in."""
        cx, cy = self.screen_to_data(sx, sy)
        xmin, xmax = self.xlim
        ymin, ymax = self.ylim

        if self.xscale == 'log':
            lcx = _log(cx)
            lmin, lmax = float(_log(xmin)), float(_log(xmax))
            self.xlim = (10 ** (lcx - (lcx - lmin) * factor),
                         10 ** (lcx + (lmax - lcx) * factor))
        else:
            self.xlim = (cx - (cx - xmin) * factor, cx + (xmax - cx) * factor)

        if self.yscale == 'log':
            lcy = float(_log(cy))
            lmin, lmax = float(_log(ymin)), float(_log(ymax))
            self.ylim = (10 ** (lcy - (lcy - lmin) * factor),
                         10 ** (lcy + (lmax - lcy) * factor))
        else:
            self.ylim = (cy - (cy - ymin) * factor, cy + (ymax - cy) * factor)

    def pan(self, dpx: float, dpy: float) -> None:
        """Pan by (dpx, dpy) screen pixels."""
        _, _, w, h = self.axes_rect
        xmin, xmax = self.xlim
        ymin, ymax = self.ylim

        if self.xscale == 'log':
            lmin, lmax = float(_log(xmin)), float(_log(xmax))
            dlx = dpx / w * (lmax - lmin) if w else 0.0
            self.xlim = (10 ** (lmin + dlx), 10 ** (lmax + dlx))
        else:
            x_range = xmax - xmin if xmax != xmin else 1.0
            dx = dpx / w * x_range if w else 0.0
            self.xlim = (xmin + dx, xmax + dx)

        if self.yscale == 'log':
            lmin, lmax = float(_log(ymin)), float(_log(ymax))
            dly = -dpy / h * (lmax - lmin) if h else 0.0   # screen Y down = data Y up
            self.ylim = (10 ** (lmin + dly), 10 ** (lmax + dly))
        else:
            y_range = ymax - ymin if ymax != ymin else 1.0
            dy = -dpy / h * y_range if h else 0.0
            self.ylim = (ymin + dy, ymax + dy)

    def set_home(self) -> None:
        self._home_xlim = self.xlim
        self._home_ylim = self.ylim

    def reset_to_home(self) -> None:
        self.xlim = self._home_xlim
        self.ylim = self._home_ylim

    def contains_screen_point(self, sx: float, sy: float) -> bool:
        left, top, w, h = self.axes_rect
        return left <= sx <= left + w and top <= sy <= top + h

    def auto_scale(
        self,
        all_x: list,
        all_y: list,
        margin: float = 0.05,
        xlim_auto: bool = True,
        ylim_auto: bool = True,
    ) -> None:
        """Fit xlim/ylim to data with a margin fraction."""
        if all_x and xlim_auto:
            x_arr = np.concatenate([np.atleast_1d(np.asarray(a, float))
                                    for a in all_x if np.asarray(a).size > 0])
            x_arr = x_arr[np.isfinite(x_arr)]
            if self.xscale == 'log':
                x_arr = x_arr[x_arr > 0]
            if x_arr.size > 0:
                if self.xscale == 'log':
                    lmin, lmax = float(np.log10(x_arr.min())), float(np.log10(x_arr.max()))
                    span = lmax - lmin if lmax != lmin else 1.0
                    self.xlim = (10 ** (lmin - span * margin),
                                 10 ** (lmax + span * margin))
                else:
                    xmin, xmax = float(x_arr.min()), float(x_arr.max())
                    span = xmax - xmin if xmax != xmin else 1.0
                    self.xlim = (xmin - span * margin, xmax + span * margin)

        if all_y and ylim_auto:
            y_arr = np.concatenate([np.atleast_1d(np.asarray(a, float))
                                    for a in all_y if np.asarray(a).size > 0])
            y_arr = y_arr[np.isfinite(y_arr)]
            if self.yscale == 'log':
                y_arr = y_arr[y_arr > 0]
            if y_arr.size > 0:
                if self.yscale == 'log':
                    lmin, lmax = float(np.log10(y_arr.min())), float(np.log10(y_arr.max()))
                    span = lmax - lmin if lmax != lmin else 1.0
                    self.ylim = (10 ** (lmin - span * margin),
                                 10 ** (lmax + span * margin))
                else:
                    ymin, ymax = float(y_arr.min()), float(y_arr.max())
                    span = ymax - ymin if ymax != ymin else 1.0
                    self.ylim = (ymin - span * margin, ymax + span * margin)

        self.set_home()
