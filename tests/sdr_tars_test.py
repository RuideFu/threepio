import sys
import time
import types
from unittest.mock import patch

import numpy as np

import _tools.sdr_tars as sdr_tars
import _tools.settings as settings
from _tools.sdr_tars import SdrTars, create_data_source, sdr_discovery
from _tools.tars import Tars


class FakeParent:
    def __init__(self):
        self.logged = []

    def log(self, message, allow_dups=False, warning=False):
        self.logged.append((message, warning))


class FakeRtlSdr:
    def __init__(self, serial_number=None, block=None):
        self.serial_number = serial_number
        self.sample_rate = None
        self.center_freq = None
        self.gain = None
        self.bias_tee_calls = []
        self.closed = False
        self._block = block if block is not None else np.zeros(512, dtype=complex)

    def set_bias_tee(self, enabled):
        self.bias_tee_calls.append(enabled)

    def read_samples(self, num_samples):
        time.sleep(0.001)
        return self._block

    def close(self):
        self.closed = True


def _fake_rtlsdr_module(serials):
    module = types.ModuleType("rtlsdr")

    class RtlSdr(FakeRtlSdr):
        @staticmethod
        def get_device_serial_addresses():
            return serials

    module.RtlSdr = RtlSdr
    return module


def _clean_env():
    return patch.dict(sdr_tars.os.environ, {}, clear=True)


# - MARK: sdr_discovery


def test_discovery_returns_none_when_pyrtlsdr_is_missing():
    with patch.dict(sys.modules, {"rtlsdr": None}):
        assert sdr_discovery() is None


def test_discovery_returns_none_when_librtlsdr_fails_to_load():
    with patch.object(sdr_tars.importlib, "import_module", side_effect=OSError):
        assert sdr_discovery() is None


def test_discovery_returns_first_serial():
    with patch.dict(sys.modules, {"rtlsdr": _fake_rtlsdr_module(["0001", "0002"])}):
        assert sdr_discovery() == "0001"


def test_discovery_returns_none_when_no_devices_are_connected():
    with patch.dict(sys.modules, {"rtlsdr": _fake_rtlsdr_module([])}):
        assert sdr_discovery() is None


# - MARK: create_data_source


def test_default_device_is_dataq():
    parent = FakeParent()
    with _clean_env(), patch.object(sdr_tars, "load_settings", return_value={}):
        source = create_data_source(parent, dataq_port=None)
    assert isinstance(source, Tars) and source.testing


def test_rtlsdr_setting_creates_sdr_source():
    parent = FakeParent()
    with _clean_env(), patch.object(
        sdr_tars, "load_settings", return_value={"device": "rtlsdr"}
    ), patch.dict(sys.modules, {"rtlsdr": _fake_rtlsdr_module(["0001"])}):
        source = create_data_source(parent, dataq_port=None)
    assert isinstance(source, SdrTars)
    assert source._sdr.serial_number == "0001"


def test_rtlsdr_setting_falls_back_to_simulation_with_a_warning():
    parent = FakeParent()
    with _clean_env(), patch.object(
        sdr_tars, "load_settings", return_value={"device": "rtlsdr"}
    ), patch.dict(sys.modules, {"rtlsdr": None}):
        source = create_data_source(parent, dataq_port=None)
    assert isinstance(source, Tars) and source.testing
    assert any(warning for _, warning in parent.logged)


def test_environment_variable_overrides_the_settings_file():
    parent = FakeParent()
    with _clean_env(), patch.object(
        sdr_tars, "load_settings", return_value={"device": "dataq"}
    ), patch.dict(sdr_tars.os.environ, {"THREEPIO_DEVICE": "rtlsdr"}), patch.dict(
        sys.modules, {"rtlsdr": _fake_rtlsdr_module(["0001"])}
    ):
        source = create_data_source(parent, dataq_port=None)
    assert isinstance(source, SdrTars)


# - MARK: SdrTars

H1_HZ = sdr_tars.H1_LINE_MHZ * 1e6


def _make_sdr_tars(parent=None, fake=None):
    fake = fake if fake is not None else FakeRtlSdr()
    return SdrTars(parent or FakeParent(), device="0001", sdr_factory=lambda: fake), fake


def test_construction_configures_the_dongle():
    with _clean_env():
        source, fake = _make_sdr_tars()
    assert fake.sample_rate == sdr_tars.DEFAULT_SAMPLE_RATE
    assert fake.center_freq == H1_HZ
    assert fake.gain == sdr_tars.DEFAULT_GAIN
    assert fake.bias_tee_calls == []  # Off by default


def test_read_latest_is_none_before_any_data():
    with _clean_env():
        source, _ = _make_sdr_tars()
    assert source.read_latest() is None


def test_read_latest_returns_scaled_power_and_drains_the_accumulator():
    with _clean_env():
        source, _ = _make_sdr_tars()
    samples = np.array([1 + 1j, -1 - 1j, 1 - 1j, -1 + 1j])  # Zero mean, |iq|^2 = 2
    source._ingest(samples)
    datum = source.read_latest()
    assert datum is not None
    assert datum.a == datum.b
    assert abs(datum.a - 2.0 * sdr_tars.POWER_SCALE) < 1e-9
    assert source.read_latest() is None


def test_pure_dc_block_integrates_to_zero_power():
    with _clean_env():
        source, _ = _make_sdr_tars()
    source._ingest(np.full(512, 0.5 + 0.5j))
    assert source.read_latest().a < 1e-9


def test_start_and_stop_manage_the_thread_and_dongle():
    with _clean_env(), patch.dict(sdr_tars.os.environ, {"THREEPIO_SDR_BIAS_TEE": "1"}):
        source, fake = _make_sdr_tars()
    assert fake.bias_tee_calls == [True]
    source.start()
    assert source.acquiring
    time.sleep(0.05)
    source.stop()
    assert not source._thread.is_alive()
    assert fake.closed
    assert fake.bias_tee_calls == [True, False]


def test_worker_error_is_logged_once_from_read_latest():
    parent = FakeParent()

    class BrokenRtlSdr(FakeRtlSdr):
        def read_samples(self, num_samples):
            raise IOError("usb gone")

    with _clean_env():
        source, _ = _make_sdr_tars(parent, BrokenRtlSdr())
    source.start()
    time.sleep(0.05)
    assert source.read_latest() is None
    assert source.read_latest() is None
    assert sum(warning for _, warning in parent.logged) == 1
    source.stop()


# - MARK: settings


def test_settings_round_trip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert settings.load_settings() == {}
    settings.save_settings(device="rtlsdr")
    settings.save_settings(other=1)
    assert settings.load_settings() == {"device": "rtlsdr", "other": 1}


def test_corrupt_settings_file_is_tolerated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / settings.SETTINGS_FILE).write_text("not json{")
    assert settings.load_settings() == {}
