from tools import Comm, DataPoint, Pulsar, Scan
from _tools.observation import State


class FakeFile:
    """Stands in for MyPrecious so tests never touch ./data/."""

    def __init__(self):
        self.lines: list[str] = []

    def write(self, val):
        self.lines.append(str(val))

    def close(self):
        pass


def make_pulsar_in_data_state(start=1000.0, end=2000.0) -> Pulsar:
    pulsar = Pulsar()
    pulsar.set_start_and_end_times(start, end)
    pulsar.set_dec(20.0, 20.0)
    pulsar.file_a = FakeFile()
    pulsar.file_b = FakeFile()
    pulsar.file_comp = FakeFile()
    pulsar.state = State.DATA
    return pulsar


def point(timestamp=43000.0) -> DataPoint:
    return DataPoint(timestamp=timestamp, dec=20.0, a=1.0, b=2.0)


def test_pulsar_is_a_scan():
    assert isinstance(Pulsar(), Scan)


def test_pulsar_asks_for_unfiltered_full_rate_data():
    assert Pulsar.FILTERED is False
    assert Pulsar.RECORDS_EVERY_SAMPLE is True
    # A plain scan must keep the filtering and the communicate()-paced recording
    assert Scan.FILTERED is True
    assert Scan.RECORDS_EVERY_SAMPLE is False


def test_communicating_during_data_does_not_write():
    """Recording is record_sample()'s job; writing here too would duplicate a
    sample once per communicate() call."""
    pulsar = make_pulsar_in_data_state()

    assert pulsar.communicate(point(), timestamp=1500.0) is Comm.NO_ACTION

    assert pulsar.file_a.lines == []
    assert pulsar.file_b.lines == []


def test_every_sample_is_recorded_during_data():
    pulsar = make_pulsar_in_data_state()

    for i in range(3):
        pulsar.record_sample(point(timestamp=43000.0 + i), timestamp=1500.0)

    # timestamp, dec per point in file_a; timestamp, dec, and the value in file_b
    assert pulsar.file_a.lines == [
        "43000.0000", "20.0000", "1.0000",
        "43001.0000", "20.0000", "1.0000",
        "43002.0000", "20.0000", "1.0000",
    ]
    assert pulsar.file_b.lines[2::3] == ["2.0000", "2.0000", "2.0000"]


def test_timestamps_resolve_the_acquisition_rate():
    """20 ms between samples needs finer than the .2f a scan writes."""
    pulsar = make_pulsar_in_data_state()

    pulsar.record_sample(point(timestamp=43000.02), timestamp=1500.0)
    pulsar.record_sample(point(timestamp=43000.04), timestamp=1500.0)

    assert pulsar.file_a.lines[0] != pulsar.file_a.lines[3]


def test_samples_outside_the_data_phase_are_not_recorded():
    pulsar = make_pulsar_in_data_state()

    pulsar.record_sample(point(), timestamp=999.0)  # Before the scheduled start
    pulsar.record_sample(point(), timestamp=2000.0)  # At the scheduled end
    pulsar.state = State.CAL_1
    pulsar.record_sample(point(), timestamp=1500.0)  # Calibration, not data

    assert pulsar.file_a.lines == []


def test_calibration_still_writes_through_communicate():
    """The cal and background phases are unchanged from a scan."""
    pulsar = make_pulsar_in_data_state()
    pulsar.state = State.CAL_1
    pulsar.cal_start = 900.0

    assert pulsar.communicate(point(), timestamp=910.0) is Comm.NO_ACTION

    assert pulsar.file_a.lines != []
