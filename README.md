# plotlive

[![PyPI](https://img.shields.io/pypi/v/plotlive)](https://pypi.org/project/plotlive/)
[![Python](https://img.shields.io/pypi/pyversions/plotlive)](https://pypi.org/project/plotlive/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/assoulsidali/plotlive/actions/workflows/ci.yml/badge.svg)](https://github.com/assoulsidali/plotlive/actions)

`import plotlive.pyplot as plt` — same API as matplotlib, but `plt.show()` opens a live pygame window you can pan, zoom, and step through frame by frame.

Built for ML educators who write tutorial code in matplotlib and want the plots to be interactive without switching libraries or learning a new API.

## Install

```bash
pip install plotlive
```

For animation export:

```bash
pip install plotlive[gif]     # GIF export  (Pillow)
pip install plotlive[video]   # MP4 export  (imageio + ffmpeg)
pip install plotlive[export]  # both
```

## Quick start

```python
import plotlive.pyplot as plt
import numpy as np

x = np.arange(50)
plt.plot(x, np.exp(-x/10), label='train loss')
plt.plot(x, np.exp(-x/12) + 0.05*np.random.randn(50), label='val loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Curve')
plt.legend()
plt.grid()
plt.show()
```

---

## Jupyter support

`plt.show()` detects the Jupyter kernel and switches to inline display. No config, no different import. Static plots come out as PNG; animations export as GIF (requires `plotlive[gif]`) or MP4 if Pillow isn't installed.

```python
import plotlive.pyplot as plt
import numpy as np

# Static — displays inline
plt.plot(np.arange(50), np.exp(-np.arange(50)/10), label='loss')
plt.legend(); plt.grid()
plt.show()
```

```python
# Animation — exports GIF and displays inline
def update(frame):
    plt.cla()
    plt.plot(np.arange(frame), np.random.randn(frame).cumsum())
    plt.title(f'Step {frame}')

plt.animate(update, frames=30, interval=100)
plt.show()
```

---

## Controls

### Mouse

| Action | Result |
|--------|--------|
| Scroll up | Zoom in (centered on cursor) |
| Scroll down | Zoom out (centered on cursor) |
| Click and drag | Pan the view |
| Double-click | Reset zoom and pan |

### Keyboard

| Key | Action |
|-----|--------|
| `?` or `H` | Show / hide the help panel |
| `Space` | Play / pause animation |
| `→` Right arrow | Step forward one frame (while paused) |
| `←` Left arrow | Step back one frame (while paused) |
| `R` | Reset zoom / pan + restart animation from frame 0 (paused) |
| `S` | Save current frame as `frame_NNNN.png` |
| `Esc` | Close the help panel |

Animations start paused. Press `Space` to play, `←` / `→` to step one frame at a time.

Zoom and pan apply to whichever subplot your cursor is over — each one is independent.

---

## Supported plot types

| Function | EDA use case |
|----------|-------------|
| `plt.plot(x, y)` | Line plots — training curves, time series |
| `plt.scatter(x, y, c=labels)` | Scatter — clusters, feature relationships |
| `plt.hist(data, bins=20)` | Histogram — feature distributions |
| `plt.bar(x, height)` / `plt.barh(y, width)` | Bar charts — feature importance, class counts |
| `plt.imshow(matrix, cmap='Blues')` | Heatmap — confusion matrix, correlation |
| `plt.boxplot(data)` | Box plot — distribution summary + outliers |
| `plt.violinplot(data)` | Violin plot — full distribution shape per group |
| `plt.fill_between(x, y1, y2)` | Shaded area — confidence bands, regions |
| `plt.errorbar(x, y, yerr=std)` | Error bars — mean ± std / confidence |
| `plt.stackplot(x, y1, y2, y3)` | Stacked area — cumulative contributions |
| `plt.pie(values, labels=...)` | Pie chart — class proportions |

---

## API reference

```python
# ── Figure / layout ──────────────────────────────────────────────────
fig = plt.figure(figsize=(10, 6))
fig, ax = plt.subplots()
fig, axs = plt.subplots(2, 3, figsize=(14, 8))   # returns 2-D array of Axes
fig.suptitle('Overall title')
plt.tight_layout()
plt.savefig('output.png')
plt.save_animation('output.gif')   # requires: pip install Pillow
plt.save_animation('output.mp4')   # requires: pip install imageio[ffmpeg]
plt.show()

# ── Plots ────────────────────────────────────────────────────────────
plt.plot(x, y, 'b--', label='data', linewidth=2)
plt.scatter(x, y, c=colors, cmap='viridis', s=50, alpha=0.7)
plt.hist(data, bins=30, color='steelblue', edgecolor='white')
plt.bar(categories, values, color='steelblue')
plt.barh(categories, values)
plt.imshow(matrix, cmap='coolwarm', vmin=-1, vmax=1)
plt.colorbar()

plt.boxplot([group_a, group_b, group_c])
plt.violinplot([group_a, group_b], positions=[1, 2], widths=0.6)
plt.fill_between(x, y_low, y_high, alpha=0.3, color='steelblue')
plt.errorbar(x, y, yerr=std, fmt='o', capsize=4)
plt.stackplot(x, y1, y2, y3, labels=['A', 'B', 'C'], alpha=0.8)
plt.pie(values, labels=['Cat A', 'Cat B', 'Cat C'], startangle=90)

# ── Axes decoration ──────────────────────────────────────────────────
plt.xlabel('x label')
plt.ylabel('y label')
plt.title('Axes title')
plt.legend()
plt.grid()
plt.xlim(0, 10)
plt.ylim(-1, 1)
plt.xscale('log')
plt.yscale('log')
plt.xticks([0, 1, 2], ['zero', 'one', 'two'])
plt.yticks([0, 0.5, 1])
plt.axhline(y=0, color='k', linewidth=0.8)
plt.axvline(x=0, color='k', linewidth=0.8)

# ── OOP API ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(2, 2, figsize=(12, 8))
ax[0, 0].plot(x, y)
ax[0, 1].scatter(x, y, c=labels, cmap='tab10')
ax[1, 0].boxplot([a, b, c])
ax[1, 1].violinplot(data)
ax[0, 0].set_xlabel('x'); ax[0, 0].set_ylabel('y')
ax[0, 0].set_title('subplot title')
ax[0, 0].legend(); ax[0, 0].grid()

# ── Animation ────────────────────────────────────────────────────────
def update(frame):
    plt.cla()
    plt.plot(x[:frame], y[:frame])
    plt.title(f'Frame {frame}')

plt.animate(update, frames=100, interval=50, repeat=True)
plt.show()

# ── Animation export ─────────────────────────────────────────────────
anim = plt.animate(update, frames=100, interval=50)
plt.save_animation('output.gif')        # requires: pip install Pillow
plt.save_animation('output.mp4')        # requires: pip install imageio[ffmpeg]
plt.save_animation('output.gif', fps=24)  # override frame rate
anim.save('output.gif')                 # or call directly on the object
plt.show()                              # interactive window opens afterwards
```

---

## Animation

### FuncAnimation — matplotlib-compatible

Matches `matplotlib.animation.FuncAnimation` — existing animation code works as-is:

```python
from plotlive.animation import FuncAnimation

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
x = np.linspace(-3, 3, 200)

def update(frame):
    ax.cla()
    ax.plot(x, np.sin(x + frame * 0.1))
    ax.set_title(f'Frame {frame}')

anim = FuncAnimation(fig, update, frames=60, interval=50, repeat=True)
plt.show()
```

All constructor parameters are supported:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fig` | — | Figure to animate |
| `func` | — | Called as `func(frame, *fargs)` each step |
| `frames` | `None` | int, list, generator, or None (→ 100 frames) |
| `init_func` | `None` | Accepted, not used (no blit) |
| `fargs` | `None` | Extra positional args forwarded to `func` |
| `save_count` | `None` | Frame count when `frames` is None |
| `interval` | `200` | Milliseconds between frames |
| `repeat` | `True` | Loop when finished |
| `blit` | `False` | Accepted, not used (full redraw always) |

`frames` as a list passes values directly to `func`, not the index:

```python
# func receives 0.0, 0.5, 1.0, 1.5, … not the list index
anim = FuncAnimation(fig, update, frames=np.linspace(0, 2*np.pi, 60))
```

### plt.animate() — convenience shorthand

```python
plt.animate(update, frames=60, interval=50, repeat=True)
plt.show()
```

---

## Animation export

Export any animation to a file without opening a window. Useful for embedding in slides or sharing with people who don't have plotlive installed.

### Install

```bash
pip install plotlive[gif]           # GIF support  (Pillow)
pip install plotlive[video]         # MP4/MOV/AVI  (imageio + ffmpeg)
pip install plotlive[export]        # both
```

Or install the optional dependency directly:

```bash
pip install Pillow                      # for GIF
pip install imageio[ffmpeg]             # for MP4 / MOV / AVI
```

### Usage

```python
import plotlive.pyplot as plt
import numpy as np

x = np.linspace(-3, 3, 200)
w = [2.5]

def update(frame):
    w[0] -= 0.15 * 2 * w[0]
    plt.cla()
    plt.plot(x, x**2, 'b-', linewidth=2, label='f(w) = w²')
    plt.scatter([w[0]], [w[0]**2], c='red', s=120, label=f'w = {w[0]:.3f}')
    plt.ylim(-0.2, 7)
    plt.legend()
    plt.title(f'Gradient Descent — step {frame + 1}')

plt.animate(update, frames=25, interval=200)
plt.save_animation('gradient_descent.gif')  # export first
plt.show()                                   # then open interactive window
```

`save_animation` renders all frames off-screen. After saving, the figure resets to frame 0 so a subsequent `show()` starts from the beginning.

Supported formats: `.gif` · `.mp4` · `.mov` · `.avi` · `.webm`

### API

| Call | Description |
|------|-------------|
| `plt.save_animation(filename)` | Export current figure's animation |
| `plt.save_animation(filename, fps=24)` | Override frame rate |
| `anim.save(filename)` | Call on any `FuncAnimation` object |
| `anim.save(filename, writer='pillow', fps=12)` | Explicit writer (matplotlib-compatible) |
| `anim.save(filename, writer='ffmpeg', fps=30)` | ffmpeg writer |
| `anim.save(filename, progress_callback=fn)` | `fn(current, total)` called each frame |

Default `fps` is derived from `interval`: `fps = 1000 / interval`.
Accepted `writer` values: `'pillow'` (GIF), `'ffmpeg'` / `'imageio'` (video), or `None` (inferred from extension).

### Quick test

Run this one-liner — no window opens, it just renders and saves:

```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
import plotlive.pyplot as plt, numpy as np
x = np.linspace(-3, 3, 200); w = [2.5]
def update(frame):
    w[0] -= 0.15 * 2 * w[0]; plt.cla()
    plt.plot(x, x**2, 'b-', linewidth=2, label='f(w)=w²')
    plt.scatter([w[0]], [w[0]**2], c='red', s=120, label=f'w={w[0]:.3f}')
    plt.ylim(-0.2, 7); plt.legend(); plt.title(f'Gradient Descent — step {frame+1}')
plt.animate(update, frames=20, interval=200)
plt.save_animation('gradient_descent.gif')
"
```

Frame progress prints to the terminal and `gradient_descent.gif` appears in the current directory.

---

## Examples

Run from the `examples/` directory after activating the venv:

```bash
cd examples
source ../.venv/bin/activate
```

---

### Static plots

#### Training curves
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
x = np.arange(50)
plt.plot(x, np.exp(-x/10), label='train loss')
plt.plot(x, np.exp(-x/12) + 0.05*np.random.randn(50), label='val loss')
plt.fill_between(x, np.exp(-x/10)-0.05, np.exp(-x/10)+0.05, alpha=0.2, label='± 1σ')
plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.title('Training Curve')
plt.legend(); plt.grid(); plt.show()
"
```

#### Confusion matrix
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
cm = np.array([[50,2,1],[3,45,5],[2,4,48]])
fig, ax = plt.subplots()
im = ax.imshow(cm, cmap='Blues')
plt.colorbar(im, ax=ax); ax.set_title('Confusion Matrix'); plt.show()
"
```

#### Feature importance + error bars
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
feats = ['age','income','tenure','score','region']
vals  = [0.40, 0.30, 0.18, 0.08, 0.04]
errs  = [0.04, 0.03, 0.02, 0.01, 0.005]
plt.barh(feats, vals)
plt.errorbar(vals, range(len(feats)), xerr=errs, fmt='none', color='black', capsize=4)
plt.xlabel('Importance'); plt.title('Feature Importance ± std'); plt.show()
"
```

#### Distribution comparison — box + violin
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(0)
data = [np.random.normal(m, s, 120) for m, s in [(0,1),(1,1.5),(3,0.5),(-1,2)]]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
ax1.boxplot(data); ax1.set_title('Box Plot')
ax2.violinplot(data); ax2.set_title('Violin Plot')
plt.show()
"
```

#### Correlation heatmap
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(0)
corr = np.corrcoef(np.random.randn(5, 100))
fig, ax = plt.subplots(figsize=(6,5))
im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
plt.colorbar(im, ax=ax); ax.set_title('Correlation Matrix'); plt.show()
"
```

#### Stacked area — class proportions over time
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
x = np.arange(20)
a = np.random.dirichlet([3,2,1], 20).T
plt.stackplot(x, a[0], a[1], a[2], labels=['Class A','Class B','Class C'], alpha=0.85)
plt.xlabel('Time step'); plt.ylabel('Proportion'); plt.title('Class Distribution Over Time')
plt.legend(); plt.show()
"
```

#### Pie chart — class balance
```bash
python3 -c "
import plotlive.pyplot as plt
plt.pie([52, 31, 17], labels=['Negative','Neutral','Positive'], startangle=90)
plt.title('Sentiment Distribution'); plt.legend(); plt.show()
"
```

---

### Animated examples

Animations **start paused**. Press `Space` to play, `←` / `→` to step frame by frame, `S` to save.

#### Gradient descent
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
x = np.linspace(-3, 3, 200); w = [2.5]
def update(frame):
    plt.cla(); w[0] -= 0.15 * 2 * w[0]
    plt.plot(x, x**2, 'b-', linewidth=2, label='f(w)=w²')
    plt.scatter([w[0]], [w[0]**2], c='red', s=120, zorder=5, label=f'w={w[0]:.3f}')
    plt.fill_between(x, 0, x**2, alpha=0.07)
    plt.ylim(-0.2, 7); plt.legend(); plt.title(f'Gradient Descent — step {frame+1}')
plt.animate(update, frames=25, interval=200); plt.show()
"
```

#### K-means clustering
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(7); K=3
data = np.vstack([np.random.randn(60,2)*0.7+c for c in [(-2,-2),(2,-2),(0,2)]])
centroids = data[np.random.choice(len(data),K,replace=False)].copy()
def update(frame):
    global centroids
    labels = np.array([[np.linalg.norm(p-c) for c in centroids] for p in data]).argmin(1).astype(float)
    centroids = np.array([data[labels==k].mean(0) if (labels==k).any() else centroids[k] for k in range(K)])
    plt.cla(); plt.scatter(data[:,0],data[:,1],c=labels,cmap='viridis',s=30,alpha=0.7)
    plt.scatter(centroids[:,0],centroids[:,1],c='red',s=200,marker='*',zorder=5,label='Centroids')
    plt.legend(); plt.title(f'K-Means — iteration {frame+1}')
plt.animate(update, frames=12, interval=500); plt.show()
"
```

#### Multi-class classification boundaries

Trains a softmax classifier with gradient descent and draws the three learned decision boundary lines (one per pair of classes). Each class uses a distinct marker shape. Watch the lines rotate into place as accuracy climbs.

```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np

np.random.seed(0)
K = 3
centers = [(-2, -1), (2, -1), (0, 2.5)]
X = np.vstack([np.random.randn(50, 2) * 0.8 + c for c in centers])
y = np.repeat(np.arange(K), 50)

W = np.zeros((2, K))
b = np.zeros(K)

MARKERS   = ['+',       'o',       '^'      ]
COLORS    = ['#e74c3c', '#3498db', '#2ecc71']
BD_COLORS = ['#8e44ad', '#e67e22', '#2c3e50']
x_edge = np.array([-5.5, 5.5])

def softmax(z):
    e = np.exp(z - z.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)

def plot_boundary(i, j, color):
    dw = W[:, i] - W[:, j]
    db = b[i] - b[j]
    if abs(dw[1]) < 1e-9:
        return
    plt.plot(x_edge, -(dw[0] * x_edge + db) / dw[1],
             color=color, linewidth=2, label=f'Boundary {i} vs {j}')

def update(frame):
    global W, b
    for _ in range(5):
        p = softmax(X @ W + b)
        oh = np.eye(K)[y]
        W -= 0.1 * (X.T @ (p - oh)) / len(X)
        b -= 0.1 * (p - oh).mean(axis=0)
    plt.cla()
    for k in range(K):
        m = y == k
        plt.scatter(X[m, 0], X[m, 1], c=COLORS[k], marker=MARKERS[k],
                    s=80, label=f'Class {k}')
    for (i, j), col in zip([(0, 1), (0, 2), (1, 2)], BD_COLORS):
        plot_boundary(i, j, col)
    acc = (np.argmax(X @ W + b, axis=1) == y).mean()
    plt.xlim(-5, 5); plt.ylim(-4, 5); plt.legend()
    plt.title(f'Softmax classifier — epoch {frame * 5} | acc {acc:.0%}')

plt.animate(update, frames=80, interval=100)
plt.show()
"
```

Export to GIF:
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(0); K=3
X=np.vstack([np.random.randn(50,2)*0.8+c for c in [(-2,-1),(2,-1),(0,2.5)]])
y=np.repeat(np.arange(K),50); W=np.zeros((2,K)); b=np.zeros(K)
MARKERS=['+','o','^']; COLORS=['#e74c3c','#3498db','#2ecc71']
BD_COLORS=['#8e44ad','#e67e22','#2c3e50']; x_edge=np.array([-5.5,5.5])
def softmax(z):
    e=np.exp(z-z.max(axis=1,keepdims=True)); return e/e.sum(axis=1,keepdims=True)
def plot_boundary(i,j,color):
    dw=W[:,i]-W[:,j]; db=b[i]-b[j]
    if abs(dw[1])<1e-9: return
    plt.plot(x_edge,-(dw[0]*x_edge+db)/dw[1],color=color,linewidth=2,label=f'Boundary {i} vs {j}')
def update(frame):
    global W,b
    for _ in range(5):
        p=softmax(X@W+b); oh=np.eye(K)[y]
        W-=0.1*(X.T@(p-oh))/len(X); b-=0.1*(p-oh).mean(axis=0)
    plt.cla()
    for k in range(K):
        m=y==k; plt.scatter(X[m,0],X[m,1],c=COLORS[k],marker=MARKERS[k],s=80,label=f'Class {k}')
    for (i,j),col in zip([(0,1),(0,2),(1,2)],BD_COLORS): plot_boundary(i,j,col)
    acc=(np.argmax(X@W+b,axis=1)==y).mean()
    plt.xlim(-5,5); plt.ylim(-4,5); plt.legend()
    plt.title(f'Softmax classifier — epoch {frame*5} | acc {acc:.0%}')
plt.animate(update, frames=60, interval=100)
plt.save_animation('classification.gif')
"
```

#### Neural network — hidden unit boundaries (ReLU)

Trains a 1-hidden-layer ReLU network on the two-moon dataset. Each subplot is one hidden unit — the shaded region is where it fires, the black line is its decision boundary, and `w=` is its output weight. Eight straight cuts combine into the curve that separates the moons. Double-click any subplot to expand it.

```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np

np.random.seed(0)
n_h = 8

# Two-moon dataset
theta = np.linspace(0, np.pi, 60)
X0 = np.c_[np.cos(theta),   np.sin(theta)     ] + np.random.randn(60,2)*0.15
X1 = np.c_[1-np.cos(theta), 0.5-np.sin(theta) ] + np.random.randn(60,2)*0.15
X  = np.vstack([X0, X1]); X = (X - X.mean(0)) / X.std(0)
y  = np.repeat([0, 1], 60)

# Network weights
W1 = np.random.randn(2, n_h) * np.sqrt(2/2)
b1 = np.zeros(n_h)
W2 = np.random.randn(n_h, 1) * np.sqrt(2/n_h)
b2 = np.zeros(1)

# Decision-boundary mesh
g = 28
gx, gy  = np.linspace(-3, 3, g), np.linspace(-3, 3, g)
xx, yy  = np.meshgrid(gx, gy)
grid    = np.c_[xx.ravel(), yy.ravel()]
gx_flat = xx.ravel(); gy_flat = yy.ravel()
x_edge  = np.array([-3.5, 3.5])
COLORS  = ['#e74c3c', '#3498db']; MARKERS = ['o', '^']

def relu(z):    return np.maximum(0, z)
def sigmoid(z): return 1 / (1 + np.exp(-np.clip(z, -50, 50)))

def forward(Xb):
    z1 = Xb @ W1 + b1
    return sigmoid(relu(z1) @ W2 + b2).ravel(), z1

fig, axs = plt.subplots(2, 4, figsize=(14, 7))

def update(frame):
    global W1, b1, W2, b2
    lr = 0.05
    for _ in range(10):
        p, z1 = forward(X); a1 = relu(z1); N = len(X)
        dz2 = (p - y).reshape(-1, 1) / N
        dW2 = a1.T @ dz2;  db2 = dz2.sum(0)
        dz1 = (dz2 @ W2.T) * (z1 > 0)
        W1 -= lr * X.T @ dz1;  b1 -= lr * dz1.sum(0)
        W2 -= lr * dW2;         b2 -= lr * db2
    p_tr, _ = forward(X)
    acc = ((p_tr > 0.5).astype(int) == y).mean()
    _, z1_g = forward(grid)
    for i, ax in enumerate(axs.flat):
        ax.cla()
        active = z1_g[:, i] > 0
        ax.scatter(gx_flat[~active], gy_flat[~active], c='#eeeeee', s=55)
        ax.scatter(gx_flat[ active], gy_flat[ active], c='#c6e2f5', s=55)
        w, b = W1[:, i], b1[i]
        if abs(w[1]) > 1e-9:
            ax.plot(x_edge, -(w[0]*x_edge + b)/w[1], 'k-', linewidth=1.5)
        for k in range(2):
            m = y == k
            ax.scatter(X[m,0], X[m,1], c=COLORS[k], marker=MARKERS[k],
                       s=45, edgecolors='k', linewidths=0.5)
        ax.set_xlim(-3, 3); ax.set_ylim(-3, 3)
        ax.set_title(f'Unit {i+1}  w={W2[i,0]:+.2f}')
    plt.suptitle(f'1-hidden-layer ReLU — epoch {frame*10} | acc {acc:.0%}'
                 '   [double-click any panel to focus]')

plt.animate(update, frames=100, interval=100)
plt.show()
"
```

#### Neural network training curves
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(1); losses, accs = [], []
def update(frame):
    t = frame/80
    losses.append(2.3*np.exp(-3*t)+0.08+0.03*np.random.randn())
    accs.append(min(0.99,1-np.exp(-4*t)*0.9+0.01*np.random.randn()))
    axs = plt.gcf().axes
    axs[0].cla(); axs[1].cla()
    axs[0].plot(losses,'b-',linewidth=2); axs[0].set_title('Loss'); axs[0].grid()
    axs[1].plot(accs,'g-',linewidth=2); axs[1].set_title('Accuracy'); axs[1].set_ylim(0,1); axs[1].grid()
plt.subplots(1,2,figsize=(10,4))
plt.animate(update, frames=80, interval=80); plt.show()
"
```

#### fill_between — confidence band widening under distribution shift
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(0)
x = np.linspace(0, 10, 80)
mean = np.sin(x) * np.exp(-x/8)
noise_levels = np.linspace(0.05, 0.6, 30)
def update(frame):
    sigma = noise_levels[frame]
    plt.cla()
    plt.plot(x, mean, 'steelblue', linewidth=2, label='prediction')
    plt.fill_between(x, mean - sigma, mean + sigma, alpha=0.35, color='steelblue', label=f'± {sigma:.2f}')
    plt.fill_between(x, mean - 2*sigma, mean + 2*sigma, alpha=0.15, color='steelblue', label='± 2σ')
    plt.ylim(-1.8, 1.8); plt.legend(); plt.grid()
    plt.title(f'Uncertainty grows under distribution shift — σ={sigma:.2f}')
plt.animate(update, frames=30, interval=150); plt.show()
"
```

#### errorbar — learning curve: accuracy rises, uncertainty shrinks with more data
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(0)
sizes = np.array([10, 25, 50, 100, 200, 400, 800])
means = 1 - 0.88*np.exp(-sizes/120) + 0.015*np.random.randn(len(sizes))
stds  = 0.32*np.exp(-sizes/80) + 0.01
def update(frame):
    n = frame + 1
    plt.cla()
    plt.errorbar(sizes[:n], means[:n], yerr=stds[:n], fmt='o-', capsize=5,
                 color='steelblue', label='accuracy ± std')
    plt.xlim(-30, 850); plt.ylim(0, 1.1)
    plt.xlabel('Training set size'); plt.ylabel('Accuracy')
    plt.title('Learning Curve — more data, less variance'); plt.legend(); plt.grid()
plt.animate(update, frames=len(sizes), interval=600); plt.show()
"
```

#### boxplot — prediction distribution tightens as model trains
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(1)
epochs = [5, 10, 20, 40, 80, 160]
data = [np.random.normal(0.35 + 0.55*(i/len(epochs)), max(0.28 - i*0.04, 0.04), 80)
        for i in range(len(epochs))]
def update(frame):
    n = frame + 1
    plt.cla()
    plt.boxplot(data[:n], labels=[str(e) for e in epochs[:n]])
    plt.ylim(-0.1, 1.1)
    plt.xlabel('Epoch'); plt.ylabel('Predicted probability')
    plt.title(f'Prediction Distribution — epoch {epochs[frame]}')
plt.animate(update, frames=len(epochs), interval=700); plt.show()
"
```

#### violinplot — activation distribution shifts as layers train
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(2)
steps = 6
data = [np.random.normal(i*0.5, max(1.1 - i*0.16, 0.15), 120) for i in range(steps)]
def update(frame):
    n = frame + 1
    plt.cla()
    plt.violinplot(data[:n], positions=list(range(1, n+1)), widths=0.7)
    plt.xlim(0, steps+1); plt.ylim(-3.5, 5.5)
    plt.xlabel('Training step'); plt.ylabel('Activation value')
    plt.title(f'Activation Distribution — step {frame+1} of {steps}')
plt.animate(update, frames=steps, interval=700); plt.show()
"
```

#### pie — class proportions shift as dataset is rebalanced
```bash
python3 -c "
import plotlive.pyplot as plt
labels = ['Negative', 'Neutral', 'Positive']
stages = [[70,20,10],[60,25,15],[50,30,20],[45,32,23],[40,35,25],[33,34,33]]
captions = ['raw','oversample pos','oversample more','near balance','balanced','uniform']
def update(frame):
    plt.cla()
    vals = stages[frame]
    plt.pie(vals, labels=labels, startangle=90)
    pcts = ' | '.join(f'{l}: {v}%' for l,v in zip(labels,vals))
    plt.title(f'Class Balance — {captions[frame]}\n{pcts}')
plt.animate(update, frames=len(stages), interval=900); plt.show()
"
```

#### stackplot — feature contributions accumulate as model complexity grows
```bash
python3 -c "
import plotlive.pyplot as plt, numpy as np
np.random.seed(3)
x = np.arange(20)
feats = ['linear','interactions','polynomials','residuals']
components = [np.abs(np.random.randn(20))*(i+1)*0.4 for i in range(len(feats))]
def update(frame):
    n = frame + 1
    plt.cla()
    plt.stackplot(x, *components[:n], labels=feats[:n], alpha=0.85)
    plt.xlim(0, 19); plt.ylim(0, sum(c.max() for c in components)*1.05)
    plt.xlabel('Sample'); plt.ylabel('Explained variance')
    plt.title(f'Model Complexity — adding {feats[frame]}')
    plt.legend()
plt.animate(update, frames=len(feats), interval=900); plt.show()
"
```

---

### Sorting algorithm visualizations

Each opens its own window with 7 elements, a color legend, and step descriptions.

```bash
cd examples
python3 bubble_sort.py
python3 insertion_sort.py
python3 selection_sort.py
python3 heap_sort.py
python3 merge_sort.py
python3 quick_sort.py
```

| Color | Meaning |
|-------|---------|
| Blue | Unsorted |
| Orange | Being compared |
| Red | Being swapped |
| Green | Confirmed sorted |

Use `←` / `→` to step frame by frame. The value of each element is shown below its bar.

#### Runtime benchmark — all 6 algorithms
```bash
python3 sort_benchmark.py
```

Benchmarks all 6 in the terminal first, then opens an animated log-scale line chart that reveals one input size at a time. Watch O(n²) and O(n log n) algorithms diverge as N grows.

---

## Run tests

```bash
pytest tests/
```

## Dependencies

- `pygame-ce >= 2.4.0`
- `numpy >= 1.24.0`
- Python 3.10+
