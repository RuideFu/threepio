from PyQt5 import QtWidgets, QtCore

from layouts import dec_cal_ui  # compiled PyQt dialogue ui


class DecDialog(QtWidgets.QDialog):
    """New observation dialogue window"""

    south_dec = -25
    north_dec = 95
    step = 10

    CAL_FILENAME = "dec-cal.txt"
    CAL_BACKUP_FILENAME = "dec-cal-backup.txt"

    def __init__(self, tars):
        QtWidgets.QWidget.__init__(self)
        self.ui = dec_cal_ui.Ui_Dialog()
        self.ui.setupUi(self)
        self.setModal(False)
        self.setWindowTitle("Calibrate declination")

        # hide the close/minimize/fullscreen buttons
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint
        )

        self.data = []
        self.current_dec = self.south_dec
        self.ui.set_dec_value.setText(str(self.current_dec))

        self.tars = tars

        # connect buttons
        self.ui.discard_cal_button.clicked.connect(self.handle_discard)
        self.ui.next_cal_button.clicked.connect(self.handle_next)
        self.ui.north_or_south_combo_box.currentIndexChanged.connect(
            self.switch_direction
        )

        # self.handle_next()

    def switch_direction(self):
        if self.ui.north_or_south_combo_box.currentIndex() == 0:
            self.current_dec = self.south_dec
            self.step = 10
        else:
            self.current_dec = self.north_dec
            self.step = -10
        self.ui.set_dec_value.setText(str(self.current_dec))

    def handle_next(self):
        # read just the declination value
        self.data.append(self.tars.read_latest()[2][1])

        self.current_dec += self.step
        if self.current_dec not in [self.south_dec, self.north_dec]:
            # disable N/S choice if not first
            self.ui.north_or_south_combo_box.setDisabled(True)
        elif self.current_dec <= self.south_dec or self.current_dec >= self.north_dec:
            self.ui.next_cal_button.setText("Save")

        self.ui.set_dec_value.setText(str(self.current_dec))

        # is calibration complete?
        if self.current_dec > self.north_dec or self.current_dec < self.south_dec:
            # copy over the current file to the backup file
            with open(self.CAL_FILENAME) as f, open(self.CAL_BACKUP_FILENAME, "w") as b:
                for line in f:
                    b.write(line)

            open(self.CAL_FILENAME, "w").close()  # overwrite file
            with open(self.CAL_FILENAME, "a") as f:
                # reverse it if it's N -> S
                self.step < 0 and self.data.reverse()

                f.write('\n'.join(str(line) for line in self.data))

            self.close()

    def handle_discard(self):
        self.close()
