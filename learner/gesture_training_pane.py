from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QSizePolicy, QComboBox, QGroupBox, QScrollArea, QListWidget, QListWidgetItem

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from myo_armband.myo_trainer import *

import pickle
import os
import time

class GestureTrackerDialog(QDialog):

    def __init__(self):
        '''
        Shows a graph for training gesture recognition
        '''
        super(GestureTrackerDialog, self).__init__()
        self.name = None
        self.design = None
        self.ip = None

        self.window_width = 1000
        self.window_height = 800
        self.setFixedSize(self.window_width, self.window_height)
        self.setWindowTitle("Train Gestures")
        self.setStyleSheet('QDialog {background-color: white;}')

        # setup the figure canvas
        self.graph = PlotWindow(parent=self, width=8, height=7.5)
        self.graph.move(180,0)

        # record groupbox
        self.gb_record = QGroupBox("controls", parent=self)
        self.gb_record.setGeometry(10,10,170,120)

        # record button
        self.record = QPushButton("record", self.gb_record)
        #self.okay.clicked.connect(self.on_okay)
        button_width = 160
        button_height = 35
        self.record.setGeometry(6, 25, button_width, button_height)
        self.record.setStyleSheet('QPushButton {color: black;}')
        self.record.clicked.connect(self.begin_countdown)
        self.countdown_label = QLabel("",parent=self)
        self.countdown_label.setGeometry(350,150,400,400)
        self.countdown_label.setStyleSheet('QLabel {color: rgba(250,0,0,50%); font: 500pt Arial}')
        self.countdown_label.hide()
        self.countdown = Countdown()
        self.countdown.update_countdown.connect(self.update_countdown)
        self.countdown.fully_counted_down.connect(self.begin_recording)
        self.trainer = Trainer()
        self.trainer.connect_armband()
        self.trainer.some_data_passer.connect(self.some_gesture_data_receiver)
        self.trainer.all_data_passer.connect(self.all_gesture_data_receiver)
        self.data_buffer = None

        # save button
        self.save = QPushButton("save", self.gb_record)
        #self.okay.clicked.connect(self.on_okay)
        button_width = 160
        button_height = 35
        self.save.setGeometry(6, 55, button_width, button_height)
        self.save.setStyleSheet('QPushButton {color: black;}')
        self.save.clicked.connect(self.save_buffer)

        # dropdown menu of available gestures to calibrate
        #self.gestures = self.get_possible_designs()
        self.gesture_box = QComboBox(self.gb_record)
        self.gesture_box.setGeometry(9,85,155,30)

        # history groupbox
        self.gb_record = QGroupBox("trainable estures", parent=self)
        self.gb_record.setGeometry(10,140,170,200)

        # history scrollpane
        self.gesture_history = QScrollArea(parent=self.gb_record)
        self.gesture_history.setGeometry(8,25,155,165)
        self.gesture_list = GestureList(self.gesture_history, self)
        self.gesture_list.setGeometry(0, 0, self.gesture_history.width(), self.gesture_history.height())
        self.gesture_list.itemClicked.connect(self.item_clicked)

        # populate the history scrollpane
        self.gesture_data = []
        if os.path.isfile("myo_armband/data_train.pkl"):
            with open("myo_armband/data_train.pkl", "rb") as infile:
                self.gesture_data = pickle.load(infile)
        self.item_ordering = []
        for item in self.gesture_data:
            self.item_ordering.append(item[7])
            list_item = QListWidgetItem(item[7])
            list_item.setData(Qt.UserRole, item)
            self.gesture_list.addItem(list_item)

        # populate the gesture_box combobox
        for item in self.gesture_data:
            self.gesture_box.addItem(item[7])

        # okay and cancel buttons
        self.okay = QPushButton("Okay", self)
        self.okay.clicked.connect(self.on_okay)
        button_width = 100
        button_height = 35
        self.okay.setGeometry((self.width()/2 - button_width/2)-50, self.height() - button_height, button_width, button_height)
        self.okay.setStyleSheet('QPushButton {color: black;}')

        self.cancel = QPushButton("Cancel", self)
        self.cancel.clicked.connect(self.on_cancel)
        button_width = 100
        button_height = 35
        self.cancel.setGeometry((self.width()/2 - button_width/2)+50, self.height() - button_height, button_width, button_height)
        self.cancel.setStyleSheet('QPushButton {color: black;}')

    def begin_countdown(self):
        self.countdown.start()

    def begin_recording(self):
        self.data_buffer = [[],[],[],[],[],[],[],"none"]
        self.trainer.start()

    def some_gesture_data_receiver(self, data, xlim):
        self.data_buffer[0].extend(data[0])
        self.data_buffer[1].extend(data[1])
        self.data_buffer[2].extend(data[2])
        self.data_buffer[3].extend(data[3])
        self.data_buffer[4].extend(data[4])
        self.data_buffer[5].extend(data[5])
        self.data_buffer[6].extend(data[6])
        self.graph.plot_gesture_data(self.data_buffer,xlim)

    def all_gesture_data_receiver(self, data):
        self.data_buffer = data
        self.data_buffer.append(str(self.gesture_box.currentText()))
        self.graph.plot_gesture_data(data)
        self.data_buffer = data

    def update_countdown(self):
        if self.countdown_label.text() == "":
            self.countdown_label.setText("3")
            self.countdown_label.show()
        elif self.countdown_label.text() == "3":
            self.countdown_label.setText("2")
        elif self.countdown_label.text() == "2":
            self.countdown_label.setText("1")
        else:
            self.countdown_label.setText("")
            self.countdown_label.hide()

    def update_gesture_train_data(self):
        print("updating")
        with open("data_train.pkl", "wb") as outfile:
            pickle.dump(self.gesture_data, outfile)

    def item_clicked(self):
        data = self.gesture_list.selectedItems()[0].data(Qt.UserRole)
        self.graph.plot_gesture_data(data)

    def save_buffer(self):
        new_data = []
        if self.data_buffer is not None:
            for data in self.gesture_data:
                if self.data_buffer[7] == data[7]:
                    new_data.append(self.data_buffer)
                else:
                    new_data.append(data)

        self.gesture_data = new_data
        self.data_buffer = None

        self.gesture_list.clear()
        for ordered_item_name in self.item_ordering:
            for item in self.gesture_data:
                if ordered_item_name == item[7]:
                    list_item = QListWidgetItem(item[7])
                    list_item.setData(Qt.UserRole, item)
                    self.gesture_list.addItem(list_item)

    def on_okay(self):
        self.update_gesture_train_data()
        self.close()

    def on_cancel(self):
        self.close()

class Countdown(QThread):

    update_countdown = pyqtSignal()
    fully_counted_down = pyqtSignal()

    def run(self):
        for i in range(3):
            self.update_countdown.emit()
            time.sleep(1)
        self.update_countdown.emit()
        self.fully_counted_down.emit()

class PlotWindow(FigureCanvas):

    def __init__(self, parent=None, width=8, height=6, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.subplots(6,1)
        fig.tight_layout()

        FigureCanvas.__init__(self, fig)
        self.fig=fig
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot_gesture_data([[1,1],[1,1],[1,1],[1,1],[1,1],[1,1],[0,1],"none"])

    def plot_gesture_data(self, data, xlim=None):
        times = data[6]
        norm_times = []
        for time in times:
            norm_times.append(time-times[0])

        self.axes[0].clear()
        self.axes[0].plot(norm_times,data[0])
        self.axes[0].set_ylabel("x accel")
        if xlim is not None:
            self.axes[0].set_xlim([0,xlim])

        self.axes[1].clear()
        self.axes[1].plot(norm_times,data[1])
        self.axes[1].set_ylabel("y accel")
        if xlim is not None:
            self.axes[1].set_xlim([0,xlim])

        self.axes[2].clear()
        self.axes[2].plot(norm_times,data[2])
        self.axes[2].set_ylabel("z accel")
        if xlim is not None:
            self.axes[2].set_xlim([0,xlim])

        self.axes[3].clear()
        self.axes[3].plot(norm_times,data[3])
        self.axes[3].set_ylabel("x rotate")
        if xlim is not None:
            self.axes[3].set_xlim([0,xlim])

        self.axes[4].clear()
        self.axes[4].plot(norm_times,data[4])
        self.axes[4].set_ylabel("y rotate")
        if xlim is not None:
            self.axes[4].set_xlim([0,xlim])

        self.axes[5].clear()
        self.axes[5].plot(norm_times,data[5])
        self.axes[5].set_ylabel("z rotate")
        if xlim is not None:
            self.axes[5].set_xlim([0,xlim])

        self.fig.tight_layout()
        self.draw()
        self.flush_events()

class GestureList(QListWidget):

    def __init__(self, parent, pane):
        super().__init__(parent=parent)
        self.pane = pane

    def keyPressEvent(self, event):
        if event.key() == 16777219: # previously Qt.Key_Delete
            self._del_item()

    def _del_item(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))
            item.data(Qt.UserRole).markForDeletion()
        self.pane.update_model()
