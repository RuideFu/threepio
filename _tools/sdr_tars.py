"""
This module provides an RTL-SDR total-power backend with the same duck-typed
contract as Tars (start/stop/read_latest -> SignalDatum | None), plus discovery
and a factory that picks the signal backend from the persisted device setting.

A background thread owns the dongle and streams sync reads continuously,
accumulating total power; read_latest() only drains the accumulator, so the
GUI thread never touches USB. Continuum power is mean |IQ|^2 over everything
acquired since the previous poll (~one strip-chart sample per INTEGRATION_TIME).
"""

import importlib
import os
import threading

import numpy as np

from .settings import load_settings
from .tars import SignalDatum, Tars

DEVICE_ENV = "THREEPIO_DEVICE"  # dataq | rtlsdr; overrides the settings file
SDR_FREQ_ENV = "THREEPIO_SDR_FREQ_MHZ"
SDR_RATE_ENV = "THREEPIO_SDR_RATE"
SDR_GAIN_ENV = "THREEPIO_SDR_GAIN"
SDR_BIAS_TEE_ENV = "THREEPIO_SDR_BIAS_TEE"

# Duplicated from teeny-tiny-telescope/ttt/utils.py; that is a separate uv
# project, so importing across the boundary is not an option.
H1_LINE_MHZ = 1420.405751768

DEFAULT_SAMPLE_RATE = 2.048e6  # Hz
DEFAULT_GAIN = 49.6  # dB; pyrtlsdr snaps to the nearest supported value

# librtlsdr requires read sizes in multiples of 512 samples. 16384 samples is
# 8 ms at 2.048 MS/s, so each read blocks well under one 10 ms GUI tick.
BLOCK_SIZE = 16384

# Raw mean |IQ|^2 of +/-1-normalized samples is ~1e-3..1 depending on gain.
# Data files record "%.4f", so scale into a volt-like 0.3-5 range to keep
# four decimals meaningful. Linear (not dB) so downstream cal/background
# ratios work like they do for the square-law detector.
POWER_SCALE = 100.0


def sdr_discovery() -> str | None:
    """Return the serial of the first RTL-SDR, or None if pyrtlsdr, librtlsdr,
    or the device itself is absent."""
    try:
        # importlib at call time keeps pyrtlsdr optional and lets tests inject
        # sys.modules["rtlsdr"]. A missing librtlsdr library raises OSError.
        rtlsdr = importlib.import_module("rtlsdr")
    except (ImportError, OSError):
        return None
    try:
        serials = rtlsdr.RtlSdr.get_device_serial_addresses()
    except Exception:
        return None
    return serials[0] if serials else None


class SdrTars:
    """
    RTL-SDR continuum backend. Matches the parts of the Tars interface the app
    uses: start(), stop(), read_latest() -> SignalDatum | None.
    """

    def __init__(self, parent, device: str, sdr_factory=None):
        self.parent = parent
        self.testing = False  # Interface parity with Tars
        self.acquiring = False

        self._lock = threading.Lock()
        self._power_sum = 0.0  # Sum of |IQ|^2 (DC-removed) since last poll
        self._sample_count = 0
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        # Worker errors cross to the GUI thread here; read_latest() logs them.
        self._error: str | None = None
        self._error_logged = False

        if sdr_factory is None:
            rtlsdr = importlib.import_module("rtlsdr")
            sdr_factory = lambda: rtlsdr.RtlSdr(serial_number=device)
        self._sdr = sdr_factory()
        self._sdr.sample_rate = float(os.environ.get(SDR_RATE_ENV) or DEFAULT_SAMPLE_RATE)
        self._sdr.center_freq = float(os.environ.get(SDR_FREQ_ENV) or H1_LINE_MHZ) * 1e6
        self._sdr.gain = float(os.environ.get(SDR_GAIN_ENV) or DEFAULT_GAIN)

        self._bias_tee = os.environ.get(SDR_BIAS_TEE_ENV, "") not in ("", "0")
        if self._bias_tee:
            # On our own open handle, unlike shelling out to rtl_biast, which
            # fails once pyrtlsdr has claimed the USB interface.
            try:
                self._sdr.set_bias_tee(True)
                self.parent.log("RTL-SDR bias tee enabled")
            except Exception as exc:
                self.parent.log(f"RTL-SDR bias tee failed: {exc!r}", warning=True)

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.acquiring = True

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._bias_tee:
            try:
                self._sdr.set_bias_tee(False)
            except Exception:
                pass
        self._sdr.close()
        self.acquiring = False

    def read_latest(self) -> SignalDatum | None:
        """Drain the power accumulated since the last poll. Never blocks."""
        if self._error and not self._error_logged:
            self.parent.log(self._error, warning=True)
            self._error_logged = True
        with self._lock:
            if self._sample_count == 0:
                return None
            power = self._power_sum / self._sample_count
            self._power_sum, self._sample_count = 0.0, 0
        return self._map_power(power * POWER_SCALE)

    # Helpers

    def _run(self):
        try:
            while not self._stop_event.is_set():
                self._ingest(self._sdr.read_samples(BLOCK_SIZE))
        except Exception as exc:
            self._error = f"RTL-SDR acquisition failed: {exc!r}"

    def _ingest(self, samples):
        # Subtracting the block mean removes the 8-bit ADC's DC spike, leaving
        # power as a variance; drop this line if raw power is ever wanted.
        samples = samples - samples.mean()
        block_power = float(np.mean(samples.real**2 + samples.imag**2))
        with self._lock:
            self._power_sum += block_power * len(samples)
            self._sample_count += len(samples)

    @staticmethod
    def _map_power(scaled_power: float) -> SignalDatum:
        """
        Map one dongle's total power onto the two-channel file format.
        Duplicating A keeps both strip-chart traces and downstream two-channel
        tooling alive. Alternatives: b=0.0 to mark B as fake, split-band A/B
        (needs an FFT), or a second dongle feeding B.
        """
        return SignalDatum(a=scaled_power, b=scaled_power)


def create_data_source(parent, dataq_port: str | None):
    """
    Pick the signal backend once at startup, from THREEPIO_DEVICE or the
    persisted Device-menu choice. Returns an object with start()/stop()/
    read_latest() -> SignalDatum | None (Tars or SdrTars).
    """
    choice = os.environ.get(DEVICE_ENV) or load_settings().get("device", "dataq")
    if choice == "rtlsdr":
        serial = sdr_discovery()
        if serial is None:
            parent.log("RTL-SDR selected but not found, simulating data", warning=True)
            return Tars(parent, device=None)
        try:
            source = SdrTars(parent, device=serial)
        except Exception as exc:
            # The dongle can be present but unopenable, e.g. held by the
            # dvb_usb_rtl28xxu kernel module.
            parent.log(f"RTL-SDR open failed ({exc!r}), simulating data", warning=True)
            return Tars(parent, device=None)
        parent.log(f"Using RTL-SDR serial {serial} as signal source")
        return source
    return Tars(parent, device=dataq_port)
