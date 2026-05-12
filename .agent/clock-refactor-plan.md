# Clock Refactor Plan

## Objective

Implement the clock changes recommended in `.agent/clock-review.md` while keeping the refactor focused and compatible with the current `threepio` desktop workflow:

1. split `SuperClock` into a sidereal/RA model and a scheduler/timer manager,
2. switch elapsed-time propagation to `time.monotonic()`,
3. rename anchor-related state so astronomical anchors and timer anchors are clearly separated,
4. remove unconditional debug output and the `time-experiment` write from the normal update path,
5. add a slow `astropy` re-sync path for robustness without moving astronomy work into the hot loop.

## Constraints from `.agent/AGENTS.md`

- Keep the change focused and minimal.
- Prefer fixing root causes over adding defensive wrappers.
- Preserve current serial/data flow and runtime file conventions.
- Avoid UI/layout churn unless the task actually changes widgets; no `.ui` regeneration is expected for this refactor.
- Favor model-level tests over hardware- or full-GUI-driven validation.
- Use dependencies from `pyproject.toml`; do not reintroduce `requirements.txt`-based workflow.

## Design goals

- Preserve the fast acquisition path: no `astropy` call on the 100 Hz `tick()`.
- Make time semantics explicit: wall-clock timestamps for file/observation timing, monotonic elapsed time for propagation, sidereal seconds for RA/LST display and sample timestamps.
- Preserve manual RA calibration semantics while allowing background truth-source correction.
- Minimize call-site churn by changing a small number of modules and keeping public APIs narrow.

## Proposed architecture

### 1. Keep `SuperClock` as the sidereal model

To avoid a broad rename across the codebase, keep the `SuperClock` class name but reduce its responsibility to sidereal/RA tracking only.

Responsibilities after refactor:

- site/location configuration,
- current sidereal time / RA derivation,
- manual calibration handling,
- RA/LST conversion helpers for other modules,
- slow re-sync to `astropy`.

Responsibilities removed from `SuperClock`:

- timer storage,
- periodic callback scheduling,
- timer anchor reset behavior.

### 2. Introduce a dedicated scheduler

Add a new timer manager, preferably in a new module such as `_tools/timer_manager.py`.

Suggested responsibilities:

- own `Timer` objects,
- add/cancel timers,
- run due timers,
- reset timer anchors only,
- keep current timer semantics intact for `update_gui()` and `update_data()`.

Suggested migration target in `threepio.py`:

- `self.clock = SuperClock()`
- `self.scheduler = TimerManager()`
- replace:
  - `self.clock.add_timer(...)` -> `self.scheduler.add_timer(...)`
  - `self.clock.run_timers()` -> `self.scheduler.run_timers()`
  - `self.clock.reset_anchor_time()` -> `self.scheduler.reset_timer_anchors()`

## Time model redesign

### 1. Separate wall-clock, monotonic, and sidereal anchors

Replace the current overloaded anchor fields with explicitly named state.

Suggested sidereal state:

- `calibration_epoch_time`: Unix epoch time associated with the current calibration reference,
- `calibration_sidereal_seconds`: sidereal seconds associated with that calibration reference,
- `propagation_anchor_monotonic`: monotonic timestamp used for elapsed propagation,
- `propagation_anchor_epoch_time`: Unix epoch corresponding to the current propagation anchor,
- `propagation_anchor_sidereal_seconds`: sidereal seconds at the propagation anchor,
- `manual_sidereal_offset_seconds`: operator-entered correction relative to astronomical truth.

Key rule:

- use `time.monotonic()` for elapsed propagation,
- use `time.time()` only when absolute epoch timestamps are needed for observation scheduling, files, and UI timestamps.

### 2. Preserve manual calibration across re-sync

Do **not** let slow `astropy` re-sync overwrite operator-entered calibration semantics.

Recommended behavior:

- compute astronomical sidereal truth from `astropy`,
- treat manual RA calibration as an offset from that truth source,
- during slow re-sync, refresh the astronomical anchor but preserve `manual_sidereal_offset_seconds`.

This avoids a bad interaction where a background re-sync silently undoes manual RA calibration.

### 3. Centralize RA/LST conversion helpers

Move sidereal conversion math behind `SuperClock` methods rather than exposing raw anchor fields to dialogs.

Suggested helpers:

- `get_sidereal_seconds()`
- `get_formatted_sidereal_time()`
- `calibrate_sidereal_time(...)`
- `ra_to_epoch_time(ra_seconds)`
- `epoch_time_to_sidereal_seconds(epoch_time)` if needed
- `get_calibration_reference()` only if a stable snapshot object is required

Goal:

- `_dialogs/obs_dialog.py` should stop reconstructing epoch conversion from raw `starting_*` fields.
- scheduling math should be defined in one place so later re-sync changes do not leak across modules.

## Slow `astropy` re-sync plan

### Policy

Use a low-frequency correction path instead of recomputing LST in the hot loop.

Recommended cadence:

- every 60 seconds as a starting default,
- optionally also on explicit events such as app startup completion or manual RA calibration completion.

### Implementation shape

1. Add an internal method that computes Green Bank sidereal seconds from `astropy` for the current epoch.
2. Add a method such as `resync_from_astropy()` that:
   - gets the current Unix time,
   - gets the current monotonic time,
   - computes astronomical sidereal seconds,
   - reapplies any manual offset,
   - updates the propagation anchor fields.
3. Register the re-sync on the scheduler, not in `tick()`.

### Safety requirements

- Re-sync must not mutate already computed observation `start_time` / `end_time`.
- Re-sync must preserve manual calibration offset.
- Re-sync must not write files or print on success.
- If a large correction is applied, log through the existing app logging path rather than using `print()`.

## Planned file changes

### Primary code paths

- `_tools/superclock.py`
  - remove scheduler ownership,
  - rename sidereal anchor fields and methods,
  - add monotonic propagation,
  - add slow re-sync support,
  - add centralized conversion helpers.
- new `_tools/timer_manager.py`
  - move `Timer` here,
  - add `TimerManager`.
- `tools/__init__.py`
  - export the new scheduler class.
- `threepio.py`
  - instantiate `TimerManager`,
  - route periodic work through the scheduler,
  - replace timer-anchor reset calls,
  - remove `time-experiment` logging from `update_gui()`.
- `_dialogs/obs_dialog.py`
  - replace direct raw-anchor math with clock conversion helpers.
- `_dialogs/ra_dialog.py`
  - keep UI behavior but ensure calibration flows through the updated sidereal API.

### Tests

- add a focused clock test module, preferably `tests/clock_test.py` or similar.
- keep tests import-level/model-level only; do not depend on connected hardware or a launched GUI.

## Step-by-step implementation sequence

### Phase 1: Extract scheduler responsibility

1. Create `TimerManager` and move timer-specific logic out of `SuperClock`.
2. Update `threepio.py` to own a scheduler instance separately from the clock.
3. Replace old timer-reset naming with scheduler-specific naming.

Deliverable:

- `SuperClock` no longer owns `timers` or timer anchor reset behavior.

### Phase 2: Make sidereal state explicit

1. Rename sidereal anchor fields to distinguish calibration reference from propagation reference.
2. Replace elapsed propagation with `time.monotonic()`.
3. Keep `time.time()` access only where absolute timestamps are actually required.

Deliverable:

- sidereal progression is monotonic-clock-based and field names describe intent.

### Phase 3: Centralize conversion logic

1. Add RA/LST conversion helpers on `SuperClock`.
2. Update `_dialogs/obs_dialog.py` to call those helpers instead of reading raw anchor state.
3. Keep behavior unchanged from the user’s perspective.

Deliverable:

- observation scheduling no longer depends on internal clock field layout.

### Phase 4: Add slow `astropy` re-sync

1. Add the astronomical truth-source method.
2. Add a low-frequency re-sync method that preserves manual offset.
3. Schedule it with `TimerManager`.
4. Optionally gate large corrections behind app logging so operators can see meaningful jumps.

Deliverable:

- the live sidereal clock self-corrects slowly without affecting the hot loop.

### Phase 5: Remove debug noise and stabilize behavior

1. Remove unconditional `print()` statements from clock/timer paths.
2. Remove the `time-experiment` append in `threepio.py`.
3. Ensure any remaining diagnostics go through structured app logging or are explicitly debug-only.

Deliverable:

- no unconditional debug I/O remains in the normal timing path.

### Phase 6: Add targeted tests

1. Test sidereal wraparound at 24 hours.
2. Test monotonic progression math from a fixed anchor.
3. Test manual calibration behavior.
4. Test slow re-sync preserving manual offset.
5. Test RA-to-epoch conversion used by observation setup.

Deliverable:

- targeted regression coverage for the new clock behavior.

## Acceptance criteria

- `SuperClock` is only responsible for sidereal/RA behavior.
- Timer management lives outside `SuperClock`.
- Live sidereal progression uses `time.monotonic()`.
- Method/field names clearly distinguish sidereal calibration/progression state from scheduler state.
- No unconditional `print()` calls remain in the refactored clock path.
- `update_gui()` no longer writes `time-experiment`.
- Slow `astropy` re-sync exists and runs off the scheduler.
- Manual RA calibration survives background re-sync.
- Observation dialog conversion no longer depends on raw internal anchor fields.
- Targeted automated tests cover the new behavior.

## Validation plan

### Targeted checks

- run the focused clock/observation tests first,
- then run `pytest -q` if the environment has the declared dependencies installed.

### Manual smoke checks

- start the app,
- confirm RA display advances continuously,
- perform manual RA calibration and confirm the display updates correctly,
- leave the app running long enough to cross at least one re-sync interval,
- verify no debug file or console spam is produced by normal operation.

## Risks and mitigations

### Risk: background re-sync changes user expectations

Mitigation:

- preserve manual offset across re-sync,
- keep observation `start_time` / `end_time` as fixed epoch values once computed,
- log only meaningful corrections.

### Risk: broad API churn in Qt code

Mitigation:

- keep `SuperClock` as the sidereal class name,
- centralize new behavior behind a small compatibility-oriented API,
- change only the modules that currently depend on raw clock internals.

### Risk: test fragility around real time

Mitigation:

- structure clock methods so time sources can be injected or patched in tests,
- validate calculations with deterministic anchors rather than sleeping in tests.
