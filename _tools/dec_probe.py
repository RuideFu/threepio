"""
Standalone declinometer probe. Run outside the GUI to find out whether the
device sends anything at all, at which baudrate, and in which framing.

    uv run python -m _tools.dec_probe                 # auto-detect port
    uv run python -m _tools.dec_probe COM4            # explicit port
    uv run python -m _tools.dec_probe --out probe.log # tee a transcript
    uv run python -m _tools.dec_probe --write         # allow NVM-changing cmds

Threepio must NOT be running: the port can only be held by one process.

The central question this answers is MISCONFIGURED vs NOT TRANSMITTING. A unit
in the factory-default poll mode is silent until commanded, so "we heard
nothing" is only evidence of a fault once every plausible baudrate and framing
has been *asked*. That is what sweep() does; passive listening alone cannot
distinguish a healthy poll-mode unit at an unexpected rate from a dead one.
"""
import argparse
import re
import struct
import sys
import time

import serial
import serial.tools.list_ports

from .minitars import discovery

# Every rate the sensor can be set to; the setting lives in non-volatile memory,
# so a unit configured by someone else can be at any of them. 38400 first
# because it is the documented default and the rate the working unit uses.
BAUDRATES = [38400, 2400, 4800, 9600, 19200, 57600, 115200]

# 8N1 is the documented framing. The rest are here to rule out a customer
# specific build: a parity mismatch does not silence a line, but it does turn
# every reply into bytes the LD parser rejects, which looks like "no response"
# to anything that only checks for well-formed frames.
FRAMINGS = [
    (8, serial.PARITY_NONE, serial.STOPBITS_ONE),
    (8, serial.PARITY_EVEN, serial.STOPBITS_ONE),
    (8, serial.PARITY_ODD, serial.STOPBITS_ONE),
    (7, serial.PARITY_EVEN, serial.STOPBITS_ONE),
]

# Long enough to catch NMEA mode, which transmits on an interval (1s by default)
# rather than continuously.
LISTEN_SECONDS = 5.0

# Level Developments command set (SOLAR-360 / LCH-360 datasheet, p4).
# Commands are lower case and exactly 7 bytes, sent as one write since the
# device discards a command with >100ms between characters.
#   get-360 -> angle: 4-byte INT32 (angle x 1000), or 9-byte "+xxx.xxx\r"
#   gettemp -> temperature; answers even when the sensor is not moving
QUERY_COMMANDS = ("gettemp", "get-360")
# These persist to non-volatile memory, so they are gated behind --write:
# a brand-new unit headed for RMA should reach the vendor in its factory state.
#   setoasc -> switch output to ASCII        (reply "OK")
#   setcasc -> start continuous ASCII output (reply "OK")
WRITE_COMMANDS = ("setoasc", "setcasc")
# 'strXXXX' sets the continuous-output interval in milliseconds, 0050..9999,
# and replies "OK". It is the rate 'setcasc' then transmits at, and it lives in
# non-volatile memory like the rest, so two units of the same part number can
# stream at very different rates. The factory default is str1000 (1Hz), which
# is 10x slower than the str0100 (10Hz) the observatory's older unit uses.
# Note this is NOT the low pass filter: the datasheet's filter index table
# (0.125-16Hz) explicitly "does not relate to output data rate".
RATE_COMMAND = "str{:04d}"
DEFAULT_INTERVAL_MS = 1000
THREEPIO_INTERVAL_MS = 100
# Returns an NMEA0183-mode unit to the LD protocol. Also a persistent change.
NMEA_TO_LD = "$PLDL100,1*38\r\n"

# What a genuine reply looks like. Anything matching one of these came out of a
# correctly-framed UART at the rate we were listening on; misframed noise from
# a stream at some other rate essentially never does.
RE_ANGLE = re.compile(rb"[+-]\d{3}\.\d{3}\r")   # get-360 ASCII, e.g. +088.246\r
RE_TEMP = re.compile(rb"[+-]\d{1,3}\.\d\r")     # gettemp,  e.g. +28.1\r
RE_NMEA = re.compile(rb"\$P?[A-Z]{4,5}[0-9,.\-+]*\*[0-9A-Fa-f]{2}")


def _read_for(ser, seconds: float, hard_cap: float = 3.0) -> bytes:
    """
    Accumulate until the line has been quiet for `seconds`.

    The old fixed-sleep-then-read-once pattern truncated slow replies: at 2400
    baud a 9-byte answer plus turnaround does not reliably land inside 0.5s.
    Activity extends the window, but `hard_cap` bounds the total so a unit in
    continuous output mode cannot hold us here forever.
    """
    got = b""
    start = time.perf_counter()
    quiet_until = start + seconds
    while time.perf_counter() < quiet_until:
        if time.perf_counter() - start > hard_cap:
            break
        n = ser.in_waiting
        if n:
            got += ser.read(n)
            quiet_until = time.perf_counter() + seconds
        else:
            time.sleep(0.02)
    return got


def _open(port: str, baudrate: int, framing=(8, serial.PARITY_NONE, serial.STOPBITS_ONE),
          timeout: float = 0.2) -> serial.Serial:
    """
    Open with every handshake line explicitly disabled.

    The sensor is a 3-wire device and drives neither CTS nor DSR. Relying on
    pyserial's defaults leaves that as an unstated assumption in the transcript;
    stating it means a reader cannot blame flow control for a silent port.
    """
    bytesize, parity, stopbits = framing
    return serial.Serial(
        port,
        baudrate=baudrate,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        timeout=timeout,
        rtscts=False,
        dsrdtr=False,
        xonxoff=False,
    )


def framing_name(framing) -> str:
    bytesize, parity, stopbits = framing
    return f"{bytesize}{parity}{int(stopbits)}"


def classify(data: bytes) -> str:
    """
    Name what came back, so silence, noise and a real answer stay distinct.

    'garbage' is the important middle case: bytes are arriving, so something is
    driving the receive line, but they do not frame up at this rate. That is a
    baudrate mismatch or a non-LD protocol, not a dead transmitter.
    """
    if not data:
        return "silent"
    if RE_NMEA.search(data):
        return "nmea"
    if RE_ANGLE.search(data):
        return "ld-ascii"
    if RE_TEMP.search(data):
        return "ld-temp"
    if b"OK" in data:
        return "ld-ok"
    # Binary output mode. The device is big-endian: a get-360 reply of
    # 00 01 7f e3 is 98275 = 98.275 degrees, which only decodes that way round.
    # Range-checking the result is what separates a real reading from noise that
    # happens to be the right length.
    if len(data) == 4:
        val = struct.unpack(">i", data)[0]
        if -360000 <= val <= 360000:
            return "ld-binary"
    # gettemp answers with a 2-byte INT16 of degrees C x 100.
    if len(data) == 2:
        val = struct.unpack(">h", data)[0]
        if -4000 <= val <= 8500:            # -40..85C, the sensor's rated range
            return "ld-binary-temp"
    printable = sum(32 <= b < 127 or b in (10, 13) for b in data)
    if printable == len(data):
        return "ascii?"
    return "garbage"


def is_valid(kind: str) -> bool:
    """A reply we can actually attribute to the sensor's protocol."""
    return kind in ("ld-ascii", "ld-temp", "ld-ok", "ld-binary",
                    "ld-binary-temp", "nmea")


def sweep(port: str, baudrates=None, framings=None) -> dict:
    """
    Ask for a reading at every baudrate x framing combination.

    This is the part that separates misconfigured from broken. Passive listening
    only finds a unit already in continuous output mode; the factory default is
    poll mode, where the sensor says nothing until it is asked in a framing it
    understands. Each combination gets a passive look first (catches continuous
    and NMEA-interval modes) and then a gettemp, which answers even when the
    sensor is perfectly still.
    """
    baudrates = BAUDRATES if baudrates is None else baudrates
    framings = FRAMINGS if framings is None else framings
    results = {}
    print(f"\n{'baud':>7} {'fram':>5} {'passive':>18}  {'gettemp':>18}")
    print(f"{'-' * 7} {'-' * 5} {'-' * 18}  {'-' * 18}")
    for baudrate in baudrates:
        for framing in framings:
            key = (baudrate, framing)
            try:
                with _open(port, baudrate, framing) as ser:
                    time.sleep(0.12)          # let the adapter apply the settings
                    passive = _read_for(ser, 0.35, hard_cap=0.7)
                    ser.reset_input_buffer()
                    ser.write(b"gettemp")
                    ser.flush()
                    active = _read_for(ser, 0.5, hard_cap=1.2)
            except (serial.SerialException, OSError, ValueError) as e:
                # A legacy 16550 COM port rejects some rates outright, and not
                # every adapter accepts 7E1. Skipping keeps one refusal from
                # ending the sweep.
                print(f"{baudrate:>7} {framing_name(framing):>5}  unsupported ({e})")
                continue
            results[key] = {"passive": passive, "active": active}
            pk, ak = classify(passive), classify(active)
            results[key]["passive_kind"], results[key]["active_kind"] = pk, ak
            flag = " <<<" if is_valid(pk) or is_valid(ak) else ""
            print(
                f"{baudrate:>7} {framing_name(framing):>5} "
                f"{f'{len(passive)}B {pk}':>18}  {f'{len(active)}B {ak}':>18}{flag}"
            )
    return results


def best_setting(results: dict):
    """The first baud/framing that produced a reply we recognise, if any."""
    for key, r in results.items():
        if is_valid(r["passive_kind"]) or is_valid(r["active_kind"]):
            return key
    return None


def listen(port: str, baudrate: int, seconds: float = LISTEN_SECONDS,
           framing=(8, serial.PARITY_NONE, serial.STOPBITS_ONE)) -> bytes:
    """Open at one baudrate and dump whatever shows up."""
    collected = b""
    with _open(port, baudrate, framing) as ser:
        print(
            f"\n=== {baudrate} baud {framing_name(framing)} === is_open={ser.is_open} "
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
        print(
            f"  total={len(collected)} bytes, terminators={terminators}, "
            f"kind={classify(collected)}"
        )
        if b"$PLDL" in collected:
            # NMEA mode ignores the 7-byte LD commands entirely, so say so:
            # threepio's parser expects the LD format and will reject these.
            print(
                "  >>> NMEA0183 mode. Return it to LD mode by sending:\n"
                f"        {NMEA_TO_LD.strip()}\\r\\n   (probe --write does this)"
            )
    return collected


def poll(port: str, baudrate: int, command: str,
         framing=(8, serial.PARITY_NONE, serial.STOPBITS_ONE)) -> bytes:
    """Some firmware only answers when asked; try a request/response exchange."""
    with _open(port, baudrate, framing, timeout=1.0) as ser:
        time.sleep(0.12)
        ser.reset_input_buffer()
        ser.write(command.encode("ascii"))
        ser.flush()
        reply = _read_for(ser, 0.5, hard_cap=2.0)
    print(
        f"\n=== poll {command!r} @ {baudrate} {framing_name(framing)} === "
        f"kind={classify(reply)} reply={reply!r}"
    )
    return reply


def probe_nmea(port: str, baudrates=None) -> tuple:
    """
    Actively rule NMEA0183 mode in or out.

    Detecting it by waiting for a '$PLDL' sentence only works if the unit is
    transmitting on an interval. An NMEA unit set to answer on demand is just as
    silent as a dead one, so send the return-to-LD command at each rate and see
    whether an LD query starts working afterwards. This writes to NVM.
    """
    baudrates = BAUDRATES if baudrates is None else baudrates
    for baudrate in baudrates:
        try:
            with _open(port, baudrate, timeout=0.5) as ser:
                time.sleep(0.12)
                ser.reset_input_buffer()
                ser.write(NMEA_TO_LD.encode("ascii"))
                ser.flush()
                nmea_reply = _read_for(ser, 0.4, hard_cap=1.0)
                ser.reset_input_buffer()
                ser.write(b"gettemp")
                ser.flush()
                after = _read_for(ser, 0.5, hard_cap=1.2)
        except (serial.SerialException, OSError, ValueError) as e:
            print(f"  {baudrate:6d} unsupported ({e})")
            continue
        kind = classify(after)
        print(
            f"  {baudrate:6d} NMEA->LD reply={nmea_reply!r} "
            f"then gettemp -> {len(after)}B {kind} {after!r}"
        )
        if is_valid(kind):
            return baudrate, after
    return None, b""


def measure_rate(port: str, baudrate: int, framing, seconds: float = 6.0) -> float:
    """
    Frames per second of a continuously-streaming unit.

    Worth measuring rather than eyeballing, because the failure it catches is
    quiet: a unit at the 1Hz factory default still works, still parses, and
    still shows a live angle, so nothing looks broken — it just samples ten
    times slower than the one it is replacing.

    Counting has to accumulate first and split once. Splitting each read
    separately double-counts any frame that straddles a read boundary, which
    silently inflates the rate.
    """
    with _open(port, baudrate, framing) as ser:
        time.sleep(0.3)
        ser.reset_input_buffer()
        buffer = b""
        start = time.perf_counter()
        while time.perf_counter() - start < seconds:
            n = ser.in_waiting
            if n:
                buffer += ser.read(n)
            else:
                time.sleep(0.002)
        elapsed = time.perf_counter() - start
    chunks = buffer.split(b"\r")[:-1]
    valid = [c for c in chunks if RE_ANGLE.fullmatch(c + b"\r")]
    rate = len(valid) / elapsed if elapsed else 0.0
    print(
        f"\n=== output rate === {len(valid)} angle frames in {elapsed:.1f}s "
        f"= {rate:.2f} Hz  (malformed {len(chunks) - len(valid)})"
    )
    if valid and rate < 5.0:
        want = RATE_COMMAND.format(THREEPIO_INTERVAL_MS)
        print(
            f"  This is the {DEFAULT_INTERVAL_MS}ms factory default, not a fault —\n"
            f"  the sensor streams correctly, just slowly. Send '{want}' to move it\n"
            f"  to {1000 // THREEPIO_INTERVAL_MS}Hz. Interval is in ms, 0050..9999,"
            " stored in NVM."
        )
    return rate


def levels(port: str, hold: float = 12.0) -> None:
    """
    Park the PC's Txd at a known RS232 level so a DMM can trace the harness.

    A voltmeter cannot follow a byte, so a normally-transmitting port tells you
    nothing about which wire is which. Holding a break forces Txd to SPACE
    (positive) and releasing it holds MARK (negative, the idle state), each long
    enough to read by hand. Whichever pin swings between roughly +7V and -7V is
    the PC's transmitter; the pin that stays put is not connected to it.

    This is what distinguishes "the sensor's Txd is dead" from "the sensor's Txd
    never reaches the connector we are listening on".
    """
    print(
        "\n=== level trace ===\n"
        "Put the DMM black lead on DB9 pin 5 (GND) and probe one pin at a time.\n"
        "Expected for a healthy 3-wire hookup:\n"
        "  DB9 pin 3 (PC Txd)  swings -7V (MARK) <-> +7V (SPACE) below\n"
        "  DB9 pin 2 (PC Rxd)  holds -5..-12V if the sensor is driving it,\n"
        "                      and sits near 0V if nothing is\n"
        "  M12 pin 3 (sens Rx) follows DB9 pin 3 if that wire is intact\n"
        "  M12 pin 4 (sens Tx) holds -5..-12V on a powered RS232 unit;\n"
        "                      near 0V means it is not an RS232 driver\n"
    )
    with _open(port, 38400) as ser:
        for label, brk in (("MARK  (idle, expect negative)", False),
                           ("SPACE (break, expect positive)", True)):
            ser.break_condition = brk
            print(f"  holding {label} for {hold:.0f}s ...", flush=True)
            deadline = time.perf_counter() + hold
            while time.perf_counter() < deadline:
                time.sleep(0.1)
        ser.break_condition = False
    print("  released; Txd back to normal idle.")


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
    # A legacy 16550 COM port rejects rates above 115200 outright ("the
    # parameter is incorrect"), so treat every rate as optional and skip the
    # ones this port will not accept.
    for baudrate in (9600, 38400, 115200, 230400):
        for payload in (b"gettemp", b"UUUUUUU"):
            try:
                with _open(port, baudrate) as ser:
                    time.sleep(0.12)
                    ser.reset_input_buffer()
                    ser.write(payload)
                    ser.flush()
                    got = _read_for(ser, 0.3, hard_cap=1.0)
            except (serial.SerialException, OSError, ValueError) as e:
                print(f"  {baudrate:6d} unsupported by this port ({e})")
                continue
            probes[(baudrate, payload)] = got
            print(f"  {baudrate:6d} sent={payload!r:12s} -> {len(got)}B {got!r}")

    if not probes:
        return "Could not open the port at any rate — is it the right COM port?"
    # Length alone is not evidence: capacitive pickup readily returns more bytes
    # than were sent. Require a reply the LD protocol can account for.
    replying = [g for g in probes.values() if is_valid(classify(g))]
    echoes = [g for (_, p), g in probes.items() if len(g) == len(p) and g]
    if replying:
        return "Sensor is replying. Rerun the command polls above for detail."
    if not echoes and not any(probes.values()):
        return (
            "Nothing comes back at all. Either nothing is wired to this port, or\n"
            "  it is the wrong COM port — check the list above and the DB9 it is on."
        )
    # A deliberate loopback (Txd shorted to Rxd, e.g. to test a cable with the
    # sensor unplugged) is DC-coupled, so it returns every payload verbatim at
    # every rate — including the low ones, where capacitive pickup dies out.
    verbatim_all = all(g == p for (_, p), g in probes.items())
    if verbatim_all:
        return (
            "CLEAN LOOPBACK — every payload came back verbatim at every rate,\n"
            "  which is a DC short from Txd to Rxd rather than a signal. If you\n"
            "  shorted the line deliberately to test a cable, that cable and the\n"
            "  DB9 wiring are good end to end: put the sensor back on it. If you\n"
            "  did not, Txd and Rxd are shorted somewhere in the harness."
        )
    alternating_ok = probes.get((38400, b"UUUUUUU")) == b"UUUUUUU"
    runs_corrupt = probes.get((38400, b"gettemp")) not in (b"", b"gettemp", None)
    dropout_low = probes.get((9600, b"gettemp")) == b""
    if alternating_ok and runs_corrupt and dropout_low:
        return (
            "Rxd is FLOATING — this port is receiving only its own Txd, coupled\n"
            "  back across the connector, and nothing is driving its receive line.\n"
            "  Wiring, per How2_SOLAR232.pdf (flying leads) / SOLAR-360 datasheet\n"
            "  (M12 connector) — the two documents use different colour codes:\n"
            "      sensor Transmit  yellow / black -> DB9 pin 2 (PC RXD)\n"
            "      sensor Receive   green  / blue  -> DB9 pin 3 (PC TXD)\n"
            "      0V and RS232 GND blue   / white -> DB9 pin 5, and to PSU 0V\n"
            "      +9-30V supply    red    / brown -> PSU only, NOT the DB9\n"
            "  If the wiring checks out, measure DB9 pin 2 against pin 5: a powered\n"
            "  idle RS232 driver sits at -5 to -12V. Around 0V means the sensor is\n"
            "  not driving the line — check that it has 9-30V across its supply\n"
            "  pair before suspecting the transmitter itself."
        )
    return "Only length-matched echoes seen; the sensor is not replying."


def diagnose(results: dict, coupling: str) -> str:
    """
    Reduce the sweep to the one distinction that decides what happens next:
    is this unit configured differently than expected, or is it not talking?
    """
    found = best_setting(results)
    if found:
        baudrate, framing = found
        r = results[found]
        kind = r["active_kind"] if is_valid(r["active_kind"]) else r["passive_kind"]
        mode = "continuous/interval" if is_valid(r["passive_kind"]) else "poll"
        note = ""
        if (baudrate, framing) != (38400, FRAMINGS[0]):
            note = (
                "\n  This is NOT the documented default of 38400 8N1, so the unit was\n"
                "  shipped with a non-standard configuration. Threepio opens at\n"
                "  38400 8N1 (minitars.MiniTars.__init__), which is why it saw\n"
                "  nothing. No fault here — reconfigure the unit or the software."
            )
        if kind == "nmea":
            note += (
                "\n  Protocol is NMEA0183, not the LD command set threepio parses.\n"
                f"  Return it with: {NMEA_TO_LD.strip()}  (probe --write does this)"
            )
        if kind in ("ld-binary", "ld-binary-temp"):
            note += (
                "\n  Output is in BINARY mode, not ASCII. The sensor is answering\n"
                "  correctly, but threepio's parser reads the ASCII '+xxx.xxx\\r'\n"
                "  form and discards these bytes. Switch the unit with 'setoasc'\n"
                "  (probe --write does this), then 'setcasc' for continuous output."
            )
        return (
            f"MISCONFIGURED, NOT BROKEN — the sensor answers at {baudrate} baud "
            f"{framing_name(framing)}\n"
            f"  ({kind} format, {mode} mode). It transmits and parses commands "
            f"correctly.{note}"
        )

    noisy = [k for k, r in results.items()
             if r["passive"] or r["active"]]
    if noisy:
        rates = sorted({b for (b, _) in noisy})
        return (
            "SIGNAL PRESENT BUT UNREADABLE — bytes arrive, but none form a valid LD\n"
            f"  or NMEA reply at any of {len(results)} baud/framing combinations\n"
            f"  (activity seen at: {rates}).\n"
            "  Something is driving the receive line, so this is not a dead\n"
            "  transmitter or a broken supply. Most likely a protocol this probe\n"
            "  does not speak, or RS485 differential levels being partially\n"
            "  rectified by the RS232 receiver. Compare against the coupling test\n"
            "  below: if it also reports FLOATING, the bytes are the adapter's own\n"
            "  Txd coupling back and there is no sensor signal at all."
        )

    head = (
        "NOT TRANSMITTING — silence at every one of "
        f"{len(results)} baud/framing combinations, passive and polled.\n"
        "  Poll mode is now excluded: the unit was actively asked for a reading at\n"
        "  each setting and never answered, so this is not a case of a healthy\n"
        "  sensor waiting to be addressed.\n"
        "  Coupling test said:\n"
        + "\n".join(f"    {line.strip()}" for line in coupling.splitlines())
    )
    if coupling.startswith("Nothing comes back at all"):
        # Worth separating out, because it cuts *against* the obvious reading.
        # A floating Rxd is a high-impedance node and picks up the adapter's own
        # Txd capacitively, most strongly at the highest rates. Getting zero
        # bytes even at 230400 means something is holding that line — which is
        # what a live RS232 driver sitting at idle does. It is equally
        # consistent with Rxd simply not reaching the adapter, and the two are
        # told apart by running this probe again with the sensor unplugged.
        return head + (
            "\n  NOTE: not even capacitive pickup came back, including at 230400\n"
            "  where a floating Rxd is supposed to couple strongly. Before reading\n"
            "  anything into that, re-run with the sensor UNPLUGGED to see what a\n"
            "  genuinely floating line looks like on this rig:\n"
            "    - unplugged run shows coupling bytes, connected run does not ->\n"
            "      something is holding the line at idle, i.e. the transmitter is\n"
            "      alive but never sends. Look at configuration and firmware.\n"
            "    - unplugged run is silent too -> there is no coupling path on this\n"
            "      hardware (a short USB adapter tail has no long cable for Txd and\n"
            "      Rxd to couple across), so the test cannot discriminate here and\n"
            "      proves nothing either way. Fall back to a DMM on DB9 pin 2 vs\n"
            "      pin 5: a powered idle RS232 driver sits at -5 to -12V, and\n"
            "      around 0V means the sensor is not driving the line."
        )
    return head + (
        "\n  Remaining causes are physical: no supply at the sensor, Tx not wired to\n"
        "  DB9 pin 2, RS485 hardware in an RS232-labelled housing, or a dead\n"
        "  transmitter. Confirm with a DMM on DB9 pin 2 vs pin 5 — a powered idle\n"
        "  RS232 driver sits at -5 to -12V; around 0V means it is not driving."
    )


class _Tee:
    """Mirror stdout into a transcript file, for attaching to an RMA."""

    def __init__(self, stream, path):
        self.stream = stream
        self.file = open(path, "w")

    def write(self, data):
        self.stream.write(data)
        self.file.write(data)
        return len(data)

    def flush(self):
        self.stream.flush()
        self.file.flush()

    def close(self):
        self.file.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port", nargs="?", help="serial port; auto-detected if omitted")
    parser.add_argument("--out", help="tee the full transcript to this file")
    parser.add_argument(
        "--write",
        action="store_true",
        help="also send commands that change non-volatile settings "
        "(setoasc/setcasc, NMEA->LD). Off by default so a unit headed for RMA "
        "reaches the vendor in its factory state.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="sweep 8N1 only, skipping the parity variants",
    )
    parser.add_argument(
        "--levels",
        action="store_true",
        help="skip the sweep; hold Txd at MARK then SPACE so a DMM can trace "
        "which connector pin the PC's transmitter actually reaches",
    )
    args = parser.parse_args(argv)

    tee = _Tee(sys.stdout, args.out) if args.out else None
    if tee:
        sys.stdout = tee
    try:
        return _run(args)
    finally:
        if tee:
            sys.stdout = tee.stream
            tee.close()
            print(f"\nTranscript written to {args.out}")


def _run(args) -> int:
    print("Available ports:")
    for p in serial.tools.list_ports.comports():
        print(f"  {p.device:20s} {p.description}  [{p.hwid}]")

    port = args.port or discovery()
    if port is None:
        print(
            "\nNo declinometer auto-detected. Auto-detection looks for the FTDI\n"
            "adapter's USB id (VID:PID=0403:6001); a built-in COM port does not\n"
            "have one. Pass the port explicitly, using a name from the list above:\n"
            "  uv run python -m _tools.dec_probe COM4"
        )
        return 1
    print(f"\nProbing {port}   write_enabled={args.write}")

    if args.levels:
        levels(port)
        return 0

    framings = FRAMINGS[:1] if args.quick else FRAMINGS
    print(f"\n=== sweep: {len(BAUDRATES)} baudrates x {len(framings)} framings ===")
    print("passive = what arrives unprompted; gettemp = reply to an explicit query")
    results = sweep(port, framings=framings)

    found = best_setting(results)
    if found:
        baudrate, framing = found
        print(f"\n=== valid reply at {baudrate} {framing_name(framing)}: detail ===")
        for command in QUERY_COMMANDS:
            try:
                poll(port, baudrate, command, framing)
            except serial.SerialException as e:
                print(f"  SerialException polling {command!r}: {e}")
        stream = listen(port, baudrate, framing=framing)
        if classify(stream) == "ld-ascii":
            measure_rate(port, baudrate, framing)
    else:
        print("\n=== no valid reply in the sweep; active NMEA-mode check ===")
        if args.write:
            nmea_baud, _ = probe_nmea(port)
            if nmea_baud:
                print(f"\n>>> Unit was in NMEA mode; now answering at {nmea_baud}.")
                found = (nmea_baud, FRAMINGS[0])
        else:
            print(
                "  Skipped: returning a unit from NMEA to LD mode writes to NVM.\n"
                "  Re-run with --write to test it."
            )

    # Binary output is the case that most needs these commands, so gating them
    # on "found nothing" was backwards: a unit answering perfectly well in
    # binary got diagnosed and then left exactly as it was.
    post_write = None
    needs_ascii = False
    if found:
        r = results.get(found, {})
        kind = r.get("active_kind") if is_valid(r.get("active_kind", "")) \
            else r.get("passive_kind")
        needs_ascii = kind in ("ld-binary", "ld-binary-temp")

    if args.write and (not found or needs_ascii):
        baudrate, framing = found if found else (38400, FRAMINGS[0])
        print(f"\n=== output-mode commands @ {baudrate} {framing_name(framing)} "
              f"(writes NVM) ===")
        for command in WRITE_COMMANDS:
            try:
                poll(port, baudrate, command, framing)
            except serial.SerialException as e:
                print(f"  SerialException polling {command!r}: {e}")
        # setcasc starts a continuous stream, so listen again afterwards —
        # the sweep above ran before the mode change and could not have seen it.
        print("\n=== re-listen after setcasc ===")
        after = listen(port, baudrate, framing=framing)
        post_write = classify(after)

    print("\n=== is anything driving the receive line? ===")
    try:
        coupling = verdict(port)
    except serial.SerialException as e:
        coupling = f"coupling test failed: {e}"
    print(f"\nCOUPLING: {coupling}")

    # diagnose() reads the sweep, which ran before any --write command. Saying
    # "output is in BINARY mode" after setoasc has already fixed it would be
    # reporting a stale state, so the post-write observation wins.
    if post_write and is_valid(post_write):
        baudrate, framing = found if found else (38400, FRAMINGS[0])
        print(
            f"\nDIAGNOSIS: RESOLVED — after setoasc/setcasc the unit streams "
            f"{post_write} at {baudrate} {framing_name(framing)},\n"
            "  which is the format threepio parses. Nothing further to do."
        )
    else:
        print(f"\nDIAGNOSIS: {diagnose(results, coupling)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
