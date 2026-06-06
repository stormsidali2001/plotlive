import pytest
from mathplotgame.colors import to_rgba, get_cmap


def test_named():
    assert to_rgba('red')[:3] == (255, 0, 0)
    assert to_rgba('blue')[:3] == (0, 0, 255)
    assert to_rgba('white')[:3] == (255, 255, 255)
    assert to_rgba('black')[:3] == (0, 0, 0)


def test_single_char():
    assert to_rgba('b')[:3] == (31, 119, 180)
    assert to_rgba('r')[:3] == (214, 39, 40)


def test_hex():
    assert to_rgba('#FF0000')[:3] == (255, 0, 0)
    assert to_rgba('#0000ff')[:3] == (0, 0, 255)
    assert to_rgba('#F00')[:3] == (255, 0, 0)


def test_cycle_alias():
    c0 = to_rgba('C0')
    assert c0[:3] == (31, 119, 180)


def test_float_tuple():
    r = to_rgba((1.0, 0.0, 0.0))
    assert r[:3] == (255, 0, 0)


def test_grayscale_string():
    g = to_rgba('0.5')
    assert g[0] == g[1] == g[2]


def test_none():
    assert to_rgba('none')[3] == 0


def test_alpha_param():
    r = to_rgba('red', alpha=0.5)
    assert r[3] == 128  # 0.5 * 255 rounded


def test_colormaps():
    cmap = get_cmap('viridis')
    lo = cmap(0.0)
    hi = cmap(1.0)
    assert lo.shape == (4,)
    assert hi.shape == (4,)
    assert lo[3] == 255

    with pytest.raises(KeyError):
        get_cmap('nonexistent_cmap')
