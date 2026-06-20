from __future__ import annotations
import math
import numpy as np

# matplotlib single-char shortcuts
_SINGLE_CHAR: dict[str, tuple[int, int, int]] = {
    'b': (31, 119, 180),
    'r': (214, 39, 40),
    'g': (44, 160, 44),
    'y': (188, 189, 34),
    'k': (0, 0, 0),
    'w': (255, 255, 255),
    'm': (148, 103, 189),
    'c': (23, 190, 207),
}

# Default color cycle (matplotlib tab10)
DEFAULT_CYCLE: list[tuple[int, int, int]] = [
    (31, 119, 180),
    (255, 127, 14),
    (44, 160, 44),
    (214, 39, 40),
    (148, 103, 189),
    (140, 86, 75),
    (227, 119, 194),
    (127, 127, 127),
    (188, 189, 34),
    (23, 190, 207),
]

# CSS named colors (subset)
_NAMED: dict[str, tuple[int, int, int]] = {
    'aliceblue': (240, 248, 255), 'antiquewhite': (250, 235, 215),
    'aqua': (0, 255, 255), 'aquamarine': (127, 255, 212),
    'azure': (240, 255, 255), 'beige': (245, 245, 220),
    'bisque': (255, 228, 196), 'black': (0, 0, 0),
    'blanchedalmond': (255, 235, 205), 'blue': (0, 0, 255),
    'blueviolet': (138, 43, 226), 'brown': (165, 42, 42),
    'burlywood': (222, 184, 135), 'cadetblue': (95, 158, 160),
    'chartreuse': (127, 255, 0), 'chocolate': (210, 105, 30),
    'coral': (255, 127, 80), 'cornflowerblue': (100, 149, 237),
    'cornsilk': (255, 248, 220), 'crimson': (220, 20, 60),
    'cyan': (0, 255, 255), 'darkblue': (0, 0, 139),
    'darkcyan': (0, 139, 139), 'darkgoldenrod': (184, 134, 11),
    'darkgray': (169, 169, 169), 'darkgreen': (0, 100, 0),
    'darkgrey': (169, 169, 169), 'darkkhaki': (189, 183, 107),
    'darkmagenta': (139, 0, 139), 'darkolivegreen': (85, 107, 47),
    'darkorange': (255, 140, 0), 'darkorchid': (153, 50, 204),
    'darkred': (139, 0, 0), 'darksalmon': (233, 150, 122),
    'darkseagreen': (143, 188, 143), 'darkslateblue': (72, 61, 139),
    'darkslategray': (47, 79, 79), 'darkturquoise': (0, 206, 209),
    'darkviolet': (148, 0, 211), 'deeppink': (255, 20, 147),
    'deepskyblue': (0, 191, 255), 'dimgray': (105, 105, 105),
    'dodgerblue': (30, 144, 255), 'firebrick': (178, 34, 34),
    'floralwhite': (255, 250, 240), 'forestgreen': (34, 139, 34),
    'fuchsia': (255, 0, 255), 'gainsboro': (220, 220, 220),
    'ghostwhite': (248, 248, 255), 'gold': (255, 215, 0),
    'goldenrod': (218, 165, 32), 'gray': (128, 128, 128),
    'green': (0, 128, 0), 'greenyellow': (173, 255, 47),
    'grey': (128, 128, 128), 'honeydew': (240, 255, 240),
    'hotpink': (255, 105, 180), 'indianred': (205, 92, 92),
    'indigo': (75, 0, 130), 'ivory': (255, 255, 240),
    'khaki': (240, 230, 140), 'lavender': (230, 230, 250),
    'lawngreen': (124, 252, 0), 'lemonchiffon': (255, 250, 205),
    'lightblue': (173, 216, 230), 'lightcoral': (240, 128, 128),
    'lightcyan': (224, 255, 255), 'lightgray': (211, 211, 211),
    'lightgreen': (144, 238, 144), 'lightgrey': (211, 211, 211),
    'lightpink': (255, 182, 193), 'lightsalmon': (255, 160, 122),
    'lightseagreen': (32, 178, 170), 'lightskyblue': (135, 206, 250),
    'lightslategray': (119, 136, 153), 'lightsteelblue': (176, 196, 222),
    'lightyellow': (255, 255, 224), 'lime': (0, 255, 0),
    'limegreen': (50, 205, 50), 'linen': (250, 240, 230),
    'magenta': (255, 0, 255), 'maroon': (128, 0, 0),
    'mediumaquamarine': (102, 205, 170), 'mediumblue': (0, 0, 205),
    'mediumorchid': (186, 85, 211), 'mediumpurple': (147, 112, 219),
    'mediumseagreen': (60, 179, 113), 'mediumslateblue': (123, 104, 238),
    'mediumspringgreen': (0, 250, 154), 'mediumturquoise': (72, 209, 204),
    'mediumvioletred': (199, 21, 133), 'midnightblue': (25, 25, 112),
    'mintcream': (245, 255, 250), 'mistyrose': (255, 228, 225),
    'moccasin': (255, 228, 181), 'navajowhite': (255, 222, 173),
    'navy': (0, 0, 128), 'oldlace': (253, 245, 230),
    'olive': (128, 128, 0), 'olivedrab': (107, 142, 35),
    'orange': (255, 165, 0), 'orangered': (255, 69, 0),
    'orchid': (218, 112, 214), 'palegoldenrod': (238, 232, 170),
    'palegreen': (152, 251, 152), 'paleturquoise': (175, 238, 238),
    'palevioletred': (219, 112, 147), 'papayawhip': (255, 239, 213),
    'peachpuff': (255, 218, 185), 'peru': (205, 133, 63),
    'pink': (255, 192, 203), 'plum': (221, 160, 221),
    'powderblue': (176, 224, 230), 'purple': (128, 0, 128),
    'rebeccapurple': (102, 51, 153), 'red': (255, 0, 0),
    'rosybrown': (188, 143, 143), 'royalblue': (65, 105, 225),
    'saddlebrown': (139, 69, 19), 'salmon': (250, 128, 114),
    'sandybrown': (244, 164, 96), 'seagreen': (46, 139, 87),
    'seashell': (255, 245, 238), 'sienna': (160, 82, 45),
    'silver': (192, 192, 192), 'skyblue': (135, 206, 235),
    'slateblue': (106, 90, 205), 'slategray': (112, 128, 144),
    'slategrey': (112, 128, 144), 'snow': (255, 250, 250),
    'springgreen': (0, 255, 127), 'steelblue': (70, 130, 180),
    'tan': (210, 180, 140), 'teal': (0, 128, 128),
    'thistle': (216, 191, 216), 'tomato': (255, 99, 71),
    'turquoise': (64, 224, 208), 'violet': (238, 130, 238),
    'wheat': (245, 222, 179), 'white': (255, 255, 255),
    'whitesmoke': (245, 245, 245), 'yellow': (255, 255, 0),
    'yellowgreen': (154, 205, 50),
}


def to_rgba(color, alpha: float = 1.0) -> tuple[int, int, int, int]:
    """Parse any matplotlib color spec into (R, G, B, A) uint8 tuple."""
    if color is None:
        return (0, 0, 0, 0)

    a = int(round(alpha * 255))

    # Already a tuple/list
    if isinstance(color, (tuple, list)):
        vals = list(color)
        if len(vals) == 4:
            # Has embedded alpha — use it
            if all(isinstance(v, float) and v <= 1.0 for v in vals):
                return (int(round(vals[0]*255)), int(round(vals[1]*255)),
                        int(round(vals[2]*255)), int(round(vals[3]*255)))
            return (int(vals[0]), int(vals[1]), int(vals[2]), int(vals[3]))
        if len(vals) == 3:
            if all(isinstance(v, float) for v in vals) and all(0.0 <= v <= 1.0 for v in vals):
                return (int(round(vals[0]*255)), int(round(vals[1]*255)),
                        int(round(vals[2]*255)), a)
            return (int(vals[0]), int(vals[1]), int(vals[2]), a)
        raise ValueError(f"Color tuple must have 3 or 4 elements, got {color}")

    # numpy array
    if isinstance(color, np.ndarray):
        return to_rgba(color.tolist(), alpha)

    if not isinstance(color, str):
        raise ValueError(f"Unrecognized color: {color!r}")

    s = color.strip()

    # 'none' / 'None'
    if s.lower() == 'none':
        return (0, 0, 0, 0)

    # Single char
    if s in _SINGLE_CHAR:
        r, g, b = _SINGLE_CHAR[s]
        return (r, g, b, a)

    # Cycle alias C0-C9
    if len(s) == 2 and s[0] == 'C' and s[1].isdigit():
        r, g, b = DEFAULT_CYCLE[int(s[1])]
        return (r, g, b, a)

    # Hex
    if s.startswith('#'):
        h = s[1:]
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        if len(h) == 6:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)
        if len(h) == 8:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))
        raise ValueError(f"Bad hex color: {color!r}")

    # Grayscale string '0.5'
    try:
        v = float(s)
        g_val = int(round(v * 255))
        return (g_val, g_val, g_val, a)
    except ValueError:
        pass

    # Named color
    low = s.lower()
    if low in _NAMED:
        r, g, b = _NAMED[low]
        return (r, g, b, a)

    raise ValueError(f"Unrecognized color: {color!r}")


# ---------------------------------------------------------------------------
# Colormaps
# ---------------------------------------------------------------------------

class Colormap:
    def __init__(self, name: str, stops: list[tuple[float, float, float, float]]):
        self.name = name
        self._stops = sorted(stops, key=lambda s: s[0])

    def __call__(self, t: float | np.ndarray) -> np.ndarray:
        t_arr = np.asarray(t, dtype=float)
        scalar = t_arr.ndim == 0
        t_arr = np.atleast_1d(np.clip(t_arr, 0.0, 1.0))
        result = np.zeros((*t_arr.shape, 4), dtype=np.uint8)
        stops = self._stops
        for i, ti in np.ndenumerate(t_arr):
            # find surrounding stops
            if ti <= stops[0][0]:
                _, r, g, b = stops[0]
                result[i] = (int(r*255), int(g*255), int(b*255), 255)
                continue
            if ti >= stops[-1][0]:
                _, r, g, b = stops[-1]
                result[i] = (int(r*255), int(g*255), int(b*255), 255)
                continue
            for j in range(len(stops) - 1):
                t0, r0, g0, b0 = stops[j]
                t1, r1, g1, b1 = stops[j+1]
                if t0 <= ti <= t1:
                    f = (ti - t0) / (t1 - t0)
                    result[i] = (
                        int((r0 + f*(r1-r0))*255),
                        int((g0 + f*(g1-g0))*255),
                        int((b0 + f*(b1-b0))*255),
                        255,
                    )
                    break
        if scalar:
            return result[0]
        return result

    def to_lut(self, n: int = 256) -> np.ndarray:
        t = np.linspace(0.0, 1.0, n)
        return self(t)


def _make_colormaps() -> dict[str, Colormap]:
    cmaps = {}

    # viridis
    cmaps['viridis'] = Colormap('viridis', [
        (0.0,  0.267, 0.005, 0.329),
        (0.25, 0.230, 0.322, 0.546),
        (0.5,  0.128, 0.566, 0.551),
        (0.75, 0.370, 0.788, 0.384),
        (1.0,  0.993, 0.906, 0.144),
    ])

    # plasma
    cmaps['plasma'] = Colormap('plasma', [
        (0.0,  0.051, 0.031, 0.529),
        (0.25, 0.459, 0.063, 0.608),
        (0.5,  0.798, 0.165, 0.412),
        (0.75, 0.973, 0.463, 0.129),
        (1.0,  0.940, 0.975, 0.131),
    ])

    # inferno
    cmaps['inferno'] = Colormap('inferno', [
        (0.0,  0.0,   0.0,   0.016),
        (0.25, 0.220, 0.016, 0.388),
        (0.5,  0.576, 0.149, 0.404),
        (0.75, 0.902, 0.435, 0.196),
        (1.0,  0.988, 1.0,   0.643),
    ])

    # magma
    cmaps['magma'] = Colormap('magma', [
        (0.0,  0.0,   0.0,   0.016),
        (0.25, 0.208, 0.012, 0.392),
        (0.5,  0.588, 0.114, 0.475),
        (0.75, 0.929, 0.518, 0.608),
        (1.0,  0.988, 0.992, 0.749),
    ])

    # coolwarm (diverging, blue->white->red)
    cmaps['coolwarm'] = Colormap('coolwarm', [
        (0.0,  0.227, 0.341, 0.749),
        (0.5,  0.867, 0.867, 0.867),
        (1.0,  0.706, 0.016, 0.149),
    ])

    # RdBu (diverging)
    cmaps['RdBu'] = Colormap('RdBu', [
        (0.0,  0.404, 0.004, 0.122),
        (0.25, 0.839, 0.376, 0.302),
        (0.5,  0.969, 0.969, 0.969),
        (0.75, 0.404, 0.663, 0.812),
        (1.0,  0.020, 0.188, 0.380),
    ])

    # Blues
    cmaps['Blues'] = Colormap('Blues', [
        (0.0, 0.969, 0.984, 1.0),
        (0.5, 0.420, 0.682, 0.839),
        (1.0, 0.031, 0.188, 0.420),
    ])

    # Reds
    cmaps['Reds'] = Colormap('Reds', [
        (0.0, 1.0,   0.961, 0.941),
        (0.5, 0.988, 0.553, 0.349),
        (1.0, 0.404, 0.0,   0.051),
    ])

    # jet (legacy)
    cmaps['jet'] = Colormap('jet', [
        (0.0,  0.0,  0.0,  0.5),
        (0.11, 0.0,  0.0,  1.0),
        (0.35, 0.0,  1.0,  1.0),
        (0.5,  0.0,  0.5,  0.0),
        (0.66, 1.0,  1.0,  0.0),
        (0.89, 1.0,  0.0,  0.0),
        (1.0,  0.5,  0.0,  0.0),
    ])

    # gray
    cmaps['gray'] = Colormap('gray', [
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0, 1.0),
    ])
    cmaps['grey'] = cmaps['gray']

    return cmaps


_COLORMAPS = _make_colormaps()


def get_cmap(name: str) -> Colormap:
    if name not in _COLORMAPS:
        raise KeyError(f"Unknown colormap {name!r}. Available: {list(_COLORMAPS)}")
    return _COLORMAPS[name]
