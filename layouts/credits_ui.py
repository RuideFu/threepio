# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'credits.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(383, 362)
        Dialog.setMinimumSize(QtCore.QSize(383, 362))
        Dialog.setMaximumSize(QtCore.QSize(383, 362))
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        spacerItem1 = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.label_2 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.button_frame = QtWidgets.QFrame(Dialog)
        self.button_frame.setObjectName("button_frame")
        self.gridLayout = QtWidgets.QGridLayout(self.button_frame)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem3, 0, 0, 1, 1)
        self.close_button = QtWidgets.QPushButton(self.button_frame)
        font = QtGui.QFont()
        font.setFamily("Iosevka Aile")
        self.close_button.setFont(font)
        self.close_button.setObjectName("close_button")
        self.gridLayout.addWidget(self.close_button, 0, 1, 1, 1)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem4, 0, 2, 1, 1)
        self.verticalLayout.addWidget(self.button_frame)

        self.retranslateUi(Dialog)
        self.close_button.clicked.connect(Dialog.close)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Credits"))
        self.label.setText(_translate("Dialog", "  __  __                    _                 \n"
" / /_/ /  _______ ___ ___  (_)__    ___  __ __\n"
"/ __/ _ \\/ __/ -_) -_) _ \\/ / _ \\_ / _ \\/ // /\n"
"\\__/_//_/_/  \\__/\\__/ .__/_/\\___(_) .__/\\_, / \n"
"                   /_/           /_/   /___/  \n"
""))
        self.label_2.setText(_translate("Dialog", "The helpful companion to the 40\' telescope\n"
"\n"
"Written with frustration by Shengjie, Isabel, and Finn\n"
"\n"
"No frills, all thrills 😎"))
        self.close_button.setText(_translate("Dialog", "Close"))