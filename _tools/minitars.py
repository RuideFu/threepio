"""
Small version of Tars, meant to be used with the Arduino declinometer as opposed to the
DataQ.
"""
import os

import serial
from .myserial import MySerial
from .declog import get_dec_logger
import serial.tools.list_ports

import time
import math

log = get_dec_logger()


def discovery():
    """Get a list of active com ports and scan for declinometer"""
    available_ports = serial.tools.list_ports.comports()

    declinometer = None
    for p in available_ports:
        log.debug(f"discovery: port {p.device} hwid={p.hwid}")
        if "VID:PID=0403:6001" in p.hwid:
            declinometer = p.device

    # See tars.discovery: a built-in COM port has no USB VID:PID to match on.
    declinometer = os.environ.get("THREEPIO_DEC_PORT") or declinometer

    log.info(f"discovery: declinometer={declinometer}")
    return declinometer


class MiniTars:
    READ_TIMEOUT = 0.25  # seconds; bounds a single blocking read_until

    def __init__(self, parent, device=None):
        self.parent = parent
        self.testing = True
        self.acquiring = False
        if device is not None:
            self.testing = False
            # Configure at construction: MySerial swallows SerialException from
            # _reconfigure_port, so assigning baudrate after opening can fail
            # silently and leave the port at the 9600 default. The timeout keeps
            # read_until from blocking forever when a line has no "\r".
            self.ser = MySerial(device, baudrate=38400, timeout=self.READ_TIMEOUT)
            log.info(
                f"MiniTars: opened {device} is_open={self.ser.is_open} "
                f"baudrate={self.ser.baudrate} timeout={self.ser.timeout} "
                f"bytesize={self.ser.bytesize} parity={self.ser.parity} "
                f"stopbits={self.ser.stopbits}"
            )
        else:
            self.parent.log("Declinometer not found, simulating data")
            log.warning("MiniTars: no device, simulating data")

        # When set, every read step is logged. Left off during normal operation
        # because tick() reads at up to 100Hz; DecDialog turns it on while it
        # is blocking on a read.
        self.verbose = False
        self.bad_line_count = 0
        self.empty_reads = 0
        self.last_empty_log = 0.0

    def handshake(self) -> bool:
        """
        Confirm the sensor is alive and put it into continuous ASCII output.

        The SOLAR-360 does not stream by default: it answers commands, and only
        transmits continuously after 'setcasc'. Both that and the ASCII/integer
        choice ('setoasc') live in the sensor's non-volatile memory, so without
        this the app silently depends on however the unit was last configured,
        and a sensor in its shipping state produces no data at all.

        Commands are lower case, exactly 7 bytes, and must be written in one go
        (the sensor discards a command with >100ms between characters).
        """
        if self.testing:
            return True

        # A unit already in continuous ASCII mode needs nothing done to it, and
        # these settings are stored in non-volatile memory, so check before
        # writing rather than rewriting the sensor's configuration every launch.
        if self._streaming():
            log.info("handshake: already streaming ASCII angles")
            return True

        if self._command(b"gettemp") is None:
            msg = "Declinometer is not responding (no reply to gettemp)"
            self.parent.log(msg)
            log.error(f"handshake: {msg}")
            return False

        for command in (b"setoasc", b"setcasc"):
            reply = self._command(command)
            # 'OK' is not necessarily at the front: once the sensor is streaming,
            # angle frames interleave with the reply to a command.
            if reply is None or b"OK" not in reply:
                log.warning(f"handshake: no OK for {command.decode()}: {reply!r}")

        # Whether or not the OKs were seen, the real test is angle data arriving.
        if not self._streaming():
            msg = "Declinometer will not stream angle data"
            self.parent.log(msg)
            log.error(f"handshake: {msg}")
            return False

        log.info("handshake: sensor now streaming ASCII angles")
        return True

    def _streaming(self, window: float = 4.0) -> bool:
        """
        True if a well-formed angle frame arrives within `window` seconds.

        The window has to cover the slowest output rate a unit may be set to.
        Sensors configured for continuous output do not all run at the same
        rate: one may emit at 10Hz and another at well under 1Hz, with gaps of
        seconds between frames. This returns as soon as a frame parses, so a
        fast unit still completes in milliseconds and only a silent one waits
        out the full window.
        """
        self.ser.reset_input_buffer()
        deadline = time.perf_counter() + window
        buffer = b""
        while time.perf_counter() < deadline:
            buffer += self.ser.read(self.ser.in_waiting or 0)
            # Any one complete frame proves the sensor is streaming. Waiting for
            # a second frame to appear before trusting the first is not safe: at
            # a slow output rate two frames may not arrive inside any reasonable
            # window, and the check then rejects a perfectly healthy stream.
            # A read that begins mid-stream still yields a leading fragment, but
            # _parse rejects that on length, so no extra guard is needed.
            if b"\r" in buffer:
                for chunk in buffer.split(b"\r")[:-1]:
                    if self._parse(chunk + b"\r") is not None:
                        return True
            time.sleep(0.02)
        log.debug(f"_streaming: no valid frame in {window}s, saw {buffer!r}")
        return False

    @staticmethod
    def _parse(line: bytes) -> float | None:
        """
        Parse one angle frame, rejecting anything that is not the sensor's
        fixed-length angle format.

        The sensor emits exactly '±xxx.xxx\\r' (9 bytes) for an angle. Length
        matters: a read that starts mid-stream yields a truncated number that
        still parses as a valid float ('6.122' out of '+136.122'), and a
        temperature reply is '±tt.t\\r' (6 bytes) — both would otherwise be
        accepted as a plausible declination and silently corrupt the data.
        """
        if len(line) != 9 or line[:1] not in (b"+", b"-") or not line.endswith(b"\r"):
            return None
        try:
            return float(line.decode())
        except (UnicodeDecodeError, ValueError):
            return None

    def _command(self, command: bytes, settle: float = 0.3) -> bytes | None:
        """Send a 7-byte command and return the reply, or None if silent."""
        assert len(command) == 7, command
        self.ser.reset_input_buffer()
        self.ser.write(command)
        self.ser.flush()
        time.sleep(settle)
        reply = self.ser.read(self.ser.in_waiting or 0)
        # A half-duplex line, or an undriven Rxd picking up our own Txd, returns
        # one byte per byte sent — possibly corrupted, so an equality check is
        # not enough. No documented reply is 7 bytes long (OK and INT16 are 2,
        # INT32 is 4, ASCII temperature 6, ASCII angle 9), so a reply the same
        # length as the command is always our own transmission coming back.
        if len(reply) == len(command):
            log.warning(
                f"_command: {command!r} came back as {reply!r} — same length as "
                "the command, so this is our own Txd echoing, not a reply"
            )
            return None
        log.debug(f"_command: {command!r} -> {reply!r}")
        return reply or None

    def start(self):
        if not self.testing:
            self.acquiring = True

    def stop(self):
        if not self.testing:
            self.ser.reset_input_buffer()
            self.acquiring = False

    def _read_one(self) -> float | None:
        """
        This reads one datapoint from the buffer.
        """
        if not self.testing:
            if self.in_waiting() < 1:
                return None
            return self.buffer_read()
        else:
            return self.random_data()

    def read_latest(self) -> float | None:
        """
        This function reads the last datapoint from the buffer and clears the buffer.
        Use this as a real-time sampling method.
        """
        if self.testing:
            return self.random_data()
        current = self._read_one()
        latest = None
        drained = 0
        while current is not None:
            latest = current
            drained += 1
            current = self._read_one()
        if self.verbose:
            self._log_read(drained, latest)
        return latest

    def _log_read(self, drained: int, latest: float | None):
        """
        Rate-limited verbose logging. read_latest can be called hundreds of
        thousands of times a second by DecDialog's spin loop, so log a value the
        moment it arrives but summarize empty reads at most once a second.
        """
        now = time.perf_counter()
        if drained:
            log.debug(f"read_latest: drained={drained} latest={latest}")
            self.empty_reads = 0
            self.last_empty_log = now
            return
        self.empty_reads += 1
        if now - self.last_empty_log >= 1.0:
            log.debug(
                f"read_latest: {self.empty_reads} empty reads in the last "
                f"{now - self.last_empty_log:.1f}s, in_waiting=0"
            )
            self.empty_reads = 0
            self.last_empty_log = now

    # Helpers

    def in_waiting(self) -> int:
        if self.testing:
            return 0
        return self.ser.in_waiting

    def buffer_read(self) -> float | None:
        """Read angle from serial buffer"""
        if self.testing:
            return None
        waiting = self.in_waiting()
        if waiting < 1:
            if self.verbose:
                log.debug("buffer_read: no data in queue")
            return None

        # read_until returns once it sees "\r" or the port timeout expires, so a
        # line can come back truncated. _parse rejects anything that is not a
        # whole angle frame rather than trusting float() to catch it.
        if self.verbose:
            log.debug(f"buffer_read: in_waiting={waiting}, entering read_until")
        start = time.perf_counter()
        line = self.ser.read_until(expected="\r".encode("ascii"))
        elapsed = time.perf_counter() - start
        if self.verbose or elapsed > 0.1:
            log.debug(
                f"buffer_read: read_until returned in {elapsed * 1000:.1f}ms, "
                f"raw={line!r}"
            )

        value = self._parse(line)
        if value is None:
            self.bad_line_count += 1
            log.warning(
                f"buffer_read: discarded frame #{self.bad_line_count} raw={line!r} "
                "(not a whole '±xxx.xxx\\r' angle)"
            )
            return None
        if self.verbose:
            log.debug(f"buffer_read: value={value}")
        return value

    # Testing

    def random_data(self) -> float:
        """For testing"""
        if self.parent.ui.dec_auto_check_box.isChecked():
            return math.sin(time.time() / 2) * 100
        return float(self.parent.ui.declination_slider.value())
