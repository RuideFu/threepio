import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from threepio.threepio import Threepio
except ImportError:
    from threepio import Threepio  # type: ignore[attr-defined,no-redef]

from _tools.tars import SignalDatum


class FakeDevice:
    sample_period = 0.01  # The DI-4108's scan interval at the configured srate/dec

    def __init__(self, *readings):
        self.readings = list(readings)

    def read_latest(self):
        return self.readings.pop(0)

    def read_all(self):
        """A reading of None stands for 'nothing arrived this tick'."""
        reading = self.readings.pop(0)
        return [] if reading is None else [reading]


class FakeClock:
    @staticmethod
    def get_sidereal_seconds():
        return 123.0

    @staticmethod
    def get_time():
        return 1000.0

    @staticmethod
    def solar_to_sidereal(solar_seconds):
        return solar_seconds


class FakeDecCalc:
    @staticmethod
    def calculate_declination(raw):
        return raw + 1.0


class FakeScheduler:
    @staticmethod
    def run_timers():
        pass


class FakeThreepio:
    """Just enough of Threepio to exercise its acquisition tick."""

    tick = Threepio.tick
    record_samples = Threepio.record_samples

    def __init__(self, tars_readings, dec_readings, current_dec=12.0, obs=None):
        self.tars = FakeDevice(*tars_readings)
        self.minitars = FakeDevice(*dec_readings)
        self.clock = FakeClock()
        self.dec_calc = FakeDecCalc()
        self.scheduler = FakeScheduler()
        self.obs = obs
        self.current_dec = current_dec
        self.current_data_point = None
        self.data = []
        self.ticks_since_last_fps_update = 0

    def update_stripchart(self):
        pass

    def update_dec_view(self):
        pass


def test_dataq_reading_is_kept_when_declinometer_is_silent():
    app = FakeThreepio([SignalDatum(8.0, -0.01)], [None])

    app.tick()

    assert len(app.data) == 1
    assert app.current_data_point.a == 8.0
    assert app.current_data_point.b == -0.01
    assert app.current_data_point.dec == 12.0


def test_a_batch_of_scans_is_kept_whole_with_spaced_timestamps():
    """A tick that finds several scans queued must keep them all, and must not
    stamp them with the same RA -- at the pulsar data rate that is the signal.

    The offsets come from the DAQ's scan interval, so overstating that interval
    back-dates a batch past the end of the previous one and the recorded
    timestamps stop increasing."""
    app = FakeThreepio([None], [None])
    app.tars.readings = []

    app.record_samples(
        [SignalDatum(1.0, 1.5), SignalDatum(2.0, 2.5), SignalDatum(3.0, 3.5)],
        sidereal_timestamp=123.0,
    )

    assert [point.a for point in app.data] == [1.0, 2.0, 3.0]
    assert [point.timestamp for point in app.data] == [122.98, 122.99, 123.0]


def test_latest_declination_is_reused_on_a_later_dataq_tick():
    app = FakeThreepio([None, SignalDatum(3.0, 4.0)], [41.0, None])

    app.tick()
    app.tick()

    assert len(app.data) == 1
    assert app.current_data_point.dec == 42.0
