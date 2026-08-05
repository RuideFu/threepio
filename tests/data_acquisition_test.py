import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from threepio.threepio import Threepio
except ImportError:
    from threepio import Threepio  # type: ignore[attr-defined,no-redef]

from _tools.tars import SignalDatum


class FakeDevice:
    def __init__(self, *readings):
        self.readings = list(readings)

    def read_latest(self):
        return self.readings.pop(0)


class FakeClock:
    @staticmethod
    def get_sidereal_seconds():
        return 123.0


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

    def __init__(self, tars_readings, dec_readings, current_dec=12.0):
        self.tars = FakeDevice(*tars_readings)
        self.minitars = FakeDevice(*dec_readings)
        self.clock = FakeClock()
        self.dec_calc = FakeDecCalc()
        self.scheduler = FakeScheduler()
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


def test_latest_declination_is_reused_on_a_later_dataq_tick():
    app = FakeThreepio([None, SignalDatum(3.0, 4.0)], [41.0, None])

    app.tick()
    app.tick()

    assert len(app.data) == 1
    assert app.current_data_point.dec == 42.0
