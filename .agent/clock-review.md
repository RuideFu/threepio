# Clock review

## Current implementation summary

The current clock is a hybrid design:

- `SuperClock.__init__()` computes Green Bank local sidereal time once with `astropy`.
- `calibrate_sidereal_time()` stores that sidereal value plus the current Unix time as an anchor.
- `get_sidereal_seconds()` advances sidereal time by applying a fixed sidereal-rate multiplier to elapsed wall-clock time.
- The main loop uses that derived sidereal value as the RA timestamp for samples, the GUI display, and observation scheduling.

In other words, the software is **already very close to an “initialize once, then extrapolate” design**. It does not recompute LST from astronomy libraries on every tick.

## What is good

- Runtime cost is low. The hot path avoids repeated `astropy` calls.
- The model is easy to reason about for short sessions: `sidereal = anchor + rate * elapsed`.
- Manual RA calibration cleanly re-anchors the model.
- Using a continuous sidereal counter is convenient for strip-chart plotting and scheduling math.

## Main concerns

### 1. The clock mixes two unrelated responsibilities

`SuperClock` is both:

- a sidereal/RA time model, and
- a general-purpose periodic task scheduler (`Timer`, `run_timers`, `add_timer`).

That coupling makes the clock harder to test and harder to evolve. A timing bug and a sidereal bug currently live in the same class.

### 2. Elapsed time is based on `time.time()`, not a mo
notonic clock

The sidereal model uses:

- calibration anchor from `time.time()`
- elapsed time from `time.time() - starting_epoch_time`

That means the derived RA/LST can jump if the OS clock is adjusted by NTP, the system wakes from sleep oddly, or the operator changes system time. For interval tracking, `time.monotonic()` would be safer.

### 3. Naming/behavior around anchors is confusing

`reset_anchor_time()` updates `self.anchor_time`, but the sidereal computation uses `starting_epoch_time`, not `anchor_time`.

So for the sidereal model, `reset_anchor_time()` does not actually re-anchor the clock. It only resets timer anchors. That is likely to confuse future maintenance, especially because the name sounds like it affects the astronomical clock too.

### 4. There is no periodic truth-source correction

After initialization or manual RA calibration, sidereal time is purely extrapolated with a constant multiplier. That is usually fine for short runs, but it means there is no automatic recovery from:

- wall-clock corrections,
- a bad initial calibration,
- long-running drift,
- location/config changes.

### 5. Debug output is still inside clock-adjacent paths

There are unconditional prints in calibration/timer code and a recurring append to `time-experiment` from `update_gui()`. That makes the timing path noisier and less production-ready than it should be.

## Comparison with alternatives

## A. Current approach: initialize once, then extrapolate

This is effectively what the code does today.

### Pros

- Very cheap during acquisition.
- Deterministic and simple.
- Good fit when data acquisition runs faster than the GUI and astronomy libraries should stay off the hot path.

### Cons

- Sensitive to wall-clock jumps if based on `time.time()`.
- Needs explicit recalibration or periodic correction for longer sessions.
- Can give a false sense that the displayed LST is still tied to a live astronomy calculation when it is not.

## B. Compute LST/RA only during initialization

If this means “compute one startup LST and use simple elapsed-time arithmetic after that,” then this is not really an alternative; it is the current design.

If this means “precompute all needed RA/LST values for the whole session during startup,” that is usually not a good fit here:

- session duration is not fixed,
- manual RA calibration exists,
- observation timing can change interactively,
- system clock adjustments would invalidate the precomputed table.

So a pure precomputation model adds complexity without much gain over the current anchor-plus-rate method.

## C. Recompute LST from `astropy` whenever needed

This is the opposite end of the spectrum.

### Pros

- Always tied to the current UTC time and site location.
- Easier to reason about as the authoritative value.
- More robust to clock changes and long runs.

### Cons

- More overhead in the hot path.
- Pulls astronomy-library work into code that currently runs frequently.
- Adds more moving parts around time scale/location handling.

For this application, doing this on every 100 Hz tick would likely be unnecessary.

## D. Recommended middle ground

The best tradeoff is usually:

1. compute LST once from `astropy` at startup or manual calibration,
2. advance it using elapsed **monotonic** time,
3. optionally re-anchor from `astropy` on a slow cadence (for example once per minute, on resume, or after explicit operator actions),
4. keep high-rate acquisition code on the lightweight extrapolated path.

That preserves performance while making the model more robust.

## Recommended changes

### High priority

1. Split `SuperClock` into two concepts:
   - a sidereal clock / RA model
   - a scheduler / timer manager
2. Use `time.monotonic()` for elapsed-time progression after calibration.
3. Rename anchor-related fields/methods so it is obvious which ones affect astronomical time versus GUI timers.
4. Remove unconditional debug prints and the `time-experiment` append from the normal update path.

### Medium priority

1. Add a slow re-sync path from `astropy` for robustness.
2. Add tests for:
   - calibration wraparound at 24h,
   - sidereal progression rate,
   - RA-to-epoch conversion in the observation dialog,
   - behavior across manual recalibration.

## Bottom line

The current clock architecture is reasonable for a desktop acquisition app, especially because it keeps astronomy calculations out of the fast loop. The biggest issue is not the basic “initialize and extrapolate” idea; it is the lack of separation between scheduler logic and sidereal logic, plus the use of non-monotonic wall-clock time as the propagation source.

So compared with an alternative that computes LST/RA during initialization, the main conclusion is:

- **the code already mostly does that**, and
- the next improvement should be **making that design more explicit and more robust**, not moving more computation into startup.
