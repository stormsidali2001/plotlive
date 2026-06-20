# How plotlive works

plotlive is a thin layer that lets you write standard matplotlib code and get an interactive pygame window instead of a static image. This post walks through every major architectural decision — why each layer exists, how the pieces fit together, and where the tricky parts live.

---

## The goal in one sentence

Run this matplotlib code:

```python
import plotlive.pyplot as plt
plt.plot([1, 2, 3], [4, 5, 6], label='data')
plt.legend()
plt.show()
```

And get a live window where you can scroll to zoom, drag to pan, and hover to read data values off the line.

The constraint is that the library must not depend on matplotlib itself. It reimplements just enough of the API to cover the plots data scientists actually reach for during EDA and ML tutorials.

---

## Layer map

```
┌─────────────────────────────────────────────────────┐
│  pyplot.py   — state machine (plt.plot, plt.show)   │
├─────────────────────────────────────────────────────┤
│  Figure / Axes  — data model                        │
│    artists.py   — Line2D, Rectangle, Polygon, …     │
│    transform.py — data ↔ screen math                │
├─────────────────────────────────────────────────────┤
│  renderer.py  — all pygame draw calls               │
├─────────────────────────────────────────────────────┤
│  events.py    — pan / zoom / keyboard               │
│  animation.py — timer-driven frame loop             │
└─────────────────────────────────────────────────────┘
           ↓
      pygame-ce + numpy
```

Each layer has a single job. Artists store data. The transform does math. The renderer draws. Events mutate state. Nothing bleeds across.

---

## Artists: data only, no drawing

Every plot call creates one or more **artist** objects and pushes them into typed lists on the Axes:

```
ax.lines        → list[Line2D]
ax.collections  → list[PathCollection]   (scatter)
ax.patches      → list[Rectangle | Polygon]
ax.images       → list[AxesImage]
ax.errorbars    → list[ErrorBar]
```

An artist is a pure data container. `Line2D` knows its x/y arrays, color, linewidth, and linestyle — nothing more. It never touches pygame. All drawing happens in the renderer, which visits each list in order.

This separation means animations are trivial: `plt.cla()` empties the lists, `update_fn(frame)` rebuilds them, and the renderer draws the new state. The renderer doesn't know or care whether the frame changed.

**Why typed lists instead of a single artist list?** Because the render order matters for visual correctness: images first, then filled polygons, then rectangles, then point collections, then lines on top, then error bars last. Keeping them in separate lists makes the order explicit and avoids an isinstance chain on every render.

---

## Transform: the single source of truth for coordinates

`Transform` owns all zoom/pan state and all coordinate math. There is one Transform per Axes.

```python
class Transform:
    xlim: tuple[float, float]   # current data extent
    ylim: tuple[float, float]
    axes_rect: tuple[int, int, int, int]  # (left, top, w, h) in screen pixels
    xscale: str  # 'linear' | 'log'
    yscale: str
```

The forward transform maps data coordinates to screen pixels:

```python
def data_to_screen(self, x, y):
    sx = left + self._x_norm(x) * width
    sy = top + height - self._y_norm(y) * height  # Y flip
    return sx, sy
```

The Y flip is the most important invariant in the system. Screen Y increases downward; data Y increases upward. The flip lives in exactly one place — `data_to_screen` — and nowhere else. Duplicating it anywhere would cause subtle, hard-to-find bugs.

### Zoom

Zoom is anchored to the cursor position:

```python
def zoom(self, sx, sy, factor):
    cx, cy = self.screen_to_data(sx, sy)   # anchor in data coords
    self.xlim = (cx - (cx - xmin) * factor, cx + (xmax - cx) * factor)
    self.ylim = (cy - (cy - ymin) * factor, cy + (ymax - cy) * factor)
```

Converting the cursor to data coordinates first is essential. If you scale `xlim` around its center instead of the cursor, the point under the cursor drifts as you zoom — a disorienting and wrong behaviour.

### Log scale

Log scale changes how `_x_norm` / `_y_norm` compute the fraction along the axis:

```python
def _y_norm(self, y):
    if self.yscale == 'log':
        ly = log10(y)
        lmin, lmax = log10(ymin), log10(ymax)
        return (ly - lmin) / (lmax - lmin)
    return (y - ymin) / (ymax - ymin)
```

Everything upstream — `data_to_screen`, `screen_to_data`, `zoom`, `pan`, `auto_scale` — just calls `_x_norm` / `_y_norm` and gets correct log-space behaviour for free.

Log zoom is geometric (scales in log space, so each scroll tick feels consistent regardless of your current position) and log pan is additive in log space (which is multiplicative in data space — dragging right multiplies all x values by the same factor).

### Auto-scale timing

`auto_scale` runs at render time, not at plot time. This is a subtle but important decision. Users often write:

```python
plt.plot(x, y)
plt.ylim(0, 1)   # called after plot()
```

If auto-scale ran inside `plot()`, the subsequent `ylim()` call would be silently overwritten on the next render. Running it at the start of `AxesRenderer.render()` — after the user has had a chance to call `set_xlim/set_ylim` — ensures user-specified limits always win.

---

## Renderer: all drawing in one place

`FigureRenderer.render()` creates a pygame Surface the size of the window, then delegates each Axes to `AxesRenderer`. Each Axes renderer gets its own surface allocation based on the normalised rect `(left, bottom, width, height)` stored on the Axes.

Within one Axes, the rendering pipeline is fixed:

```
1.  auto_scale()                  — fit limits to data
2.  compute data_rect             — pixel rect for the actual plot area
3.  fill axes background
4.  draw grid lines
5.  AxesImage (imshow)
6.  Polygon (fill_between, violin, pie, stackplot)
7.  Rectangle (bar, hist, boxplot body)
8.  PathCollection (scatter)
9.  Line2D (plot, boxplot whiskers)
10. ErrorBar (whiskers + caps)
11. axes border
12. ticks + tick labels
13. title, xlabel, ylabel
14. legend
15. colorbar
```

Steps 5–10 draw on a **subsurface** — a zero-copy view into the full surface clipped to the data rectangle. This has two benefits: pygame automatically clips draw calls to the subsurface bounds (no manual clipping code needed), and artists don't need to know where on screen the data area starts.

The catch: all screen coordinates from `Transform` are in full-surface space, so the renderer subtracts `data_rect.topleft` before using them on the subsurface:

```python
sx, sy = ax.transform.data_to_screen(x, y)
sx -= data_rect.left
sy -= data_rect.top
```

This subtraction lives in `_screen_to_sub()` and is called at the top of every `_draw_*` helper. Miss it once and everything renders at the wrong position.

### Transparent polygons can't use subsurfaces

Polygons need an alpha channel for `fill_between` and violin plots. pygame surfaces created with `SRCALPHA` support per-pixel alpha, but `subsurface()` returns a view that inherits its parent's flags — and the parent surface has no alpha channel.

The fix is to create a temporary SRCALPHA surface the same size as the data area, draw the polygon on it, and then blit it onto the subsurface:

```python
tmp = pygame.Surface((data_w, data_h), pygame.SRCALPHA)
pygame.draw.polygon(tmp, facecolor, points)
data_surf.blit(tmp, (0, 0))
```

This allocates a new surface per polygon per frame. For the typical number of polygons in a plot it's fast enough, but it's worth knowing this is happening.

### Pie chart aspect ratio

Pie charts require `aspect='equal'` — a circle should look like a circle, not an ellipse that stretches to fill whatever rectangle the Axes was given. The renderer detects this before setting `axes_rect`:

```python
if ax._aspect == 'equal':
    x_ppu = data_w / x_range   # pixels per data unit, x
    y_ppu = data_h / y_range   # pixels per data unit, y
    if x_ppu < y_ppu:
        data_h = int(data_w * y_range / x_range)   # shrink height
    else:
        data_w = int(data_h * x_range / y_range)   # shrink width
```

The smaller dimension drives the other, and the leftover pixels become empty margins. The transform's `axes_rect` is updated to reflect the squarer geometry before any drawing begins.

---

## The event loop

`plt.show()` drives a standard pygame event loop at 60 fps:

```python
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == animation_event_id:
            dirty |= animation._on_timer()
        else:
            dirty |= state.handle_event(event, screen=screen)

    if dirty:
        surface = FigureRenderer(fig).render()
        screen.blit(surface, (0, 0))
        pygame.display.flip()
        dirty = False

    clock.tick(60)
```

`dirty` is the only redraw flag. Nothing renders unless something actually changed. This matters because rendering is not free — rebuilding the whole surface on every tick at 60 fps would be wasteful.

`InteractionState` translates raw pygame events into mutations on `Transform`:

| Event | Action |
|-------|--------|
| Left mouse down | start pan, record position |
| Mouse motion while dragging | `transform.pan(dx, dy)` |
| Mouse wheel | `transform.zoom(cx, cy, factor)` |
| Double-click | `transform.reset_to_home()` |
| Scroll up/down | zoom in/out centered on cursor |

Each event handler returns `True` if it changed something, which propagates to `dirty`. Mouse motion always returns `True` because the hover tooltip needs to follow the cursor even when not panning.

**Per-axes isolation**: zoom and pan only apply to the Axes under the cursor. `_find_ax_at(sx, sy)` uses `Transform.contains_screen_point()` to identify which Axes the cursor is inside. A figure with a 2×2 grid of subplots has four completely independent Transform instances; zooming into one doesn't touch the others.

---

## Animation

`Animation` wraps the user's `update_fn(frame)` and drives it with a pygame timer:

```python
pygame.time.set_timer(event_id, interval_ms)   # fires every N ms
```

The timer fires a `USEREVENT` that the main loop intercepts. On each tick, `_on_timer()` calls `update_fn(frame)`, increments the frame counter, and marks all axes dirty.

Animations **start paused**. The timer is not activated in `plt.animate()` or `plt.show()` — only when the user presses Space. This allows scrubbing with arrow keys before anything has played, which is useful when you want to examine the starting state or step through an algorithm one frame at a time.

**Frame scrubbing** is implemented as two methods:

```python
def step_forward(self):
    return self._show_frame(self._displayed_frame + 1)

def step_back(self):
    return self._show_frame(max(0, self._displayed_frame - 1))
```

`_show_frame(n)` calls `update_fn(n)` directly, bypassing the timer entirely. Because `update_fn` typically clears the axes and redraws from scratch, any frame is reachable in O(1) regardless of whether it was previously rendered. The animation is random-access, not sequential.

**Exporting to GIF or MP4** uses the same headless render path. `Animation.save(filename)` iterates all frames, calls `update_fn(i)` and `FigureRenderer(fig).render()` for each, converts the resulting `pygame.Surface` to a `(H, W, 3)` numpy array via `pygame.surfarray.array3d().transpose(1, 0, 2)`, then hands the frame list to Pillow (GIF) or imageio+ffmpeg (video). No display window is needed — `pygame.init()` alone is sufficient, because font rendering goes through `pygame.font` which doesn't require `display.set_mode()`. The typical pattern is export then show:

```python
anim = plt.animate(update, frames=30, interval=150)
plt.save_animation('gradient_descent.gif')  # headless export
plt.show()                                   # interactive window
```

After `save()` completes, it calls `update_fn(0)` to restore the figure to frame 0, so the subsequent `show()` opens at the beginning rather than the last frame.

**R key** resets both the view and the animation simultaneously:

```python
ax.transform.reset_to_home()
anim.pause()
anim._finished = False
anim._next_frame = 0
anim._show_frame(0)
```

The order matters: pause first (cancel the timer), then reset the frame counter, then render frame 0. Calling `_show_frame(0)` before pausing would let the timer fire and advance to frame 1 before the user sees frame 0.

---

## Ticks and log scale

Tick generation lives in `ticks.py` and is scale-aware:

**Linear**: a nice-step algorithm that tries steps from `[1, 2, 2.5, 5, 10] × 10^k` and picks the first that gives 3–8 ticks across the current view.

**Log**: decade ticks (1, 10, 100, …) at every power of ten in range, plus 2× and 5× intermediate ticks when fewer than three decades are visible. Labels use plain numbers for exponents −3 to 4 (`0.001` through `10000`) and scientific notation (`1e+8`) for anything beyond.

The renderer calls the right tick generator based on `ax._xscale` / `ax._yscale` and uses the same ticks for both the grid lines and the tick marks. They are always in sync.

---

## Color system

`to_rgba(color, alpha=1.0)` converts any matplotlib-style color spec to an `(R, G, B, A)` uint8 tuple that pygame can use directly. Accepted forms:

- Named: `'steelblue'`, `'red'`, `'k'`, `'w'`
- Single char: `'b'`, `'r'`, `'g'`, `'m'`, `'c'`, `'y'`
- Hex: `'#3498DB'`, `'#3498DB80'` (with alpha)
- Cycle alias: `'C0'` through `'C9'` (tab10 palette)
- Grayscale: `'0.5'`
- Float tuple: `(0.2, 0.4, 0.8)` in [0, 1]
- `'none'` → fully transparent

The 10-color default cycle is tab10. Each Axes tracks a `_color_cycle_idx` counter that auto-increments every time a plot call uses the default color. `cla()` resets the counter so re-drawn animations stay consistent across frames.

---

## Format string parsing

`plt.plot(x, y, 'r--o')` is shorthand for `color='red', linestyle='--', marker='o'`. Parsing this is more subtle than it looks because the characters can appear in any order and some overlap: `-` could start `-` (solid) or `--` (dashed) or `-.` (dash-dot).

The parser tries longer patterns first:

```python
for ls in ['-.', '--', '-', ':']:   # longest first
    if fmt.startswith(ls):
        props['linestyle'] = ls
        fmt = fmt[len(ls):]
        break
```

Without this, `'--'` would match as two `-` characters and set the linestyle to solid.

---

## What's missing

The library is deliberately scoped to what's needed for interactive ML tutorials. Deferred features that would add significant complexity:

- `ax.twinx()` / `ax.twiny()` — shared-axis subplots with independent scales
- `sharex` / `sharey` — linked zoom across subplots
- `ax.annotate()` / `ax.text()` — arbitrary text at data coordinates
- `contour` / `contourf` — contour lines over 2D grids
- Multiple simultaneous figure windows

The core architecture is designed so these could be added without restructuring: artists extend naturally, the transform already supports independent x/y scales, and the event loop is straightforward to extend. But each would take meaningful work to get right, so they're out of scope for now.
