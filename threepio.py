import time
from enum import Enum
from functools import reduce
from typing import Callable
from math import floor

from PySide6 import QtWidgets, QtCore, QtGui, QtMultimedia, QtCharts

from dialogs import AlertDialog, CreditsDialog, DecDialog, ObsDialog, RADialog
from layouts import threepio_ui, quit_ui
from tools import (
    Comm,
    DataPoint,
    Survey,
    Scan,
    Spectrum,
    SuperClock,
    TimerManager,
    GB_LATITUDE,
    Tars,
    MiniTars,
    discovery,
    LogTask,
    Observation,
    Alert,
    DecCalc,
    ObsType,
)


class Threepio(QtWidgets.QMainWindow):
    """
    Green Bank Observatory's 40-Foot Telescope's very own data acquisition system.
    Extends Qt's QMainWindow class and is the main window of the application.
    """

    # Basic time
    BASE_PERIOD = 10  # ms = 100Hz
    GUI_UPDATE_PERIOD = 1000  # ms = 1Hz
    STRIPCHART_PERIOD = 16.7  # ms = 60Hz

    # Style
    BLUE = 0x2196F3
    RED = 0xFF5252
    MIN_WIDTH = 860

    # The voltage range slider is integer-only, so it counts tenths of a volt.
    VOLTAGE_SLIDER_STEPS_PER_VOLT = 10
    VOLTAGE_SLIDER_MAX_VOLTS = 15

    class Mode(Enum):
        NORMAL = 0
        TESTING = 1

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        # Use main_ui for window setup
        self.ui = threepio_ui.Ui_MainWindow()
        with open("stylesheet.qss", encoding="utf-8") as f:
            self.base_stylesheet = f.read()
        self.setStyleSheet(self.base_stylesheet)
        self.ui.setupUi(self)
        self.setWindowTitle("Threepio")

        # Mode
        self.legacy_mode = False
        self.mode = Threepio.Mode.NORMAL

        # "Console" output
        self.message_log: list[LogTask] = []
        self.log(">>> THREEPIO")
        self.update_console()

        stripchart_log_task = self.log(">>> Initializing...")
        # Clock
        self.clock = SuperClock()
        self.scheduler = TimerManager()

        # Initialize stripchart
        self.stripchart_display_seconds = 8
        self.should_clear_stripchart = False
        self.channel_visibility = (True, True)
        self.stripchart_series_a = QtCharts.QLineSeries()
        self.stripchart_series_b = QtCharts.QLineSeries()
        self.stripchart_dynamic_scale_enabled = True
        self.stripchart_grid_enabled = False
        self.stripchart_grid_density = 8
        self.stripchart_manual_min_voltage = 0.0
        self.stripchart_manual_max_voltage = 5.0
        self.stripchart_min_voltage_range = 1.0
        self.initialize_voltage_range_slider()
        self.axis_x = QtCharts.QValueAxis()
        self.axis_y = QtCharts.QValueAxis()
        self.chart = QtCharts.QChart()
        self.ui.stripchart.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.initialize_stripchart()  # Should this include more of the above?

        self.update_stripchart_speed()

        # Connect buttons
        self.ui.stripchart_speed_slider.valueChanged.connect(
            self.update_stripchart_speed
        )
        self.ui.stripchart_dynamic_scale_checkbox.toggled.connect(
            self.toggle_stripchart_dynamic_scale
        )
        self.ui.stripchart_voltage_range_slider.valuesChanged.connect(
            self.update_stripchart_voltage_range
        )
        self.ui.stripchart_grid_checkbox.toggled.connect(self.toggle_stripchart_grid)
        self.ui.stripchart_grid_density_slider.valueChanged.connect(
            self.update_stripchart_grid_density
        )

        self.ui.actionInfo.triggered.connect(self.handle_credits)

        self.ui.actionScan.triggered.connect(self.handle_scan)
        self.ui.actionSurvey.triggered.connect(self.handle_survey)
        self.ui.actionSpectrum.triggered.connect(self.handle_spectrum)
        self.ui.actionGetInfo.triggered.connect(self.handle_get_info)

        self.ui.actionDec.triggered.connect(self.dec_calibration)
        self.ui.actionRA.triggered.connect(self.ra_calibration)

        self.ui.actionNormal.triggered.connect(self.set_state_normal)
        self.ui.actionTesting.triggered.connect(self.set_state_testing)
        self.ui.actionLegacy.triggered.connect(self.toggle_state_legacy)

        self.theme_action_group = QtGui.QActionGroup(self)
        for action, scheme in (
            (self.ui.actionThemeSystem, QtCore.Qt.ColorScheme.Unknown),
            (self.ui.actionThemeLight, QtCore.Qt.ColorScheme.Light),
            (self.ui.actionThemeDark, QtCore.Qt.ColorScheme.Dark),
        ):
            self.theme_action_group.addAction(action)
            action.triggered.connect(lambda _=False, s=scheme: self.set_theme(s))

        self.ui.channel_dual_button.clicked.connect(
            lambda: self.set_channel_visibility(True, True)
        )
        self.ui.channel_a_button.clicked.connect(
            lambda: self.set_channel_visibility(True, False)
        )
        self.ui.channel_b_button.clicked.connect(
            lambda: self.set_channel_visibility(False, True)
        )
        self.ui.chart_clear_button.clicked.connect(self.clear_stripchart)

        # Bleeps and bloops
        self.beep_sound = QtMultimedia.QSoundEffect()
        url = QtCore.QUrl()
        self.beep_sound.setSource(url.fromLocalFile("assets/beep3.wav"))
        self.beep_sound.setVolume(0.5)
        # self.click_sound.play()
        self.last_beep_time = 0.0

        # Alerts
        self.open_alert = None
        self.alert_thread: set[QtCore.QThread] = set()
        self.worker = None

        # Tars/DATAQ
        dataq, declinometer = discovery()
        self.tars = Tars(parent=self, device=dataq)
        self.tars.start()
        self.minitars = MiniTars(parent=self, device=declinometer)
        if declinometer is None:
            # Simulated declination looks identical to real data downstream, so
            # say so loudly rather than only writing it to the message log.
            self.alert(Alert("Declinometer not found — declination is SIMULATED", "Got it"))
        elif not self.minitars.handshake():
            self.alert(Alert("Declinometer found but not responding", "Got it"))
        self.minitars.start()

        # Establish observation
        self.obs = None
        self.ui_thinks_obs_is_set = False
        self.completed_one_calibration = False

        # Establish data array & most recent dec
        self.data = []
        self.current_dec = 0.0
        self.current_data_point = None

        # Tars communication interpretation
        self.previous_transmission = None

        # Telescope visualization
        self.dec_scene = QtWidgets.QGraphicsScene()
        self.ui.dec_view.setScene(self.dec_scene)
        self.update_dec_view()

        # Initial dec calibration
        self.dec_calc = DecCalc()
        try:
            self.dec_calc.load_dec_cal()
        except FileNotFoundError:
            self.alert(Alert("Dec must be calibrated", "Got it"))

        # Primary clock
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)  # Do everything
        self.timer.start(self.BASE_PERIOD)  # Set refresh rate
        # Assign timers to functions meant to fire periodically
        self.scheduler.add_timer(1000, self.update_gui, name="update_gui")
        self.scheduler.add_timer(60000, self.clock.resync_from_astropy, name="sidereal_resync")
        self.data_timer = self.scheduler.add_timer(1000,
                                               self.update_data,
                                               name="update_data")

        # Measure refresh rate
        self.time_of_last_fps_update = time.perf_counter()
        self.ticks_since_last_fps_update = 0

        # Alert user that threepio is done initializing
        stripchart_log_task.set_status(0)
        self.message("Ready!!!")

    def tick(self):
        """
        Primary controller for each clock tick. Fires as fast as possible up to 100Hz.
        Anything meant to update as often as possible should be placed here. Everything
        else should be assigned to a timer.
        """

        # Attempt to grab latest data point; it won't always be written to the data file
        tars_datum = self.tars.read_latest()  # Get data from DAQ
        minitars_datum = self.minitars.read_latest()  # Get data from Arduino
        sidereal_timestamp = self.clock.get_sidereal_seconds()

        # The two devices stream independently. Keep the most recent
        # declination rather than requiring both serial frames to land during
        # the same 10 ms tick; otherwise a slow or disconnected declinometer
        # suppresses every valid DATAQ voltage reading.
        if minitars_datum is not None:
            self.current_dec = self.dec_calc.calculate_declination(minitars_datum)

        if tars_datum is not None:
            self.current_data_point = DataPoint(  # Create data point
                float(sidereal_timestamp),  # RA
                float(self.current_dec),  # Dec
                float(tars_datum.a),  # Channel A
                float(tars_datum.b),  # Channel B
            )
            self.data.append(self.current_data_point)  # Add to data list

        self.scheduler.run_timers()  # Run all timers that are due

        # Update every tick
        self.update_stripchart()
        self.update_dec_view()

        self.ticks_since_last_fps_update += 1  # For measuring fps

    def update_data(self) -> None:
        if not self.check_and_set_observation_state():
            return
        assert self.obs is not None  # The language server was complaining

        period = 1000 / self.obs.freq  # Hz -> ms
        self.data_timer.set_period(period)

        transmission = self.obs.communicate(
            self.current_data_point, self.clock.get_time()
        )

        obs_type = self.obs.obs_type

        if transmission != self.previous_transmission:
            if transmission is Comm.START_CAL:
                alerts = [
                    Alert("Turn the calibration switches ON", "Okay"),
                    Alert("Are the calibration switches ON?", "Yes"),
                ]
                if self.completed_one_calibration:
                    if self.obs.obs_type is ObsType.SURVEY:
                        alerts = [
                            Alert("STOP the telescope", "Okay"),
                            Alert("Has the telescope been stopped?", "Yes"),
                        ] + alerts
                    elif self.obs.obs_type is ObsType.SPECTRUM:
                        alerts = [
                            Alert("Set frequency to 1319.5MHz", "Okay"),
                            Alert("Is the frequency set to 1319.5MHz?", "Yes"),
                        ] + alerts

                self.alert(
                    *alerts,
                    callback=self.make_advance_obs_callback(
                        "Taking calibration data!!!"
                    ),
                )
                self.completed_one_calibration = True  # Only alert on second cal

            elif transmission is Comm.START_BG:
                self.alert(
                    Alert("Turn the calibration switches OFF", "Okay"),
                    Alert("Are the calibration switches OFF?", "Yes"),
                    callback=self.make_advance_obs_callback(
                        "Taking background data!!!"
                    ),
                )

        # print(transmission)

        should_beep = False
        if transmission is Comm.START_WAIT:
            self.obs.next()
            self.message(f"Waiting for {obs_type.name.lower()} to begin...")
        elif transmission is Comm.START_DATA:
            self.obs.next()
            self.message(f"Taking {obs_type.name.lower()} data!!!")
        elif transmission is Comm.FINISHED:
            self.obs.next()
            self.message(f"{obs_type.name.capitalize()} complete!!!")
            self.obs = None
        elif transmission is Comm.SEND_TEL_NORTH:
            self.message("Send telescope NORTH at max speed!!!", beep=False, log=False)
            should_beep = True
        elif transmission is Comm.SEND_TEL_SOUTH:
            self.message("Send telescope SOUTH at max speed!!!", beep=False, log=False)
            should_beep = True
        elif transmission is Comm.END_SEND_TEL:
            self.message(
                f"Taking {obs_type.name.lower()} data!!!", beep=False, log=False
            )
        elif transmission is Comm.FINISHING_SWEEP:
            self.message("Finishing last sweep!!!", beep=False)
        elif transmission is Comm.BEEP:
            should_beep = True
        elif transmission is Comm.NEXT:
            self.obs.next()
        elif transmission is Comm.NO_ACTION:
            pass
        
        if should_beep:
            self.beep(message="update_data")

        if should_beep:
            self.beep(message="update_data")

        self.previous_transmission = transmission

    def make_advance_obs_callback(self, message: str) -> Callable[[], None]:
        """Build an alert callback that advances the observation only if it is
        still in the state the alert was spawned for, so a duplicate or stale
        dialog cannot advance the state machine a second time."""
        assert self.obs is not None
        spawn_state = self.obs.state

        def callback():
            if self.obs is None or self.obs.state is not spawn_state:
                return
            self.scheduler.reset_timer_anchors()
            self.obs.next()
            self.message(message)

        return callback

    def set_state_normal(self):
        self.ui.actionNormal.setChecked(True)
        self.ui.actionTesting.setChecked(False)
        self.ui.testing_frame.hide()
        self.adjustSize()
        self.mode = Threepio.Mode.NORMAL

    def set_state_testing(self):
        self.ui.actionNormal.setChecked(False)
        self.ui.actionTesting.setChecked(True)
        self.ui.testing_frame.show()
        self.mode = Threepio.Mode.TESTING

    def set_theme(self, scheme: QtCore.Qt.ColorScheme):
        """Set light/dark appearance; Unknown follows the system setting."""
        QtGui.QGuiApplication.styleHints().setColorScheme(scheme)

    def toggle_state_legacy(self):
        """Makes Threepio look like the outgoing ERIRA DAQ software."""
        self.legacy_mode = not self.legacy_mode
        legacy_stylesheet = ""
        if self.legacy_mode:
            legacy_stylesheet = "\n* { background-color:#00ff00; color:#ff0000 }"
        self.setStyleSheet(f"{self.base_stylesheet}{legacy_stylesheet}")
        url = QtCore.QUrl()
        self.beep_sound.setSource(
            url.fromLocalFile(
                f"assets/beep{'-legacy' if self.legacy_mode else '3'}.wav"
            )
        )
        self.ui.actionLegacy.setChecked(self.legacy_mode)

    def check_and_set_observation_state(self) -> bool:
        """Check if there is a discrepancy between whether an observation is currently
        loaded and the ui state and update the UI accordingly."""

        def set_observation_ui_state(obs_is_loaded: bool):
            self.ui.actionRA.setDisabled(obs_is_loaded)
            self.ui.actionDec.setDisabled(obs_is_loaded)
            self.ui.actionSurvey.setDisabled(obs_is_loaded)
            self.ui.actionScan.setDisabled(obs_is_loaded)
            self.ui.actionSpectrum.setDisabled(obs_is_loaded)
            self.ui.actionGetInfo.setDisabled(not obs_is_loaded)
            self.ui_thinks_obs_is_set = obs_is_loaded

        if self.obs is not None:
            if not self.ui_thinks_obs_is_set:
                set_observation_ui_state(True)  # Update UI if discrepancy
            return True
        else:
            if self.ui_thinks_obs_is_set:  
                set_observation_ui_state(False)
            return False

    @staticmethod
    def handle_credits():
        dialog = CreditsDialog()
        dialog.exec()

    def update_stripchart_speed(self):
        self.stripchart_display_seconds = 120 - (
            (110 / 1000) * self.ui.stripchart_speed_slider.value()
        )
        self.ui.stripchart_speed_value_label.setText(
            f"{self.stripchart_display_seconds:.0f}s"
        )

    def update_gui(self):
        # current_time = self.clock.get_time()

        self.ui.ra_value.setText(self.clock.get_formatted_sidereal_time())  # RA
        self.ui.dec_value.setText(f"{self.current_dec:.4f}°")  # Dec
        if self.obs is not None:
            self.ui.sweep_value.setText(
                str(self.obs.sweep_number) if self.obs.sweep_number != -1 else "n/a"
            )  # Sweep number

        self.update_progress_bar()
        self.update_fps()
        self.update_console()
        self.update_voltage()

    def update_progress_bar(self):
        try:
            assert self.obs is not None
            (start_time, end_time) = self.obs.state_time_interval # type: ignore
            
            if end_time > 0.0:
                # print(f"{start_time=}, {end_time=}, {time.time()=}")
                current_time = time.time()

                val = 0
                if end_time > current_time > start_time and start_time > 0:
                    val = int(round(
                        (current_time - start_time) / (end_time - start_time) * 1000))
                self.ui.progressBar.setValue(val)

                # Set the label
                time_until_next_step = end_time - current_time
                # TODO: Abstract this?
                hours = int((atuns := abs(time_until_next_step)) / 3600)
                minutes = int((atuns - (hours * 3600)) / 60)
                seconds = int(round(atuns - (hours * 3600) - (minutes * 60)))
                label = reduce(
                    lambda a, c: a + c,
                    [
                        f"T{'-' if time_until_next_step > 0 else '+'}",
                        f"{hours:0>2}:" if hours > 0 else "",
                        f"{minutes:0>2}:" if minutes > 0 else "",
                        f"{seconds:0>2}",
                    ],
                )
                self.ui.progressBar.setFormat(label)
                return
        except AssertionError:
            self.ui.progressBar.setFormat("n/a")
            self.ui.progressBar.setValue(0)

    def update_dec_view(self):
        angle = self.current_dec - GB_LATITUDE

        # Telescope dish
        dish = QtGui.QPixmap("assets/dish.png")
        dish = QtWidgets.QGraphicsPixmapItem(dish)
        dish.setTransformOriginPoint(32, 32)
        dish.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
        dish.setY(16)
        dish.setRotation(angle)

        # Telescope base
        base = QtGui.QPixmap("assets/base.png")
        base = QtWidgets.QGraphicsPixmapItem(base)
        base.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)

        self.dec_scene.clear()
        for i in [dish, base]:
            self.dec_scene.addItem(i)

    def update_fps(self):
        """Updates the fps counter to display current refresh rate"""
        current_time = time.perf_counter()
        time_since_last_fps_update = current_time - self.time_of_last_fps_update

        try:
            new_fps = "%.2fHz" % (
                self.ticks_since_last_fps_update / time_since_last_fps_update
            )
        except ZeroDivisionError:
            new_fps = "-1.0"

        self.ui.refresh_value.setText(new_fps)
        self.time_of_last_fps_update = current_time
        self.ticks_since_last_fps_update = 0

    def initialize_stripchart(self):
        self.chart.addSeries(self.stripchart_series_b)
        self.chart.addSeries(self.stripchart_series_a)
        self.chart.addAxis(self.axis_x, QtCore.Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self.axis_y, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.stripchart_series_a.attachAxis(self.axis_x)
        self.stripchart_series_b.attachAxis(self.axis_x)
        self.stripchart_series_a.attachAxis(self.axis_y)
        self.stripchart_series_b.attachAxis(self.axis_y)
        self.update_stripchart_voltage_range()
        self.update_stripchart_grid_density()
        self.toggle_stripchart_dynamic_scale()
        self.toggle_stripchart_grid()
        self.set_channel_visibility(*self.channel_visibility)

        legend = self.chart.legend()
        if legend is not None:
            legend.hide()

        self.ui.stripchart.setChart(self.chart)

    def update_stripchart(self):
        try:
            # Parse latest data point
            # TODO: This will duplicate points if one fails to read
            new_a_raw = self.data[len(self.data) - 1].a
            new_b_raw = self.data[len(self.data) - 1].b
            new_ra_raw = self.data[len(self.data) - 1].timestamp

            # Handle legacy tuple payloads from old Tars sampling code.
            if isinstance(new_a_raw, tuple):
                new_a_raw = new_a_raw[1]
            if isinstance(new_b_raw, tuple):
                new_b_raw = new_b_raw[1]

            new_a = float(new_a_raw)
            new_b = float(new_b_raw)
            new_ra = float(new_ra_raw)

            # Add new data point to both series
            self.stripchart_series_a.append(new_a, new_ra)
            self.stripchart_series_b.append(new_b, new_ra)

            # We use these value several times
            current_sideral_seconds = self.clock.get_sidereal_seconds()
            oldest_y = current_sideral_seconds - self.stripchart_display_seconds

            # Remove the trailing end of the series
            clear_it = self.should_clear_stripchart  # Prevents a race hazard?
            for i in [self.stripchart_series_a, self.stripchart_series_b]:
                if clear_it:
                    i.clear()
                elif i.count() > 2 and i.at(1).y() < oldest_y:
                    i.removePoints(0, 2)
            self.should_clear_stripchart = False

            # Check for visibility
            if self.channel_visibility[0]:
                pen = QtGui.QPen(QtGui.QColor(self.BLUE))
            else:
                pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
            self.stripchart_series_a.setPen(pen)

            if self.channel_visibility[1]:
                pen = QtGui.QPen(QtGui.QColor(self.RED))
            else:
                pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
            self.stripchart_series_b.setPen(pen)

            self.axis_y.setMin(oldest_y)
            self.axis_y.setMax(current_sideral_seconds)
            self.update_stripchart_axes()

        except IndexError:  # No data yet
            pass

    def set_channel_visibility(self, show_a: bool, show_b: bool):
        self.channel_visibility = (show_a, show_b)
        if show_a and show_b:
            self.ui.channel_dual_button.setChecked(True)
        elif show_a:
            self.ui.channel_a_button.setChecked(True)
        else:
            self.ui.channel_b_button.setChecked(True)

    def clear_stripchart(self):
        self.should_clear_stripchart = True

    def initialize_voltage_range_slider(self):
        slider = self.ui.stripchart_voltage_range_slider
        steps = self.VOLTAGE_SLIDER_STEPS_PER_VOLT
        slider.setRange(0, self.VOLTAGE_SLIDER_MAX_VOLTS * steps)
        slider.setMinimumSpan(round(self.stripchart_min_voltage_range * steps))
        slider.setTickInterval(steps)
        slider.setPageStep(steps)
        slider.setValues(
            round(self.stripchart_manual_min_voltage * steps),
            round(self.stripchart_manual_max_voltage * steps),
        )

    def toggle_stripchart_dynamic_scale(self):
        self.stripchart_dynamic_scale_enabled = (
            self.ui.stripchart_dynamic_scale_checkbox.isChecked()
        )
        manual_visible = not self.stripchart_dynamic_scale_enabled
        self.ui.stripchart_voltage_range_slider.setVisible(manual_visible)
        self.ui.stripchart_voltage_range_value_label.setVisible(manual_visible)
        self.update_stripchart_axes()

    def update_stripchart_voltage_range(self):
        low, high = self.ui.stripchart_voltage_range_slider.values()
        steps = self.VOLTAGE_SLIDER_STEPS_PER_VOLT
        self.stripchart_manual_min_voltage = low / steps
        self.stripchart_manual_max_voltage = high / steps
        self.ui.stripchart_voltage_range_value_label.setText(
            f"{self.stripchart_manual_min_voltage:.1f}"
            f"–{self.stripchart_manual_max_voltage:.1f} V"
        )
        self.update_stripchart_axes()

    def toggle_stripchart_grid(self):
        self.stripchart_grid_enabled = self.ui.stripchart_grid_checkbox.isChecked()
        self.axis_x.setVisible(self.stripchart_grid_enabled)
        self.axis_y.setVisible(self.stripchart_grid_enabled)
        self.axis_x.setLabelsVisible(False)
        self.axis_y.setLabelsVisible(False)
        self.axis_x.setGridLineVisible(self.stripchart_grid_enabled)
        self.axis_y.setGridLineVisible(self.stripchart_grid_enabled)
        self.axis_x.setMinorGridLineVisible(self.stripchart_grid_enabled)
        self.axis_y.setMinorGridLineVisible(self.stripchart_grid_enabled)
        self.ui.stripchart_grid_density_slider.setVisible(self.stripchart_grid_enabled)
        self.ui.stripchart_grid_density_value_label.setVisible(
            self.stripchart_grid_enabled
        )
        self.update_stripchart_axes()

    def update_stripchart_grid_density(self):
        self.stripchart_grid_density = self.ui.stripchart_grid_density_slider.value()
        self.update_stripchart_axes()

    def enforce_min_voltage_span(self, min_voltage: float, max_voltage: float):
        """Widen a voltage window that is too narrow to read, keeping it above 0V."""
        deficit = self.stripchart_min_voltage_range - (max_voltage - min_voltage)
        if deficit > 0:
            min_voltage = max(0.0, min_voltage - deficit / 2)
            max_voltage = min_voltage + self.stripchart_min_voltage_range
        return min_voltage, max_voltage

    def calculate_stripchart_voltage_range(self):
        """Fit both ends of the axis to the data, but never show below 0V."""
        voltages = [
            point.x()
            for series in [self.stripchart_series_a, self.stripchart_series_b]
            for point in series.points()
        ]
        if not voltages:
            return 0.0, self.stripchart_min_voltage_range
        min_voltage = max(0.0, min(voltages))
        return self.enforce_min_voltage_span(
            min_voltage, max(max(voltages), min_voltage)
        )

    def update_stripchart_axes(self):
        if self.stripchart_dynamic_scale_enabled:
            min_voltage, max_voltage = self.calculate_stripchart_voltage_range()
        else:
            min_voltage, max_voltage = self.enforce_min_voltage_span(
                self.stripchart_manual_min_voltage, self.stripchart_manual_max_voltage
            )
        self.axis_x.setMin(min_voltage)
        self.axis_x.setMax(max_voltage)
        if not self.stripchart_grid_enabled:
            self.axis_x.setVisible(False)
            self.axis_y.setVisible(False)

        x_divisions = max(1, self.stripchart_grid_density)
        volts_per_div = (max_voltage - min_voltage) / x_divisions
        self.ui.stripchart_grid_density_value_label.setText(
            f"{volts_per_div:.1f} V/div"
        )

        y_range = self.axis_y.max() - self.axis_y.min()
        x_range = max_voltage - min_voltage
        plot_area = self.chart.plotArea()
        if y_range > 0 and x_range > 0 and plot_area.width() > 0 and plot_area.height() > 0:
            y_divisions = max(
                1, int(round(x_divisions * (plot_area.height() / plot_area.width())))
            )
            y_step = y_range / y_divisions
            self.axis_x.setTickType(QtCharts.QValueAxis.TickType.TicksFixed)
            self.axis_y.setTickType(QtCharts.QValueAxis.TickType.TicksDynamic)
            current_sidereal_time = self.clock.get_sidereal_seconds()
            time_scroll_offset = current_sidereal_time % self.stripchart_display_seconds
            self.axis_y.setTickAnchor(current_sidereal_time - time_scroll_offset)
            self.axis_y.setTickInterval(y_step)
            self.axis_x.setTickCount(x_divisions + 1)

    def update_voltage(self):
        if len(self.data) > 0:
            self.ui.channelA_value.setText("%.4fV" % self.data[len(self.data) - 1].a)
            self.ui.channelB_value.setText("%.4fV" % self.data[len(self.data) - 1].b)

    def handle_survey(self):
        obs = Survey()
        self.new_observation(obs)

    def handle_scan(self):
        obs = Scan()
        self.new_observation(obs)

    def handle_spectrum(self):
        obs = Spectrum()
        self.new_observation(obs)

    def new_observation(self, obs: Observation):
        dialog = ObsDialog(self, obs, self.clock)
        try:
            dialog.setWindowTitle("New " + obs.obs_type.name.capitalize())
        except AttributeError:
            pass
        dialog.exec()
        self.completed_one_calibration = False

    def handle_get_info(self):
        assert self.obs is not None
        dialog = ObsDialog(self, self.obs, self.clock, info=True)
        dialog.setWindowTitle("Current " + self.obs.obs_type.name.capitalize())
        dialog.exec()

    def dec_calibration(self):
        dialog = DecDialog(self.minitars, self)
        if self.mode is Threepio.Mode.TESTING:
            dialog.show()
        dialog.exec()

        self.dec_calc.load_dec_cal()

    def ra_calibration(self):
        dialog = RADialog(self, self.clock)
        dialog.show()
        dialog.exec()

    def message(self, message, beep=True, log=True):
        if log:
            self.log(message)
        if beep:
            self.beep(message="message")
        self.ui.message_label.setText(message)

    def log(self, message, allow_dups=False, warning=False) -> LogTask:
        new_log_task = LogTask(message)
        if (
            len(self.message_log) == 0
            or allow_dups
            or message != self.message_log[-1].message
        ):
            if warning:
                new_log_task.set_leading_str("WARNING!")
            else:
                try:
                    new_log_task.set_leading_str(
                        self.clock.get_formatted_sidereal_time()
                    )
                except AttributeError:
                    pass
            self.message_log.append(new_log_task)
            print(new_log_task.get_message())
        return new_log_task

    def update_console(self):
        """Refresh console with the latest statuses and last 7 logs"""
        number_of_logs = floor(self.ui.console_label.height() / 14)
        self.ui.console_label.setText(
            reduce(
                lambda c, a: c + "\n" + a,
                [i.get_message() for i in self.message_log[-1*number_of_logs:]],
            )
        )

    def alert(self, *alerts, callback: Callable[[], None] = lambda: None):
        new_thread = QtCore.QThread()
        self.alert_thread.add(new_thread)
        self.worker = self.AlertWorker(self)
        self.worker.moveToThread(new_thread)
        # Connect signals and slots
        new_thread.started.connect(
                lambda: self.worker is not None
                and self.worker.run(*alerts, callback=callback) # type: ignore
            )
        self.worker.finished.connect(new_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)

        def cleanup():
            self.alert_thread.remove(new_thread)
            new_thread.deleteLater()

        new_thread.finished.connect(cleanup)

        new_thread.start()

    class AlertWorker(QtCore.QObject):
        finished = QtCore.Signal()
        progress = QtCore.Signal(int)

        def __init__(self, threepio):
            super().__init__()
            self.threepio = threepio

        def run(self, *alerts, callback: Callable[[], None]):
            for alert in alerts:
                self.threepio.alert_aux(alert.text, alert.button)
            callback()
            self.finished.emit()

    def alert_aux(self, alert_text, button_text):
        self.log(alert_text)
        alert = AlertDialog(alert_text, button_text)
        self.beep(message="alert")
        alert.show()
        alert.exec()

    def beep(self, message=""):
        """Make beep play for user. Message param is only for debugging."""
        if time.time() - self.last_beep_time > 0.1:
            self.beep_sound.play()
            self.last_beep_time = time.time()
            print("beep!", message, time.time())

    def closeEvent(self, event):  # type: ignore
        """Override quit action to confirm before closing"""
        quit_dialog = QtWidgets.QDialog()
        quit_dialog.ui = quit_ui.Ui_Dialog()  # type: ignore
        quit_dialog.ui.setupUi(quit_dialog)

        quit_dialog.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowTitleHint
            | QtCore.Qt.WindowType.CustomizeWindowHint
        )

        close = quit_dialog.exec()
        if close:
            event.accept()
        else:
            event.ignore()


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QtGui.QIcon(f"assets/robot.png"))
    window = Threepio()
    window.set_state_normal()
    # window.set_state_testing()
    window.show()
    sys.exit(app.exec())  # Exit with code from app


if __name__ == "__main__":
    main()
