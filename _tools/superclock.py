"""Clock model for sidereal/RA calculations."""

from __future__ import annotations
import datetime
import time
from astropy.time import Time
from astropy.coordinates import EarthLocation
from astropy.utils import iers

# Offline operation: never fetch IERS Earth-rotation tables from the internet.
# Use the tables bundled with astropy-iers-data and extrapolate (with a warning)
# if the system date runs past them — ms-level UT1 error, negligible for us.
iers.conf.auto_download = False
iers.conf.auto_max_age = None
iers.conf.iers_degraded_accuracy = "warn"

SIDEREAL = 1.00273790935  # The number of sidereal seconds per second
GB_LATITUDE = 38.437235  # North
GB_LONGITUDE = -79.839835  # West (so negative)
SIDEREAL_DAY_SECONDS = 86400


class SuperClock:
    """Sidereal clock model with optional manual calibration offset."""

    def __init__(self):
        self.manual_sidereal_offset_seconds = 0.0
        self.calibration_epoch_time = 0.0
        self.calibration_sidereal_seconds = 0.0
        self.propagation_anchor_monotonic = 0.0
        self.propagation_anchor_epoch_time = 0.0
        self.propagation_anchor_sidereal_seconds = 0.0
        self.resync_from_astropy()

    @staticmethod
    def get_time() -> float:
        return time.time()

    @staticmethod
    def solar_to_sidereal(solar_seconds: float) -> float:
        return solar_seconds * SIDEREAL

    @staticmethod
    def sidereal_to_solar(sidereal_seconds: float) -> float:
        return sidereal_seconds / SIDEREAL

    @staticmethod
    def get_time_slug() -> str:
        return "{:%Y.%m.%d-%H.%M}".format(datetime.datetime(*time.localtime()[:5]))

    @staticmethod
    def get_time_until(destination_time) -> float:
        return time.time() - destination_time

    @staticmethod
    def deformat_time_string(time_string: str) -> float:
        hours, minutes, seconds = map(float, time_string.split(":"))
        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def hours_to_seconds(hours: float) -> float:
        return hours * 3600

    def _sidereal_seconds_from_astropy(self, epoch_time: float) -> float:
        loc = EarthLocation(lat=GB_LATITUDE, lon=GB_LONGITUDE)
        t = Time(epoch_time, format="unix", scale="utc", location=loc)
        return SuperClock.hours_to_seconds(t.sidereal_time("apparent").value) % SIDEREAL_DAY_SECONDS

    def calibrate_sidereal_time(self, sidereal_seconds: float) -> None:
        astronomical_truth = self._sidereal_seconds_from_astropy(time.time())
        self.manual_sidereal_offset_seconds = (sidereal_seconds - astronomical_truth) % SIDEREAL_DAY_SECONDS
        self.resync_from_astropy()

    def resync_from_astropy(self) -> None:
        epoch_time = time.time()
        monotonic_time = time.monotonic()
        astronomical_sidereal = self._sidereal_seconds_from_astropy(epoch_time)
        corrected_sidereal = (astronomical_sidereal + self.manual_sidereal_offset_seconds) % SIDEREAL_DAY_SECONDS

        self.calibration_epoch_time = epoch_time
        self.calibration_sidereal_seconds = corrected_sidereal
        self.propagation_anchor_epoch_time = epoch_time
        self.propagation_anchor_monotonic = monotonic_time
        self.propagation_anchor_sidereal_seconds = corrected_sidereal

    def get_sidereal_seconds(self) -> float:
        elapsed_solar = time.monotonic() - self.propagation_anchor_monotonic
        return (self.propagation_anchor_sidereal_seconds + SIDEREAL * elapsed_solar) % SIDEREAL_DAY_SECONDS

    def ra_to_epoch_time(self, ra_seconds: float) -> float:
        current_sidereal = self.get_sidereal_seconds()
        delta_sidereal = (ra_seconds - current_sidereal) % SIDEREAL_DAY_SECONDS
        delta_solar = self.sidereal_to_solar(delta_sidereal)
        return time.time() + delta_solar

    def get_sidereal_tuple(self) -> tuple[int, int, int]:
        current_sidereal_time = self.get_sidereal_seconds()
        minutes, seconds = divmod(current_sidereal_time, 60)
        hours, minutes = divmod(minutes, 60)
        return int(hours) % 24, int(minutes), int(seconds)

    def get_formatted_sidereal_time(self) -> str:
        hours, minutes, seconds = self.get_sidereal_tuple()
        return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}"
