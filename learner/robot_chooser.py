from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton

class ChooseRobotDialog(QDialog):

	def __init__(self, parent):
		super(ChooseRobotDialog, self).__init__(parent=parent)

		self.parent = parent
		self.rval = False

		self.window_width = 600
		self.window_height = 300
		self.resize(self.window_width, self.window_height)
		self.setWindowTitle("Who is bodystorming the robot?")
		self.instruction_label = QLabel("Who is the robot?", self)
		self.instruction_label.move(150, 10)
		self.instruction_label.setFont(QFont("Arial", 18, QFont.Bold))

		# buttons
		self.p1_button = QPushButton(self.parent.participant_names[0], self)
		self.p1_button.setStyleSheet('QPushButton {color: black; font-size: 32pt}')
		self.p1_button.setGeometry(10, 50, self.window_width/2 - 15, self.window_height - 110)
		self.p1_button.clicked.connect(self.on_p1)
		if len(self.parent.participant_names) > 1:
			self.p2_button = QPushButton(self.parent.participant_names[1], self)
			self.p2_button.setStyleSheet('QPushButton {color: black; font-size: 32pt}')
			self.p2_button.setGeometry(self.window_width/2 + 5, 50, self.window_width/2 - 15, self.window_height - 110)
			self.p2_button.clicked.connect(self.on_p2)

	def on_p1(self):
		self.parent.p1_is_robot = True
		self.rval = True
		self.close()

	def on_p2(self):
		self.parent.p1_is_robot = False
		self.rval = True
		self.close()
