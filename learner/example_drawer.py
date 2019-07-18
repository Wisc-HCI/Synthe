from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtWidgets import QLabel, QDialog, QScrollArea, QGroupBox, QPushButton, QComboBox
from PyQt5.QtGui import QImage, QPalette, QBrush, QIcon, QPixmap, QPainter, QColor, QFont, QPainterPath, QPen, QPolygonF
from bodystorming_simulation import Output, Demo, Input
from functools import partial

class ExampleDrawer(QLabel):

	def __init__(self, parent, demo, parameterization_pane, height=None, yval=None, buttons=True):
		super(ExampleDrawer, self).__init__(parent)
		if height is None or yval is None:
			self.setGeometry(0, 0, parent.width() if parent.width()>(((len(demo)+1) * 300 + 50 + 160)) else (((len(demo)+1) * 300 + 50 + 160)), parent.height())
		else:
			self.setGeometry(0,yval,parent.width() if parent.width()>(((len(demo)+1) * 300 + 50 + 160)) else (((len(demo)+1) * 300 + 50 + 160)),height)
		self.demo = demo

		p = self.palette()
		p.setColor(self.backgroundRole(), Qt.white)
		self.setPalette(p)

		self.start_x = 50
		self.move_x = 300
		self.rect_width = 160
		self.rect_height = 80
		self.font_size = 18

		self.double_click_example = False
		self.buttons_allowed = buttons
		self.button_idx_map = {}

		if self.buttons_allowed:
			self.add_append_remove_buttons()

		# store gaze and gesture settings
		gaze2output = {}
		gesture2output = {}

		self.parameterization_pane = parameterization_pane
		self.parent = parent

	def set_start_x(self, start_x):
		self.start_x = start_x

	def set_move_x(self, move_x):
		self.move_x = move_x

	def set_rect_width(self, rect_width):
		self.rect_width = rect_width

	def set_rect_height(self, rect_height):
		self.rect_height = rect_height

	def set_font_size(self, size):
		self.font_size = size

	def link_double_click(self, callback):
		self.double_click_example = True
		self.callback = callback

	def mousePressEvent(self, event):
		#print("1")
		pass

	def mouseReleaseEvent(self, event):
		#print("2")
		pass

	def mouseDoubleClickEvent(self, event):
		if self.double_click_example:
			self.parent.expand_example(self.demo, self.callback)
		else:
			# determine whether clicking on an input or an output

			x = event.x()
			y = event.y()

			# output
			output_id = self.coord_is_in_output(x, y)
			if output_id > -1:
				self.parameterization_pane.setup_output_parameters(self.demo[output_id][1])

			# input
			input_id = self.coord_is_in_input(x, y)
			if input_id > -1:
				self.parameterization_pane.setup_input_parameters(self.demo[input_id][0])

	def coord_is_in_input(self, x, y):
		is_within = -1

		for i in range(len(self.demo)):
			#print("DEMO: {}".format(self.demo[i]))
			if x > (self.start_x + (i)*self.move_x + self.rect_width) and x < (self.start_x + (i)*self.move_x + self.rect_width + self.move_x-self.rect_width):
				if y > self.height()/2 - 22 and y < self.height()/2 + 22:
					is_within = i
					break

		return is_within

	def coord_is_in_output(self, x, y):
		is_within = -1

		for i in range(len(self.demo)):
			if x > (self.start_x + (i+1)*self.move_x) and x < (self.start_x + (i+1)*self.move_x + self.rect_width):
				if y > self.height()/2 - self.rect_height/2 and y < self.height()/2 + self.rect_height/2:
					is_within = i
					break

		return is_within

	def add_append_remove_buttons(self):
		
		for i in range(len(self.demo)):
			self.place_add_button(i)

			if len(self.demo) > 1:
				button_remove = QPushButton("-", parent=self)
				button_remove.setGeometry(self.start_x + (i+1)*self.move_x - 25, self.height()/2 + 10, 15,15)
				button_remove.setStyleSheet('QPushButton {color: black;}')
				button_remove.clicked.connect(partial(self.removeDemoItem,i))
				self.button_idx_map[button_remove] = i

		self.place_add_button(len(self.demo))

	def place_add_button(self, i):
		button_add = QPushButton("+", parent=self)
		button_add.setGeometry(self.start_x + self.rect_width + 6 + (i)*self.move_x, self.height()/2 + 10, 15,15)
		button_add.setStyleSheet('QPushButton {color: black;}')
		button_add.clicked.connect(partial(self.addDemoItem,i))
		self.button_idx_map[button_add] = i

	def addDemoItem(self, i):
		#print("i: {}".format(i))
		out = Output("Empty")
		out.gaze = "None"
		out.gesture = "None"
		out.speech = ""

		inp = Input("Empty")

		demo_item = (inp, out)

		if i < len(self.demo):
			self.demo.insert(i, demo_item)
		else:
			self.demo.append(demo_item)
		self.update_buttons()
		self.parameterization_pane.clear_parameters_pane()

		self.resize(self.parent.width() if self.parent.width()>(((len(self.demo)+1) * 300 + 50 + 160)) else (((len(self.demo)+1) * 300 + 50 + 160)), self.height())

	def removeDemoItem(self, i):
		del self.demo[i]
		self.update_buttons()
		self.parameterization_pane.clear_parameters_pane()

		self.resize(self.parent.width() if self.parent.width()>(((len(self.demo)+1) * 300 + 50 + 160)) else (((len(self.demo)+1) * 300 + 50 + 160)), self.height())

	def update_buttons(self):
		for button in self.button_idx_map:
			button.setParent(None)
		self.button_idx_map.clear()
		self.update()
		if self.buttons_allowed:
			self.add_append_remove_buttons()

			for button in self.button_idx_map:
				button.show()
				button.update()

	def paintEvent(self, event):

		start_x = self.start_x
		move_x = self.move_x
		rect_width = self.rect_width

		qp = QPainter()
		qp.begin(self)

		# add the initial state and output label (with no options)
		qp.setPen(QColor(0, 0, 0))
		qp.setFont(QFont('Arial', 14))
		qp.drawText(start_x,self.height()/2 - self.rect_height/2 -5, "0.")

		path = QPainterPath()
		brush = QBrush(QColor(0,255,150,255))
		qp.setBrush(brush)
		path.addRoundedRect(QRectF(start_x,self.height()/2 - self.rect_height/2,rect_width,self.rect_height), 10, 10);
		qp.setPen(QColor(0, 0, 0))
		qp.drawPath(path);

		qp.setPen(QColor(0, 0, 0))
		qp.setFont(QFont('Arial', self.font_size))
		rect = QRectF(start_x,self.height()/2 - self.rect_height/2 + 10,self.rect_width,20)
		qp.drawText(rect, Qt.AlignHCenter, "Start")

		for i in range(len(self.demo)):

			# now draw the example
			brush = QBrush(QColor(0,0,0,25))
			qp.setBrush(brush)

			'''
			states (robot output)
			'''
			qp.setPen(QColor(0, 0, 0))
			demo_item = self.demo[i]

			if i == len(self.demo) - 1:
				brush = QBrush(QColor(255,0,0,100))
				qp.setBrush(brush)

			path = QPainterPath()
			path.addRoundedRect(QRectF(start_x + (i+1)*move_x,self.height()/2 - self.rect_height/2,self.rect_width,self.rect_height), 10, 10);
			qp.drawPath(path);

			# label the output
			qp.setPen(QColor(0, 0, 0))
			qp.setFont(QFont('Arial', self.font_size))
			rect = QRectF(start_x + (i+1)*move_x + 10,self.height()/2 - self.rect_height/2 + 10,self.rect_width,20)
			qp.drawText(rect, Qt.AlignLeft, self.demo[i][1].output) 

			if self.buttons_allowed:
				qp.setPen(QColor(0, 0, 0, 150))
				#qp.setFont(QFont('Minion Pro', self.font_size - 3, italic=True))
				#rect = QRectF(start_x + (i+1)*move_x + 10,self.height()/2 - self.rect_height/2 + int(round(9.0*self.rect_height/16)),self.rect_width - 20,20)
				#qp.drawText(rect, Qt.AlignLeft, "Gaze: {}".format(self.demo[i][1].gaze))

				qp.setFont(QFont('Minion Pro', self.font_size - 3, italic=True))
				rect = QRectF(start_x + (i+1)*move_x + 10,self.height()/2 - self.rect_height/2 + int(round(9.0*self.rect_height/16)),self.rect_width - 20,20)
				qp.drawText(rect, Qt.AlignLeft, "Gesture: {}".format(self.demo[i][1].gesture))

			# number the state
			qp.setPen(QColor(0, 0, 0))
			qp.setFont(QFont('Arial', 14))
			qp.drawText(start_x + (i+1)*move_x + 5,self.height()/2 - self.rect_height/2 - 5, "{}.".format(i+1))			

			'''
			arrow (human input)
			'''
			brush = QBrush(QColor(0,0,0,255))
			qp.setBrush(brush)
			qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
			qp.drawLine(start_x + (i)*move_x + rect_width, self.height()/2, start_x + (i+1)*move_x, self.height()/2)
			polygon = QPolygonF()
			polygon.append(QPointF(start_x + (i+1)*move_x - 15, self.height()/2 + 5))
			polygon.append(QPointF(start_x + (i+1)*move_x - 15, self.height()/2 - 5))
			polygon.append(QPointF(start_x + (i+1)*move_x, self.height()/2))
			qp.drawPolygon(polygon)

			# label the input
			rect = QRectF(start_x + (i)*move_x + rect_width, self.height()/2 - 11.0*self.rect_height/40, move_x-rect_width, 22)
			qp.setPen(QColor(0, 0, 0))
			qp.setFont(QFont('Minion Pro', self.font_size, italic=True))
			qp.drawText(rect, Qt.AlignHCenter, self.demo[i][0].inp)

		qp.end()