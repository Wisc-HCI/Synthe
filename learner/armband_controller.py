import socket
import pickle
import select
import sys
from gesture_training_pane import *

class ArmbandController:

	def __init__(self, connector):
		self.HOST = "localhost"
		self.PORT1 = 8878
		self.message1 = None
		self.message2 = None
		self.connected = False

	def onclick(self):

		if self.connected:
			self.s1.close()
			self.connected = False
			print("ROBOT CONTROLLER >> Connection closed")
			return

		self.s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s1.settimeout(15)
		#self.s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print('SERVER >> Socket created')

		#Bind socket to local host and port
		try:
			self.s1.bind((self.HOST, self.PORT1))
		#	self.s2.bind((self.HOST, self.PORT2))
		except socket.error as msg:
			print('Bind failed.')
			return

		print('SERVER >> Socket bind complete')

		#Start listening on socket
		self.s1.listen(10)
		#self.s2.listen(10)
		print('SERVER >> Socket now listening')

		try:
			#now keep talking with the client
			#wait to accept a connection - blocking call
			self.conn1, addr = self.s1.accept()
			print('SERVER >> Connected with intent parser 1' + addr[0] + ':' + str(addr[1]) + ' on port ' + str(self.PORT1))

		except:
			self.s1.close()
			print("socket closed")

	def calibrate(self):
		self.new_design_dialog = GestureTrackerDialog()
		self.new_design_dialog.exec_()

	def start_record(self):
		try:

			# send the start notification
			ready_to_read, ready_to_write, in_error = select.select([], [self.conn1], [])
			ready_to_write[0].send(b"sigstart")

			# receive acknowledgement
			'''
			ready_to_read, ready_to_write, in_error = select.select([self.conn1], [], [])
			message1 = ready_to_read[0].recv(1024)
			ready_to_read, ready_to_write, in_error = select.select([self.conn2], [], [])
			message2 = ready_to_read[0].recv(1024)

			if message1.decode("utf-8") == '' or message2.decode("utf-8") == '':
				raise Exception('I know Python!')
			'''

			return True

		except (select.error, Exception):
			self.conn1.close()
			self.conn2.close()
			print("SERVER >> Armbands disconnected")

			return False

	def end_record(self, threadname):
		try:
			ready_to_read, ready_to_write, in_error = select.select([], [self.conn1], [])
			ready_to_write[0].send(b"sigend")

			print("ended the recording, waiting for data to return")
			ready_to_read, ready_to_write, in_error = select.select([self.conn1], [], [])
			message1 = ready_to_read[0].recv(8192)
			print("part1 returned...")

			#return message1, message2
			self.message1 = message1
			self.message2 = message1
		except select.error:
			self.conn1.close()
			self.conn2.close()
			print("SERVER >> Armbands disconnected during recording")

			return None

	def get_return_vals(self):
		if self.message1 is not None and self.message2 is not None:
			message1 = self.message1
			message2 = self.message2
			return message1, message2
		else:
			return None

	def clear_messages(self):
		self.message1 = None
		self.message2 = None

	def close_connection(self):
		self.conn1.shutdown(2)
		self.conn2.shutdown(2)
		self.conn1.close()
		self.conn2.close()
