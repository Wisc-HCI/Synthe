from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSlider
from PyQt5.QtGui import QFont
import time

class StateSizeChooser():

	def __init__(self, parameters_group, gui):
		self.parameters_group = parameters_group
		self.gui = gui

		vertical_offset = 0

		self.comboBoxLabel = QLabel("Maximum number of states", parent=self.parameters_group)
		self.comboBoxLabel.setFont(QFont("Veranda", 10))
		self.comboBoxLabel.move(10, vertical_offset + 30)
		self.sp = QSlider(Qt.Horizontal, parent=self.parameters_group)
		self.sp.setGeometry(40,vertical_offset + 45,300,25)
		self.sp.setMinimum(0)
		self.sp.setMaximum(10)
		self.sp.setTickInterval(1)
		self.sp.setValue(5)
		self.sp.setTickPosition(QSlider.TicksBelow)
		self.sp.sliderReleased.connect(self.slider_value_change)
		self.minimum_label = QLabel("0", parent=self.parameters_group)
		self.minimum_label.setGeometry(5+40,vertical_offset + 73, 10, 10)
		self.minimum_label.setFont(QFont("Veranda", 10))
		#self.mid_label_1 = QLabel("5", parent=self.parameters_group)
		#self.mid_label_1.setGeometry(5+110,vertical_offset + 73, 20, 10)
		#self.mid_label_1.setFont(QFont("Veranda", 10))
		self.mid_label_2 = QLabel("5", parent=self.parameters_group)
		self.mid_label_2.setGeometry(5+180,vertical_offset + 73, 20, 10)
		self.mid_label_2.setFont(QFont("Veranda", 10))
		#self.mid_label_3 = QLabel("15", parent=self.parameters_group)
		#self.mid_label_3.setGeometry(5+250,vertical_offset + 73, 20, 10)
		#self.mid_label_3.setFont(QFont("Veranda", 10))
		self.maximum_label = QLabel("10", parent=self.parameters_group)
		self.maximum_label.setGeometry(5+320, vertical_offset + 73, 20, 10)
		self.maximum_label.setFont(QFont("Veranda", 10))

	def slider_value_change(self):
		n = self.sp.value()
		print("SLIDER >> set value to {} at {}".format(n, time.time()))
		self.gui.update_model(n)

	def value(self):
		return self.sp.value()