#!/usr/bin/env python3
import os
import sys
import math
import subprocess

from PyQt5 import QtCore
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIcon, QPalette, QPixmap
from PyQt5.QtWidgets import *
from functools import partial

from persistence import persistence
from modbus import modbus


# TODO: units of use = set use times as automatic replacement of charge time when given
# TODO: Charge bar automatically fills in with planned demand
# TODO: Different devices colour in the chargebar
# TODO: Edit
# TODO: Charging Icon
# TODO: Calibration timer

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
    currentCapacity = 300  # WH
    batteryCharge = round((currentCapacity / maxCapacity) * 100)  # %

    savedVoltage = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    savedCurrent = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    savedPower = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    step = 0

    devices = db.load()
    # ID, Name, colour, image, Unit of Use, Voltage V, Current A, Power Wh, in planner

    scrollArea = None
    layout = None

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

        self.layout = QGridLayout()

        chargeLabel = QLabel("Current Charge:")
        chargeBar = QProgressBar(self)
        chargeBar.setValue(self.batteryCharge)

        self.layout.addWidget(chargeLabel, 0, 0, 1, 1)
        self.layout.addWidget(chargeBar, 0, 1, 1, 3)

        values = QLabel("0A 0V 0 W, time of use remaining with current consumption: 0h 0m")
        self.layout.addWidget(values, 1, 0, 1, 3)
        # creating a timer object
        #        timer = QTimer(self)

        # adding action to timer
        #        timer.timeout.connect(lambda: self.updateCharge(values, chargeBar, client))
        #        for i in range(0, 10):
        #            self.updateCharge(values, chargeBar, client)
        # update the timer every 30 seconds
        #        timer.start(30000)

        self.scrollArea = QScrollArea()

        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("QScrollBar:vertical { width: 30px; }")

        self.layout.addWidget(self.scrollArea, 2, 0, 1, 4)

        plusButton = QPushButton("+")
        plusButton.clicked.connect(partial(self.createDevice))

        helpButton = QPushButton("?")
        helpButton.clicked.connect(partial(self.help))

        self.layout.addWidget(plusButton, 3, 0, 1, 1)
        self.layout.addWidget(helpButton, 3, 3, 1, 1)

        self.deviceList()

        # Page Setup done

        widget = QWidget()
        widget.setLayout(self.layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

    def deviceList(self):
        scrollLayout = QGridLayout()
        scrollWidget = QWidget()
        scrollWidget.setLayout(scrollLayout)
        self.scrollArea.setWidget(scrollWidget)
        imageLabel = QLabel("Image")
        nameLabel = QLabel("Name")
        timeLabel = QLabel("Time of Use:")
        unitLabel = QLabel("Units of Use:")
        plannedLabel = QLabel("Planned:")

        scrollLayout.addWidget(imageLabel, 0, 0)
        scrollLayout.addWidget(nameLabel, 0, 1)
        scrollLayout.addWidget(timeLabel, 0, 2)
        scrollLayout.addWidget(unitLabel, 0, 3)
        scrollLayout.addWidget(plannedLabel, 0, 4)

        row = 1
        for device in self.devices:
            pixmap = QPixmap('./Images/' + device[3]).scaled(120, 120)
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
            if device[4] != 0:
                uou = int((hours * 60 + minutes) / device[4])
            else:
                uou = "N/A"
            units = QLabel(str(uou))
            units.setStyleSheet('background-color: ' + colour)
            plannedUnits = QSpinBox()
            plannedUnits.setStyleSheet('background-color: ' + colour)
            plannedUnits.setMinimum(0)
            plannedUnits.setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Expanding)
            plannedUnits.valueChanged.connect(partial(self.addBar, device, plannedUnits))
            scrollLayout.addWidget(image, row, 0)
            scrollLayout.addWidget(name, row, 1)
            scrollLayout.addWidget(time, row, 2)
            scrollLayout.addWidget(units, row, 3)
            scrollLayout.addWidget(plannedUnits, row, 4)
            row += 1

    def details(self, device):

        scrollLayout = QGridLayout()
        scrollWidget = QWidget()
        scrollWidget.setLayout(scrollLayout)
        self.scrollArea.setWidget(scrollWidget)

        pixmap = QPixmap('./Images/' + device[3]).scaled(240, 240)
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
        edit.clicked.connect(partial( self.editDevice, device))
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

    def editDevice(self, device):
        values = []

        scrollLayout = QGridLayout()
        scrollWidget = QWidget()
        scrollWidget.setLayout(scrollLayout)
        self.scrollArea.setWidget(scrollWidget)

        nameLabel = QLabel("Name:")
        name = MatchBoxLineEdit(str(device[1]))
        scrollLayout.addWidget(nameLabel, 0, 0, 1, 2)
        scrollLayout.addWidget(name, 0, 2, 1, 2)
        values.append(name)

        colour = device[2]
        colourButton = QPushButton("Choose Colour")
        colourLabel = QLabel("")
        colourLabel.setStyleSheet("background-color:" + colour)
        scrollLayout.addWidget(colourButton, 1, 0, 1, 2)
        scrollLayout.addWidget(colourLabel, 1, 2, 1, 2)
        values.append(colour)
        colourButton.clicked.connect(partial(self.getColour, values, colourLabel))

        image = device[3]
        pixmap = QPixmap('./Images/' + image).scaled(120, 120)
        imageButton = QPushButton("Choose Image")
        imageLabel = QLabel("")
        imageLabel.setPixmap(pixmap)
        scrollLayout.addWidget(imageButton, 2, 0, 1, 2)
        scrollLayout.addWidget(imageLabel, 2, 2, 2, 2)
        values.append(image)
        imageButton.clicked.connect(partial(self.chooseImage, values, imageLabel))

        uouLabel = QLabel("Duration of Unit of Use:")
        minutes = QSpinBox()
        minutes.setMinimum(0)
        minutes.setMaximum(60)
        minutes.setSingleStep(5)
        minutes.setValue(device[4])
        scrollLayout.addWidget(uouLabel, 4, 0, 1, 2)
        scrollLayout.addWidget(minutes, 4, 2, 1, 2)
        values.append(minutes)

        calibrate = QPushButton("Calibrate Device")
        scrollLayout.addWidget(calibrate, 5, 0, 1, 4)

        save = QPushButton("Save Changes")
        save.clicked.connect(partial(self.changeDevice, device, values))
        scrollLayout.addWidget(save, 6, 0, 1, 2)
        exit = QPushButton("Discard Changes")
        exit.clicked.connect(partial(self.deviceList))
        scrollLayout.addWidget(exit, 6, 2, 1, 2)

    def changeDevice(self, device, values):
        device[1] = values[0].text()
        device[2] = values[1]
        device[3] = values[2]
        device[4] = values[3].value()
        self.db.addEdit(device)
        self.deviceList()

    def createDevice(self):
        values = []

        scrollLayout = QGridLayout()
        scrollWidget = QWidget()
        scrollWidget.setLayout(scrollLayout)
        self.scrollArea.setWidget(scrollWidget)

        nameLabel = QLabel("Name:")
        name = MatchBoxLineEdit()
        scrollLayout.addWidget(nameLabel, 0, 0, 1, 2)
        scrollLayout.addWidget(name, 0, 2, 1, 2)
        values.append(name)

        colour = "lightgreen"
        colourButton = QPushButton("Choose Colour")
        colourLabel = QLabel("")
        colourLabel.setStyleSheet("background-color:" + colour)
        scrollLayout.addWidget(colourButton, 1, 0, 1, 2)
        scrollLayout.addWidget(colourLabel, 1, 2, 1, 2)
        values.append(colour)
        colourButton.clicked.connect(partial(self.getColour, values, colourLabel))

        image = "blank.png"
        pixmap = QPixmap('./Images/' + image).scaled(120, 120)
        imageButton = QPushButton("Choose Image")
        imageLabel = QLabel("")
        imageLabel.setPixmap(pixmap)
        scrollLayout.addWidget(imageButton, 2, 0, 1, 2)
        scrollLayout.addWidget(imageLabel, 2, 2, 2, 2)
        values.append(image)
        imageButton.clicked.connect(partial(self.chooseImage, values, imageLabel))

        uouLabel = QLabel("Duration of Unit of Use:")
        minutes = QSpinBox()
        minutes.setMinimum(0)
        minutes.setMaximum(60)
        minutes.setSingleStep(5)
        scrollLayout.addWidget(uouLabel, 4, 0, 1, 2)
        scrollLayout.addWidget(minutes, 4, 2, 1, 2)
        values.append(minutes)

        save = QPushButton("Create New Device")
        save.clicked.connect(partial(self.addDevice, values))
        scrollLayout.addWidget(save, 5, 0, 1, 2)
        exit = QPushButton("Exit")
        exit.clicked.connect(partial(self.deviceList))
        scrollLayout.addWidget(exit, 5, 2, 1, 2)

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
        #        self.devices.append(newDevice)
        #        self.db.addEdit(newDevice)
        self.deviceList()

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
                name, ending = entries[entry].split('.')
                button = QPushButton(name)
                button.setIcon(QIcon('./Images/' + entries[entry]))
                button.clicked.connect(partial(self.getImage, values, imageLabel, entries[entry], dlg))
                button.setSizePolicy(
                    QSizePolicy.Preferred,
                    QSizePolicy.Expanding)
                layout.addWidget(button, j, i)
                entry += 1

        dlg.setLayout(layout)

        dlg.exec()

    def getImage(self, values, imageLabel, image, dlg):
        pixmap = QPixmap('./Images/' + image)
        imageLabel.setPixmap(pixmap)
        values[2] = image
        dlg.accept()

    def addBar(self, device, spinBox):
        bar = QProgressBar(self)
        bar.setValue(int(self.batteryCharge / 2))
        op = QGraphicsOpacityEffect(bar)
        op.setOpacity(0.5)
        bar.setGraphicsEffect(op)
        bar.setFormat("")
        self.layout.addWidget(bar, 0, 1, 1, 3)

    # Help Functions below here

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

    def calibrateDevices(self, device, name):
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
