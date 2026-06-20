from __future__ import annotations
import numpy as np

_MARKERS = set('os^v<>Dp+x.*phH1234')
# Order matters: parse multi-char linestyles before single-char
_LINESTYLES = ['-.', '--', '-', ':']
_LS_MARKERS = set('-')  # chars that could be either linestyle or marker start


def _parse_fmt(fmt: str) -> dict:
    """
    Parse matplotlib format string like 'b--o' into property dict.
    Returns subset of: color, linestyle, marker.
    """
    if not fmt:
        return {}

    result: dict = {}
    s = fmt

    # Extract linestyle first (multi-char before single-char)
    for ls in _LINESTYLES:
        if ls in s:
            result['linestyle'] = ls
            s = s.replace(ls, '', 1)
            break

    # Remaining characters: color and/or marker
    color_chars = set('brgykwmc')
    for ch in list(s):
        if ch in color_chars and 'color' not in result:
            result['color'] = ch
        elif ch in _MARKERS and 'marker' not in result:
            result['marker'] = ch

    return result


def _parse_plot_args(args: tuple) -> list[tuple[np.ndarray, np.ndarray, str]]:
    """
    Parse positional args to plot() into list of (x, y, fmt) tuples.

    Patterns:
      (y,)           -> (arange(len(y)), y, '')
      (y, fmt)       -> (arange(len(y)), y, fmt)  if fmt is str
      (x, y)         -> (x, y, '')
      (x, y, fmt)    -> (x, y, fmt)
      (x, y, fmt, x2, y2, fmt2, ...) -> multiple
    """
    segments: list[tuple[np.ndarray, np.ndarray, str]] = []
    i = 0
    args_list = list(args)

    while i < len(args_list):
        a0 = args_list[i]

        # Detect string (format) at position i
        if isinstance(a0, str):
            raise ValueError(f"Unexpected string argument at position {i}: {a0!r}")

        x0 = np.asarray(a0, dtype=float)

        if i + 1 >= len(args_list):
            # Only one array: treat as y
            segments.append((np.arange(len(x0), dtype=float), x0, ''))
            i += 1
            continue

        a1 = args_list[i + 1]

        if isinstance(a1, str):
            # (y, fmt)
            segments.append((np.arange(len(x0), dtype=float), x0, a1))
            i += 2
            continue

        # a1 is array-like: (x, y, ...)
        y0 = np.asarray(a1, dtype=float)

        if i + 2 < len(args_list) and isinstance(args_list[i + 2], str):
            fmt = args_list[i + 2]
            segments.append((x0, y0, fmt))
            i += 3
        else:
            segments.append((x0, y0, ''))
            i += 2

    return segments
