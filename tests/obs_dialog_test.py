import os
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTime
from PySide6.QtWidgets import QApplication

from tools import ObsRecord, Scan, SuperClock
from _dialogs.obs_dialog import ObsDialog

_app = QApplication.instance() or QApplication([])


def make_info_dialog() -> tuple[Scan, ObsDialog]:
    scan = Scan()
    scan.set_start_and_end_times(1000.0, 2000.0)
    scan.set_dec(30.0, 30.0)
    scan.input_record = ObsRecord(
        start_time=QTime(10, 0, 0),
        end_time=QTime(11, 0, 0),
        min_dec="30",
        max_dec="30",
        data_acquisition_rate_value=6,
        file_name_value="info-test",
    )
    dialog = ObsDialog(None, scan, SuperClock(), info=True)
    return scan, dialog


def test_info_accept_leaves_the_live_observation_alone():
    scan, dialog = make_info_dialog()
    file_calls = []
    scan.set_files = lambda: file_calls.append("set_files")

    dialog.accept()

    assert file_calls == []  # no MyPrecious re-creation, so no file truncation
    assert scan.name == "Untitled"  # set_name never ran
    assert scan.start_time == 1000.0  # schedule not re-derived from current LST
    assert scan.end_time == 2000.0


def make_scan_dialog(start: QTime, end: QTime) -> tuple[Scan, SuperClock, ObsDialog]:
    scan = Scan()
    scan.set_files = lambda: None  # keep MyPrecious off the disk
    clock = SuperClock()
    dialog = ObsDialog(None, scan, clock)
    dialog.ui.start_time.setTime(start)
    dialog.ui.end_time.setTime(end)
    dialog.ui.min_dec.setText("30")
    return scan, clock, dialog


def set_observation_at_lst(dialog: ObsDialog, clock: SuperClock, lst_seconds: float):
    with patch.object(clock, "get_sidereal_seconds", return_value=lst_seconds), patch(
        "_tools.superclock.time.time", return_value=1_000_000.0
    ):
        dialog.set_observation()


def test_midnight_wrap_schedules_end_after_start():
    # LST 22:00, start RA 23:30, end RA 00:30 -> a 1-sidereal-hour observation
    scan, clock, dialog = make_scan_dialog(QTime(23, 30, 0), QTime(0, 30, 0))
    set_observation_at_lst(dialog, clock, lst_seconds=22 * 3600)
    assert scan.end_time > scan.start_time
    assert scan.end_time - scan.start_time == pytest.approx(
        SuperClock.sidereal_to_solar(3600)
    )


def test_end_ra_behind_start_ra_wraps_to_next_sidereal_day():
    # LST 10:00, start RA 11:00, end RA 10:30. The end's *next* transit is in
    # 30 minutes, before the start -- the end must anchor to the first transit
    # after the start instead (23.5 sidereal hours later).
    scan, clock, dialog = make_scan_dialog(QTime(11, 0, 0), QTime(10, 30, 0))
    set_observation_at_lst(dialog, clock, lst_seconds=10 * 3600)
    assert scan.end_time > scan.start_time
    assert scan.end_time - scan.start_time == pytest.approx(
        SuperClock.sidereal_to_solar(23.5 * 3600)
    )


def test_equal_start_and_end_ra_rejected():
    scan, clock, dialog = make_scan_dialog(QTime(10, 30, 0), QTime(10, 30, 0))
    with pytest.raises(ValueError, match="differ"):
        set_observation_at_lst(dialog, clock, lst_seconds=9 * 3600)
