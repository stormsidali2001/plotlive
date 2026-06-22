"""Tests for _parsers._parse_fmt and _parse_plot_args."""
import numpy as np
import pytest
from plotlive._parsers import _parse_fmt, _parse_plot_args


# ── _parse_fmt ────────────────────────────────────────────────────────────────

class TestParseFmt:
    def test_empty(self):
        assert _parse_fmt('') == {}

    def test_color_only(self):
        assert _parse_fmt('b') == {'color': 'b'}
        assert _parse_fmt('r') == {'color': 'r'}
        assert _parse_fmt('k') == {'color': 'k'}

    def test_linestyle_solid(self):
        assert _parse_fmt('-')['linestyle'] == '-'

    def test_linestyle_dashed(self):
        assert _parse_fmt('--')['linestyle'] == '--'

    def test_linestyle_dotted(self):
        assert _parse_fmt(':')['linestyle'] == ':'

    def test_linestyle_dashdot(self):
        # '-.' must be parsed before '-'
        r = _parse_fmt('-.')
        assert r['linestyle'] == '-.'
        assert 'marker' not in r

    def test_color_and_linestyle(self):
        r = _parse_fmt('b--')
        assert r['color'] == 'b'
        assert r['linestyle'] == '--'

    def test_color_linestyle_marker(self):
        r = _parse_fmt('ro-')
        assert r['color'] == 'r'
        assert r['linestyle'] == '-'
        assert r['marker'] == 'o'

    def test_marker_only(self):
        r = _parse_fmt('o')
        assert r['marker'] == 'o'
        assert 'linestyle' not in r

    def test_dot_marker(self):
        r = _parse_fmt('.')
        assert r['marker'] == '.'

    def test_triangle_up_marker(self):
        r = _parse_fmt('^')
        assert r['marker'] == '^'

    def test_dashdot_with_color(self):
        r = _parse_fmt('g-.')
        assert r['color'] == 'g'
        assert r['linestyle'] == '-.'

    def test_color_not_duplicated(self):
        # Second color char is treated as marker if needed, but color should only be set once
        r = _parse_fmt('b')
        assert list(r.keys()).count('color') == 1


# ── _parse_plot_args ──────────────────────────────────────────────────────────

class TestParsePlotArgs:
    def test_y_only(self):
        segs = _parse_plot_args(([1, 2, 3],))
        assert len(segs) == 1
        x, y, fmt = segs[0]
        assert x.tolist() == [0.0, 1.0, 2.0]
        assert y.tolist() == [1.0, 2.0, 3.0]
        assert fmt == ''

    def test_x_y(self):
        segs = _parse_plot_args(([0, 1], [4, 5]))
        assert len(segs) == 1
        x, y, fmt = segs[0]
        assert x.tolist() == [0.0, 1.0]
        assert y.tolist() == [4.0, 5.0]
        assert fmt == ''

    def test_x_y_fmt(self):
        segs = _parse_plot_args(([0, 1], [4, 5], 'r--'))
        assert len(segs) == 1
        x, y, fmt = segs[0]
        assert fmt == 'r--'

    def test_y_fmt(self):
        segs = _parse_plot_args(([1, 2, 3], 'b-'))
        assert len(segs) == 1
        _, y, fmt = segs[0]
        assert y.tolist() == [1.0, 2.0, 3.0]
        assert fmt == 'b-'

    def test_multi_segment(self):
        segs = _parse_plot_args(([0, 1], [0, 1], 'r-', [0, 1], [1, 0], 'b--'))
        assert len(segs) == 2
        assert segs[0][2] == 'r-'
        assert segs[1][2] == 'b--'

    def test_numpy_arrays_preserved(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        segs = _parse_plot_args((x, y))
        assert segs[0][0].dtype == float

    def test_unexpected_string_raises(self):
        with pytest.raises(ValueError, match="Unexpected string"):
            _parse_plot_args(('oops', [1, 2, 3]))
