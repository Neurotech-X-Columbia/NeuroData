"""Built-in Stimuli Classes"""
import random
import time

from PyQt5.QtWidgets import (QWidget, QGridLayout, QVBoxLayout, QOpenGLWidget)
from PyQt5.QtCore import QThread, Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QBrush, QFont, QSurfaceFormat


class FlashingThread(QThread):
    flash_signal = pyqtSignal()

    def __init__(self, frequency):
        super().__init__()
        self.frequency = frequency
        self.is_running = True

    def run(self):
        interval = 1 / (2 * self.frequency)
        while self.is_running:
            self.flash_signal.emit()
            self.msleep(int(1000 * interval))

    def stop(self):
        self.is_running = False


class FlashingBox(QOpenGLWidget):
    def __init__(self, frequency):
        super().__init__()
        self.frequency = frequency
        self.flash_state = False
        self.flashing_thread = FlashingThread(frequency)
        self.flashing_thread.flash_signal.connect(self.toggle_flash)
        self.flashing_thread.start()

    def toggle_flash(self):
        self.flash_state = not self.flash_state
        self.update()

    def paintGL(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(Qt.black) if self.flash_state else QColor(Qt.white)
        painter.setBrush(QBrush(color))

        painter.drawRect(self.rect())
        painter.setPen(QColor(Qt.black) if not self.flash_state else QColor(Qt.white))
        painter.setFont(QFont('Arial', 16))
        painter.drawText(self.rect(), Qt.AlignCenter, f'{self.frequency:.1f} Hz')

    def closeEvent(self, event):
        self.flashing_thread.stop()
        self.flashing_thread.wait()


class GridFlash(QWidget):
    """
    Flashes frequencies on a grid
    
    Parameters
    ----------
    frequencies: int
        frequencies to include
    rows: int
        number of rows in grid
    cols: int
        number of columns in grid
    """
    exit_sig = pyqtSignal()
    def __init__(self, frequencies: list, rows: int, cols: int):
        super().__init__()
        layout = QGridLayout()
        self.active = True
        self.setLayout(layout)
        self.setMinimumSize(650, 650)

        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(p)

        n = 0
        for i in range(rows):
            for j in range(cols):
                if n < len(frequencies):
                    box = FlashingBox(frequencies[n])
                    layout.addWidget(box, i, j)
                    n += 1

        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        fmt.setSwapInterval(1)
        fmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        fmt.setRenderableType(QSurfaceFormat.OpenGL)
        QSurfaceFormat.setDefaultFormat(fmt)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        
    def closeEvent(self, event):
        self.exit_sig.emit()


class ToggleThread(QThread):
    flash_signal = pyqtSignal()

    def __init__(self, times, dur, start_time):
        super().__init__()
        self.times = times
        self.dur = dur
        self.is_running = True
        self.start_time = start_time

    def run(self):
        while self.is_running:
            for t in self.times:
                while time.time() < self.start_time + t:
                    self.msleep(100)

                self.flash_signal.emit()
                self.msleep(int(1000 * self.dur))
                self.flash_signal.emit()

    def stop(self):
        self.is_running = False


class PromptBox(QOpenGLWidget):
    def __init__(self, text, times, dur, stime):
        super().__init__()
        self.text = text
        self.flash_state = False
        self.toggle_thread = ToggleThread(times, dur, stime)
        self.toggle_thread.flash_signal.connect(self.toggle_flash)
        self.toggle_thread.start()
        w, h = 250, 100
        x = self.width() // 2 - w // 2
        y = self.height() // 2
        self.coords = (x, y, w, h)

    def toggle_flash(self):
        self.flash_state = not self.flash_state
        self.update()

    def paintGL(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(29, 35, 36))

        path = QPainterPath()
        rect = QRectF(*self.coords)
        path.addRoundedRect(rect, 10, 10)
        color = QColor(0, 123, 255) if self.flash_state else QColor(29, 35, 36)
        painter.fillPath(path, color)
        painter.setPen(QColor(Qt.white) if self.flash_state else QColor(29, 35, 36))
        painter.drawText(rect, Qt.AlignCenter, self.text)

    def closeEvent(self, event):
        self.flashing_thread.stop()
        self.flashing_thread.wait()


class RandomPrompt(QWidget):
    """
    Randomly shows prompt with given text during active stimulus blocks
    
    Parameters
    ----------
    prompt: str
        Text to put in prompt
    ppb: int
        Number of prompts per block of active stimulus
    cooldown: int
        Minimum time between prompts in seconds   
    stimcycle: str
        Stimulus cycle for the session
    dur: float
        How long to leave the prompt on the screen
    blength: int
        The length of one block
    """
    exit_sig = pyqtSignal()
    def __init__(self, prompt: str, ppb: int, cooldown: int, stimcycle: str, blength: int, dur=1.5):
        super().__init__()
        self.active = False
        self.prompt = prompt
        self.ppb = ppb
        self.cd = cooldown 
        self.stimcycle = stimcycle 
        self.blength = blength
        self.dur = dur 

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumSize(650, 650)

        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(29, 35, 36))
        self.setPalette(p)

        fmt = QSurfaceFormat()
        fmt.setSamples(4)
        fmt.setSwapInterval(1)
        fmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        fmt.setRenderableType(QSurfaceFormat.OpenGL)
        QSurfaceFormat.setDefaultFormat(fmt)

    def gen_times(self):
        res = 0.1
        domain = range(0, int(self.blength/res))
        offsets = []
        times = []

        for num, char in enumerate(self.stimcycle):
            if char == '1':
                offsets.append(num)

        for off in offsets:
            btimes = []
            blocked = set()
            pcount = 0
            while pcount < self.ppb:
                while (new := random.choice(domain)) in blocked:
                    pass

                bufmin, bufmax = max(0, new-self.cd/res), min(len(domain)/res, new+self.cd/res)
                consumed = range(int(bufmin), int(bufmax))
                for t in consumed:
                    blocked.add(t)
                
                if len(blocked) == len(domain):
                    pcount = 0
                    blocked = set()
                else:
                    btimes.append(new*res + off*self.blength)
                    pcount += 1

            times += btimes
        
        return sorted(times)
    
    def show(self):
        self.start()
        super().show()

    def start(self):
        self.active = True
        times = self.gen_times()
        box = PromptBox(self.prompt, times, self.dur, time.time())
        self.layout.addWidget(box)
    
    def closeEvent(self, event):
        self.exit_sig.emit()
