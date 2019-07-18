from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QLineEdit

class Notification(QDialog):

	def __init__(self, message):
		super(Notification, self).__init__()

		self.resize(300, 175)
		self.setWindowTitle("Network Notification")

		self.message = message

		self.instruction_label = QLabel(self.message, self)
		self.instruction_label.move(10, 10)
		self.instruction_label.setWordWrap(True)

		self.okay = QPushButton("Okay", self)
		self.okay.clicked.connect(self.on_okay)
		button_width = 100
		button_height = 35
		self.okay.setGeometry(self.width()/2 - button_width/2, self.height() - button_height, button_width, button_height)
		self.okay.setStyleSheet('QPushButton {color: black;}')

	def on_okay(self):
		self.close()

class MicrophonesDisconnected(Notification):

	def __init__(self, message):
		super(MicrophonesDisconnected, self).__init__(message)

class RobotDisconnected(Notification):

	def __init__(self, message):
		super(RobotDisconnected, self).__init__(message)

class RobotErrorOccurred(Notification):

	def __init__(self, message):
		super(RobotErrorOccurred, self).__init__(message)

class BindFailed(Notification):

	def __init__(self, message):
		super(BindFailed, self).__init__(message)


