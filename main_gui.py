import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    batteryCharge = 75
    # ID, Name, Tags
    items = [
        [0, "Lamp", ["Kitchen", "Living Room"]],
        [1, "Blender", ["Kitchen"]],
        [2, "Blender", ["Kitchen"]],
        [3, "Blender", ["Kitchen"]],
        [4, "Blender", ["Kitchen"]],
        [5, "Blender", ["Kitchen"]],
        [6, "Blender", ["Kitchen"]],
        [7, "Blender", ["Kitchen"]],
        [8, "Blender", ["Kitchen"]],
        [9, "Blender", ["Kitchen"]],
        [10, "Blender", ["Kitchen"]],
        [11, "Blender", ["Kitchen"]],
        [12, "Blender", ["Kitchen"]],
        [13, "Blender", ["Kitchen"]],
        [14, "Blender", ["Kitchen"]],
        [15, "Blender", ["Kitchen"]],
        [16, "Blender", ["Kitchen"]],
        [17, "Blender", ["Kitchen"]]
    ]

    def onMyToolBarButtonClick(self, s):
        print("click", s)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Main Page")
        self.setGeometry(0,0, 1024, 600)

        #TODO: Use a QStackedLayout to switch between pages

        # Setup Main page

        toolbar = QToolBar("Page Selector")
        self.addToolBar(toolbar)

        buttonHistory = QAction("History", self)
        buttonHistory.setStatusTip("See Historic Data")
        buttonHistory.triggered.connect(self.onMyToolBarButtonClick)
        toolbar.addAction(buttonHistory)

        buttonSettings = QAction("Settings", self)
        buttonSettings.setStatusTip("See your Settings")
        buttonSettings.triggered.connect(self.onMyToolBarButtonClick)
        toolbar.addAction(buttonSettings)


        buttonPlanner = QAction("Planner", self)
        buttonPlanner.setStatusTip("Plan your energy expenditure")
        buttonPlanner.triggered.connect(self.onMyToolBarButtonClick)
        toolbar.addAction(buttonPlanner)

        buttonMain = QAction("Main", self)
        buttonMain.setStatusTip("See the main page")
        buttonMain.triggered.connect(self.onMyToolBarButtonClick)
        toolbar.addAction(buttonMain)

        self.setStatusBar(QStatusBar(self))

        layout = QGridLayout()

        chargeLabel = QLabel("Charge: "+str(self.batteryCharge) +"%")
        chargeBar = QProgressBar(self)
        chargeBar.setValue(self.batteryCharge)
        chargeBar.setGeometry(0,0, 600, 100)

        layout.addWidget(chargeLabel, 0, 0)
        layout.addWidget(chargeBar, 0, 1)

        tableWidget = QTableWidget(self)
        tableWidget.setRowCount(len(self.items)+1)
        tableWidget.setColumnCount(6)
        #add up to 1000
        tableWidget.setColumnWidth(0, 50)
        tableWidget.setColumnWidth(1, 150)
        tableWidget.setColumnWidth(2, 261)
        tableWidget.setColumnWidth(3, 300)
        tableWidget.setColumnWidth(4, 100)
        tableWidget.setColumnWidth(5, 100)

        layout.addWidget(tableWidget, 2, 0, 2, 0)

        # Page Setup done

        row = 0
        for item in self.items:
            name = QLabel(item[1])
            time = QLabel("Time Of Use Remaining: 7H 23M")
            details = QPushButton("Details")
            delete = QPushButton("Delete")
            #icon
            tableWidget.setCellWidget(row, 1, name)
            #tags
            tableWidget.setCellWidget(row, 3, time)
            tableWidget.setCellWidget(row, 4, details)
            tableWidget.setCellWidget(row, 5, delete)
            row+=1

        plusButton = QPushButton("+")
        tableWidget.setCellWidget(row, 0, plusButton)

        tableWidget.setItem(row, 1, QTableWidgetItem("Add New Item"))

        widget = QWidget()
        widget.setLayout(layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()