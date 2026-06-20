from __future__ import annotations

import inspect
from typing import Callable

_ANIMATION_EVENT_ID = None


def _get_animation_event():
    global _ANIMATION_EVENT_ID
    if _ANIMATION_EVENT_ID is None:
        import pygame
        _ANIMATION_EVENT_ID = pygame.USEREVENT + 1
    return _ANIMATION_EVENT_ID


# ------------------------------------------------------------------
# Export helpers
# ------------------------------------------------------------------

def _surf_to_array(surf):
    """pygame Surface → (H, W, 3) uint8 numpy array."""
    import pygame
    import numpy as np
    arr = pygame.surfarray.array3d(surf)        # (W, H, 3)
    return np.ascontiguousarray(arr.transpose(1, 0, 2))  # (H, W, 3)


def _save_gif(arrays: list, filename: str, fps: int) -> None:
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            'GIF export requires Pillow:\n'
            '  pip install Pillow'
        )
    duration_ms = max(20, int(1000 / fps))
    imgs = [Image.fromarray(arr) for arr in arrays]
    imgs[0].save(
        filename,
        save_all=True,
        append_images=imgs[1:],
        loop=0,
        duration=duration_ms,
        optimize=False,
    )


def _save_video(arrays: list, filename: str, fps: int) -> None:
    try:
        import imageio
    except ImportError:
        raise ImportError(
            'Video export requires imageio:\n'
            '  pip install imageio[ffmpeg]'
        )
    with imageio.get_writer(filename, fps=fps) as writer:
        for arr in arrays:
            writer.append_data(arr)


def _resolve_backend(filename: str, writer) -> str:
    """Return 'gif' or 'video', inferring from writer name and file extension."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if isinstance(writer, str):
        if writer == 'pillow':
            return 'gif'
        if writer in ('ffmpeg', 'ffmpeg_file', 'imageio'):
            return 'video'
    if ext == 'gif':
        return 'gif'
    if ext in ('mp4', 'mov', 'avi', 'webm'):
        return 'video'
    raise ValueError(
        f'Unknown format ".{ext}". '
        'Supported extensions: .gif  .mp4  .mov  .avi'
    )


def _resolve_frames(frames, save_count) -> list:
    """Convert matplotlib-style frames arg to a concrete list of frame values."""
    if frames is None:
        n = save_count if save_count is not None else 100
        return list(range(n))
    if isinstance(frames, int):
        return list(range(frames))
    if inspect.isgeneratorfunction(frames):
        gen = frames()
        if save_count is not None:
            return [next(gen) for _ in range(save_count)]
        return list(gen)
    return list(frames)


class FuncAnimation:
    """
    matplotlib-compatible animation driven by a user-supplied function.

    Matches the ``matplotlib.animation.FuncAnimation`` interface exactly::

        from plotlive.animation import FuncAnimation
        anim = FuncAnimation(fig, update, frames=50, interval=200)
        anim.save('output.gif')

    Animations start **paused** — press Space to play, ←/→ to step.
    """

    def __init__(
        self,
        fig,
        func: Callable,
        frames=None,
        init_func=None,
        fargs=None,
        save_count: int | None = None,
        *,
        cache_frame_data: bool = True,
        interval: int = 200,
        repeat_delay: int = 0,
        repeat: bool = True,
        blit: bool = False,
    ):
        self.figure = fig
        self._func = func
        self._fargs = tuple(fargs) if fargs is not None else ()
        self.interval = interval
        self.repeat = repeat

        self._frame_seq = _resolve_frames(frames, save_count)
        self.frames = len(self._frame_seq)

        self._displayed_frame: int = -1
        self._next_frame: int = 0
        self._playing: bool = False
        self._finished: bool = False

    def _call_func(self, i: int) -> None:
        frame = self._frame_seq[i]
        if self._fargs:
            self._func(frame, *self._fargs)
        else:
            self._func(frame)

    @property
    def event_id(self) -> int:
        return _get_animation_event()

    # ------------------------------------------------------------------
    # Playback control
    # ------------------------------------------------------------------

    def start(self) -> None:
        import pygame
        self._playing = True
        self._finished = False
        pygame.time.set_timer(self.event_id, self.interval)

    def pause(self) -> None:
        import pygame
        self._playing = False
        pygame.time.set_timer(self.event_id, 0)

    def resume(self) -> None:
        if not self._finished:
            self.start()

    def toggle(self) -> None:
        if self._playing:
            self.pause()
        else:
            self.resume()

    # ------------------------------------------------------------------
    # Frame rendering
    # ------------------------------------------------------------------

    def _show_frame(self, n: int) -> bool:
        n = max(0, min(n, self.frames - 1))
        self._call_func(n)
        self._displayed_frame = n
        self._next_frame = n + 1
        for ax in self.figure.axes:
            ax._dirty = True
        return True

    def step_forward(self) -> bool:
        next_n = self._displayed_frame + 1
        if next_n >= self.frames:
            return False
        return self._show_frame(next_n)

    def step_back(self) -> bool:
        prev_n = max(0, self._displayed_frame - 1) if self._displayed_frame >= 0 else 0
        return self._show_frame(prev_n)

    # ------------------------------------------------------------------
    # Export — matches matplotlib's Animation.save() signature
    # ------------------------------------------------------------------

    def save(
        self,
        filename: str,
        writer=None,
        fps: int | None = None,
        dpi: float | None = None,
        codec: str | None = None,
        bitrate: int | None = None,
        extra_args=None,
        metadata: dict | None = None,
        extra_anim=None,
        savefig_kwargs: dict | None = None,
        *,
        progress_callback=None,
    ) -> None:
        """
        Render all frames off-screen and write to *filename*.

        Matches ``matplotlib.animation.Animation.save()``::

            anim.save('output.gif', writer='pillow', fps=10)
            anim.save('output.mp4', writer='ffmpeg', fps=30)
            anim.save('output.gif')   # writer and fps inferred automatically

        Requirements:
          GIF   — pip install Pillow
          Video — pip install imageio[ffmpeg]
        """
        import pygame
        from .renderer import FigureRenderer

        if not pygame.get_init():
            pygame.init()

        backend = _resolve_backend(filename, writer)  # raises early for bad ext
        effective_fps = fps if fps is not None else max(1, 1000 // self.interval)

        print(f'Exporting {self.frames} frames → {filename}')
        arrays = []
        _step = max(1, self.frames // 10)
        for i in range(self.frames):
            self._call_func(i)
            surf = FigureRenderer(self.figure).render()
            arrays.append(_surf_to_array(surf))
            if progress_callback is not None:
                progress_callback(i + 1, self.frames)
            if (i + 1) % _step == 0 or i == self.frames - 1:
                print(f'  {i + 1}/{self.frames}')

        self._call_func(0)  # restore to frame 0 so show() opens at the start

        if backend == 'gif':
            _save_gif(arrays, filename, effective_fps)
        else:
            _save_video(arrays, filename, effective_fps)
        print(f'Saved → {filename}')

    # ------------------------------------------------------------------
    # Timer callback (called by the pygame event loop in pyplot.show())
    # ------------------------------------------------------------------

    def _on_timer(self) -> bool:
        if not self._playing or self._finished:
            return False

        self._show_frame(self._next_frame)

        if self._next_frame >= self.frames:
            if self.repeat:
                self._next_frame = 0
                self._displayed_frame = -1
            else:
                self._finished = True
                self.pause()

        return True


# Alias so existing code using Animation still works
Animation = FuncAnimation
