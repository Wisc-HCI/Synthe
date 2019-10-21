from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget, QLabel, QGroupBox, QPushButton
from PyQt5.QtGui import QIcon, QPixmap, QFont

class VisButtons():

	def __init__(self, parameters_group, gui):
		self.parameters_group = parameters_group
		self.gui = gui

		# add a label
		self.button_label = QLabel("Visualization", parent=self.parameters_group)
		self.button_label.setFont(QFont("Veranda", 10))
		self.button_label.move(10, 30)

		# set up the button to the clean representation
		self.model_button = QPushButton('Model', self.parameters_group)
		self.model_button.setGeometry(0, 40, self.parameters_group.width()/2, 70)
		icon = QIcon()
		icon.addPixmap(QPixmap("fig/dagre.png"))
		self.model_button.setIcon(icon)
		self.model_button.setIconSize(QSize(50,50))
		self.model_button.setCheckable(True)
		self.model_button.toggle()
		self.model_button.clicked.connect(self.model_button_checked)

		# set up the button to the tree representation
		self.traces_button = QPushButton('Traces', self.parameters_group)
		self.traces_button.setGeometry(self.parameters_group.width()/2, 40, self.parameters_group.width()/2, 70)
		icon = QIcon()
		icon.addPixmap(QPixmap("fig/traces.png"))
		self.traces_button.setIcon(icon)
		self.traces_button.setIconSize(QSize(50,50))
		self.traces_button.setCheckable(True)
		self.traces_button.clicked.connect(self.traces_button_checked)

	def model_button_checked(self):
		if self.model_button.isChecked():
			self.traces_button.setChecked(False)

		elif (not self.model_button.isChecked()) and (not self.traces_button.isChecked()):
			self.model_button.toggle()

		self.gui.update_representation("Clean")

	def traces_button_checked(self):
		if self.traces_button.isChecked():
			self.model_button.setChecked(False)

		elif (not self.model_button.isChecked()) and (not self.traces_button.isChecked()):
			self.traces_button.toggle()

		self.gui.update_representation("Tree")

	def get_selected(self):
		if self.traces_button.isChecked():
			return "Tree"
		elif self.model_button.isChecked():
			#self.model_button_checked()
			return "Clean"
		else:
			print("ERROR: no buttons are checked")
			exit(1)