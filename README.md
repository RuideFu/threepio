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
