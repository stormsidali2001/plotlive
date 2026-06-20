# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] — 2026-06-06

### Added
- Initial release
- `matplotlib.pyplot`-compatible state-machine API (`plt.plot`, `plt.scatter`, `plt.hist`, `plt.bar`, `plt.imshow`, `plt.show`, …)
- OOP API (`fig, ax = plt.subplots()`)
- Pan (drag), zoom (scroll wheel), reset (double-click or R key)
- Hover tooltips showing nearest data point
- Subplot grid via `plt.subplots(nrows, ncols)`
- Animation via `FuncAnimation` / `plt.animate()` with play/pause/step controls
- Export animations to GIF (Pillow) or MP4 (imageio + ffmpeg)
- Jupyter notebook inline display — static figures as PNG, animations as GIF/MP4
- 10 built-in colormaps: `viridis`, `plasma`, `inferno`, `magma`, `coolwarm`, `RdBu`, `Blues`, `Reds`, `jet`, `gray`
- `plt.colorbar()` for heatmaps
- `plt.savefig()` to PNG
- Log scale (`set_xscale('log')`, `set_yscale('log')`)
- Bundled DejaVu Sans fonts (no system font dependency)
