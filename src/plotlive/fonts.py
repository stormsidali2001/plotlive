"""
Font loading with a three-level fallback:
  1. Bundled FreeSansBold.ttf (copied from pygame-ce, Apache 2.0)
  2. pygame SysFont (OS-level)
  3. pygame built-in default (None path)
"""
from __future__ import annotations
import functools
from pathlib import Path

_DATA_DIR = Path(__file__).parent / 'data'
_BUNDLED_BOLD = str(_DATA_DIR / 'FreeSansBold.ttf')

_ROLE_SIZES: dict[str, tuple[str | None, int]] = {
    'tick':     (_BUNDLED_BOLD, 11),
    'label':    (_BUNDLED_BOLD, 13),
    'title':    (_BUNDLED_BOLD, 14),
    'legend':   (_BUNDLED_BOLD, 11),
    'tooltip':  (_BUNDLED_BOLD, 10),
    'suptitle': (_BUNDLED_BOLD, 16),
}


def _ensure_init():
    import pygame
    if not pygame.font.get_init():
        pygame.font.init()


def _make_font(path: str | None, size: int):
    """Create a pygame Font with fallback to default."""
    import pygame
    _ensure_init()
    if path and Path(path).exists():
        try:
            f = pygame.font.Font(path, size)
            # Validate by doing a test render
            f.render('a', True, (0, 0, 0))
            return f
        except Exception:
            pass
    # Fallback to SysFont
    for name in ('freesans', 'arial', 'helvetica', 'sans'):
        try:
            f = pygame.font.SysFont(name, size)
            f.render('a', True, (0, 0, 0))
            return f
        except Exception:
            continue
    # Final fallback: pygame built-in
    return pygame.font.Font(None, size)


@functools.lru_cache(maxsize=64)
def get_font(role: str = 'tick', size_override: int | None = None):
    """Return a cached font for the given role."""
    path, size = _ROLE_SIZES.get(role, _ROLE_SIZES['tick'])
    if size_override is not None:
        size = size_override
    return _make_font(path, size)


def render_text(text: str, role: str, color: tuple):
    """Render text to a pygame Surface."""
    font = get_font(role)
    return font.render(text, True, color[:3])


def render_text_rotated(text: str, role: str, color: tuple, angle: float = 90.0):
    """Render text rotated by angle degrees."""
    import pygame
    surf = render_text(text, role, color)
    return pygame.transform.rotate(surf, angle)
