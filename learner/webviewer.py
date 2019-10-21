import sys
import json
from grapher import *
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

class WebViewer(QWebEngineView):

	def __init__(self, frame, parent):
		super().__init__(parent)
		self.label = parent
		self.frame = frame

		#self.setStyleSheet("background-color: blue")

	def make_blank_graphs(self):
		self.make_dimensions_file()
		with open('d3js/links.json', 'w') as outfile:
			json.dump([], outfile)
		with open('d3js/root.json', 'w') as outfile:
			json.dump({}, outfile)
		with open('d3js/children.json', 'w') as outfile:
			json.dump({}, outfile)

	def update_graph(self, solution, bodystorm):
		self.make_dimensions_file()
		raw_edges = solution.results

		Grapher().make_mealy(raw_edges,self.frame.bodystorm)

		original_state_mapper = {}
		for edge in raw_edges:
			if int(str(edge[0])) not in original_state_mapper:
				original_state_mapper[int(str(edge[0]))] = [int(str(edge[0]))]
			if int(str(edge[2])) not in original_state_mapper:
				original_state_mapper[int(str(edge[2]))] = [int(str(edge[2]))]

		# DAGRE GRAPH
		# first consolidate transitions with the same io
		# edges are: (source id, source name, target id, target name)
		edges_dict = {}
		for edge in raw_edges:
			gesture = int(str(solution.gesture_map[(int(str(edge[0])),str(edge[1]),int(str(edge[2])),int(str(edge[3])))]))
			edge_io = (int(str(edge[0])), int(str(edge[2])), int(str(edge[3])), gesture)
			if edge_io in edges_dict:
				input_to_append = edge[1]
				edges_dict[edge_io] = (edges_dict[edge_io][0],
									   edges_dict[edge_io][1] + "\n{}".format(input_to_append),
									   edges_dict[edge_io][2],
									   edges_dict[edge_io][3])
			else:
				edges_dict[edge_io] = edge

		edges = []
		for key, value in edges_dict.items():
			edges.append(value)

		# loop through the results and map states to names
		'''
		state2name = {}
		for i in range(self.frame.slider.value()):
			state2name[i] = str(i) if i > 0 else "Start"
		for edge in edges:
			if int(str(edge[2])) != -1:
				state2name[int(str(edge[2]))] = bodystorm.OMEGA_map_rev[int(str(edge[3]))]
		'''

		reachability, gestures = solution.get_reachability(bodystorm)
		solution.compute_speech_map(bodystorm)
		print(solution.speech_map)

		json_array = {}
		json_array["links"] = []
		for edge in edges:
			if str(edge[2]) != '-1':

				# check if input has a newline in it
				inp_gesture_key = str(edge[1])
				idx = str(edge[1]).find('\n')
				if idx != -1:
					inp_gesture_key = str(edge[1])[:idx]

				temp_dict = {"source": int(str(edge[0])),
							 "target": int(str(edge[2])),
							 "input": edge[1],
							 "output": bodystorm.OMEGA_map_rev[int(str(edge[3]))],
							 "gesture": bodystorm.GESTURE_map_rev[int(str(solution.gesture_map[(int(str(edge[0])),inp_gesture_key,int(str(edge[2])),int(str(edge[3])))]))]}
							 #"gesture": gestures[bodystorm.OMEGA_map_rev[int(str(edge[3]))]]}
				json_array["links"].append(temp_dict)

		# we want the followind:
		# state ID
		# gaze
		# gesture
		# whether reachable or not
		# whether it is a final state or not
		json_array["states"] = {}
		for st in range(len(reachability)):
			if st in original_state_mapper:
				for state in original_state_mapper[st]:
					#print("reach: {}".format(reachability[st]["gesture"]))
					json_array["states"][state] = {"id": state,
											    "reachable": reachability[st]["reach"],
											    "final": True if reachability[st]["reach"] == True and len(reachability[st]["outputs"]) == 0 else False}
			#print(reachability[st])
			#r=print(json_array["states"][st])

		with open('d3js/links.json', 'w') as outfile:
			json.dump(json_array, outfile)

		Grapher().make_regular(raw_edges,self.frame.bodystorm)

	def load_graph(self, type):
		if type == "basic":
			url = QUrl.fromLocalFile("/Users/david/Documents/UW_Research/BodystormingHRI/learner/d3js/example.html")
		elif type == "dagre":
			url = QUrl.fromLocalFile("/Users/david/Documents/UW_Research/synthe/learner/d3js/example2_mealy.html")
		else:
			url = QUrl.fromLocalFile("/Users/david/Documents/UW_Research/BodystormingHRI/learner/d3js/example3.html")

		self.load(url)

		print("painting dot view")
		self.frame.dotview.load_image(self.frame.label,"graph.png")

	def load_blank_html(self):
		url = QUrl.fromLocalFile("/Users/david/Documents/UW_Research/BodystormingHRI/learner/d3js/blank.html")
		self.load(url)

	def make_dimensions_file(self):
		dimension_dict = {"width":self.frame.width - 410, "height":self.frame.height - 105, "font":self.frame.font_size, "behaviors":self.frame.nonverbal_behaviors}
		with open('d3js/dimensions.json', 'w') as outfile:
			json.dump(dimension_dict, outfile)
