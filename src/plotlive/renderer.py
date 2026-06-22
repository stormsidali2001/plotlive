from __future__ import annotations
import numpy as np
from .ticks import auto_ticks, format_ticks, log_ticks, format_log_tick
from .colors import get_cmap, to_rgba
from .drawing import draw_dashed_polyline, draw_marker, draw_colorbar_strip
from .fonts import get_font, render_text, render_text_rotated
from .artists import Polygon, ErrorBar, Rectangle

# Pixel margins for label/tick areas outside data rect
_MARGIN_LEFT   = 65
_MARGIN_RIGHT  = 20
_MARGIN_BOTTOM = 50
_MARGIN_TOP    = 35
_TICK_LEN      = 5
_COLORBAR_W    = 55  # pixels reserved for colorbar on right


def _norm_to_pixel(rect_norm, fig_w, fig_h):
    """Convert (left, bottom, w, h) normalized to pixel (left, top, w, h)."""
    nl, nb, nw, nh = rect_norm
    px_l = int(nl * fig_w)
    px_h = int(nh * fig_h)
    px_w = int(nw * fig_w)
    px_t = int((1.0 - nb - nh) * fig_h)
    return px_l, px_t, px_w, px_h


class FigureRenderer:
    def __init__(self, figure):
        self.figure = figure

    def render(self):
        import pygame
        fig = self.figure
        w, h = fig.pixel_size
        surface = pygame.Surface((w, h))
        bg = to_rgba(fig.facecolor)
        surface.fill(bg[:3])

        focused = fig._focused_ax

        if focused is not None:
            # Focus mode: expand the selected axes to fill the whole figure
            ax_surf = AxesRenderer(focused, w, h, ax_offset=(0, 0)).render()
            surface.blit(ax_surf, (0, 0))

            # Subtle exit hint at the bottom
            font = get_font('label')
            hint = font.render(
                'Focus mode  —  double-click or Esc to return',
                True, (150, 150, 150),
            )
            surface.blit(hint, (w // 2 - hint.get_width() // 2, h - hint.get_height() - 4))
        else:
            for ax in fig.axes:
                ax_l, ax_t, ax_w, ax_h = _norm_to_pixel(ax.rect_norm, w, h)
                ax_surf = AxesRenderer(ax, ax_w, ax_h, ax_offset=(ax_l, ax_t)).render()
                surface.blit(ax_surf, (ax_l, ax_t))

            # Suptitle
            if fig._suptitle:
                font = get_font('suptitle')
                ts = font.render(fig._suptitle, True, (0, 0, 0))
                surface.blit(ts, (w // 2 - ts.get_width() // 2, 4))

        return surface


class AxesRenderer:
    """Renders one Axes into a pygame.Surface of size (ax_w, ax_h).

    ax_offset is the (left, top) position of this axes surface within the
    full figure, in pixels.  It is added to axes_rect so that
    transform.contains_screen_point() works correctly with figure-space
    mouse coordinates.
    """

    def __init__(self, ax, ax_w: int, ax_h: int, ax_offset: tuple[int, int] = (0, 0)):
        self.ax = ax
        self.ax_w = ax_w
        self.ax_h = ax_h
        self.ax_offset = ax_offset

    def render(self):
        import pygame
        ax = self.ax

        # Auto-scale before we know data extents
        if ax._xlim_auto or ax._ylim_auto:
            ax._compute_auto_limits()

        # Reserve colorbar space if needed
        has_colorbar = ax._colorbar_image is not None
        cb_reserve = _COLORBAR_W if has_colorbar else 0

        # Compute data area within the axes allocation
        margin_right = _MARGIN_RIGHT + cb_reserve
        data_l = _MARGIN_LEFT
        data_t = _MARGIN_TOP
        data_w = max(1, self.ax_w - _MARGIN_LEFT - margin_right)
        data_h = max(1, self.ax_h - _MARGIN_TOP - _MARGIN_BOTTOM)

        # Equal-aspect adjustment (used by pie charts)
        if ax._aspect == 'equal':
            xmin, xmax = ax.transform.xlim
            ymin, ymax = ax.transform.ylim
            x_range = max(xmax - xmin, 1e-10)
            y_range = max(ymax - ymin, 1e-10)
            x_ppu = data_w / x_range
            y_ppu = data_h / y_range
            if x_ppu < y_ppu:
                new_h = max(1, int(data_w * y_range / x_range))
                data_t += (data_h - new_h) // 2
                data_h = new_h
            else:
                new_w = max(1, int(data_h * x_range / y_range))
                data_l += (data_w - new_w) // 2
                data_w = new_w

        # axes_rect in figure-space so coordinate math works with figure-space
        # mouse coordinates regardless of subplot position.
        off_l, off_t = self.ax_offset
        ax.transform.axes_rect = (off_l + data_l, off_t + data_t, data_w, data_h)
        # panel_rect covers the full subplot area including tick/label margins,
        # so hit-testing (hover, zoom, pan) works anywhere inside the panel.
        ax.transform.panel_rect = (off_l, off_t, self.ax_w, self.ax_h)

        surface = pygame.Surface((self.ax_w, self.ax_h))
        surface.fill((255, 255, 255))

        data_rect = pygame.Rect(data_l, data_t, data_w, data_h)

        # 1. Axes background
        pygame.draw.rect(surface, ax._facecolor[:3], data_rect)

        # 2. Grid
        if ax._grid:
            self._draw_grid(surface, data_rect)

        # 3-8. Data layers (clip to data_rect via subsurface)
        data_surf = surface.subsurface(data_rect)
        self._draw_images(data_surf)
        self._draw_polys(data_surf)      # fill_between / violin / pie / stackplot
        self._draw_patches(data_surf)
        self._draw_collections(data_surf)
        self._draw_lines(data_surf)
        self._draw_errorbars(data_surf)  # error bar whiskers

        # 8. Axes border
        pygame.draw.rect(surface, (0, 0, 0), data_rect, 1)

        # 9. Ticks + labels
        self._draw_ticks(surface, data_rect)
        self._draw_labels(surface, data_rect)

        # 10. Legend
        if ax._legend_visible:
            self._draw_legend(surface, data_rect)

        # 11. Colorbar
        if has_colorbar:
            cb_rect = pygame.Rect(
                data_l + data_w + _MARGIN_RIGHT,
                data_t,
                _COLORBAR_W - _MARGIN_RIGHT - 5,
                data_h,
            )
            self._draw_colorbar(surface, cb_rect, ax._colorbar_image)

        ax._dirty = False
        return surface

    # ------------------------------------------------------------------
    # Data drawing helpers (operate on subsurface — origin is data_rect.topleft)
    # ------------------------------------------------------------------

    def _screen_to_sub(self, sx, sy):
        """Convert transform screen coords to subsurface (data area) coords."""
        l, t, _, _ = self.ax.transform.axes_rect
        if isinstance(sx, np.ndarray):
            return sx - l, sy - t
        return sx - l, sy - t

    def _draw_lines(self, surf) -> None:
        from .drawing import draw_dashed_polyline, draw_marker
        ax = self.ax
        for line in ax.lines:
            if not line.visible or line.xdata.size == 0:
                continue
            sx, sy = ax.transform.data_to_screen(line.xdata, line.ydata)
            sx, sy = self._screen_to_sub(sx, sy)
            points = list(zip(sx.tolist(), sy.tolist()))

            a = int(line.color[3] * line.alpha) if len(line.color) > 3 else 255
            color = (line.color[0], line.color[1], line.color[2], a)

            if line.linestyle not in ('None', 'none', ''):
                draw_dashed_polyline(surf, color, points,
                                     linewidth=max(1, int(line.linewidth)),
                                     linestyle=line.linestyle)
            if line.marker:
                mfc = line.markerfacecolor
                mc = to_rgba(mfc) if mfc else color
                for px, py in points:
                    draw_marker(surf, mc, (px, py),
                                marker=line.marker, size=line.markersize ** 2)

    def _draw_collections(self, surf) -> None:
        ax = self.ax
        for col in ax.collections:
            if not col.visible or col.xdata.size == 0:
                continue
            colors = col.resolve_colors()
            sx, sy = ax.transform.data_to_screen(col.xdata, col.ydata)
            sx, sy = self._screen_to_sub(sx, sy)
            for i in range(len(sx)):
                c = tuple(int(v) for v in colors[i, :3])
                a = int(colors[i, 3] * col.alpha)
                draw_marker(surf, (*c, a), (sx[i], sy[i]),
                            marker=col.marker, size=col.sizes[i])

    def _draw_polys(self, surf) -> None:
        """Render Polygon artists (fill_between, violinplot, pie, stackplot)."""
        import pygame
        ax = self.ax
        _, _, dw, dh = ax.transform.axes_rect

        for patch in ax.patches:
            if not isinstance(patch, Polygon) or not patch.visible:
                continue
            xy = patch.xy
            if len(xy) < 3:
                continue
            sx, sy = ax.transform.data_to_screen(xy[:, 0], xy[:, 1])
            sx = sx - ax.transform.axes_rect[0]
            sy = sy - ax.transform.axes_rect[1]
            points = list(zip(sx.tolist(), sy.tolist()))

            fc = patch.facecolor
            if fc[3] > 0:
                tmp = pygame.Surface((dw, dh), pygame.SRCALPHA)
                pygame.draw.polygon(tmp, fc, points)
                surf.blit(tmp, (0, 0))

            ec = patch.edgecolor
            if ec[3] > 0:
                lw = max(1, int(patch.linewidth))
                pygame.draw.polygon(surf, ec[:3], points, lw)

    def _draw_errorbars(self, surf) -> None:
        """Render ErrorBar whiskers and caps."""
        import pygame
        from .drawing import draw_marker, draw_dashed_polyline
        ax = self.ax

        for eb in ax.errorbars:
            if not eb.visible:
                continue
            color = (*eb.color[:3], int(eb.color[3] * eb.alpha))
            lw = max(1, int(eb.linewidth))
            cap = int(eb.capsize)

            sx_all, sy_all = ax.transform.data_to_screen(eb.xdata, eb.ydata)
            sx_all, sy_all = self._screen_to_sub(sx_all, sy_all)

            for idx in range(len(eb.xdata)):
                px, py = float(sx_all[idx]), float(sy_all[idx])

                if eb.yerr is not None:
                    y_lo = eb.ydata[idx] - eb.yerr[0, idx]
                    y_hi = eb.ydata[idx] + eb.yerr[1, idx]
                    _, sy_lo = ax.transform.data_to_screen(eb.xdata[idx], y_lo)
                    _, sy_hi = ax.transform.data_to_screen(eb.xdata[idx], y_hi)
                    sy_lo -= ax.transform.axes_rect[1]
                    sy_hi -= ax.transform.axes_rect[1]
                    pygame.draw.line(surf, color, (int(px), int(sy_hi)),
                                     (int(px), int(sy_lo)), lw)
                    for sy_cap in [int(sy_lo), int(sy_hi)]:
                        pygame.draw.line(surf, color,
                                         (int(px) - cap, sy_cap),
                                         (int(px) + cap, sy_cap), lw)

                if eb.xerr is not None:
                    x_lo = eb.xdata[idx] - eb.xerr[0, idx]
                    x_hi = eb.xdata[idx] + eb.xerr[1, idx]
                    sx_lo, _ = ax.transform.data_to_screen(x_lo, eb.ydata[idx])
                    sx_hi, _ = ax.transform.data_to_screen(x_hi, eb.ydata[idx])
                    sx_lo -= ax.transform.axes_rect[0]
                    sx_hi -= ax.transform.axes_rect[0]
                    pygame.draw.line(surf, color, (int(sx_lo), int(py)),
                                     (int(sx_hi), int(py)), lw)
                    for sx_cap in [int(sx_lo), int(sx_hi)]:
                        pygame.draw.line(surf, color,
                                         (sx_cap, int(py) - cap),
                                         (sx_cap, int(py) + cap), lw)

    def _draw_patches(self, surf) -> None:
        import pygame
        ax = self.ax
        _, _, dw, dh = ax.transform.axes_rect
        dl, dt = 0, 0  # subsurface origin

        for patch in ax.patches:
            if isinstance(patch, Polygon) or not patch.visible:
                continue
            # Convert all four corners to sub-surface coords
            px0 = ax.transform.data_x_to_screen(patch.x)
            px1 = ax.transform.data_x_to_screen(patch.x + patch.width)
            py0 = ax.transform.data_y_to_screen(patch.y + patch.height)  # top
            py1 = ax.transform.data_y_to_screen(patch.y)                 # bottom

            # Shift to subsurface coords
            px0 -= ax.transform.axes_rect[0]
            px1 -= ax.transform.axes_rect[0]
            py0 -= ax.transform.axes_rect[1]
            py1 -= ax.transform.axes_rect[1]

            # Zero-dimension patches are legend-only markers — don't draw them
            if patch.width == 0 and patch.height == 0:
                continue

            rx = int(round(min(px0, px1)))
            ry = int(round(min(py0, py1)))
            rw = max(1, int(round(abs(px1 - px0))))
            rh = max(1, int(round(abs(py1 - py0))))

            # Clip to data area
            rx = max(dl, rx); ry = max(dt, ry)
            if rx + rw > dw: rw = dw - rx
            if ry + rh > dh: rh = dh - ry
            if rw <= 0 or rh <= 0:
                continue

            fc = patch.facecolor[:3]
            pygame.draw.rect(surf, fc, (rx, ry, rw, rh))
            if patch.edgecolor[3] > 0:
                ec = patch.edgecolor[:3]
                pygame.draw.rect(surf, ec, (rx, ry, rw, rh), max(1, int(patch.linewidth)))

    def _draw_images(self, surf) -> None:
        import pygame
        ax = self.ax
        _, _, dw, dh = ax.transform.axes_rect

        for img in ax.images:
            data = img.data
            # Build RGBA pixel array
            if data.ndim == 2:
                # Scalar data — apply colormap
                vmin = img.vmin if img.vmin is not None else float(data.min())
                vmax = img.vmax if img.vmax is not None else float(data.max())
                span = vmax - vmin if vmax != vmin else 1.0
                t = np.clip((data.astype(float) - vmin) / span, 0.0, 1.0)
                cmap = get_cmap(img.cmap_name)
                rgba = cmap(t)  # (H, W, 4) uint8
            elif data.ndim == 3 and data.shape[2] in (3, 4):
                if data.dtype != np.uint8:
                    rgba_f = np.clip(data, 0, 1) if data.max() <= 1.0 else data
                    rgba = (rgba_f * 255).astype(np.uint8) if rgba_f.max() <= 1.0 else rgba_f.astype(np.uint8)
                else:
                    rgba = data
                if rgba.shape[2] == 3:
                    alpha_ch = np.full((*rgba.shape[:2], 1), 255, dtype=np.uint8)
                    rgba = np.concatenate([rgba, alpha_ch], axis=2)
            else:
                continue

            h_d, w_d = rgba.shape[:2]
            if img.origin == 'upper':
                # row 0 = top, screen Y down = matches
                pass
            else:
                rgba = rgba[::-1, :, :]  # flip for 'lower'

            # Scale to data area
            img_surf = pygame.Surface((w_d, h_d), pygame.SRCALPHA)
            try:
                pygame.surfarray.blit_array(img_surf, rgba.transpose(1, 0, 2).copy())
            except Exception:
                # Fallback pixel-by-pixel (slow but safe)
                for r in range(h_d):
                    for c in range(w_d):
                        img_surf.set_at((c, r), tuple(rgba[r, c]))

            scaled = pygame.transform.scale(img_surf, (dw, dh))
            surf.blit(scaled, (0, 0))

    def _draw_grid(self, surface, data_rect) -> None:
        import pygame
        ax = self.ax
        l, t, w, h = data_rect.left, data_rect.top, data_rect.width, data_rect.height
        xmin, xmax = ax.transform.xlim
        ymin, ymax = ax.transform.ylim
        color = ax._grid_color[:3]
        lw = max(1, int(ax._grid_linewidth))
        off_l, off_t = self.ax_offset  # figure→axes-surface conversion

        xticks = (log_ticks(xmin, xmax) if ax._xscale == 'log'
                  else auto_ticks(xmin, xmax))
        for tick in xticks:
            sx = int(ax.transform.data_x_to_screen(tick)) - off_l
            if l <= sx <= l + w:
                pygame.draw.line(surface, color, (sx, t), (sx, t + h), lw)

        yticks = (log_ticks(ymin, ymax) if ax._yscale == 'log'
                  else auto_ticks(ymin, ymax))
        for tick in yticks:
            sy = int(ax.transform.data_y_to_screen(tick)) - off_t
            if t <= sy <= t + h:
                pygame.draw.line(surface, color, (l, sy), (l + w, sy), lw)

    def _draw_ticks(self, surface, data_rect) -> None:
        import pygame
        ax = self.ax
        l, t, w, h = data_rect.left, data_rect.top, data_rect.width, data_rect.height
        font = get_font('tick')
        black = (0, 0, 0)
        off_l, off_t = self.ax_offset  # figure→axes-surface conversion

        # X ticks
        xmin, xmax = ax.transform.xlim
        if ax._xticks_manual is not None:
            xticks = ax._xticks_manual
            xlabels = (ax._xtick_labels_manual
                       if ax._xtick_labels_manual else [str(v) for v in xticks])
        elif ax._xtick_labels is not None:
            # Categorical from bar()
            xticks = list(range(len(ax._xtick_labels)))
            xlabels = ax._xtick_labels
        elif ax._xscale == 'log':
            xticks = log_ticks(xmin, xmax)
            xlabels = [format_log_tick(t_) for t_ in xticks]
        else:
            xticks = auto_ticks(xmin, xmax)
            xlabels = format_ticks(xticks)

        for tick, lbl in zip(xticks, xlabels):
            sx = int(ax.transform.data_x_to_screen(tick)) - off_l
            if l <= sx <= l + w:
                pygame.draw.line(surface, black, (sx, t + h), (sx, t + h + _TICK_LEN))
                ts = font.render(str(lbl), True, black)
                surface.blit(ts, (sx - ts.get_width() // 2, t + h + _TICK_LEN + 2))

        # Y ticks
        ymin, ymax = ax.transform.ylim
        if ax._yticks_manual is not None:
            yticks = ax._yticks_manual
            ylabels = (ax._ytick_labels_manual
                       if ax._ytick_labels_manual else [str(v) for v in yticks])
        elif ax._ytick_labels_manual is not None:
            # Categorical from barh()
            yticks = list(range(len(ax._ytick_labels_manual)))
            ylabels = ax._ytick_labels_manual
        elif ax._yscale == 'log':
            yticks = log_ticks(ymin, ymax)
            ylabels = [format_log_tick(t_) for t_ in yticks]
        else:
            yticks = auto_ticks(ymin, ymax)
            ylabels = format_ticks(yticks)

        for tick, lbl in zip(yticks, ylabels):
            sy = int(ax.transform.data_y_to_screen(tick)) - off_t
            if t <= sy <= t + h:
                pygame.draw.line(surface, black, (l - _TICK_LEN, sy), (l, sy))
                ts = font.render(str(lbl), True, black)
                surface.blit(ts, (l - _TICK_LEN - ts.get_width() - 2,
                                   sy - ts.get_height() // 2))

    def _draw_labels(self, surface, data_rect) -> None:
        ax = self.ax
        l, t, w, h = data_rect.left, data_rect.top, data_rect.width, data_rect.height
        black = (0, 0, 0)

        if ax._title:
            ts = render_text(ax._title, 'title', black)
            surface.blit(ts, (l + w // 2 - ts.get_width() // 2, t - ts.get_height() - 4))

        if ax._xlabel:
            ts = render_text(ax._xlabel, 'label', black)
            surface.blit(ts, (l + w // 2 - ts.get_width() // 2,
                               t + h + _TICK_LEN + 14 + 2))

        if ax._ylabel:
            ts = render_text_rotated(ax._ylabel, 'label', black, 90.0)
            surface.blit(ts, (4, t + h // 2 - ts.get_height() // 2))

    def _draw_legend(self, surface, data_rect) -> None:
        import pygame
        ax = self.ax
        l, t, w, h = data_rect.left, data_rect.top, data_rect.width, data_rect.height
        font = get_font('legend')
        black = (0, 0, 0)

        # Collect labeled artists (deduplicate by label text)
        entries = []
        seen = set()

        def _add(kind, color, label):
            if label and not label.startswith('_') and label not in seen:
                entries.append((kind, color, label))
                seen.add(label)

        for line in ax.lines:
            _add('line', line.color[:3], line.label)
        for col in ax.collections:
            c = col.resolve_colors()
            _add('marker', tuple(int(v) for v in c[0, :3]), col.label)
        for patch in ax.patches:
            _add('rect', patch.facecolor[:3], patch.label)
        for eb in ax.errorbars:
            _add('line', eb.color[:3], eb.label)

        if not entries:
            return

        pad = 5
        swatch_w = 18
        row_h = font.get_height() + 4
        box_w = swatch_w + pad + max(font.size(e[2])[0] for e in entries) + pad * 2
        box_h = len(entries) * row_h + pad * 2

        # Position: upper right inside data area
        bx = l + w - box_w - pad
        by = t + pad

        # Semi-transparent background
        legend_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        legend_surf.fill((255, 255, 255, 200))
        pygame.draw.rect(legend_surf, (180, 180, 180), (0, 0, box_w, box_h), 1)

        for i, (kind, color, label) in enumerate(entries):
            ry = pad + i * row_h
            if kind == 'line':
                pygame.draw.line(legend_surf, color[:3],
                                 (pad, ry + row_h // 2),
                                 (pad + swatch_w, ry + row_h // 2), 2)
            elif kind == 'marker':
                draw_marker(legend_surf, (*color[:3], 255),
                            (pad + swatch_w // 2, ry + row_h // 2), 'o', 36)
            else:
                pygame.draw.rect(legend_surf, color[:3],
                                 (pad, ry + 2, swatch_w, row_h - 4))
            ts = font.render(label, True, black)
            legend_surf.blit(ts, (pad + swatch_w + pad, ry + 2))

        surface.blit(legend_surf, (bx, by))

    def _draw_colorbar(self, surface, cb_rect, img: 'AxesImage') -> None:
        data = img.data
        if data.ndim == 2:
            vmin = img.vmin if img.vmin is not None else float(data.min())
            vmax = img.vmax if img.vmax is not None else float(data.max())
            cmap = get_cmap(img.cmap_name)
            draw_colorbar_strip(surface, cb_rect, cmap, vmin, vmax)

    def _draw_tooltip(self, surface, hits: list[dict], pos: tuple[int, int]) -> None:
        import pygame
        if not hits:
            return
        hit = hits[0]
        txt = f"x={hit['x']:.4g}, y={hit['y']:.4g}"
        font = get_font('tooltip')
        ts = font.render(txt, True, (0, 0, 0))
        bx, by = pos[0] + 12, pos[1] - 20
        bw, bh = ts.get_width() + 8, ts.get_height() + 6
        # Keep on screen
        sw, sh = surface.get_size()
        bx = min(bx, sw - bw - 2)
        by = max(by, 2)
        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg.fill((255, 255, 220, 230))
        pygame.draw.rect(bg, (180, 180, 0), (0, 0, bw, bh), 1)
        bg.blit(ts, (4, 3))
        surface.blit(bg, (bx, by))
