"""
Standalone declinometer probe. Run outside the GUI to find out whether the
device sends anything at all, and at which baudrate.

    uv run python -m _tools.dec_probe

Threepio must NOT be running: the port can only be held by one process.
"""
import sys
import time

import serial

from .minitars import discovery

BAUDRATES = [38400, 9600, 19200, 57600, 115200]
LISTEN_SECONDS = 3.0


def listen(port: str, baudrate: int, seconds: float = LISTEN_SECONDS) -> bytes:
    """Open at one baudrate and dump whatever shows up."""
    collected = b""
    with serial.Serial(port, baudrate=baudrate, timeout=0.2) as ser:
        print(
            f"\n=== {baudrate} baud === is_open={ser.is_open} "
            f"dtr={ser.dtr} rts={ser.rts} timeout={ser.timeout}"
        )
        deadline = time.perf_counter() + seconds
        while time.perf_counter() < deadline:
            waiting = ser.in_waiting
            if waiting:
                chunk = ser.read(waiting)
                collected += chunk
                print(f"  +{len(chunk)} bytes: {chunk!r}")
            else:
                time.sleep(0.05)
    if not collected:
        print("  (nothing received)")
    else:
        terminators = {
            "\\r": collected.count(b"\r"),
            "\\n": collected.count(b"\n"),
        }
        print(f"  total={len(collected)} bytes, terminators={terminators}")
    return collected


def poll(port: str, baudrate: int, command: str) -> bytes:
    """Some firmware only answers when asked; try a request/response exchange."""
    with serial.Serial(port, baudrate=baudrate, timeout=1.0) as ser:
        ser.reset_input_buffer()
        ser.write(command.encode("ascii"))
        ser.flush()
        time.sleep(0.5)
        reply = ser.read(ser.in_waiting or 32)
    print(f"\n=== poll {command!r} @ {baudrate} === reply={reply!r}")
    return reply


def verdict(port: str) -> str:
    """
    Decide whether anything is actually driving the adapter's receive line.

    An undriven Rxd picks up the adapter's own Txd through cable capacitance.
    That coupling is high-pass, which makes it easy to tell from a real signal:
    it drops out at low baud, sharpens as baud rises, and passes an alternating
    0x55 pattern cleanly at any rate while corrupting bytes containing runs of
    like bits. A genuine RS232 driver is DC-coupled and does none of that.
    """
    probes = {}
    for baudrate in (9600, 38400, 230400):
        for payload in (b"gettemp", b"UUUUUUU"):
            with serial.Serial(port, baudrate=baudrate, timeout=0.2) as ser:
                time.sleep(0.12)
                ser.reset_input_buffer()
                ser.write(payload)
                ser.flush()
                got = b""
                deadline = time.perf_counter() + 1.0
                while time.perf_counter() < deadline:
                    n = ser.in_waiting
                    if n:
                        got += ser.read(n)
                    else:
                        time.sleep(0.02)
            probes[(baudrate, payload)] = got
            print(f"  {baudrate:6d} sent={payload!r:12s} -> {len(got)}B {got!r}")

    echoes = [g for (_, p), g in probes.items() if len(g) == len(p)]
    longer = [g for (_, p), g in probes.items() if len(g) > len(p)]
    if longer:
        return "Sensor is replying. Rerun the command polls above for detail."
    if not echoes:
        return "Nothing comes back at all — check the adapter and the port."
    alternating_ok = probes[(38400, b"UUUUUUU")] == b"UUUUUUU"
    runs_corrupt = probes[(38400, b"gettemp")] not in (b"", b"gettemp")
    dropout_low = probes[(9600, b"gettemp")] == b""
    if alternating_ok and runs_corrupt and dropout_low:
        return (
            "Rxd is FLOATING — the adapter is receiving only its own Txd through\n"
            "  cable capacitance, so nothing is driving its receive line. Detach\n"
            "  the sensor and rerun: if this result is unchanged, the sensor was\n"
            "  never in the signal path and the fault is the adapter or the wire\n"
            "  from the sensor's Txd (pin 4, black) to the adapter's RX."
        )
    return "Only length-matched echoes seen; the sensor is not replying."


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else discovery()
    if port is None:
        print("No declinometer found. Pass a port explicitly: "
              "uv run python -m _tools.dec_probe /dev/tty.usbserial-XXXX")
        return 1
    print(f"Probing {port}")

    for baudrate in BAUDRATES:
        try:
            if listen(port, baudrate):
                print(f"\n>>> Data seen at {baudrate} baud.")
        except serial.SerialException as e:
            print(f"  SerialException at {baudrate}: {e}")

    # Level Developments command set (SOLAR-360 / LCH-360 datasheet, p4).
    # Commands are lower case and exactly 7 bytes, sent as one write since the
    # device discards a command with >100ms between characters.
    #   get-360 -> angle: 4-byte INT32 (angle x 1000), or 9-byte "+xxx.xxx\r"
    #   gettemp -> temperature; answers even when the sensor is not moving
    #   setoasc -> switch output to ASCII       (reply "OK")
    #   setcasc -> start continuous ASCII output (reply "OK")
    for command in ("gettemp", "get-360", "setoasc", "setcasc"):
        try:
            poll(port, 38400, command)
        except serial.SerialException as e:
            print(f"  SerialException polling {command!r}: {e}")

    print("\n=== is anything driving the receive line? ===")
    try:
        print(f"\nVERDICT: {verdict(port)}")
    except serial.SerialException as e:
        print(f"  SerialException during verdict: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
