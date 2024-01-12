import BoardBridge
import BoardlessBridge

from brainflow import BrainFlowInputParams, BrainFlowError, LogLevels
from brainflow.board_shim import BoardShim
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer, QTime, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (QFrame, QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QFileDialog, 
                             QVBoxLayout, QHBoxLayout, QGridLayout)
from threading import Thread
from time import sleep
from Style import StateIndicator, QTextEditLogger, GridStimMenu, RandomPromptMenu
from Stimuli import GridFlash, RandomPrompt

import json
import os


def create_empty_info():
    return {
        "SessionParams": {
            "SubjectName": "",
            "ProjectName": "",
            "ResponseType": "",
            "StimulusType": "",
            "BlockLength": "",
            "BlockCount": "",
            "StimCycle": ""
        },
        "HardwareParams": {
            "SampleRate": "",
            "HeadsetConfiguration": "",
            "HeadsetModel": "",
            "BufferSize": "100000"
        },
        "Description": "",
        "Annotations": [],
        "Date": datetime.now().strftime("%m-%d-%y"),
        "Time": datetime.now().strftime("%H:%M"),
        "FileID": ""
        }


def init_combobox(cbox, default, *options):
    cbox.setCurrentText(default)
    cbox.addItems(options)


class PageWindow(QFrame):
    """Allows page-switching functionality"""
    gosig = pyqtSignal(str, bool)

    def goto(self, name, reset=False):
        self.gosig.emit(name, reset)


class ModeWindow(PageWindow):
    """Choose between test and regular mode."""
    modesig = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setObjectName("ModeFrame")
        self.setContentsMargins(60, 60, 60, 60)
        self.regular_button = QPushButton("Collection Mode")
        self.regular_button.setStyleSheet("padding: 20px; border: 10px; ")
        self.regular_button.pressed.connect(self.set_regular)
        self.boardless_button = QPushButton("Test Mode (Boardless)")
        self.boardless_button.setStyleSheet("padding: 20px; border: 10px; ")
        self.boardless_button.pressed.connect(self.set_boardless)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.regular_button)
        self.layout.addWidget(self.boardless_button)

    def set_boardless(self):
        self.modesig.emit(True)

    def set_regular(self):
        self.modesig.emit(False)


class InfoWindow(PageWindow):
    """Accepts and validates input for info.json"""
    boardmap = {'Cyton': (0, 250),
                'CytonDaisy': (2, 125)}
    stimmap = {'GridFlash': GridFlash,
               'RandomPrompt': RandomPrompt}
    buffsize_d = 100000
    buffsize_max = 450000
    buffsize_min = 3000
    blengthmax = 3600
    bcountmax = 360

    def __init__(self, collection_window, boardless=False):
        """Create elements"""
        super().__init__()
        self.boardless = boardless
        self.setObjectName("FullFrame")
        self.date = datetime.now().strftime("%m-%d-%y")
        self.time = datetime.now().strftime("%H:%M")
        self.infodict = create_empty_info()
        self.sespath = None
        self.infodict['Date'] = self.date
        self.infodict['Time'] = self.time
        self.board = None
        self.stimscript = None

        # Directory Row
        self.dirlabel = QLabel("Session directory: ")
        self.curdir = QLabel(os.getcwd())
        self.dir_select = QPushButton("Browse")
        self.dir_select.clicked.connect(self.get_directory)
        self.dirframe = QFrame()
        self.dirframe.setFrameStyle(QFrame.Panel | QFrame.Plain)

        # Session Parameters
        self.sname = QLabel("Subject name:")
        self.pname = QLabel("Project name:")
        self.rtype = QLabel("Response type:")
        self.stype = QLabel("Stimulus type:")
        self.blength = QLabel("Block length (s):")
        self.bcount = QLabel("Block count:")
        self.stimcycle = QLabel("Stimulus cycle:")
        self.description = QLabel("Description")
        self.fsname = QLineEdit()
        self.fpname = QLineEdit()
        self.frtype = QComboBox()
        init_combobox(self.frtype, "SSVEP", "SSVEP", "ERP", "other")
        self.fstype = QComboBox()
        init_combobox(self.fstype, "visual", "visual", "audio", "other")
        self.fblength = QLineEdit()
        self.fblength.setValidator(QIntValidator(1, self.blengthmax))
        self.fbcount = QLineEdit()
        self.fbcount.setValidator(QIntValidator(1, self.blengthmax))
        self.fstimcycle = QLineEdit()
        self.fstimcycle.setPlaceholderText("Ex: 10101")
        self.fdescription = QTextEdit()
        self.fdescription.setPlaceholderText("Ex: SSVEP freq. 7/9/13 Hz GUI v1.2")
        self.fdescription.setMinimumHeight(115)
        self.sesframe = QFrame()
        self.sesframe.setFrameStyle(QFrame.Panel | QFrame.Plain)
        self.errdiv = QFrame()
        self.errdiv.setFrameStyle(QFrame.HLine | QFrame.Plain)
        self.errdiv.setObjectName("Divider")
        self.datelabel = QLabel(self.date)
        self.timelabel = QLabel(self.time)
        self.errlabel = QLabel()
        self.errlabel.setObjectName("ErrorLabel")

        # Hardware Parameters
        self.hardframe = QFrame()
        self.hardframe.setFrameStyle(QFrame.Panel | QFrame.Plain)
        self.config = QLabel("Headset configuration:")
        self.model = QLabel("Headset model:")
        self.buffsize = QLabel("Buffer size (samples):")
        self.serialport = QLabel("Board serial port: ")
        self.stimscript = QLabel("Stimulus script:")
        self.fconfig = QComboBox()
        init_combobox(self.fconfig, "standard", "Standard", "Occipital", "Other")
        self.fmodel = QComboBox()
        init_combobox(self.fmodel, "CytonDaisy", "CytonDaisy", "Cyton")
        self.fbuffsize = QLineEdit()
        self.fbuffsize.setPlaceholderText(str(self.buffsize_d))
        self.fbuffsize.setValidator(QIntValidator(self.buffsize_min, self.buffsize_max))
        self.fserialport = QLineEdit()
        self.fserialport.setPlaceholderText("Ex: COM4")
        self.fstimscript = QComboBox()
        init_combobox(self.fstimscript, "External/None", "External/None", "Grid Flash", "Random Prompting")
        self.fstimscript.currentTextChanged.connect(self.stim_config)

        # Confirmation
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.confirm)

        self.dir = self.curdir.text()
        self.colwin = collection_window
        self.init()

    def init(self):
        """Place elements"""
        layout = QVBoxLayout()

        # Directory Selector
        dirlayout = QGridLayout(self.dirframe)
        dirlayout.addWidget(self.dirlabel, 0, 0, 1, 2)
        dirlayout.addWidget(self.curdir, 0, 2)
        dirlayout.addWidget(self.dir_select, 0, 3)
        layout.addWidget(self.dirframe)

        # Parameter layout
        middlebar = QHBoxLayout()

        # Session Parameters and Error Box
        seslayout = QGridLayout(self.sesframe)
        seslayout.addWidget(self.sname, 0, 0)
        seslayout.addWidget(self.fsname, 0, 1)
        seslayout.addWidget(self.pname, 1, 0)
        seslayout.addWidget(self.fpname, 1, 1)
        seslayout.addWidget(self.rtype, 2, 0)
        seslayout.addWidget(self.frtype, 2, 1)
        seslayout.addWidget(self.stype, 3, 0)
        seslayout.addWidget(self.fstype, 3, 1)
        seslayout.addWidget(self.blength, 4, 0)
        seslayout.addWidget(self.fblength, 4, 1)
        seslayout.addWidget(self.bcount, 5, 0)
        seslayout.addWidget(self.fbcount, 5, 1)
        seslayout.addWidget(self.stimcycle, 6, 0)
        seslayout.addWidget(self.fstimcycle, 6, 1)
        seslayout.addWidget(self.description, 7, 0, 1, 2)
        seslayout.addWidget(self.fdescription, 8, 0, 1, 2)

        middlebar.addWidget(self.sesframe)

        # Hardware Parameters
        rightlayout = QVBoxLayout()
        hardlayout = QGridLayout(self.hardframe)
        hardlayout.setRowStretch(6, 5)
        hardlayout.setRowStretch(7, 1)
        hardlayout.setRowMinimumHeight(6, 2)
        hardlayout.addWidget(self.config, 1, 0)
        hardlayout.addWidget(self.fconfig, 1, 1)
        hardlayout.addWidget(self.model, 2, 0)
        hardlayout.addWidget(self.fmodel, 2, 1)
        hardlayout.addWidget(self.buffsize, 3, 0)
        hardlayout.addWidget(self.fbuffsize, 3, 1)
        hardlayout.addWidget(self.serialport, 4, 0)
        hardlayout.addWidget(self.fserialport, 4, 1)
        hardlayout.addWidget(self.stimscript, 5, 0)
        hardlayout.addWidget(self.fstimscript, 5, 1)

        hardlayout.addWidget(self.errdiv, 7, 0, 1, 2, Qt.AlignBottom)
        hardlayout.addWidget(self.datelabel, 8, 0, Qt.AlignBottom)
        hardlayout.addWidget(self.timelabel, 8, 1, Qt.AlignBottom | Qt.AlignRight)
        hardlayout.addWidget(self.errlabel, 9, 0, 1, 2, Qt.AlignBottom)
        rightlayout.addWidget(self.hardframe)
        self.hardlayout = hardlayout

        middlebar.addLayout(rightlayout)

        layout.addLayout(middlebar)
        layout.addWidget(self.confirm_button)
        self.setLayout(layout)

    def reset(self):
        """Ready window for new collection session"""
        self.fbcount.clear()
        self.fblength.clear()
        self.fstimcycle.clear()
        self.fdescription.clear()
        self.fstimscript.setCurrentText("External/None")
        if menu := self.hardlayout.itemAtPosition(6, 0):
            menu.clear()

        self.date = datetime.now().strftime("%m-%d-%y")
        self.time = datetime.now().strftime("%H:%M")
        self.infodict['Date'] = self.date
        self.infodict['Time'] = self.time
        self.stimscript = None

    def confirm(self):
        """Validate info, proceed to collection if valid"""
        if not (res := self.check_info())[0]:
            self.errlabel.setText(f"Error: {res[1]}")
        else:
            self.errlabel.setText(" ")
            self.save_info()
            if self.board:
                self.start(False)
            else:
                self.start(True)

    def start(self, new):
        """Create new collection session and proceed to collection window"""
        if new:
            params = BrainFlowInputParams()
            params.serial_port = self.fserialport.text()
            bid = self.boardmap[self.fmodel.currentText()][0]
            try:
                self.board = BoardShim(bid, params)
            except BrainFlowError as E:
                self.errlabel.setText(f"Error creating BoardShim object.\n{E}")
                return

        if self.boardless:
            session = BoardlessBridge.CollectionSession(self.board, self.sespath, int(self.fbuffsize.text()))
        else:
            session = BoardBridge.CollectionSession(self.board, self.sespath, int(self.fbuffsize.text()))

        ipath = os.path.join(self.sespath, "info.json")
        if self.stimscript:
            self.stimscript.add_info(ipath)
        self.colwin.init_session(ipath, session, new, stim=self.stimscript)
        self.goto("collect")

    def check_info(self):
        """Validate info"""
        if not self.curdir.text().strip():
            return False, "No session directory supplied."
        if "data.csv" in os.listdir(self.curdir.text().strip()):
            return False, "Data file already in target directory."
        if "info.json" in os.listdir(self.curdir.text().strip()):
            return False, "Info JSON already in target directory."
        if not self.fsname.text().strip():
            return False, "No subject name supplied."
        if not self.fpname.text().strip():
            return False, "No project name supplied."
        bl = self.fblength.text().strip()
        if not bl:
            return False, "No block length supplied."
        bl = int(bl)
        if bl < 1:
            return False, "Block length must be positive."
        if bl > self.blengthmax:
            return False, f"Block length too high. (Max: {self.blengthmax})"
        bc = self.fbcount.text().strip()
        if not bc:
            return False, "No block count supplied."
        bc = int(bc)
        if bc < 1:
            return False, "Block count must be positive."
        elif bc > self.bcountmax:
            return False, f"Block count too high. (Max: {self.bcountmax})"

        if not self.fstimcycle.text().strip():
            return False, "No stimulus cycle supplied."
        stimcycle = self.fstimcycle.text().strip()
        test = stimcycle.replace("1", "").replace("0", "")
        if len(test):
            return False, "Invalid characters in stim cycle."
        if len(stimcycle) != bc:
            return False, "Stim cycle does not match block count."
        if not self.fdescription.toPlainText().strip(" "):
            return False, "No session description supplied."
        if not self.fbuffsize.text().strip():
            return False, "No buffer size supplied."
        if int(self.fbuffsize.text()) > self.buffsize_max:
            return False, f"Buffer size too high. (Max: {self.buffsize_max})"
        if int(self.fbuffsize.text()) < self.buffsize_min:
            return False, f"Buffer size too low. (Min: {self.buffsize_min})"
        if not self.fserialport.text().strip():
            return False, "No serial port supplied."
        
        menu = self.hardlayout.itemAtPosition(6, 0)
        if menu and not (res := menu.validate(self))[0]:
            return res
        elif not menu:
            self.stimscript = None
        else:
            self.stimscript = InfoWindow.stimmap[menu.stimname](*menu.get_args())

        return True, ""

    def save_info(self):
        """"Save info as info.json"""
        info = self.infodict
        info['SessionParams']['SubjectName'] = self.fsname.text().strip()
        info['SessionParams']['ProjectName'] = self.fpname.text().strip()
        info['SessionParams']['ResponseType'] = self.frtype.currentText()
        info['SessionParams']['StimulusType'] = self.fstype.currentText()
        blength, bcount = self.fblength.text(), self.fbcount.text()
        info['SessionParams']['BlockLength'] = blength
        info['SessionParams']['BlockCount'] = bcount
        info['SessionParams']['StimCycle'] = self.fstimcycle.text().strip()
        info['HardwareParams']['HeadsetConfiguration'] = self.fconfig.currentText()
        model = self.fmodel.currentText()
        info['HardwareParams']['HeadsetModel'] = model
        info['HardwareParams']['SampleRate'] = str(self.boardmap[model][1])
        info['HardwareParams']['BufferSize'] = str(self.fbuffsize.text())
        info['Description'] = self.fdescription.toPlainText().strip()

        bcount = int(bcount)
        blength = int(blength)
        info['Annotations'] += [(float(blength*k), f"Block{k}") for k in range(1, bcount+1)]

        suffix = self.date + "_" + str(datetime.now().timestamp()).split(".")[1]
        self.sespath = os.path.join(self.curdir.text(), f"session_{suffix}")
        os.makedirs(self.sespath, exist_ok=True, mode=0o777)
        with open(os.path.join(self.sespath, "info.json"), 'w') as f:
            json.dump(info, f, ensure_ascii=False, indent=4)

    def get_directory(self):
        dir = QFileDialog.getExistingDirectory(self, "Choose a directory")
        self.curdir.setText(dir)

    @pyqtSlot(str)
    def stim_config(self, new):
        if menu := self.hardlayout.itemAtPosition(6, 0):
            menu.clear()
        if new == "Grid Flash":
            self.hardlayout.addLayout(GridStimMenu(), 6, 0, 1, 2)
        elif new == "Random Prompting":
            self.hardlayout.addLayout(RandomPromptMenu(), 6, 0, 1, 2)


class CollectionWindow(PageWindow):
    """Displays session controls and real time information (timers, logs, active state)"""
    def __init__(self):
        super().__init__()
        self.setObjectName("FullFrame")

    def init_session(self, infopath, csession, new=True, stim=None):
        """Set up for collection session
        
        Parameters
        ----------
        infopath: str
            path to info.json including filename
        csession: CollectionSession
            CollectionSession for the current session
        new: bool
            whether or not the window has previously been laid out
        stim: QWidget
            stim window for a built-in stimulus script
        """
        self.csession = csession
        flags = self.csession.get_flags()
        # Only set by collection thread to indicate board status
        self.ready_flag, self.ongoing, self.error_flag = flags[0]
        # Start set by GUI thread to start collection, but stop may be set by either collection or GUI thread
        self.start_event, self.stop_event = flags[1]

        self.infopath = infopath
        with open(infopath, 'r') as i:
            self.info = json.loads(i.read())

        self.bcount = int(self.info['SessionParams']['BlockCount'])
        self.blength = int(self.info['SessionParams']['BlockLength'])
        self.stimcycle = self.info['SessionParams']['StimCycle']
        self.stim = stim
        if self.stim:
            self.stim.exit_sig.connect(self.end_stim)

        self.session_status = "Preparing"
        self.current_block = 0
        self.start_time = None
        self.t = 0
        self.complete = False
        self.timer = QTimer(self)

        if new:
            self.build_frame()
            self.fill_frame()
        self.activate()

    def build_frame(self):
        """Create frames/widgets"""
        # Info Panel
        info_labels = QLabel("Session Info\nSubject:\nProject:\nResponse type:\nStimulus type:\n\n" +
                             "Sampling rate:\nConfiguration:\nModel:\n\nSession Structure\nBlock Count:\n" +
                             "Block Length:\nCycle:")
        info_labels.setObjectName('FieldLabels')
        info_text = QLabel()
        self.info_panel = InfoPanel(self.info, info_labels, info_text)

        # Status Panel
        status_label = QLabel("Active")
        status_info = QLabel()
        timer_label = QLabel("00:00")
        stimer_label = QLabel("00:00")
        infslabel = QLabel("Session status:")
        infslabel.setStyleSheet("font-weight: bold")
        block_status = QLabel()
        self.state_indicator = StateIndicator("#04d481", "black")
        self.status_panel = StatusPanel(status_label, status_info, block_status, 
                                        timer_label, stimer_label, 
                                        self.state_indicator, infslabel)

        # Buttons and top level widgets
        self.entry_button = QPushButton("Mark Event")
        self.entry_button.clicked.connect(self.on_enter_annotation)
        self.entry_button.setDisabled(True)
        self.entry_annotation = QLineEdit(self)
        self.entry_annotation.setPlaceholderText("t0")
        self.entry_annotation.returnPressed.connect(self.on_enter_annotation)
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_session)
        self.start_button.setDisabled(True)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.pause_stream)
        self.stop_button.setDisabled(True)

        # Log Box
        log_label = QLabel("Session Logs")
        log_label.setObjectName("FieldLabels")
        self.log_panel = LogPanel(self.infopath, log_label, self.csession)

    def fill_frame(self):
        """Inserts widgets in layouts"""
        layout = QVBoxLayout()
        gridlayout = QGridLayout()
        gridlayout.setColumnStretch(0, 1)
        gridlayout.setColumnStretch(1, 2)
        gridlayout.setRowStretch(2, 1)
        
        gridlayout.addWidget(self.info_panel, 0, 0, 2, 1)
        gridlayout.addWidget(self.status_panel, 0, 1)
        gridlayout.addWidget(self.log_panel, 2, 0, 1, 2)

        buttonlayout = QGridLayout()
        buttonlayout.addWidget(self.entry_annotation, 0, 0, 1, 3)
        buttonlayout.addWidget(self.entry_button, 0, 3)
        buttonlayout.addWidget(self.start_button, 1, 0, 1, 2)
        buttonlayout.addWidget(self.stop_button, 1, 2, 1, 2)
        gridlayout.addLayout(buttonlayout, 1, 1)

        layout.addLayout(gridlayout)
        self.setLayout(layout)

    def activate(self):
        """Set starting fields and begin session"""
        self.info_panel.set_info(self.info)
        self.set_start_mode('Start', True)
        self.log_panel.reset(self.infopath, self.csession)
        self.status_panel.set_block_time("00:00")
        self.status_panel.set_session_time("00:00")
        self.update_status()
        ready_thread = Thread(target=self.wait_for_ready, name="ReadyThread")
        ready_thread.start()
        self.csession.start()

    def wait_for_ready(self):
        """Show preparation status"""
        i = 0
        while not (ready := self.ready_flag.is_set()) and not self.error_flag.is_set() and not self.stop_event.is_set():
            infostat = "Preparing" + "." * i
            self.status_panel.set_session_status(infostat)
            i = (i+1) % 4
            sleep(0.5)
        if ready:
            self.status_panel.set_session_status("Ready")
            self.start_button.setDisabled(False)
        elif self.error_flag.is_set():
            infostat = self.csession.get_error()
            self.status_panel.set_session_status(infostat, error=True)

    def show_ongoing(self):
        """Show collecting status"""
        i = 0
        while not self.stop_event.is_set() and not self.error_flag.is_set():
            infostat = "Collecting" + "." * i
            self.status_panel.set_session_status(infostat)
            i = (i+1) % 4
            sleep(0.5)

    def add_annotation(self, time, note):
        self.info['Annotations'].append([time, note])
        with open(self.infopath, 'w') as file:
            json.dump(self.info, file, ensure_ascii=False, indent=4)
        self.csession.log_message(LogLevels.LEVEL_INFO, f"[GUI]: Annotation saved - '{note}'")

    def on_enter_annotation(self):
        if not self.start_time:
            return
        annotation = self.entry_annotation.text()
        timestamp = round((datetime.now() - self.start_time).total_seconds(), 2)

        if not annotation:
            annotation = f"t{self.t}"

        self.add_annotation(timestamp, annotation)
        self.entry_annotation.clear()
        self.entry_annotation.setPlaceholderText(self.tlabel())

    def update_status(self):
        if 1 <= self.current_block < len(self.stimcycle):  # Session in progress and not last block
            next_active = self.stimcycle[self.current_block] == '1'
            next = "Active" if next_active else "Inactive"
            self.status_panel.set_block_info(f"Block: {self.current_block}/{self.bcount}\nNext: {next}")
        elif self.current_block == self.bcount:  # Session in progress on last block
            self.status_panel.set_block_info(f"Block: {self.current_block}/{self.bcount}\nNext: None")
        elif self.current_block == 0:  # Initial state before starting session
            next_active = self.stimcycle[self.current_block] == '1'
            next = "Active" if next_active else "Inactive"
            self.status_panel.set_block_info(f"Block: {self.current_block}/{self.bcount}\nNext: {next}")
            return
        else:  # Negative current block or current block > bcount. Should never happen.
            return

        if self.stimcycle[self.current_block-1] == '1' and not self.state_indicator.is_active():
            self.state_indicator.set_active(True)
        elif self.stimcycle[self.current_block-1] == '0' and self.state_indicator.is_active():
            self.state_indicator.set_active(False)

    def update_timer(self):
        if self.error_flag.is_set():
            self.status_panel.set_session_status(self.csession.get_error(), error=True)
            self.stop_session()
            return

        elapsed_time = datetime.now() - self.start_time
        elapsed_seconds = int(elapsed_time.total_seconds())
        remaining_seconds = max(0, self.blength - (elapsed_seconds % self.blength))
        formatted_time = QTime(0, 0).addSecs(remaining_seconds).toString("mm:ss")
        self.status_panel.set_block_time(formatted_time)
        self.status_panel.set_session_time(QTime(0, 0).addSecs(elapsed_seconds).toString("mm:ss"))

        self.update_status()
        self.update_block(elapsed_time)

    def update_block(self, elapsed):
        self.current_block = int(elapsed.total_seconds() / self.blength) + 1
        if self.current_block > self.bcount:
            self.session_status = "Complete"
            self.current_block = self.bcount
            self.status_panel.set_block_time("00:00")
            self.pause_stream()  # Change to pause_stream

    def start_session(self):
        if not self.ready_flag.is_set():
            return
        ongoing_thread = Thread(target=self.show_ongoing, name="OngoingThread")
        ongoing_thread.start()
        self.start_event.set()
        self.current_block = 1
        self.start_time = datetime.now()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(10)  # Timer interval in milliseconds
        self.entry_button.setDisabled(False)
        self.start_button.setDisabled(True)
        self.stop_button.setDisabled(False)
        if self.stim:
            self.stim.show()
            self.csession.log_message(LogLevels.LEVEL_INFO, f"[GUI]: {type(self.stim).__name__} launched.")

    def new_session(self):
        self.goto("info", True)

    def set_start_mode(self, mode, disabled=False):
        if mode == 'Start':
            self.start_button.disconnect()
            self.start_button.pressed.connect(self.start_session)
            self.start_button.setDisabled(disabled)
            self.start_button.setText('Start')
        elif mode == 'New Session':
            self.start_button.disconnect()
            self.start_button.pressed.connect(self.new_session)
            self.start_button.setDisabled(disabled)
            self.start_button.setText("New Session")

    def pause_stream(self):
        self.stop_event.set()
        self.log_panel.end_log()
        self.timer.stop()
        self.state_indicator.set_active(False)
        self.stop_button.setDisabled(True)
        self.entry_button.setDisabled(True)
        if not self.error_flag.is_set():
            self.set_start_mode('New Session')
            self.status_panel.set_session_status("Complete", error=False)
        else:
            self.status_panel.set_session_status(self.csession.get_error(), error=True)
        if self.stim:
            self.stim.close()

    def end_stim(self):
        self.stim.close()
        self.csession.log_message(LogLevels.LEVEL_INFO, f"[GUI]: {type(self.stim).__name__} closed.")
        self.pause_stream()

    def stop_session(self):
        self.stop_event.set()
        self.log_panel.end_log()
        self.timer.stop()
        self.state_indicator.set_active(False)
        self.stop_button.setDisabled(True)
        self.entry_button.setDisabled(True)
        if self.error_flag.is_set():
            self.status_panel.set_session_status(self.csession.get_error(), error=True)
        else:
            self.status_panel.set_session_status("Complete", error=False)
        if self.stim:
            self.stim.close()

    def tlabel(self):
        self.t += 1
        return f"t{self.t}"


class InfoPanel(QFrame):
    def __init__(self, info, info_labels, info_text):
        super().__init__()
        self.setFrameStyle(QFrame.Panel | QFrame.Plain)

        self.info = info
        self.info_text = info_text

        layout = QHBoxLayout(self)
        leftlayout = QVBoxLayout()
        rightlayout = QVBoxLayout()
        leftlayout.addWidget(info_labels, alignment=Qt.AlignTop | Qt.AlignLeft)
        rightlayout.addWidget(info_text, alignment=Qt.AlignTop | Qt.AlignLeft)
        layout.addLayout(leftlayout)
        layout.addLayout(rightlayout)

    def set_info(self, info=None):
        if info:
            self.info = info
        sub = self.info['SessionParams'].get('SubjectName', '--') + '\n'
        proj = self.info['SessionParams'].get('ProjectName', '--') + '\n'
        resp = self.info['SessionParams'].get('ResponseType', '--') + '\n'
        stype = self.info['SessionParams'].get('StimulusType', '--') + '\n\n'
        srate = self.info['HardwareParams'].get('SampleRate', '--') + '\n'
        config = self.info['HardwareParams'].get('HeadsetConfiguration', '--') + '\n'
        model = self.info['HardwareParams'].get('HeadsetModel', '--') + '\n'

        bcount = self.info['SessionParams']['BlockCount']
        blength = self.info['SessionParams']['BlockLength']
        stimcycle = self.info['SessionParams']['StimCycle']

        cdetails = '\n'.join(['\n' + bcount, blength + 's', stimcycle])
        itext = '\n' + sub + proj + resp + stype + srate + config + model + '\n' + cdetails

        self.info_text.setText(itext)


class StatusPanel(QFrame):
    def __init__(self, status_label, status_info, block_status, 
                 block_timer, session_timer, state_indicator, infslabel):
        super().__init__()
        self.setFrameStyle(QFrame.Panel | QFrame.Plain)
        self.status_info = status_info
        self.btimer = block_timer
        self.stimer = session_timer
        self.state_indicator = state_indicator
        self.block_status = block_status

        layout = QGridLayout(self)
        layout.setRowStretch(2, 1)
        layout.setColumnStretch(2, 1)
        layout.addWidget(state_indicator, 0, 0)
        layout.addWidget(status_label, 0, 1)
        layout.addWidget(block_status, 1, 0, 2, 2, Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(block_timer, 1, 2, Qt.AlignTop | Qt.AlignRight)
        layout.addWidget(session_timer, 0, 2, Qt.AlignTop | Qt.AlignRight)
        layout.addWidget(infslabel, 2, 0, 1, 2, Qt.AlignBottom | Qt.AlignLeft)
        layout.addWidget(status_info, 2, 2, 1, 2, Qt.AlignBottom | Qt.AlignLeft)
    
    def set_session_status(self, status, error=False):
        """Set label next to Session Status"""
        if error:
            self.status_info.setStyleSheet("color: #c20808")
        else:
            self.status_info.setStyleSheet("color: #c5cfde")
        self.status_info.setText(status[:25])
    
    def set_block_info(self, status):
        """Set block number and next block state"""
        self.block_status.setText(status)
    
    def set_block_time(self, time_string):
        self.btimer.setText(time_string)
    
    def set_session_time(self, time_string):
        self.stimer.setText(time_string)

    def set_active(self, active):
        self.state_indicator.set_active(active)


def init_logbox(ipath, session):
    """Pass logfile to BoardShim and set up for GUI log window"""
    lfile = os.path.join(os.path.normpath(ipath + os.sep + os.pardir), "sessionlog.log")
    session.activate_logger(lfile)
    return QTextEditLogger(lfile)


class LogPanel(QFrame):
    def __init__(self, ipath, log_label, session):
        super().__init__()
        self.setFrameStyle(QFrame.Panel | QFrame.Plain)
        self.log_label = log_label
        self.logbox = init_logbox(ipath, session)

        layout = QVBoxLayout(self)
        layout.addWidget(log_label, Qt.AlignTop | Qt.AlignLeft)
        self.logbox.mount(layout)
        layout.setStretchFactor(log_label, 1)
        layout.setStretchFactor(self.logbox, 10)

    def reset(self, ipath, session):
        self.logbox.clear()
        newfile = os.path.join(os.path.normpath(ipath + os.sep + os.pardir), "sessionlog.log")
        session.activate_logger(newfile)
        self.logbox.reset_file(newfile)

    def end_log(self):
        self.logbox.end()
