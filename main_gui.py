import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    batteryCharge = 75

    def onMyToolBarButtonClick(self, s):
        print("click", s)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Main Page")
        self.setGeometry(0,0, 1024, 600)

        #TODO: Use a QStackedLayout to switch between pages

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
        layout.addWidget(chargeBar, 0, 1)#, 10, 1)

        tableWidget = QTableWidget(self)
        tableWidget.setRowCount(10)
        tableWidget.setColumnCount(5)

        layout.addWidget(tableWidget, 2, 0, 2, 0)

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