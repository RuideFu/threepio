from types import SimpleNamespace
from unittest.mock import patch

import _tools.minitars as minitars
import _tools.tars as tars


FTDI_PORT = SimpleNamespace(device="/dev/ttyUSB0", hwid="USB VID:PID=0403:6001")


def _discover(module, *, native_exists, explicit=None, ports=(FTDI_PORT,)):
    environment = {} if explicit is None else {"THREEPIO_DEC_PORT": explicit}
    with patch.object(module.serial.tools.list_ports, "comports", return_value=ports), patch.object(
        module.os.path, "exists", return_value=native_exists
    ), patch.dict(module.os.environ, environment, clear=True):
        result = module.discovery()
    return result[1] if module is tars else result


def test_native_uart_is_preferred_over_connected_ftdi_adapter():
    assert _discover(tars, native_exists=True) == "/dev/serial0"
    assert _discover(minitars, native_exists=True) == "/dev/serial0"


def test_explicit_port_is_preferred_over_native_uart():
    assert _discover(tars, native_exists=True, explicit="/dev/custom") == "/dev/custom"
    assert _discover(minitars, native_exists=True, explicit="/dev/custom") == "/dev/custom"


def test_ftdi_adapter_is_used_when_native_uart_is_absent():
    assert _discover(tars, native_exists=False) == "/dev/ttyUSB0"
    assert _discover(minitars, native_exists=False) == "/dev/ttyUSB0"


def test_no_port_is_returned_when_nothing_is_available():
    assert _discover(tars, native_exists=False, ports=()) is None
    assert _discover(minitars, native_exists=False, ports=()) is None
