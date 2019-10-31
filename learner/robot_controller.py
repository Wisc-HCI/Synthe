import sys
import socket
import re
import os
import select
import traceback
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QDialog, QLabel
from PyQt5.QtGui import QFont
from network_notifications import *

import google
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue


class MicrophoneStream(object):
	"""Opens a recording stream as a generator yielding the audio chunks."""
	def __init__(self, rate, chunk):
		self._rate = rate
		self._chunk = chunk

		# Create a thread-safe buffer of audio data
		self._buff = queue.Queue()
		self.closed = True

	def __enter__(self):
		self._audio_interface = pyaudio.PyAudio()
		self._audio_stream = self._audio_interface.open(
			format=pyaudio.paInt16,
			# The API currently only supports 1-channel (mono) audio
			# https://goo.gl/z757pE
			channels=1, rate=self._rate,
			input=True, frames_per_buffer=self._chunk,
			# Run the audio stream asynchronously to fill the buffer object.
			# This is necessary so that the input device's buffer doesn't
			# overflow while the calling thread makes network requests, etc.
			stream_callback=self._fill_buffer,
		)

		self.closed = False

		return self

	def __exit__(self, type, value, traceback):
		print("GCP_STREAMING >> MicrophoneStream: exiting....closing MicrophoneStream....")
		self._audio_stream.stop_stream()
		self._audio_stream.close()
		self.closed = True
		# Signal the generator to terminate so that the client's
		# streaming_recognize method will not block the process termination.
		self._buff.put(None)
		self._audio_interface.terminate()

	def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
		"""Continuously collect data from the audio stream, into the buffer."""
		self._buff.put(in_data)
		return None, pyaudio.paContinue

	def generator(self):
		while not self.closed:
			# Use a blocking get() to ensure there's at least one chunk of
			# data, and stop iteration if the chunk is None, indicating the
			# end of the audio stream.
			chunk = self._buff.get()
			if chunk is None:
				return
			data = [chunk]

			# Now consume whatever other data's still buffered.
			while True:
				try:
					chunk = self._buff.get(block=False)
					if chunk is None:
						return
					data.append(chunk)
				except queue.Empty:
					break

			yield b''.join(data)


class GCP_Streamer:
	"""

	Requirements:
		using pip:
			pip install pyaudio
			pip install --upgrade google-cloud-speech
		Need to configure Google Cloud credentials:
			export GOOGLE_APPLICATION_CREDENTIALS="[PATH]"
	"""

	def __init__(self):
		# Audio recording parameters
		self.rate = 16000
		self.chunk = int(self.rate / 10)  # 100ms

		# Google Speech Client config parameters
		self.language_code = 'en-US' # US English
		self.punctuation = True # audo attaching punctuation
		self.single_utterance = True # indicates whether this request should automatically end after speech is no longer detected.


		# Google Speech Client Initialization
		self.client = speech.SpeechClient()
		self.config = types.RecognitionConfig(
			encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
			sample_rate_hertz=self.rate,
			language_code=self.language_code,
			enable_automatic_punctuation=self.punctuation)
		self.streaming_config = types.StreamingRecognitionConfig(
			config=self.config,
			interim_results=True,
			single_utterance = self.single_utterance)

		self.timeout = 5 # The amount of time, in seconds, to wait for the request to complete.
		self.done_streaming_flag = False

	def streaming_results(self, responses, keywords=None):
		"""Iterates through server responses and returns them.

		Each response may contain multiple results, and each result may contain
		multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
		return only the transcription for the top alternative of the top result.

		In this case, responses are provided for interim results as well. If the
		response is an interim one, this method stamps a carriage at the end of
		it, to allow the next result to overwrite it, until the response is a
		final one. For the final one, a newline is added to preserve the
		finalized transcription.

		The method will return a result when a keyword is detected or when one
		of the exit/done flag is set.

		:param keywords: keywords for breaking the listening loop and exiting
		the streaming. (Thjs has not been tested yet)
		:param responses: server responses from server. The responses passed is
		a generator that will block until a response is provided by the server.
		Return: the final sentence
		"""
		final_transcript = ''
		num_chars_printed = 0
		for response in responses:
			if not response.results:
				continue

			# The `results` list is consecutive. For streaming, we only care about
			# the first result being considered, since once it's `is_final`, it
			# moves on to considering the next utterance.
			result = response.results[0]
			if not result.alternatives:
				continue

			# Display the transcription of the top alternative.
			transcript = result.alternatives[0].transcript

			# Display interim results, but with a carriage return at the end of the
			# line, so subsequent lines will overwrite them.
			#
			# If the previous result was longer than this one, we need to print
			# some extra spaces to overwrite the previous result
			overwrite_chars = ' ' * (num_chars_printed - len(transcript))

			if not result.is_final:
				sys.stdout.write(transcript + overwrite_chars + '\r')
				sys.stdout.flush()

				num_chars_printed = len(transcript)

			else:
				print("one line of final result: {}".format(transcript + overwrite_chars) )
				final_transcript +=  transcript + overwrite_chars

				# Exit recognition if keywords detected
				if re.search(r'\b(exit|quit)\b', transcript, re.I):
					print('Stop keywords detected. Exiting..')
					break

				# Exit recognition if done_streaming_flag is set
				if self.done_streaming_flag or self.single_utterance:
					print('GCP_Streamer: stop flag is set. Streaming exiting..')
					break

				num_chars_printed = 0

		return final_transcript

	def recognize_speech(self):
		"""
		Main functions that uses microphone to listen for speech and return
		each line of transcription results as string text
		"""
		with MicrophoneStream(self.rate, self.chunk) as stream:
			try:
				audio_generator = stream.generator()
				requests = (types.StreamingRecognizeRequest(audio_content=content)
							for content in audio_generator)

				responses = self.client.streaming_recognize(self.streaming_config, requests, timeout=self.timeout)

				transcript = self.streaming_results(responses)
			except google.api_core.exceptions.DeadlineExceeded as e:
				print("GCP_STREAMING >> timeout")
				return "#timeout#"

		return transcript

class RobotController():

	def __init__(self, frame, host="localhost", userobot=1):
		self.HOST = host
		self.PORT1 = 8889
		self.frame = frame
		self.connected = False
		if userobot==1:
			self.gcp_speech = GCP_Streamer()

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

			while True:
				ready_to_read, ready_to_write, in_error = select.select([self.conn1], [], [])
				message1 = ready_to_read[0].recv(1024)

				if message1.decode("utf-8") == "endlisten":
					break

				# recognize speech
				transcript = self.gcp_speech.recognize_speech()
				print(transcript)
				ready_to_read, ready_to_write, in_error = select.select([], [self.conn1], [])
				ready_to_write[0].sendall(str.encode(transcript))

			ready_to_read, ready_to_write, in_error = select.select([], [self.conn1], [])
			ready_to_write[0].sendall(b"endlisten")

			self.notification = SimulationNotification(self, self.conn1)

			print("ROBOT CONTROLLER >> sent")
			f.close()
		except (select.error, Exception):
			print("ROBOT CONTROLLER >> Simulator was unable to connect to robot.")
			traceback.print_exc()
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
