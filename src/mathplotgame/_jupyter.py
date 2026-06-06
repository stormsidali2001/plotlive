"""
mathplotgame._jupyter — inline display helpers for Jupyter notebooks.

This module is imported lazily inside pyplot.show() only when a Jupyter
kernel is detected, so it never affects the normal pygame path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .figure import Figure


def is_jupyter() -> bool:
    """Return True when running inside a Jupyter notebook (not terminal IPython)."""
    try:
        from IPython import get_ipython  # type: ignore[import]
        ip = get_ipython()
        return ip is not None and type(ip).__name__ == 'ZMQInteractiveShell'
    except Exception:
        return False


def show_figure(fig: Figure) -> None:
    """Render figure as PNG and display it inline via IPython."""
    import pygame
    import tempfile
    import os
    from IPython.display import display, Image  # type: ignore[import]
    from .renderer import FigureRenderer

    if not pygame.get_init():
        pygame.init()

    surf = FigureRenderer(fig).render()
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            tmp = f.name
        pygame.image.save(surf, tmp)
        with open(tmp, 'rb') as f:
            png_data = f.read()
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    display(Image(data=png_data, format='png'))


def show_animation(fig: Figure, set_current_fig) -> None:
    """Export animation as GIF (or MP4 fallback) and display it inline via IPython.

    set_current_fig is a callable(fig) that updates pyplot's global state so
    that gcf()/gca() resolve correctly inside state-machine update functions.
    """
    import pygame
    import tempfile
    import os
    from IPython.display import display  # type: ignore[import]

    if not pygame.get_init():
        pygame.init()

    # Keep gcf()/gca() pointing at this figure while frames are rendered
    set_current_fig(fig)

    anim = fig._animation
    if anim is None:
        return

    # --- GIF via Pillow (preferred: self-contained, works everywhere) ---
    try:
        import PIL  # noqa: F401 — availability check only
        from IPython.display import Image  # type: ignore[import]
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
                tmp = f.name
            anim.save(tmp, writer='pillow')
            with open(tmp, 'rb') as f:
                gif_data = f.read()
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
        display(Image(data=gif_data, format='gif'))
        return
    except ImportError:
        pass

    # --- MP4 via imageio + ffmpeg (fallback) ---
    try:
        import imageio  # noqa: F401
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                tmp = f.name
            anim.save(tmp, writer='ffmpeg')
            with open(tmp, 'rb') as f:
                video_data = f.read()
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
        import base64
        from IPython.display import HTML  # type: ignore[import]
        b64 = base64.b64encode(video_data).decode('ascii')
        display(HTML(
            f'<video controls style="max-width:100%">'
            f'<source type="video/mp4" src="data:video/mp4;base64,{b64}">'
            f'</video>'
        ))
        return
    except (ImportError, Exception):
        pass

    # --- Last resort: first frame as static image ---
    anim._call_func(0)
    for ax in fig.axes:
        ax._dirty = True
    show_figure(fig)
