# Strip Chart Upgrades Plan

## Objective

Add the requested strip chart improvements while keeping the change focused and aligned with the current `threepio` Qt desktop architecture:

1. add a control to enable or disable dynamic strip chart scaling,
2. keep dynamic scaling shared across both plotted channels so they remain directly comparable,
3. add a manual maximum-voltage slider next to the dynamic-scale control,
4. add optional grid lines with a toggle to show or hide them.

## Constraints from `.agent/AGENTS.md`

- Keep the change focused and minimal.
- Prefer fixing root causes over adding defensive wrappers.
- Preserve current serial/data flow and runtime file conventions.
- Because this changes widget structure, update the editable `.ui` source and keep the generated `*_ui.py` module in sync.
- Favor targeted validation over full hardware-driven testing.

## Current state

### Chart setup

- `threepio.py` initializes two `QLineSeries` objects and a `QChart` during window startup.
- `initialize_stripchart()` currently hides the legend and installs the chart view, but does not establish a persistent voltage axis.
- `update_stripchart()` appends both channel series, prunes old points, then recreates chart/axis attachments during each refresh.

### Strip chart controls

- `layouts/threepio.ui` currently provides:
  - the strip chart speed slider,
  - `Toggle Channels`,
  - `Clear Chart`.
- There is no UI state for dynamic scaling, manual voltage limits, or grid visibility.

## Working assumptions

- Interpret “make sure both axis are scale the same” as: when dynamic scaling is enabled, compute one shared voltage range from both channel series and apply that single range to the shared voltage axis so channel A and channel B stay visually comparable.
- Keep the existing strip chart orientation unchanged: voltage on the horizontal axis and time/right-ascension progression on the vertical axis.
- Keep the existing time-window behavior driven by `stripchart_display_seconds`; this plan only changes voltage scaling and chart presentation.

## Files likely to change

- `threepio.py`
- `layouts/threepio.ui`
- `layouts/threepio_ui.py`
- `tests/` only if the refactor extracts range-calculation helpers that can be validated without launching the GUI

## Implementation plan

### 1. Stabilize strip chart axis ownership

Refactor the strip chart so axes are created once and updated in place instead of being recreated on every refresh.

- Add persistent chart-axis members during initialization, such as:
  - `self.axis_x` for voltage,
  - `self.axis_y` for time / sidereal seconds.
- Move axis creation and series attachment into `initialize_stripchart()`.
- Add a helper for axis configuration so the update loop only changes ranges and visibility.
- Keep the current legend-hidden behavior and existing channel colors.

This is the key enabling change because manual scaling, dynamic scaling, and grid toggling all become simpler and more reliable once the chart owns stable axes.

### 2. Extend the strip chart control area

Update `layouts/threepio.ui` so the strip chart control group includes the new controls without disrupting the existing speed slider and buttons.

- Add a checkable control for dynamic scaling, preferably labeled `Dynamic Scale`.
- Place a horizontal maximum-voltage slider immediately next to that control, plus a compact value label so the current fixed limit is visible.
- Add a checkable control for grid lines, preferably labeled `Grid`.
- Keep `Toggle Channels` and `Clear Chart` in place unless layout pressure makes a small rearrangement necessary.
- Regenerate or synchronize `layouts/threepio_ui.py` after the `.ui` change.

### 3. Add strip chart presentation state

Introduce explicit state on the main window so the chart behavior is controlled by named values instead of implicit widget reads scattered through the refresh path.

Suggested state:

- `stripchart_dynamic_scale_enabled`
- `stripchart_grid_enabled`
- `stripchart_manual_max_voltage`
- optionally `stripchart_auto_max_voltage` if the computed range is cached for display/debugging

Suggested slots/helpers:

- `toggle_stripchart_dynamic_scale()`
- `update_stripchart_max_voltage()`
- `toggle_stripchart_grid()`
- `update_stripchart_axes()`
- `calculate_stripchart_voltage_range()`

### 4. Implement shared dynamic scaling

Implement voltage-axis range calculation around a single shared rule for both channels.

- In dynamic mode, inspect the visible strip chart data for both channel series and compute one shared maximum absolute voltage.
- Apply that value symmetrically around zero, e.g. `[-max_voltage, +max_voltage]`, so positive and negative excursions remain comparable.
- Add a minimum floor so an empty or flat signal never collapses the axis to zero width.
- Base the automatic range on visible/recent points only, not the entire run history, so the chart responds to the active time window.

This shared-range approach is the practical interpretation of “scale both axis the same” in the current chart design because both channel traces already share one voltage axis.

### 5. Implement fixed manual scaling

Use the new slider to control the maximum displayed voltage whenever dynamic scaling is disabled.

- Map the slider range to a useful engineering voltage range for this application.
- Update the label/readout whenever the slider moves.
- In manual mode, set the voltage axis to the slider-driven symmetric range and skip automatic recalculation.
- Decide whether the slider stays enabled at all times or is enabled only when dynamic scaling is off; if possible, disable it visually when auto mode is active to make the interaction clear.
- The slider should have range from 1-15V, with ticks at each integer volt.  

### 6. Add grid line control

Hook the grid toggle to the persistent chart axes.

- Enable or disable grid lines through the `QValueAxis` configuration rather than rebuilding the chart.
- Preserve the current low-chrome look by keeping labels hidden if that remains desirable.
- If Qt requires visible axes for visible grid lines, keep labels/ticks minimal so the chart gains structure without becoming cluttered.

### 7. Update the refresh path carefully

Once the new axis/control model exists, simplify `update_stripchart()`.

- Keep the existing data append, pruning, and channel-visibility behavior.
- Replace per-refresh axis construction with:
  - time-axis range updates,
  - voltage-axis range updates based on dynamic/manual mode,
  - optional grid visibility updates only when settings change.
- Verify `clear_stripchart()` also resets any cached auto-scaling state so the next samples establish a fresh range.

## Validation plan

### Targeted manual checks

- Launch the app and verify the new controls appear in the strip chart group.
- Confirm `Dynamic Scale` changes whether the voltage axis follows incoming data or the manual slider.
- Confirm both channel traces use the same voltage range during dynamic scaling.
- Confirm the maximum-voltage slider clamps the chart range when dynamic scaling is off.
- Confirm the grid toggle shows and hides chart grid lines without breaking updates.
- Confirm `Toggle Channels`, `Clear Chart`, and the speed slider still work as before.

### Low-risk automated checks

- If voltage-range logic is extracted into a small helper, add focused tests for:
  - empty data,
  - single-channel-dominant data,
  - symmetric range generation,
  - manual range floor behavior.
- Avoid new tests that require live Qt event loops, serial devices, or telescope hardware unless the implementation naturally makes such testing easy.

## Risks and notes

- The current refresh path recreates chart/axis attachments every update, so moving axis setup out of the hot path should happen before adding new chart behavior.
- `layouts/Makefile` still references `pyuic5` while runtime uses `PySide6`; if UI regeneration is required, preserve the repository’s existing pattern and document any toolchain mismatch encountered.
- If the intended meaning of “both axis are scale the same” is equal physical X/Y aspect ratio rather than one shared voltage scale for both channels, confirm that before implementation because it would materially change chart behavior.
