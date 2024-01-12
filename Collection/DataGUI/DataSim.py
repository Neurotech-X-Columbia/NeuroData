import numpy as np
from time import sleep
from threading import Thread


# Simulated data generator for GUI testing
class DataSim:
    def __init__(self, rows):
        self.buffer = np.zeros((rows, 1))
        self.rows = rows
        self.count = 1
        self.active = False
        self.logger = None

    def start_stream(self):
        self.active = True
        gen = Thread(target=self.generate_data)
        gen.start()

    def stop_stream(self):
        self.active = False

    def generate_data(self):
        while self.active:
            sleep(.25)
            new_col = np.ones((self.rows, 1)) * self.count
            if not self.buffer.any():
                self.buffer = new_col
            else:
                self.buffer = np.hstack((self.buffer, new_col))
            self.count += 1

    def get_data(self):
        copy = np.copy(self.buffer)
        self.buffer = np.zeros((5, 1))
        return copy
