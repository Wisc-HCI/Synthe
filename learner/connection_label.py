from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtGui import QImage, QPalette, QBrush, QIcon, QPixmap, QPainter, QColor, QFont
from server import *
from name_dialog import *

class ConnectionLabel(QLabel):

	def __init__(self, parent, gui):
		super().__init__(parent=parent)

		self.setGeometry(10, parent.height()-20, 146, 12)
		self.gui = gui

		self.connection_label = QLabel("Connection Status:", self)
		self.connection_label.move(0,0)
		self.connection_label.setFont(QFont("Veranda", 10))

		#self.network_button = QPushButton('', self)
		#self.network_button.setGeometry(125, 0, 12, 12)
		#connectIcon = QIcon()
		#connectIcon.addPixmap(QPixmap("fig/ConnectIcon.png"))
		#self.network_button.setIcon(connectIcon)
		#self.network_button.clicked.connect(self.on_click)
		#self.network_button.setCheckable(True)
		self.designer1 = False
		self.designer2 = False
		self.bodystorm_listener = Server(self)
		self.bodystorm_listener.ready.connect(self.connect_designer)
		self.bodystorm_listener.update.connect(self.upload_bodystorms)
		self.update()

	def on_click(self):



		try:
			self.bodystorm_listener.start()
		except:
			print("CONN LABEL >> Error: unable to start thread")
			traceback.print_exc()

		self.gui.bodystorm_listener = self.bodystorm_listener

	def close_socket(self):
		self.bodystorm_listener.close_socket()
		self.disconnect()

	def upload_bodystorms(self):
		print("pass")

	def disconnect(self):
		self.designer1 = False
		self.designer2 = False
		self.update()

	def connect_designer(self, designerID):
		if designerID == 1:
			self.designer1 = True
			self.update()
		else:
			self.designer2 = True
			self.update()

			self.userDialog = NameDialog(self)
			self.userDialog.exec_()

	def update_names(self, name1, name2):
		self.gui.update_names(name1, name2)

	def paintEvent(self,e):
		qp = QPainter(self)
		qp.begin(self)

		if self.designer1:
			qp.drawPixmap(95,0, 12, 12, QPixmap("fig/ConnectedIcon.png"))
		else:
			qp.drawPixmap(95,1, 10, 10, QPixmap("fig/NotconnectedIcon.png"))
		if self.designer2:
			qp.drawPixmap(110,0, 12, 12, QPixmap("fig/ConnectedIcon.png"))
		else:
			qp.drawPixmap(110,1, 10, 10, QPixmap("fig/NotconnectedIcon.png"))
		qp.end()

