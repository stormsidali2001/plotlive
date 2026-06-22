from __future__ import annotations
import numpy as np
from .artists import (Line2D, PathCollection, Rectangle, BarContainer,
                       AxesImage, Polygon, ErrorBar)
from .transform import Transform
from .colors import to_rgba, DEFAULT_CYCLE
from ._parsers import _parse_fmt, _parse_plot_args


def _gaussian_kde(data: np.ndarray, x_eval: np.ndarray, bandwidth=None) -> np.ndarray:
    n = len(data)
    if n < 2:
        return np.zeros_like(x_eval, dtype=float)
    std = data.std()
    h = float(bandwidth) if bandwidth is not None else max(1.06 * std * n**(-0.2), 1e-10)
    diff = (x_eval[:, None] - data[None, :]) / h
    density = np.exp(-0.5 * diff**2).sum(axis=1)
    density /= n * h * np.sqrt(2 * np.pi)
    return density


def _resolve_color_list(color, n: int, next_color_fn) -> list:
    """
    Return a list of n colors.
    - If color is a list/tuple of n strings or tuples: use per-bar.
    - If color is a single color spec: broadcast to all n bars.
    - If color is None: use the color cycle (one call, broadcast).
    """
    if color is None:
        c = next_color_fn()
        return [c] * n
    if isinstance(color, (list, np.ndarray)) and len(color) == n:
        # Could be list of color strings or list of tuples
        if n > 0 and isinstance(color[0], (str, tuple, list)):
            return list(color)
        # Single color that happened to be a sequence — fall through
    return [color] * n


class Legend:
    def __init__(self, ax: 'Axes', loc: str = 'best'):
        self.ax = ax
        self.loc = loc


class Axes:
    """
    One subplot. Stores all artists and axis state.
    Rendering is delegated to AxesRenderer.
    """

    def __init__(self, figure: 'Figure', rect_norm: tuple[float, float, float, float]):
        self._figure = figure
        self.rect_norm = rect_norm  # (left, bottom, width, height) in [0,1]

        self.lines: list[Line2D] = []
        self.collections: list[PathCollection] = []
        self.patches: list = []   # Rectangle | Polygon
        self.images: list[AxesImage] = []
        self.errorbars: list[ErrorBar] = []

        self.transform = Transform()

        self._xlim_auto: bool = True
        self._ylim_auto: bool = True
        self._xlabel: str = ''
        self._ylabel: str = ''
        self._title: str = ''
        self._xscale: str = 'linear'
        self._yscale: str = 'linear'
        self._legend_visible: bool = False
        self._legend_loc: str = 'best'
        self._grid: bool = False
        self._grid_color: tuple = (200, 200, 200, 255)
        self._grid_linewidth: float = 0.5
        self._grid_linestyle: str = '--'
        self._facecolor: tuple = (255, 255, 255, 255)
        self._xticks_manual: list | None = None
        self._yticks_manual: list | None = None
        self._xtick_labels_manual: list | None = None
        self._ytick_labels_manual: list | None = None
        self._xtick_labels: list | None = None  # for categorical x in bar()
        self._colorbar_image: AxesImage | None = None
        self._aspect: str = 'auto'

        self._color_cycle_idx: int = 0
        self._dirty: bool = True

    # ------------------------------------------------------------------
    # Color cycle
    # ------------------------------------------------------------------

    def _next_color(self) -> tuple:
        color = DEFAULT_CYCLE[self._color_cycle_idx % len(DEFAULT_CYCLE)]
        self._color_cycle_idx += 1
        return color

    # ------------------------------------------------------------------
    # Plot methods
    # ------------------------------------------------------------------

    def plot(self, *args, **kwargs) -> list[Line2D]:
        """Plot lines. Returns list of Line2D."""
        segments = _parse_plot_args(args)
        lines = []
        for x, y, fmt in segments:
            props = _parse_fmt(fmt)
            # kwargs override fmt
            for k, v in kwargs.items():
                props[k] = v
            if 'color' not in props and 'c' not in props:
                props['color'] = self._next_color()
            line = Line2D(x, y, **props)
            self.lines.append(line)
            lines.append(line)
        self._dirty = True
        return lines

    def scatter(self, x, y, s=20, c=None, marker='o', cmap=None,
                vmin=None, vmax=None, alpha=1.0, linewidths=0,
                edgecolors='none', label='', **kwargs) -> PathCollection:
        if c is None:
            c = self._next_color()
        col = PathCollection(
            x, y, s=s, c=c, marker=marker,
            cmap=cmap or 'viridis', vmin=vmin, vmax=vmax,
            alpha=alpha, linewidths=linewidths,
            edgecolors=edgecolors, label=label,
        )
        self.collections.append(col)
        self._dirty = True
        return col

    def hist(self, x, bins=10, range=None, density=False, weights=None,
             color=None, edgecolor='black', alpha=1.0, label='',
             orientation='vertical', **kwargs):
        """Compute histogram and create Rectangle patches. Returns (n, edges, patches)."""
        color = color if color is not None else self._next_color()
        x_arr = np.asarray(x, dtype=float).ravel()
        counts, edges = np.histogram(x_arr, bins=bins, range=range,
                                     density=density, weights=weights)
        patch_list = []
        for i, (count, left) in enumerate(zip(counts, edges[:-1])):
            w = edges[i + 1] - left
            rect_label = label if i == 0 else '_nolegend_'
            if orientation == 'horizontal':
                r = Rectangle(0, left, float(count), w,
                               color=color, edgecolor=edgecolor,
                               alpha=alpha, label=rect_label, _horizontal=True)
            else:
                r = Rectangle(left, 0, w, float(count),
                               color=color, edgecolor=edgecolor,
                               alpha=alpha, label=rect_label)
            self.patches.append(r)
            patch_list.append(r)
        self._dirty = True
        return counts, edges, patch_list

    def bar(self, x, height, width=0.8, bottom=0, color=None,
            edgecolor='black', linewidth=1.0, align='center',
            label='', alpha=1.0, **kwargs) -> BarContainer:
        x_arr = np.asarray(x)
        # Categorical support
        if x_arr.dtype.kind in ('U', 'S', 'O'):
            self._xtick_labels = [str(v) for v in x_arr]
            x_arr = np.arange(len(x_arr), dtype=float)
        else:
            x_arr = x_arr.astype(float)

        if align == 'center':
            x_arr = x_arr - width / 2

        heights = np.atleast_1d(np.asarray(height, dtype=float))
        bottoms = np.broadcast_to(np.atleast_1d(np.asarray(bottom, dtype=float)),
                                   heights.shape).copy()

        # color may be a single value or a per-bar list
        color_list = _resolve_color_list(color, len(heights), self._next_color)

        patch_list = []
        for i, (xi, h, b) in enumerate(zip(x_arr, heights, bottoms)):
            rect_label = label if i == 0 else '_nolegend_'
            r = Rectangle(float(xi), float(b), float(width), float(h),
                           color=color_list[i], edgecolor=edgecolor,
                           linewidth=linewidth, label=rect_label, alpha=alpha)
            self.patches.append(r)
            patch_list.append(r)
        self._dirty = True
        return BarContainer(patch_list, label=label)

    def barh(self, y, width, height=0.8, left=0, color=None,
             edgecolor='black', linewidth=1.0, align='center',
             label='', alpha=1.0, **kwargs) -> BarContainer:
        """Horizontal bar chart."""
        y_arr = np.asarray(y)
        if y_arr.dtype.kind in ('U', 'S', 'O'):
            self._ytick_labels_manual = [str(v) for v in y_arr]
            y_arr = np.arange(len(y_arr), dtype=float)
        else:
            y_arr = y_arr.astype(float)

        if align == 'center':
            y_arr = y_arr - height / 2

        widths = np.atleast_1d(np.asarray(width, dtype=float))
        lefts = np.broadcast_to(np.atleast_1d(np.asarray(left, dtype=float)),
                                 widths.shape).copy()

        color_list = _resolve_color_list(color, len(widths), self._next_color)

        patch_list = []
        for i, (yi, w, l) in enumerate(zip(y_arr, widths, lefts)):
            rect_label = label if i == 0 else '_nolegend_'
            r = Rectangle(float(l), float(yi), float(w), float(height),
                           color=color_list[i], edgecolor=edgecolor,
                           linewidth=linewidth, label=rect_label, alpha=alpha,
                           _horizontal=True)
            self.patches.append(r)
            patch_list.append(r)
        self._dirty = True
        return BarContainer(patch_list, label=label)

    def imshow(self, X, cmap=None, vmin=None, vmax=None,
               aspect='equal', origin='upper', extent=None,
               interpolation='nearest', **kwargs) -> AxesImage:
        img = AxesImage(X, cmap=cmap or 'viridis', vmin=vmin, vmax=vmax,
                        aspect=aspect, origin=origin, extent=extent)
        self.images.append(img)
        self._colorbar_image = img
        self._dirty = True
        return img

    def fill_between(self, x, y1, y2=0, alpha=0.3, color=None,
                     label='', edgecolor='none', **kwargs):
        x = np.asarray(x, float)
        y1 = np.broadcast_to(np.asarray(y1, float), x.shape).copy()
        y2 = np.broadcast_to(np.asarray(y2, float), x.shape).copy()
        xy = np.vstack([
            np.column_stack([x, y1]),
            np.column_stack([x[::-1], y2[::-1]]),
        ])
        c = color if color is not None else self._next_color()
        poly = Polygon(xy, color=c, alpha=alpha, edgecolor=edgecolor, label=label)
        self.patches.append(poly)
        self._dirty = True
        return poly

    def errorbar(self, x, y, yerr=None, xerr=None, fmt='', capsize=4,
                 color=None, label='', **kwargs):
        c = color if color is not None else self._next_color()
        eb = ErrorBar(x, y, yerr=yerr, xerr=xerr, color=c,
                      capsize=capsize, label=label, **kwargs)
        self.errorbars.append(eb)
        # Draw the central line / markers via existing plot()
        line_kw = {k: v for k, v in kwargs.items() if k != 'capsize'}
        line_kw['color'] = c
        if label:
            line_kw['label'] = label
        if fmt:
            self.plot(x, y, fmt, **line_kw)
        else:
            self.plot(x, y, **line_kw)
        self._dirty = True
        return eb

    def boxplot(self, data, positions=None, widths=0.5, vert=True,
                color=None, **kwargs):
        if isinstance(data, np.ndarray) and data.ndim == 1:
            datasets = [data]
        elif not hasattr(data[0], '__len__'):
            datasets = [np.asarray(data, float)]
        else:
            datasets = [np.asarray(d, float) for d in data]

        n = len(datasets)
        if positions is None:
            positions = list(range(1, n + 1))
        half_w = widths / 2 if isinstance(widths, (int, float)) else widths[0] / 2
        c = color if color is not None else self._next_color()

        for i, (d, pos) in enumerate(zip(datasets, positions)):
            d = np.asarray(d, float); d = d[np.isfinite(d)]
            if d.size == 0:
                continue
            q1, med, q3 = float(np.percentile(d, 25)), float(np.median(d)), float(np.percentile(d, 75))
            iqr = q3 - q1
            lo = max(float(d.min()), q1 - 1.5 * iqr)
            hi = min(float(d.max()), q3 + 1.5 * iqr)
            outliers = d[(d < lo) | (d > hi)]
            rect_lbl = kwargs.get('label', '_nolegend_') if i == 0 else '_nolegend_'

            if vert:
                self.patches.append(Rectangle(pos - half_w, q1, 2 * half_w, q3 - q1,
                                               color=c, edgecolor=c, linewidth=1.5,
                                               label=rect_lbl))
                for y0, y1_ in [(q1, lo), (q3, hi)]:
                    self.lines.append(Line2D([pos, pos], [y0, y1_], color=c,
                                             linewidth=1, linestyle='--'))
                for y_cap in [lo, hi]:
                    self.lines.append(Line2D([pos - half_w * 0.6, pos + half_w * 0.6],
                                             [y_cap, y_cap], color=c, linewidth=1.5))
                self.lines.append(Line2D([pos - half_w, pos + half_w], [med, med],
                                         color='white', linewidth=2.5))
                if outliers.size:
                    self.collections.append(PathCollection(
                        np.full(len(outliers), float(pos)), outliers,
                        s=20, c=c, marker='o'))
            else:
                self.patches.append(Rectangle(q1, pos - half_w, q3 - q1, 2 * half_w,
                                               color=c, edgecolor=c, linewidth=1.5,
                                               label=rect_lbl))
                for x0, x1_ in [(q1, lo), (q3, hi)]:
                    self.lines.append(Line2D([x0, x1_], [pos, pos], color=c,
                                             linewidth=1, linestyle='--'))
                for x_cap in [lo, hi]:
                    self.lines.append(Line2D([x_cap, x_cap],
                                             [pos - half_w * 0.6, pos + half_w * 0.6],
                                             color=c, linewidth=1.5))
                self.lines.append(Line2D([med, med], [pos - half_w, pos + half_w],
                                         color='white', linewidth=2.5))
                if outliers.size:
                    self.collections.append(PathCollection(
                        outliers, np.full(len(outliers), float(pos)),
                        s=20, c=c, marker='o'))
        self._dirty = True

    def violinplot(self, data, positions=None, widths=0.5, vert=True,
                   color=None, alpha=0.7, **kwargs):
        if isinstance(data, np.ndarray) and data.ndim == 1:
            datasets = [data]
        elif not hasattr(data[0], '__len__'):
            datasets = [np.asarray(data, float)]
        else:
            datasets = [np.asarray(d, float) for d in data]

        n = len(datasets)
        if positions is None:
            positions = list(range(1, n + 1))
        half_w = widths / 2 if isinstance(widths, (int, float)) else widths[0] / 2

        for i, (d, pos) in enumerate(zip(datasets, positions)):
            d = np.asarray(d, float); d = d[np.isfinite(d)]
            if d.size < 2:
                continue
            c = color if color is not None else (self._next_color() if i == 0
                                                  else self._next_color())
            y_eval = np.linspace(d.min(), d.max(), 150)
            density = _gaussian_kde(d, y_eval)
            max_d = density.max()
            if max_d == 0:
                continue
            dn = density / max_d * half_w
            lbl = kwargs.get('label', '_nolegend_') if i == 0 else '_nolegend_'
            if vert:
                xy = np.vstack([np.column_stack([pos + dn, y_eval]),
                                np.column_stack([pos - dn[::-1], y_eval[::-1]])])
            else:
                xy = np.vstack([np.column_stack([y_eval, pos + dn]),
                                np.column_stack([y_eval[::-1], pos - dn[::-1]])])
            self.patches.append(Polygon(xy, color=c, alpha=alpha,
                                        edgecolor=c, linewidth=1, label=lbl))
            med = float(np.median(d))
            if vert:
                self.lines.append(Line2D([pos - half_w * 0.4, pos + half_w * 0.4],
                                         [med, med], color='white', linewidth=2))
            else:
                self.lines.append(Line2D([med, med],
                                         [pos - half_w * 0.4, pos + half_w * 0.4],
                                         color='white', linewidth=2))
        self._dirty = True

    def pie(self, x, labels=None, colors=None, startangle=90, **kwargs):
        x = np.asarray(x, float)
        x = x[x > 0]
        total = x.sum()
        if total == 0:
            return []
        fracs = x / total
        if colors is None:
            colors = [DEFAULT_CYCLE[i % len(DEFAULT_CYCLE)] for i in range(len(x))]
        theta = float(np.radians(startangle))
        wedges = []
        for i, (frac, c) in enumerate(zip(fracs, colors)):
            theta_end = theta + 2 * np.pi * frac
            n_pts = max(3, int(60 * frac))
            angles = np.linspace(theta, theta_end, n_pts)
            xs = np.concatenate([[0.0], np.cos(angles), [0.0]])
            ys = np.concatenate([[0.0], np.sin(angles), [0.0]])
            lbl = labels[i] if labels and i < len(labels) else '_nolegend_'
            poly = Polygon(np.column_stack([xs, ys]),
                           color=c, alpha=float(kwargs.get('alpha', 1.0)),
                           edgecolor='white', linewidth=1.5, label=lbl)
            self.patches.append(poly)
            wedges.append(poly)
            theta = theta_end
        self.set_xlim(-1.4, 1.4)
        self.set_ylim(-1.4, 1.4)
        self._aspect = 'equal'
        self.set_xticks([], [])
        self.set_yticks([], [])
        self._dirty = True
        return wedges

    def stackplot(self, x, *ys, labels=None, colors=None, alpha=1.0, **kwargs):
        x = np.asarray(x, float)
        if labels is None:
            labels = [''] * len(ys)
        if colors is None:
            colors = [self._next_color() for _ in ys]
        baseline = np.zeros_like(x)
        polys = []
        for y_arr, c, lbl in zip(ys, colors, labels):
            top = baseline + np.asarray(y_arr, float)
            polys.append(self.fill_between(x, baseline, top,
                                           color=c, alpha=alpha, label=lbl))
            baseline = top
        return polys

    # ------------------------------------------------------------------
    # Axes configuration
    # ------------------------------------------------------------------

    def set_xlabel(self, label: str, **kwargs) -> None:
        self._xlabel = label
        self._dirty = True

    def set_ylabel(self, label: str, **kwargs) -> None:
        self._ylabel = label
        self._dirty = True

    def set_title(self, label: str, **kwargs) -> None:
        self._title = label
        self._dirty = True

    def set_xlim(self, left=None, right=None, **kwargs) -> tuple:
        if isinstance(left, (tuple, list)):
            left, right = left[0], left[1]
        if left is not None and right is not None:
            self.transform.xlim = (float(left), float(right))
            self.transform._home_xlim = self.transform.xlim
            self._xlim_auto = False
        self._dirty = True
        return self.transform.xlim

    def set_ylim(self, bottom=None, top=None, **kwargs) -> tuple:
        if isinstance(bottom, (tuple, list)):
            bottom, top = bottom[0], bottom[1]
        if bottom is not None and top is not None:
            self.transform.ylim = (float(bottom), float(top))
            self.transform._home_ylim = self.transform.ylim
            self._ylim_auto = False
        self._dirty = True
        return self.transform.ylim

    def get_xlim(self) -> tuple[float, float]:
        return self.transform.xlim

    def get_ylim(self) -> tuple[float, float]:
        return self.transform.ylim

    def legend(self, *args, loc='best', **kwargs) -> Legend:
        self._legend_visible = True
        self._legend_loc = loc
        self._dirty = True
        return Legend(self, loc=loc)

    def grid(self, visible=True, which='major', axis='both',
             color=None, linewidth=0.5, linestyle='--', **kwargs) -> None:
        self._grid = visible
        if color:
            self._grid_color = to_rgba(color)
        self._grid_linewidth = linewidth
        self._grid_linestyle = linestyle
        self._dirty = True

    def set_facecolor(self, color) -> None:
        self._facecolor = to_rgba(color)
        self._dirty = True

    def set_xscale(self, value: str, **kwargs) -> None:
        self._xscale = value
        self.transform.xscale = value
        self._dirty = True

    def set_yscale(self, value: str, **kwargs) -> None:
        self._yscale = value
        self.transform.yscale = value
        self._dirty = True

    def set_xticks(self, ticks, labels=None, **kwargs) -> None:
        self._xticks_manual = list(ticks)
        self._xtick_labels_manual = list(labels) if labels is not None else None
        self._dirty = True

    def set_yticks(self, ticks, labels=None, **kwargs) -> None:
        self._yticks_manual = list(ticks)
        self._ytick_labels_manual = list(labels) if labels is not None else None
        self._dirty = True

    def get_xticks(self) -> list:
        return self._xticks_manual or []

    def get_yticks(self) -> list:
        return self._yticks_manual or []

    def tick_params(self, axis='both', **kwargs) -> None:
        pass  # MVP: no-op

    def set_aspect(self, aspect, **kwargs) -> None:
        self._aspect = str(aspect)
        self._dirty = True

    def invert_xaxis(self) -> None:
        xmin, xmax = self.transform.xlim
        self.transform.xlim = (xmax, xmin)
        self._dirty = True

    def invert_yaxis(self) -> None:
        ymin, ymax = self.transform.ylim
        self.transform.ylim = (ymax, ymin)
        self._dirty = True

    def cla(self) -> None:
        """Clear axes — reset artists and state."""
        self.lines.clear()
        self.collections.clear()
        self.patches.clear()
        self.images.clear()
        self.errorbars.clear()
        self._color_cycle_idx = 0
        self._xlim_auto = True
        self._ylim_auto = True
        self._xlabel = ''
        self._ylabel = ''
        self._title = ''
        self._legend_visible = False
        self._aspect = 'auto'
        self._xtick_labels = None
        self._xticks_manual = None
        self._yticks_manual = None
        self._xtick_labels_manual = None
        self._ytick_labels_manual = None
        self._colorbar_image = None
        self._dirty = True

    # ------------------------------------------------------------------
    # Auto-scale (called by renderer at render time)
    # ------------------------------------------------------------------

    def _compute_auto_limits(self) -> None:
        all_x: list = []
        all_y: list = []

        for line in self.lines:
            if line.xdata.size:
                all_x.append(line.xdata)
                all_y.append(line.ydata)
        for col in self.collections:
            if col.xdata.size:
                all_x.append(col.xdata)
                all_y.append(col.ydata)
        for patch in self.patches:
            if isinstance(patch, Polygon):
                if patch.xy.size:
                    all_x.append(patch.xy[:, 0])
                    all_y.append(patch.xy[:, 1])
            else:
                all_x.extend([patch.x, patch.x + patch.width])
                all_y.extend([patch.y, patch.y + patch.height])
        for eb in self.errorbars:
            all_x.append(eb.xdata)
            all_y.append(eb.ydata)
            if eb.yerr is not None:
                all_y.append(eb.ydata - eb.yerr[0])
                all_y.append(eb.ydata + eb.yerr[1])
            if eb.xerr is not None:
                all_x.append(eb.xdata - eb.xerr[0])
                all_x.append(eb.xdata + eb.xerr[1])
        for img in self.images:
            if img.extent:
                xmin, xmax, ymin, ymax = img.extent
            else:
                h, w = img.data.shape[:2]
                xmin, xmax, ymin, ymax = -0.5, w - 0.5, -0.5, h - 0.5
            all_x.extend([[xmin, xmax]])
            all_y.extend([[ymin, ymax]])

        if all_x or all_y:
            # For bar charts, include y=0 in the y range
            has_bars = any(isinstance(p, Rectangle) for p in self.patches)
            if has_bars:
                all_y.append([0.0])

            self.transform.auto_scale(
                all_x, all_y,
                margin=0.05,
                xlim_auto=self._xlim_auto,
                ylim_auto=self._ylim_auto,
            )

    # ------------------------------------------------------------------
    # Hit testing for hover tooltips
    # ------------------------------------------------------------------

    def hit_test(self, sx: float, sy: float,
                 threshold_px: float = 12.0) -> list[dict]:
        hits = []
        for line in self.lines:
            if not line.visible or line.xdata.size == 0:
                continue
            px, py = self.transform.data_to_screen(line.xdata, line.ydata)
            dists = np.hypot(px - sx, py - sy)
            idx = int(np.argmin(dists))
            if dists[idx] < threshold_px:
                hits.append({
                    'artist': line,
                    'x': float(line.xdata[idx]),
                    'y': float(line.ydata[idx]),
                    'index': idx,
                })
        for col in self.collections:
            if not col.visible or col.xdata.size == 0:
                continue
            px, py = self.transform.data_to_screen(col.xdata, col.ydata)
            dists = np.hypot(px - sx, py - sy)
            idx = int(np.argmin(dists))
            if dists[idx] < threshold_px:
                hits.append({
                    'artist': col,
                    'x': float(col.xdata[idx]),
                    'y': float(col.ydata[idx]),
                    'index': idx,
                })
        return hits
