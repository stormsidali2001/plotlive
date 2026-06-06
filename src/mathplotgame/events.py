from __future__ import annotations
import time


ZOOM_IN  = 0.85
ZOOM_OUT = 1.0 / 0.85
_DBL_CLICK = 0.35  # seconds

_HELP_LINES = [
    ('?  /  H',      'Show / hide this help panel'),
    ('Space',        'Play / pause animation'),
    ('-> Right arrow', 'Step forward one frame  (while paused)'),
    ('<- Left arrow',  'Step back one frame     (while paused)'),
    ('Scroll up',    'Zoom in  (centered on cursor)'),
    ('Scroll down',  'Zoom out (centered on cursor)'),
    ('Drag',         'Pan the view'),
    ('Double-click', 'Focus subplot  (multi-plot)  /  Reset zoom (single plot)'),
    ('Esc',          'Exit focus mode'),
    ('R',            'Reset zoom / pan  +  restart animation'),
    ('S',            'Save current frame as frame_NNNN.png'),
    ('?  /  H  /  Esc', 'Close this panel'),
]


class InteractionState:
    """Tracks interactive input. Mutates Axes.transform on pan/zoom events."""

    def __init__(self, figure):
        self.figure = figure
        self._pan_active: bool = False
        self._pan_last_pos: tuple[int, int] | None = None
        self._active_ax = None
        self._hover_pos: tuple[int, int] | None = None
        self._last_click_time: float = 0.0
        self.show_help: bool = False

    def _find_ax_at(self, sx: int, sy: int):
        # In focus mode all interaction targets the focused subplot
        if self.figure._focused_ax is not None:
            return self.figure._focused_ax
        for ax in self.figure.axes:
            if ax.transform.contains_screen_point(sx, sy):
                return ax
        return None

    def handle_event(self, event, screen=None) -> bool:
        """
        Process one pygame event. Returns True if a redraw is needed.
        screen is the pygame display surface, used for saving frames.
        """
        import pygame
        dirty = False
        anim = self.figure._animation

        # While help is open, only allow keys that close it
        if self.show_help:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_h,
                                 pygame.K_SLASH, pygame.K_QUESTION):
                    self.show_help = False
                    dirty = True
            return dirty

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            ax = self._find_ax_at(*event.pos)
            if ax:
                self._active_ax = ax
                self._pan_active = True
                self._pan_last_pos = event.pos
                now = time.monotonic()
                if now - self._last_click_time < _DBL_CLICK:
                    if self.figure._focused_ax is not None:
                        # Exit focus mode
                        self.figure._focused_ax = None
                        dirty = True
                    elif len(self.figure.axes) > 1:
                        # Enter focus mode on the clicked subplot
                        self.figure._focused_ax = ax
                        dirty = True
                    else:
                        # Single-axes figure: keep the original reset-to-home
                        ax.transform.reset_to_home()
                        dirty = True
                self._last_click_time = now

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._pan_active = False
            self._pan_last_pos = None

        elif event.type == pygame.MOUSEMOTION:
            self._hover_pos = event.pos
            if self._pan_active and self._pan_last_pos and self._active_ax:
                dx = event.pos[0] - self._pan_last_pos[0]
                dy = event.pos[1] - self._pan_last_pos[1]
                self._active_ax.transform.pan(dx, dy)
                self._pan_last_pos = event.pos
                dirty = True
            dirty = True

        elif event.type == pygame.MOUSEWHEEL:
            ax = self._find_ax_at(*pygame.mouse.get_pos())
            if ax:
                factor = ZOOM_IN if event.y > 0 else ZOOM_OUT
                mx, my = pygame.mouse.get_pos()
                ax.transform.zoom(mx, my, factor)
                dirty = True

        elif event.type == pygame.KEYDOWN:
            key = event.key

            # Exit focus mode
            if key == pygame.K_ESCAPE and self.figure._focused_ax is not None:
                self.figure._focused_ax = None
                dirty = True

            # Help panel
            elif key in (pygame.K_h, pygame.K_SLASH, pygame.K_QUESTION):
                self.show_help = True
                dirty = True

            # View reset + animation restart
            elif key == pygame.K_r:
                ax = self.figure._focused_ax or self._active_ax or (self.figure.axes[0] if self.figure.axes else None)
                if ax:
                    ax.transform.reset_to_home()
                    dirty = True
                if anim:
                    anim.pause()
                    anim._finished = False
                    anim._next_frame = 0
                    dirty |= anim._show_frame(0)

            # Animation: play/pause toggle
            elif key == pygame.K_SPACE:
                if anim:
                    anim.toggle()
                    dirty = True

            # Animation: step forward one frame
            elif key == pygame.K_RIGHT:
                if anim and not anim._playing:
                    dirty = anim.step_forward()

            # Animation: step back one frame
            elif key == pygame.K_LEFT:
                if anim and not anim._playing:
                    dirty = anim.step_back()

            # Save current frame as PNG
            elif key == pygame.K_s:
                if screen is not None:
                    _save_frame(screen, anim)

        return dirty

    def get_hover_hits(self) -> list[dict]:
        if not self._hover_pos:
            return []
        ax = self._find_ax_at(*self._hover_pos)
        if not ax:
            return []
        return ax.hit_test(*self._hover_pos)


def draw_help_overlay(surface) -> None:
    """Draw a centred help panel over the current surface."""
    import pygame
    from .fonts import get_font

    sw, sh = surface.get_size()
    font_key  = get_font('label')
    font_title = get_font('title')

    pad   = 20
    row_h = font_key.get_height() + 6
    col_gap = 24

    # Measure columns
    key_w = max(font_key.size(k)[0] for k, _ in _HELP_LINES)
    val_w = max(font_key.size(v)[0] for _, v in _HELP_LINES)
    title_surf = font_title.render('Keyboard shortcuts', True, (255, 255, 255))

    box_w = pad + key_w + col_gap + val_w + pad
    box_h = pad + title_surf.get_height() + 10 + len(_HELP_LINES) * row_h + pad

    bx = (sw - box_w) // 2
    by = (sh - box_h) // 2

    # Dim background
    dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    surface.blit(dim, (0, 0))

    # Panel background
    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    panel.fill((30, 30, 30, 230))
    pygame.draw.rect(panel, (100, 100, 100), (0, 0, box_w, box_h), 1)
    surface.blit(panel, (bx, by))

    # Title
    surface.blit(title_surf, (bx + (box_w - title_surf.get_width()) // 2, by + pad))
    ty = by + pad + title_surf.get_height() + 10

    # Separator line
    pygame.draw.line(surface, (80, 80, 80),
                     (bx + pad, ty - 4), (bx + box_w - pad, ty - 4))

    # Rows
    for key_text, val_text in _HELP_LINES:
        ks = font_key.render(key_text, True, (255, 200, 60))
        vs = font_key.render(val_text, True, (200, 200, 200))
        surface.blit(ks, (bx + pad, ty))
        surface.blit(vs, (bx + pad + key_w + col_gap, ty))
        ty += row_h

    # Dismiss hint
    hint = get_font('tooltip').render('Press  ?  H  or  Esc  to close', True, (130, 130, 130))
    surface.blit(hint, (bx + (box_w - hint.get_width()) // 2, ty + 6))


def _save_frame(screen, anim) -> None:
    import pygame
    frame_num = anim._displayed_frame if anim and anim._displayed_frame >= 0 else 0
    filename = f'frame_{frame_num:04d}.png'
    pygame.image.save(screen, filename)
    print(f'Saved {filename}')
