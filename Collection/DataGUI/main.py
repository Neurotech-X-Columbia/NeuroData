"""Data Collection GUI v1.0.0"""
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QSizePolicy)
from Windows import CollectionWindow, InfoWindow, ModeWindow
from Style import Style

# Multi-page structure adapted from 
# https://stackoverflow.com/questions/56867107/how-to-make-a-multi-page-application-in-pyqt5


class DataCollectionGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pages = {}
        self.setWindowTitle("Data Collection GUI")
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setCentralWidget(self.stack)

        mwindow = ModeWindow()
        mwindow.modesig.connect(self.init)
        self.register(mwindow, 'mode')
        self.stack.setCurrentWidget(mwindow)

        self.setStyleSheet(Style.style)
        self.show()

    @pyqtSlot(bool)
    def init(self, boardless=False):
        if boardless:
            self.setWindowTitle("Data Collection GUI (Boardless Mode)")
        cwindow = CollectionWindow()
        self.register(cwindow, 'collect')
        self.register(InfoWindow(cwindow, boardless), 'info')
        self.stack.setCurrentWidget(self.pages['info'])

    @pyqtSlot(str, bool)
    def goto(self, name, reset=False):
        widget = self.pages[name]
        if reset:
            widget.reset()
        self.stack.setCurrentWidget(widget)

    def register(self, widget, name):
        self.pages[name] = widget
        self.stack.addWidget(widget)
        widget.gosig.connect(self.goto)

    def closeEvent(self, event):
        cwin = self.pages.get('collect', None)
        if self.stack.currentWidget() == cwin:
            cwin.csession.error_flag.set()
        event.accept()


if __name__ == "__main__":
    app = QApplication([])
    gui = DataCollectionGUI()
    app.exec_()
