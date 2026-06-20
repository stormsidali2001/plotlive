from __future__ import annotations
import math


def auto_ticks(vmin: float, vmax: float, max_ticks: int = 8) -> list[float]:
    """Generate clean tick positions using a nice-step algorithm."""
    if vmin == vmax:
        return [vmin]

    span = vmax - vmin
    if span == 0:
        return [vmin]

    mag = math.floor(math.log10(abs(span)))
    norm = span / 10**mag

    nice_steps = [1, 2, 2.5, 5, 10]
    for ns in nice_steps:
        step = ns * 10**(mag - 1)
        snap_min = math.ceil(vmin / step) * step
        ticks = []
        t = snap_min
        while t <= vmax + step * 1e-9:
            # Round to avoid float drift
            rounded = round(t / step) * step
            if vmin - step * 1e-9 <= rounded <= vmax + step * 1e-9:
                ticks.append(rounded)
            t += step
        if 3 <= len(ticks) <= max_ticks:
            return _clean(ticks, step)

    # Fallback: 5 evenly spaced
    step = span / 4
    ticks = [vmin + i * step for i in range(5)]
    return _clean(ticks, step)


def _clean(ticks: list[float], step: float) -> list[float]:
    """Remove float noise close to zero."""
    result = []
    for t in ticks:
        if abs(t) < step * 1e-9:
            t = 0.0
        result.append(t)
    return result


def format_tick(value: float, step: float) -> str:
    """Format a tick label based on the step size."""
    if value == 0.0:
        return '0'
    if step == 0:
        return str(value)

    abs_step = abs(step)
    if abs_step >= 1.0:
        if value == int(value):
            return str(int(value))
        return f'{value:.1f}'
    if abs_step >= 0.1:
        return f'{value:.1f}'
    if abs_step >= 0.01:
        return f'{value:.2f}'
    if abs_step >= 0.001:
        return f'{value:.3f}'
    # Scientific notation
    return f'{value:.2e}'


def format_ticks(ticks: list[float]) -> list[str]:
    """Format a full list of ticks, inferring step from the list."""
    if len(ticks) < 2:
        step = abs(ticks[0]) if ticks else 1.0
    else:
        step = abs(ticks[1] - ticks[0])
    return [format_tick(t, step) for t in ticks]


def log_ticks(vmin: float, vmax: float) -> list[float]:
    """Generate tick positions for a log-scale axis (powers of 10, plus 2× and 5× per decade)."""
    if vmin <= 0 or vmax <= 0 or vmin >= vmax:
        return []
    import math
    lmin = math.floor(math.log10(vmin))
    lmax = math.ceil(math.log10(vmax))
    n_decades = lmax - lmin

    # Decade-only ticks for wide ranges; add 2× and 5× for narrow ones
    multipliers = [1] if n_decades > 4 else [1, 2, 5]
    ticks = []
    for e in range(lmin, lmax + 1):
        for m in multipliers:
            v = m * 10.0 ** e
            if vmin <= v <= vmax:
                ticks.append(v)
    return sorted(set(ticks)) if ticks else [vmin, vmax]


def format_log_tick(value: float) -> str:
    """Format a single log-scale tick label."""
    import math
    if value <= 0:
        return str(value)
    exp = math.log10(value)
    if abs(exp - round(exp)) < 1e-9:
        e = int(round(exp))
        if -3 <= e <= 4:
            # Plain number: 0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000
            v = 10 ** e
            return str(v) if v >= 1 else f'{v:g}'
        return f'1e{e}'
    return f'{value:g}'
