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
from dataclasses import dataclass


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


class Tars:
    """
    A wrapper class of a serial object which supports functionalities specifically
    useful for DATAQ instruments.
    """

    RANGE_VOLT = (10, 5, 2, 1, 0.5, 0.2)
    RANGE_RATE = (50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50, 20, 10)

    COMMAND_TIMEOUT = 0.25  # seconds; bounds one blocking read for a command echo
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

        self.configured = self.setup()

    def start(self):
        if not self.testing:
            # "start" never echoes, so nothing should follow it but samples.
            self.ser.reset_input_buffer()
            self.send("start")
            self.acquiring = True

    def reset(self):
        if not self.testing:
            self.send("reset 1")

    def stop(self):
        if self.testing:
            return
        self.send("stop")
        self.ser.reset_input_buffer()
        self.acquiring = False

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

    def read_latest(self) -> SignalDatum | None:
        """
        This function reads the last datapoint from the buffer and clears the buffer.
        Use this as a real-time sampling method.
        """
        if self.testing:
            return self.random_data()
        current = self._read_one()
        latest = None
        while current is not None:
            latest = current
            current = self._read_one()
        return latest

    # Helpers

    def send(self, command: str):
        if self.testing:
            return
        self.ser.write((command + "\r").encode())

    def command(self, command: str) -> str | None:
        """
        Send one command and return the device's echo, or None if none arrived
        within COMMAND_TIMEOUT. Replies may be padded with NUL bytes after the
        terminating CR; because read_until() leaves that padding buffered, it
        can appear at the beginning of the next reply.
        """
        self.send(command)
        echo = self.ser.read_until(b"\r")
        if not echo.endswith(b"\r"):
            return None
        return echo.decode(errors="replace").strip("\x00 \t\r\n")

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
        """
        deadline = time.time() + self.DRAIN_TIMEOUT
        while time.time() < deadline:
            if not self.ser.read(max(1, self.ser.in_waiting)):
                return  # A read that timed out empty means the line is quiet

    def setup(self) -> bool:
        if self.testing:
            return False

        # "stop" echoes even mid-scan, so this works whether or not the device
        # was left acquiring by a previous run.
        self.send("stop")
        self._drain()
        self.acquiring = False

        commands = ["ps 0"]  # Small pocketsize for responsiveness
        commands += [f"slist {i} {word}" for i, word in enumerate(self.channels)]
        # Sample rate is a throughput on this device, not a per-channel rate:
        # 60,000,000/(srate * dec) = 60,000,000/(1171 * 512) = 100 Hz total,
        # so each of the two channels is sampled at ~50 Hz.
        commands += ["dec 512", "srate 1171"]

        model = self.command("info 1")
        if model is None:
            # Nothing is echoing, so there is no echo to synchronize on. Fall
            # back to the blind sequence: fire everything, wait, and flush.
            # Anything left in the buffer would otherwise be decoded as samples
            # -- printable ASCII pairs land in 8224..32382 counts, and an odd
            # byte count shifts every later sample for the rest of the session.
            self.parent.log("DataQ is not echoing commands; configuring blind", warning=True)
            self.send("encode 0")
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

        # The DI-4108 applies "encode 0" but does not echo it. Some firmware
        # revisions may echo, so accept either silence or the expected reply,
        # while still rejecting an explicit unexpected response.
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
