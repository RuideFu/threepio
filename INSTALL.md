# Installing Threepio on Raspberry Pi OS

These instructions set up Threepio as a launchable desktop app on a Raspberry Pi,
running from a git checkout managed by [`uv`](https://docs.astral.sh/uv/). Updates
are then just `git pull` — no rebuilt binaries to distribute.

## Requirements

- **Raspberry Pi 4 or 5** (2 GB RAM or more recommended)
- **Raspberry Pi OS (64-bit), Bookworm or newer, Desktop image**

The 64-bit part is mandatory: PySide6 (the Qt GUI library) does not publish
32-bit ARM packages. Verify before going further:

```
$ uname -m
aarch64
```

If this prints `armv7l`, the Pi is running a 32-bit OS and must be reflashed
with the 64-bit image from Raspberry Pi Imager.

## 1. Install system packages

Most of what Threepio needs ships inside its Python packages, but Qt relies on
a few system libraries that are not always present on Raspberry Pi OS:

```
$ sudo apt update
$ sudo apt install -y git curl libxcb-cursor0 libxkbcommon-x11-0 libegl1
```

## 2. Install `uv`

```
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then close and reopen the terminal (or run `source ~/.local/bin/env`) so that
`uv` is on your `PATH`. Verify with `uv --version`.

## 3. Clone and install Threepio

```
$ cd ~
$ git clone https://github.com/finnjames/threepio.git
$ cd threepio
$ uv sync
```

`uv sync` downloads a self-contained Python 3.13 build for the Pi and installs
all dependencies into `.venv/`. No system Python is used or modified. The first
run takes a few minutes on a Pi; PySide6 is a large download.

## 4. Serial port permissions

Threepio talks to the telescope hardware over serial. On Raspberry Pi OS,
serial devices belong to the `dialout` group:

```
$ sudo usermod -aG dialout $USER
```

**Log out and back in** (or reboot) for the group change to take effect.

To verify the hardware is visible, plug it in and check for devices:

```
$ ls /dev/ttyUSB* /dev/ttyACM*
```

## 5. Test run

```
$ cd ~/threepio
$ uv run threepio.py
```

Threepio loads its stylesheet, sounds, and images relative to the working
directory, so **always launch it from the repository directory**. The desktop
launcher below handles this automatically.

## 6. Desktop launcher

Create `~/.local/share/applications/threepio.desktop` with the following
content, replacing `<user>` with your username in all three paths:

```ini
[Desktop Entry]
Type=Application
Name=Threepio
Comment=40-foot telescope data acquisition
Exec=/home/<user>/.local/bin/uv run threepio.py
Path=/home/<user>/threepio
Icon=/home/<user>/threepio/assets/robot.png
Terminal=false
Categories=Science;
```

Threepio now appears in the applications menu. For an icon on the desktop as
well:

```
$ cp ~/.local/share/applications/threepio.desktop ~/Desktop/
$ chmod +x ~/Desktop/threepio.desktop
```

The `Path=` line is what makes the launcher work — it starts Threepio inside
the repository so all assets resolve. `Exec=` uses the full path to `uv`
because desktop launchers do not read your shell profile.

## 7. Optional: start Threepio on boot

Create `~/.config/autostart/threepio.desktop` with the same content as the
launcher above. Threepio will then open automatically when the desktop loads.

## Where data is stored

Threepio writes everything inside the repository directory:

- **Observation files** (`.md1`): `~/threepio/data/`
- **Declination calibration**: `~/threepio/dec-cal.txt` (with backup
  `dec-cal-backup.txt`)
- **Debug log**: `~/threepio/dec-debug.log`

These files are ignored by git, so they survive updates and never conflict
with `git pull`. If observations must outlive the Pi's SD card, copy or back
up `~/threepio/data/` — nothing is stored anywhere else on the system.

## Updating

```
$ cd ~/threepio
$ git pull
$ uv sync
```

## Troubleshooting

**The window never appears / "could not load the Qt platform plugin
'xcb'"** — a system library is missing. Re-run the `apt install` line from
step 1. If it persists, run from a terminal with `QT_DEBUG_PLUGINS=1
uv run threepio.py` to see which library Qt is looking for.

**No serial ports found** — confirm the device shows up in `ls /dev/ttyUSB*
/dev/ttyACM*`, and that `groups` lists `dialout`. If you added the group in
step 4 without logging out, it has not taken effect yet.

**`uv: command not found`** — the installer puts `uv` in `~/.local/bin`,
which joins your `PATH` on next login. Either reopen the terminal or use the
full path `~/.local/bin/uv`.

**No beep sounds** — check the audio output device in the desktop's volume
control (right-click the speaker icon in the taskbar); HDMI monitors without
speakers are a common culprit.
