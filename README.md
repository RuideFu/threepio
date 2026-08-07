# Threepio 🤖

The new data acquisition system for the 40-foot radio telescope at the [Green Bank Observatory](https://greenbankobservatory.org/). This software is part of the [ERIRA](https://www.danreichart.com/erira) program.

## Dependencies

Threepio uses `PyQt5` for GUI and `pySerial` for communication to the data collection hardware, including a [SOLAR-360-2-RS232](https://www.leveldevelopments.com/products/inclinometers/inclinometer-sensors/single-axis-inclinometer-sensors/solar-360-series/solar-360-2-rs232-inclinometer-sensor-single-axis-180-rs232-with-tc/) inclinometer and a DataQ A2D card.

## Setting Up

Threepio uses [`uv`](https://docs.astral.sh/uv/) to manage its Python version, virtual environment, and dependencies.

### Install `uv`

**Linux & macOS**
```
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows** (PowerShell)
```
PS> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

See the [`uv` installation docs](https://docs.astral.sh/uv/getting-started/installation/) for alternatives (Homebrew, pipx, etc.).

### Clone & install

Clone the repo and `cd` into it.
```
$ git clone https://github.com/finnjames/threepio.git
$ cd threepio
```

Threepio requires Python 3.13.x. `uv` reads `pyproject.toml`/`uv.lock`, automatically installing the right Python version (if needed) and creating a virtual environment in `.venv`.
```
$ uv sync
```

### Run

```
$ uv run threepio.py
```

`uv run` automatically uses the project's virtual environment, so there's no need to activate it manually. If you prefer, you can still activate it (`source .venv/bin/activate` on Linux/macOS, `.\.venv\Scripts\Activate.ps1` on Windows) and run `python threepio.py` directly.

## RTL-SDR signal source

Threepio can acquire continuum data from an RTL-SDR dongle instead of the DATAQ ADC. Select **Mode > Device > RTL-SDR** and restart Threepio (the choice persists in `threepio-settings.json`; DATAQ is the default). The driver integrates total power — mean |IQ|² over ~10 ms windows at 2.048 MS/s — and writes the same value to channels A and B.

Setup:

```
$ uv sync --extra sdr
```

This installs `pyrtlsdrlib`, which bundles the [rtl-sdr-blog](https://github.com/rtlsdrblog/rtl-sdr-blog) build of `librtlsdr` (V4 support included) — no system library, `brew install`, or `DYLD_LIBRARY_PATH` needed, on macOS, Linux, or Windows. On Linux, blacklist the DVB kernel driver so it doesn't claim the dongle: `echo 'blacklist dvb_usb_rtl28xxu' | sudo tee /etc/modprobe.d/rtlsdr-blacklist.conf`. Two harmless quirks of the bundled driver: it may print "Kernel driver is active..." on macOS even though the device opens fine, and gain *readback* reports 0.0 dB even though the set gain is applied (verified by noise-floor measurement).

Environment knobs (all optional): `THREEPIO_SDR_FREQ_MHZ` (default 1420.406, the H1 line), `THREEPIO_SDR_RATE` (Hz, default 2.048e6), `THREEPIO_SDR_GAIN` (dB, default 49.6, snapped to the tuner's nearest step), `THREEPIO_SDR_BIAS_TEE=1` to power an LNA, and `THREEPIO_DEVICE=dataq|rtlsdr` to override the menu choice (useful headless). Note: recorded values and the strip chart's "V" readout are scaled linear power (mean |IQ|² × 100), not volts.
