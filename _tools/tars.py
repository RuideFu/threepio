"""
This module includes a Tars class that encapsulate a serialpy object and provides
simple methods for initializing, starting, stopping, resetting, and reading from
the DATAQ device connected via a USB serial connection. The module also includes
a few helper functions relevant to the tasks.
"""

import os

import serial
from .myserial import MySerial
import serial.tools.list_ports
import time

import random as r  # For testing
import math
import statistics
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class SignalDatum:
    a: float
    b: float


DAQ_PORT_ENV = "THREEPIO_DAQ_PORT"
DEC_PORT_ENV = "THREEPIO_DEC_PORT"
NATIVE_DEC_PORT = "/dev/serial0"

# Every DATAQ range table is model-specific: Tars.RANGE_VOLT is the DI-4108
# column. A DI-4208 reads +/-2.5 where the DI-4108 reads +/-2, and both it and
# the DI-2108P offer unipolar ranges that need a different conversion formula
# entirely, so decoding one of those with this table is silently wrong.
DAQ_MODEL = "4108"
DEFAULT_RANGE_VOLT = 10  # Accommodates the receiver's signal above 5 V

# srate/dec set how often the DI-4108 walks the whole scan list, not how much
# data it produces per second: every channel in the list is sampled once per
# pass, so SCAN_RATE is the per-channel rate and throughput is SCAN_RATE * N.
# Measured on a DI-4108 with these constants: 200 samples/s with two channels in
# the list and 400 with four, both at 99.9 scans/s. Consecutive scans are
# therefore 1/SCAN_RATE apart no matter how many channels they carry.
BASE_CLOCK_HZ = 60_000_000  # Input to the DI-4108's sample-rate divider
SRATE = 1171
DECIMATION = 512
SCAN_RATE = BASE_CLOCK_HZ / (SRATE * DECIMATION)  # ~100 Hz per channel

# The analog front end integrates with an RC time constant of 0.3 s, band-limiting
# the signal to ~1/(2*pi*0.3) = 0.53 Hz before the ADC ever sees it. At ~100 Hz per
# channel that is ~190x oversampled, so everything above the analog corner is noise
# added after the capacitors (ADC quantization, cabling, ground). A single-pole IIR
# matched to the same constant removes that noise at almost no cost in signal.
#
#   0.3  matched to the hardware:  corner 0.53 Hz, noise /5.6, 95% settle ~0.9 s
#   0.1  light, transient-safe:    corner 1.6 Hz,  noise /3.3, 95% settle ~0.3 s
#   1.0  heavy, slow drift scans:  corner 0.16 Hz, noise /10,  95% settle ~3.0 s
#   0    disables the filter (samples pass through exactly as before)


"""
| `filter_tau` |      Cutoff | Effect                                           |
| -----------: | ----------: | ------------------------------------------------ |
|       0.05 s |     3.18 Hz | Minimal added smoothing                          |
|   **0.08 s** | **1.99 Hz** | Recommended starting point                       |
|       0.16 s |     0.99 Hz | Stronger smoothing, more delay                   |
|       0.30 s |     0.53 Hz | Generally too slow; duplicates backend filtering |

"""

FILTER_TAU = 0.08  # seconds


class FilterKind(Enum):
    """
    Which software filter sits between the ADC and everything downstream.

    The two algorithms solve different problems and are not really substitutes:

      SINGLE_POLE  attenuates broadband noise across the whole band above its
                   corner, at the cost of delaying and smoothing everything.
                   This is what reduces the sampling noise the ~0.3 s analog
                   integrator leaves behind.
      HAMPEL       replaces samples that sit more than HAMPEL_SIGMAS robust
                   standard deviations off the local median, and passes every
                   other sample through untouched. It removes isolated spikes
                   (RFI hits, ADC glitches, a dropped serial byte) without
                   blurring real structure -- but it does almost nothing to
                   Gaussian noise, so on its own it will not quiet the trace.

    Hence BOTH, which is usually what you want: despike first, then smooth.
    The order matters. A spike that reaches the lowpass is smeared across the
    following ~tau of output, so removing it afterward is no longer possible.
    """

    NONE = "none"
    SINGLE_POLE = "single_pole"
    HAMPEL = "hampel"
    BOTH = "both"


FILTER_KIND = FilterKind.SINGLE_POLE

# Hampel parameters. The window is a trailing one -- a centered window would
# delay every sample by half its length, which is not free on a live stripchart.
# 7 samples is ~70 ms at ~100 Hz per channel and tolerates up to 3 consecutive
# bad samples; 3 sigmas passes ~99.7% of clean Gaussian data untouched.
HAMPEL_WINDOW = 7
HAMPEL_SIGMAS = 3.0


def discovery() -> tuple[str | None, str | None]:
    # Get a list of active com ports to scan for possible DATAQ Instruments devices
    available_ports = serial.tools.list_ports.comports()

    dataq = None
    declinometer = None
    for p in available_ports:
        if "VID:PID=0683:4109" in p.hwid:
            dataq = p.device
        if "VID:PID=0403:6001" in p.hwid:
            declinometer = p.device

    # An explicit port always wins. On a Raspberry Pi, prefer its stable
    # /dev/serial0 alias over an enumerated FTDI adapter: the USB adapter may
    # remain plugged in even when the sensor has moved to the GPIO UART.
    # Other built-in/non-FTDI ports can still be selected by name:
    #     set THREEPIO_DEC_PORT=COM4        (Windows)
    #     export THREEPIO_DEC_PORT=/dev/... (macOS/Linux)
    dataq = os.environ.get(DAQ_PORT_ENV) or dataq
    explicit_dec_port = os.environ.get(DEC_PORT_ENV)
    if explicit_dec_port:
        declinometer = explicit_dec_port
    elif os.path.exists(NATIVE_DEC_PORT):
        declinometer = NATIVE_DEC_PORT

    return dataq, declinometer


def slist_word(channel: int, volts: float = DEFAULT_RANGE_VOLT) -> int:
    """
    Build one scan list configuration word: bits 3:0 select the analog channel,
    bits 11:8 select the measurement range, bits 15:12 are unused and must be 0.
    """
    return (Tars.RANGE_VOLT.index(volts) << 8) | channel


def range_volt(word: int) -> float:
    """Recover the full-scale volts a scan list word asked the device for."""
    return Tars.RANGE_VOLT[(word >> 8) & 0xF]


class SinglePoleLowpass:
    """
    One-pole IIR lowpass (exponential moving average) -- the digital equivalent of
    an RC integrator: y += alpha * (x - y), with alpha = dt/(tau + dt).

    Filtering runs in sample-index space, not wall-clock. The DI-4108 clocks its
    scans in hardware, so consecutive samples are evenly spaced at `period` no
    matter when the GUI thread gets around to reading them; deriving alpha from
    time deltas would instead let the cutoff wander every time a tick runs long.
    """

    def __init__(self, tau: float, period: float):
        # tau <= 0 gives alpha == 1, i.e. pure passthrough
        self.alpha = 1.0 if tau <= 0 else period / (tau + period)
        self.value: float | None = None

    def reset(self):
        self.value = None

    def update(self, sample: float) -> float:
        # Seed with the first sample rather than 0. Starting from zero makes the
        # output ramp up from the bottom of the range for several tau after every
        # start(), which looks exactly like a real rising signal on the stripchart.
        if self.value is None:
            self.value = sample
        else:
            self.value += self.alpha * (sample - self.value)
        return self.value


class HampelFilter:
    """
    Trailing-window Hampel identifier: replace a sample with the window median
    when it lies more than `sigmas` robust standard deviations away from it,
    and otherwise pass it through untouched.

    Spread is estimated as 1.4826 * MAD (median absolute deviation) rather than
    a standard deviation, so a spike cannot inflate the very threshold meant to
    catch it -- the median and MAD both tolerate up to half the window being
    corrupt, where one bad sample is enough to hide itself behind an ordinary
    mean and standard deviation.

    This is a despiker, not a smoother. It leaves inliers exactly as they were,
    so it does not reduce Gaussian noise; pair it with SinglePoleLowpass if the
    trace needs quieting as well.
    """

    # A spread estimate of zero would make every deviation "infinitely" many
    # sigmas and clamp the output to the median. That is not hypothetical here:
    # a quiet channel resting on one ADC code (305 uV on the +/-10 V range) makes
    # more than half the window identical, so MAD is exactly 0 and the filter
    # would quantize away every small real change. Below this, pass through.
    MIN_SPREAD = 1e-12

    def __init__(self, window: int, sigmas: float):
        self.samples: deque[float] = deque(maxlen=max(1, window))
        self.sigmas = sigmas

    def reset(self):
        self.samples.clear()

    def update(self, sample: float) -> float:
        self.samples.append(sample)
        # A partly-filled window has too few samples for the median to be robust;
        # judging a spike against 2 neighbors mostly rejects good data instead.
        if len(self.samples) < self.samples.maxlen:
            return sample

        median = statistics.median(self.samples)
        mad = statistics.median([abs(x - median) for x in self.samples])
        spread = 1.4826 * mad
        if spread < self.MIN_SPREAD:
            return sample
        if abs(sample - median) > self.sigmas * spread:
            return median
        return sample


class FilterChain:
    """
    Applies filter stages in order. An empty chain is the identity, which is how
    FilterKind.NONE is expressed.
    """

    def __init__(self, stages):
        self.stages = tuple(stages)

    def reset(self):
        for stage in self.stages:
            stage.reset()

    def update(self, sample: float) -> float:
        for stage in self.stages:
            sample = stage.update(sample)
        return sample


def make_filter(kind: FilterKind, period: float) -> FilterChain:
    """
    Build the filter chain for one channel. Despiking precedes smoothing: a
    spike that reaches the lowpass is already smeared across its output.
    """
    stages = []
    if kind in (FilterKind.HAMPEL, FilterKind.BOTH):
        stages.append(HampelFilter(HAMPEL_WINDOW, HAMPEL_SIGMAS))
    if kind in (FilterKind.SINGLE_POLE, FilterKind.BOTH):
        stages.append(SinglePoleLowpass(FILTER_TAU, period))
    return FilterChain(stages)


class Tars:
    """
    A wrapper class of a serial object which supports functionalities specifically
    useful for DATAQ instruments.
    """

    RANGE_VOLT = (10, 5, 2, 1, 0.5, 0.2)
    RANGE_RATE = (50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50, 20, 10)

    COMMAND_TIMEOUT = 0.25  # seconds; bounds one blocking read for a command echo
    # "stop" and "encode" reconfigure the acquisition engine, and the DI-4108
    # answers neither them nor anything sent behind them until it is done --
    # measured at 0.99-1.00 s, every time, whether or not it was scanning. At
    # COMMAND_TIMEOUT the echo always misses, which reads as a mute device.
    SLOW_COMMAND_TIMEOUT = 2.0
    SLOW_COMMANDS = ("stop", "encode")
    DRAIN_TIMEOUT = 1.0  # seconds; caps how long a still-scanning device can stall setup

    def __init__(self, parent, device=None):
        self.parent = parent

        self.testing = device is None
        if self.testing:
            self.parent.log("DataQ not found, simulating data")

        # Configure at construction: MySerial swallows SerialException from
        # _reconfigure_port, so assigning the timeout after opening can fail
        # silently and leave the port blocking forever on a short read.
        self.ser = MySerial(device, timeout=self.COMMAND_TIMEOUT)
        self.channels = [
            slist_word(0),  # Telescope channel A
            slist_word(1),  # Telescope channel B
        ]
        self.acquiring = False

        # The interval between consecutive scans, which is also the interval
        # between consecutive samples of any one channel: adding channels to the
        # scan list widens each scan rather than slowing the walk.
        self.sample_period = 1 / SCAN_RATE
        self.filters = tuple(
            make_filter(FILTER_KIND, self.sample_period) for _ in self.channels
        )

        # Pulsar observations need the raw samples: every software filter here
        # is a lowpass well below the pulse rate, so it would smear the very
        # signal the mode exists to record.
        self.filtering = True

        self.configured = self.setup()

    def start(self):
        self.reset_filters()
        if not self.testing:
            # "start" never echoes, so nothing should follow it but samples.
            self.ser.reset_input_buffer()
            self.send("start")
            self.acquiring = True

    def reset(self):
        self.reset_filters()
        if not self.testing:
            self.send("reset 1")

    def stop(self):
        self.reset_filters()
        if self.testing:
            return
        self.send("stop")
        self.ser.reset_input_buffer()
        self.acquiring = False

    def reset_filters(self):
        """
        Forget the filter state. Every caller of this also flushes the input
        buffer, and a value from before that gap must not bleed across it.
        """
        for channel_filter in self.filters:
            channel_filter.reset()

    def set_filtering(self, enabled: bool):
        """
        Turn the software filter chain on or off. Switching either way discards
        the filter state, so a value from the previous regime cannot bleed into
        the first filtered sample after it is turned back on.
        """
        if enabled == self.filtering:
            return
        self.filtering = enabled
        self.reset_filters()

    def _read_one(self) -> SignalDatum | None:
        """
        This reads one datapoint from the buffer. Each datapoint has three channels:
        channel 0: telescope channel A
        channel 1: telescope channel B
        channel 2: declinometer
        """
        if self.testing:
            return self.random_data()

        if self.in_waiting() < (2 * len(self.channels)):
            return None
        channel_a = self.buffer_read(self.channels[0])
        channel_b = self.buffer_read(self.channels[1])
        if channel_a is None or channel_b is None:
            return None
        return SignalDatum(a=float(channel_a), b=float(channel_b))

    def read_all(self) -> list[SignalDatum]:
        """
        Read every scan waiting in the buffer, filter them, and return all of them
        oldest-first. Use this when no sample may be dropped, e.g. pulsar mode.

        Returns an empty list when no new scan arrived, so the caller's data rate is
        unchanged -- tick() must not append a duplicate point on an empty read.
        """
        if self.testing:
            return [self._filter(self.random_data())]
        data = []
        current = self._read_one()
        while current is not None:
            # Every decoded scan updates the filter, not just the newest one.
            # Dropping the backlog would waste the averaging and stretch the
            # effective time constant whenever a slow tick lets scans queue up.
            data.append(self._filter(current))
            current = self._read_one()
        return data

    def read_latest(self) -> SignalDatum | None:
        """
        As read_all(), but keeping only the newest scan (None if there was none).
        Use this as a real-time sampling method.
        """
        data = self.read_all()
        return data[-1] if data else None

    def _filter(self, datum: SignalDatum) -> SignalDatum:
        if not self.filtering:
            return datum
        return SignalDatum(
            a=self.filters[0].update(datum.a),
            b=self.filters[1].update(datum.b),
        )

    # Helpers

    def send(self, command: str):
        if self.testing:
            return
        self.ser.write((command + "\r").encode())

    def command(self, command: str) -> str | None:
        """
        Send one command and return the device's echo, or None if none arrived
        in time. Replies may be padded with NUL bytes after the terminating CR;
        because read_until() leaves that padding buffered, it can appear at the
        beginning of the next reply.

        A slow command gets SLOW_COMMAND_TIMEOUT; everything else gets
        COMMAND_TIMEOUT, so an absent echo still fails fast.
        """
        with self._read_timeout(self._timeout_for(command)):
            self.send(command)
            echo = self.ser.read_until(b"\r")
        if not echo.endswith(b"\r"):
            return None
        return echo.decode(errors="replace").strip("\x00 \t\r\n")

    def _timeout_for(self, command: str) -> float:
        verb = command.split()[0] if command.split() else command
        if verb in self.SLOW_COMMANDS:
            return self.SLOW_COMMAND_TIMEOUT
        return self.COMMAND_TIMEOUT

    @contextmanager
    def _read_timeout(self, timeout: float):
        """Widen the port's read timeout for one exchange, then put it back."""
        previous = self.ser.timeout
        if timeout == previous:
            yield
            return
        self.ser.timeout = timeout
        try:
            yield
        finally:
            self.ser.timeout = previous

    @staticmethod
    def _matches(echo: str | None, command: str) -> bool:
        # Compare on whitespace-separated tokens: the protocol pins the fields
        # of an echo but not the exact spacing between them.
        return echo is not None and echo.split() == command.split()

    def _configure(self, command: str) -> bool:
        """Send a configuration command and confirm the device echoed it back."""
        echo = self.command(command)
        if self._matches(echo, command):
            return True
        self.parent.log(f"DataQ did not confirm '{command}' (got {echo!r})", warning=True)
        return False

    def _drain(self):
        """
        Read until the device goes quiet. On startup it may still be streaming
        binary from a crashed session, in which case the "stop" echo arrives
        behind an unknown amount of sample data, so drain rather than parse.

        Call this only once "stop" has been given time to take effect: the
        device falls silent while it stops, and an empty read taken during that
        silence would look like a settled line.
        """
        deadline = time.time() + self.DRAIN_TIMEOUT
        while time.time() < deadline:
            if not self.ser.read(max(1, self.ser.in_waiting)):
                return  # A read that timed out empty means the line is quiet

    def setup(self) -> bool:
        if self.testing:
            return False

        # "stop" echoes even mid-scan, so this works whether or not the device
        # was left acquiring by a previous run. Wait for that echo rather than
        # just firing it off: the device answers nothing for ~1 s while it
        # stops, and every command sent into that gap is lost.
        self.command("stop")
        self._drain()
        self.acquiring = False

        commands = ["ps 0"]  # Small pocketsize for responsiveness
        commands += [f"slist {i} {word}" for i, word in enumerate(self.channels)]
        # 60,000,000/(srate * dec) = 60,000,000/(1171 * 512) = 100 scans/s, and
        # every channel in the scan list is sampled once per scan, so both run at
        # ~100 Hz. SinglePoleLowpass reads the same constants, so changing these
        # retunes the filter with them.
        commands += [f"dec {DECIMATION}", f"srate {SRATE}"]

        model = self.command("info 1")
        if model is None:
            # Nothing is echoing, so there is no echo to synchronize on. Fall
            # back to the blind sequence: fire everything, wait, and flush.
            # Anything left in the buffer would otherwise be decoded as samples
            # -- printable ASCII pairs land in 8224..32382 counts, and an odd
            # byte count shifts every later sample for the rest of the session.
            self.parent.log("DataQ is not echoing commands; configuring blind", warning=True)
            # Blind or not, "encode" still stalls the device for ~1 s, and the
            # rest of the sequence would land in that gap. command() waits it
            # out; its (absent) reply is what we are already resigned to.
            self.command("encode 0")
            for command in commands:
                self.send(command)
            time.sleep(0.2)
            self.ser.reset_input_buffer()
            return False

        ok = True
        if not self._matches(model, f"info 1 {DAQ_MODEL}"):
            self.parent.log(
                f"DataQ reports {model!r}, not a DI-{DAQ_MODEL}; "
                f"voltage ranges will be misread",
                warning=True,
            )
            ok = False

        # The DI-4108 does echo "encode 0", but only after the ~1 s it spends
        # applying it, and some firmware revisions may not echo at all. Accept
        # either silence or the expected reply, while still rejecting an
        # explicit unexpected response.
        encode_echo = self.command("encode 0")
        if encode_echo is not None and not self._matches(encode_echo, "encode 0"):
            self.parent.log(
                f"DataQ did not confirm 'encode 0' (got {encode_echo!r})",
                warning=True,
            )
            ok = False

        for command in commands:
            ok &= self._configure(command)

        if ok:
            channels = ", ".join(str(word & 0xF) for word in self.channels)
            self.parent.log(
                f"DI-{DAQ_MODEL} confirmed; channels {channels} at "
                f"±{range_volt(self.channels[0])} V"
            )
        return ok

    def in_waiting(self) -> int:
        if self.testing:
            return 0
        return self.ser.in_waiting

    def buffer_read(self, channel: int) -> float | None:
        """
        This function reads one value from the serial buffer. I.E. it will only read
        *one channel* at a time. Therefore, do not use this function by itself. If data
        is not always read in pairs of three there's no way to tell the channels apart.
        """
        if self.testing:
            return None

        if self.in_waiting() < 2:
            return None
        buffer = self.ser.read(2)
        # The device returns 16-bit two's complement spanning the configured
        # bipolar range, so a positive coax signal uses only the positive half
        # of its configured range: 0 V -> 0 counts, +FS -> +32767.
        # Every range this device offers is bipolar, so there is no unipolar
        # code that would win back the unused bit.
        return (
            range_volt(channel)
            * int.from_bytes(buffer, byteorder="little", signed=True)
            / 32768
        )

    # - MARK: Testing

    def random_data(self) -> SignalDatum:
        """This gives something that kind of looks like real data, for UI testing."""
        x = time.time() / 8

        n = r.choice([-0.2, 1]) / (64 * (r.random() + 0.02))
        n *= 0.08 * self.parent.ui.noise_dial.value() ** 2

        v = self.parent.ui.variance_dial.value()

        c = 1 if self.parent.ui.calibration_check_box.isChecked() else 0

        f = 0
        # f = math.sin(4 * x)

        g = (
            2.6 / (math.sin(2 * x) + 1.4)
            + 0.4 * math.sin(8 * x)
            - 0.8 * math.sin(4 * x)
            + (1 / (math.sin(8 * x) + 1.4))
        )

        a = f + g * v + n + c
        b = a - 0.1 * self.parent.ui.polarization_dial.value() * g * (v / 2 + 1)

        a, b = (i / 272 + c + 1 for i in (a, b))  # Normalize, kinda

        return SignalDatum(float(a), float(b))
