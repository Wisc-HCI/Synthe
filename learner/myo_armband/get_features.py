import numpy as np
from scipy import signal
from matplotlib import pyplot as plt
from preprocessor import *

class FeatureGetter:

	def parse_Y(self, data_y):
		Y = []
		for i in range(len(data_y)):

			y = -1
			if data_y[i][0] == 1:
				y = 0
			elif data_y[i][1] == 1:
				y = 1
			elif data_y[i][2] == 1:
				y = 2
			elif data_y[i][3] == 1:
				y = 3
			else:
				y = 4

			Y.append(y)

		return Y

	def get_features(self, data_x, bounds_x, add_vect):
		preproc = Preprocessor()
		mm_vals = preproc.get_max_min_values(data_x)
		X = []
		for i in range(len(data_x)):
			#print(bounds_x[i][0])
			#print(bounds_x[i][1]+1)
			data_bx = data_x[i][0][bounds_x[i][0]:bounds_x[i][1]+1]
			data_by = data_x[i][1][bounds_x[i][0]:bounds_x[i][1]+1]
			data_bz = data_x[i][2][bounds_x[i][0]:bounds_x[i][1]+1]

			gyro_bx = data_x[i][3][bounds_x[i][0]:bounds_x[i][1]+1]
			gyro_by = data_x[i][4][bounds_x[i][0]:bounds_x[i][1]+1]
			gyro_bz = data_x[i][5][bounds_x[i][0]:bounds_x[i][1]+1]

			length = self.get_duration(bounds_x[i])
			#print("data_bx: {}".format(data_bx))
			abs_x = self.get_max_absolute_value(data_bx)
			abs_y = self.get_max_absolute_value(data_by)
			abs_z = self.get_max_absolute_value(data_bz)
			ave_energy_x = self.get_average_energy(data_bx)
			ave_energy_y = self.get_average_energy(data_by)
			ave_energy_z = self.get_average_energy(data_bz)
			std_x = self.get_stdev(data_bx)
			std_y = self.get_stdev(data_by)
			std_z = self.get_stdev(data_bz)

			# number of extrema in regular
			smoothed_x = preproc.get_smoothed_curve(data_bx, 7)
			x_sm_peak_idxs = list(signal.find_peaks(smoothed_x, prominence=0.15)[0]) + list(signal.find_peaks(np.array([i*-1 for i in list(smoothed_x)]), prominence=0.15)[0])
			x_sm_peaks = len(signal.find_peaks(smoothed_x,prominence=0.15)[0]) + len(signal.find_peaks(np.array([i*-1 for i in list(smoothed_x)]), prominence=0.15)[0])
			smoothed_y = preproc.get_smoothed_curve(data_by, 7)
			y_sm_peak_idxs = list(signal.find_peaks(smoothed_y)[0]) + list(signal.find_peaks(np.array([i*-1 for i in list(smoothed_y)]))[0])
			y_sm_peaks = len(signal.find_peaks(smoothed_y,prominence=0.15)[0]) + len(signal.find_peaks(np.array([i*-1 for i in list(smoothed_y)]), prominence=0.15)[0])
			smoothed_z = preproc.get_smoothed_curve(data_bz, 7)
			z_sm_peak_idxs = list(signal.find_peaks(smoothed_z)[0]) + list(signal.find_peaks(np.array([i*-1 for i in list(smoothed_z)]))[0])
			z_sm_peaks = len(signal.find_peaks(smoothed_z,prominence=0.15)[0]) + len(signal.find_peaks(np.array([i*-1 for i in list(smoothed_z)]), prominence=0.15)[0])
			#print("x: {}, y: {}, z: {}".format(x_sm_peaks, y_sm_peaks, z_sm_peaks))

			# number of extrema in gyroscope
			smoothed_x = preproc.get_smoothed_curve(gyro_bx, 7)
			#x_sm_peak_idxs = list(signal.find_peaks(smoothed_x, prominence=0.15)[0]) + list(signal.find_peaks(np.array([i*-1 for i in list(smoothed_x)]), prominence=0.15)[0])
			x_gyro_peaks = len(signal.find_peaks(smoothed_x,prominence=0.15)[0]) + len(signal.find_peaks(np.array([i*-1 for i in list(smoothed_x)]), prominence=0.15)[0])
			smoothed_y = preproc.get_smoothed_curve(gyro_by, 7)
			#y_sm_peak_idxs = list(signal.find_peaks(smoothed_y)[0]) + list(signal.find_peaks(np.array([i*-1 for i in list(smoothed_y)]))[0])
			y_gyro_peaks = len(signal.find_peaks(smoothed_y,prominence=0.15)[0]) + len(signal.find_peaks(np.array([i*-1 for i in list(smoothed_y)]), prominence=0.15)[0])
			smoothed_z = preproc.get_smoothed_curve(gyro_bz, 7)
			#z_sm_peak_idxs = list(signal.find_peaks(smoothed_z)[0]) + list(signal.find_peaks(np.array([i*-1 for i in list(smoothed_z)]))[0])
			z_gyro_peaks = len(signal.find_peaks(smoothed_z,prominence=0.15)[0]) + len(signal.find_peaks(np.array([i*-1 for i in list(smoothed_z)]), prominence=0.15)[0])

			# number of extrema in fft
			#fft_x = np.fft.fft(preproc.get_smoothed_curve(data_bx))
			fft_x = np.fft.fft(data_bx)
			x_peaks = len(signal.find_peaks(fft_x,prominence=20)[0]) + len(signal.find_peaks(fft_x*-1,prominence=20)[0])
			#fft_y = np.fft.fft(preproc.get_smoothed_curve(data_by))
			fft_y = np.fft.fft(data_by)
			y_peaks = len(signal.find_peaks(fft_y,prominence=20)[0]) + len(signal.find_peaks(fft_y*-1,prominence=20)[0])
			#fft_z = np.fft.fft(preproc.get_smoothed_curve(data_bz))
			fft_z = np.fft.fft(data_bz)
			z_peaks = len(signal.find_peaks(fft_z,prominence=20)[0]) + len(signal.find_peaks(fft_z*-1,prominence=20)[0])
			#print("x: {}, y: {}, z: {}".format(x_peaks, y_peaks, z_peaks))

			'''
			plt.subplot(2, 1, 1)
			plt.plot(data_bx)

			plt.subplot(2, 1, 2)
			plt.plot(fft_x)
			plt.show()
			plt.exit()
			'''
			'''
			plt.subplot(12, 1, 1)
			plt.ylim(mm_vals["x_min"], mm_vals["x_max"])
			#for x in x_sm_peak_idxs:
			#	plt.axvline(x,color="333333")
			plt.plot(data_bx)

			plt.subplot(12, 1, 2)
			plt.ylim(mm_vals["y_min"], mm_vals["y_max"])
			#for x in y_sm_peak_idxs:
			#	plt.axvline(x,color="333333")
			plt.plot(data_by)

			plt.subplot(12, 1, 3)
			plt.ylim(mm_vals["z_min"], mm_vals["z_max"])
			#for x in z_sm_peak_idxs:
			#	plt.axvline(x,color="333333")
			plt.plot(data_bz)

			plt.subplot(12, 1, 4)
			#for x in x_sm_peak_idxs:
			#	plt.axvline(x,color="333333")
			plt.plot(fft_x)

			plt.subplot(12, 1, 5)
			#for x in y_sm_peak_idxs:
			#	plt.axvline(x,color="333333")
			plt.plot(fft_y)

			plt.subplot(12, 1, 6)
			#for x in z_sm_peak_idxs:
			#	plt.axvline(x,color="333333")
			plt.plot(fft_z)

			plt.subplot(12, 1, 7)
			plt.ylim(mm_vals["gx_min"], mm_vals["gx_max"])
			plt.plot(gyro_bx)

			plt.subplot(12, 1, 8)
			plt.ylim(mm_vals["gy_min"], mm_vals["gy_max"])
			plt.plot(gyro_by)

			plt.subplot(12, 1, 9)
			plt.ylim(mm_vals["gz_min"], mm_vals["gz_max"])
			plt.plot(gyro_bz)
			plt.show()
			'''

			# obtain average acceleration
			if len(data_bx) > 2:
				x_grad = np.gradient(preproc.get_smoothed_curve(data_bx))
				y_grad = np.gradient(preproc.get_smoothed_curve(data_by))
				z_grad = np.gradient(preproc.get_smoothed_curve(data_bz))
			else:
				x_grad = 0
				y_grad = 0
				z_grad = 0
			ave_energy_grad_x = self.get_average_energy(x_grad)
			ave_energy_grad_y = self.get_average_energy(y_grad)
			ave_energy_grad_z = self.get_average_energy(z_grad)
			abs_grad_x = self.get_max_absolute_value(x_grad)
			abs_grad_y = self.get_max_absolute_value(y_grad)
			abs_grad_z = self.get_max_absolute_value(z_grad)

			# obtain average fft acceleration
			if len(data_bx) > 2:
				x_fft_grad = np.gradient(fft_x)
				y_fft_grad = np.gradient(fft_y)
				z_fft_grad = np.gradient(fft_z)
			else:
				x_fft_grad = 0
				y_fft_grad = 0
				z_fft_grad = 0
			ave_energy_grad_x_fft = self.get_average_energy(x_fft_grad)
			ave_energy_grad_y_fft = self.get_average_energy(y_fft_grad)
			ave_energy_grad_z_fft = self.get_average_energy(z_fft_grad)
			abs_grad_x_fft = self.get_max_absolute_value(x_fft_grad)
			abs_grad_y_fft = self.get_max_absolute_value(y_fft_grad)
			abs_grad_z_fft = self.get_max_absolute_value(z_fft_grad)

			# obtain average gyro acceleration
			if len(data_bx) > 2:
				x_gyro_grad = np.gradient(fft_x)
				y_gyro_grad = np.gradient(fft_y)
				z_gyro_grad = np.gradient(fft_z)
			else:
				x_gyro_grad = 0
				y_gyro_grad = 0
				z_gyro_grad = 0
			ave_energy_grad_x_gyro = self.get_average_energy(x_gyro_grad)
			ave_energy_grad_y_gyro = self.get_average_energy(y_gyro_grad)
			ave_energy_grad_z_gyro = self.get_average_energy(z_gyro_grad)
			abs_grad_x_gyro = self.get_max_absolute_value(x_gyro_grad)
			abs_grad_y_gyro = self.get_max_absolute_value(y_gyro_grad)
			abs_grad_z_gyro = self.get_max_absolute_value(z_gyro_grad)

			# obtain average gyroscope rate


			arr = []
			if add_vect[0]:
				arr.append(length)
			if add_vect[1]:
				arr.append(abs_x)
				arr.append(abs_y)
				arr.append(abs_z)
			if add_vect[2]:
				arr.append(ave_energy_x)
				arr.append(ave_energy_y)
				arr.append(ave_energy_z)
			if add_vect[3]:
				arr.append(std_x)
				arr.append(std_y)
				arr.append(std_z)
			if add_vect[4]:
				arr.append(x_peaks*1.0/length if length > 0 else 0)
				arr.append(y_peaks*1.0/length if length > 0 else 0)
				arr.append(z_peaks*1.0/length if length > 0 else 0)
			if add_vect[5]:
				arr.append(ave_energy_grad_x)
				arr.append(ave_energy_grad_y)
				arr.append(ave_energy_grad_z)
			if add_vect[6]:
				arr.append(abs_grad_x)
				arr.append(abs_grad_y)
				arr.append(abs_grad_z)

			# peak frequency
			if add_vect[7]:
				arr.append(x_sm_peaks*1.0/length if length > 0 else 0)
				arr.append(y_sm_peaks*1.0/length if length > 0 else 0)
				arr.append(z_sm_peaks*1.0/length if length > 0 else 0)
			if add_vect[8]:
				arr.append(ave_energy_grad_x_fft)
				arr.append(ave_energy_grad_y_fft)
				arr.append(ave_energy_grad_z_fft)
			if add_vect[9]:
				arr.append(abs_grad_x_fft)
				arr.append(abs_grad_y_fft)
				arr.append(abs_grad_z_fft)

			if add_vect[10]:
				arr.append(x_gyro_peaks*1.0/length if length > 0 else 0)
				arr.append(y_gyro_peaks*1.0/length if length > 0 else 0)
				arr.append(z_gyro_peaks*1.0/length if length > 0 else 0)
			if add_vect[11]:
				arr.append(ave_energy_grad_x_gyro)
				arr.append(ave_energy_grad_y_gyro)
				arr.append(ave_energy_grad_z_gyro)
			if add_vect[12]:
				arr.append(abs_grad_x_gyro)
				arr.append(abs_grad_y_gyro)
				arr.append(abs_grad_z_gyro)

			#X.append([length, abs_x, abs_y, abs_z, ave_energy_x, ave_energy_y, ave_energy_z, std_x, std_y, std_z, x_peaks, y_peaks, z_peaks, ave_energy_grad_x, ave_energy_grad_y, ave_energy_grad_z, abs_grad_x, abs_grad_y, abs_grad_z, x_sm_peaks, y_sm_peaks, z_sm_peaks, ave_energy_grad_x, ave_energy_grad_y, ave_energy_grad_z, abs_grad_x, abs_grad_y, abs_grad_z])
			#X.append([x_peaks, y_peaks, z_peaks])
			X.append(arr)

		return X

	def get_duration(self, bounds):
		return (bounds[1]+1) - bounds[0]

	def get_max_absolute_value(self, data):
		abs_data = np.absolute(np.array(data))
		return np.max(abs_data)

	def get_average_energy(self, data):
		abs_data = np.absolute(np.array(data))
		return np.average(abs_data)

	def get_stdev(self, data):
		return np.std(np.array(data))
