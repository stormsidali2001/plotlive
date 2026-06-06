import numpy as np
from mathplotgame.transform import Transform


def make_transform():
    t = Transform()
    t.xlim = (0.0, 10.0)
    t.ylim = (0.0, 5.0)
    t.axes_rect = (0, 0, 100, 50)  # left, top, width, height
    return t


def test_data_to_screen_origin():
    t = make_transform()
    sx, sy = t.data_to_screen(0.0, 0.0)
    assert float(sx) == pytest.approx(0.0)
    # y=0 should map to bottom of screen = top + height
    assert float(sy) == pytest.approx(50.0)


def test_data_to_screen_max():
    t = make_transform()
    sx, sy = t.data_to_screen(10.0, 5.0)
    assert float(sx) == pytest.approx(100.0)
    assert float(sy) == pytest.approx(0.0)


def test_round_trip():
    t = make_transform()
    x_data, y_data = 3.7, 2.1
    sx, sy = t.data_to_screen(x_data, y_data)
    x_back, y_back = t.screen_to_data(float(sx), float(sy))
    assert x_back == pytest.approx(x_data, abs=1e-9)
    assert y_back == pytest.approx(y_data, abs=1e-9)


def test_zoom_anchor():
    t = make_transform()
    # Zoom in at center
    t.zoom(50, 25, 0.5)
    xmin, xmax = t.xlim
    ymin, ymax = t.ylim
    # Should still be centered on (5, 2.5)
    assert (xmin + xmax) / 2 == pytest.approx(5.0, abs=1e-6)
    assert (ymin + ymax) / 2 == pytest.approx(2.5, abs=1e-6)
    # Range should be halved
    assert (xmax - xmin) == pytest.approx(5.0, abs=1e-6)


def test_pan():
    t = make_transform()
    t.pan(10, 0)  # pan right by 10 px -> data shifts right
    xmin, xmax = t.xlim
    assert xmin == pytest.approx(1.0, abs=1e-6)
    assert xmax == pytest.approx(11.0, abs=1e-6)


def test_reset_to_home():
    t = make_transform()
    t.set_home()
    t.pan(50, 0)
    t.reset_to_home()
    assert t.xlim == (0.0, 10.0)
    assert t.ylim == (0.0, 5.0)


def test_contains():
    t = make_transform()
    assert t.contains_screen_point(50, 25)
    assert not t.contains_screen_point(150, 25)


import pytest
