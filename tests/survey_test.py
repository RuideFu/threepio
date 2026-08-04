from tools import Comm, DataPoint, Survey
from _tools.observation import State


class FakeFile:
    """Stands in for MyPrecious so tests never touch ./data/."""

    def __init__(self):
        self.lines: list[str] = []

    def write(self, val):
        self.lines.append(str(val))

    def close(self):
        pass


def make_survey_in_data_state(start=1000.0, end=2000.0) -> Survey:
    survey = Survey()
    survey.set_start_and_end_times(start, end)
    survey.set_dec(20.0, 40.0)
    survey.file_a = FakeFile()
    survey.file_b = FakeFile()
    survey.file_comp = FakeFile()
    survey.state = State.DATA
    return survey


def point(dec: float) -> DataPoint:
    return DataPoint(timestamp=43000.0, dec=dec, a=1.0, b=1.0)


def test_past_end_time_in_band_finishes_sweep():
    survey = make_survey_in_data_state()
    survey.outside = False  # mid-sweep, dish inside the dec band
    assert survey.communicate(point(dec=30.0), timestamp=2001.0) is Comm.FINISHING_SWEEP


def test_past_end_time_out_of_band_starts_calibration():
    survey = make_survey_in_data_state()
    assert survey.communicate(point(dec=10.0), timestamp=2001.0) is Comm.START_CAL


def test_during_data_in_band_records_point():
    survey = make_survey_in_data_state()
    survey.outside = False
    assert survey.communicate(point(dec=30.0), timestamp=1500.0) is Comm.NO_ACTION
    assert survey.file_a.lines and survey.file_b.lines


def test_final_sweep_start_cal_latches_despite_jitter():
    """A dish that is never stopped keeps crossing the dec limit; the
    transmission must not flap back to FINISHING_SWEEP, or every crossing
    re-spawns the 'STOP the telescope' dialog set."""
    survey = make_survey_in_data_state()
    survey.outside = False
    assert survey.communicate(point(dec=30.0), timestamp=2001.0) is Comm.FINISHING_SWEEP
    assert survey.communicate(point(dec=10.0), timestamp=2002.0) is Comm.START_CAL
    assert survey.communicate(point(dec=30.0), timestamp=2003.0) is Comm.START_CAL
    assert survey.communicate(point(dec=10.0), timestamp=2004.0) is Comm.START_CAL


def test_no_data_written_after_final_sweep():
    survey = make_survey_in_data_state()
    assert survey.communicate(point(dec=10.0), timestamp=2001.0) is Comm.START_CAL
    survey.communicate(point(dec=30.0), timestamp=2002.0)
    survey.communicate(point(dec=30.0), timestamp=2003.0)
    assert survey.file_a.lines == []
