# Control Panel Refactor Plan — Strip Chart Section

## Objective

Clean up the strip chart control group in [layouts/threepio.ui](../layouts/threepio.ui) so every option (speed, voltage scale, grid, channel visibility, clear) follows one consistent layout and interaction pattern. The current group accreted three different slider-row patterns and a multi-state cycle button; this pass unifies them, hides dead controls, and adds light QSS polish.

## Constraints from `.agent/AGENTS.md`

- Keep edits focused and minimal; don't refactor unrelated panels (Signal, Declinometer, Data, Message, Console).
- The `.ui` file is the source of truth — regenerate `layouts/threepio_ui.py` to match.
- The runtime is **PySide6** (declared in `pyproject.toml`, used by every `from PySide6 import …` in the codebase). The `AGENTS.md` note about `pyuic5` reflects a stale `layouts/Makefile`; this refactor regenerates with `pyside6-uic` instead so the source-of-truth and the generator finally agree. (See step 5 and the "Deprecated / legacy API cleanup" section.)
- Prefer fixing root causes over patching symptoms (e.g., reorganize the layout instead of layering spacers/stretches to mask alignment problems).
- Validate by import + targeted manual GUI check; do not add hardware-dependent tests.

## Current state (what the panel looks like today)

`stripchart_control_group` at [layouts/threepio.ui:539-718](../layouts/threepio.ui#L539-L718) holds four heterogeneous rows inside a `QGridLayout`:

| Row | Pattern | Widgets |
|-----|---------|---------|
| 0 | Label – slider – label, wrapped in `frame_2` + `gridLayout_3` | `stripchart_slower_label`, `stripchart_speed_slider`, `stripchart_faster_label` |
| 1 | Bare `QHBoxLayout` (`horizontalLayout_4`) | `stripchart_dynamic_scale_checkbox`, `stripchart_max_voltage_slider`, `stripchart_max_voltage_value_label` |
| 2 | Bare `QHBoxLayout` (`horizontalLayout_5`) | `stripchart_grid_checkbox`, `stripchart_grid_sparser_label`, `stripchart_grid_density_slider`, `stripchart_grid_denser_label` |
| 3 | `QHBoxLayout` (`horizontalLayout`) wrapped in `frame` | `toggle_channel_button`, `chart_clear_button` |

### Concrete UX problems

1. **Sliders don't align.** Each row uses a different label/widget mix, so the slider tracks start at different x-offsets. The eye has nowhere to anchor.
2. **Three different "what does this slider do?" patterns.** Speed uses bracketing labels (Slower/Faster), grid density does the same (Sparser/Denser), max voltage uses a single trailing readout (`5V`). Pick one.
3. **No numeric readout for speed or grid density.** Users can't tell what window/density they're at; the only signal is visual rate of redraw. The voltage slider is the only one with a value label, and that label has no min-width so it shifts horizontally as digits change.
4. **Dead controls when toggled off.** The grid-density slider and labels remain visible but disabled when `Grid` is unchecked, adding noise.
5. **Toggle Channels is a 4-state cycle.** [threepio.py:536-538](../threepio.py#L536-L538) walks `(A, B) → (B, A^B)`, producing A-only → both → B-only → neither. The label "Toggle Channels" implies a 2-state toggle, and there's no visual cue for current state.
6. **Tab order is incomplete.** [layouts/threepio.ui:1068-1077](../layouts/threepio.ui#L1068-L1077) lists `stripchart_speed_slider` then jumps straight to `chart_clear_button`, skipping every control added in the strip chart upgrade.
7. **No tooltips.** Nothing explains what `Dynamic Scale` actually does to the X axis, or that "Toggle Channels" cycles through four states.
8. **Wrapper `QFrame`s exist only as layout helpers.** `frame_2` and `frame` (rows 0 and 3) add nothing structural and complicate margin handling.
9. **Empty `stylesheet.qss`.** The repo carries a stylesheet file but never populates it; small, self-contained QSS for this panel is a low-risk first use.

## Working assumptions (confirmed with user)

- **Channel toggling** is replaced by two buttons (`Toggle A`, `Toggle B`) with colored swatches reflecting current visibility — preserves the per-channel control the cycle button offered, but makes state visible at a glance.
- **Grid density** is hidden (not just disabled) when the `Grid` checkbox is off.
- **Visual scope** is layout cleanup plus light QSS polish — no font/color overhauls, no icons, no broader theming.

## Target layout

Rebuild `stripchart_control_group` as a single `QGridLayout` with three columns: **label · control · readout**. Every row obeys this shape so sliders, checkboxes, and readouts align vertically.

```
┌─ Strip chart ───────────────────────────────────────────────┐
│ Time window      [────────●─────────]              8s        │
│ Voltage scale    ☑ Auto   [────●─────]            ±5 V       │
│ Grid             ☑ Show   [───●──────]             8 lines   │  ← row hidden when ☐
│ Channels         [● Toggle A]   [● Toggle B]                 │
│                                          [ Clear chart ]     │
└─────────────────────────────────────────────────────────────┘
```

Column behavior:

- **Column 0 (label):** right-aligned text label naming the option. Width is set so the longest label fits; all rows share it via grid column.
- **Column 1 (control):** the primary interactive widget(s). For voltage scale and grid, this column hosts an inline `QHBoxLayout` of `[checkbox, slider]` so the on/off and tuning live together.
- **Column 2 (readout):** monospace numeric label showing the current value (`8s`, `±5 V`, `8 lines`). Fixed minimum width so digits don't shift the layout. Empty for the channels/clear row.

Action row (`Channels` + `Clear chart`) sits at the bottom and spans all three columns. The clear button right-aligns via a stretch.

## Files to change

- `layouts/threepio.ui` — restructure `stripchart_control_group`, rename a couple of widgets where the new role demands it, fix tabstops, add tooltips.
- `layouts/threepio_ui.py` — regenerate (or hand-sync, given the pyuic5/PySide6 mismatch noted in `AGENTS.md`).
- `threepio.py` — replace `toggle_channels` cycle with two independent toggles, add slider-readout updates for speed and grid density, switch `toggle_stripchart_grid` to set widget *visibility* (not just `setEnabled`) on the density row, refresh tooltips, and update any signal wiring that changed.
- `stylesheet.qss` — add a small block scoped to `#stripchart_control_group` for sub-row spacing, slider track height, and the channel-toggle swatch colors.

## Implementation plan

### 1. Restructure the `.ui` group

Replace the body of `stripchart_control_group` with a fresh `QGridLayout` (3 columns × 5 rows). Each option row uses `(label_col=0, control_col=1, readout_col=2)`.

Suggested widget map (renaming where current names mismatch the new role):

| Row | Col 0 (label) | Col 1 (control) | Col 2 (readout) |
|-----|--------------|-----------------|-----------------|
| 0 | `stripchart_speed_label` ("Time window") | `stripchart_speed_slider` (existing) | `stripchart_speed_value_label` (new) |
| 1 | `stripchart_voltage_label` ("Voltage scale") | inline H-layout: `stripchart_dynamic_scale_checkbox` ("Auto") + `stripchart_max_voltage_slider` | `stripchart_max_voltage_value_label` (existing, restyled) |
| 2 | `stripchart_grid_label` ("Grid") | inline H-layout: `stripchart_grid_checkbox` ("Show") + `stripchart_grid_density_slider` | `stripchart_grid_density_value_label` (new) |
| 3 | `stripchart_channels_label` ("Channels") | inline H-layout: `toggle_channel_a_button` + `toggle_channel_b_button` | _empty_ |
| 4 | _empty (or spans 0–1)_ | _stretch_ | `chart_clear_button` |

Notes on the rename:

- Drop `stripchart_slower_label`, `stripchart_faster_label`, `stripchart_grid_sparser_label`, `stripchart_grid_denser_label` — their job is taken over by the new readout column. Tick marks on the slider already convey direction.
- `Dynamic Scale` checkbox label shortens to `Auto` since the row label ("Voltage scale") already establishes context. Same with `Grid` → `Show`.
- Replace `toggle_channel_button` (single cycle button) with two buttons: `toggle_channel_a_button` and `toggle_channel_b_button`. Each is checkable (`<property name="checkable"><bool>true</bool></property>`) so its checked state mirrors visibility, with a colored swatch via QSS (see step 4).
- Remove the `frame` and `frame_2` wrapper widgets — the new grid layout doesn't need them, and the existing zero-margin overrides are a workaround for nested wrapping.

Tooltips to add (one per control):

- Speed slider: "Length of the time window shown on the chart."
- Auto checkbox: "Auto-fit the voltage axis to incoming data; when off, use the manual slider."
- Max voltage slider: "Manual maximum voltage (±) when Auto is off."
- Show checkbox: "Show grid lines on the chart."
- Grid density slider: "Number of vertical grid divisions."
- Toggle A / Toggle B: "Show or hide channel A/B."
- Clear chart: "Discard the currently plotted samples."

### 2. Fix tab order

Update `<tabstops>` ([layouts/threepio.ui:1068-1077](../layouts/threepio.ui#L1068-L1077)) to walk top-to-bottom through the new panel before continuing on to `dec_view` and the other groups:

```
stripchart_speed_slider →
stripchart_dynamic_scale_checkbox → stripchart_max_voltage_slider →
stripchart_grid_checkbox → stripchart_grid_density_slider →
toggle_channel_a_button → toggle_channel_b_button →
chart_clear_button → dec_view → variance_dial → polarization_dial →
noise_dial → calibration_check_box → declination_slider
```

### 3. Wire up the new behaviors in `threepio.py`

- **Speed readout:** in `update_stripchart_speed` ([threepio.py:370-373](../threepio.py#L370-L373)), also write `f"{self.stripchart_display_seconds:.0f}s"` to `stripchart_speed_value_label`.
- **Grid density readout:** in `update_stripchart_grid_density` ([threepio.py:574-576](../threepio.py#L574-L576)), write `f"{self.stripchart_grid_density} lines"` to the new label.
- **Voltage readout consistency:** keep the existing `update_stripchart_max_voltage` ([threepio.py:552-559](../threepio.py#L552-L559)) but format as `f"±{self.stripchart_manual_max_voltage:.0f} V"` to convey that the axis is symmetric around zero. Give the label a fixed `minimumWidth` in the `.ui` so digit changes don't shift the layout.
- **Hide vs. disable for grid density:** in `toggle_stripchart_grid` ([threepio.py:561-572](../threepio.py#L561-L572)), call `setVisible` on the density slider, its row label, and its readout instead of `setEnabled`. The whole row collapses when grid is off.
- **Channel toggles:** replace `toggle_channels` ([threepio.py:536-538](../threepio.py#L536-L538)) with two slot methods, e.g. `toggle_channel_a` / `toggle_channel_b`, that flip a single entry of `self.channel_visibility` and update the corresponding button's `checked` state. Initialize both buttons checked. The existing `update_stripchart` pen logic ([threepio.py:516-527](../threepio.py#L516-L527)) already keys off `self.channel_visibility` and needs no changes.
- **Signal wiring:** in `__init__` ([threepio.py:94-124](../threepio.py#L94-L124)), drop the `toggle_channel_button` connection and add the two new ones. Make sure the new readout labels are populated once at startup (call the slot during init) so they aren't blank before the first user interaction.

### 4. Light QSS in `stylesheet.qss`

Add a small block scoped to the new panel. Keep it short — this is the first real use of the file, so set the precedent of small, scoped rules:

```qss
QGroupBox#stripchart_control_group QLabel[role="readout"] {
    font-family: "Iosevka Aile";
    min-width: 56px;
    qproperty-alignment: AlignRight;
}

QGroupBox#stripchart_control_group QSlider::groove:horizontal {
    height: 4px;
}

QPushButton#toggle_channel_a_button:checked {
    border-left: 4px solid #2196f3;  /* matches Threepio.BLUE */
}
QPushButton#toggle_channel_b_button:checked {
    border-left: 4px solid #ff5252;  /* matches Threepio.RED */
}
QPushButton#toggle_channel_a_button:!checked,
QPushButton#toggle_channel_b_button:!checked {
    border-left: 4px solid transparent;
    color: #888;
}
```

Mark the three readout labels with a dynamic property (`<property name="role"><string>readout</string></property>`) so the QSS selector targets them without per-widget rules. The button colors mirror `Threepio.BLUE` / `Threepio.RED` (defined as class constants in `threepio.py`).

Make sure `stylesheet.qss` is actually loaded by the app — check the `QApplication` setup in `threepio.py` / `run.pyw`. If it isn't, wire it up via `app.setStyleSheet(open("stylesheet.qss").read())` at startup (one line, at the same place the app instance is constructed).

### 5. Regenerate `threepio_ui.py` with `pyside6-uic`

The runtime is PySide6, so generated code must be PySide6 too. Update `layouts/Makefile` to invoke `pyside6-uic` (replacing the stale `pyuic5` rule), then regenerate:

```sh
pyside6-uic layouts/threepio.ui -o layouts/threepio_ui.py
```

This single change fixes the long-standing toolchain mismatch flagged in `AGENTS.md`. After regeneration, `from layouts.threepio_ui import Ui_MainWindow` should import cleanly and expose the new attribute names listed in step 1. Run the same regeneration for any other `.ui` files the Makefile covers (`alert.ui`, `credits.ui`, `dec_cal.ui`, `obs.ui`, `quit.ui`, `ra_cal.ui`) so all generated modules end up on the same generator — the diffs against the existing files should be minimal (mostly the `# -*- coding: utf-8 -*-` header and import lines), but commit them so future regenerations don't surface unrelated noise.

After regeneration, also update the `AGENTS.md` "UI and Generated Files" section that documents the `pyuic5` discrepancy — it's now resolved.

### 6. Deprecated / legacy API cleanup

Concrete deprecated calls to fix while the `.ui` and surrounding code are already in flight:

- **PyQt5 custom-widget header in `threepio.ui`.** [layouts/threepio.ui:1061-1067](../layouts/threepio.ui#L1061-L1067) declares `<header>PyQt5.QtChart</header>`, which is a leftover from the pre-migration `.ui`. Change it to the PySide6 module path so the generator and any external `.ui`-loading tools see the right import:

  ```xml
  <customwidget>
    <class>QChartView</class>
    <extends>QGraphicsView</extends>
    <header>PySide6.QtCharts</header>
  </customwidget>
  ```

  Note the `QtCharts` plural — PySide6 renamed `QtChart` (PyQt5) to `QtCharts`, matching the import already used at [threepio.py:55](../threepio.py#L55).

- **Unscoped enum on `QPainter`.** [threepio.py:89](../threepio.py#L89) uses `QtGui.QPainter.Antialiasing`, which is the unscoped enum form deprecated in PySide6 6.4+. Update to the scoped form:

  ```python
  self.ui.stripchart.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
  ```

- **Sweep for any other unscoped enum accesses** while the file is open. Run a quick grep across the main module and dialog wrappers and convert what you find:

  ```sh
  grep -nE 'QPainter\.(Antialiasing|TextAntialiasing|SmoothPixmapTransform)' \
       threepio.py dialogs/*.py _dialogs/*.py
  grep -nE 'Qt\.(Align[A-Z][a-z]+|Horizontal|Vertical|Checked|Unchecked|PartiallyChecked)' \
       threepio.py dialogs/*.py _dialogs/*.py
  grep -nE '\.exec_\(' threepio.py dialogs/*.py _dialogs/*.py
  ```

  Common conversions:
  - `Qt.AlignBottom` → `Qt.AlignmentFlag.AlignBottom`
  - `Qt.Horizontal` → `Qt.Orientation.Horizontal`
  - `Qt.Checked` / `Qt.Unchecked` → `Qt.CheckState.Checked` / `Qt.CheckState.Unchecked`
  - `dialog.exec_()` → `dialog.exec()` (the trailing-underscore form was a Python-2-keyword workaround and is deprecated)

  Limit the sweep to obvious one-line replacements; do not rewrite signal-slot syntax or rework dialog lifecycles in this pass — that is a separate refactor.

- **`.ui` file enum strings** (`Qt::AlignBottom`, `QSlider::TicksBothSides`, etc.) are interpreted by `pyside6-uic` and emit modern scoped forms in the generated module. Leave them as-is; rewriting them in XML produces no functional change.

- **AGENTS.md follow-up.** Once the generator/runtime mismatch is resolved, drop the "current `layouts/Makefile` uses `pyuic5`, while the runtime imports `PySide6`" caveat from `AGENTS.md` so future agents don't replicate the workaround.

### 7. Remove the now-unused widget references

- Drop the `stripchart_slower_label` / `stripchart_faster_label` / `stripchart_grid_sparser_label` / `stripchart_grid_denser_label` lookups (none exist in `threepio.py` today, but confirm via grep before removing from the `.ui`).
- Drop the old `toggle_channel_button` symbol from both the `.ui` and `threepio.py`.

## Validation plan

1. **Static:** `python -c "from layouts.threepio_ui import Ui_MainWindow"` to confirm the regenerated module imports without referencing missing widgets.
2. **Static:** `pytest -q` to catch any incidental breakage.
3. **Manual GUI smoke:** launch `python threepio.py` (no hardware required for the control panel itself):
   - All five rows align: labels in a column, sliders in a column, readouts in a column.
   - Speed slider readout updates live (`8s` → `120s` range).
   - Auto checkbox enables/disables the voltage slider; readout shows `±N V`.
   - Show checkbox collapses/expands the grid-density row entirely.
   - Toggle A / Toggle B independently hide the corresponding series; swatch color reflects checked state; both off → empty chart.
   - Clear chart still resets the plot.
   - Tab key walks through controls in the order listed in step 2.
   - Tooltips appear on hover.
4. **Visual sanity:** confirm the panel doesn't grow vertically beyond its previous footprint when grid is off (the hidden row should reclaim the space).

## Out of scope (call out, don't fix here)

- Restyling other group boxes (Signal, Declinometer, Data, Message). Those have their own inconsistencies (large inline `<palette>` blocks for channel value colors, hard-coded `pointsize` fonts, raw style strings on the console frame) but are out of scope for a strip-chart-focused pass.
- Persisting user preferences (Auto on/off, manual voltage, grid density) across sessions.
- Broad signal-slot or dialog-lifecycle rewrites. The deprecated-API sweep in step 6 is intentionally limited to one-line scoped-enum and `exec_` → `exec` replacements.

## Risks

- **`pyside6-uic` invocation differences.** It lives alongside `pyside6` in the `pyside6` distribution; verify it's on PATH inside the project's venv before editing `layouts/Makefile`. If it isn't, install with `python -m pip install pyside6` (already declared in `pyproject.toml`).
- **Regenerated UI diffs may be larger than expected.** Switching generators can churn formatting (header comments, import order, `setObjectName` placement) across all `*_ui.py` files. Review the diff per file; the structural content should be identical.
- **Stylesheet wiring may not exist.** If `stylesheet.qss` was never loaded, the QSS will have no visible effect until the loader line is added. Check `run.pyw` and the `__main__` block in `threepio.py` early in the implementation.
- **Channel-toggle button colors:** the chosen swatch colors must match the chart pen colors used in [threepio.py:518-527](../threepio.py#L518-L527) (`self.BLUE` / `self.RED`). If those constants change, the QSS needs to be updated in tandem — but that's a class-constants concern, not a styling one.
- **Deprecated-enum sweep scope creep.** The sweep is bounded to one-line replacements; if a hit requires structural changes (e.g., `QFlags` arithmetic, custom subclasses), defer to a separate cleanup PR.
