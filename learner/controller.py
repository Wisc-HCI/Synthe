from bodystorming_simulation import *
from sat_solver import *
from PyQt5 import QtCore
from copy import deepcopy
import time

class Controller(QtCore.QThread):

	update_progress = QtCore.pyqtSignal(object,object)
	update_UI = QtCore.pyqtSignal(object)
	update_solution = QtCore.pyqtSignal(object,object)
	remove_thread = QtCore.pyqtSignal()

	def __init__(self):
		QtCore.QThread.__init__(self)
		self.n = 4
		self.bodystorm = None
		self.new_trace = False
		self.terminated = False
		self.gui = None
		self.solver = None
		self.thread_wait = True
		self.threadcount = -1

	def connect_to_parent(self, term_signal):
		term_signal.connect(self.terminate)

	def run(self):

		self.solver = SMTSolver(self.update_progress, self, self.threadcount)
		self.solver.solve(self.bodystorm, self.n)

		if self.terminated == False:
			solution = self.solver.solution
			print("CONTROLLER >> solution is none? {}".format(solution is None))
			if solution is not None:
				#Grapher().make_mealy(solution,self.bodystorm)
				#self.GUI.load_image("graph.png")
				self.update_solution.emit(solution,self.n)
				self.update_UI.emit(self.new_trace)
			else:
				self.update_solution.emit(solution,self.n)
				self.update_progress.emit(0,"")

		#print("CONTROLLER >> emitting, then waiting 4 seconds")
		#self.thread_wait = False
		#print("CONTROLLER >> terminated")
		self.remove_thread.emit()

	def terminate(self):
		print("CONTROLLER >> terminating {}".format(self))
		self.terminated = True
		self.solver.terminate()
		self.remove_thread.emit()

		self.thread_wait = False
		print("CONTROLLER >> terminated")





