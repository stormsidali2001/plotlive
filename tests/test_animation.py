"""Tests for FuncAnimation frame resolution, stepping, and export."""
import os
import tempfile
import pytest
import numpy as np

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from plotlive.figure import Figure
from plotlive.animation import FuncAnimation, _resolve_frames, _resolve_backend


# ── _resolve_frames ───────────────────────────────────────────────────────────

class TestResolveFrames:
    def test_none_defaults_to_100(self):
        frames = _resolve_frames(None, None)
        assert frames == list(range(100))

    def test_none_with_save_count(self):
        frames = _resolve_frames(None, 20)
        assert frames == list(range(20))

    def test_int(self):
        frames = _resolve_frames(30, None)
        assert frames == list(range(30))

    def test_list(self):
        vals = [0.1, 0.2, 0.3]
        frames = _resolve_frames(vals, None)
        assert frames == vals

    def test_numpy_linspace(self):
        vals = np.linspace(0, 1, 5).tolist()
        frames = _resolve_frames(list(np.linspace(0, 1, 5)), None)
        assert len(frames) == 5
        assert frames[0] == pytest.approx(0.0)
        assert frames[-1] == pytest.approx(1.0)

    def test_generator_function(self):
        def gen():
            yield from range(5)
        frames = _resolve_frames(gen, 3)
        assert frames == [0, 1, 2]


# ── _resolve_backend ──────────────────────────────────────────────────────────

class TestResolveBackend:
    def test_gif_extension(self):
        assert _resolve_backend('out.gif', None) == 'gif'

    def test_mp4_extension(self):
        assert _resolve_backend('out.mp4', None) == 'video'

    def test_mov_extension(self):
        assert _resolve_backend('out.mov', None) == 'video'

    def test_avi_extension(self):
        assert _resolve_backend('out.avi', None) == 'video'

    def test_writer_pillow(self):
        assert _resolve_backend('out.gif', 'pillow') == 'gif'

    def test_writer_ffmpeg(self):
        assert _resolve_backend('out.mp4', 'ffmpeg') == 'video'

    def test_writer_imageio(self):
        assert _resolve_backend('out.mp4', 'imageio') == 'video'

    def test_unknown_extension_raises(self):
        with pytest.raises(ValueError):
            _resolve_backend('out.xyz', None)


# ── FuncAnimation construction and frame stepping ─────────────────────────────

def make_anim(n_frames=10, repeat=True):
    fig = Figure(figsize=(4, 3))
    ax = fig.add_subplot(1, 1, 1)
    calls = []

    def update(frame):
        calls.append(frame)

    anim = FuncAnimation(fig, update, frames=n_frames, interval=100, repeat=repeat)
    return anim, calls


class TestFuncAnimation:
    def test_frame_count(self):
        anim, _ = make_anim(15)
        assert anim.frames == 15

    def test_frame_seq_is_range(self):
        anim, _ = make_anim(8)
        assert anim._frame_seq == list(range(8))

    def test_list_frames_passed_to_func(self):
        fig = Figure(figsize=(4, 3))
        ax = fig.add_subplot(1, 1, 1)
        received = []

        def update(frame):
            received.append(frame)

        vals = [0.5, 1.5, 2.5]
        anim = FuncAnimation(fig, update, frames=vals, interval=100)
        for i in range(len(vals)):
            anim._show_frame(i)
        assert received == vals

    def test_fargs_forwarded(self):
        fig = Figure(figsize=(4, 3))
        ax = fig.add_subplot(1, 1, 1)
        received = []

        def update(frame, multiplier):
            received.append(frame * multiplier)

        anim = FuncAnimation(fig, update, frames=3, interval=100, fargs=(10,))
        for i in range(3):
            anim._show_frame(i)
        assert received == [0, 10, 20]

    def test_step_forward(self):
        anim, calls = make_anim(5)
        anim._show_frame(0)     # display frame 0 first
        anim.step_forward()     # should advance to frame 1
        assert calls[-1] == 1
        assert anim._displayed_frame == 1

    def test_step_back(self):
        anim, calls = make_anim(5)
        anim._show_frame(3)
        anim.step_back()
        assert calls[-1] == 2
        assert anim._displayed_frame == 2

    def test_step_forward_at_end_returns_false(self):
        anim, _ = make_anim(3)
        anim._show_frame(2)    # last frame
        assert anim.step_forward() is False

    def test_step_back_clamps_to_zero(self):
        anim, calls = make_anim(3)
        anim._show_frame(0)
        anim.step_back()
        assert calls[-1] == 0
        assert anim._displayed_frame == 0

    def test_show_frame_clamps_high(self):
        anim, calls = make_anim(5)
        anim._show_frame(100)   # beyond end
        assert calls[-1] == 4   # clamped to last frame

    def test_show_frame_clamps_low(self):
        anim, calls = make_anim(5)
        anim._show_frame(-5)    # before start
        assert calls[-1] == 0   # clamped to first frame

    def test_on_timer_repeat(self):
        anim, calls = make_anim(3, repeat=True)
        anim._playing = True
        anim._next_frame = 0
        # Simulate advancing past the last frame
        for _ in range(4):
            anim._on_timer()
        # Should have wrapped around
        assert anim._next_frame == 1  # wrapped, then advanced once more
        assert not anim._finished

    def test_on_timer_no_repeat(self):
        import pygame
        if not pygame.get_init():
            pygame.init()
        anim, calls = make_anim(3, repeat=False)
        anim._playing = True
        anim._next_frame = 0
        for _ in range(4):
            anim._on_timer()
        assert anim._finished
        assert not anim._playing

    def test_dirty_flag_set_on_show_frame(self):
        fig = Figure(figsize=(4, 3))
        ax = fig.add_subplot(1, 1, 1)
        ax._dirty = False
        anim = FuncAnimation(fig, lambda f: None, frames=5)
        anim._show_frame(0)
        assert ax._dirty is True

    def test_save_gif(self):
        """Integration: save() produces a real GIF file."""
        import pygame
        if not pygame.get_init():
            pygame.init()

        fig = Figure(figsize=(3, 2))
        ax = fig.add_subplot(1, 1, 1)
        x = np.linspace(0, 1, 20)

        def update(frame):
            ax.cla()
            ax.plot(x, np.sin(x * frame * 0.5))

        anim = FuncAnimation(fig, update, frames=4, interval=200)
        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
            path = f.name
        try:
            anim.save(path, fps=4)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 1000  # not a blank stub
        finally:
            os.unlink(path)

    def test_progress_callback(self):
        import pygame
        if not pygame.get_init():
            pygame.init()

        fig = Figure(figsize=(3, 2))
        ax = fig.add_subplot(1, 1, 1)
        progress = []

        def update(frame):
            ax.cla()
            ax.plot([0, 1], [frame, frame])

        anim = FuncAnimation(fig, update, frames=4, interval=200)
        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
            path = f.name
        try:
            anim.save(path, fps=4, progress_callback=lambda c, t: progress.append((c, t)))
            assert len(progress) == 4
            assert progress[-1] == (4, 4)
        finally:
            os.unlink(path)

    def test_save_restores_to_frame_0(self):
        """After save(), animation state should be reset to frame 0."""
        import pygame
        if not pygame.get_init():
            pygame.init()

        fig = Figure(figsize=(3, 2))
        ax = fig.add_subplot(1, 1, 1)
        last_frame = []

        def update(frame):
            ax.cla()
            ax.plot([0, 1], [frame, frame + 1])
            last_frame.append(frame)

        anim = FuncAnimation(fig, update, frames=4, interval=200)
        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
            path = f.name
        try:
            anim.save(path, fps=4)
            # Last call is frame 0 (restore)
            assert last_frame[-1] == 0
        finally:
            os.unlink(path)
