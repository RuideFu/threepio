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
    """

    def __init__(
        self,
        device=None,
        timeout=None,
        model=DAQ_MODEL,
        silent=False,
        preload=b"",
        drop=(),
        eol="\r",
    ):
        self.device = device
        self.timeout = timeout
        self.model = model
        self.silent = silent
        self.drop = set(drop)
        self.eol = eol
        self.written = []
        self.buffer = bytearray(preload)

    # Device behavior

    def write(self, data):
        command = data.decode().strip()
        self.written.append(command)
        if self.silent or command in self.drop or command == "start":
            return len(data)
        response = f"info 1 {self.model}" if command == "info 1" else command
        self.buffer += (response + self.eol).encode()
        return len(data)

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
        index = self.buffer.find(expected)
        if index < 0:
            return self.read(len(self.buffer))  # Timed out mid-line
        return self.read(index + len(expected))

    def reset_input_buffer(self):
        self.buffer.clear()


def _tars(tau=None, **kwargs):
    """
    Build a Tars against a fake device. `tau` overrides FILTER_TAU for tests that
    want a known filter coefficient, or disables filtering entirely with tau=0;
    it is read at construction, so patching it here is what the class sees.
    """
    parent = FakeParent()
    serial = FakeSerial(**kwargs)
    tau = tars.FILTER_TAU if tau is None else tau
    with (
        patch.object(tars, "MySerial", lambda device, timeout=None: serial),
        patch.object(tars, "FILTER_TAU", tau),
    ):
        return Tars(parent, device="/dev/fake"), parent, serial


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
    daq, _, serial = _tars(tau=0)
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


def _five_volt_daq(tau=None):
    daq, _, serial = _tars(tau=tau)
    daq.channels = [slist_word(0, volts=5), slist_word(1, volts=5)]
    return daq, serial


def test_filter_alpha_follows_the_configured_scan_rate():
    # The DI-4108 walks the whole scan list at SCAN_RATE, so each of the two
    # channels is sampled at half that. A future edit to srate/dec/channel count
    # that silently detunes the cutoff should fail here.
    daq, _, _ = _tars()
    period = 2 / (tars.BASE_CLOCK_HZ / (tars.SRATE * tars.DECIMATION))

    assert period == pytest.approx(0.02, abs=1e-4)
    assert [f.alpha for f in daq.filters] == [
        pytest.approx(period / (tars.FILTER_TAU + period))
    ] * 2


def test_zero_tau_passes_samples_through_unchanged():
    daq, serial = _five_volt_daq(tau=0)
    assert all(f.alpha == 1.0 for f in daq.filters)

    serial.buffer = bytearray(b"\x00\x40\x00\x20" b"\x00\x60\x00\x10")

    assert daq.read_latest().a == pytest.approx(3.75)


def test_first_sample_is_not_ramped_in_from_zero():
    # Seeding the filter at 0 would make every start() look like a real rising
    # signal for several tau.
    daq, serial = _five_volt_daq()
    serial.buffer = bytearray(b"\x00\x40\x00\x20")

    datum = daq.read_latest()

    assert datum.a == pytest.approx(2.5)
    assert datum.b == pytest.approx(1.25)


def test_read_latest_lowpasses_toward_the_input():
    daq, serial = _five_volt_daq()
    alpha = daq.filters[0].alpha
    # Seeds at (2.5, 1.25), then steps toward (3.75, 0.625).
    serial.buffer = bytearray(b"\x00\x40\x00\x20" b"\x00\x60\x00\x10")

    datum = daq.read_latest()

    assert datum.a == pytest.approx(2.5 + alpha * 1.25)
    assert datum.b == pytest.approx(1.25 - alpha * 0.625)


def test_every_queued_scan_updates_the_filter():
    # A slow tick lets scans queue up. Keeping only the newest would both waste
    # the averaging and stretch the effective time constant.
    daq, serial = _five_volt_daq()
    alpha = daq.filters[0].alpha
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
    daq, serial = _five_volt_daq()
    serial.buffer = bytearray(b"\x00\x40\x00\x20")
    assert daq.read_latest().a == pytest.approx(2.5)

    daq.start()
    serial.buffer = bytearray(b"\x00\x60\x00\x10")

    assert daq.read_latest().a == pytest.approx(3.75)  # Freshly seeded, not blended


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
