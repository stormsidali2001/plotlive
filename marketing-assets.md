# plotlive: Marketing Assets

> **Portfolio spec:** 1400x788px, 16:9. Generate at that size in DALL-E, downscale to 700x394 before uploading to Upwork or LinkedIn.

Generate each prompt in **ChatGPT → DALL-E**. For feature frames: generate the frame in DALL-E, take the screenshot separately, then merge in Canva by dragging the screenshot into the blank white card on the right side.

---

## Screenshot Guide

Take these screenshots as direct window captures of the running pygame window (snippets A/B/C), or as a Chrome tab capture at 1440x900 (snippet D).

| # | What to show | Verified working |
|---|-------------|-----------------|
| 1 | Scatter plot window, hover tooltip floating over a data point | Snippet A |
| 2 | Gradient descent animation paused on frame 2, red dot visible partway down the bowl, title reads "Gradient Descent step 2" | Snippet B |
| 3 | 2x2 subplot grid: training curves top-left, confusion matrix top-right, feature importance bottom-left, scatter bottom-right | Snippet C |
| 4 | Jupyter notebook tab, two cells visible, inline PNG chart rendered below the second cell | Snippet D |
| 5 | Terminal window mid-export: lines like `Exporting 25 frames → gradient_descent.gif` and `5/25` visible | Snippet E |

**Prerequisites:**
```bash
source .venv/bin/activate        # activate the virtual environment
pip install plotlive             # if not already installed
```

**Screenshot 1: scatter with tooltip**

1. Run Snippet A. A pygame window opens immediately.
2. Move the mouse slowly over any colored point until a small label appears showing the point's coordinates.
3. While the tooltip is visible, press `Cmd+Shift+4` (macOS) or `PrintScreen` (Windows). On macOS, click the window to capture just that window.
4. Wrap in [Screely](https://screely.com): upload the file, pick "White frame" and "Light shadow", download.

**Screenshot 2: gradient descent paused on frame 2**

1. Run Snippet B. The window opens paused on frame 1 (title reads "Gradient Descent step 1", red dot near the right side of the bowl at w≈2.5).
2. Press the right arrow key once. The title changes to "Gradient Descent step 2" and the dot moves left.
3. Screenshot the window with `Cmd+Shift+4` → click window.
4. Confirm in the image: dot is somewhere between x=1 and x=2, clearly on the slope, not at the bottom.
5. Wrap in Screely.

**Screenshot 3: 2x2 subplot grid**

1. Run Snippet C. A single window with four panels opens.
2. Hover the mouse over the top-left (Training Curves) panel and scroll up once so it zooms in slightly, demonstrating per-panel independent zoom. This makes the screenshot more interesting.
3. Screenshot the full window with `Cmd+Shift+4` → click window.
4. Confirm all four panels are visible and labeled.
5. Wrap in Screely.

**Screenshot 4: Jupyter inline output**

1. Install Jupyter if needed: `pip install notebook`
2. Run: `jupyter notebook` (venv must be active). A browser tab opens.
3. Create a new Python 3 notebook.
4. In cell 1, type and run: `import plotlive.pyplot as plt, numpy as np`
5. In cell 2, paste Snippet D (the static version), run the cell. A PNG chart appears inline below the cell.
6. In Chrome: open DevTools (`Cmd+Option+I`), click the device toolbar (phone/tablet icon), set dimensions to 1440x900.
7. Press `Cmd+Shift+P`, type "Capture full size screenshot", press Enter.
8. The saved PNG shows the notebook header, both cells, and the inline chart output.
9. Wrap in Screely.

**Screenshot 5: terminal export progress**

1. Open a terminal window. Set font size to 14pt and window width to ~100 characters so the progress lines are readable.
2. Run Snippet E. Lines print to the terminal every few frames:
   ```
   Exporting 25 frames → gradient_descent.gif
     5/25
    10/25
   ```
3. Screenshot the terminal while the progress lines are printing (not after it finishes).
4. On macOS: `Cmd+Shift+4`, drag to select just the terminal window content area.
5. Wrap in Screely.

**Snippets:**

```bash
# Snippet A — scatter with tooltip
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(0)
X = np.random.randn(80, 2)
labels = (X[:,0]+X[:,1] > 0).astype(float)
plt.scatter(X[:,0], X[:,1], c=labels, cmap='viridis', s=60, alpha=0.8)
plt.xlabel('Feature 1'); plt.ylabel('Feature 2'); plt.title('Scatter  hover any point')
plt.show()
"

# Snippet B — gradient descent animation (press Space to step)
python3 -c "
import plotlive.pyplot as plt, numpy as np
x = np.linspace(-3, 3, 200); w = [2.5]
def update(frame):
    w[0] -= 0.15 * 2 * w[0]
    plt.cla()
    plt.plot(x, x**2, 'b-', linewidth=2, label='f(w)=w^2')
    plt.scatter([w[0]], [w[0]**2], c='red', s=120, zorder=5, label=f'w={w[0]:.3f}')
    plt.ylim(-0.2, 7); plt.legend()
    plt.title(f'Gradient Descent  step {frame+1}')
plt.animate(update, frames=25, interval=200); plt.show()
"

# Snippet C — 2x2 subplot grid
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(0)
fig, axs = plt.subplots(2, 2, figsize=(11, 8))
x = np.arange(50)
axs[0,0].plot(x, np.exp(-x/10), label='train'); axs[0,0].plot(x, np.exp(-x/12)+0.05*np.random.randn(50), label='val')
axs[0,0].set_title('Training Curves'); axs[0,0].legend()
cm = np.array([[50,2,1],[3,45,5],[2,4,48]])
im = axs[0,1].imshow(cm, cmap='Blues'); axs[0,1].set_title('Confusion Matrix')
feats=['age','income','tenure','score']; vals=[0.4,0.3,0.18,0.08]
axs[1,0].barh(feats, vals); axs[1,0].set_title('Feature Importance')
X2 = np.random.randn(60, 2); c2 = (X2[:,0]>0).astype(float)
axs[1,1].scatter(X2[:,0],X2[:,1],c=c2,cmap='coolwarm',s=40); axs[1,1].set_title('Scatter')
plt.show()
"

# Snippet D — Jupyter inline (paste into a Jupyter cell)
# import plotlive.pyplot as plt, numpy as np
# x = np.arange(50)
# plt.plot(x, np.exp(-x/10), label='loss'); plt.legend(); plt.grid(); plt.show()

# Snippet E — export terminal output
python3 -c "
import sys; sys.path.insert(0,'src')
import plotlive.pyplot as plt, numpy as np
x = np.linspace(-3,3,200); w=[2.5]
def update(f):
    w[0]-=0.15*2*w[0]; plt.cla()
    plt.plot(x,x**2,'b-',linewidth=2); plt.scatter([w[0]],[w[0]**2],c='red',s=120)
    plt.ylim(-0.2,7); plt.title(f'step {f+1}')
plt.animate(update,frames=25,interval=200)
plt.save_animation('gradient_descent.gif',fps=10)
"
```

---

## Prompt 1: Portfolio Thumbnail

> Self-contained. No screenshot needed. Upload directly to Upwork or use as GitHub social preview.

```
A flat vector illustration, 1400x788 px, 16:9 ratio, white background (#FFFFFF), no gradients on background, no textures.

Left 30%: a friendly cartoon Python developer, male or female, sitting cross-legged on the floor with a laptop. The laptop screen shows a tiny graph with two colored lines. The character has round eyes, a simple geometric style, and wears a purple hoodie. A small pygame logo icon (a purple triangle) floats near the laptop screen.

Center: the word "plotlive" in bold rounded sans-serif, 64px, color #1E1B2E. Directly below it, in 22px muted gray (#64748B): "matplotlib code. live interactive window." Below that, three pill-shaped labels arranged horizontally: pill 1 has a purple background (#673AB7) with white text "pan + zoom", pill 2 has a teal background (#0D9488) with white text "animate", pill 3 has an indigo background (#4F46E5) with white text "Jupyter inline".

Right 30%: three floating white cards (border-radius 12px, 1px border #E2E8F0, light drop shadow). Card 1: bold "11" in 48px purple (#673AB7), below it "plot types" in 14px #64748B. Card 2: bold "0" in 48px, below it "new imports" in 14px #64748B, with a green checkmark icon. Card 3: bold "GIF + MP4" in 24px, below it "export formats" in 14px #64748B.

No photographic elements. No dark backgrounds. No gradients anywhere.
```

---

## Prompt 2: Feature Frame — Interactive Window

> Drop your screenshot 1 (scatter plot with tooltip) into the blank white card area in Canva.
> Feature: the pygame window responds to scroll, drag, and hover with no extra setup, while keeping the same matplotlib API the user already wrote.

**How to get this screenshot:**
1. Run Snippet A from the guide above.
2. Hover the mouse over one of the scatter points so the tooltip appears.
3. Screenshot the full pygame window with `Cmd+Shift+4`, select the window.
4. Wrap in Screely (white frame, light shadow).

```
A flat vector marketing frame, 1400x788 px, 16:9, background color #F8FAFC, no gradients on background.

Left 32% vertical strip:
- Top: a small badge, 28px tall, background #673AB7, border-radius 6px, white text in 11px bold uppercase: "INTERACTIVE WINDOW"
- Below the badge, a bold heading in #1E1B2E, 28px, two lines: "Pan, zoom, hover." second line: "Zero extra config."
- Below the heading, 4 bullet points in 14px #64748B. Each bullet dot is a 6px circle in #673AB7. Bullets: "scroll to zoom centered on cursor", "drag to pan any axis", "hover shows the nearest point value", "double-click resets the view"
- Below the bullets, a small flat vector illustration: a cartoon magnifying glass hovering over a tiny line chart, outline-only style, purple and gray.

Right 65%: one large white card, border-radius 16px, 1px border #E2E8F0, drop shadow (0 4px 24px rgba(0,0,0,0.08)). The card interior is completely blank white. No UI elements inside the white card.

No UI elements inside the white card. All text and illustration stay in the left strip only.
```

---

## Prompt 3: Feature Frame — Animation Controls

> Drop your screenshot 2 (gradient descent animation, paused mid-frame) into the blank white card in Canva.
> Feature: animations start paused, letting the viewer step through each frame manually to follow an algorithm at their own pace.

**How to get this screenshot:**
1. Run Snippet B from the guide above.
2. The window opens paused on frame 1. Press the right arrow key once to advance to frame 2.
3. Screenshot the pygame window. The title bar should show "Gradient Descent step 2" and the red dot should be visibly partway down the bowl.
4. Wrap in Screely (white frame, light shadow).

```
A flat vector marketing frame, 1400x788 px, 16:9, background color #F8FAFC, no gradients on background.

Left 32% vertical strip:
- Top: a small badge, 28px tall, background #0D9488, border-radius 6px, white text in 11px bold uppercase: "ANIMATION"
- Below the badge, bold heading in #1E1B2E, 28px, two lines: "Step through" second line: "every frame."
- Below the heading, 4 bullet points in 14px #64748B. Bullet dots are 6px circles in #0D9488. Bullets: "starts paused on frame 0", "Space bar plays or pauses", "arrow keys step one frame at a time", "S key saves the current frame as PNG"
- Below the bullets, a small flat vector of a film strip with 3 frames: first frame shows a curve, second shows a red dot on the curve, third shows the dot lower on the curve. Simple outline style, teal and gray.

Right 65%: one large white card, border-radius 16px, 1px border #E2E8F0, drop shadow (0 4px 24px rgba(0,0,0,0.08)). The card interior is completely blank white. No UI elements inside the white card.

No UI elements inside the white card.
```

---

## Prompt 4: Feature Frame — Subplot Grid

> Drop your screenshot 3 (2x2 subplot grid) into the blank white card in Canva.
> Feature: plt.subplots() returns a grid of independent axes, each with its own zoom and pan state.

**How to get this screenshot:**
1. Run Snippet C from the guide above.
2. The window shows 4 subplots. Try scrolling over one subplot to show it zoomed independently.
3. Screenshot the full window. All 4 plots must be visible.
4. Wrap in Screely (white frame, light shadow).

```
A flat vector marketing frame, 1400x788 px, 16:9, background color #F8FAFC, no gradients on background.

Left 32% vertical strip:
- Top: a small badge, 28px tall, background #4F46E5, border-radius 6px, white text in 11px bold uppercase: "SUBPLOTS"
- Below the badge, bold heading in #1E1B2E, 28px, two lines: "Grid layouts." second line: "Each axis independent."
- Below the heading, 4 bullet points in 14px #64748B. Bullet dots are 6px circles in #4F46E5. Bullets: "fig, axs = plt.subplots(2, 2)", "zoom one panel without affecting others", "double-click any panel to expand it", "mix plot types freely in one figure"
- Below the bullets, a small flat illustration of a 2x2 grid of tiny chart thumbnails: top-left shows two lines, top-right a heatmap grid, bottom-left horizontal bars, bottom-right a scatter cloud. Simple outline style, indigo and gray.

Right 65%: one large white card, border-radius 16px, 1px border #E2E8F0, drop shadow (0 4px 24px rgba(0,0,0,0.08)). The card interior is completely blank white. No UI elements inside the white card.

No UI elements inside the white card.
```

---

## Prompt 5: Feature Frame — Jupyter Inline

> Drop your screenshot 4 (Jupyter notebook with inline GIF output) into the blank white card in Canva.
> Feature: plt.show() detects the Jupyter kernel and switches to inline display automatically, static plots as PNG and animations as GIF.

**How to get this screenshot:**
1. Run `jupyter notebook` in the repo root (venv must be active).
2. Create a new notebook.
3. In cell 1: `import plotlive.pyplot as plt, numpy as np`
4. In cell 2: paste Snippet D (the static version), run it. The plot appears inline below the cell.
5. Screenshot the Jupyter tab in Chrome at 1440x900 using DevTools device toolbar. The notebook header, the two cells, and the inline plot output must all be visible.
6. Wrap in Screely (white frame, light shadow).

```
A flat vector marketing frame, 1400x788 px, 16:9, background color #F8FAFC, no gradients on background.

Left 32% vertical strip:
- Top: a small badge, 28px tall, background #D97706, border-radius 6px, white text in 11px bold uppercase: "JUPYTER"
- Below the badge, bold heading in #1E1B2E, 28px, two lines: "Inline output." second line: "Same import."
- Below the heading, 4 bullet points in 14px #64748B. Bullet dots are 6px circles in #D97706. Bullets: "plt.show() detects the kernel automatically", "static plots render as PNG", "animations export as GIF", "no config, no different import path"
- Below the bullets, a small flat illustration of a Jupyter notebook cell: a gray rectangle with a green play button on the left, a line of code inside, and a tiny line chart below it as the cell output. Amber and gray.

Right 65%: one large white card, border-radius 16px, 1px border #E2E8F0, drop shadow (0 4px 24px rgba(0,0,0,0.08)). The card interior is completely blank white. No UI elements inside the white card.

No UI elements inside the white card.
```

---

## Prompt 6: Feature Frame — Export to GIF and MP4

> Drop your screenshot 5 (terminal showing export progress) into the blank white card in Canva.
> Feature: save_animation() renders all frames headlessly and writes a GIF or MP4 file, no display required.

**How to get this screenshot:**
1. Run Snippet E in a terminal window. The output will print frame progress like: `Exporting 25 frames → gradient_descent.gif` with lines `  5/25`, `10/25`, etc.
2. Screenshot the terminal during the export (while progress lines are printing).
3. Make the terminal window about 800px wide and resize font to 14px so the text is legible.
4. Wrap in Screely.

```
A flat vector marketing frame, 1400x788 px, 16:9, background color #F8FAFC, no gradients on background.

Left 32% vertical strip:
- Top: a small badge, 28px tall, background #059669, border-radius 6px, white text in 11px bold uppercase: "EXPORT"
- Below the badge, bold heading in #1E1B2E, 28px, two lines: "GIF and MP4." second line: "No window needed."
- Below the heading, 4 bullet points in 14px #64748B. Bullet dots are 6px circles in #059669. Bullets: "plt.save_animation('out.gif')", "runs fully headless, no display required", "fps derived from interval automatically", "pip install plotlive[gif] adds GIF support"
- Below the bullets, a flat illustration of a file icon with a play button in the center and a small progress bar below it, labeled '.gif'. Simple green and gray outline style.

Right 65%: one large white card, border-radius 16px, 1px border #E2E8F0, drop shadow (0 4px 24px rgba(0,0,0,0.08)). The card interior is completely blank white. No UI elements inside the white card.

No UI elements inside the white card.
```

---

## Assembly Workflow

1. **Take the screenshots** using the snippets above. Use macOS `Cmd+Shift+4` for pygame windows; use Chrome DevTools 1440x900 for Jupyter.
2. **Wrap each screenshot** in [Screely](https://screely.com) with style: white frame, light shadow.
3. **Generate the DALL-E frames** in ChatGPT using the prompts above.
4. In **Canva**: upload the Screely screenshot, then drag it over the blank white card on the right side of the DALL-E frame. Resize to fill the card area and clip to its bounds.
5. Export at 1400x788 for Upwork. LinkedIn recommends 1200x627 so crop 80px off each vertical edge.

| Tool | Purpose |
|------|---------|
| [Screely](https://screely.com) | Wraps the pygame or Jupyter screenshot in a clean browser frame |
| [Canva](https://canva.com) | Merges DALL-E frame with Screely screenshot |
| [favicon.io](https://favicon.io) | Converts PNG icon to .ico for docs fallback |
