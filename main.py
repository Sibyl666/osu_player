from PySide2.QtWidgets import QMainWindow, QApplication, QFormLayout, QPushButton, QWidget, QSlider, QLabel
from PySide2.QtCore import Slot, QThreadPool, QRunnable, Qt, Signal, QObject
import configparser
import os
import random
from pygame import mixer_music, mixer, USEREVENT
import pygame

mSignal = None
volume = 0
first_play = True


class Communicate(QObject):
    signal_str = Signal(str)


def get_signal():
    global mSignal
    if mSignal is None:
        mSignal = Communicate()
    return mSignal


class Main(QMainWindow):
    def __init__(self):
        global volume
        super(Main, self).__init__()
        mixer.init(44100, -16, 2, 2048)
        pygame.init()

        self.signals = get_signal()
        self.signals.signal_str.connect(self.change_map_title)

        ssf = open("style.stylesheet", "r").read()
        self.config = configparser.ConfigParser()
        self.config.read("settings.ini")

        self.path = self.config["settings"]["path"]
        self.volume = float(self.config["settings"]["volume"])
        volume = self.volume
        mixer_music.set_volume(self.volume)

        self.setWindowTitle("Osu Player")
        self.setStyleSheet(ssf)
        self.setMinimumWidth(500)

        playrandom = QPushButton("Play Random")
        pause = QPushButton("Pause")
        unpause = QPushButton("Unpause")
        restart = QPushButton("Restart")
        self.map_name = QLabel()
        self.map_name.setStyleSheet(ssf)

        self.slider = QSlider()
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.TickPosition(QSlider.NoTicks)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setStyleSheet(ssf)
        self.slider.setValue(self.volume * 100)

        template = QFormLayout()
        template.addRow(self.map_name)
        template.addRow(playrandom)
        template.addRow(pause, unpause)
        template.addRow(restart)
        template.addRow(self.slider)

        self.templatewidget = QWidget()
        self.templatewidget.setLayout(template)

        self.setCentralWidget(self.templatewidget)

        self.all_files = []
        self.path_and_file = []

        for root, dirs, files in os.walk(self.path):
            self.all_files.append((root, files))

        for dirs_files in self.all_files:
            for file in dirs_files[1]:
                if file.endswith(".mp3"):
                    self.path_and_file.append((dirs_files[0], file))

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

        playrandom.pressed.connect(self.play)
        pause.pressed.connect(self.pause)
        unpause.pressed.connect(self.unpause)
        restart.pressed.connect(self.restart)

        self.slider.valueChanged.connect(self.volume_value)

    def volume_value(self):
        global volume
        volume = self.slider.value()
        volume = float(volume / 100)
        self.config["settings"]["volume"] = str(volume)
        with open("settings.ini", "w") as file:
            self.config.write(file)
        mixer_music.set_volume(volume)

    def play(self):
        global first_play
        if first_play is False:
            mixer_music.stop()
        else:
            first_play = False
            self.worker = Worker(self.path_and_file)
            if self.threadpool.activeThreadCount() == 1:
                mixer.quit()

            self.threadpool.start(self.worker)

    @Slot(str)
    def change_map_title(self, words):
        print(words)
        self.map_name.setText(words)
        self.setWindowTitle(words)

    def pause(self):
        mixer_music.pause()

    def unpause(self):
        mixer_music.unpause()

    def restart(self):
        mixer_music.rewind()


class Worker(QRunnable):
    def __init__(self, path_and_file):
        global volume
        self.volume = volume
        super(Worker, self).__init__()
        self.path_and_file = path_and_file
        self.NEXT = USEREVENT + 1
        self.signals = get_signal()
        pygame.init()

    def run(self):
        mixer.init(44100, -16, 2, 2048)

        rand = random.choice(self.path_and_file)
        map_title = str(rand[0]).split("\\")[-1]

        mixer_music.load(f"{rand[0]}\{rand[1]}")
        mixer_music.play()
        mixer_music.set_endevent(self.NEXT)
        mixer_music.set_volume(self.volume)
        self.signals.signal_str.emit(map_title)
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == self.NEXT:
                        rand = random.choice(self.path_and_file)
                        map_title = str(rand[0]).split("\\")[-1]

                        self.signals.signal_str.emit(map_title)

                        mixer_music.load(f"{rand[0]}\{rand[1]}")

                        mixer_music.play()


if __name__ == '__main__':
    app = QApplication([])

    win = Main()
    win.show()

    app.exec_()
