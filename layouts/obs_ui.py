# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'obs.ui'
#
# Created by: PyQt5 UI code generator 5.15.3
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(264, 288)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.end_time = QtWidgets.QDateTimeEdit(Dialog)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        self.end_time.setFont(font)
        self.end_time.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.end_time.setObjectName("end_time")
        self.gridLayout.addWidget(self.end_time, 1, 2, 1, 1)
        self.ending_dec = QtWidgets.QLineEdit(Dialog)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        self.ending_dec.setFont(font)
        self.ending_dec.setObjectName("ending_dec")
        self.gridLayout.addWidget(self.ending_dec, 4, 2, 1, 1)
        self.start_time = QtWidgets.QTimeEdit(Dialog)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        self.start_time.setFont(font)
        self.start_time.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.start_time.setObjectName("start_time")
        self.gridLayout.addWidget(self.start_time, 0, 2, 1, 1)
        self.starting_dec = QtWidgets.QLineEdit(Dialog)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        self.starting_dec.setFont(font)
        self.starting_dec.setObjectName("starting_dec")
        self.gridLayout.addWidget(self.starting_dec, 2, 2, 1, 1)
        self.start_label = QtWidgets.QLabel(Dialog)
        self.start_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.start_label.setObjectName("start_label")
        self.gridLayout.addWidget(self.start_label, 0, 1, 1, 1)
        self.line = QtWidgets.QFrame(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 7, 1, 1, 2)
        self.data_acquisition_rate_label = QtWidgets.QLabel(Dialog)
        self.data_acquisition_rate_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.data_acquisition_rate_label.setObjectName("data_acquisition_rate_label")
        self.gridLayout.addWidget(self.data_acquisition_rate_label, 6, 1, 1, 1)
        self.start_dec_label = QtWidgets.QLabel(Dialog)
        self.start_dec_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.start_dec_label.setObjectName("start_dec_label")
        self.gridLayout.addWidget(self.start_dec_label, 2, 1, 1, 1)
        self.end_dec_label = QtWidgets.QLabel(Dialog)
        self.end_dec_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.end_dec_label.setObjectName("end_dec_label")
        self.gridLayout.addWidget(self.end_dec_label, 4, 1, 1, 1)
        self.data_acquisition_rate_value = QtWidgets.QSpinBox(Dialog)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        self.data_acquisition_rate_value.setFont(font)
        self.data_acquisition_rate_value.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.data_acquisition_rate_value.setMinimum(1)
        self.data_acquisition_rate_value.setMaximum(100)
        self.data_acquisition_rate_value.setProperty("value", 10)
        self.data_acquisition_rate_value.setObjectName("data_acquisition_rate_value")
        self.gridLayout.addWidget(self.data_acquisition_rate_value, 6, 2, 1, 1)
        self.end_label = QtWidgets.QLabel(Dialog)
        self.end_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.end_label.setObjectName("end_label")
        self.gridLayout.addWidget(self.end_label, 1, 1, 1, 1)
        self.button_frame = QtWidgets.QFrame(Dialog)
        self.button_frame.setObjectName("button_frame")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.button_frame)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.accept_button = QtWidgets.QPushButton(self.button_frame)
        self.accept_button.setObjectName("accept_button")
        self.gridLayout_2.addWidget(self.accept_button, 0, 2, 1, 1)
        self.cancel_button = QtWidgets.QPushButton(self.button_frame)
        self.cancel_button.setObjectName("cancel_button")
        self.gridLayout_2.addWidget(self.cancel_button, 0, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.button_frame, 9, 1, 1, 2)
        self.frame = QtWidgets.QFrame(Dialog)
        self.frame.setObjectName("frame")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.file_name_label = QtWidgets.QLabel(self.frame)
        self.file_name_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.file_name_label.setObjectName("file_name_label")
        self.gridLayout_3.addWidget(self.file_name_label, 0, 0, 1, 1)
        self.file_name_value = QtWidgets.QLineEdit(self.frame)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        self.file_name_value.setFont(font)
        self.file_name_value.setObjectName("file_name_value")
        self.gridLayout_3.addWidget(self.file_name_value, 0, 2, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem1, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.frame, 8, 1, 1, 2)
        self.error_label = QtWidgets.QLabel(Dialog)
        self.error_label.setStyleSheet("color: red")
        self.error_label.setAlignment(QtCore.Qt.AlignCenter)
        self.error_label.setObjectName("error_label")
        self.gridLayout.addWidget(self.error_label, 10, 1, 1, 2)
        self.data_acquisition_rate_label.setBuddy(self.data_acquisition_rate_value)

        self.retranslateUi(Dialog)
        self.cancel_button.clicked.connect(Dialog.reject)
        self.accept_button.clicked.connect(Dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.start_time, self.end_time)
        Dialog.setTabOrder(self.end_time, self.starting_dec)
        Dialog.setTabOrder(self.starting_dec, self.ending_dec)
        Dialog.setTabOrder(self.ending_dec, self.data_acquisition_rate_value)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "New Observation"))
        self.end_time.setDisplayFormat(_translate("Dialog", "HH:mm:ss"))
        self.start_time.setDisplayFormat(_translate("Dialog", "HH:mm:ss"))
        self.start_label.setText(_translate("Dialog", "Starting RA"))
        self.data_acquisition_rate_label.setText(_translate("Dialog", "Data Acquisition Rate"))
        self.start_dec_label.setText(_translate("Dialog", "Minimum Declination"))
        self.end_dec_label.setText(_translate("Dialog", "Maximum Declination"))
        self.end_label.setText(_translate("Dialog", "Ending RA"))
        self.accept_button.setText(_translate("Dialog", "Start Observation"))
        self.cancel_button.setText(_translate("Dialog", "Cancel"))
        self.file_name_label.setText(_translate("Dialog", "File name"))
        self.error_label.setText(_translate("Dialog", "Error creating observation"))
