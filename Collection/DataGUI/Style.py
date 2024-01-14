"""Widget-derived custom classes and style sheet"""
import math

from abc import ABC, ABCMeta, abstractmethod
from collections import namedtuple
from numpy import linspace
from PyQt5.QtCore import Qt, QFileSystemWatcher
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QFrame, QPlainTextEdit, QGridLayout, QLabel, QLineEdit


class StateIndicator(QFrame):
    """Visual indicator for active and inactive states"""
    def __init__(self, active_color, inactive_color, dia=20):
        super().__init__()
        self.setFixedSize(dia, dia)
        self.dia = dia
        self.setFrameStyle(QFrame.Panel | QFrame.Plain)

        self.active = active_color
        self.inactive = inactive_color
        self.set_active(False)
        self.on = False

    def set_active(self, active=True):
        self.on = active
        if active:
            self.setStyleSheet(f"background-color: {self.active}; border-radius: {self.dia//2}px;")
        else:
            self.setStyleSheet(f"background-color: {self.inactive}; border-radius: {self.dia//2}px;")
        self.update()

    def is_active(self):
        return self.on


class QABCMeta(ABCMeta, type(QGridLayout)):
    """Metaclass to combine ABC and QGridLayout"""


class StimMenu(ABC, metaclass=QABCMeta):
    """Built-in stimulus menus should subclass this with validate() and get_args() implemented"""
    def __init__(self, stimname):
        self.stimname = stimname
        self.fields = None  # Subclass should set these in init (named tuples are convenient)
        self.labels = None  # Subclass should set these in init (named tuples are convenient)
        self.setSpacing(5)
        self.setColumnStretch(0, 2)

    def populate(self):
        for row, label in enumerate(self.labels):
            label.setObjectName("MenuLabel")
            self.addWidget(label, row, 0, Qt.AlignRight)
        for row, field in enumerate(self.fields):
            self.addWidget(field, row, 1)
    
    def clear(self):
        """Clear all menu elements and set parent of self to None"""
        for element in self.fields + self.labels:
            element.setParent(None)
        self.setParent(None)

    @abstractmethod
    def validate(self, window=None):
        """Return (bool, str) that indicates whether values in menu fields are valid for the corresponding script"""

    @abstractmethod
    def get_args(self):
        """Return list of args to be passed to the corresponding stimulus script"""


class GridStimMenu(QGridLayout, StimMenu):
    """Menu that corresponds to GridFlash built-in stimulus."""
    def __init__(self):
        super().__init__(stimname="GridFlash")
        FieldTuple = namedtuple("FieldTuple", ["minfield", "maxfield", "stepfield"])
        LabelTuple = namedtuple("LabelTuple", ["minlabel", "maxlabel", "steplabel"])
        
        minfield = QLineEdit()
        minfield.setValidator(QDoubleValidator(1, 100, 2))
        maxfield = QLineEdit()
        maxfield.setValidator(QDoubleValidator(1, 100, 2))
        stepfield = QLineEdit()
        self.fields = FieldTuple(minfield, maxfield, stepfield)

        minlabel = QLabel("Freq. Minimum (Hz):")
        maxlabel = QLabel("Freq. Maximum (Hz):")
        steplabel = QLabel("Step count:")
        self.labels = LabelTuple(minlabel, maxlabel, steplabel)

        self.populate()

    def validate(self, window=None):
        if not self.fields.minfield.text().strip():
            return False, "Minimum freq. missing."
        if not self.fields.maxfield.text().strip():
            return False, "Maximum freq. missing."
        if not self.fields.stepfield.text().strip():
            return False, "Step count missing."
        if not float(self.fields.minfield.text()) <= float(self.fields.minfield.text()):
            return False, "Minimum freq. cannot be greater than maximum freq."
        return True, ""

    def get_args(self):
        """Return usable args for running the stim script"""
        rows = cols = math.ceil(math.sqrt(int(self.fields.stepfield.text())))
        min, max, steps = (float(self.fields.minfield.text()),
                           float(self.fields.maxfield.text()),
                           int(self.fields.stepfield.text()))
        return linspace(min, max, steps), rows, cols


class RandomPromptMenu(QGridLayout, StimMenu):
    """Menu that corresponds to built-in RandomPrompt built-in stimulus."""
    def __init__(self):
        super().__init__(stimname="RandomPrompt")
        FieldTuple = namedtuple("FieldTuple", ["pfield", "ppbfield", "dfield", "cfield"])
        LabelTuple = namedtuple("LabelTuple", ["plabel", "ppblabel", "dlabel", "clabel"])
        self.iwindow = None

        pfield = QLineEdit()  # Prompt field
        ppbfield = QLineEdit()  # Prompts per block field
        ppbfield.setValidator(QIntValidator(1, 1000))
        cfield = QLineEdit()  # Prompt cooldown field
        cfield.setPlaceholderText("1")
        cfield.setValidator(QDoubleValidator(0.25, 10000, 2))
        dfield = QLineEdit()  # Prompt duration field
        dfield.setValidator(QDoubleValidator(0.25, 1000, 2))
        self.fields = FieldTuple(pfield, ppbfield, dfield, cfield)

        plabel = QLabel("Prompt text:")
        ppblabel = QLabel("Prompts per block:")
        dlabel = QLabel("Prompt duration:")
        clabel = QLabel("Prompt cooldown:")
        self.labels = LabelTuple(plabel, ppblabel, dlabel, clabel)

        self.populate()

    def validate(self, iwindow=None):
        self.iwindow = iwindow
        prompt = self.fields.pfield.text().strip()
        
        if not prompt:
            return False, "No prompt text supplied."
        if not self.fields.ppbfield.text().strip():
            return False, "Prompts per block not supplied."
        if not self.fields.dfield.text().strip():
            return False, "No duration supplied."
        if not self.fields.cfield.text().strip():
            return False, "No cooldown supplied."
        
        ppb = int(self.fields.ppbfield.text())
        cooldown = float(self.fields.cfield.text())
        dur = float(self.fields.dfield.text())
        if cooldown < dur:
            return False, "Duration longer than cooldown."

        prompt_time = ppb * cooldown
        total_time = int(self.iwindow.fblength.text())
        if prompt_time/total_time > 0.75:
            return False, "Too many prompts for one block."

        return True, ""
    
    def get_args(self):
        if not self.iwindow:
            raise Exception("Args not yet validated.")
        return (self.fields.pfield.text().strip(), int(self.fields.ppbfield.text()), float(self.fields.cfield.text()), 
                self.iwindow.fstimcycle.text().strip(), int(self.iwindow.fblength.text()), float(self.fields.dfield.text()))


class QTextEditLogger(QPlainTextEdit):
    """Monitors logfile for updates and prints to GUI"""
    def __init__(self, filepath, parent_layout=None):
        super().__init__()
        self.logfile = open(filepath, buffering=1)
        self.path = filepath
        self.readpos = 0

        self.watcher = QFileSystemWatcher()
        self.watcher.addPath(filepath)
        self.watcher.fileChanged.connect(self.update_log_window)

        self.setReadOnly(True)
        self.setBackgroundVisible(True)
        if parent_layout:
            self.mount(parent_layout)

    def mount(self, layout):
        layout.addWidget(self)

    def update_log_window(self):
        if self.logfile.closed:
            return
        self.logfile.seek(self.readpos)
        line = self.logfile.read()
        self.appendPlainText(line)
        self.readpos = self.logfile.tell()

    def reset_file(self, filepath):
        if self.path:
            self.watcher.removePath(self.path)
        if not self.logfile.closed:
            self.logfile.close()
        self.logfile = open(filepath, buffering=1)
        self.watcher.addPath(filepath)
        self.path = filepath
        self.readpos = 0

    def end(self):
        self.logfile.close()
        self.watcher.removePath(self.path)
        self.path = None

    def __exit__(self, type, val, traceback):
        self.logfile.close()
        print(traceback)


class Style:
    style = """
    QFrame {
        color: white;
        background-color: #1d2324;
        border-radius: 10px;
    }
    #FullFrame { background-color: #43484d;
                 border-radius: 0px;
    }
    #ModeFrame { background-color: #1d2324; 
                 border-radius: 0px;}
    QLabel {
        color: #c5cfde;
        font: Candara;
        font-size: 18px;
    }
    #FieldLabels { font-weight: bold; }
    #ErrorLabel { color: #c20808 }
    #MenuLabel { font-size: 14px; }
    #Divider { background-color: #6c6f70; }
    QPushButton {
        background-color: #007bff;
        color:  white;
        border: none;
        padding: 8px 12px;
        border-radius: 5px;
        font-size: 18px;
    }
    QPushButton:hover {
        background-color: #0056b3;
    }
    QPushButton:pressed {
        background-color: #003d80;
    }
    QPushButton:disabled {
        background-color: #1d2324;
        color: white;
    }
    QLineEdit {
        padding: 2px;
        margin: 2px;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 18px;
    }
    QTextEdit {
        background-color: white;
        border: 1 px solid #ccc;
        border-radius: 5px;
        padding: 2px;
        font-size: 16px;
        color: black;
        margin: 2px;
    }
    QPlainTextEdit{
        font-family: MonoSpace;
        font-size: 13px;
    }
    QComboBox {
        padding: 2px;
        color: white;
        background-color: #43484d;
        font-size: 16px;
    }
    QComboBox QAbstractItemView{
        color: white;
        background-color: #1d2324;
        border-radius: 0px;
    }"""