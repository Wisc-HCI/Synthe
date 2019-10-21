import math
import numpy as np

class Preprocessor():

	def low_pass(self, data):
		pass

	def find_active_frames(self, data):
		bounds = []
		for i in range(len(data)):
			x = data[i][0]
			idxs_x,_ = self.get_idx_active_frames(x)
			if len(idxs_x) == 0:
				idxs_x.append(0)
				idxs_x.append(0)
			y = data[i][1]
			idxs_y,_ = self.get_idx_active_frames(y)
			if len(idxs_y) == 0:
				idxs_y.append(0)
				idxs_y.append(0)
			z = data[i][2]
			idxs_z,_ = self.get_idx_active_frames(z)
			if len(idxs_z) == 0:
				idxs_z.append(0)
				idxs_z.append(0)

			start = min(idxs_x[0], idxs_y[0], idxs_z[0])
			end = max(idxs_x[-1], idxs_y[-1], idxs_z[-1])
			bounds.append((start,end))

		return bounds

	def get_max_min_values(self, data):
		mm = {}
		mm["x_max"] = 0
		mm["x_min"] = 0
		mm["y_max"] = 0
		mm["y_min"] = 0
		mm["z_max"] = 0
		mm["z_min"] = 0

		mm["gx_max"] = 0
		mm["gx_min"] = 0
		mm["gy_max"] = 0
		mm["gy_min"] = 0
		mm["gz_max"] = 0
		mm["gz_min"] = 0

		for d in data:
			self.get_max_min_vals_helper(d,0,"x_max","max",mm)
			self.get_max_min_vals_helper(d,0,"x_min","min",mm)
			self.get_max_min_vals_helper(d,1,"y_max","max",mm)
			self.get_max_min_vals_helper(d,1,"y_min","min",mm)
			self.get_max_min_vals_helper(d,2,"z_max","max",mm)
			self.get_max_min_vals_helper(d,2,"z_min","min",mm)
			self.get_max_min_vals_helper(d,3,"gx_max","max",mm)
			self.get_max_min_vals_helper(d,3,"gx_min","min",mm)
			self.get_max_min_vals_helper(d,4,"gy_max","max",mm)
			self.get_max_min_vals_helper(d,4,"gy_min","min",mm)
			self.get_max_min_vals_helper(d,5,"gz_max","max",mm)
			self.get_max_min_vals_helper(d,5,"gz_min","min",mm)

		return mm

	def get_max_min_vals_helper(self, d, idx, string, minmax, mm):

		if minmax == "max":
			if max(d[idx]) > mm[string]:
				mm[string] = max(d[idx])
		else:
			if min(d[idx]) < mm[string]:
				mm[string] = min(d[idx])

	def get_idx_active_frames(self, data):
		win_size = 25
		win_side = int(math.floor(win_size/2.0))
		curr_idx = 0
		end_idx = len(data)
		cutoff = 0.25

		active_idxs = []
		flat_idxs = []

		while curr_idx < end_idx:
			to_eval = [data[i] for i in range(max(0,curr_idx - win_side), min(len(data),curr_idx + win_side+1))]

			std = np.std(np.array(to_eval))


			if std >= 0.05:
				active_idxs.append(curr_idx)
			else:
				flat_idxs.append(curr_idx)

			curr_idx += 1

		return active_idxs, flat_idxs

	def get_smoothed_curve(self, data, win_size=31):
		win_side = int(math.floor(win_size/2.0))
		curr_idx = 0
		end_idx = len(data)
		cutoff = 0.25

		smoothed_idxs = []

		while curr_idx < end_idx:
			to_eval = [data[i] for i in range(max(0,curr_idx - win_side), min(len(data),curr_idx + win_side+1))]

			w = [((i+1)/(math.ceil(win_size/2.0))) if i < math.ceil(win_size/2.0) else ((win_size-i)/(math.ceil(win_size/2.0))) for i in range(win_size)]
			
			# trim w if necessary
			if curr_idx - win_side < 0:
				w = w[abs(curr_idx - win_side):]
			if curr_idx + win_side+1 > len(data):
				w = w[:len(w) - abs(len(data)-(curr_idx + win_side+1))]

			ave = np.average(np.array(to_eval), weights=w)
			smoothed_idxs.append(ave)

			curr_idx += 1

		return smoothed_idxs
