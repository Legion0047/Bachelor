import os
import sys
import math

from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import *
from functools import partial

from persistence import persistence
from modbus import modbus


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

    items = db.load()
    labelList = []
    # ID, Name, Tags, Voltage V, Current A, Power Wh, in planner

    # TODO: Po file
    # TODO: Help and About button in menubar

    def __init__(self):
        super().__init__()

        client = modbus.connect(self)

        self.setWindowTitle("Main Page")
        self.setGeometry(0, 0, 1024, 600)
        # Setup Main page
        layout = QGridLayout()

        chargeLabel = QLabel("Current Charge:")
        chargeBar = QProgressBar(self)
        chargeBar.setValue(self.batteryCharge)

        layout.addWidget(chargeLabel, 0, 0)
        layout.addWidget(chargeBar, 0, 1)

        values = QLabel("0A 0V 0 W, time of use remaining with current consumption: 0h 0m")
        layout.addWidget(values, 1, 1)
        # creating a timer object
        timer = QTimer(self)

        # adding action to timer
        timer.timeout.connect(lambda: self.updateCharge(values, chargeBar, client))
        for i in range(0, 10):
            self.updateCharge(values, chargeBar, client)
        # update the timer every 30 seconds
        timer.start(30000)

        tableWidget = QTableWidget(self)
        tableWidget.setRowCount(len(self.items) + 2)
        tableWidget.setColumnCount(7)
        # add up to 1001, remaining 23 pixels are needed by the scrollbar
        tableWidget.setColumnWidth(0, 75)
        tableWidget.setColumnWidth(1, 150)
        tableWidget.setColumnWidth(2, 100)
        tableWidget.setColumnWidth(3, 350)
        tableWidget.setColumnWidth(4, 100)
        tableWidget.setColumnWidth(5, 100)
        tableWidget.setColumnWidth(6, 100)

        layout.addWidget(tableWidget, 2, 0, 1, 2)

        logo = QLabel("hello")
        logo.setPixmap(QtGui.QPixmap(os.getcwd() + "/TUW_logo.png"))
        layout.addWidget(logo, 3, 0, 1, 2)

        toolbar = QToolBar("Page Selector")
        self.addToolBar(toolbar)

        buttonMain = QAction("Main", self)
        buttonMain.setStatusTip("See the main page")
        buttonMain.triggered.connect(lambda: self.renderTable(0, tableWidget))
        toolbar.addAction(buttonMain)

        buttonPlanner = QAction("Planner", self)
        buttonPlanner.setStatusTip("Plan your energy expenditure")
        buttonPlanner.triggered.connect(lambda: self.renderTable(1, tableWidget))
        toolbar.addAction(buttonPlanner)

        self.setStatusBar(QStatusBar(self))
        # Page Setup done

        self.renderTable(0, tableWidget)

        widget = QWidget()
        widget.setLayout(layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

    def renderTable(self, page, tableWidget, nameSearch="name", tagSearch="tags"):
        # page = 0: Main
        # page = 1: PLanner
        tableWidget.clear()
        tableWidget.setRowCount(len(self.items) + 2)
        searchButton = QPushButton("Search")
        nameSearchField = QLineEdit(nameSearch)
        tableWidget.setCellWidget(0, 1, nameSearchField)
        tagSearchField = QLineEdit(tagSearch)
        tableWidget.setCellWidget(0, 2, tagSearchField)
        searchButton.clicked.connect(partial(self.searchFilter, page, tableWidget, nameSearchField, tagSearchField))
        tableWidget.setCellWidget(0, 0, searchButton)

        if nameSearch == "name": nameSearch = ""
        if tagSearch == "tags": tagSearch = ""

        # initialized here to exist beyond the if blocks
        plannerItems = []
        self.labelList = []
        capacityLabel = QLabel("Required Capacity: 0%")
        items = self.items
        if page == 0:
            tableWidget.setColumnWidth(3, 350)
            tableWidget.setColumnWidth(4, 100)
            tableWidget.setRowCount(len(self.items) + 2)
        else:
            tableWidget.setColumnWidth(3, 225)
            tableWidget.setColumnWidth(4, 225)
            itemsToPLan = 0
            for item in self.items:
                if item[6] == True:
                    itemsToPLan += 1
            tableWidget.setRowCount(itemsToPLan + 2)

            hoursLabel = QLabel("Hours:")
            minutesLabel = QLabel("Minutes:")
            tableWidget.setCellWidget(0, 3, hoursLabel)
            tableWidget.setCellWidget(0, 4, minutesLabel)
        row = 1
        for item in items:
            # Filter plan
            if page == 1 and not item[6]:
                continue
            # Filter tag
            tagFound = False
            for tag in item[2]:
                if tagSearch.upper() in tag.upper():
                    tagFound = True
                    break
            # Filter name
            if nameSearch.upper() in item[1].upper() and tagFound:
                name = QLabel(item[1])

                tags = item[2]
                text = ""
                for tag in tags:
                    text += tag + " | "
                tag = QLabel(text[:len(text) - 3])

                # TODO icon
                tableWidget.setCellWidget(row, 1, name)
                tableWidget.setCellWidget(row, 2, tag)
                if page == 0:
                    minutesDec, hours = math.modf(self.currentCapacity / item[5])
                    minutes = int(minutesDec * 60)
                    time = QLabel("Time Of Use Remaining: " + str(int(hours)) + "h " + str(minutes) + "m")
                    self.labelList.append(time)

                    details = QPushButton("Details")
                    details.clicked.connect(partial(self.details, item[0]))
                    details.setIcon(QIcon('glass.png'))
                    edit = QPushButton("Edit")
                    edit.clicked.connect(partial(self.edit, item[0], tableWidget, nameSearch, tagSearch))
                    edit.setIcon(QIcon('pencil.png'))
                    delete = QPushButton("Delete")
                    delete.clicked.connect(partial(self.delete, 0, item[0], tableWidget, nameSearch, tagSearch))
                    delete.setIcon(QIcon('trash.png'))
                    tableWidget.setCellWidget(row, 3, time)
                    tableWidget.setCellWidget(row, 4, details)
                    tableWidget.setCellWidget(row, 5, edit)
                    tableWidget.setCellWidget(row, 6, delete)
                else:
                    hours = QSpinBox()
                    hours.setMinimum(0)
                    hours.setMaximum(24)
                    minutes = QSpinBox()
                    minutes.setMinimum(0)
                    minutes.setMaximum(60)
                    minutes.setSingleStep(5)
                    tempitem = [item, hours, minutes]
                    plannerItems.append(tempitem)
                    details = QPushButton("Details")
                    details.clicked.connect(partial(self.details, item[0]))
                    details.setIcon(QIcon('glass.png'))
                    remove = QPushButton("Remove")
                    remove.clicked.connect(partial(self.delete, 1, item[0], tableWidget, nameSearch, tagSearch))
                    remove.setIcon(QIcon('trash.png'))
                    tableWidget.setCellWidget(row, 3, hours)
                    tableWidget.setCellWidget(row, 4, minutes)
                    tableWidget.setCellWidget(row, 5, details)
                    tableWidget.setCellWidget(row, 6, remove)

                row += 1

        plusButton = QPushButton("+")
        tableWidget.setCellWidget(row, 0, plusButton)
        if page == 0:
            plusButton.clicked.connect(partial(self.createItem, tableWidget, nameSearch, tagSearch))
            tableWidget.setItem(row, 1, QTableWidgetItem("Add New Item"))
        else:
            plusButton.clicked.connect(partial(self.addItemToPlaner, tableWidget))
            tableWidget.setItem(row, 1, QTableWidgetItem("Add Item to Planner"))

            capacityButton = QPushButton("Calculate Capacity")
            capacityButton.clicked.connect(partial(self.calculateCapacity, plannerItems, capacityLabel))
            tableWidget.setCellWidget(row, 3, capacityLabel)
            tableWidget.setCellWidget(row, 4, capacityButton)

        descriptionTimer = QTimer(self)

        # adding action to timer
        descriptionTimer.timeout.connect(lambda: self.calculateTime())
        # update the timer every 30 seconds
        descriptionTimer.start(30000)

    def details(self, itemId):
        item = self.getById(itemId)

        dlg = QDialog(self)
        dlg.setWindowTitle("Details")
        dlg.setGeometry(0, 0, 512, 300)

        layout = QGridLayout()

        nameLabel = QLabel("Name:")
        name = QLabel(item[1])
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(name, 0, 1)

        tagLabel = QLabel("Tags:")
        tags = item[2]
        text = ""
        for tag in tags:
            text += tag + " | "
        tag = QLabel(text[:len(text) - 3])
        layout.addWidget(tagLabel, 1, 0)
        layout.addWidget(tag, 1, 1)

        voltageLabel = QLabel("Voltage:")
        voltage = QLabel(str(item[3]) + "V")
        layout.addWidget(voltageLabel, 2, 0)
        layout.addWidget(voltage, 2, 1)

        currentLabel = QLabel("Current:")
        current = QLabel(str(item[4]) + "A")
        layout.addWidget(currentLabel, 3, 0)
        layout.addWidget(current, 3, 1)

        powerLabel = QLabel("Power:")
        power = QLabel(str(item[5]) + "Wh")
        layout.addWidget(powerLabel, 4, 0)
        layout.addWidget(power, 4, 1)

        dlg.setLayout(layout)

        dlg.exec()

    def edit(self, itemId, tableWidget, nameSearch, tagSearch):
        values = []
        item = self.getById(itemId)

        dlg = QDialog(self)
        dlg.setWindowTitle("Details")
        dlg.setGeometry(0, 0, 512, 150)

        layout = QGridLayout()

        nameLabel = QLabel("Name:")
        name = QLineEdit(item[1])
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(name, 0, 1)
        values.append(name)

        tagLabel = QLabel("Tags:")
        tags = item[2]
        text = ""
        for tag in tags:
            text += tag + " | "
        tag = QLineEdit(text[:len(text) - 3])
        layout.addWidget(tagLabel, 1, 0)
        layout.addWidget(tag, 1, 1)
        values.append(tag)

        explanationLabel1 = QLabel(
            "Before pressing save, please disconnect all devices save for the you are trying to add.")
        explanationLabel2 = QLabel(
            "Leave the device running at what you would consider 'normal use' until told otherwise.")
        layout.addWidget(explanationLabel1, 2, 0, 1, 2)
        layout.addWidget(explanationLabel2, 3, 0, 1, 2)

        #TODO: Differentiate between editing name/tag and synching the device

        save = QPushButton("Save Changes")
        save.clicked.connect(partial(self.changeItem, itemId, values, tableWidget, dlg, nameSearch, tagSearch))
        layout.addWidget(save, 4, 0, 1, 2)
        dlg.setLayout(layout)

        dlg.exec()

    def changeItem(self, itemId, values, tableWidget, dialogue, nameSearch, tagSearch):
        item = self.getById(itemId)
        item[1] = values[0].text()
        tags = values[1].text().split("|")
        for tag in tags:
            tag = tag.strip()
        item[2] = tags
        self.renderTable(0, tableWidget, nameSearch, tagSearch)
        self.db.addEdit(item)
        dialogue.accept()

        # creating a timer object
        timer = QTimer(self)
        # adding action to timer
        timer.singleShot(360000,
                         lambda: self.calibrateItem(itemId, item[1], item[2], tableWidget, nameSearch, tagSearch))

    def addItemToPlaner(self, tableWidget):
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Item")
        dlg.setGeometry(0, 0, 512, 300)

        layout = QGridLayout()

        itemsToAdd = []
        for item in self.items:
            if item[6] == False:
                itemsToAdd.append(item)

        localTable = QTableWidget(self)
        localTable.setRowCount(len(itemsToAdd))
        localTable.setColumnCount(3)
        localTable.setColumnWidth(0, 150)
        localTable.setColumnWidth(1, 202)
        localTable.setColumnWidth(2, 100)
        row = 0
        for itemToAdd in itemsToAdd:
            name = QLabel(itemToAdd[1])
            tags = itemToAdd[2]
            text = ""
            for tag in tags:
                text += tag + " | "
            tag = QLabel(text[:len(text) - 3])
            add = QPushButton("Add Item")
            add.clicked.connect(partial(self.appendItem, itemToAdd, tableWidget, dlg))
            localTable.setCellWidget(row, 0, name)
            localTable.setCellWidget(row, 1, tag)
            localTable.setCellWidget(row, 2, add)
            row += 1
        layout.addWidget(localTable)
        dlg.setLayout(layout)

        dlg.exec()

    def appendItem(self, item, tableWidget, dialogue):
        item[6] = True
        self.renderTable(1, tableWidget)
        dialogue.accept()

    def createItem(self, tableWidget, nameSearch, tagSearch):
        values = []
        dlg = QDialog(self)
        dlg.setWindowTitle("New Item")
        dlg.setGeometry(0, 0, 512, 150)

        layout = QGridLayout()

        nameLabel = QLabel("Name:")
        name = QLineEdit()
        layout.addWidget(nameLabel, 0, 0)
        layout.addWidget(name, 0, 1)
        values.append(name)

        tagLabel = QLabel("Tags:")
        tag = QLineEdit()
        layout.addWidget(tagLabel, 1, 0)
        layout.addWidget(tag, 1, 1)
        values.append(tag)

        explanationLabel1 = QLabel(
            "Before pressing save, please disconnect all devices save for the you are trying to add.")
        explanationLabel2 = QLabel(
            "Leave the device running at what you would consider 'normal use' until told otherwise.")
        layout.addWidget(explanationLabel1, 2, 0, 1, 2)
        layout.addWidget(explanationLabel2, 3, 0, 1, 2)

        save = QPushButton("Create New Item")
        save.clicked.connect(partial(self.addItem, values, tableWidget, dlg, nameSearch, tagSearch))
        layout.addWidget(save, 4, 0, 1, 2)
        dlg.setLayout(layout)

        dlg.exec()

    def addItem(self, values, tableWidget, dialogue, nameSearch, tagSearch):
        newItem = []
        itemId = 0
        for item in self.items:
            if item[0] > itemId:
                itemId = item[0]
        itemId += 1
        newItem.append(itemId)
        newItem.append(values[0].text())
        tags = values[1].text().split("|")
        for tag in tags:
            tag = tag.strip()
        newItem.append(tags)
        newItem.append(1.0)
        newItem.append(1.0)
        newItem.append(1.0)
        newItem.append(False)
        self.items.append(newItem)
        self.db.addEdit(newItem)
        self.renderTable(0, tableWidget)
        dialogue.accept()

        # creating a timer object
        timer = QTimer(self)
        # adding action to timer
        timer.singleShot(360000,
                         lambda: self.calibrateItem(itemId, newItem[1], newItem[2], tableWidget, nameSearch, tagSearch))

    def delete(self, page, itemId, tableWidget, nameSearch, tagSearch):
        item = self.getById(itemId)
        if page == 0:
            self.items.remove(item)
            self.db.delete(item)
        else:
            item[6] = False
        self.renderTable(page, tableWidget, nameSearch, tagSearch)

    # Help Functions below here
    def getById(self, itemId):
        for item in self.items:
            if item[0] == itemId:
                return item
        return []

    def calculateCapacity(self, items, label):
        requiredCapacity = 0
        for item in items:
            hours = float(item[1].text())
            minutes = float(item[2].text())
            hours += float(minutes / 60)
            requiredCapacity += hours * item[0][5]
        label.setText("Required Capacity: " + str(round((requiredCapacity / self.maxCapacity) * 100)) + "%")

    def calculateTime(self):
        for item, label in zip(self.items, self.labelList):
            if label:
                minutesDec, hours = math.modf(self.currentCapacity / item[5])
                minutes = int(minutesDec * 60)
                label.setText("Time Of Use Remaining: " + str(int(hours)) + "h " + str(minutes) + "m")

    def searchFilter(self, page, tableWidget, nameSearchField, tagSearchField):
        nameSearch = nameSearchField.text()
        tagSearch = tagSearchField.text()
        self.renderTable(page, tableWidget, nameSearch, tagSearch)

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

    def calibrateItem(self, itemId, name, itemTags, tableWidget, nameSearch, tagSearch):
        item = self.getById(itemId)
        item[1] = name
        item[2] = itemTags

        avgVoltage = sum(self.savedVoltage) / len(self.savedVoltage)
        item[3] = float(f'{avgVoltage:.3f}')
        avgCurrent = sum(self.savedCurrent) / len(self.savedCurrent)
        item[4] = float(f'{avgCurrent:.3f}')
        avgPower = sum(self.savedPower) / len(self.savedPower)
        item[5] = float(f'{avgPower:.3f}')

        self.renderTable(0, tableWidget, nameSearch, tagSearch)
        self.db.addEdit(item)
        dlg = QDialog(self)
        dlg.setWindowTitle("Item Calibrated")
        dlg.setGeometry(0, 0, 512, 150)

        layout = QGridLayout()

        infoLabel = QLabel("Your Item has now been calibrated and can be unplugged.")
        layout.addWidget(infoLabel, 0, 0)
        dlg.setLayout(layout)
        dlg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    custom_font = QFont('Arial', 14)
    app.setFont(custom_font)
    window = MainWindow()
    window.show()

    app.exec()
