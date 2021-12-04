import time
from functools import reduce

from PyQt5 import QtChart, QtCore, QtGui, QtWidgets, QtMultimedia

from dialogs import AlertDialog, CreditsDialog, DecDialog, ObsDialog, RADialog
from layouts import threepio_ui, quit_ui
from tools import (
    Comm,
    DataPoint,
    Survey,
    Scan,
    Spectrum,
    SuperClock,
    Tars,
    MiniTars,
    discovery,
    LogTask,
    Observation,
)


class Threepio(QtWidgets.QMainWindow):
    """
    Green Bank Observatory's 40-Foot Telescope's very own data acquisition system.
    Extends Qt's QMainWindow class and is the main window of the application.
    """

    # basic time
    BASE_PERIOD = 10  # ms = 100Hz
    GUI_UPDATE_PERIOD = 1000  # ms = 1Hz
    STRIPCHART_PERIOD = 16.7  # ms = 60Hz
    # how many data points to draw to stripchart
    stripchart_display_seconds = 8
    should_clear_stripchart = False

    # test data
    ticker = 0
    other_ticker = 0
    foo = 0.0

    # stripchart
    stripchart_low = -1
    stripchart_high = 1

    # declination calibration lists
    x = list[float]
    y = list[float]

    # palette
    BLUE = 0x2196F3
    RED = 0xFF5252

    # tars communication interpretation
    transmission = None
    old_transmission = None

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        # use main_ui for window setup
        self.ui = threepio_ui.Ui_MainWindow()
        with open("stylesheet.qss") as f:
            self.setStyleSheet(f.read())
        self.ui.setupUi(self)
        self.setWindowTitle("threepio")

        # hide the close/minimize/fullscreen buttons
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint
        )

        # mode
        self.legacy_mode = False
        self.mode = "normal"

        # "console" output
        self.message_log: list[LogTask] = []
        self.log(">>> THREEPIO")
        self.update_console()

        # clock
        self.clock = SuperClock()
        self.set_time()

        # initialize stripchart
        stripchart_log_task = self.log("Initializing stripchart...")
        self.stripchart_series_a = QtChart.QLineSeries()
        self.stripchart_series_b = QtChart.QLineSeries()
        self.axis_y = QtChart.QValueAxis()
        self.chart = QtChart.QChart()
        self.ui.stripchart.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(QtGui.QColor(self.BLUE))
        pen.setWidth(1)
        self.stripchart_series_a.setPen(pen)
        pen.setColor(QtGui.QColor(self.RED))
        self.stripchart_series_b.setPen(pen)
        self.initialize_stripchart()  # should this include more of the above?
        stripchart_log_task.set_status(0)

        self.update_stripchart_speed()

        stripchart_log_task = self.log("Initializing buttons...")
        # connect buttons
        self.ui.stripchart_speed_slider.valueChanged.connect(
            self.update_stripchart_speed
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

        self.ui.chart_clear_button.clicked.connect(self.clear_stripchart)
        stripchart_log_task.set_status(0)

        # Tars/DATAQ
        dataq, arduino = discovery()
        self.tars = Tars(parent=self, device=dataq)
        self.tars.start()
        self.minitars = MiniTars(parent=self, device=arduino)
        self.minitars.start()

        # bleeps and bloops
        stripchart_log_task = self.log("Initializing audio...")
        self.click_sound = QtMultimedia.QSoundEffect()
        url = QtCore.QUrl()
        self.click_sound.setSource(url.fromLocalFile("assets/beep3.wav"))
        self.click_sound.setVolume(0.5)
        # self.click_sound.play()
        self.last_beep_time = 0.0
        self.tobeepornottobeep = False
        stripchart_log_task.set_status(0)

        # alerts
        self.open_alert = None

        # establish observation
        self.observation = None
        self.observation_state = False
        self.stop_tel_alert = False

        # establish data array & most recent dec
        self.data = []
        self.current_dec = 0.0
        self.current_data_point = None

        # telescope visualization
        self.dec_scene = QtWidgets.QGraphicsScene()
        self.ui.dec_view.setScene(self.dec_scene)
        self.update_dec_view()

        # run initial calibration
        self.load_dec_cal()

        # primary clock
        stripchart_log_task = self.log("Initializing clock...")
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)  # do everything
        self.timer.start(self.BASE_PERIOD)  # set refresh rate
        # assign timers to functions meant to fire periodically
        self.clock.add_timer(1000, self.update_gui)
        self.data_timer = self.clock.add_timer(1000, self.update_data)
        stripchart_log_task.set_status(0)

        # measure refresh rate
        self.time_of_last_fps_update = time.perf_counter()
        self.ticks_since_last_fps_update = 0

        # alert user that threepio is done initializing
        self.message("Ready!!!")

    def tick(self):
        """
        Primary controller for each clock tick. Fires as fast as possible up to 100Hz.
        Anything meant to update as often as possible should be placed here. Everything
        else should be assigned to a timer.
        """

        # attempt to grab latest data point; it won't always be stored
        tars_data = self.tars.read_latest()  # get data from DAQ
        minitars_data = self.minitars.read_latest()  # get data from Arduino
        sidereal_timestamp = self.clock.get_sidereal_seconds()

        # if data was available above, save it
        if tars_data is not None and minitars_data is not None:
            self.current_dec = self.calculate_declination(minitars_data)  # get dec
            self.current_data_point = DataPoint(  # create data point
                sidereal_timestamp,  # ra
                self.current_dec,  # dec
                tars_data[0][1],  # channel a
                tars_data[1][1],  # channel b
            )
            self.data.append(self.current_data_point)  # add to data list

        self.clock.run_timers()  # run all timers that are due

        # update every tick
        self.update_stripchart()
        self.update_dec_view()

        self.ticks_since_last_fps_update += 1  # for measuring fps

    def update_data(self) -> None:
        # print(
        #     f"start: {self.clock.starting_time}, "
        #     f"anchor: {self.clock.anchor_time}, "
        #     f"current: {time.time()}"
        # )
        if not self.check_observation_state():
            return

        period = 1000 / self.observation.freq  # Hz -> ms
        self.data_timer.set_period(period)

        self.old_transmission = self.transmission
        self.transmission = self.observation.communicate(
            self.current_data_point, self.clock.get_time()
        )

        obs_type = self.observation.obs_type

        if self.transmission == Comm.START_CAL:
            if obs_type == "Spectrum":
                self.alert("Set frequency to 1319.5MHz")
            if self.stop_tel_alert and self.observation.obs_type == "Survey":
                self.alert("STOP the telescope", "Okay")
                self.alert("Has the telescope been stopped?", "Yes")
            self.stop_tel_alert = True  # only alert on second cal
            self.alert("Turn the calibration switches ON", "Okay")
            self.alert("Are the calibration switches ON?", "Yes")
            self.clock.reset_anchor_time()
            self.observation.next()
            self.message("Taking calibration data!!!")
        elif self.transmission == Comm.START_BG:
            self.alert("Turn the calibration switches OFF", "Okay")
            self.alert("Are the calibration switches OFF?", "Yes")
            self.clock.reset_anchor_time()
            self.observation.next()
            self.message("Taking background data!!!")
        elif self.transmission == Comm.START_WAIT:
            self.observation.next()
            self.message(f"Waiting for {obs_type.lower()} to begin...")
        elif self.transmission == Comm.START_DATA:
            self.observation.next()
            self.message(f"Taking {obs_type.lower()} data!!!")
        elif self.transmission == Comm.FINISHED:
            self.observation.next()
            self.message(f"{obs_type} complete!!!")
            self.observation = None
        elif self.transmission == Comm.SEND_TEL_NORTH:
            self.message("Send telescope NORTH at max speed!!!", beep=False, log=False)
            self.tobeepornottobeep = True
        elif self.transmission == Comm.SEND_TEL_SOUTH:
            self.message("Send telescope SOUTH at max speed!!!", beep=False, log=False)
            self.tobeepornottobeep = True
        elif self.transmission == Comm.END_SEND_TEL:
            self.message(f"Taking {obs_type.lower()} data!!!", beep=False, log=False)
        elif self.transmission == Comm.BEEP:
            self.tobeepornottobeep = True
        elif self.transmission == Comm.NEXT:
            self.observation.next()
        elif self.transmission == Comm.NO_ACTION:
            pass

        # time_until_start = self.observation.start_RA - current_time
        # if time_until_start <= 0 < (self.observation.end_RA - current_time):
        #     self.message(f"Taking {obs_type} data!!!")

    def set_state_normal(self):
        self.ui.actionNormal.setChecked(True)
        self.ui.actionTesting.setChecked(False)
        self.ui.testing_frame.hide()
        self.adjustSize()
        self.setFixedSize(800, 640)
        self.mode = "normal"

    def set_state_testing(self):
        self.ui.actionNormal.setChecked(False)
        self.ui.actionTesting.setChecked(True)
        self.setFixedSize(800, 826)
        self.ui.testing_frame.show()
        self.mode = "testing"

    def toggle_state_legacy(self):
        """lol"""
        self.legacy_mode = not self.legacy_mode
        self.setStyleSheet(
            "background-color:#00ff00; color:#ff0000" if self.legacy_mode else ""
        )
        url = QtCore.QUrl()
        self.click_sound.setSource(
            url.fromLocalFile(
                f"assets/beep{'-legacy' if self.legacy_mode else '3'}.wav"
            )
        )
        self.ui.actionLegacy.setChecked(self.legacy_mode)

    def check_observation_state(self) -> bool:
        if (
            self.observation_state
            and self.observation is None
            or not self.observation_state
            and self.observation is not None
        ):
            self.toggle_observation_state()

        return self.observation_state

    def toggle_observation_state(self) -> None:
        # disable resetting RA/Dec after loading obs
        self.observation_state = not self.observation_state
        for a in (
            self.ui.actionRA,
            self.ui.actionDec,
            self.ui.actionSurvey,
            self.ui.actionScan,
            self.ui.actionSpectrum,
        ):
            a.setDisabled(self.observation_state)
        self.ui.actionGetInfo.setEnabled(self.observation_state)

    @staticmethod
    def handle_credits():
        dialog = CreditsDialog()
        dialog.exec_()

    def set_time(self):
        dialog = RADialog(self, self.clock)
        dialog.show()
        dialog.exec_()

    def update_stripchart_speed(self):
        self.stripchart_display_seconds = 120 - (
            (110 / 6) * self.ui.stripchart_speed_slider.value()
        )

    def update_gui(self):
        # current_time = self.clock.get_time()
        if self.tobeepornottobeep:
            self.beep(message="update_gui")
            self.tobeepornottobeep = False

        self.ui.ra_value.setText(self.clock.get_formatted_sidereal_time())  # RA
        self.ui.dec_value.setText(f"{self.current_dec:.4f}°")  # dec
        if self.observation is not None:
            self.ui.sweep_value.setText(
                f"{self.observation.sweeps if self.observation.sweeps != -1 else 'n/a'}"
            )  # sweep number

        self.update_progress_bar()

        self.update_fps()

        self.update_console()

        self.update_voltage()

    def update_progress_bar(self):
        # T=start_RA
        if self.observation is not None:
            # if not self.observation.end_RA - self.observation.start_RA <= 1:
            if (
                self.clock.get_time_until(self.observation.start_RA)
                > 0
                > self.clock.get_time_until(self.observation.end_RA)
            ):  # between start and end time
                self.ui.progressBar.setValue(
                    int(
                        (
                            self.clock.get_time_until(self.observation.end_RA)
                            / (self.observation.end_RA - self.observation.start_RA)
                        )
                        * 100
                        % 100
                    )
                )
            else:
                self.ui.progressBar.setValue(0)

            # display the time nicely
            tus = self.clock.get_time_until(
                self.observation.start_RA
            )  # time until start
            hours = int((abs_tus := abs(tus)) / 3600)
            minutes = int((abs_tus - (hours * 3600)) / 60)
            seconds = int(abs_tus - (hours * 3600) - (minutes * 60))
            self.ui.progressBar.setFormat(
                "T"
                + ("-" if tus < 0 else "+")
                + ("{:0>2}".format(hours) + ":" if hours != 0 else "")
                + ("{:0>2}".format(minutes) + ":" if minutes != 0 else "")
                + "{:0>2}".format(seconds)
            )
            return

        self.ui.progressBar.setFormat("n/a")
        self.ui.progressBar.setValue(0)

    def update_dec_view(self):
        angle = self.current_dec - self.clock.GB_LATITUDE

        # telescope dish
        dish = QtGui.QPixmap("assets/dish.png")
        dish = QtWidgets.QGraphicsPixmapItem(dish)
        dish.setTransformOriginPoint(32, 32)
        dish.setTransformationMode(QtCore.Qt.SmoothTransformation)
        dish.setY(16)
        dish.setRotation(angle)

        # telescope base
        base = QtGui.QPixmap("assets/base.png")
        base = QtWidgets.QGraphicsPixmapItem(base)
        base.setTransformationMode(QtCore.Qt.SmoothTransformation)

        self.dec_scene.clear()
        for i in [dish, base]:
            self.dec_scene.addItem(i)

    def update_fps(self):
        """updates the fps counter to display current refresh rate"""
        current_time = time.perf_counter()
        time_since_last_fps_update = current_time - self.time_of_last_fps_update

        try:
            new_fps = "%.2fHz" % (
                self.ticks_since_last_fps_update / time_since_last_fps_update
            )
        except ZeroDivisionError:
            new_fps = -1.0

        self.ui.refresh_value.setText(new_fps)
        self.time_of_last_fps_update = current_time
        self.ticks_since_last_fps_update = 0

    def initialize_stripchart(self):
        self.chart.addSeries(self.stripchart_series_b)
        self.chart.addSeries(self.stripchart_series_a)

        self.chart.legend().hide()

        self.ui.stripchart.setChart(self.chart)

    def update_stripchart(self):
        try:
            # parse latest data point
            # TODO: this will duplicate points if one fails to read
            new_a = self.data[len(self.data) - 1].a
            new_b = self.data[len(self.data) - 1].b
            new_ra = self.data[len(self.data) - 1].timestamp

            # add new data point to both series
            self.stripchart_series_a.append(new_a, new_ra)
            self.stripchart_series_b.append(new_b, new_ra)

            # we use these value several times
            current_sideral_seconds = self.clock.get_sidereal_seconds()
            oldest_y = current_sideral_seconds - self.stripchart_display_seconds

            # remove the trailing end of the series
            clear_it = self.should_clear_stripchart  # prevents a race hazard?
            for i in [self.stripchart_series_a, self.stripchart_series_b]:
                if clear_it:
                    i.clear()
                elif i.count() > 2 and i.at(1).y() < oldest_y:
                    i.removePoints(0, 2)
            self.should_clear_stripchart = False

            # These lines are required to prevent a Qt error
            self.chart.removeSeries(self.stripchart_series_b)
            self.chart.removeSeries(self.stripchart_series_a)
            self.chart.addSeries(self.stripchart_series_b)
            self.chart.addSeries(self.stripchart_series_a)

            axis_y = QtChart.QValueAxis()
            axis_y.setMin(oldest_y)
            axis_y.setMax(current_sideral_seconds)
            axis_y.setVisible(False)

            self.chart.setAxisY(axis_y)
            self.stripchart_series_a.attachAxis(axis_y)
            self.stripchart_series_b.attachAxis(axis_y)
        except IndexError:  # no data yet
            pass

    def clear_stripchart(self):
        self.should_clear_stripchart = True

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
        dialog.setWindowTitle("New " + obs.obs_type)
        dialog.exec_()
        self.stop_tel_alert = False

    def handle_get_info(self):
        if self.observation is not None:
            pass
        dialog = ObsDialog(self, self.observation, self.clock, info=True)
        dialog.setWindowTitle("Current " + self.observation.obs_type)
        dialog.exec_()

    def dec_calibration(self):
        dialog = DecDialog(self.minitars, self)
        if self.mode == "testing":
            dialog.show()
        dialog.exec_()

        self.load_dec_cal()

    def load_dec_cal(self):
        """read the dec calibration from file and store it in memory"""
        # create y array
        self.y = []
        i = DecDialog.south_dec
        while i <= DecDialog.north_dec:
            self.y.append(float(i))
            i += abs(DecDialog.step)

        # create x array
        self.x = []
        with open("dec-cal.txt", "r") as f:  # get data from file
            c = f.read().splitlines()
            for i in c:
                self.x.append(float(i))

    def calculate_declination(self, input_dec: float):
        """calculate the true dec from declinometer input and calibration data"""

        # input is below data
        if input_dec < self.x[0]:
            return (
                (self.y[1] - self.y[0])
                / (self.x[1] - self.x[0])
                * (input_dec - self.x[0])
            ) + self.y[0]

        # input is above data
        if input_dec > self.x[-1]:
            return (
                (self.y[-1] - self.y[-2])
                / (self.x[-1] - self.x[-2])
                * (input_dec - self.x[-1])
            ) + self.y[-1]

        # input is within data
        for i in range(len(self.x)):
            if input_dec <= self.x[i + 1]:
                if input_dec >= self.x[i]:
                    # (dy/dx)x + y_0
                    return (
                        (self.y[i + 1] - self.y[i])
                        / (self.x[i + 1] - self.x[i])
                        * (input_dec - self.x[i])
                    ) + self.y[i]

    def ra_calibration(self):
        self.set_time()

    def message(self, message, beep=True, log=True):
        if log:
            self.log(message)
        if beep:
            self.beep(message="message")
        self.ui.message_label.setText(message)

    def log(self, message, allow_dups=False) -> LogTask:
        if (
            len(self.message_log) == 0
            or allow_dups
            or message != self.message_log[-1].message
        ):
            new_log_task = LogTask(message)
            try:
                new_log_task.set_sidereal_str(self.clock.get_formatted_sidereal_time())
            except AttributeError:
                pass
            self.message_log.append(new_log_task)
            return new_log_task

    def update_console(self):
        """refresh console with the latest statuses and last 7 logs"""
        self.ui.console_label.setText(
            reduce(
                lambda c, a: c + "\n" + a,
                [i.get_message() for i in self.message_log[-7:]],
            )
        )

    def alert(self, message, button_message="Close"):
        self.log(message)
        alert = AlertDialog(message, button_message)
        self.beep(message="alert")
        alert.show()
        alert.exec_()

    # noinspection PyUnusedLocal
    def beep(self, message=""):
        """message is for debugging"""
        self.click_sound.play()
        self.last_beep_time = time.time()
        # print("beep!", message, time.time())

    def closeEvent(self, event):
        """override quit action to confirm before closing"""
        m = QtWidgets.QDialog()
        m.ui = quit_ui.Ui_Dialog()
        m.ui.setupUi(m)

        m.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint
        )

        close = m.exec()
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
    sys.exit(app.exec_())  # exit with code from app


if __name__ == "__main__":
    main()
