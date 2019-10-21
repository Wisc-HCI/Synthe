import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QLineEdit, QComboBox

class NewDesignDialog(QDialog):

    def __init__(self):
        '''
        We need: (1) design name
                 (2) alphabet
                 (3) IP addr
        '''
        super(NewDesignDialog, self).__init__()
        self.name = None
        self.design = None
        self.ip = None

        self.window_width = 300
        self.window_height = 180
        self.setFixedSize(self.window_width, self.window_height)
        self.setWindowTitle("New Design")

        # name
        name_label = QLabel("Name: ",parent=self)
        name_label.setGeometry(50,20,80,15)
        self.name_box = QLineEdit(self)
        self.name_box.setGeometry(100,18,160,20)

        # design type
        self.designs = self.get_possible_designs()
        design_label = QLabel("Alphabet: ", parent=self)
        design_label.setGeometry(29,60,80,15)
        self.design_box = QComboBox(self)
        self.design_box.setGeometry(98,54,160,30)
        for design in self.designs:
            self.design_box.addItem(design)

        # ip
        ip_label = QLabel("Computer IP: ", parent=self)
        ip_label.setGeometry(10,100,80,15)
        self.ip_box = QLineEdit(self)
        self.ip_box.setGeometry(100,98,160,20)

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

    def get_possible_designs(self):
        '''
        Search for and return all available design files
        '''
        designs = {}

        # search in alphabets file
        for root, dirs, files in os.walk("alphabets"):
            for file in files:
                if "alphabet.py" in files:
                    design_name = root[root.index("/")+1:]
                    filename = file[:file.index(".")]
                    designs[design_name] = "{}/{}".format(root,filename).replace("/",".")

        return designs

    def on_okay(self):
        self.name = self.name_box.text()
        self.design = self.designs[str(self.design_box.currentText())]
        self.ip = self.ip_box.text()

        if self.name == "" or self.ip == "":
            return
        self.close()

    def on_cancel(self):
        self.close()
