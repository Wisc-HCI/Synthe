from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon, QPixmap
from exporter import *
from robot_controller import *

class SimulateButton(QPushButton):

	def __init__(self, button_text, parent, gui, robot_controller):
		super(SimulateButton, self).__init__(button_text, parent=parent)

		self.setGeometry(parent.width() - 15 - 100, gui.bodystorm_history.height() + 15, 100, 35)
		icon = QIcon()
		icon.addPixmap(QPixmap("fig/StartIcon.png"))
		self.setIcon(icon)
		self.robot_control = robot_controller

	def simulate(self, interaction, bodystorm):
		#print("about to call the exporter")
		Exporter().export_to_xml(interaction, bodystorm)
		self.robot_control.simulate()

	def export_design(self, interaction, bodystorm):
		Exporter().export_to_xml(interaction, bodystorm)

class RecordButton(QPushButton):

	def __init__(self, button_text, parent, gui):
		super(RecordButton, self).__init__(button_text, parent=parent)

		self.setGeometry(parent.width() - 15 - 200, gui.bodystorm_history.height() + 15, 100, 35)
		icon = QIcon()
		icon.addPixmap(QPixmap("fig/RecordIcon.png"))
		self.setIcon(icon)