Project Overview
- `threepio` is a Python desktop application for Green Bank Observatory's 40-foot telescope data acquisition workflow.
- The entry point is `threepio.py`, which builds a Qt main window and coordinates dialogs, layouts, hardware I/O, and observation logic.
- Treat the checked-in metadata as mixed-vintage: `README.md` still references `PyQt5` and `requirements.txt`, but the current code and `pyproject.toml` use `PySide6` and declare dependencies there. Prefer the code and `pyproject.toml` when in doubt.
Repository Map
- `threepio.py`: main GUI application entry point.
- `tools/` and `_tools/`: observation models, hardware communication helpers, clocks, discovery, and related logic.
- `dialogs/` and `_dialogs/`: dialog wrappers and related UI behavior.
- `layouts/`: Qt Designer `.ui` sources and generated `*_ui.py` modules.
- `tests/`: lightweight Python tests and smoke checks.
- `assets/`: bundled media and static resources.
- `data/`: runtime data output; keep existing ignore behavior intact.
Setup and Run
- Preferred environment is Python `3.13`.
- Install dependencies from `pyproject.toml` / `uv.lock` rather than `requirements.txt`.
- Recommended setup:
  - `python3.13 -m venv venv`
  - `source venv/bin/activate`
  - `python -m pip install -U pip`
  - `python -m pip install -e . pytest`
- Launch the app with `python threepio.py`.
Testing and Validation
- Run targeted tests first, then broader checks if needed.
- Default test command: `pytest -q`.
- Many code paths interact with telescope hardware or serial devices; avoid introducing tests that require connected hardware unless the task explicitly calls for it.
- For UI-only or static refactors, favor import-level or model-level verification over launching the full GUI.
UI and Generated Files
- In `layouts/`, the `.ui` files are the editable sources and the `*_ui.py` files are generated artifacts.
- If a task changes widget structure, labels, or layout wiring, update the relevant `.ui` file and regenerate the matching `*_ui.py` file so both stay in sync.
- Use `pyside6-uic` to regenerate files in `layouts/`; the runtime and generated modules should stay on the same PySide6 toolchain.
Editing Guidance
- Make focused, minimal changes that match the existing code style.
- Prefer fixing root causes over adding defensive patches around symptoms.
- Avoid broad renames across the Qt/UI code unless necessary; many modules are tightly coupled by generated attribute names.
- Preserve local data paths, serial behavior, and runtime file conventions unless the task specifically changes them.
- Do not remove checked-in generated UI modules unless the task explicitly asks for that cleanup.
Documentation Guidance
- If behavior changes, update `README.md` when the user-facing setup or run instructions are affected.
- If you notice stale docs, align them with the current Python / `PySide6` setup when that is within scope.
Safety Notes
- Be careful with code that touches serial devices, calibration files, or files under `data/`.
- Prefer non-destructive reads when investigating hardware-facing code.
- Keep `.gitignore` entries for virtual environments, generated runtime data, and local IDE files intact.

Recent Agent Update (2026-05-12)
- Implemented strip chart upgrades described in `.agent/strip-chart-upgrades.md`:
  - Added dynamic scale toggle, manual max-voltage slider (1-15V), and grid toggle controls.
  - Added shared dynamic voltage scaling across both strip chart channels using a symmetric range.
  - Refactored strip chart axis usage to persistent chart axes updated in place.
