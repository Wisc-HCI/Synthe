from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QFont

class StatusPane(QLabel):

	def __init__(self, parent):
		super(StatusPane, self).__init__(parent=parent)

		self.setGeometry(0,50,parent.width(),40)
		self.status = [False,False,False] # recording, waiting, updating
		#self.setWindowFlags(Qt.FramelessWindowHint)
		#self.setAttribute(Qt.WA_TranslucentBackground)
		#self.setStyleSheet("background:transparent;background-color:green")

	def update_status(self, category):
		self.hide()
		if category=="record":
			self.setStyleSheet("QLabel {background-color: rgba(250,0,0,100); color: white}")
			self.setText("  recording")
			self.status[0] = True
		elif category=="wait":
			self.setStyleSheet("QLabel {background-color: rgba(0,0,0,100); color: white}")
			self.setText("  analyzing audio, please wait...")
			self.status[1] = True
		elif category=="updating":
			self.setStyleSheet("QLabel {background-color: rgba(255,150,0,100); color: white}")
			self.setText("  computing interaction -- you may discuss or bodystorm")
			self.status[2] = True
		self.setAlignment(Qt.AlignLeft)
		self.setFont(QFont("Veranda", 30, QFont.Bold))
		#pixmap = QPixmap(filename)
		#if pixmap.width() > self.width() or pixmap.height() > self.height():
		#	pixmap = pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
		#self.setPixmap(pixmap)

		self.show()
		self.update()
		self.repaint()

	def remove_status(self, toremove):
		if toremove == "all":
			self.status = [False,False,False]
			self.hide()
		elif toremove == "recording" and self.status[0]:
			self.status[0] = False
			self.check_if_can_hide()
			self.hide()
		elif toremove == "waiting" and self.status[1]:
			self.status[1] = False
			self.check_if_can_hide()
			self.hide()
		elif toremove == "updating" and self.status [2]:
			self.status[2] = False
			self.check_if_can_hide()
			self.hide()
		else:
			self.status = [False,False,False]
			self.hide()

	def check_if_can_hide(self):
		if not self.status[0] and not self.status[1] and not self.status[2]:
			self.hide()