import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from threepio.threepio import Threepio
except ImportError:
    from threepio import Threepio  # type: ignore[attr-defined,no-redef]
from _tools.observation import State


class FakeScheduler:
    def reset_timer_anchors(self):
        pass


class FakeObs:
    def __init__(self):
        self.state = State.DATA
        self.next_calls = 0

    def next(self):
        self.next_calls += 1
        self.state = State.CAL_2


class FakeThreepio:
    """Just enough of Threepio to exercise make_advance_obs_callback."""

    make_advance_obs_callback = Threepio.make_advance_obs_callback

    def __init__(self):
        self.obs = FakeObs()
        self.scheduler = FakeScheduler()

    def message(self, text, **kwargs):
        pass


def test_duplicate_callbacks_advance_state_only_once():
    fake = FakeThreepio()
    first = fake.make_advance_obs_callback("Taking calibration data!!!")
    duplicate = fake.make_advance_obs_callback("Taking calibration data!!!")
    first()
    duplicate()
    assert fake.obs.next_calls == 1
    assert fake.obs.state is State.CAL_2


def test_callback_is_noop_after_observation_cleared():
    fake = FakeThreepio()
    callback = fake.make_advance_obs_callback("Taking calibration data!!!")
    fake.obs = None
    callback()  # Must not raise
