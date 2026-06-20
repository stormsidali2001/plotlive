from __future__ import annotations
import math
import numpy as np

_LINESTYLE_PATTERNS: dict[str, list[int] | None] = {
    '-': None, 'solid': None,
    '--': [8, 4], 'dashed': [8, 4],
    '-.': [8, 4, 2, 4], 'dashdot': [8, 4, 2, 4],
    ':': [2, 3], 'dotted': [2, 3],
    'None': None, 'none': None, '': None,
}


def draw_dashed_polyline(
    surface,
    color: tuple,
    points: list[tuple[float, float]],
    linewidth: int = 1,
    linestyle: str = '-',
) -> None:
    """Draw a polyline with optional dash pattern on a pygame Surface."""
    import pygame

    # Filter out NaN-split segments
    segments = _split_nan(points)
    pattern = _LINESTYLE_PATTERNS.get(linestyle, None)

    for seg in segments:
        if len(seg) < 2:
            continue
        ipts = [(int(round(p[0])), int(round(p[1]))) for p in seg]

        if pattern is None:
            if linestyle in ('None', 'none', ''):
                continue
            # Solid anti-aliased
            if linewidth <= 1:
                pygame.draw.aalines(surface, color[:3], False, ipts)
            else:
                pygame.draw.lines(surface, color[:3], False, ipts, linewidth)
        else:
            _draw_dashed(surface, color[:3], seg, pattern, linewidth)


def _draw_dashed(surface, color, points, pattern, linewidth):
    import pygame
    pat_idx = 0
    draw = True
    remaining = pattern[0]

    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        seg_len = math.hypot(x1 - x0, y1 - y0)
        if seg_len == 0:
            continue
        dx, dy = (x1 - x0) / seg_len, (y1 - y0) / seg_len
        dist = 0.0

        while dist < seg_len:
            chunk = min(remaining, seg_len - dist)
            ex = x0 + dx * (dist + chunk)
            ey = y0 + dy * (dist + chunk)
            if draw:
                sx, sy = x0 + dx * dist, y0 + dy * dist
                pygame.draw.line(surface, color,
                                 (int(round(sx)), int(round(sy))),
                                 (int(round(ex)), int(round(ey))),
                                 max(1, linewidth))
            dist += chunk
            remaining -= chunk
            if remaining <= 0:
                pat_idx = (pat_idx + 1) % len(pattern)
                draw = not draw
                remaining = pattern[pat_idx]


def _split_nan(points):
    segments = []
    current = []
    for p in points:
        if math.isnan(p[0]) or math.isnan(p[1]):
            if current:
                segments.append(current)
            current = []
        else:
            current.append(p)
    if current:
        segments.append(current)
    return segments


def draw_marker(surface, color: tuple, pos: tuple[float, float],
                marker: str, size: float) -> None:
    """Draw a single marker at pos."""
    import pygame
    x, y = int(round(pos[0])), int(round(pos[1]))
    r = max(2, round(math.sqrt(max(size, 1)) / 1.5))
    c = color[:3]

    if marker == 'o':
        pygame.draw.circle(surface, c, (x, y), r)
    elif marker == 's':
        pygame.draw.rect(surface, c, (x - r, y - r, 2*r, 2*r))
    elif marker == '^':
        pts = [(x, y - r), (x - r, y + r), (x + r, y + r)]
        pygame.draw.polygon(surface, c, pts)
    elif marker == 'v':
        pts = [(x, y + r), (x - r, y - r), (x + r, y - r)]
        pygame.draw.polygon(surface, c, pts)
    elif marker == '<':
        pts = [(x - r, y), (x + r, y - r), (x + r, y + r)]
        pygame.draw.polygon(surface, c, pts)
    elif marker == '>':
        pts = [(x + r, y), (x - r, y - r), (x - r, y + r)]
        pygame.draw.polygon(surface, c, pts)
    elif marker == 'D':
        pts = [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]
        pygame.draw.polygon(surface, c, pts)
    elif marker == '+':
        pygame.draw.line(surface, c, (x - r, y), (x + r, y), 1)
        pygame.draw.line(surface, c, (x, y - r), (x, y + r), 1)
    elif marker == 'x':
        pygame.draw.line(surface, c, (x - r, y - r), (x + r, y + r), 1)
        pygame.draw.line(surface, c, (x + r, y - r), (x - r, y + r), 1)
    elif marker == '.':
        pygame.draw.circle(surface, c, (x, y), max(1, r // 2))
    elif marker == '*':
        # 6-point star approximated as two overlapping triangles
        pts1 = [(x, y - r), (x - r, y + r//2), (x + r, y + r//2)]
        pts2 = [(x, y + r), (x - r, y - r//2), (x + r, y - r//2)]
        pygame.draw.polygon(surface, c, pts1)
        pygame.draw.polygon(surface, c, pts2)
    else:
        # Default: circle
        pygame.draw.circle(surface, c, (x, y), r)


def draw_colorbar_strip(surface, rect, cmap, vmin: float, vmax: float,
                         n_ticks: int = 5) -> None:
    """Draw a vertical colorbar strip in rect with tick labels to the right."""
    import pygame
    from .ticks import auto_ticks, format_ticks
    from .fonts import get_font

    l, t, w, h = rect.left, rect.top, rect.width, rect.height
    bar_w = max(12, w // 3)

    # Draw the color gradient strip
    lut = cmap.to_lut(h)
    for i in range(h):
        # top of strip = vmax, bottom = vmin (reverse for screen coords)
        color = tuple(int(v) for v in lut[h - 1 - i, :3])
        pygame.draw.line(surface, color, (l, t + i), (l + bar_w, t + i))

    # Border
    pygame.draw.rect(surface, (0, 0, 0), (l, t, bar_w, h), 1)

    # Ticks and labels
    ticks = auto_ticks(vmin, vmax, max_ticks=n_ticks)
    labels = format_ticks(ticks)
    font = get_font('tick')
    for tick, label in zip(ticks, labels):
        frac = (tick - vmin) / (vmax - vmin) if vmax != vmin else 0.5
        sy = t + h - int(frac * h)
        pygame.draw.line(surface, (0, 0, 0), (l + bar_w, sy), (l + bar_w + 3, sy), 1)
        txt_surf = font.render(label, True, (0, 0, 0))
        surface.blit(txt_surf, (l + bar_w + 5, sy - txt_surf.get_height() // 2))
