from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QLineEdit

class NameDialog(QDialog):

	def __init__(self, parent):
		super(NameDialog, self).__init__(parent=parent)

		self.parent = parent

		self.resize(300, 175)
		self.setWindowTitle("Enter your names")

		label_x = 10
		label_y = 50
		move_y = 50

		self.instruction_label = QLabel("Enter your names below", self)
		self.instruction_label.move(label_x, 10)
		self.p1_label = QLabel("Participant 1: ", self)
		self.p1_label.move(label_x, label_y)
		self.p2_label = QLabel("Participant 2: ", self)
		self.p2_label.move(label_x, label_y + move_y)

		self.textarea_p1 = QLineEdit(self)
		self.textarea_p1.setGeometry(100, label_y, 150, 20)

		self.textarea_p2 = QLineEdit(self)
		self.textarea_p2.setGeometry(100, label_y + move_y, 150, 20)

		self.okay = QPushButton("Okay", self)
		self.okay.clicked.connect(self.on_okay)
		button_width = 100
		button_height = 35
		self.okay.setGeometry(self.width()/2 - button_width/2, self.height() - button_height, button_width, button_height)
		self.okay.setStyleSheet('QPushButton {color: black;}')

	def on_okay(self):
		self.parent.update_names(self.textarea_p1.text(), self.textarea_p2.text())
		self.close()


