from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QSizePolicy, QComboBox, QLineEdit, QGroupBox, QScrollArea, QListWidget, QListWidgetItem

import sounddevice as sd
import pyaudio
import time

class AudioInputDialog(QDialog):

    end_signal = pyqtSignal()

    def __init__(self, participants_to_devices):
        super(AudioInputDialog, self).__init__()
        self.window_width = 405
        self.window_height = 310
        self.setFixedSize(self.window_width, self.window_height)
        self.setWindowTitle("Audio Input Devices")
        self.setStyleSheet('QDialog {background-color: white;}')

        # create data structures for existing (selected) devices
        self.previously_selected_device_names = []
        self.devices_to_participant_names = {}
        for p,dev in participants_to_devices.items():
            self.previously_selected_device_names.append(p)
            self.devices_to_participant_names[dev["name"]] = p

        # set up thread
        self.audio_refresher = AudioRefresherThread(self.end_signal, self.update_devices)
        self.audio_refresher.start()

        # list of available input devices
        self.avail_device_label = QLabel("Select input devices to use", parent=self)
        self.avail_device_label.setStyleSheet('QLabel {font-weight: bold;}')
        self.avail_device_label.setGeometry(10,5,320,40)
        self.input_device_scroll = QScrollArea(parent=self)
        self.input_device_scroll.setGeometry(10,35,320,100)
        self.input_device_list = QListWidget(self.input_device_scroll)
        self.input_device_list.setGeometry(0, 0, self.input_device_scroll.width(), self.input_device_scroll.height())
        self.input_device_list.itemClicked.connect(self.select_unselected_item)
        self.unselected_device = None
        self.add_device_button = QPushButton("add", parent=self)
        self.add_device_button.setGeometry(330,31,75,35)
        self.add_device_button.setStyleSheet('QPushButton {color: black;}')
        self.add_device_button.clicked.connect(self.add_device)

        # list of chosen input devices
        self.selected_device_label = QLabel("Selected input devices", parent=self)
        self.selected_device_label.setStyleSheet('QLabel {font-weight: bold;}')
        self.selected_device_label.setGeometry(10,140,320,40)
        self.selected_device_scroll = QScrollArea(parent=self)
        self.selected_device_scroll.setGeometry(10,170,320,100)
        self.selected_device_list = QListWidget(self.selected_device_scroll)
        self.selected_device_list.setGeometry(0, 0, self.selected_device_scroll.width(), self.selected_device_scroll.height())
        self.selected_device_list.itemClicked.connect(self.select_selected_item)
        self.selected_device = None
        self.chosen_devices = {}
        self.edit_device_button = QPushButton("edit", parent=self)
        self.edit_device_button.setGeometry(330,166,75,35)
        self.edit_device_button.setStyleSheet('QPushButton {color: black;}')
        self.edit_device_button.clicked.connect(self.open_device_editor)
        self.remove_device_button = QPushButton("remove", parent=self)
        self.remove_device_button.setGeometry(330,200,75,35)
        self.remove_device_button.setStyleSheet('QPushButton {color: black;}')
        self.remove_device_button.clicked.connect(self.remove_device)

        # device nicknames
        self.nicknames = {}

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

        # look through previously selected devices, add to selected list if need be
        for devname,p in self.devices_to_participant_names.items():
            self.nicknames[devname] = p
            new_item = QListWidgetItem("{0:<0} {1:>30}".format(devname,p))
            item_data = participants_to_devices[p]
            new_item.setData(Qt.UserRole, item_data)
            self.selected_device_list.addItem(self.unselected_device)
            self.chosen_devices[dev["name"]] = dev

    def open_device_editor(self):
        if self.selected_device is not None:
            curr_nickname = self.nicknames[self.selected_device.data(Qt.UserRole)["name"]]
            ai_editor = AudioInputEditor(curr_nickname)
            ai_editor.exec_()
            nickname = ai_editor.curr_nickname
            self.nicknames[self.selected_device.data(Qt.UserRole)["name"]] = nickname
            self.update_devices()

    def update_devices(self):
        # get all existing items
        existing_items = {}
        for i in range(self.input_device_list.count()):
            existing_items[self.input_device_list.item(i).data(Qt.UserRole)["name"]] = self.input_device_list.item(i)
        selected_item = self.input_device_list.selectedItems()[0] if len(self.input_device_list.selectedItems()) > 0 else None

        device_list = sd.query_devices()
        self.input_device_list.clear()
        for device in device_list:
            # update nicknames
            if device["name"] not in self.nicknames:
                self.nicknames[device["name"]] = "participant"

            if device["max_input_channels"] > 0 and device["name"] not in self.chosen_devices:
                new_item = QListWidgetItem(device["name"])
                if device["name"] in existing_items:
                    new_item.setData(Qt.UserRole, device)
                    self.input_device_list.addItem(new_item)
                    if selected_item is not None and existing_items[device["name"]] == selected_item:
                        self.input_device_list.setCurrentItem(new_item)
                        self.unselected_device = new_item
                else:
                    new_item.setData(Qt.UserRole, device)
                    self.input_device_list.addItem(new_item)

        # get all existing items
        existing_items = {}
        for i in range(self.selected_device_list.count()):
            existing_items[self.selected_device_list.item(i).data(Qt.UserRole)["name"]] = self.selected_device_list.item(i)
        selected_item = self.selected_device_list.selectedItems()[0] if len(self.selected_device_list.selectedItems()) > 0 else None

        self.selected_device_list.clear()
        for device in device_list:
            if device["max_input_channels"] > 0 and device["name"] in self.chosen_devices:
                new_item = QListWidgetItem("{0:<0} {1:>30}".format(device["name"],self.nicknames[device["name"]]))
                if device["name"] in existing_items:
                    new_item.setData(Qt.UserRole, device)
                    self.selected_device_list.addItem(new_item)
                    if selected_item is not None and existing_items[device["name"]] == selected_item:
                        self.selected_device_list.setCurrentItem(new_item)
                        self.selected_device = new_item
                else:
                    new_item.setData(Qt.UserRole, device)
                    self.selected_device_list.addItem(new_item)

    def select_unselected_item(self):
        self.unselected_device = self.input_device_list.selectedItems()[0]

    def select_selected_item(self):
        self.selected_device = self.selected_device_list.selectedItems()[0]

    def add_device(self):
        if len(list(self.chosen_devices.keys())) > 1:
            return
        if self.unselected_device is not None:
            self.input_device_list.takeItem(self.input_device_list.row(self.unselected_device))
            dat = self.unselected_device.data(Qt.UserRole)
            self.unselected_device.setText("{0:<0} {1:>30}".format(dat["name"],self.nicknames[dat["name"]]))
            self.selected_device_list.addItem(self.unselected_device)
            self.chosen_devices[dat["name"]] = dat
            self.unselected_device = None

    def remove_device(self):
        if self.selected_device is not None:
            self.selected_device_list.takeItem(self.selected_device_list.row(self.selected_device))
            dat = self.selected_device.data(Qt.UserRole)
            self.selected_device.setText(dat["name"])
            self.input_device_list.addItem(self.selected_device)
            del self.chosen_devices[dat["name"]]
            self.selected_device = None

    def on_okay(self):
        # compile results
        self.end_signal.emit()
        self.devices_to_return = {}
        for dev_name in self.chosen_devices.keys():
            dev_nickname = self.nicknames[dev_name]
            self.devices_to_return[dev_nickname] = self.chosen_devices[dev_name]

        # add the device ids to the chosen devices
        p = pyaudio.PyAudio()
        device_count = p.get_host_api_info_by_index(0).get('deviceCount')
        for i in range(device_count):
            name = p.get_device_info_by_host_api_device_index(0, i).get('name')
            if name in self.chosen_devices.keys():
                nickname = self.nicknames[name]
                self.devices_to_return[nickname]['id'] = i

        self.close()

    def on_cancel(self):
        self.devices_to_return = None
        self.end_signal.emit()
        self.close()

class AudioRefresherThread(QThread):

    update_devices = pyqtSignal()

    def __init__(self, end_signal, update_device_callback):
        super(AudioRefresherThread, self).__init__()
        self.terminate = False
        self.end_signal = end_signal
        self.end_signal.connect(self.init_termination)
        self.update_devices.connect(update_device_callback)

    def run(self):
        sd._terminate()
        sd._initialize()
        self.update_devices.emit()

    def init_termination(self):
        self.terminate = True

class AudioInputEditor(QDialog):

    def __init__(self, curr_nickname):
        super(AudioInputEditor, self).__init__()
        self.window_width = 230
        self.window_height = 100
        self.setFixedSize(self.window_width, self.window_height)
        self.setWindowTitle("Edit Audio Input")
        self.setStyleSheet('QDialog {background-color: white;}')

        # ickname
        name_label = QLabel("Name: ",parent=self)
        name_label.setGeometry(10,20,80,15)
        self.nickname_box = QLineEdit(self)
        self.nickname_box.setText(curr_nickname)
        self.curr_nickname = curr_nickname
        self.nickname_box.setGeometry(60,18,160,20)

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

    def on_okay(self):
        self.curr_nickname = self.nickname_box.text()
        self.close()

    def on_cancel(self):
        self.close()
