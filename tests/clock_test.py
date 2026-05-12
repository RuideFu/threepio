from unittest.mock import patch

from _tools.superclock import SIDEREAL, SuperClock


def test_sidereal_wraparound():
    clock = SuperClock()
    with patch.object(clock, "propagation_anchor_sidereal_seconds", 86399.0), patch(
        "_tools.superclock.time.monotonic", return_value=clock.propagation_anchor_monotonic + 2.0
    ):
        value = clock.get_sidereal_seconds()
    assert 0.0 <= value < 86400.0


def test_monotonic_progression_math():
    clock = SuperClock()
    clock.propagation_anchor_sidereal_seconds = 1000.0
    clock.propagation_anchor_monotonic = 50.0
    with patch("_tools.superclock.time.monotonic", return_value=55.0):
        value = clock.get_sidereal_seconds()
    assert abs(value - (1000.0 + 5.0 * SIDEREAL)) < 1e-6


def test_manual_calibration_offset_preserved_on_resync():
    clock = SuperClock()
    with patch.object(clock, "_sidereal_seconds_from_astropy", return_value=100.0), patch(
        "_tools.superclock.time.time", return_value=1000.0
    ), patch("_tools.superclock.time.monotonic", return_value=500.0):
        clock.calibrate_sidereal_time(160.0)

    assert abs(clock.manual_sidereal_offset_seconds - 60.0) < 1e-6

    with patch.object(clock, "_sidereal_seconds_from_astropy", return_value=200.0), patch(
        "_tools.superclock.time.time", return_value=1100.0
    ), patch("_tools.superclock.time.monotonic", return_value=600.0):
        clock.resync_from_astropy()

    assert abs(clock.propagation_anchor_sidereal_seconds - 260.0) < 1e-6


def test_ra_to_epoch_time_conversion():
    clock = SuperClock()
    with patch.object(clock, "get_sidereal_seconds", return_value=1000.0), patch(
        "_tools.superclock.time.time", return_value=2000.0
    ):
        epoch = clock.ra_to_epoch_time(1100.0)
    assert abs(epoch - (2000.0 + SuperClock.sidereal_to_solar(100.0))) < 1e-6
