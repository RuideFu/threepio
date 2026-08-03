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

    # An explicit port always wins. Auto-detection matches on the USB VID:PID of
    # the FTDI adapter, which a built-in COM port (or any non-FTDI adapter) does
    # not have, so on those machines the port can only be chosen by name:
    #     set THREEPIO_DEC_PORT=COM4        (Windows)
    #     export THREEPIO_DEC_PORT=/dev/... (macOS/Linux)
    dataq = os.environ.get(DAQ_PORT_ENV) or dataq
    declinometer = os.environ.get(DEC_PORT_ENV) or declinometer

    return dataq, declinometer


def convert(buffer: list, volt: int) -> float:
    return volt * int.from_bytes(buffer, byteorder="little", signed=True) / 32768


class Tars:
    """
    A wrapper class of a serial object which supports functionalities specifically
    useful for DATAQ instruments.
    """

    RANGE_VOLT = (10, 5, 2, 1, 0.5, 0.2)
    RANGE_RATE = (50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50, 20, 10)

    def __init__(self, parent, device=None):
        self.parent = parent

        self.testing = device is None
        if self.testing:
            self.parent.log("DataQ not found, simulating data")

        self.ser = MySerial(device)
        self.channels = [
            0x0100,  # Channel 0, telescope channel A, ±5 V range
            0x0101,  # Channel 1, telescope channel B, ±5 V range
        ]
        self.acquiring = False

        self.setup()

    def start(self):
        if not self.testing:
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

    def setup(self):
        if self.testing:
            return

        self.send("stop")
        self.send("encode 0")  # 0 = binary, 1 = ascii
        self.send("ps 0")  # Small pocketsize for responsiveness

        for i in range(0, len(self.channels)):
            self.send("slist " + str(i) + " " + str(self.channels[i]))

        # Define sample rate = 100 Hz:
        # 60,000,000/(srate * dec) = 60,000,000/(1171 * 512) = 100 Hz
        self.send("dec 512")
        self.send("srate 1171")

        # self.send("dec 512")
        # self.send("srate 11718")

        # The device echoes every command back as ASCII on the same stream
        # buffer_read decodes as samples. Measured on a DI-4108 (fw 8B), the
        # commands above leave 51 bytes in the buffer -- an odd count, so
        # without this flush the first ~25 readings are the text of these
        # commands (which decodes to 6.25-9.94 V, since printable ASCII pairs
        # land in 8224..32382 counts) and every sample after them is shifted
        # by one byte for the rest of the session. "start" draws no echo, so
        # flushing here is enough.
        time.sleep(0.2)
        self.ser.reset_input_buffer()

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
        # bipolar range, so a 0..+5 V coax signal uses only the positive half
        # of the ±5 V range: 0 V -> 0 counts, +5 V -> +32767, 152.6 uV/LSB.
        # Every range this device offers is bipolar, so there is no unipolar
        # code that would win back the unused bit; ±5 V is still the tightest
        # range that does not clip a 5 V input.
        return (
            Tars.RANGE_VOLT[channel >> 8]
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
