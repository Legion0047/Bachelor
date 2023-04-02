import sys
import math

from PyQt5.QtWidgets import *
from functools import partial

from persistence import persistence

class MainWindow(QMainWindow):
    db = persistence()
    realCapacity = 960  # WH
    reservedCapacity = 60  # WH
    maxCapacity = realCapacity - reservedCapacity  # WH
    currentCapacity = 512  # WH
    batteryCharge = round((currentCapacity / maxCapacity) * 100)  # %


    db.load()
    # ID, Name, Tags, Voltage V, Current A, Power Wh, in planner
    items = [
        [0, "Lamp", ["Kitchen", "Living Room"], 230, 23, 10.5, False],
        [1, "Blender", ["Kitchen"], 220, 2.2, 600, False]
    ]


    def __init__(self):
        super().__init__()

        self.setWindowTitle("Main Page")
        self.setGeometry(0, 0, 1024, 600)
        # Setup Main page
        layout = QGridLayout()

        chargeLabel = QLabel("Current Charge:")
        chargeBar = QProgressBar(self)
        chargeBar.setValue(self.batteryCharge)
        chargeBar.setGeometry(0, 0, 600, 100)

        layout.addWidget(chargeLabel, 0, 0)
        layout.addWidget(chargeBar, 0, 1)

        tableWidget = QTableWidget(self)
        tableWidget.setRowCount(len(self.items) + 2)
        tableWidget.setColumnCount(7)
        # add up to 1001, remaining 23 pixels are needed by the scrollbar
        tableWidget.setColumnWidth(0, 50)
        tableWidget.setColumnWidth(1, 150)
        tableWidget.setColumnWidth(2, 211)
        tableWidget.setColumnWidth(3, 250)
        tableWidget.setColumnWidth(4, 100)
        tableWidget.setColumnWidth(5, 100)
        tableWidget.setColumnWidth(6, 100)

        layout.addWidget(tableWidget, 2, 0, 2, 0)

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
        capacityLabel = QLabel("Required Capacity: 0%")
        items = self.items
        if page == 0:
            tableWidget.setColumnWidth(3, 250)
            tableWidget.setColumnWidth(4, 100)
            tableWidget.setRowCount(len(self.items) + 2)
        else:
            tableWidget.setColumnWidth(3, 175)
            tableWidget.setColumnWidth(4, 175)
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
            if page == 1 and not item[6]:
                continue
            tagFound = False
            for tag in item[2]:
                if tagSearch.upper() in tag.upper():
                    tagFound = True
                    break
            if nameSearch.upper() in item[1].upper() and tagFound:
                name = QLabel(item[1])

                tags = item[2]
                text = ""
                for tag in tags:
                    text += tag + " | "
                tag = QLabel(text[:len(text) - 3])

                #TODO icon
                tableWidget.setCellWidget(row, 1, name)
                tableWidget.setCellWidget(row, 2, tag)
                if page == 0:
                    minutesDec, hours = math.modf(self.currentCapacity / item[5])
                    minutes = int(minutesDec * 60)
                    time = QLabel("Time Of Use Remaining: " + str(int(hours)) + "h " + str(minutes) + "m")

                    details = QPushButton("Details")
                    details.clicked.connect(partial(self.details, item[0]))
                    edit = QPushButton("Edit")
                    edit.clicked.connect(partial(self.edit, item[0], tableWidget, nameSearch, tagSearch))
                    delete = QPushButton("Delete")
                    delete.clicked.connect(partial(self.delete, 0, item[0], tableWidget, nameSearch, tagSearch))
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
                    tempitem = [item,hours,minutes]
                    plannerItems.append(tempitem)
                    details = QPushButton("Details")
                    details.clicked.connect(partial(self.details, item[0]))
                    remove = QPushButton("Delete")
                    remove.clicked.connect(partial(self.delete, 1, item[0], tableWidget, nameSearch, tagSearch))
                    tableWidget.setCellWidget(row, 3, hours)
                    tableWidget.setCellWidget(row, 4, minutes)
                    tableWidget.setCellWidget(row, 5, details)
                    tableWidget.setCellWidget(row, 6, remove)

                row += 1

        plusButton = QPushButton("+")
        tableWidget.setCellWidget(row, 0, plusButton)
        if page == 0:
            plusButton.clicked.connect(partial(self.createItem, tableWidget))
            tableWidget.setItem(row, 1, QTableWidgetItem("Add New Item"))
        else:
            plusButton.clicked.connect(partial(self.addItemToPlaner, tableWidget))
            tableWidget.setItem(row, 1, QTableWidgetItem("Add Item to Planner"))

            capacityButton = QPushButton("Calculate Capacity")
            capacityButton.clicked.connect(partial(self.calculateCapacity, plannerItems, capacityLabel))
            tableWidget.setCellWidget(row, 3, capacityLabel)
            tableWidget.setCellWidget(row, 4, capacityButton)

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

        tagLabel = QLabel("Name:")
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
        dlg.setGeometry(0, 0, 512, 300)

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

        voltageLabel = QLabel("Voltage:")
        voltage = QLineEdit(str(item[3]) + " V")
        layout.addWidget(voltageLabel, 2, 0)
        layout.addWidget(voltage, 2, 1)
        values.append(voltage)

        currentLabel = QLabel("Current:")
        current = QLineEdit(str(item[4]) + " A")
        layout.addWidget(currentLabel, 3, 0)
        layout.addWidget(current, 3, 1)
        values.append(current)

        powerLabel = QLabel("Power:")
        power = QLineEdit(str(item[5]) + " Wh")
        layout.addWidget(powerLabel, 4, 0)
        layout.addWidget(power, 4, 1)
        values.append(power)

        save = QPushButton("Save Changes")
        save.clicked.connect(partial(self.changeItem, itemId, values, tableWidget, dlg, nameSearch, tagSearch))
        layout.addWidget(save, 5, 0, 1, 2)
        dlg.setLayout(layout)

        dlg.exec()

    def changeItem(self, itemId, values, tableWidget, dialogue, nameSearch, tagSearch):
        item = self.getById(itemId)
        item[1] = values[0].text()
        tags = values[1].text().split("|")
        for tag in tags:
            tag = tag.strip()
        item[2] = tags
        value, refuse = values[2].text().split(" ")
        item[3] = float(value)
        value, refuse = values[3].text().split(" ")
        item[4] = float(value)
        value, refuse = values[4].text().split(" ")
        item[5] = float(value)
        self.renderTable(0, tableWidget, nameSearch, tagSearch)
        self.db.edit(item)
        dialogue.accept()

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

    def createItem(self, tableWidget):
        values = []
        dlg = QDialog(self)
        dlg.setWindowTitle("New Item")
        dlg.setGeometry(0, 0, 512, 300)

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

        voltageLabel = QLabel("Voltage:")
        voltage = QLineEdit()
        layout.addWidget(voltageLabel, 2, 0)
        layout.addWidget(voltage, 2, 1)
        values.append(voltage)

        currentLabel = QLabel("Current:")
        current = QLineEdit()
        layout.addWidget(currentLabel, 3, 0)
        layout.addWidget(current, 3, 1)
        values.append(current)

        powerLabel = QLabel("Power:")
        power = QLineEdit()
        layout.addWidget(powerLabel, 4, 0)
        layout.addWidget(power, 4, 1)
        values.append(power)

        save = QPushButton("Create New Item")
        save.clicked.connect(partial(self.addItem, values, tableWidget, dlg))
        layout.addWidget(save, 5, 0, 1, 2)
        dlg.setLayout(layout)

        dlg.exec()

    def addItem(self, values, tableWidget, dialogue):
        newItem = []
        # TODO Replace this in the future
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
        newItem.append(float(values[2].text()))
        newItem.append(float(values[3].text()))
        newItem.append(float(values[4].text()))
        newItem.append(False)
        # End of TODO
        self.items.append(newItem)
        self.db.add(item)
        self.renderTable(0, tableWidget)
        dialogue.accept()

    def delete(self, page, itemId, tableWidget, nameSearch, tagSearch):
        item = self.getById(itemId)
        if page == 0:
            self.items.remove(item)
            self.db.delete(item)
        else:
            item[6] = False
        self.renderTable(page, tableWidget, nameSearch, tagSearch)

    #Help Functions below here
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
            hours += float(minutes/60)
            requiredCapacity += hours*item[0][5]
        label.setText("Required Capacity: "+str(round((requiredCapacity / self.maxCapacity) * 100))+"%")

    def searchFilter(self, page, tableWidget, nameSearchField, tagSearchField):
        nameSearch = nameSearchField.text()
        tagSearch = tagSearchField.text()
        self.renderTable(page, tableWidget, nameSearch, tagSearch)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
