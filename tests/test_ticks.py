from mathplotgame.ticks import auto_ticks, format_tick, format_ticks


def test_basic():
    ticks = auto_ticks(0, 10)
    assert len(ticks) >= 3
    assert min(ticks) >= 0
    assert max(ticks) <= 10


def test_zero_range():
    ticks = auto_ticks(5.0, 5.0)
    assert ticks == [5.0]


def test_negative_range():
    ticks = auto_ticks(-10, -1)
    assert all(-10 <= t <= -1 for t in ticks)
    assert len(ticks) >= 3


def test_small_range():
    ticks = auto_ticks(0.001, 0.005)
    assert len(ticks) >= 2


def test_no_float_drift():
    ticks = auto_ticks(0, 1)
    for t in ticks:
        # No tick should have excessive decimal noise
        assert abs(t - round(t, 10)) < 1e-9


def test_format_int():
    assert format_tick(5.0, 1.0) == '5'


def test_format_decimal():
    s = format_tick(0.5, 0.1)
    assert '0.5' in s


def test_format_ticks_list():
    labels = format_ticks([0, 2, 4, 6, 8, 10])
    assert labels[0] == '0'
    assert all(isinstance(l, str) for l in labels)
