import sys
import socket 
import os
import select
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QDialog, QLabel
from PyQt5.QtGui import QFont
from network_notifications import *

class RobotController():

	def __init__(self, frame):
		self.HOST = sys.argv[1]
		self.PORT1 = 8889
		self.frame = frame
		self.connected = False

	def on_click(self):
		if self.connected:
			self.s1.close()
			self.connected = False
			print("ROBOT CONTROLLER >> Connection closed")
			return

		self.s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s1.settimeout(15)
		#self.s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print('ROBOT CONTROLLER >> Robot socket created')
		 
		#Bind socket to local host and port
		try:
			self.s1.bind((self.HOST, self.PORT1))
		except socket.error as msg:
			print('ROBOT CONTROLLER >> Robot bind failed.')
			self.disconnect()
			return
			 
		print('ROBOT CONTROLLER >> Robot socket bind complete')
		 
		try:
			#Start listening on socket
			self.s1.listen(10)
			#self.s2.listen(10)
			print('ROBOT CONTROLLER >> Robot socket now listening')
		
			#now keep talking with the client
			#wait to accept a connection - blocking call
			self.conn1, addr = self.s1.accept()
			print('ROBOT CONTROLLER >> Connected with robot ' + addr[0] + ':' + str(addr[1]) + ' on port ' + str(self.PORT1))
			self.connected = True
		except:
			self.s1.close()
			print("socket closed")

	def simulate(self):

		try:
			print("ROBOT CONTROLLER >> sending interaction file to robot...")
			f = open("../robot/interactions/test_interaction.xml", "rb")
			l = os.path.getsize("../robot/interactions/test_interaction.xml")
			m = f.read(l)
			ready_to_read, ready_to_write, in_error = select.select([], [self.conn1], [])
			ready_to_write[0].sendall(m)

			# ack
			ready_to_read, ready_to_write, in_error = select.select([self.conn1], [], [])
			message1 = ready_to_read[0].recv(1024)

			if message1.decode("utf-8") == '':
				f.close()
				raise Exception('I know Python!')

			print("ROBOT CONTROLLER >> sent")
			f.close()

			self.notification = SimulationNotification(self, self.conn1)
		except (select.error, Exception):
			print("ROBOT CONTROLLER >> Simulator was unable to connect to robot.")
			self.connected = False
			mic_notification = RobotDisconnected("Unable to connect to the robot. Please ask the experimenter for help.")
			mic_notification.exec_()


	def disconnect(self):
		self.connected = False

class SimulationNotification(QDialog):

	def __init__(self, parent, conn1):
		super(SimulationNotification, self).__init__(parent=parent.frame)

		self.parent = parent
		self.conn1 = conn1

		self.resize(360, 100)
		self.label = QLabel("Simulating interaction on the robot.", self)
		self.label.setFont(QFont("Veranda", 20))
		self.label.move(10,10)

		self.instruct_label = QLabel("To stop, say \"exit\" when the robot is listening.", self)
		self.instruct_label.setFont(QFont("Veranda", 14))
		self.instruct_label.move(20, 55)

		print("showing")
		self.show()
		QCoreApplication.processEvents()

		# wait for a signal to return
		ready_to_read, ready_to_write, in_error = select.select([self.conn1], [], [])
		message = ready_to_read[0].recv(1024)
		print("received end signal")

		if message.decode("utf-8") == "error":
			mic_notification = RobotErrorOccurred("An error occured during execution of the robot. Please ask an experimenter for help.")
			mic_notification.exec_()

		self.close()
