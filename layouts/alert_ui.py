# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'alert.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(320, 100)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.alert = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        font.setPointSize(24)
        self.alert.setFont(font)
        self.alert.setAlignment(QtCore.Qt.AlignCenter)
        self.alert.setObjectName("alert")
        self.gridLayout.addWidget(self.alert, 0, 0, 1, 2)
        self.button_frame = QtWidgets.QFrame(Dialog)
        self.button_frame.setObjectName("button_frame")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.button_frame)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.close_button = QtWidgets.QPushButton(self.button_frame)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        self.close_button.setFont(font)
        self.close_button.setObjectName("close_button")
        self.gridLayout_2.addWidget(self.close_button, 0, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.button_frame, 2, 0, 1, 2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Alert"))
        self.alert.setText(_translate("Dialog", "!!!"))
        self.close_button.setText(_translate("Dialog", "Close"))