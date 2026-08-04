import os

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
