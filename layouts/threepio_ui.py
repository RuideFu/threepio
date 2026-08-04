# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'threepio.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCharts import QChartView
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QDial,
    QFrame, QGraphicsView, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QMainWindow, QMenu,
    QMenuBar, QProgressBar, QPushButton, QSizePolicy,
    QSlider, QSpacerItem, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(860, 1004)
        MainWindow.setMinimumSize(QSize(860, 900))
        MainWindow.setAutoFillBackground(True)
        self.actionRA = QAction(MainWindow)
        self.actionRA.setObjectName(u"actionRA")
        self.actionDec = QAction(MainWindow)
        self.actionDec.setObjectName(u"actionDec")
        self.actionSurvey = QAction(MainWindow)
        self.actionSurvey.setObjectName(u"actionSurvey")
        self.actionInfo = QAction(MainWindow)
        self.actionInfo.setObjectName(u"actionInfo")
        self.actionQuit = QAction(MainWindow)
        self.actionQuit.setObjectName(u"actionQuit")
        self.actionHelp = QAction(MainWindow)
        self.actionHelp.setObjectName(u"actionHelp")
        self.actionHelp.setEnabled(False)
        self.actionScan = QAction(MainWindow)
        self.actionScan.setObjectName(u"actionScan")
        self.actionSpectrum = QAction(MainWindow)
        self.actionSpectrum.setObjectName(u"actionSpectrum")
        self.actionNormal = QAction(MainWindow)
        self.actionNormal.setObjectName(u"actionNormal")
        self.actionNormal.setCheckable(True)
        self.actionTesting = QAction(MainWindow)
        self.actionTesting.setObjectName(u"actionTesting")
        self.actionTesting.setCheckable(True)
        self.actionLegacy = QAction(MainWindow)
        self.actionLegacy.setObjectName(u"actionLegacy")
        self.actionLegacy.setCheckable(True)
        self.actionGetInfo = QAction(MainWindow)
        self.actionGetInfo.setObjectName(u"actionGetInfo")
        self.actionGetInfo.setEnabled(False)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.testing_frame = QFrame(self.centralwidget)
        self.testing_frame.setObjectName(u"testing_frame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.testing_frame.sizePolicy().hasHeightForWidth())
        self.testing_frame.setSizePolicy(sizePolicy)
        self.testing_frame.setMinimumSize(QSize(0, 180))
        self.gridLayout_8 = QGridLayout(self.testing_frame)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.gridLayout_8.setContentsMargins(-1, 0, -1, -1)
        self.dec_group_box = QGroupBox(self.testing_frame)
        self.dec_group_box.setObjectName(u"dec_group_box")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.dec_group_box.sizePolicy().hasHeightForWidth())
        self.dec_group_box.setSizePolicy(sizePolicy1)
        self.gridLayout_9 = QGridLayout(self.dec_group_box)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.north_label = QLabel(self.dec_group_box)
        self.north_label.setObjectName(u"north_label")
        self.north_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.gridLayout_9.addWidget(self.north_label, 0, 1, 1, 1)

        self.south_label = QLabel(self.dec_group_box)
        self.south_label.setObjectName(u"south_label")
        self.south_label.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)

        self.gridLayout_9.addWidget(self.south_label, 1, 1, 1, 1)

        self.declination_slider = QSlider(self.dec_group_box)
        self.declination_slider.setObjectName(u"declination_slider")
        self.declination_slider.setMinimum(-99)
        self.declination_slider.setMaximum(99)
        self.declination_slider.setSingleStep(1)
        self.declination_slider.setValue(0)
        self.declination_slider.setTickInterval(20)

        self.gridLayout_9.addWidget(self.declination_slider, 0, 0, 2, 1)

        self.dec_auto_check_box = QCheckBox(self.dec_group_box)
        self.dec_auto_check_box.setObjectName(u"dec_auto_check_box")
        self.dec_auto_check_box.setChecked(True)

        self.gridLayout_9.addWidget(self.dec_auto_check_box, 2, 0, 1, 2)


        self.gridLayout_8.addWidget(self.dec_group_box, 0, 1, 1, 1)

        self.signal_group_box = QGroupBox(self.testing_frame)
        self.signal_group_box.setObjectName(u"signal_group_box")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.signal_group_box.sizePolicy().hasHeightForWidth())
        self.signal_group_box.setSizePolicy(sizePolicy2)
        self.gridLayout_6 = QGridLayout(self.signal_group_box)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.polarization_label = QLabel(self.signal_group_box)
        self.polarization_label.setObjectName(u"polarization_label")
        self.polarization_label.setAlignment(Qt.AlignCenter)

        self.gridLayout_6.addWidget(self.polarization_label, 3, 2, 1, 1)

        self.noise_label = QLabel(self.signal_group_box)
        self.noise_label.setObjectName(u"noise_label")
        self.noise_label.setAlignment(Qt.AlignCenter)

        self.gridLayout_6.addWidget(self.noise_label, 3, 3, 1, 1)

        self.variance_label = QLabel(self.signal_group_box)
        self.variance_label.setObjectName(u"variance_label")
        self.variance_label.setAlignment(Qt.AlignCenter)

        self.gridLayout_6.addWidget(self.variance_label, 3, 0, 1, 1)

        self.variance_dial = QDial(self.signal_group_box)
        self.variance_dial.setObjectName(u"variance_dial")
        self.variance_dial.setMinimum(0)
        self.variance_dial.setMaximum(16)
        self.variance_dial.setPageStep(4)
        self.variance_dial.setValue(4)
        self.variance_dial.setWrapping(False)
        self.variance_dial.setNotchTarget(1.000000000000000)
        self.variance_dial.setNotchesVisible(True)

        self.gridLayout_6.addWidget(self.variance_dial, 1, 0, 1, 1)

        self.noise_dial = QDial(self.signal_group_box)
        self.noise_dial.setObjectName(u"noise_dial")
        self.noise_dial.setMinimum(0)
        self.noise_dial.setMaximum(16)
        self.noise_dial.setPageStep(4)
        self.noise_dial.setValue(4)
        self.noise_dial.setWrapping(False)
        self.noise_dial.setNotchTarget(1.000000000000000)
        self.noise_dial.setNotchesVisible(True)

        self.gridLayout_6.addWidget(self.noise_dial, 1, 3, 1, 1)

        self.polarization_dial = QDial(self.signal_group_box)
        self.polarization_dial.setObjectName(u"polarization_dial")
        self.polarization_dial.setMinimum(0)
        self.polarization_dial.setMaximum(16)
        self.polarization_dial.setPageStep(4)
        self.polarization_dial.setValue(4)
        self.polarization_dial.setWrapping(False)
        self.polarization_dial.setNotchTarget(1.000000000000000)
        self.polarization_dial.setNotchesVisible(True)

        self.gridLayout_6.addWidget(self.polarization_dial, 1, 2, 1, 1)

        self.calibration_check_box = QCheckBox(self.signal_group_box)
        self.calibration_check_box.setObjectName(u"calibration_check_box")

        self.gridLayout_6.addWidget(self.calibration_check_box, 1, 4, 3, 1)


        self.gridLayout_8.addWidget(self.signal_group_box, 0, 0, 1, 1)


        self.gridLayout.addWidget(self.testing_frame, 1, 0, 1, 1)

        self.main_frame = QFrame(self.centralwidget)
        self.main_frame.setObjectName(u"main_frame")
        self.gridLayout_7 = QGridLayout(self.main_frame)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.data_display_group = QGroupBox(self.main_frame)
        self.data_display_group.setObjectName(u"data_display_group")
        self.gridLayout_2 = QGridLayout(self.data_display_group)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.channelA_value = QLabel(self.data_display_group)
        self.channelA_value.setObjectName(u"channelA_value")
        palette = QPalette()
        brush = QBrush(QColor(33, 150, 243, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, brush)
        brush1 = QBrush(QColor(127, 127, 127, 255))
        brush1.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, brush1)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, brush1)
        self.channelA_value.setPalette(palette)
        font = QFont()
        font.setFamilies([u"Iosevka Aile"])
        font.setPointSize(20)
        font.setBold(True)
        self.channelA_value.setFont(font)
        self.channelA_value.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.channelA_value, 3, 1, 1, 2)

        self.sweep_label = QLabel(self.data_display_group)
        self.sweep_label.setObjectName(u"sweep_label")
        font1 = QFont()
        font1.setPointSize(20)
        self.sweep_label.setFont(font1)

        self.gridLayout_2.addWidget(self.sweep_label, 5, 0, 1, 1)

        self.channelB_value = QLabel(self.data_display_group)
        self.channelB_value.setObjectName(u"channelB_value")
        palette1 = QPalette()
        brush2 = QBrush(QColor(255, 82, 82, 255))
        brush2.setStyle(Qt.BrushStyle.SolidPattern)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush2)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, brush2)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush2)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, brush2)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, brush1)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, brush1)
        self.channelB_value.setPalette(palette1)
        self.channelB_value.setFont(font)
        self.channelB_value.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.channelB_value, 4, 1, 1, 2)

        self.ra_value = QLabel(self.data_display_group)
        self.ra_value.setObjectName(u"ra_value")
        self.ra_value.setFont(font)
        self.ra_value.setScaledContents(False)
        self.ra_value.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.ra_value, 1, 1, 1, 2)

        self.channelA_label = QLabel(self.data_display_group)
        self.channelA_label.setObjectName(u"channelA_label")
        self.channelA_label.setFont(font1)

        self.gridLayout_2.addWidget(self.channelA_label, 3, 0, 1, 1)

        self.sweep_value = QLabel(self.data_display_group)
        self.sweep_value.setObjectName(u"sweep_value")
        self.sweep_value.setFont(font)
        self.sweep_value.setScaledContents(False)
        self.sweep_value.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.sweep_value, 5, 2, 1, 1)

        self.dec_label = QLabel(self.data_display_group)
        self.dec_label.setObjectName(u"dec_label")
        self.dec_label.setFont(font1)

        self.gridLayout_2.addWidget(self.dec_label, 2, 0, 1, 1)

        self.dec_value = QLabel(self.data_display_group)
        self.dec_value.setObjectName(u"dec_value")
        self.dec_value.setFont(font)
        self.dec_value.setScaledContents(False)
        self.dec_value.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_2.addWidget(self.dec_value, 2, 1, 1, 2)

        self.channelB_label = QLabel(self.data_display_group)
        self.channelB_label.setObjectName(u"channelB_label")
        self.channelB_label.setFont(font1)

        self.gridLayout_2.addWidget(self.channelB_label, 4, 0, 1, 1)

        self.ra_label = QLabel(self.data_display_group)
        self.ra_label.setObjectName(u"ra_label")
        self.ra_label.setFont(font1)

        self.gridLayout_2.addWidget(self.ra_label, 1, 0, 1, 1)


        self.gridLayout_7.addWidget(self.data_display_group, 1, 0, 1, 1)

        self.stripchart_control_group = QGroupBox(self.main_frame)
        self.stripchart_control_group.setObjectName(u"stripchart_control_group")
        self.gridLayout_4 = QGridLayout(self.stripchart_control_group)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.stripchart_speed_label = QLabel(self.stripchart_control_group)
        self.stripchart_speed_label.setObjectName(u"stripchart_speed_label")
        self.stripchart_speed_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_4.addWidget(self.stripchart_speed_label, 0, 0, 1, 1)

        self.stripchart_speed_slider = QSlider(self.stripchart_control_group)
        self.stripchart_speed_slider.setObjectName(u"stripchart_speed_slider")
        self.stripchart_speed_slider.setMaximum(1000)
        self.stripchart_speed_slider.setValue(500)
        self.stripchart_speed_slider.setOrientation(Qt.Horizontal)
        self.stripchart_speed_slider.setTickPosition(QSlider.NoTicks)

        self.gridLayout_4.addWidget(self.stripchart_speed_slider, 0, 1, 1, 1)

        self.stripchart_speed_value_label = QLabel(self.stripchart_control_group)
        self.stripchart_speed_value_label.setObjectName(u"stripchart_speed_value_label")
        self.stripchart_speed_value_label.setMinimumSize(QSize(56, 0))
        self.stripchart_speed_value_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_4.addWidget(self.stripchart_speed_value_label, 0, 2, 1, 1)

        self.stripchart_voltage_label = QLabel(self.stripchart_control_group)
        self.stripchart_voltage_label.setObjectName(u"stripchart_voltage_label")
        self.stripchart_voltage_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_4.addWidget(self.stripchart_voltage_label, 1, 0, 1, 1)

        self.stripchart_voltage_layout = QHBoxLayout()
        self.stripchart_voltage_layout.setSpacing(8)
        self.stripchart_voltage_layout.setObjectName(u"stripchart_voltage_layout")
        self.stripchart_dynamic_scale_checkbox = QCheckBox(self.stripchart_control_group)
        self.stripchart_dynamic_scale_checkbox.setObjectName(u"stripchart_dynamic_scale_checkbox")
        self.stripchart_dynamic_scale_checkbox.setChecked(True)

        self.stripchart_voltage_layout.addWidget(self.stripchart_dynamic_scale_checkbox)

        self.stripchart_max_voltage_slider = QSlider(self.stripchart_control_group)
        self.stripchart_max_voltage_slider.setObjectName(u"stripchart_max_voltage_slider")
        self.stripchart_max_voltage_slider.setMinimum(1)
        self.stripchart_max_voltage_slider.setMaximum(15)
        self.stripchart_max_voltage_slider.setValue(5)
        self.stripchart_max_voltage_slider.setOrientation(Qt.Horizontal)
        self.stripchart_max_voltage_slider.setTickPosition(QSlider.TicksBelow)
        self.stripchart_max_voltage_slider.setTickInterval(1)

        self.stripchart_voltage_layout.addWidget(self.stripchart_max_voltage_slider)

        self.stripchart_voltage_layout.setStretch(1, 1)

        self.gridLayout_4.addLayout(self.stripchart_voltage_layout, 1, 1, 1, 1)

        self.stripchart_max_voltage_value_label = QLabel(self.stripchart_control_group)
        self.stripchart_max_voltage_value_label.setObjectName(u"stripchart_max_voltage_value_label")
        self.stripchart_max_voltage_value_label.setMinimumSize(QSize(56, 0))
        self.stripchart_max_voltage_value_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_4.addWidget(self.stripchart_max_voltage_value_label, 1, 2, 1, 1)

        self.stripchart_grid_label = QLabel(self.stripchart_control_group)
        self.stripchart_grid_label.setObjectName(u"stripchart_grid_label")
        self.stripchart_grid_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_4.addWidget(self.stripchart_grid_label, 2, 0, 1, 1)

        self.stripchart_grid_layout = QHBoxLayout()
        self.stripchart_grid_layout.setSpacing(8)
        self.stripchart_grid_layout.setObjectName(u"stripchart_grid_layout")
        self.stripchart_grid_checkbox = QCheckBox(self.stripchart_control_group)
        self.stripchart_grid_checkbox.setObjectName(u"stripchart_grid_checkbox")

        self.stripchart_grid_layout.addWidget(self.stripchart_grid_checkbox)

        self.stripchart_grid_density_slider = QSlider(self.stripchart_control_group)
        self.stripchart_grid_density_slider.setObjectName(u"stripchart_grid_density_slider")
        self.stripchart_grid_density_slider.setMinimum(2)
        self.stripchart_grid_density_slider.setMaximum(24)
        self.stripchart_grid_density_slider.setValue(8)
        self.stripchart_grid_density_slider.setOrientation(Qt.Horizontal)
        self.stripchart_grid_density_slider.setTickPosition(QSlider.TicksBelow)
        self.stripchart_grid_density_slider.setTickInterval(1)

        self.stripchart_grid_layout.addWidget(self.stripchart_grid_density_slider)

        self.stripchart_grid_layout.setStretch(1, 1)

        self.gridLayout_4.addLayout(self.stripchart_grid_layout, 2, 1, 1, 1)

        self.stripchart_grid_density_value_label = QLabel(self.stripchart_control_group)
        self.stripchart_grid_density_value_label.setObjectName(u"stripchart_grid_density_value_label")
        self.stripchart_grid_density_value_label.setMinimumSize(QSize(56, 0))
        self.stripchart_grid_density_value_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_4.addWidget(self.stripchart_grid_density_value_label, 2, 2, 1, 1)

        self.stripchart_channels_label = QLabel(self.stripchart_control_group)
        self.stripchart_channels_label.setObjectName(u"stripchart_channels_label")
        self.stripchart_channels_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_4.addWidget(self.stripchart_channels_label, 3, 0, 1, 1)

        self.stripchart_actions_layout = QHBoxLayout()
        self.stripchart_actions_layout.setSpacing(8)
        self.stripchart_actions_layout.setObjectName(u"stripchart_actions_layout")
        self.channel_dual_button = QPushButton(self.stripchart_control_group)
        self.channel_button_group = QButtonGroup(MainWindow)
        self.channel_button_group.setObjectName(u"channel_button_group")
        self.channel_button_group.addButton(self.channel_dual_button)
        self.channel_dual_button.setObjectName(u"channel_dual_button")
        self.channel_dual_button.setCheckable(True)
        self.channel_dual_button.setChecked(True)

        self.stripchart_actions_layout.addWidget(self.channel_dual_button)

        self.channel_a_button = QPushButton(self.stripchart_control_group)
        self.channel_button_group.addButton(self.channel_a_button)
        self.channel_a_button.setObjectName(u"channel_a_button")
        self.channel_a_button.setCheckable(True)

        self.stripchart_actions_layout.addWidget(self.channel_a_button)

        self.channel_b_button = QPushButton(self.stripchart_control_group)
        self.channel_button_group.addButton(self.channel_b_button)
        self.channel_b_button.setObjectName(u"channel_b_button")
        self.channel_b_button.setCheckable(True)

        self.stripchart_actions_layout.addWidget(self.channel_b_button)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.stripchart_actions_layout.addItem(self.horizontalSpacer_6)

        self.chart_clear_button = QPushButton(self.stripchart_control_group)
        self.chart_clear_button.setObjectName(u"chart_clear_button")

        self.stripchart_actions_layout.addWidget(self.chart_clear_button)

        self.stripchart_actions_layout.setStretch(3, 1)

        self.gridLayout_4.addLayout(self.stripchart_actions_layout, 3, 1, 1, 2)

        self.gridLayout_4.setColumnStretch(1, 1)

        self.gridLayout_7.addWidget(self.stripchart_control_group, 2, 0, 1, 1)

        self.console_background = QFrame(self.main_frame)
        self.console_background.setObjectName(u"console_background")
        self.gridLayout_11 = QGridLayout(self.console_background)
        self.gridLayout_11.setObjectName(u"gridLayout_11")
        self.gridLayout_11.setContentsMargins(0, -1, 0, -1)
        self.console_inner_frame_2 = QFrame(self.console_background)
        self.console_inner_frame_2.setObjectName(u"console_inner_frame_2")
        self.console_inner_frame_2.setStyleSheet(u"background: black; border-radius: 5px")
        self.gridLayout_12 = QGridLayout(self.console_inner_frame_2)
        self.gridLayout_12.setObjectName(u"gridLayout_12")
        self.console_label = QLabel(self.console_inner_frame_2)
        self.console_label.setObjectName(u"console_label")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.console_label.sizePolicy().hasHeightForWidth())
        self.console_label.setSizePolicy(sizePolicy3)
        font2 = QFont()
        font2.setFamilies([u"Iosevka Aile"])
        font2.setPointSize(10)
        font2.setBold(True)
        self.console_label.setFont(font2)
        self.console_label.setStyleSheet(u"color: #0f0")
        self.console_label.setAlignment(Qt.AlignBottom|Qt.AlignLeading|Qt.AlignLeft)

        self.gridLayout_12.addWidget(self.console_label, 0, 0, 1, 1)

        self.dec_view = QGraphicsView(self.console_inner_frame_2)
        self.dec_view.setObjectName(u"dec_view")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.dec_view.sizePolicy().hasHeightForWidth())
        self.dec_view.setSizePolicy(sizePolicy4)
        self.dec_view.setStyleSheet(u"background: transparent")
        self.dec_view.setFrameShape(QFrame.NoFrame)
        self.dec_view.setFrameShadow(QFrame.Plain)
        self.dec_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dec_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dec_view.setRenderHints(QPainter.Antialiasing|QPainter.TextAntialiasing)

        self.gridLayout_12.addWidget(self.dec_view, 0, 1, 1, 1)


        self.gridLayout_11.addWidget(self.console_inner_frame_2, 0, 0, 1, 1)


        self.gridLayout_7.addWidget(self.console_background, 3, 0, 1, 1)

        self.message_group_box = QGroupBox(self.main_frame)
        self.message_group_box.setObjectName(u"message_group_box")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(4)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.message_group_box.sizePolicy().hasHeightForWidth())
        self.message_group_box.setSizePolicy(sizePolicy5)
        self.gridLayout_5 = QGridLayout(self.message_group_box)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.refresh_value = QLabel(self.message_group_box)
        self.refresh_value.setObjectName(u"refresh_value")
        font3 = QFont()
        font3.setFamilies([u"Iosevka Aile"])
        font3.setBold(True)
        self.refresh_value.setFont(font3)
        self.refresh_value.setStyleSheet(u"color: #7a7c7e")
        self.refresh_value.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gridLayout_5.addWidget(self.refresh_value, 2, 1, 1, 1)

        self.message_label = QLabel(self.message_group_box)
        self.message_label.setObjectName(u"message_label")
        self.message_label.setFont(font1)

        self.gridLayout_5.addWidget(self.message_label, 0, 0, 1, 2)

        self.progressBar = QProgressBar(self.message_group_box)
        self.progressBar.setObjectName(u"progressBar")
        font4 = QFont()
        font4.setFamilies([u"Iosevka Aile"])
        font4.setPointSize(16)
        self.progressBar.setFont(font4)
        self.progressBar.setMaximum(1000)
        self.progressBar.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.progressBar.setInvertedAppearance(False)

        self.gridLayout_5.addWidget(self.progressBar, 1, 0, 1, 2)

        self.refresh_label = QLabel(self.message_group_box)
        self.refresh_label.setObjectName(u"refresh_label")
        self.refresh_label.setStyleSheet(u"color: #7a7c7e")

        self.gridLayout_5.addWidget(self.refresh_label, 2, 0, 1, 1)


        self.gridLayout_7.addWidget(self.message_group_box, 0, 0, 1, 1)

        self.output_frame = QFrame(self.main_frame)
        self.output_frame.setObjectName(u"output_frame")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy6.setHorizontalStretch(5)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.output_frame.sizePolicy().hasHeightForWidth())
        self.output_frame.setSizePolicy(sizePolicy6)
        self.output_frame.setMinimumSize(QSize(360, 0))
        self.gridLayout_10 = QGridLayout(self.output_frame)
        self.gridLayout_10.setObjectName(u"gridLayout_10")
        self.gridLayout_10.setContentsMargins(0, 0, 0, 0)
        self.stripchart = QChartView(self.output_frame)
        self.stripchart.setObjectName(u"stripchart")
        self.stripchart.setFrameShape(QFrame.NoFrame)
        self.stripchart.setFrameShadow(QFrame.Plain)

        self.gridLayout_10.addWidget(self.stripchart, 0, 0, 1, 1)


        self.gridLayout_7.addWidget(self.output_frame, 0, 2, 4, 1)


        self.gridLayout.addWidget(self.main_frame, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menuCalibration = QMenu(self.menubar)
        self.menuCalibration.setObjectName(u"menuCalibration")
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuMode = QMenu(self.menubar)
        self.menuMode.setObjectName(u"menuMode")
        self.menuObservation = QMenu(self.menubar)
        self.menuObservation.setObjectName(u"menuObservation")
        MainWindow.setMenuBar(self.menubar)
        QWidget.setTabOrder(self.stripchart_speed_slider, self.stripchart_dynamic_scale_checkbox)
        QWidget.setTabOrder(self.stripchart_dynamic_scale_checkbox, self.stripchart_max_voltage_slider)
        QWidget.setTabOrder(self.stripchart_max_voltage_slider, self.stripchart_grid_checkbox)
        QWidget.setTabOrder(self.stripchart_grid_checkbox, self.stripchart_grid_density_slider)
        QWidget.setTabOrder(self.stripchart_grid_density_slider, self.channel_dual_button)
        QWidget.setTabOrder(self.channel_dual_button, self.channel_a_button)
        QWidget.setTabOrder(self.channel_a_button, self.channel_b_button)
        QWidget.setTabOrder(self.channel_b_button, self.chart_clear_button)
        QWidget.setTabOrder(self.chart_clear_button, self.dec_view)
        QWidget.setTabOrder(self.dec_view, self.variance_dial)
        QWidget.setTabOrder(self.variance_dial, self.polarization_dial)
        QWidget.setTabOrder(self.polarization_dial, self.noise_dial)
        QWidget.setTabOrder(self.noise_dial, self.calibration_check_box)
        QWidget.setTabOrder(self.calibration_check_box, self.declination_slider)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuObservation.menuAction())
        self.menubar.addAction(self.menuCalibration.menuAction())
        self.menubar.addAction(self.menuMode.menuAction())
        self.menuCalibration.addAction(self.actionRA)
        self.menuCalibration.addAction(self.actionDec)
        self.menuFile.addAction(self.actionHelp)
        self.menuFile.addAction(self.actionInfo)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuMode.addAction(self.actionNormal)
        self.menuMode.addAction(self.actionTesting)
        self.menuMode.addSeparator()
        self.menuMode.addAction(self.actionLegacy)
        self.menuObservation.addAction(self.actionScan)
        self.menuObservation.addAction(self.actionSurvey)
        self.menuObservation.addAction(self.actionSpectrum)
        self.menuObservation.addSeparator()
        self.menuObservation.addAction(self.actionGetInfo)

        self.retranslateUi(MainWindow)
        self.actionQuit.triggered.connect(MainWindow.close)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionRA.setText(QCoreApplication.translate("MainWindow", u"RA...", None))
#if QT_CONFIG(shortcut)
        self.actionRA.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+R", None))
#endif // QT_CONFIG(shortcut)
        self.actionDec.setText(QCoreApplication.translate("MainWindow", u"Dec...", None))
#if QT_CONFIG(shortcut)
        self.actionDec.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+D", None))
#endif // QT_CONFIG(shortcut)
        self.actionSurvey.setText(QCoreApplication.translate("MainWindow", u"New Survey...", None))
#if QT_CONFIG(shortcut)
        self.actionSurvey.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+2", None))
#endif // QT_CONFIG(shortcut)
        self.actionInfo.setText(QCoreApplication.translate("MainWindow", u"Credits...", None))
        self.actionQuit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
#if QT_CONFIG(shortcut)
        self.actionQuit.setShortcut(QCoreApplication.translate("MainWindow", u"Esc", None))
#endif // QT_CONFIG(shortcut)
        self.actionHelp.setText(QCoreApplication.translate("MainWindow", u"Help...", None))
        self.actionScan.setText(QCoreApplication.translate("MainWindow", u"New Scan...", None))
#if QT_CONFIG(shortcut)
        self.actionScan.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+1", None))
#endif // QT_CONFIG(shortcut)
        self.actionSpectrum.setText(QCoreApplication.translate("MainWindow", u"New Spectrum...", None))
#if QT_CONFIG(shortcut)
        self.actionSpectrum.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+3", None))
#endif // QT_CONFIG(shortcut)
        self.actionNormal.setText(QCoreApplication.translate("MainWindow", u"Normal", None))
#if QT_CONFIG(shortcut)
        self.actionNormal.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+N", None))
#endif // QT_CONFIG(shortcut)
        self.actionTesting.setText(QCoreApplication.translate("MainWindow", u"Testing", None))
#if QT_CONFIG(shortcut)
        self.actionTesting.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+T", None))
#endif // QT_CONFIG(shortcut)
        self.actionLegacy.setText(QCoreApplication.translate("MainWindow", u"Legacy", None))
        self.actionGetInfo.setText(QCoreApplication.translate("MainWindow", u"Get Info...", None))
#if QT_CONFIG(shortcut)
        self.actionGetInfo.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+I", None))
#endif // QT_CONFIG(shortcut)
        self.dec_group_box.setTitle(QCoreApplication.translate("MainWindow", u"Declinometer", None))
        self.north_label.setText(QCoreApplication.translate("MainWindow", u"+", None))
        self.south_label.setText(QCoreApplication.translate("MainWindow", u"-", None))
        self.dec_auto_check_box.setText(QCoreApplication.translate("MainWindow", u"Auto", None))
        self.signal_group_box.setTitle(QCoreApplication.translate("MainWindow", u"Signal", None))
        self.polarization_label.setText(QCoreApplication.translate("MainWindow", u"Polarization", None))
        self.noise_label.setText(QCoreApplication.translate("MainWindow", u"Interference", None))
        self.variance_label.setText(QCoreApplication.translate("MainWindow", u"Variance", None))
        self.calibration_check_box.setText(QCoreApplication.translate("MainWindow", u"Calibration", None))
        self.data_display_group.setTitle(QCoreApplication.translate("MainWindow", u"Data", None))
        self.channelA_value.setText(QCoreApplication.translate("MainWindow", u"0.0000V", None))
        self.sweep_label.setText(QCoreApplication.translate("MainWindow", u"Sweep:", None))
        self.channelB_value.setText(QCoreApplication.translate("MainWindow", u"0.0000V", None))
        self.ra_value.setText(QCoreApplication.translate("MainWindow", u"00:00:00", None))
        self.channelA_label.setText(QCoreApplication.translate("MainWindow", u"Channel A:", None))
        self.sweep_value.setText(QCoreApplication.translate("MainWindow", u"n/a", None))
        self.dec_label.setText(QCoreApplication.translate("MainWindow", u"Declination:", None))
        self.dec_value.setText(QCoreApplication.translate("MainWindow", u"0.0000deg", None))
        self.channelB_label.setText(QCoreApplication.translate("MainWindow", u"Channel B:", None))
        self.ra_label.setText(QCoreApplication.translate("MainWindow", u"Right Ascension:", None))
        self.stripchart_control_group.setTitle(QCoreApplication.translate("MainWindow", u"Strip chart", None))
        self.stripchart_speed_label.setText(QCoreApplication.translate("MainWindow", u"Scroll speed", None))
#if QT_CONFIG(tooltip)
        self.stripchart_speed_slider.setToolTip(QCoreApplication.translate("MainWindow", u"How quickly the chart scrolls; the readout shows the visible time window in seconds.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.stripchart_speed_value_label.setToolTip(QCoreApplication.translate("MainWindow", u"How quickly the chart scrolls; the readout shows the visible time window in seconds.", None))
#endif // QT_CONFIG(tooltip)
        self.stripchart_speed_value_label.setText(QCoreApplication.translate("MainWindow", u"65s", None))
        self.stripchart_speed_value_label.setProperty(u"role", QCoreApplication.translate("MainWindow", u"readout", None))
        self.stripchart_voltage_label.setText(QCoreApplication.translate("MainWindow", u"Voltage scale", None))
#if QT_CONFIG(tooltip)
        self.stripchart_dynamic_scale_checkbox.setToolTip(QCoreApplication.translate("MainWindow", u"Auto-fit the voltage axis to incoming data; when off, use the manual slider.", None))
#endif // QT_CONFIG(tooltip)
        self.stripchart_dynamic_scale_checkbox.setText(QCoreApplication.translate("MainWindow", u"Auto", None))
#if QT_CONFIG(tooltip)
        self.stripchart_max_voltage_slider.setToolTip(QCoreApplication.translate("MainWindow", u"Manual maximum voltage when Auto is off.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.stripchart_max_voltage_value_label.setToolTip(QCoreApplication.translate("MainWindow", u"Manual maximum voltage when Auto is off.", None))
#endif // QT_CONFIG(tooltip)
        self.stripchart_max_voltage_value_label.setText(QCoreApplication.translate("MainWindow", u"5 V", None))
        self.stripchart_max_voltage_value_label.setProperty(u"role", QCoreApplication.translate("MainWindow", u"readout", None))
        self.stripchart_grid_label.setText(QCoreApplication.translate("MainWindow", u"Grid", None))
#if QT_CONFIG(tooltip)
        self.stripchart_grid_checkbox.setToolTip(QCoreApplication.translate("MainWindow", u"Show grid lines on the chart.", None))
#endif // QT_CONFIG(tooltip)
        self.stripchart_grid_checkbox.setText(QCoreApplication.translate("MainWindow", u"Show", None))
#if QT_CONFIG(tooltip)
        self.stripchart_grid_density_slider.setToolTip(QCoreApplication.translate("MainWindow", u"Voltage step per grid division.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.stripchart_grid_density_value_label.setToolTip(QCoreApplication.translate("MainWindow", u"Voltage step per grid division.", None))
#endif // QT_CONFIG(tooltip)
        self.stripchart_grid_density_value_label.setText(QCoreApplication.translate("MainWindow", u"1.3 V/div", None))
        self.stripchart_grid_density_value_label.setProperty(u"role", QCoreApplication.translate("MainWindow", u"readout", None))
        self.stripchart_channels_label.setText(QCoreApplication.translate("MainWindow", u"Channels", None))
#if QT_CONFIG(tooltip)
        self.channel_dual_button.setToolTip(QCoreApplication.translate("MainWindow", u"Show both channels.", None))
#endif // QT_CONFIG(tooltip)
        self.channel_dual_button.setText(QCoreApplication.translate("MainWindow", u"Dual", None))
#if QT_CONFIG(tooltip)
        self.channel_a_button.setToolTip(QCoreApplication.translate("MainWindow", u"Show only channel A.", None))
#endif // QT_CONFIG(tooltip)
        self.channel_a_button.setText(QCoreApplication.translate("MainWindow", u"A", None))
#if QT_CONFIG(tooltip)
        self.channel_b_button.setToolTip(QCoreApplication.translate("MainWindow", u"Show only channel B.", None))
#endif // QT_CONFIG(tooltip)
        self.channel_b_button.setText(QCoreApplication.translate("MainWindow", u"B", None))
#if QT_CONFIG(tooltip)
        self.chart_clear_button.setToolTip(QCoreApplication.translate("MainWindow", u"Discard the currently plotted samples.", None))
#endif // QT_CONFIG(tooltip)
        self.chart_clear_button.setText(QCoreApplication.translate("MainWindow", u"Clear chart", None))
        self.console_label.setText(QCoreApplication.translate("MainWindow", u">>>", None))
        self.message_group_box.setTitle(QCoreApplication.translate("MainWindow", u"Message", None))
        self.refresh_value.setText(QCoreApplication.translate("MainWindow", u"0.00Hz", None))
        self.message_label.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.refresh_label.setText(QCoreApplication.translate("MainWindow", u"Refresh rate:", None))
        self.menuCalibration.setTitle(QCoreApplication.translate("MainWindow", u"Calibrate", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuMode.setTitle(QCoreApplication.translate("MainWindow", u"Mode", None))
        self.menuObservation.setTitle(QCoreApplication.translate("MainWindow", u"Observation", None))
    # retranslateUi

