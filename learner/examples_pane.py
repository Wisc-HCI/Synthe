from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QGroupBox, QProgressBar, QListWidget, QListWidgetItem, QDialog, QLabel
from example_drawer import *
from BodystormExample import Example

class ExamplesPane(QDialog):

	def __init__(self, bodystorm, update_model_callback):
		super(ExamplesPane, self).__init__()

		self.update_model_callback = update_model_callback
		self.model_update_needed = False

		self.resize(1200,600)
		self.scrollarea_groupbox = QGroupBox("Demonstrations", parent=self)
		self.scrollarea_groupbox.setGeometry(10, 10, self.width() - 20, self.height() - 50)

		self.scroll_area = QScrollArea(self.scrollarea_groupbox)
		self.scroll_area.setGeometry(0, 18, self.scrollarea_groupbox.width(), self.scrollarea_groupbox.height()-18)
		self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

		self.area_label = ExampleDrawerContainer(parent=self)
		self.area_label.setGeometry(0,0,self.scroll_area.width() if self.scroll_area.width()>(((bodystorm.get_max_demo_len()+1) * 150 + 50 + 80)) else (((bodystorm.get_max_demo_len()+1) * 150 + 50 + 80)), len(bodystorm.demos)*120)

		curr_yval = 0
		examples = []

		for demo in bodystorm.demos:
			example = ExampleDrawer(self.area_label, demo.demo_array, self, 200, curr_yval, False)
			example.set_start_x(50)
			example.set_move_x(150)
			example.set_rect_width(80)
			example.set_rect_height(40)
			example.set_font_size(10)
			example.link_double_click(self.future_callback_required)
			examples.append(example)

			curr_yval += 120
		self.scroll_area.setWidget(self.area_label)

		self.set_buttons()

	def future_callback_required(self):
		self.model_update_needed = True

	def set_buttons(self):
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

	def on_okay(self):
		if self.model_update_needed:
			self.update_model_callback()

		self.close()

	def on_cancel(self):
		self.close()

class ExampleDrawerContainer(QLabel):

	def __init__(self, parent):
		super(ExampleDrawerContainer, self).__init__(parent=parent)
		self.parent = parent
		# unlinked at the moment
		self.Alphabet = None

	def update_traces(self, bodystorm, update_model_callback):

		self.update_model_callback = update_model_callback
		self.model_update_needed = False

		self.resize(self.parent.width(),self.parent.height())
		#self.scrollarea_groupbox = QGroupBox("Bodysessions", parent=self)
		#self.scrollarea_groupbox.setGeometry(10, 10, self.width() - 20, self.height() - 50)

		self.scroll_area = QScrollArea(parent=self)
		self.scroll_area.setGeometry(0, 18, self.width(), self.height()-18)
		self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

		self.area_label = ExampleDrawerContainer(parent=self)
		self.area_label.setGeometry(0,0,
									self.scroll_area.width() if self.scroll_area.width()>(((bodystorm.get_max_demo_len()+1) * 150 + 50 + 80)) else (((bodystorm.get_max_demo_len()+1) * 150 + 50 + 80)),
									len(bodystorm.demos)*120)

		curr_yval = 0
		examples = []

		for demo in bodystorm.demos:
			example = ExampleDrawer(self.area_label, demo.demo_array, self, 200, curr_yval, False)
			example.set_start_x(50)
			example.set_move_x(150)
			example.set_rect_width(80)
			example.set_rect_height(40)
			example.set_font_size(10)
			example.link_double_click(self.future_callback_required)
			examples.append(example)

			curr_yval += 120
		self.scroll_area.setWidget(self.area_label)

		self.update()
		self.show()
	def future_callback_required(self):
		self.model_update_needed = True

	def expand_example(self, item, callback):
		self.userDialog = Example(self, item, callback, self.Alphabet)
		self.userDialog.exec_()
