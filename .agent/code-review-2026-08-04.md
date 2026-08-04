# Threepio Code Review — Critical Bugs & Oversights

**Date:** 2026-08-04 · **Commit reviewed:** `fc8a2c8` (main, clean tree)
**Method:** Full-codebase review (app, `_tools/`, `_dialogs/`, tests, data files, recent git history). Every finding below was verified against the current source; numeric claims about `DecCalc` were reproduced by executing the real class against the checked-in `dec-cal.txt`. Two claims surfaced during review did **not** survive verification and are noted at the end.

**Fix status:** C1 and C2 fixed 2026-08-04 (see inline notes). C3–C5 and all High findings open.

---

## Critical — corrupts data or breaks observations

### C1. Declination is computed wrong on this checkout — errors up to 100°

`_tools/deccalc.py:50` — `calculate_declination` assumes the calibration x-values (raw inclinometer readings) are **ascending**:

```python
if fx[0].x <= input_dec <= fx[-1].x:   # "within data" guard
```

The real `dec-cal.txt` is **descending** (68.603 → −7.255), because the inclinometer reading falls as declination rises. The guard becomes `68.603 <= v <= -7.255`, which is never true, so the interpolation loop never executes and *every* input falls into the "below data" branch (`deccalc.py:57-58`), extrapolating the first segment's slope across the whole 125° range.

Reproduced by running the actual class against the actual file — **0 of the 26 calibration points satisfy the guard**:

| raw input | table says | code returns | error |
|---:|---:|---:|---:|
| 68.603 | −25° | +79.4° | +104.4° |
| 51.224 | 0° | −14.3° | −14.3° |
| 35.190 | 40° | −4.5° | −44.5° |
| 26.998 | 60° | +0.5° | −59.5° |
| −7.255 | 100° | +21.5° | −78.5° |

The resulting mapping is not even monotonic. This poisons the dec readout (`threepio.py:212`, `391`), the `dec` column of **every recorded `.md1`/`.md2` file**, and Survey's north/south turnaround logic (`survey.py:22`), which compares the garbage dec against the user's real dec bounds — a Survey will command the telescope in the wrong direction or never find its band.

`DecDialog` naturally produces descending tables (it even *warns only if the table is non-monotonic*, `dec_dialog.py:96-99` / `177`), so this is the normal operating condition, not an exotic one.

**Fix:** make `calculate_declination` order-agnostic — e.g. sort `fx` by x at load time (keeping the (x, y) pairs together), or detect direction and normalize. Add a unit test running the real `dec-cal.txt` shape (descending) through round-trip checks.

**✅ FIXED 2026-08-04:** `load_dec_cal` now sorts the (x, y) pairs by x after building them (`deccalc.py:35-39`), so interpolation is correct for either mounting direction (confirmed design intent: the inclinometer can be mounted both ways; the table must be monotonic). Verified against the real `dec-cal.txt`: all 26 points round-trip exactly (was 0 of 26 in-range). New tests: `tests/deccalc_test.py` (4 tests — both mount directions with real non-uniform calibration values, midpoint interpolation, extrapolation beyond both ends).

### C2. `Comm.FINISH_SWEEP` doesn't exist — crash at the end of a Survey

`_tools/observation.py:160` returns `Comm.FINISH_SWEEP`, but the enum member is `FINISHING_SWEEP` (`_tools/comm.py:17`). Any Survey that reaches `end_time` while the dish is inside the dec band raises `AttributeError` out of `communicate()` → `update_data()` → `tick()`, on every subsequent tick. The handler for `FINISHING_SWEEP` at `threepio.py:307` is unreachable dead code. The final cal/bg phases never run, so the observation ends without calibration data and without the metadata footer.

**Fix:** one-line rename. A single test driving a Survey through its end state would have caught it.

**✅ FIXED 2026-08-04:** renamed to `Comm.FINISHING_SWEEP` at `observation.py:160`; the handler at `threepio.py:307` is now reachable. New tests: `tests/survey_test.py` (3 tests — past-end in-band returns `FINISHING_SWEEP`, past-end out-of-band returns `START_CAL`, in-band mid-data records the point). Note: the related Medium finding — `data_logic` invoked *inside* the `elif` condition with side effects, aborting mid-slew at `end_time` — is still open.

### C3. `start_calibration_1()` clobbers the scheduled start time — WAITING never waits

`_tools/observation.py:204`:

```python
def start_calibration_1(self):
    self.state = State.CAL_1
    self.start_time = time.time()   # overwrites the RA-derived scheduled start
```

`start_time` was carefully computed from the requested RA (`obs_dialog.py:188`, `superclock.py:82-86`). After the clobber:

- `State.WAITING`'s guard `timestamp < self.start_time` (`observation.py:147`) is instantly false, so the "wait for the source" phase is a no-op. Data recording begins right after background ends — i.e. whenever the operator happened to click through the calibration alerts — instead of at the requested RA.
- `start_data()` records the wrong interval (`observation.py:222`), so the progress bar lies.
- `write_meta()`'s `LOCAL START DATE/TIME` (`observation.py:289-290`) reports calibration start, not data start. (`stop()` similarly overwrites `end_time` at `observation.py:239`.)

**Fix:** store cal/bg anchors in their own fields (`cal_start` already exists) and leave `start_time`/`end_time` as the user's schedule.

### C4. One click on "Get Info" wipes the live observation's data files

`_dialogs/obs_dialog.py:104-110`:

```python
def accept(self):
    if self.info:
        self.close()          # <-- no return; falls through
    try:
        self.clear_messages()
        if not self.confirmed:    # info mode leaves confirmed=False (set at :71)
            self.set_observation()
```

The Get Info menu item is only enabled *while an observation is loaded* (`threepio.py:355`) and passes the live `self.obs` (`threepio.py:672`). `set_observation()` then calls `obs.set_name(...)` → `set_files()` → three fresh `MyPrecious`, whose constructor **truncates the files** (`precious.py:19`, `73-75`) — destroying all data recorded so far — and re-derives `start_time`/`end_time` from the widgets against the *current* LST (`obs_dialog.py:188-193`), pushing the live observation's schedule into the future so it silently stops recording.

**Fix:** `return` after `self.close()` in info mode. Separately, `MyPrecious` should not truncate an existing file without an explicit overwrite decision (see H7).

### C5. The midnight-wraparound guard is a no-op — end-before-start records zero data, silently

`_dialogs/obs_dialog.py:183-185`:

```python
if ending_ra < starting_ra:
    ending_ra += 3600 * 24
    self.show_warning("Assuming ending RA is the next day")
```

`ra_to_epoch_time` (`superclock.py:82-86`) computes `(ra_seconds - current_sidereal) % 86400`, so the +86400 cancels exactly — the branch changes nothing. Failure case: current LST 10:00, start RA 11:00, end RA 10:30 → `end_time` lands *before* `start_time`. Validation passes, cal/bg run normally, then `State.DATA` immediately fails `timestamp < self.end_time` (`observation.py:154`) and jumps straight to the closing calibration. The observation "completes" having written **no science data**, with no error.

**Fix:** validate `end_time > start_time` after conversion to epoch times (and reject, not warn). The dialog-side RA arithmetic can be deleted.

---

## High — reliability, threading, hardware robustness

### H1. Most DAQ samples are discarded, and stale points are re-recorded

`threepio.py:211` — a `DataPoint` is only created when the DAQ (100 Hz) **and** the declinometer (10 Hz; 1 Hz at the sensor's factory default) both return fresh data in the same 10 ms tick; otherwise the DAQ sample is thrown away. Meanwhile `update_data` (`threepio.py:237`) writes whatever `current_data_point` still holds, so the same values are recorded repeatedly. Evidence in the repo: the first 90 lines of `data/2024.06.13-19.47_a.md1` are the same triplet (`43124.12 / 34.99 / 9.5311`) repeated 30 times. The code half-acknowledges the problem at `threepio.py:499` (TODO about duplicate stripchart points).

Edge case: `current_data_point` starts as `None` (`threepio.py:162`); if the declinometer is present but never streams, the first recording state hits `point.timestamp` at `observation.py:275` → `AttributeError` inside the timer callback.

**Fix:** cache the last declination and build a DataPoint on every fresh DAQ sample; guard `communicate()` against a `None` point.

### H2. Blocking serial reads on the GUI thread — measured 278 ms stalls; up to ~9 s startup freeze

- `minitars.py:275` — `read_until` is called from `tick()` (GUI thread, 100 Hz). On garbage input with no `\r`, each call burns the full 0.25 s port timeout, and `read_latest` (`minitars.py:220-229`) loops while bytes remain. `dec-debug.log` (checked in) shows back-to-back `read_until returned in 278.6ms` lines — dozens of consecutive discarded frames, i.e. the UI frozen for seconds while DAQ samples pile up (worsening the framing risk in H5).
- `minitars.handshake()` runs synchronously in `Threepio.__init__` (`threepio.py:150`): worst case two 4 s `_streaming()` windows + three 0.3 s command settles ≈ 9 s of frozen, blank window.

**Fix:** move declinometer I/O off the GUI thread (a `QThread` with a queue, or a Qt serial notifier), or at minimum cap `read_until(size=9)` and add a per-tick byte budget / bad-frame backoff.

### H3. `TimerManager` still runs on wall clock — a known, half-fixed defect

`_tools/timer_manager.py:26` uses `time.time()` for scheduling. An NTP step backwards makes `current_time - anchor_time` negative and **every timer stalls** — GUI updates, data recording, and the sidereal resync — until wall clock catches up; anchors are never re-anchored to recover. `.agent/clock-review.md` flagged exactly this; the fix (monotonic time) was applied to `SuperClock` but not to the extracted `TimerManager`. Related: `run_if_appropriate` fires at most once per call regardless of elapsed periods, so delayed ticks silently drop samples rather than catching up; `set_period` (`timer_manager.py:34-37`) is annotated `int` but receives floats (`threepio.py:234`) and compares with `!=` — works, but only accidentally.

**Fix:** `time.monotonic()` in `Timer`, plus a negative-elapsed re-anchor guard.

### H4. Alert dialogs are created and run on a worker thread

`threepio.py:726-745` — `alert()` connects a plain lambda to `QThread.started`, so `AlertWorker.run` executes **in the worker thread**; `alert_aux` (`threepio.py:761-766`) then constructs `AlertDialog` and calls `.show()`/`.exec()` there. Qt requires all widget creation/painting on the GUI thread — this is undefined behavior that happens to mostly work. Compounding it:

- `self.worker` (`threepio.py:729`) is overwritten by each new alert while the previous worker may still be running, and the `started` lambda resolves `self.worker` at *signal* time — overlapping alerts can run the wrong worker.
- `alert_aux` calls `self.log()` from the worker thread, mutating `message_log` while `update_console()` reads it on the GUI thread.
- Alert callbacks assert on shared state they don't own (`threepio.py:263`, `274`) after arbitrary operator delay.

**Fix:** keep dialogs on the main thread (queue alerts and show them via a signal/slot with a `QueuedConnection`); if sequential blocking flow is needed, model it as a state machine, not a thread.

### H5. Serial-layer robustness gaps

- **Port-open failures are uncaught:** `Tars`/`MiniTars` construction (`threepio.py:143-145`) has no try/except; a busy port or permissions error kills the app with a traceback at launch. A **mid-run disconnect** raises `SerialException` out of `tick()` on every tick; there is no reconnect or degrade path.
- **`MySerial._reconfigure_port` swallows `SerialException`** (`myserial.py:9-10`), so a port can "open" successfully at the wrong baudrate. `minitars.py:53-57` documents working around this, but the constructor path goes through the same swallowing override.
- **DAQ framing depends on a single flush:** channel A/B identity relies entirely on the `reset_input_buffer()` at `tars.py:171` (the `412ba86` echo fix) holding for the whole session. `buffer_read` (`tars.py:178-200`) has no sync markers and no recovery: one dropped/extra byte (USB hiccup, buffer overrun during the stalls in H2) permanently swaps channels and corrupts every subsequent sample, undetectably. `Tars.stop()`/`reset()` — the only things that re-flush — have zero call sites.
- **`/dev/serial0` unconditionally beats the FTDI adapter** (`tars.py:53-54`, `minitars.py:37-38`, from commit `1a70bf6`): `/dev/serial0` exists on essentially every Raspberry Pi, so on a Pi with the sensor on USB, discovery hands back a dead (or console-noisy) UART unless `THREEPIO_DEC_PORT` is set. `tests/discovery_test.py` locks this in rather than catching it.
- **A missing DataQ is only logged, not alerted** (`tars.py:77`): the app silently simulates telescope data that looks identical downstream. The declinometer gets a modal alert (`threepio.py:149`); the science channels deserve at least the same.
- **No shutdown path:** `closeEvent` (`threepio.py:775-791`) never sends `stop` to the DAQ (it keeps streaming), never closes either port, and never stops the tick timer.

### H6. Sidereal-day wraparound breaks the strip chart and file timestamps

- `DataPoint.timestamp` is sidereal seconds-of-day; it wraps 86399→0 mid-observation with no day counter, and the 60 s `resync_from_astropy` (`threepio.py:185`) applies corrections as instantaneous jumps — with no magnitude check or logging (required by `.agent/clock-refactor-plan.md:147`, not implemented) — so recorded timestamps can also step slightly backwards.
- Strip chart pruning (`threepio.py:520-528`) compares `at(1).y() < oldest_y`. After LST midnight, `oldest_y` restarts near 0 while buffered points sit near 86400, so the condition stays false for the next ~24 h: pre-wrap points are never pruned, the series grows unboundedly, and `calculate_stripchart_voltage_range()` (`threepio.py:602-607`) — an O(n) scan of every point, already run on **every tick** — degrades progressively. Overnight runs get slower and leak memory.
- `resync_from_astropy` → astropy `sidereal_time("apparent")` can trigger an IERS table download — network I/O on the GUI thread, at startup and every 60 s; on an offline machine an exception would escape into `tick()`.

**Fix:** unwrap timestamps monotonically (track a day counter), prune by point count or age delta, cache the voltage range incrementally, precompute/pin IERS data, and slew (or at least log) large resync corrections.

### H7. Data-file integrity hazards

- **Filename collision silently destroys data:** the default name slug has 1-minute resolution (`superclock.py:40-41`), and `MyPrecious.__file_clear()` truncates on construction (`precious.py:19`, `73-75`) with no existence check anywhere. Two observations in the same minute — or any reused custom name — wipe the earlier files.
- **Quit mid-observation loses the footer:** there is no abort path and `closeEvent` never calls `obs.stop()`, so interrupted runs end with no metadata and no terminating `*` (see the 0-byte `2026.05.12-15.48_*` files). Samples survive only because every value is flushed immediately.
- **Metadata is written at the *end* of the file** (`write_meta` called from `stop()`, `observation.py:243`) and only on a clean finish — consumers must parse from both ends and cannot rely on it existing.
- **Silent unit change:** commit `412ba86` removed the `5 +` offset in `tars.buffer_read` (physically correct for the bipolar ±5 V range), but files recorded before/after differ by +5 V with nothing in the format to distinguish them. Anyone reducing ERIRA data across that boundary needs to know.
- **`_comp` files are stillborn:** `self.composite` is set `False` at `observation.py:43` and never set anywhere else, so every `_comp` file is created, truncated, and left empty forever (all `data/*_comp.*` are 0 bytes).

---

## Medium

- **`DecCalc` robustness** (`deccalc.py`): duplicate adjacent x-values in the matched segment → `ZeroDivisionError` inside `tick()` (a strictly monotonic table — now a confirmed precondition, see C1 — cannot contain duplicates, but nothing *enforces* monotonicity at load time; `DecDialog` only warns). A short/corrupt `dec-cal.txt` is silently `zip`-truncated (`deccalc.py:34`); an empty one → `IndexError` on first use. The `FileNotFoundError` fallback (`deccalc.py:42`) builds 13 x-values against 26 y-values, then re-raises — `threepio.py:174-177` alerts and keeps running on that mismatched half-table. `dec_calibration()` (`threepio.py:682`) calls `load_dec_cal()` *uncaught* — cancelling the dec dialog with no `dec-cal.txt` on disk raises out of the menu slot.
- **`assert` used for validation** (`observation.py:98,101`): `assert min_dec` rejects declination **0°** (falsy float) with an `AssertionError` that `accept()`'s `except ValueError` doesn't catch; all such asserts vanish under `python -O`. Same pattern at `threepio.py:404/434` (`AssertionError` as control flow) and `observation.py:264-266`.
- **Dec input truncated to int** (`obs_dialog.py:204-205`): `int(float(text))` silently turns 40.75° into 40°; combined with the assert above, any entry in (−1, 1) becomes 0 and crashes. No range check against the telescope's −25…100° limits.
- **Survey off-by-ones** (`survey.py:21-36`): on re-entering the band, `data_logic` returns `END_SEND_TEL` *before* writing, dropping the first in-band sample of every sweep; `sweep_number` starts at 1 and increments on first entry, so the GUI shows "2" during sweep 1. In `observation.py:157-159`, `data_logic(...)` is invoked *inside an `elif` condition* — its side effects (file writes, sweep counting) happen while merely being tested, and when it returns `SEND_TEL_*` at `end_time` the condition is false, aborting to `START_CAL` mid-slew and swallowing the command (this is the same line as bug C2).
- **Console/log edge cases** (`threepio.py:716-724`): `reduce` with no initializer → `TypeError` on an empty `message_log`; `floor(height/14) == 0` makes `[-0:]` show the *entire* log. Unconditional `print()` on every log line (`threepio.py:713`) and every beep (`threepio.py:773`).
- **Unbounded memory:** `self.data` grows one `DataPoint` per tick forever (`threepio.py:219`) — ~360k objects/hour — but is only ever read as `data[-1]`.
- **Per-tick disk and decode churn:** `update_dec_view()` reloads `dish.png`/`base.png` from disk at 100 Hz (`threepio.py:442,450`); `MyPrecious.MAX_BUFFER_SIZE = 0` means a full `open()`/`close()` per *value* — ~3 per point per file at up to 10 Hz (`precious.py:9,57-65`); `__del__` doing I/O (`precious.py:21-23`) relies on GC ordering at shutdown.
- **Import-time side effect:** `minitars.py:15` runs `get_dec_logger()` at module scope — merely importing `tools` creates/appends `dec-debug.log` in the CWD (tests included), with a flush per record and no rotation.
- **Circular-import fragility:** `_tools/observation.py:5` imports `from tools import ...` while `tools/__init__.py` imports `_tools.observation`; it only works because of the current name ordering in `tools/__init__.py`. Reordering that file breaks the app. Several modules bypass the facade inconsistently.
- **Swallowed exceptions:** the *entire* 50-line `update_stripchart` body is wrapped in `except IndexError: pass` (`threepio.py:548`) — an `IndexError` from anywhere inside (including `DecCalc`) is silently treated as "no data yet"; `except Exception` around `complete_calibration` (`dec_dialog.py:145-147`); `except AttributeError: pass` at `threepio.py:665,710`.
- **`DecDialog.validate_data`** (`dec_dialog.py:180`): `if i < 2: continue` skips `None`-checks for the first two entries; `assert sorted(x) or sorted(x, reverse=True)` (`dec_dialog.py:177`) is tautological — it checks nothing about ordering.

## Low / hygiene

- **CWD-relative paths everywhere:** `stylesheet.qss` (`threepio.py:56`), `assets/*` (`threepio.py:131,442,450,799`), `dec-cal.txt` (`deccalc.py:37`), `./data/` (`precious.py:15`), `dec-debug.log` (`declog.py`). The app only runs from the repo root.
- **Duplicated code:** the `should_beep` block appears twice verbatim (`threepio.py:316-320`); `minitars.discovery()` duplicates the dec half of `tars.discovery()` and is unused by the app.
- **Dead code:** `Comm.NEXT` handler (`threepio.py:311` — nothing returns it), `GUI_UPDATE_PERIOD`/`STRIPCHART_PERIOD` (`threepio.py:39-40` — never referenced; the real cadences are hardcoded), `tars.convert()` (`tars.py:59` — stale duplicate of the scaling), `spectrum.set_data_time` (never called; `data_end` ignored), legacy tuple unwrapping (`threepio.py:504-508`), `SuperClock.get_time_until` (`superclock.py:44-45` — returns time *since*, sign-inverted vs. its name), `calibration_epoch_time`/`propagation_anchor_epoch_time` written but never read, `acquiring` flags written but never read.
- **Stale docs/tooling:** README says PyQt5; the code is PySide6. `requirements.txt` is empty. `layouts/makefile` still invokes `pyuic5`. `.agent/AGENTS.md` predates the control-panel refactor its own plan said to record. The 4 MB `time-experiment` artifact is still checked into the repo root.
- `observation.py:65-71`: `start_time`/`end_time` assigned twice in `__init__`; `threepio.py:243` mixes `!=` and `is` for enum comparison.

---

## Test coverage

`pytest` is not installed in `.venv` (`python -m pytest` → module not found), so nothing runs the suite; the last recorded run (`.pytest_cache`) has `tests/observation_test.py::test1` **failing**.

- `tests/observation_test.py` is broken and vacuous: it calls `obs.set_ra(...)`, which doesn't exist (renamed to `set_start_and_end_times`); `set_dec(60, 30)` violates max ≥ min and would raise anyway; the body is `print()`-only with **zero assertions**. Running it also writes real files into `./data/` (the 0-byte `scan_a.md1`/`survey_a.md2`/`spectrum_a.md1` are test droppings).
- `tests/clock_test.py` (4 tests) covers `SuperClock` reasonably, though `test_sidereal_wraparound` only asserts `0 <= v < 86400`, which the implementation's `% 86400` guarantees trivially.
- `tests/discovery_test.py` locks in the `/dev/serial0` precedence (see H5) rather than questioning it.

**Highest-value missing tests** (each would have caught a Critical above): ~~`DecCalc.calculate_declination` against a descending table (C1)~~ — added 2026-08-04 as `tests/deccalc_test.py`; driving the `Observation` state machine end-to-end through every `Comm` verb (C3; the Survey end-state slice of this is now covered by `tests/survey_test.py`); `ObsDialog.set_observation` RA→epoch conversion including end-before-start (C5); `MyPrecious` truncation semantics (C4/H7); `Survey.data_logic` band-crossing (Medium); `Timer.run_if_appropriate` under clock steps (H3).

## Status vs. prior `.agent/` reviews

- `clock-review.md` item 2 (non-monotonic scheduling clock): fixed in `SuperClock`, **still open in `TimerManager`** (H3).
- `clock-refactor-plan.md:147` (log large resync corrections): **not implemented** (H6).
- `strip-chart-upgrades.md:101` (auto-range over visible points only): holds only while pruning works, which the wraparound bug (H6) breaks.
- `AGENTS.md` "last updated" predates the control-panel refactor.

## Claims checked and rejected during this review

- An alleged `IndexError` at `deccalc.py:52` (`fx[i+1]` overrun) is **unreachable**: whenever the range guard passes, a crossing segment must exist (discrete intermediate-value argument), so the loop always returns before overrunning. Verified by construction and by testing non-monotonic tables.
- `MyPrecious` "leaks file handles" — false: it opens and closes per write; the real problems are the churn and truncate-on-construct (H7).
