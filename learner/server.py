import socket
import pickle
import select
from PyQt5 import QtCore
import sys
from network_notifications import *

class Server(QtCore.QThread):

	ready = QtCore.pyqtSignal(object)
	update = QtCore.pyqtSignal(object)

	def __init__(self, connector):
		QtCore.QThread.__init__(self)
		self.HOST = sys.argv[1]
		self.PORT1 = 8888
		self.connector = connector
		self.message1 = None
		self.message2 = None

	def run(self):
		 
		self.s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.s1.settimeout(15)
		#self.s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print('MICROPHONES >> Socket created')
		 
		#Bind socket to local host and port
		try:
			self.s1.bind((self.HOST, self.PORT1))
		#	self.s2.bind((self.HOST, self.PORT2))
		except socket.error as msg:
			print('Bind failed.')
			#self.s1.shutdown(socket.SHUT_RDWR)
			self.s1.close()
			return
			 
		print('MICROPHONES >> Socket bind complete')
		 
		#Start listening on socket
		self.s1.listen(10)
		#self.s2.listen(10)
		print('MICROPHONES >> Socket now listening')
	
		#now keep talking with the client
		#wait to accept a connection - blocking call
		try:
			self.conn1, addr = self.s1.accept()
			print('MICROPHONES >> Connected with intent parser 1' + addr[0] + ':' + str(addr[1]) + ' on port ' + str(self.PORT1))
			self.ready.emit(1)

			self.conn2, addr = self.s1.accept()
			print('MICROPHONES >> Connected with intent parser 2' + addr[0] + ':' + str(addr[1]) + ' on port ' + str(self.PORT1))
			self.ready.emit(2)
		except:
			print("MICROPHONES >> socket timeout")
			#self.s1.shutdown(socket.SHUT_RDWR)
			self.s1.close()

	def close_socket(self):
		#self.s1.shutdown(socket.SHUT_RDWR)
		self.s1.close()
		print("MICROPHONES >> socket closed")

	def start_record(self):
		try:

			# send the start notification
			ready_to_read, ready_to_write, in_error = select.select([], [self.conn1], [])
			ready_to_write[0].send(b"begin")
			ready_to_read, ready_to_write, in_error = select.select([], [self.conn2], [])
			ready_to_write[0].send(b"begin")

			# receive acknowledgement
			ready_to_read, ready_to_write, in_error = select.select([self.conn1], [], [])
			message1 = ready_to_read[0].recv(1024)
			ready_to_read, ready_to_write, in_error = select.select([self.conn2], [], [])
			message2 = ready_to_read[0].recv(1024)

			if message1.decode("utf-8") == '' or message2.decode("utf-8") == '':
				raise Exception('I know Python!')

			return True

		except (select.error, Exception):
			self.conn1.close()
			self.conn2.close()
			print("SERVER >> Microphones disconnected")
			self.connector.disconnect()
			mic_notification = MicrophonesDisconnected("The microphones were disconnected. Please ask the experimenter for help.")
			mic_notification.exec_()

			return False

	def end_record(self, threadname):
		try:

			# attempting to send the end message
			print("attempting to send the end message")
			ready_to_read, ready_to_write, in_error = select.select([], [self.conn1], [])
			ready_to_write[0].send(b"end")
			ready_to_read, ready_to_write, in_error = select.select([], [self.conn2], [])
			ready_to_write[0].send(b"end")

			ready_to_read, ready_to_write, in_error = select.select([self.conn1], [], [])
			message1 = ready_to_read[0].recv(8192)
			ready_to_read, ready_to_write, in_error = select.select([self.conn2], [], [])
			message2 = ready_to_read[0].recv(8192)

			self.message1 = pickle.loads(message1)
			self.message2 = pickle.loads(message2)

			#return message1, message2
		except select.error:
			self.conn1.close()
			self.conn2.close()
			print("SERVER >> Microphones disconnected during recording")
			self.connector.disconnect()


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