from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap

class DotViewer():

	def load_image(self, label, filename):
		pixmap = QPixmap(filename)
		if pixmap.width() > label.width() or pixmap.height() > label.height():
			pixmap = pixmap.scaled(label.width(), label.height(), Qt.KeepAspectRatio)
		label.setPixmap(pixmap)