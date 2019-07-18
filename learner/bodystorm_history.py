from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QGroupBox, QProgressBar, QListWidget, QListWidgetItem, QDialog
from PyQt5.QtGui import QColor, QPalette
from BodystormExample import *

class BodystormHistory(QGroupBox):

	def __init__(self, name, parent, frame):
		super().__init__(name, parent=parent)
		self.frame = frame
		self.setGeometry(10, 10, self.frame.plotlabel1.width() - 20, self.frame.plotlabel1.height() - 300 - 100 - 40)	 
		self.scrollable_history = QScrollArea(self)
		self.scrollable_history.setGeometry(10, 40, self.width() - 20, self.height() - 65)
		self.scrollable_history.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.bodystorm_list = BodystormList(self.scrollable_history, self)
		self.bodystorm_list.setGeometry(0, 0, self.scrollable_history.width(), self.scrollable_history.height())
		self.bodystorm_list.itemClicked.connect(self.item_checked)

		# qlabel description of checkboxes and session info
		self.headers = QLabel("on/off      bodysession information", self)
		self.headers.move(10, 25)
		self.headers.setFont(QFont("Veranda", 10))

		# to keep track of changes in which demos are checked and not
		self.check_tracker = {}

	def populate_bodystorm_history(self, bodystorm, solution):
		#print("here are the bodystorm demos")
		if self.bodystorm_list.count() > 0:
			self.bodystorm_list.itemDoubleClicked.disconnect()
		self.bodystorm_list.clear()
		self.check_tracker.clear()

		if solution is not None:
			t_err = solution.transition_error

			# although the solution may exist, it might not have 
			for demo_object in bodystorm.demos:
				if demo_object not in t_err:
					t_err[demo_object] = {}
					for i in range(len(demo_object.demo_array)):
						t_err[demo_object][i] = 0

		else:
			t_err = {}
			for demo_object in bodystorm.demos:
				t_err[demo_object] = {}
				for i in range(len(demo_object.demo_array)):
					t_err[demo_object][i] = 0
		for i in range(len(bodystorm.demos)):
			demo_object = bodystorm.demos[i]
			#print("   {}".format(demo_object))

			#print("       {}".format(demo_object))
			if demo_object.activated:
				demo_t_error = t_err[demo_object]
			#	print("           demo error is {}".format(demo_t_error))

				# calculate the percent satisfied
				tot_error = 0
				possible_error = 0
				for key in demo_t_error:
			#		print("TRANSITION ERROR")
			#		print(demo_t_error[key])
					tot_error += demo_t_error[key]

					# NOTE: CHANGE THIS VALUE IF THE VALUE IN THE SAT SOLVER CHANGES
					possible_error += 10

				# we multiply it by 2 so that human inputs are accounted for
				percent_satisfied = 1 - tot_error*1.0/(possible_error*2)
				demo_object.satisfied = percent_satisfied

			# decide on color
			if demo_object.activated == False:
				color = QColor(0, 0, 0, 0)
			elif percent_satisfied >= 1:
				color = QColor(0,0,0,0)
			elif percent_satisfied >= 0.92:
				color = QColor(255,85,50,30)
			elif percent_satisfied >= 0.84:
				color = QColor(255,85,50,60)
			elif percent_satisfied >= 0.76:
				color = QColor(255,85,50,90)
			elif percent_satisfied >= 0.68:
				color = QColor(255,85,50,120)
			elif percent_satisfied >= 0.60:
				color = QColor(255,85,50,150)
			elif percent_satisfied >= 0.52:
				color = QColor(255,85,50,180)
			else:
				color = QColor(255,85,50,210)


			item = QListWidgetItem("  {0:<0}. {1:<15}".format(str(i), str(demo_object)))
			if demo_object.activated == False:
				item.setForeground(QColor(0,0,0,100))
			item.setBackground(QColor(color))
			item.setData(Qt.UserRole, demo_object)
			item.setFont(QFont('Courier'))
			item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
			item.setCheckState(Qt.Checked if demo_object.activated else Qt.Unchecked)
			self.check_tracker[demo_object] = item.checkState()
			self.bodystorm_list.addItem(item)

		self.bodystorm_list.itemDoubleClicked.connect(self.expand_example)

		#for example in self.bodystorm_examples:
			
			#item = QListWidgetItem()
			#item.setSizeHint(example.sizeHint()) 
			#self.bodystorm_list.addItem(item)
			#self.bodystorm_list.setItemWidget(item, example)

	def get_most_recent_item(self):
		return self.bodystorm_list.item(self.bodystorm_list.count() - 1)

	def expand_example(self, item):
		self.userDialog = Example(self, item.data(Qt.UserRole).demo_array, self.frame.update_model)
		self.userDialog.exec_()

	def expand_most_recent_example(self):
		self.expand_example(self.get_most_recent_item())

	def update_model(self):
		self.frame.update_model(self.frame.slider.value())

	def item_checked(self):
		# debugging
		print("ITEM CHECKED:")
		print("pre")
		for i in range(self.bodystorm_list.count()):
			print("{} - {}".format(self.bodystorm_list.item(i).data(Qt.UserRole), self.bodystorm_list.item(i).data(Qt.UserRole).activated))

		#print("pre-database")
		sol_db = self.frame.solution_db
		db_demos = sol_db.db
		#for demos in db_demos:
		#	print("  db item:")
		#	for demo in demos.demos:
		#		print("    {} - {}".format(str(demo), demo.activated))
		# end debugging
		update_model_needed = False
		for i in range(self.bodystorm_list.count()):
			print("active? {}".format(self.bodystorm_list.item(i).data(Qt.UserRole).activated))
			print("checked? {}".format(self.bodystorm_list.item(i).checkState()))
			if (self.bodystorm_list.item(i).checkState() == Qt.Unchecked and self.bodystorm_list.item(i).data(Qt.UserRole).activated == True) or (self.bodystorm_list.item(i).checkState() == Qt.Checked and self.bodystorm_list.item(i).data(Qt.UserRole).activated == False):
			#if self.check_tracker[self.bodystorm_list.item(i).data(Qt.UserRole)] != self.bodystorm_list.item(i).checkState():
				update_model_needed = True

			if self.bodystorm_list.item(i).checkState() == Qt.Unchecked:
				self.bodystorm_list.item(i).data(Qt.UserRole).setActivated(False)
			else:
				self.bodystorm_list.item(i).data(Qt.UserRole).setActivated(True)

		#print("post")
		#for i in range(self.bodystorm_list.count()):
		#	print("{} - {}".format(self.bodystorm_list.item(i).data(Qt.UserRole), self.bodystorm_list.item(i).data(Qt.UserRole).activated))
		if update_model_needed:
			self.update_model()

class BodystormList(QListWidget):

	def __init__(self, parent, pane):
		super().__init__(parent=parent)
		self.pane = pane

	def keyPressEvent(self, event):
		if event.key() == 16777219: # previously Qt.Key_Delete
			self._del_item()

	def _del_item(self):
		for item in self.selectedItems():
			self.takeItem(self.row(item))
			item.data(Qt.UserRole).markForDeletion()
		self.pane.update_model()
