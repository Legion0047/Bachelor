#!/usr/bin/env python3
import os
import sys
import math
import subprocess

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import *
from functools import partial

from persistence import persistence
from modbus import modbus


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

    savedVoltage = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    savedCurrent = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    savedPower = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    step = 0

    devices = db.load()
    # ID, Name, colour, image, Unit of Use, Voltage V, Current A, Power Wh, in planner
    labels = []
    spinBoxes = []

    scrollArea = None
    layout = None
    chargeBar = None
    chargingIcon = None
    plannedBars = []
    calibrationBar = None

    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 1024, 600)
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint
        )
        self.layout = QGridLayout()

        # Make startup Splash screen
        pixmap = QPixmap('Images/TUW_logo.png').scaled(512, 600, QtCore.Qt.KeepAspectRatio)
        logo = QLabel("")
        logo.setAlignment(QtCore.Qt.AlignCenter)
        logo.setPixmap(pixmap)
        self.layout.addWidget(logo, 0, 0)

        name = QLabel("Computer Aided Sustainability")
        name.setAlignment(QtCore.Qt.AlignCenter)
        name.setFont(QFont('Arial', 50))
        self.layout.addWidget(name, 1, 0)

        widget = QWidget()
        widget.setLayout(self.layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

        # replace splashscreen with main window after 5s
        timer = QTimer(self)
        timer.singleShot(5000, partial(self.launchMain, logo, name))

    def launchMain(self, logo, name):
        self.layout.removeWidget(logo)
        self.layout.removeWidget(name)
        client = modbus.connect(self)

        chargeLabel = QLabel("Current Charge:")
        self.chargeBar = QProgressBar(self)
        self.chargeBar.setMaximum(100)
        self.chargeBar.setFormat("")
        self.chargeBar.setValue(self.batteryCharge)

        self.layout.addWidget(chargeLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.chargeBar, 0, 1, 1, 3)

        values = QLabel("0A 0V 0 W, time of use remaining: 0h 0m")
        self.layout.addWidget(values, 1, 0, 1, 3)

        pixmap = QPixmap('Images/blank.png').scaled(60, 60, QtCore.Qt.KeepAspectRatio)
        self.chargingIcon = QLabel("")
        self.chargingIcon.setPixmap(pixmap)
        self.layout.addWidget(self.chargingIcon, 1, 3, 1, 1)
        # creating a timer object
        timer = QTimer(self)

        # adding action to timer
        timer.timeout.connect(lambda: self.updateValues(values, client))
        for i in range(0, 12):
            self.updateValues(values, client)
        # update the timer every 5 seconds
        timer.start(5000)

        self.scrollArea = QScrollArea(self)

        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("QScrollBar:vertical { width: 30px; }")

        self.layout.addWidget(self.scrollArea, 2, 0, 1, 4)

        plusButton = QPushButton("+")
        plusButton.clicked.connect(partial(self.createEditDevice, [], True))

        helpButton = QPushButton("?")
        helpButton.clicked.connect(partial(self.help))

        self.calibrationBar = QProgressBar()
        self.calibrationBar.setFormat("")
        self.calibrationBar.setValue(0)

        self.layout.addWidget(plusButton, 3, 0, 1, 1)
        self.layout.addWidget(helpButton, 3, 3, 1, 1)
        self.layout.addWidget(self.calibrationBar, 3, 1, 1, 2)

        self.deviceList()

    def deviceList(self):
        scrollLayout = QGridLayout()
        scrollWidget = QWidget()
        scrollWidget.setLayout(scrollLayout)
        self.scrollArea.setWidget(scrollWidget)
        imageLabel = QLabel("Image:")
        nameLabel = QLabel("Name:")
        timeLabel = QLabel("Time of Use:")
        unitLabel = QLabel("Units of Use:")
        plannedLabel = QLabel("Planned:")

        scrollLayout.addWidget(imageLabel, 0, 0)
        scrollLayout.addWidget(nameLabel, 0, 1)
        scrollLayout.addWidget(timeLabel, 0, 2)
        scrollLayout.addWidget(unitLabel, 0, 3)
        scrollLayout.addWidget(plannedLabel, 0, 4)

        self.labels = []
        self.spinBoxes = []

        row = 1
        for device in self.devices:
            pixmap = QPixmap('Images/' + device[3]).scaled(120, 120, QtCore.Qt.KeepAspectRatio)
            image = QLabel("")
            image.setPixmap(pixmap)

            colour = device[2]
            name = QPushButton(device[1])
            name.setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Expanding)
            name.setStyleSheet('background-color: ' + colour)
            name.clicked.connect(partial(self.details, device))
            minutesDec, hours = math.modf(self.currentCapacity / device[7])
            minutes = int(minutesDec * 60)
            time = QLabel(str(int(hours)) + "h " + str(minutes) + "m")
            time.setStyleSheet('background-color: ' + colour)
            plannedUnits = QSpinBox()
            plannedUnits.setStyleSheet('background-color: ' + colour)
            plannedUnits.setMinimum(0)
            plannedUnits.setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Expanding)
            plannedUnits.valueChanged.connect(partial(self.changeBar))
            self.spinBoxes.append(plannedUnits)

            if device[4] != 0:
                uou = math.floor((hours * 60 + minutes) / device[4])
                plannedUnits.setMaximum(uou)
                units = QLabel(str(uou) + " per " + str(device[4]) + "m")
            else:
                uou = "N/A"
                plannedUnits.setMaximum(0)
                units = QLabel(str(uou))

            units.setStyleSheet('background-color: ' + colour)
            scrollLayout.addWidget(image, row, 0)
            scrollLayout.addWidget(name, row, 1)
            scrollLayout.addWidget(time, row, 2)
            scrollLayout.addWidget(units, row, 3)
            scrollLayout.addWidget(plannedUnits, row, 4)

            plannedBar = QProgressBar(self)
            plannedBar.setFormat(str(self.chargeBar.value()) + "%")
            plannedBar.setAlignment(QtCore.Qt.AlignCenter)
            plannedBar.setStyleSheet("QProgressBar"
                                     "{"
                                     "background-color : rgba(0, 0, 0, 0);"
                                     "}"

                                     "QProgressBar::chunk"
                                     "{"
                                     "background : " + colour +
                                     "}"
                                     )
            plannedBar.setValue(0)
            self.layout.addWidget(plannedBar, 0, 1, 1, 3)
            self.plannedBars.append(plannedBar)
            self.labels.append([time, units])

            row += 1

    def details(self, device):

        scrollLayout = QGridLayout()
        scrollWidget = QWidget()
        scrollWidget.setLayout(scrollLayout)
        self.scrollArea.setWidget(scrollWidget)

        pixmap = QPixmap('Images/' + device[3]).scaled(200, 200, QtCore.Qt.KeepAspectRatio)
        image = QLabel("")
        image.setPixmap(pixmap)
        scrollLayout.addWidget(image, 0, 0)

        name = QLabel("Name: " + str(device[1]))
        scrollLayout.addWidget(name, 0, 1)

        uouLabel = QLabel("Duration of Unit of Use: " + str(device[4]) + "m")
        scrollLayout.addWidget(uouLabel, 1, 1)

        colour = QLabel("")
        colour.setStyleSheet("background-color:" + device[2])
        scrollLayout.addWidget(colour, 2, 0, 1, 2)

        stats = QLabel(
            "Voltage: " + str(device[5]) + "V,    Current: " + str(device[6]) + "A,    Power: " + str(device[7]) + "W")
        scrollLayout.addWidget(stats, 3, 0, 1, 2)

        edit = QPushButton("Edit")
        edit.clicked.connect(partial(self.createEditDevice, device, False))
        scrollLayout.addWidget(edit, 4, 0)

        delete = QPushButton("Delete")
        delete.setStyleSheet('background-color: #e01b24')
        delete.clicked.connect(partial(self.delete, device))
        scrollLayout.addWidget(delete, 4, 1)

        exit = QPushButton("Exit")
        exit.clicked.connect(partial(self.deviceList))
        scrollLayout.addWidget(exit, 5, 0, 1, 2)

    def delete(self, device):
        dlg = QDialog(self)
        dlg.setWindowTitle("Delete Device")
        dlg.setGeometry(60, 60, 512, 300)
        dlg.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint
        )

        layout = QGridLayout()

        label = QLabel("Are you sure you want to delete this device?")
        layout.addWidget(label, 0, 0, 1, 2)

        yes = QPushButton("Yes")
        yes.setStyleSheet('background-color: #e01b24')
        yes.clicked.connect(partial(self.removeDevice, device, dlg))
        no = QPushButton("No")
        no.clicked.connect(partial(self.returnDetails, device, dlg))

        layout.addWidget(no, 1, 0)
        layout.addWidget(yes, 1, 1)

        dlg.setLayout(layout)

        dlg.exec()

    def removeDevice(self, device, dlg):
        self.devices.remove(device)
        self.db.delete(device)
        dlg.accept()
        self.deviceList()

    def returnDetails(self, device, dlg):
        dlg.accept()
        self.details(device)

    def createEditDevice(self, device, create):
        values = []

        scrollLayout = QGridLayout()
        scrollWidget = QWidget()
        scrollWidget.setLayout(scrollLayout)
        self.scrollArea.setWidget(scrollWidget)
        if create:
            name = MatchBoxLineEdit("")
        else:
            name = MatchBoxLineEdit(str(device[1]))
        nameLabel = QLabel("Name:")
        scrollLayout.addWidget(nameLabel, 0, 0, 1, 2)
        scrollLayout.addWidget(name, 0, 2, 1, 2)
        values.append(name)

        if create:
            colour = "lightgreen"
        else:
            colour = device[2]
        colourButton = QPushButton("Choose Colour")
        colourLabel = QLabel("")
        colourLabel.setStyleSheet("background-color:" + colour)
        scrollLayout.addWidget(colourButton, 1, 0, 1, 2)
        scrollLayout.addWidget(colourLabel, 1, 2, 1, 2)
        values.append(colour)
        colourButton.clicked.connect(partial(self.getColour, values, colourLabel))

        if create:
            image = "blank.png"
        else:
            image = device[3]
        pixmap = QPixmap('Images/' + image).scaled(140, 140, QtCore.Qt.KeepAspectRatio)
        imageButton = QPushButton("Choose Image")
        imageLabel = QLabel("")
        imageLabel.setPixmap(pixmap)
        scrollLayout.addWidget(imageButton, 2, 0, 1, 2)
        scrollLayout.addWidget(imageLabel, 2, 2, 1, 2)
        values.append(image)
        imageButton.clicked.connect(partial(self.chooseImage, values, imageLabel))

        uouLabel = QLabel("Duration of Unit of Use:")
        minutes = QSpinBox()
        minutes.setMinimum(0)
        minutes.setMaximum(60)
        minutes.setSingleStep(5)
        minutes.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding)
        if create:
            minutes.setValue(0)
        else:
            minutes.setValue(device[4])

        scrollLayout.addWidget(uouLabel, 3, 0, 1, 2)
        scrollLayout.addWidget(minutes, 3, 2, 1, 2)
        values.append(minutes)

        if create:
            save = QPushButton("Create New Device")
            save.clicked.connect(partial(self.addDevice, values))
            scrollLayout.addWidget(save, 4, 0, 1, 2)
            exit = QPushButton("Exit")
            exit.clicked.connect(partial(self.deviceList))
            scrollLayout.addWidget(exit, 4, 2, 1, 2)
        else:
            save = QPushButton("Save Changes")
            save.clicked.connect(partial(self.changeDevice, device, values, False))
            scrollLayout.addWidget(save, 4, 0, 1, 2)
            exit = QPushButton("Discard Changes")
            exit.clicked.connect(partial(self.deviceList))
            scrollLayout.addWidget(exit, 4, 2, 1, 2)
            calibrate = QPushButton("Calibrate Device")
            calibrate.clicked.connect(partial(self.changeDevice, device, values, True))
            scrollLayout.addWidget(calibrate, 5, 0, 1, 4)

    def changeDevice(self, device, values, sync):
        device[1] = values[0].text()
        device[2] = values[1]
        device[3] = values[2]
        device[4] = values[3].value()
        self.db.addEdit(device)
        self.deviceList()
        if sync:
            # creating a timer object
            timer = QTimer(self)
            # adding action to timer
            timer.singleShot(1000, lambda: self.calibrationTimer(device, 0))

    def addDevice(self, values):
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
        self.devices.append(newDevice)
        self.db.addEdit(newDevice)
        self.deviceList()

        # creating a timer object

        timer = QTimer(self)
        # adding action to timer
        timer.singleShot(1000, lambda: self.calibrationTimer(newDevice, 0))

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
        entries = os.listdir('Images/')

        layout = QGridLayout()

        columns = int(len(entries) / 5)
        if len(entries) % 5 > 0:
            columns += 1
        entry = 0
        for i in range(0, columns):
            for j in range(0, 5):
                if entry >= len(entries): break
                name, ending = entries[entry].split('.')
                button = QPushButton(name)
                button.setIcon(QIcon('Images/' + entries[entry]))
                button.clicked.connect(partial(self.getImage, values, imageLabel, entries[entry], dlg))
                button.setSizePolicy(
                    QSizePolicy.Preferred,
                    QSizePolicy.Expanding)
                layout.addWidget(button, j, i)
                entry += 1

        dlg.setLayout(layout)

        dlg.exec()

    def getImage(self, values, imageLabel, image, dlg):
        pixmap = QPixmap('Images/' + image).scaled(140, 140, QtCore.Qt.KeepAspectRatio)
        imageLabel.setPixmap(pixmap)
        values[2] = image
        dlg.accept()

    def changeBar(self):
        deviceValue = 0
        for device, spin, bar in zip(reversed(self.devices), reversed(self.spinBoxes), reversed(self.plannedBars)):
            if device[4] > 0:
                deviceValue += (device[4] / 60) * device[7] * spin.value()
                if deviceValue > self.currentCapacity: deviceValue = self.currentCapacity
                bar.setValue(round((deviceValue / self.maxCapacity) * 100))

    def updateValues(self, valuesLabel, client):
        # y = 51.57*x - 2474
        values = self.modbus.readCharge(self, client)
        self.savedVoltage[self.step] = values[0]
        self.savedCurrent[self.step] = values[1]
        self.savedPower[self.step] = values[2]
        self.step += 1
        if self.step >= 12: self.step = 0
        avgVoltage = sum(self.savedVoltage) / len(self.savedVoltage)
        avgVoltage = float(f'{avgVoltage:.3f}')
        avgCurrent = sum(self.savedCurrent) / len(self.savedCurrent)
        avgCurrent = float(f'{avgCurrent:.3f}')
        avgPower = sum(self.savedPower) / len(self.savedPower)
        avgPower = float(f'{avgPower:.3f}')
        self.currentCapacity = (51.57 * avgVoltage) - 2474
        if self.currentCapacity > self.maxCapacity: self.currentCapacity = self.maxCapacity
        newValue = round((self.currentCapacity / self.maxCapacity) * 100)
        if newValue >= self.chargeBar.value():
            pixmap = QPixmap('Images/plugCharging.png').scaled(60, 60, QtCore.Qt.KeepAspectRatio)
            self.chargingIcon.setPixmap(pixmap)
        else:
            pixmap = QPixmap('Images/blank.png').scaled(60, 60, QtCore.Qt.KeepAspectRatio)
            self.chargingIcon.setPixmap(pixmap)
        self.chargeBar.setValue(newValue)
        for bar in self.plannedBars:
            bar.setFormat(str(round((self.currentCapacity / self.maxCapacity) * 100)) + "%")

        minutesDec, hours = math.modf(self.currentCapacity / avgPower)
        minutes = int(minutesDec * 60)

        valuesLabel.setText(str(avgVoltage) + "V " + str(avgCurrent) + "A " + str(
            avgPower) + "W, time of use remaining: " + str(int(hours)) + "h " + str(
            minutes) + "m")

        for device, [label, uouLabel], box in zip(self.devices, self.labels, self.spinBoxes):
            if label:
                minutesDec, hours = math.modf(self.currentCapacity / device[5])
                minutes = int(minutesDec * 60)
                label.setText(str(int(hours)) + "h " + str(minutes) + "m")
                if device[4] != 0:
                    uou = int((hours * 60 + minutes) / device[4])
                    box.setMaximum(uou)
                    uouLabel.setText(str(uou) + " per " + str(device[4]) + "m")

    def calibrationTimer(self, device, counter):
        if counter >= 65:
            self.calibrationBar.setValue(0)
            self.calibrateDevice(device)
        else:
            self.calibrationBar.setValue(round((counter / 65) * 100))
            timer = QTimer()
            timer.singleShot(1000, lambda: self.calibrationTimer(device, counter + 1))

    def calibrateDevice(self, device):

        avgVoltage = sum(self.savedVoltage) / len(self.savedVoltage)
        device[5] = float(f'{avgVoltage:.3f}')
        avgCurrent = sum(self.savedCurrent) / len(self.savedCurrent)
        device[6] = float(f'{avgCurrent:.3f}')
        avgPower = sum(self.savedPower) / len(self.savedPower)
        device[7] = float(f'{avgPower:.3f}')

        self.db.addEdit(device)
        dlg = QDialog(self)
        dlg.setWindowTitle("Device Calibrated")
        dlg.setGeometry(0, 0, 512, 150)
        dlg.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint
        )

        layout = QGridLayout()

        infoLabel = QLabel("Your Device has now been calibrated and can be unplugged.")
        layout.addWidget(infoLabel, 0, 0)

        accept = QPushButton("Accept")
        accept.clicked.connect(dlg.accept)
        layout.addWidget(accept, 1, 0)

        dlg.setLayout(layout)
        dlg.exec()

    def help(self):
        print("I hope this helps")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    custom_font = QFont('Arial', 20)
    app.setFont(custom_font)
    app.setStyleSheet("""
    QSpinBox::down-button{
        width: 50
    }
    QSpinBox::up-button{
        width: 50
    }""")
    window = MainWindow()
    window.show()

    app.exec()
