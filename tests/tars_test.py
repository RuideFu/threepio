import statistics
from unittest.mock import patch

import pytest

import _tools.tars as tars
from _tools.tars import DAQ_MODEL, DEFAULT_RANGE_VOLT, Tars, range_volt, slist_word


class FakeParent:
    def __init__(self):
        self.logged = []

    def log(self, message, allow_dups=False, warning=False):
        self.logged.append((message, warning))

    def warnings(self):
        return [message for message, warning in self.logged if warning]


class FakeSerial:
    """
    Stands in for the DI-4108. Echoes every command it is written, the way the
    real device does while it is not scanning, and returns b"" from a read it
    cannot satisfy, the way pyserial does when the port timeout expires.

    With `stalling`, it also reproduces the ~1 s the real device spends applying
    "stop" and "encode": it answers neither them nor the next few commands
    unless the reader widens its timeout enough to wait the pause out.
    """

    STALLED_COMMANDS = 3  # How many later commands a stall swallows

    def __init__(
        self,
        device=None,
        timeout=None,
        model=DAQ_MODEL,
        silent=False,
        preload=b"",
        drop=(),
        eol="\r",
        stalling=False,
    ):
        self.device = device
        self.timeout = timeout
        self.model = model
        self.silent = silent
        self.drop = set(drop)
        self.eol = eol
        self.stalling = stalling
        self.stalled = 0
        self.written = []
        self.read_timeouts = []
        self.buffer = bytearray(preload)

    # Device behavior

    def write(self, data):
        command = data.decode().strip()
        self.written.append(command)
        if self.silent or command in self.drop or command == "start":
            return len(data)
        if self.stalling and not self._answers(command):
            return len(data)
        response = f"info 1 {self.model}" if command == "info 1" else command
        self.buffer += (response + self.eol).encode()
        return len(data)

    def _answers(self, command) -> bool:
        """Whether a stalling device is in any state to reply to `command`."""
        if command.split()[0] in Tars.SLOW_COMMANDS:
            if self.timeout is None or self.timeout < 1.0:
                # Not waited on, so the echo lands in nobody's read, and the
                # device stays busy through whatever is sent next.
                self.stalled = self.STALLED_COMMANDS
                return False
            return True
        if self.stalled:
            self.stalled -= 1
            return False
        return True

    # pyserial surface

    @property
    def in_waiting(self):
        return len(self.buffer)

    def read(self, size=1):
        if len(self.buffer) < size:  # Short of `size` bytes, the read times out
            return b""
        chunk = bytes(self.buffer[:size])
        del self.buffer[:size]
        return chunk

    def read_until(self, expected=b"\n", size=None):
        self.read_timeouts.append((self.written[-1] if self.written else None, self.timeout))
        index = self.buffer.find(expected)
        if index < 0:
            return self.read(len(self.buffer))  # Timed out mid-line
        return self.read(index + len(expected))

    def reset_input_buffer(self):
        self.buffer.clear()


def _tars(tau=None, kind=None, **kwargs):
    """
    Build a Tars against a fake device. `tau` and `kind` override FILTER_TAU and
    FILTER_KIND for tests that want a known filter; both are read at construction,
    so patching them here is what the class sees.
    """
    parent = FakeParent()
    serial = FakeSerial(**kwargs)
    tau = tars.FILTER_TAU if tau is None else tau
    kind = tars.FILTER_KIND if kind is None else kind
    def open_port(device, timeout=None):
        serial.device, serial.timeout = device, timeout
        return serial

    with (
        patch.object(tars, "MySerial", open_port),
        patch.object(tars, "FILTER_TAU", tau),
        patch.object(tars, "FILTER_KIND", kind),
    ):
        return Tars(parent, device="/dev/fake"), parent, serial


def _alpha(daq):
    """The lowpass coefficient of a channel's chain."""
    (lowpass,) = [
        s for s in daq.filters[0].stages if isinstance(s, tars.SinglePoleLowpass)
    ]
    return lowpass.alpha


def _config_commands(serial):
    return [command for command in serial.written if command not in ("stop", "info 1")]


def _expected_config_commands():
    return [
        "encode 0",
        "ps 0",
        f"slist 0 {slist_word(0)}",
        f"slist 1 {slist_word(1)}",
        "dec 512",
        "srate 1171",
    ]


# - MARK: scan list words


def test_slist_word_packs_channel_and_range():
    # Bits 3:0 are the channel, bits 11:8 the range code; +/-5 V is code 1.
    assert slist_word(0) == slist_word(0, volts=DEFAULT_RANGE_VOLT)
    assert slist_word(0, volts=5) == 0x0100
    assert slist_word(1, volts=5) == 0x0101
    assert slist_word(1, volts=10) == 0x0001
    assert slist_word(7, volts=0.2) == 0x0507


@pytest.mark.parametrize("code,volts", list(enumerate(Tars.RANGE_VOLT)))
def test_range_volt_round_trips_every_documented_range(code, volts):
    word = slist_word(3, volts=volts)
    assert word >> 8 == code
    assert range_volt(word) == volts


# - MARK: buffer_read


@pytest.mark.parametrize(
    "raw,expected",
    [
        (b"\xff\x7f", 5 * 32767 / 32768),  # Positive full scale, 4.99985 V
        (b"\x00\x80", -5.0),  # Negative full scale
        (b"\x00\x00", 0.0),
        (b"\xff\xff", -5 / 32768),  # -1 count
        (b"\x00\x40", 2.5),  # Pins byte order: little-endian 0x4000
    ],
)
def test_buffer_read_decodes_the_documented_adc_coding(raw, expected):
    daq, _, serial = _tars()
    serial.buffer = bytearray(raw)
    assert daq.buffer_read(slist_word(0, volts=5)) == pytest.approx(expected)


def test_buffer_read_returns_none_without_a_whole_sample():
    daq, _, serial = _tars()
    serial.buffer = bytearray(b"\x01")
    assert daq.buffer_read(slist_word(0)) is None


# - MARK: setup


def test_setup_verifies_the_model_and_every_configuration_command():
    daq, parent, serial = _tars()

    assert daq.configured is True
    assert parent.warnings() == []
    assert serial.written[0] == "stop"
    assert "info 1" in serial.written
    assert _config_commands(serial) == _expected_config_commands()


def test_setup_reports_the_configured_range():
    _, parent, _ = _tars()
    assert any(f"±{DEFAULT_RANGE_VOLT} V" in message for message, _ in parent.logged)


def test_setup_warns_when_the_model_is_not_a_4108():
    # A DI-4208 answers commands identically but reads +/-2.5 where RANGE_VOLT
    # says +/-2, so the range table would silently misscale its samples.
    daq, parent, _ = _tars(model="4208")

    assert daq.configured is False
    assert any("4208" in message for message in parent.warnings())


def test_setup_warns_when_a_range_command_is_not_confirmed():
    command = f"slist 1 {slist_word(1)}"
    daq, parent, _ = _tars(drop=[command])

    assert daq.configured is False
    assert any(command in message for message in parent.warnings())


def test_setup_waits_out_the_commands_that_stall_the_device():
    # "stop" and "encode" take ~1 s on the real DI-4108. Reading their echo at
    # the ordinary timeout gives up first, and everything sent behind them is
    # swallowed -- which reads as a mute device and configures it blind.
    daq, parent, serial = _tars(stalling=True)

    assert daq.configured is True
    assert parent.warnings() == []
    assert _config_commands(serial) == _expected_config_commands()


def test_only_the_stalling_commands_get_the_longer_timeout():
    # The wide timeout is what an absent echo costs, so it stays off the
    # commands that answer immediately.
    _, _, serial = _tars()
    waited = dict(serial.read_timeouts)

    assert waited["stop"] == Tars.SLOW_COMMAND_TIMEOUT
    assert waited["encode 0"] == Tars.SLOW_COMMAND_TIMEOUT
    assert waited["info 1"] == Tars.COMMAND_TIMEOUT
    assert waited[f"slist 0 {slist_word(0)}"] == Tars.COMMAND_TIMEOUT
    # And the port is handed back at its normal setting.
    assert serial.timeout == Tars.COMMAND_TIMEOUT


def test_setup_configures_blind_when_the_device_does_not_echo():
    daq, parent, serial = _tars(silent=True)

    assert daq.configured is False
    assert any("not echoing" in message for message in parent.warnings())
    # Still fully configured, and the buffer flushed, so behavior is no worse
    # than before echo verification existed.
    assert _config_commands(serial) == _expected_config_commands()
    assert serial.in_waiting == 0


def test_setup_drains_samples_left_over_from_a_crashed_session():
    # A device still scanning from a previous run buries the "stop" echo behind
    # binary samples; anything left would be decoded as data and shift alignment.
    daq, parent, serial = _tars(preload=b"\x11\x22\x33\x44\x55")

    assert daq.configured is True
    assert parent.warnings() == []


def test_setup_tolerates_crlf_terminated_echoes():
    # read_until("\r") leaves the "\n" behind, so it arrives as the first byte
    # of the next echo; verification compares tokens rather than raw bytes.
    daq, parent, _ = _tars(eol="\r\n")

    assert daq.configured is True
    assert parent.warnings() == []


def test_setup_tolerates_silent_encode_and_nul_padded_echoes():
    # The real DI-4108 does not echo "encode 0" and commonly appends a NUL
    # after CR. read_until(CR) leaves that byte at the front of the next echo.
    daq, parent, _ = _tars(drop=["encode 0"], eol="\r\x00")

    assert daq.configured is True
    assert parent.warnings() == []


def test_read_latest_decodes_both_channels():
    # Unfiltered, so this stays a test of the decoding alone.
    daq, _, serial = _tars(kind=tars.FilterKind.NONE)
    daq.channels = [slist_word(0, volts=5), slist_word(1, volts=5)]
    # Two scans of (channel A, channel B), little-endian, +/-5 V range.
    serial.buffer = bytearray(b"\x00\x40\x00\x20" b"\x00\x60\x00\x10")

    datum = daq.read_latest()

    assert datum.a == pytest.approx(3.75)  # 0x6000 = 24576 counts
    assert datum.b == pytest.approx(0.625)  # 0x1000 = 4096 counts
    assert serial.in_waiting == 0


def test_read_latest_returns_none_without_a_whole_scan():
    # An empty read must stay None: tick() appends to the data list on anything
    # that is not None, so returning the held filter state would double the
    # recorded data rate.
    daq, _, _ = _tars()
    assert daq.read_latest() is None


# - MARK: lowpass filter


def _five_volt_daq(tau=None, kind=None):
    daq, _, serial = _tars(tau=tau, kind=kind)
    daq.channels = [slist_word(0, volts=5), slist_word(1, volts=5)]
    return daq, serial


def test_filter_alpha_follows_the_configured_scan_rate():
    # srate/dec set how often the DI-4108 walks the scan list, and every channel
    # is sampled once per walk, so the per-channel period is 1/SCAN_RATE however
    # many channels there are. A future edit to srate/dec that silently detunes
    # the cutoff should fail here.
    daq, _, _ = _tars(kind=tars.FilterKind.SINGLE_POLE)
    period = 1 / (tars.BASE_CLOCK_HZ / (tars.SRATE * tars.DECIMATION))

    assert period == pytest.approx(0.01, abs=1e-4)
    assert _alpha(daq) == pytest.approx(period / (tars.FILTER_TAU + period))


def test_sample_period_is_the_scan_interval_not_the_throughput():
    # Measured on the hardware: 99.9 scans/s with two channels in the scan list
    # and 99.9 with four, so a wider list raises throughput, not scan rate.
    # Scaling this by the channel count would stretch every back-dated pulsar
    # timestamp and detune the filter by the same factor.
    daq, _, _ = _tars()

    assert daq.sample_period == pytest.approx(1 / tars.SCAN_RATE)
    assert daq.sample_period == pytest.approx(0.01, abs=1e-4)


def test_filter_kind_none_passes_samples_through_unchanged():
    daq, serial = _five_volt_daq(kind=tars.FilterKind.NONE)
    assert daq.filters[0].stages == ()

    serial.buffer = bytearray(b"\x00\x40\x00\x20" b"\x00\x60\x00\x10")

    assert daq.read_latest().a == pytest.approx(3.75)


def test_zero_tau_passes_samples_through_unchanged():
    daq, serial = _five_volt_daq(tau=0, kind=tars.FilterKind.SINGLE_POLE)
    assert _alpha(daq) == 1.0

    serial.buffer = bytearray(b"\x00\x40\x00\x20" b"\x00\x60\x00\x10")

    assert daq.read_latest().a == pytest.approx(3.75)


def test_first_sample_is_not_ramped_in_from_zero():
    # Seeding the filter at 0 would make every start() look like a real rising
    # signal for several tau.
    daq, serial = _five_volt_daq(kind=tars.FilterKind.SINGLE_POLE)
    serial.buffer = bytearray(b"\x00\x40\x00\x20")

    datum = daq.read_latest()

    assert datum.a == pytest.approx(2.5)
    assert datum.b == pytest.approx(1.25)


def test_read_latest_lowpasses_toward_the_input():
    daq, serial = _five_volt_daq(kind=tars.FilterKind.SINGLE_POLE)
    alpha = _alpha(daq)
    # Seeds at (2.5, 1.25), then steps toward (3.75, 0.625).
    serial.buffer = bytearray(b"\x00\x40\x00\x20" b"\x00\x60\x00\x10")

    datum = daq.read_latest()

    assert datum.a == pytest.approx(2.5 + alpha * 1.25)
    assert datum.b == pytest.approx(1.25 - alpha * 0.625)


def test_every_queued_scan_updates_the_filter():
    # A slow tick lets scans queue up. Keeping only the newest would both waste
    # the averaging and stretch the effective time constant.
    daq, serial = _five_volt_daq(kind=tars.FilterKind.SINGLE_POLE)
    alpha = _alpha(daq)
    # Seed at 0 V, then hold 2.5 V for two more scans.
    serial.buffer = bytearray(
        b"\x00\x00\x00\x00" b"\x00\x40\x00\x40" b"\x00\x40\x00\x40"
    )

    datum = daq.read_latest()

    assert datum.a == pytest.approx(2.5 * (1 - (1 - alpha) ** 2))
    assert datum.a != pytest.approx(2.5 * alpha)  # Only the last scan applied


def test_start_resets_the_filter():
    # start() flushes the input buffer, so the pre-flush value must not bleed
    # across the gap.
    daq, serial = _five_volt_daq(kind=tars.FilterKind.SINGLE_POLE)
    serial.buffer = bytearray(b"\x00\x40\x00\x20")
    assert daq.read_latest().a == pytest.approx(2.5)

    daq.start()
    serial.buffer = bytearray(b"\x00\x60\x00\x10")

    assert daq.read_latest().a == pytest.approx(3.75)  # Freshly seeded, not blended


# - MARK: Hampel filter


def _hampel(window=5, sigmas=3.0):
    return tars.HampelFilter(window=window, sigmas=sigmas)


def _feed(f, samples):
    return [f.update(x) for x in samples]


def test_hampel_passes_a_partly_filled_window_through():
    # Judging a spike against 2 neighbors mostly rejects good data instead.
    f = _hampel(window=5)
    assert _feed(f, [1.0, 9.0, 1.0, 1.0]) == [1.0, 9.0, 1.0, 1.0]


def test_hampel_replaces_a_spike_with_the_local_median():
    f = _hampel(window=5)
    noise = [1.0, 1.1, 0.9, 1.05, 0.95]
    _feed(f, noise)

    assert f.update(50.0) == pytest.approx(statistics.median(noise[1:] + [50.0]))


def test_hampel_leaves_ordinary_samples_untouched():
    # It is a despiker, not a smoother: inliers come out bit-for-bit unchanged.
    f = _hampel(window=5)
    samples = [1.0, 1.1, 0.9, 1.05, 0.95, 1.02, 0.98, 1.03]

    assert _feed(f, samples) == samples


def test_hampel_passes_through_when_the_window_has_no_spread():
    # A quiet channel resting on one ADC code makes MAD exactly 0. Without the
    # guard, every deviation is "infinitely" many sigmas and the output clamps
    # to the median, quantizing away small real changes.
    f = _hampel(window=5)
    _feed(f, [2.0] * 5)

    assert f.update(2.0001) == pytest.approx(2.0001)


def test_hampel_survives_a_run_of_bad_samples():
    # The median and MAD tolerate up to half the window being corrupt, where a
    # mean and standard deviation would let one spike hide itself.
    f = _hampel(window=7)
    _feed(f, [1.0, 1.1, 0.9, 1.05, 0.95, 1.02, 0.98])

    # Three consecutive spikes in a 7-window: still a clean majority, so every
    # one comes back at the surrounding level instead of 80.
    assert _feed(f, [80.0] * 3) == pytest.approx([1.02, 1.02, 1.05])


def test_hampel_gives_up_once_the_bad_samples_are_the_majority():
    # The honest limit of the window: 4 of 7 corrupt makes the spike level the
    # median, and it passes through as if it were the signal.
    f = _hampel(window=7)
    _feed(f, [1.0, 1.1, 0.9, 1.05, 0.95, 1.02, 0.98])

    assert _feed(f, [80.0] * 4)[-1] == pytest.approx(80.0)


def test_hampel_reset_forgets_the_window():
    f = _hampel(window=5)
    _feed(f, [1.0] * 5)
    f.reset()

    # Back to a partly-filled window, so this passes through instead of being
    # judged against the pre-reset samples.
    assert f.update(50.0) == 50.0


# - MARK: filter chain


def test_both_despikes_before_smoothing():
    # Order matters: a spike that reaches the lowpass is smeared across the
    # following ~tau of output, so removing it afterward is impossible.
    daq, _, _ = _tars(kind=tars.FilterKind.BOTH)
    stages = daq.filters[0].stages

    assert [type(s) for s in stages] == [tars.HampelFilter, tars.SinglePoleLowpass]


@pytest.mark.parametrize(
    "kind,expected",
    [
        (tars.FilterKind.NONE, []),
        (tars.FilterKind.SINGLE_POLE, [tars.SinglePoleLowpass]),
        (tars.FilterKind.HAMPEL, [tars.HampelFilter]),
        (tars.FilterKind.BOTH, [tars.HampelFilter, tars.SinglePoleLowpass]),
    ],
)
def test_every_filter_kind_builds_its_chain(kind, expected):
    chain = tars.make_filter(kind, period=0.02)
    assert [type(s) for s in chain.stages] == expected


def test_chain_resets_every_stage():
    chain = tars.make_filter(tars.FilterKind.BOTH, period=0.02)
    _feed(chain, [1.0] * 10)
    chain.reset()

    hampel, lowpass = chain.stages
    assert len(hampel.samples) == 0
    assert lowpass.value is None


def test_lowpass_step_response_converges_on_the_input():
    lowpass = tars.SinglePoleLowpass(tau=0.3, period=0.02)

    lowpass.update(0.0)
    for _ in range(1000):
        value = lowpass.update(1.0)

    assert value == pytest.approx(1.0)

    lowpass.reset()
    assert lowpass.update(4.2) == pytest.approx(4.2)  # Reseeds, no memory of 1.0


def test_start_flushes_before_scanning():
    daq, _, serial = _tars()
    serial.buffer = bytearray(b"\x99")  # A stray byte would offset every sample

    daq.start()

    assert serial.written[-1] == "start"
    assert serial.in_waiting == 0
    assert daq.acquiring is True


def test_simulated_device_never_touches_the_port():
    daq = Tars(FakeParent(), device=None)
    assert daq.testing is True
    assert daq.configured is False
    assert daq.buffer_read(slist_word(0)) is None
