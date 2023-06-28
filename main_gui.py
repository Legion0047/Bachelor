#!/usr/bin/env python3
import os
import sys
import math
import subprocess

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QPixmap
from PyQt5.QtWidgets import *
from functools import partial

from persistence import persistence
from modbus import modbus


# TODO: units of use = set use times as automatic replacement of charge time when given
# TODO: Charge bar automatically fills in with planned demand
# TODO: Different devices colour in the chargebar

class MatchBoxLineEdit(QLineEdit):
    def focusInEvent(self, e):
        try:
            subprocess.Popen(["matchbox-keyboard"])
        except FileNotFoundError:
            pass

    def focusOutEvent(self, e):
        subprocess.Popen(["killall", "matchbox-keyboard"])


class MainWindow(QMainWindow):
    db = persistence()
    modbus = modbus
    realCapacity = 450  # WH
    reservedCapacity = 50  # WH
    maxCapacity = realCapacity - reservedCapacity  # WH
    currentCapacity = 0  # WH
    batteryCharge = round((currentCapacity / maxCapacity) * 100)  # %

    savedVoltage = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    savedCurrent = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    savedPower = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    step = 0

    devices = db.load()
    # ID, Name, colour, image, Unit of Use, Voltage V, Current A, Power Wh, in planner

    chargeBar = None

    def __init__(self):
        super().__init__()

        #        client = modbus.connect(self)
        client = []

        self.setWindowTitle("Main Page")
        self.setGeometry(0, 0, 1024, 600)
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint
        )
        # Setup Main page
        layout = QGridLayout()

        chargeLabel = QLabel("Current Charge:")
        self.chargeBar = QProgressBar(self)
        self.chargeBar.setValue(self.batteryCharge)

        layout.addWidget(chargeLabel, 0, 0, 1, 1)
        layout.addWidget(self.chargeBar, 0, 1, 1, 3)

        values = QLabel("0A 0V 0 W, time of use remaining with current consumption: 0h 0m")
        layout.addWidget(values, 1, 0, 1, 3)
        # creating a timer object
        #        timer = QTimer(self)

        # adding action to timer
        #        timer.timeout.connect(lambda: self.updateCharge(values, chargeBar, client))
        #        for i in range(0, 10):
        #            self.updateCharge(values, chargeBar, client)
        # update the timer every 30 seconds
        #        timer.start(30000)

        scrollArea = QScrollArea()
        scrollArea.setBackgroundRole(QPalette.Dark)
        layout.addWidget(scrollArea, 2, 0, 1, 4)

        plusButton = QPushButton("+")
        plusButton.clicked.connect(partial(self.createDevice))

        helpButton = QPushButton("?")
        helpButton.clicked.connect(partial(self.help))

        layout.addWidget(plusButton, 3, 0, 1, 1)
        layout.addWidget(helpButton, 3, 3, 1, 1)

        # Page Setup done

        widget = QWidget()
        widget.setLayout(layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

    def createDevice(self):
        values = []
        dlg = QDialog(self)
        dlg.setWindowTitle("New Device")
        dlg.setGeometry(30, 30, 512, 300)
        dlg.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint
        )

        layout = QGridLayout()

        nameLabel = QLabel("Name:")
        name = MatchBoxLineEdit()
        layout.addWidget(nameLabel, 0, 0, 1, 2)
        layout.addWidget(name, 0, 3, 1, 2)
        values.append(name)

        colour = "lightgreen"
        colourButton = QPushButton("Choose Colour")
        colourLabel = QLabel("")
        colourLabel.setStyleSheet("background-color:" + colour)
        layout.addWidget(colourButton, 1, 0, 1, 2)
        layout.addWidget(colourLabel, 1, 3, 1, 2)
        values.append(colour)
        colourButton.clicked.connect(partial(self.getColour, values, colourLabel))

        image = "blank.png"
        pixmap = QPixmap('./Images/' + image)
        imageButton = QPushButton("Choose Image")
        imageLabel = QLabel("")
        imageLabel.setPixmap(pixmap)
        layout.addWidget(imageButton, 2, 0, 1, 2)
        layout.addWidget(imageLabel, 2, 3, 2, 2)
        values.append(image)
        imageButton.clicked.connect(partial(self.chooseImage, values, imageLabel))

        uouLabel = QLabel("Duration of Unit of Use:")
        minutes = QSpinBox()
        minutes.setMinimum(0)
        minutes.setMaximum(60)
        minutes.setSingleStep(5)
        layout.addWidget(uouLabel, 4, 0, 1, 2)
        layout.addWidget(minutes, 4, 3, 1, 2)
        values.append(minutes)

        save = QPushButton("Create New Device")
        save.clicked.connect(partial(self.addDevice, values, dlg))
        layout.addWidget(save, 5, 0, 1, 2)
        close = QPushButton("Close")
        close.clicked.connect(dlg.close)
        layout.addWidget(close, 5, 3, 1, 2)
        dlg.setLayout(layout)

        dlg.exec()

    def addDevice(self, values, dlg):
        newDevice = []
        deviceId = 0
        for device in self.devices:
            if device[0] > deviceId:
                deviceId = device[0]
        deviceId += 1
        newDevice.append(deviceId)
        newDevice.append(values[0].text())
        newDevice.append(values[1])
        newDevice.append(values[2])
        newDevice.append(values[3].value())
        newDevice.append(1.0)
        newDevice.append(1.0)
        newDevice.append(1.0)
#        self.devices.append(newDevice)
#        self.db.addEdit(newDevice)
        dlg.accept()

        # creating a timer object
#        timer = QTimer(self)
        # adding action to timer
#        timer.singleShot(360000,
#                         lambda: self.calibrateDevice(deviceId, newDevice[1]))

    def getColour(self, values, colourLabel):
        pickedColour = QColorDialog.getColor()
        if pickedColour.isValid():
            colour = pickedColour.name()
            colourLabel.setStyleSheet("background-color:" + colour)
            values[1] = colour

    def chooseImage(self, values, imageLabel):

        dlg = QDialog(self)
        dlg.setWindowTitle("Choose Image")
        dlg.setGeometry(60, 60, 512, 300)
        dlg.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint
        )
        entries = os.listdir('./Images/')

        layout = QGridLayout()

        columns = int(len(entries) / 5)
        if len(entries) % 5 > 0:
            columns += 1
        entry = 0
        for i in range(0, columns):
            for j in range(0, 5):
                if entry >= len(entries): break
                button = QPushButton()
                button.setIcon(QIcon('./Images/' + entries[entry]))
                button.clicked.connect(partial(self.getImage, values, imageLabel, entries[entry], dlg))
                layout.addWidget(button, j, i)
                entry += 1

        dlg.setLayout(layout)

        dlg.exec()

    def getImage(self, values, imageLabel, image, dlg):
        pixmap = QPixmap('./Images/' + image)
        imageLabel.setPixmap(pixmap)
        values[2] = image
        dlg.accept()

    # Help Functions below here
    def getById(self, deviceId):
        for device in self.devices:
            if device[0] == deviceId:
                return device
        return []

    def calculateCapacity(self, devices, label):
        requiredCapacity = 0
        for device in devices:
            hours = float(device[1].text())
            minutes = float(device[2].text())
            hours += float(minutes / 60)
            requiredCapacity += hours * device[0][5]
        label.setText("Required Capacity: " + str(round((requiredCapacity / self.maxCapacity) * 100)) + "%")

    def calculateTime(self):
        for device, label in zip(self.devices, self.labelList):
            if label:
                minutesDec, hours = math.modf(self.currentCapacity / device[5])
                minutes = int(minutesDec * 60)
                label.setText("Time Of Use Remaining: " + str(int(hours)) + "h " + str(minutes) + "m")

    def updateCharge(self, valuesLabel, chargeBar, client):
        # y = 51.57*x - 2474
        values = self.modbus.readCharge(self, client)
        self.savedVoltage[self.step] = values[0]
        self.savedCurrent[self.step] = values[1]
        self.savedPower[self.step] = values[2]
        self.step += 1
        if self.step >= 10: self.step = 0
        avgVoltage = sum(self.savedVoltage) / len(self.savedVoltage)
        avgVoltage = float(f'{avgVoltage:.3f}')
        avgCurrent = sum(self.savedCurrent) / len(self.savedCurrent)
        avgCurrent = float(f'{avgCurrent:.3f}')
        avgPower = sum(self.savedPower) / len(self.savedPower)
        avgPower = float(f'{avgPower:.3f}')
        self.currentCapacity = (51.57 * avgVoltage) - 2474
        if self.currentCapacity > self.maxCapacity: self.currentCapacity = self.maxCapacity
        chargeBar.setValue(round((self.currentCapacity / self.maxCapacity) * 100))

        minutesDec, hours = math.modf(self.currentCapacity / avgPower)
        minutes = int(minutesDec * 60)

        valuesLabel.setText(str(avgVoltage) + "V " + str(avgCurrent) + "A " + str(
            avgPower) + "W, time of use remaining with current consumption: " + str(int(hours)) + "h " + str(
            minutes) + "m")

    def calibrateDevices(self, deviceId, name):
        device = self.getById(deviceId)
        device[1] = name

        avgVoltage = sum(self.savedVoltage) / len(self.savedVoltage)
        device[5] = float(f'{avgVoltage:.3f}')
        avgCurrent = sum(self.savedCurrent) / len(self.savedCurrent)
        device[6] = float(f'{avgCurrent:.3f}')
        avgPower = sum(self.savedPower) / len(self.savedPower)
        device[7] = float(f'{avgPower:.3f}')

#        self.db.addEdit(device)
        dlg = QDialog(self)
        dlg.setWindowTitle("Device Calibrated")
        dlg.setGeometry(0, 0, 512, 150)

        layout = QGridLayout()

        infoLabel = QLabel("Your Device has now been calibrated and can be unplugged.")
        layout.addWidget(infoLabel, 0, 0)
        dlg.setLayout(layout)
        dlg.exec()

    def help(self):
        print("I hope this helps")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    custom_font = QFont('Arial', 20)
    app.setFont(custom_font)
    window = MainWindow()
    window.show()

    app.exec()
