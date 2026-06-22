"""Smoke-test every code example from README, docs, and marketing-assets.md.

Each entry is an isolated subprocess — no shared pyplot state.
Animated examples call save_animation() instead of show() so they run headless.
"""
import subprocess, sys, os, textwrap, tempfile, shutil

PYTHON = '.venv/bin/python'
ENV = {**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}

HEADER = textwrap.dedent("""\
    import sys, os
    sys.path.insert(0, 'src')
    import numpy as np
    import plotlive.pyplot as plt
""")

# Each snippet: (name, code)
# Animated snippets use a tmp dir for output; static snippets call savefig.
EXAMPLES = []

def static(name, code):
    EXAMPLES.append(('static', name, textwrap.dedent(code).strip()))

def animated(name, code):
    EXAMPLES.append(('animated', name, textwrap.dedent(code).strip()))

# ── README / docs static ──────────────────────────────────────────────────────

static('training_curves', """
    np.random.seed(0)
    x = np.arange(50)
    plt.figure(figsize=(8, 5))
    plt.plot(x, np.exp(-x/10), label='train loss')
    plt.plot(x, np.exp(-x/12) + 0.05*np.random.randn(50), label='val loss')
    plt.fill_between(x, np.exp(-x/10)-0.05, np.exp(-x/10)+0.05, alpha=0.2, label='± 1σ')
    plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.title('Training Curve')
    plt.legend(); plt.grid()
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('confusion_matrix', """
    cm = np.array([[50,2,1],[3,45,5],[2,4,48]])
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap='Blues')
    plt.colorbar(im, ax=ax); ax.set_title('Confusion Matrix')
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('feature_importance_errorbar', """
    feats = ['age','income','tenure','score','region']
    vals  = [0.40, 0.30, 0.18, 0.08, 0.04]
    errs  = [0.04, 0.03, 0.02, 0.01, 0.005]
    plt.figure(figsize=(7, 4))
    plt.barh(feats, vals)
    plt.errorbar(vals, range(len(feats)), xerr=errs, fmt='none', color='black', capsize=4)
    plt.xlabel('Importance'); plt.title('Feature Importance ± std')
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('distribution_comparison', """
    np.random.seed(0)
    data = [np.random.normal(m, s, 120) for m, s in [(0,1),(1,1.5),(3,0.5),(-1,2)]]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    ax1.boxplot(data); ax1.set_title('Box Plot')
    ax2.violinplot(data); ax2.set_title('Violin Plot')
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('correlation_heatmap', """
    np.random.seed(0)
    corr = np.corrcoef(np.random.randn(5, 100))
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
    plt.colorbar(im, ax=ax); ax.set_title('Correlation Matrix')
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('stacked_area', """
    np.random.seed(1)
    x = np.arange(20)
    a = np.random.dirichlet([3,2,1], 20).T
    plt.figure(figsize=(8, 4))
    plt.stackplot(x, a[0], a[1], a[2], labels=['Class A','Class B','Class C'], alpha=0.85)
    plt.xlabel('Time step'); plt.ylabel('Proportion'); plt.title('Class Distribution Over Time')
    plt.legend()
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('pie_chart', """
    plt.figure(figsize=(5, 5))
    plt.pie([52, 31, 17], labels=['Negative','Neutral','Positive'], startangle=90)
    plt.title('Sentiment Distribution'); plt.legend()
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('subplots_2x2', """
    np.random.seed(0)
    fig, axs = plt.subplots(2, 2, figsize=(11, 8))
    x = np.arange(50)
    axs[0,0].plot(x, np.exp(-x/10), label='train')
    axs[0,0].plot(x, np.exp(-x/12)+0.05*np.random.randn(50), label='val')
    axs[0,0].set_title('Training Curves'); axs[0,0].legend()
    cm = np.array([[50,2,1],[3,45,5],[2,4,48]])
    im = axs[0,1].imshow(cm, cmap='Blues'); axs[0,1].set_title('Confusion Matrix')
    feats=['age','income','tenure','score']; vals=[0.4,0.3,0.18,0.08]
    axs[1,0].barh(feats, vals); axs[1,0].set_title('Feature Importance')
    X2 = np.random.randn(60, 2); c2 = (X2[:,0]>0).astype(float)
    axs[1,1].scatter(X2[:,0],X2[:,1],c=c2,cmap='coolwarm',s=40); axs[1,1].set_title('Scatter')
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('scatter_tooltip', """
    np.random.seed(0)
    X = np.random.randn(80, 2)
    labels = (X[:,0]+X[:,1] > 0).astype(float)
    plt.scatter(X[:,0], X[:,1], c=labels, cmap='viridis', s=60, alpha=0.8)
    plt.xlabel('Feature 1'); plt.ylabel('Feature 2'); plt.title('Scatter')
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('axhline_axvline', """
    x = np.linspace(-3, 3, 100)
    plt.plot(x, np.sin(x))
    plt.axhline(y=0, color='k', linewidth=0.8)
    plt.axvline(x=0, color='k', linewidth=0.8)
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('log_scale', """
    x = np.logspace(0, 3, 50)
    plt.figure()
    plt.plot(x, x**2, label='x^2')
    plt.xscale('log'); plt.yscale('log')
    plt.xlabel('x'); plt.ylabel('y'); plt.legend()
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

static('custom_ticks', """
    plt.figure()
    plt.plot([0,1,2], [0,1,0])
    plt.xticks([0, 1, 2], ['zero', 'one', 'two'])
    plt.yticks([0, 0.5, 1])
    plt.savefig('/tmp/_plotlive_smoke.png')
""")

# ── README animated ───────────────────────────────────────────────────────────

animated('gradient_descent', """
    x = np.linspace(-3, 3, 200); w = [2.5]
    plt.figure(figsize=(7, 5))
    def update(frame):
        w[0] -= 0.15 * 2 * w[0]
        plt.cla()
        plt.plot(x, x**2, 'b-', linewidth=2, label='f(w)=w²')
        plt.scatter([w[0]], [w[0]**2], c='red', s=120, zorder=5, label=f'w={w[0]:.3f}')
        plt.fill_between(x, 0, x**2, alpha=0.07)
        plt.ylim(-0.2, 7); plt.legend()
        plt.title(f'Gradient Descent  step {frame+1}')
    plt.animate(update, frames=8, interval=200)
    plt.save_animation('{out}/gradient_descent.gif', fps=10)
""")

animated('kmeans', """
    np.random.seed(7); K = 3
    data = np.vstack([np.random.randn(60,2)*0.7+c for c in [(-2,-2),(2,-2),(0,2)]])
    centroids = data[np.random.choice(len(data),K,replace=False)].copy()
    plt.figure(figsize=(6, 6))
    def update(frame):
        global centroids
        labels = np.array([[np.linalg.norm(p-c) for c in centroids] for p in data]).argmin(1).astype(float)
        centroids = np.array([data[labels==k].mean(0) if (labels==k).any() else centroids[k] for k in range(K)])
        plt.cla()
        plt.scatter(data[:,0],data[:,1],c=labels,cmap='viridis',s=40,alpha=0.7)
        plt.scatter(centroids[:,0],centroids[:,1],c='red',s=220,marker='*',zorder=5,label='Centroids')
        plt.legend(); plt.title(f'K-Means  iteration {{frame+1}}')
    plt.animate(update, frames=5, interval=500)
    plt.save_animation('{out}/kmeans.gif', fps=4)
""")

animated('softmax_classifier', """
    np.random.seed(0); K = 3
    centers = [(-2,-1),(2,-1),(0,2.5)]
    X = np.vstack([np.random.randn(50,2)*0.8+c for c in centers])
    y = np.repeat(np.arange(K), 50)
    W = np.zeros((2,K)); b = np.zeros(K)
    MARKERS=['+','o','^']
    COLORS=['#e74c3c','#3498db','#2ecc71']
    BD_COLORS=['#8e44ad','#e67e22','#2c3e50']
    x_edge=np.array([-5.5,5.5])
    def softmax(z):
        e=np.exp(z-z.max(axis=1,keepdims=True))
        return e/e.sum(axis=1,keepdims=True)
    def plot_boundary(i,j,color):
        dw=W[:,i]-W[:,j]; db=b[i]-b[j]
        if abs(dw[1])<1e-9: return
        plt.plot(x_edge,-(dw[0]*x_edge+db)/dw[1],color=color,linewidth=2,label=f'Boundary {{i}} vs {{j}}')
    def update(frame):
        global W, b
        for _ in range(5):
            p=softmax(X@W+b); oh=np.eye(K)[y]
            W-=0.1*(X.T@(p-oh))/len(X); b-=0.1*(p-oh).mean(axis=0)
        plt.cla()
        for k in range(K):
            m=y==k; plt.scatter(X[m,0],X[m,1],c=COLORS[k],marker=MARKERS[k],s=80,label=f'Class {{k}}')
        for (i,j),col in zip([(0,1),(0,2),(1,2)],BD_COLORS): plot_boundary(i,j,col)
        acc=(np.argmax(X@W+b,axis=1)==y).mean()
        plt.xlim(-5,5); plt.ylim(-4,5); plt.legend()
        plt.title(f'Softmax  epoch {{frame*5}}  acc {{acc:.0%}}')
    plt.figure(figsize=(7,6))
    plt.animate(update, frames=10, interval=100)
    plt.save_animation('{out}/softmax.gif', fps=10)
""")

animated('relu_network', """
    np.random.seed(0); n_h=8
    theta=np.linspace(0,np.pi,60)
    X0=np.c_[np.cos(theta),np.sin(theta)]+np.random.randn(60,2)*0.15
    X1=np.c_[1-np.cos(theta),0.5-np.sin(theta)]+np.random.randn(60,2)*0.15
    X=np.vstack([X0,X1]); X=(X-X.mean(0))/X.std(0)
    y=np.repeat([0,1],60)
    W1=np.random.randn(2,n_h)*np.sqrt(2/2); b1=np.zeros(n_h)
    W2=np.random.randn(n_h,1)*np.sqrt(2/n_h); b2=np.zeros(1)
    g=16; gx,gy=np.linspace(-3,3,g),np.linspace(-3,3,g)
    xx,yy=np.meshgrid(gx,gy); grid=np.c_[xx.ravel(),yy.ravel()]
    gx_flat=xx.ravel(); gy_flat=yy.ravel()
    x_edge=np.array([-3.5,3.5])
    COLORS=['#e74c3c','#3498db']; MARKERS=['o','^']
    def relu(z): return np.maximum(0,z)
    def sigmoid(z): return 1/(1+np.exp(-np.clip(z,-50,50)))
    def forward(Xb):
        z1=Xb@W1+b1; return sigmoid(relu(z1)@W2+b2).ravel(),z1
    fig,axs=plt.subplots(2,4,figsize=(12,6))
    def update(frame):
        global W1,b1,W2,b2
        for _ in range(10):
            p,z1=forward(X); a1=relu(z1); N=len(X)
            dz2=(p-y).reshape(-1,1)/N
            dW2=a1.T@dz2; db2=dz2.sum(0)
            dz1=(dz2@W2.T)*(z1>0)
            W1-=0.05*X.T@dz1; b1-=0.05*dz1.sum(0)
            W2-=0.05*dW2; b2-=0.05*db2
        p_tr,_=forward(X); acc=((p_tr>0.5).astype(int)==y).mean()
        _,z1_g=forward(grid)
        for i,ax in enumerate(axs.flat):
            ax.cla()
            active=z1_g[:,i]>0
            ax.scatter(gx_flat[~active],gy_flat[~active],c='#eeeeee',s=20)
            ax.scatter(gx_flat[active],gy_flat[active],c='#c6e2f5',s=20)
            w,bv=W1[:,i],b1[i]
            if abs(w[1])>1e-9: ax.plot(x_edge,-(w[0]*x_edge+bv)/w[1],'k-',linewidth=1.5)
            for k in range(2):
                m=y==k; ax.scatter(X[m,0],X[m,1],c=COLORS[k],marker=MARKERS[k],s=30)
            ax.set_xlim(-3,3); ax.set_ylim(-3,3)
            ax.set_title(f'U{{i+1}} w={{W2[i,0]:+.2f}}')
        plt.suptitle(f'ReLU epoch {{frame*10}} acc {{acc:.0%}}')
    plt.animate(update, frames=8, interval=100)
    plt.save_animation('{out}/relu_network.gif', fps=8)
""")

animated('training_curves_anim', """
    losses, accs = [], []
    fig, _ = plt.subplots(1, 2, figsize=(9, 4))
    def update(frame):
        t = frame/20
        losses.append(2.3*np.exp(-3*t)+0.08+0.03*np.random.randn())
        accs.append(min(0.99, 1-np.exp(-4*t)*0.9+0.01*np.random.randn()))
        ax0, ax1 = plt.gcf().axes[0], plt.gcf().axes[1]
        ax0.cla(); ax1.cla()
        ax0.plot(losses,'b-',linewidth=2); ax0.set_title('Loss'); ax0.grid()
        ax1.plot(accs,'g-',linewidth=2); ax1.set_title('Accuracy'); ax1.set_ylim(0,1); ax1.grid()
    plt.animate(update, frames=20, interval=80)
    plt.save_animation('{out}/training_curves_anim.gif', fps=15)
""")

animated('fill_between_bands', """
    np.random.seed(0)
    x = np.linspace(0, 10, 80)
    mean = np.sin(x) * np.exp(-x/8)
    noise_levels = np.linspace(0.05, 0.6, 12)
    plt.figure(figsize=(8, 4))
    def update(frame):
        sigma = noise_levels[frame]
        plt.cla()
        plt.plot(x, mean, 'steelblue', linewidth=2, label='prediction')
        plt.fill_between(x, mean-sigma, mean+sigma, alpha=0.35, color='steelblue', label=f'±{{sigma:.2f}}')
        plt.fill_between(x, mean-2*sigma, mean+2*sigma, alpha=0.15, color='steelblue', label='±2σ')
        plt.ylim(-1.8, 1.8); plt.legend(); plt.grid()
        plt.title(f'Distribution shift  σ={{sigma:.2f}}')
    plt.animate(update, frames=len(noise_levels), interval=150)
    plt.save_animation('{out}/fill_between.gif', fps=6)
""")

animated('errorbar_learning', """
    np.random.seed(0)
    sizes = np.array([10, 25, 50, 100, 200, 400, 800])
    means = 1 - 0.88*np.exp(-sizes/120) + 0.015*np.random.randn(len(sizes))
    stds  = 0.32*np.exp(-sizes/80) + 0.01
    plt.figure(figsize=(8, 4))
    def update(frame):
        n = frame + 1
        plt.cla()
        plt.errorbar(sizes[:n], means[:n], yerr=stds[:n], fmt='o-', capsize=5,
                     color='steelblue', label='accuracy ± std')
        plt.xlim(-30, 850); plt.ylim(0, 1.1)
        plt.xlabel('Training set size'); plt.ylabel('Accuracy')
        plt.title('Learning Curve'); plt.legend(); plt.grid()
    plt.animate(update, frames=len(sizes), interval=600)
    plt.save_animation('{out}/errorbar_learning.gif', fps=2)
""")

animated('boxplot_epoch', """
    np.random.seed(1)
    epochs = [5, 10, 20, 40, 80, 160]
    data = [np.random.normal(0.35+0.55*(i/len(epochs)), max(0.28-i*0.04,0.04), 80)
            for i in range(len(epochs))]
    plt.figure(figsize=(8, 4))
    def update(frame):
        n = frame + 1
        plt.cla()
        plt.boxplot(data[:n], labels=[str(e) for e in epochs[:n]])
        plt.ylim(-0.1, 1.1)
        plt.xlabel('Epoch'); plt.ylabel('Predicted probability')
        plt.title(f'Prediction Distribution  epoch {{epochs[frame]}}')
    plt.animate(update, frames=len(epochs), interval=700)
    plt.save_animation('{out}/boxplot_epoch.gif', fps=2)
""")

animated('violinplot_activation', """
    np.random.seed(2)
    steps = 6
    data = [np.random.normal(i*0.5, max(1.1-i*0.16,0.15), 120) for i in range(steps)]
    plt.figure(figsize=(8, 4))
    def update(frame):
        n = frame + 1
        plt.cla()
        plt.violinplot(data[:n], positions=list(range(1,n+1)), widths=0.7)
        plt.xlim(0, steps+1); plt.ylim(-3.5, 5.5)
        plt.xlabel('Training step'); plt.ylabel('Activation value')
        plt.title(f'Activation Distribution  step {{frame+1}} of {{steps}}')
    plt.animate(update, frames=steps, interval=700)
    plt.save_animation('{out}/violinplot_activation.gif', fps=2)
""")

animated('pie_rebalancing', """
    labels = ['Negative', 'Neutral', 'Positive']
    stages = [[70,20,10],[60,25,15],[50,30,20],[45,32,23],[40,35,25],[33,34,33]]
    captions = ['raw','oversample pos','oversample more','near balance','balanced','uniform']
    plt.figure(figsize=(5, 5))
    def update(frame):
        plt.cla()
        vals = stages[frame]
        plt.pie(vals, labels=labels, startangle=90)
        pcts = ' | '.join(f'{{l}}: {{v}}%' for l,v in zip(labels,vals))
        plt.title(f'Class Balance  {{captions[frame]}}')
    plt.animate(update, frames=len(stages), interval=900)
    plt.save_animation('{out}/pie_rebalancing.gif', fps=1)
""")

animated('stackplot_complexity', """
    np.random.seed(3)
    x = np.arange(20)
    feats = ['linear','interactions','polynomials','residuals']
    components = [np.abs(np.random.randn(20))*(i+1)*0.4 for i in range(len(feats))]
    plt.figure(figsize=(8, 4))
    def update(frame):
        n = frame + 1
        plt.cla()
        plt.stackplot(x, *components[:n], labels=feats[:n], alpha=0.85)
        plt.xlim(0, 19); plt.ylim(0, sum(c.max() for c in components)*1.05)
        plt.xlabel('Sample'); plt.ylabel('Explained variance')
        plt.title(f'Model Complexity  adding {{feats[frame]}}')
        plt.legend()
    plt.animate(update, frames=len(feats), interval=900)
    plt.save_animation('{out}/stackplot_complexity.gif', fps=1)
""")

# ── Marketing-assets snippets ─────────────────────────────────────────────────

animated('marketing_export_headless', """
    x = np.linspace(-3,3,200); w=[2.5]
    plt.figure(figsize=(7, 5))
    def update(f):
        w[0]-=0.15*2*w[0]; plt.cla()
        plt.plot(x,x**2,'b-',linewidth=2,label='f(w)=w²')
        plt.scatter([w[0]],[w[0]**2],c='red',s=120,zorder=5,label=f'w={{w[0]:.3f}}')
        plt.ylim(-0.2,7); plt.legend(); plt.title(f'step {{f+1}}')
    plt.animate(update,frames=8,interval=200)
    plt.save_animation('{out}/marketing_export.gif',fps=10)
""")


def run_example(kind, name, code, outdir):
    if '{out}' in code:
        code = code.replace('{out}', outdir)
    full = HEADER + '\n' + code
    result = subprocess.run(
        [PYTHON, '-c', full],
        env=ENV, capture_output=True, text=True, timeout=120
    )
    ok = result.returncode == 0
    if not ok:
        print(f'  FAIL  [{kind}] {name}')
        # show last 15 lines of stderr
        for line in result.stderr.strip().splitlines()[-15:]:
            print(f'        {line}')
    else:
        print(f'  ok    [{kind}] {name}')
    return ok


if __name__ == '__main__':
    outdir = tempfile.mkdtemp(prefix='plotlive_smoke_')
    passed = failed = 0
    try:
        for kind, name, code in EXAMPLES:
            try:
                if run_example(kind, name, code, outdir):
                    passed += 1
                else:
                    failed += 1
            except subprocess.TimeoutExpired:
                print(f'  TIMEOUT  [{kind}] {name}')
                failed += 1
    finally:
        shutil.rmtree(outdir, ignore_errors=True)

    total = passed + failed
    print(f'\n{passed}/{total} passed', '✓' if failed == 0 else f'  ({failed} FAILED)')
    sys.exit(0 if failed == 0 else 1)
