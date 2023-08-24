"""Classes that integrate Brainflow functionality into the GUI"""
from brainflow import LogLevels, BrainFlowError
from brainflow.board_shim import BoardShim
from DataSim import DataSim
from pandas import DataFrame
from PyQt5.QtCore import QFileSystemWatcher
from PyQt5.QtWidgets import QPlainTextEdit
from threading import Thread, Event
from time import sleep

import numpy as np  # Remove
import os
import random  # Remove

class ExceptableThread(Thread):
    def run(self):
        self.exc = None
        try:
            self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e


class CollectionSession(Thread):
    """
    Handles board setup and communication with GUI threads
    
    Parameters
    ----------
    boardshim: brainflow.board_shim.BoardShim
        BoardShim object used to run current session
    sespath: str
        Path to directory where data, info, and log files will be stored
    buffsize: Size of on-board data buffer in samples
    """
    class PrepInterruptedException(Exception):
        """Raised by user closing the window during board preparation."""

    def __init__(self, boardshim: BoardShim, sespath, buffsize):
        super().__init__(name="CollectionThread")
        self.board = boardshim
        self.buffsize = buffsize
        self.sespath = sespath
        self.fname = "data.csv"
        self.ready_flag, self.ongoing, self.error_flag = Event(), Event(), Event()
        self.start_event, self.stop_event = Event(), Event()
        self.error_message = ""
        self.lfpath = None

        rows = BoardShim.get_num_rows(self.board.board_id)
        self.data = np.zeros((rows, 1))
        self.sim = DataSim(rows)  # Remove

    def activate_logger(self, fpath):
        """Configure board logger to accept custom messages and log at INFO"""
        self.board.set_log_level(LogLevels.LEVEL_INFO)
        self.board.set_log_file(fpath)
        self.lfpath = fpath

    def log_message(self, level, message):
        """Log custom message"""
        self.board.log_message(level, message)

    def prepare(self):
        """Prepare board for collection. Sets error flag upon failure, ready flag on success."""
        if self.board.is_prepared():
            self.ready_flag.set()
            return
        self.log_message(LogLevels.LEVEL_INFO, "[GUI]: Preparing board...")
        try:
            # ExceptableThread allows calling thread to access exceptions encountered in child thread
            # proc = ExceptableThread(target=self.board.prepare_session, daemon=True, name="PrepThread")  # Uncomment
            proc = ExceptableThread(target=sleep, daemon=True, args=(5,), name="PrepThread")   # Remove
            proc.start()
            while proc.is_alive():  # Checks for interruption by threads other than PrepThread (probably a window close)
                if self.stop_event.is_set() or self.error_flag.is_set():
                    raise CollectionSession.PrepInterruptedException("Board preparation interrupted.")
            if self.board.is_prepared() or True:  # Remove second part
                self.ready_flag.set()
                self.log_message(LogLevels.LEVEL_INFO, "[GUI]: Board preparation successful.")
            else:
                raise proc.exc if proc.exc else Exception("Unknown error. Check logs.")
        except BrainFlowError as E:
            self.error_message = f"Error: {str(E)}"
            self.log_message(LogLevels.LEVEL_INFO, f"{str(E)}")
            self.error_flag.set()
        except CollectionSession.PrepInterruptedException as E:
            self.error_message = f"Error: {str(E)}"
            self.log_message(LogLevels.LEVEL_INFO, f"[GUI]: {str(E)}")
            self.error_flag.set()
        except Exception as E:
            self.error_message = f"Error: {str(E)}"
            self.error_flag.set()

    def start_stream(self):
        self.log_message(LogLevels.LEVEL_INFO, "[GUI]: Stream started.")
        if not self.ready_flag.is_set():
            return
        # self.board.start_stream()  # Uncomment
        self.sim.start_stream()  # Remove

    def update_data(self):
        try:
            if random.randint(1, 2) == 3:  # Remove block
                self.error_message = "RandomError: Encountered random error."
                self.log_message(LogLevels.LEVEL_INFO, self.error_message)
                self.error_flag.set()
            if not self.data.any():
                # self.data = self.board.get_board_data()  # Uncomment
                self.data = self.sim.get_data()  # Remove
            else:
                # self.data = np.hstack((self.data, self.board.get_board_data()))  # Uncomment
                self.data = np.hstack((self.data, self.sim.get_data()))  # Remove
            self.save_data()
        except BrainFlowError as E:
            self.error_message = f"Error: {E}"
            self.error_flag.set()
            self.end_session()
            return

    def save_data(self):
        DataFrame(np.copy(self.data)).to_csv(os.path.join(self.sespath, self.fname))
        self.log_message(LogLevels.LEVEL_INFO, "[GUI]: Update saved.")

    def run(self):
        self.prepare()

        while not self.start_event.is_set() and not self.error_flag.is_set():  # In ready state
            sleep(0.1)
        if self.error_flag.is_set():  # Probably window closed before starting stream
            # self.board.release_session()  # Uncomment
            return

        self.start_stream()
        self.ongoing.set()

        stopped = False
        while not (error := self.error_flag.is_set()) and not (stopped := self.stop_event.is_set()):
            sleep(5)
            self.update_data()

        if error:  # Error during collection (window close counted as error)
            self.end_session()
            return
        if stopped:  # Stopped by user or natural end of session
            self.pause_session()  # Change to pause_session

    def pause_session(self):
        # self.board.stop_stream()  # Uncomment
        self.sim.stop_stream()  # Remove
        self.ready_flag.clear()
        self.ongoing.clear()
        self.log_message(LogLevels.LEVEL_INFO, "[GUI]: Stream stopped.")

    def end_session(self):
        self.save_data()
        # self.board.stop_stream()  # Uncomment
        # self.board.release_session()  # Uncomment
        self.sim.stop_stream()  # Remove
        self.ready_flag.clear()
        self.ongoing.clear()
        self.log_message(LogLevels.LEVEL_INFO, "[GUI]: Session ended.")

    def get_error(self):
        return self.error_message

    def get_flags(self):
        return (self.ready_flag, self.ongoing, self.error_flag), (self.start_event, self.stop_event)
    

class QTextEditLogger(QPlainTextEdit):
    """Monitors logfile for updates and prints to GUI"""
    def __init__(self, filepath, parent_layout=None):
        super().__init__()
        self.logfile = open(filepath, buffering=1)
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
        self.logfile.seek(self.readpos)
        line = self.logfile.read()
        self.appendPlainText(line)
        self.readpos = self.logfile.tell()

    def __exit__(self, type, val, traceback):
        self.logfile.close()
        print(traceback)
