from strategy.pairs_signal import generate_positions
import pandas as pd


def test_generate_positions_basic():
    zscore = pd.Series([
        None,
        -2.1,
        -2.5,
        -1.0,
        -0.4,
        0.2,
        2.2,
        3.6,
        0.3
    ])

    result = generate_positions(
        zscore,
        entry_threshold=2.0,
        exit_threshold=0.5,
        stop_threshold=3.5
    )

    expected = pd.Series(
        [0, 1, 1, 1, 0, 0, -1, 0, 0],
        dtype="float64"
    )

    assert result.equals(expected)

def test_generate_positions_no_stop():
    zscore = pd.Series([
        None,
        -2.1,
        -3.6,  # 本来ならstop
        -1.0,
        -0.4
    ])

    result = generate_positions(
        zscore,
        entry_threshold=2.0,
        exit_threshold=0.5,
        stop_threshold=None
    )

    expected = pd.Series(
        [0, 1, 1, 1, 0],
        dtype="float64"
    )

    assert result.equals(expected)