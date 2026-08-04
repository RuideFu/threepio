from unittest.mock import patch

from tools import Comm, DataPoint, Scan
from _tools.observation import State, get_date, get_time


class FakeFile:
    """Stands in for MyPrecious so tests never touch ./data/."""

    def __init__(self):
        self.lines: list[str] = []

    def write(self, val):
        self.lines.append(str(val))

    def close(self):
        pass


def make_scan(start=1000.0, end=2000.0) -> Scan:
    scan = Scan()
    scan.set_start_and_end_times(start, end)
    scan.set_dec(30.0, 30.0)
    scan.file_a = FakeFile()
    scan.file_b = FakeFile()
    scan.file_comp = FakeFile()
    return scan


def point() -> DataPoint:
    return DataPoint(timestamp=43000.0, dec=30.0, a=1.0, b=1.0)


def test_starting_calibration_preserves_scheduled_start_time():
    scan = make_scan(start=1000.0, end=2000.0)
    scan.next()  # OFF -> CAL_1
    assert scan.state is State.CAL_1
    assert scan.start_time == 1000.0


def test_waiting_holds_until_scheduled_start():
    scan = make_scan(start=1000.0, end=2000.0)
    scan.state = State.WAITING
    assert scan.communicate(point(), timestamp=999.0) is Comm.NO_ACTION
    assert scan.communicate(point(), timestamp=1000.5) is Comm.START_DATA


def test_waiting_does_not_stall_on_a_late_start():
    scan = make_scan(start=1000.0, end=2000.0)
    scan.state = State.WAITING
    assert scan.communicate(point(), timestamp=1750.0) is Comm.START_DATA


def test_footer_records_factual_data_start_and_stop():
    scan = make_scan(start=1000.0, end=2000.0)
    scan.state = State.WAITING
    with patch("_tools.observation.time.time", return_value=1234.0):
        scan.next()  # WAITING -> DATA
    assert scan.data_start == 1234.0

    scan.state = State.BG_2
    with patch("_tools.observation.time.time", return_value=2345.0):
        scan.next()  # BG_2 -> stop()
    assert scan.state is State.DONE

    footer = scan.file_a.lines
    assert "LOCAL START DATE: " + get_date(1234.0) in footer
    assert "LOCAL START TIME: " + get_time(1234.0) in footer
    assert "LOCAL STOP DATE: " + get_date(2345.0) in footer
    assert "LOCAL STOP TIME: " + get_time(2345.0) in footer
