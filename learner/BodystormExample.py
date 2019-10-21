from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtWidgets import QLabel, QDialog, QScrollArea, QGroupBox, QPushButton, QComboBox, QSpinBox, QTextEdit
from PyQt5.QtGui import QImage, QPalette, QBrush, QIcon, QPixmap, QPainter, QColor, QFont, QPainterPath, QPen, QPolygonF
from example_drawer import *
from copy import deepcopy
from functools import partial

class Example(QDialog):

	def __init__(self, bodystorm_history, demo, update_model_callback, Alphabet):
		super(Example, self).__init__()
		self.bodystorm_history = bodystorm_history
		self.Alphabet = Alphabet
		self.demo = deepcopy(demo)
		self.actual_demo = demo
		self.update_model_callback = update_model_callback

		self.resize(1400,380)
		self.scrollarea_groupbox = QGroupBox("Bodystorm recording", parent=self)
		self.scrollarea_groupbox.setGeometry(10, 10, self.width() - 220, self.height() - 50)

		self.parameterization_groupbox = QGroupBox("Parameters", parent=self)
		self.parameterization_groupbox.setGeometry(self.width() - 200, 10, 190, self.height() - 50)

		self.scroll_area = QScrollArea(self.scrollarea_groupbox)
		self.scroll_area.setGeometry(0, 18, self.scrollarea_groupbox.width(), self.scrollarea_groupbox.height()-18)
		self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.example_drawer = ExampleDrawer(self.scroll_area, self.demo, self)
		self.scroll_area.setWidget(self.example_drawer)

		self.set_okay_cancel_buttons()
		self.output_parameter_widgets = {"output": None, "output_label": None, "gesture": None, "gesture_label": None, "gaze": None, "gaze_label":None, "timing": None, "timing_label":None}
		self.input_parameter_widgets = {"input": None, "input_label":None, "timing": None, "timing_label":None}

	def set_okay_cancel_buttons(self):
		button_width = 100
		button_height = 35
		button_spacing = 20
		self.okay = QPushButton('Okay', self)
		self.okay.setGeometry(self.width()/2 - button_width - button_spacing/2, self.height() - button_height, button_width, button_height)
		self.okay.setStyleSheet('QPushButton {color: black;}')
		self.okay.clicked.connect(self.on_okay)

		self.cancel = QPushButton("Cancel", self)
		self.cancel.setGeometry(self.width()/2 + button_spacing/2, self.height() - button_height, button_width, button_height)
		self.cancel.clicked.connect(self.on_cancel)

	def setup_output_parameters(self, demo_output):
		self.remove_widget_parents(self.output_parameter_widgets)
		self.remove_widget_parents(self.input_parameter_widgets)
		self.parameterization_groupbox.update()

		output_val = demo_output.output
		gaze_val = demo_output.gaze
		gesture_val = demo_output.gesture
		speech_val = demo_output.speech

		input_speech_label = QLabel("Robot actor's speech", self.parameterization_groupbox)
		input_speech_label.move(10, 35)
		input_speech = QTextEdit(self.parameterization_groupbox)
		input_speech.setText(speech_val)
		input_speech.setGeometry(10, 50, self.parameterization_groupbox.width()-20, 80)
		input_speech.textChanged.connect(partial(self.on_output_text_edited,demo_output))

		output_label = QLabel("Speech classification", self.parameterization_groupbox)
		output_label.move(10, 155)
		output_chooser = QComboBox(parent=self.parameterization_groupbox)
		for output in self.Alphabet.get_outputs():
			output_chooser.addItem(output)
		output_chooser.setGeometry(10,170, self.parameterization_groupbox.width()-20, 30)
		output_chooser.setCurrentIndex(output_chooser.findText(output_val))
		output_chooser.currentTextChanged.connect(partial(self.on_output_select,demo_output))

		'''
		gaze_chooser_label = QLabel("Robot gaze", self.parameterization_groupbox)
		gaze_chooser_label.move(10, 105)
		gaze_chooser = QComboBox(parent=self.parameterization_groupbox)
		gaze_chooser.setGeometry(10,120, self.parameterization_groupbox.width()-20, 30)
		for gaze in Gaze.get_gazes():
			gaze_chooser.addItem(gaze)
		gaze_chooser.setCurrentIndex(gaze_chooser.findText(gaze_val))
		gaze_chooser.currentTextChanged.connect(partial(self.on_gaze_select,demo_output))
		'''

		gesture_chooser_label = QLabel("Robot gesture", self.parameterization_groupbox)
		gesture_chooser_label.move(10, 225)
		gesture_chooser = QComboBox(parent=self.parameterization_groupbox)
		gesture_chooser.setGeometry(10,240, self.parameterization_groupbox.width()-20, 30)
		for gesture in self.Alphabet.get_gestures():
			gesture_chooser.addItem(gesture)
		gesture_chooser.setCurrentIndex(gesture_chooser.findText(gesture_val))
		gesture_chooser.currentTextChanged.connect(partial(self.on_gesture_select,demo_output))

		self.output_parameter_widgets["speech"] = (input_speech,demo_output)
		self.output_parameter_widgets["speech_label"] = input_speech_label
		self.output_parameter_widgets["output"] = output_chooser
		self.output_parameter_widgets["output_label"] = output_label
		#self.output_parameter_widgets["gaze"] = gaze_chooser
		#self.output_parameter_widgets["gaze_label"] = gaze_chooser_label
		self.output_parameter_widgets["gesture"] = gesture_chooser
		self.output_parameter_widgets["gesture_label"] = gesture_chooser_label

		self.output_parameter_widgets["speech"][0].show()
		self.output_parameter_widgets["speech"][0].update()
		self.output_parameter_widgets["speech_label"].show()
		self.output_parameter_widgets["speech_label"].update()
		self.output_parameter_widgets["output"].show()
		self.output_parameter_widgets["output"].update()
		self.output_parameter_widgets["output_label"].show()
		self.output_parameter_widgets["output_label"].update()
		#self.output_parameter_widgets["gaze"].show()
		#self.output_parameter_widgets["gaze"].update()
		#self.output_parameter_widgets["gaze_label"].show()
		#self.output_parameter_widgets["gaze_label"].update()
		self.output_parameter_widgets["gesture"].show()
		self.output_parameter_widgets["gesture"].update()
		self.output_parameter_widgets["gesture_label"].show()
		self.output_parameter_widgets["gesture_label"].update()

	def setup_input_parameters(self, demo_input):
		self.remove_widget_parents(self.output_parameter_widgets)
		self.remove_widget_parents(self.input_parameter_widgets)
		self.parameterization_groupbox.update()

		input_val = demo_input.inp
		timing_val = demo_input.time
		speech_val = demo_input.speech

		input_speech_label = QLabel("Human actor's speech", self.parameterization_groupbox)
		input_speech_label.move(10, 35)
		input_speech = QTextEdit(self.parameterization_groupbox)
		input_speech.setText(speech_val)
		input_speech.setGeometry(10, 50, self.parameterization_groupbox.width()-20, 80)
		input_speech.textChanged.connect(partial(self.on_input_text_edited,demo_input))

		input_label = QLabel("Speech classification", self.parameterization_groupbox)
		input_label.move(10, 155)
		input_chooser = QComboBox(parent=self.parameterization_groupbox)
		for inp in self.Alphabet.get_inputs():
			input_chooser.addItem(inp)
		input_chooser.setGeometry(10,170, self.parameterization_groupbox.width()-20, 30)
		input_chooser.setCurrentIndex(input_chooser.findText(input_val))
		input_chooser.currentTextChanged.connect(partial(self.on_input_select,demo_input))

		'''
		if input_val == "Empty":
			timing_label = QLabel("Length of human pause (sec)", self.parameterization_groupbox)
			timing_label.move(10, 105)
			time_chooser = QSpinBox(parent=self.parameterization_groupbox)
			time_chooser.move(10,120)
			time_chooser.setMinimum(0)
			time_chooser.setMaximum(16)
			time_chooser.setValue(timing_val)   # temporary
			time_chooser.valueChanged.connect(partial(self.on_input_time_select, demo_input))
		'''
		self.input_parameter_widgets["speech"] = (input_speech,demo_input)
		self.input_parameter_widgets["speech_label"] = input_speech_label
		self.input_parameter_widgets["input"] = input_chooser
		self.input_parameter_widgets["input_label"] = input_label
		'''
		if input_val == "Empty":
			self.input_parameter_widgets["timing"] = time_chooser
			self.input_parameter_widgets["timing_label"] = timing_label
		'''
		self.input_parameter_widgets["speech"][0].show()
		self.input_parameter_widgets["speech"][0].update()
		self.input_parameter_widgets["speech_label"].show()
		self.input_parameter_widgets["speech_label"].update()
		self.input_parameter_widgets["input"].show()
		self.input_parameter_widgets["input"].update()
		self.input_parameter_widgets["input_label"].show()
		self.input_parameter_widgets["input_label"].update()
		'''
		if input_val == "Empty":
			self.input_parameter_widgets["timing_label"].show()
			self.input_parameter_widgets["timing_label"].update()
			self.input_parameter_widgets["timing"].show()
			self.input_parameter_widgets["timing"].update()
		'''

	def clear_parameters_pane(self):
		self.remove_widget_parents(self.output_parameter_widgets)
		self.remove_widget_parents(self.input_parameter_widgets)

	def remove_widget_parents(self, widget_dict):
		#print(widget_dict)
		for widget in widget_dict:

			if widget_dict[widget] is not None:
				if widget == "speech":
					demo_item = widget_dict[widget][1]
					demo_item.speech = widget_dict[widget][0].toPlainText()
					widget_dict[widget][0].deleteLater()
				else:
					widget_dict[widget].deleteLater()
				widget_dict[widget] = None

	def on_okay(self):

		# make the updated demo array the same as the new demo array
		self.actual_demo.clear()
		for item in self.demo:
			self.actual_demo.append(item)



		self.update_model_callback()

		self.close()

	def on_cancel(self):
		self.close()

	def on_output_text_edited(self, component):
		component.speech = self.output_parameter_widgets["speech"][0].toPlainText()

	def on_input_text_edited(self, component):
		component.speech = self.input_parameter_widgets["speech"][0].toPlainText()

	def on_output_select(self, output):
		output.output = self.output_parameter_widgets["output"].currentText()
		self.example_drawer.update()

	def on_gaze_select(self, output):
		output.gaze = self.output_parameter_widgets["gaze"].currentText()
		self.example_drawer.update()

	def on_gesture_select(self, output):
		output.gesture = self.output_parameter_widgets["gesture"].currentText()

		# TODO: this is incredibly hacky
		output.updated_gesture = True
		#for item in self.demo:
		#	if output.output == item[1].output:
		#		item[1].gesture = output.gesture
		###############################

		self.example_drawer.update()

	def on_output_time_select(self, output):
		output.time = int(self.output_parameter_widgets["timing"].value())
		self.example_drawer.update()

	def on_input_select(self, input_obj):
		input_obj.inp = self.input_parameter_widgets["input"].currentText()
		self.example_drawer.update()

	def on_input_time_select(self, input_obj):
		input_obj.time = int(self.input_parameter_widgets["timing"].value())
		self.example_drawer.update()
