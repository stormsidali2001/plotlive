# plotlive — codebase guide

Interactive matplotlib-compatible graphs rendered with pygame-ce. Drop-in replacement for the most common `matplotlib.pyplot` patterns; renders a live, pannable, zoomable window instead of a static plot.

## Dev setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[gif,video]"   # install with all optional deps
pytest                          # run unit tests
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest   # headless (CI)
```

## Architecture

```
pyplot.py  (state-machine API — plt.plot, plt.show …)
  └─ Figure  (figure.py)
       └─ Axes  (axes.py)  — stores artists, no draw calls
            ├─ Artists  (artists.py)  — Line2D, PathCollection, Rectangle, AxesImage …
            ├─ CoordTransform  (transform.py)  — data↔screen math, zoom/pan state
            └─ [rendered by] AxesRenderer  (renderer.py)
                  ├─ ticks.py   — auto_ticks(), format_ticks()
                  ├─ drawing.py — draw_dashed_polyline(), draw_marker()
                  ├─ fonts.py   — cached Font instances, rotated text
                  └─ colors.py  — to_rgba(), Colormap

pyplot.show()
  ├─ non-Jupyter → pygame event loop (InteractionState + FuncAnimation timer)
  └─ Jupyter     → _jupyter.py (headless render → PNG/GIF/MP4 via IPython.display)
```

## Coordinate systems — the biggest gotcha

Two spaces exist and **must not be mixed**:

| Space | Origin | Used by |
|-------|--------|---------|
| Figure-space | top-left of the full window (px) | `transform.data_x_to_screen()`, `transform.data_y_to_screen()`, `axes_rect` |
| Axes-surface space | top-left of the data area pygame subsurface | `_draw_ticks`, `_draw_grid`, all drawing on `subsurface(data_rect)` |

`data_y_to_screen(y)` returns **figure-space** y (includes `ax_offset`).  
Before comparing against `data_rect.top / data_rect.bottom`, subtract `self.ax_offset[1]`.  
This is done in both `_draw_ticks` and `_draw_grid` in `renderer.py`.

## Key invariants

- **Y-axis is flipped**: screen Y=0 is top, data Y increases upward. All flips live in `CoordTransform` only — never duplicate elsewhere.
- **`plot()` always returns a list** — `line, = plt.plot(x, y)` tuple-unpack is idiomatic.
- **Auto-scale runs at render time**, not at `plot()` time — users often call `set_xlim()` after `plot()`.
- **Drawing on `subsurface(data_rect)`** shifts the origin; subtract `data_rect.topleft` from all figure-space coords.
- **`pygame.draw.circle` at r≤2** produces a diamond artifact. Minimum usable radius for circles is r=3; the marker formula uses `max(2, round(sqrt(size)/1.5))`.

## File map

| File | Responsibility |
|------|---------------|
| `pyplot.py` | Global state (`_figures`, `_current_figure`, `_current_axes`), state-machine API, `show()` |
| `figure.py` | `Figure` — owns `axes[]`, `pixel_size`, `_animation` |
| `axes.py` | `Axes` — stores artists, `hit_test()`, `cla()`, axis config |
| `artists.py` | Data-only artist classes (no pygame) |
| `transform.py` | `CoordTransform` — zoom/pan state, data↔screen math |
| `renderer.py` | `FigureRenderer` + `AxesRenderer` — all pygame draw calls |
| `animation.py` | `FuncAnimation` — pygame timer playback + `save()` to GIF/MP4 |
| `events.py` | `InteractionState` — pan, zoom, hover, keyboard, focus mode |
| `drawing.py` | `draw_dashed_polyline()`, `draw_marker()`, `draw_colorbar_strip()` |
| `ticks.py` | `auto_ticks()`, `log_ticks()`, `format_ticks()` |
| `colors.py` | `to_rgba()`, `Colormap`, 10 built-in colormaps |
| `fonts.py` | Cached `pygame.font.Font` instances, `render_text_rotated()` |
| `_parsers.py` | `_parse_fmt()`, `_parse_plot_args()` — matplotlib format strings |
| `_jupyter.py` | `is_jupyter()`, `show_figure()`, `show_animation()` — IPython inline display |

## Adding a new plot type

1. Add an artist class in `artists.py` (data storage only).
2. Add a method on `Axes` in `axes.py` that creates the artist and appends it.
3. Add a drawing branch in `AxesRenderer.render()` in `renderer.py`.
4. Delegate from `pyplot.py` via `gca().new_method(...)`.

## Running examples

```bash
SDL_VIDEODRIVER=dummy python examples/bubble_sort.py   # headless smoke test
python examples/bubble_sort.py                         # interactive window
```
