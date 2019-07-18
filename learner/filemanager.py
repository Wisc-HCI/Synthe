import pickle
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QFileDialog

class SaveFile(QDialog):

	def __init__(self, bodystorm):
		super(SaveFile, self).__init__()
		self.bodystorm = bodystorm

		self.resize(400, 100)
		self.setWindowTitle("Save Traces")

		self.label = QLabel("filename", parent=self)
		self.label.setGeometry(10, 10, 60, 20)

		self.textarea = QLineEdit(self)
		self.textarea.setGeometry(80, 10, 200, 20)

		button_width = 100
		button_height = 35
		button_spacing = 20
		self.okay = QPushButton('Okay', self)
		self.okay.setGeometry(self.width()/2 - button_width - button_spacing/2, self.height() - button_height, button_width, button_height)
		self.okay.setStyleSheet('QPushButton {color: black;}')

		self.cancel = QPushButton("Cancel", self)
		self.cancel.setGeometry(self.width()/2 + button_spacing/2, self.height() - button_height, button_width, button_height)

		self.okay.clicked.connect(self.save)
		self.cancel.clicked.connect(self.cancel_save)

	def save(self, autosave=False):

		path = "saved_traces/"
		pickle.dump(self.bodystorm, open("{}{}.p".format(path, "autosave" if autosave else self.textarea.text()), "wb"))

		self.close()

	def cancel_save(self):

		self.close()

class LoadFile(QFileDialog):

	def __init__(self):
		super(LoadFile, self).__init__()

	def openFileNameDialog(self):	
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","Pickle Files (*.p)", options=options)
		if fileName:
			#print(fileName)
			return pickle.load(open(fileName, "rb"))
		else:
			None

