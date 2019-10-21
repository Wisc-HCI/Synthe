from copy import deepcopy

class SolutionDatabase():

	 def __init__(self):
	 	self.db = {}
	 	self.in_progress = None

	 def clear_db(self):
	 	self.db = {}
	 	self.in_progress = None

	 def add(self, demo_list, solution, size):
	 	#print("inside add")
	 	if self.query(demo_list, size) is None:
	 		# add to the database
	 		self.db[DemoContainer(demo_list, size)] = solution

	 	#print(str(self))

	 def query(self, demo_list, size):
	 	#print("inside query")
	 	queried_solution = None

	 	for demos in self.db:
	 		if demos.is_same(demo_list, size):
	 			queried_solution = self.db[demos]
	 			break

	 	return queried_solution

	 def set_in_progress(self, demo_list, size):
	 	self.in_progress = DemoContainer(demo_list, size)

	 def check_if_in_progress(self, demo_list, size):
	 	if self.in_progress == None:
	 		return False
	 	else:
	 		if self.in_progress.is_same(demo_list, size):
	 			return True
	 		else:
	 			return False

	 def remove_in_progress(self):
	 	self.in_progress = None

	 def __str__(self):
	 	string = "solution database:\n"
	 	for demo_container in self.db:
	 		string += str(demo_container)
	 	return string

class DemoContainer():

	def __init__(self, demos, size):
		self.demos = deepcopy(demos)
		self.size = size

	def __str__(self):
		string = "demo container"
		for demo in self.demos:
			string += "DEMO: {} - {}\n".format(str(demo), "activated" if demo.activated else "INactive")
		return string

	def is_same(self, other_demos, size):
		#print("ARE THEY THE SAME")
		#print(self)
		#print("~~~")
		if self.size != size:
			return False
		else:

			is_same = True

			# check one direction
			is_same = self.is_same_helper(self.demos, other_demos)

			if is_same == False:
				#print("IS SAME? False")
				return is_same

			# check the other direction
			is_same = self.is_same_helper(other_demos, self.demos)
			#print("IS SAME? {}".format(is_same))
			return is_same

	def is_same_helper(self, demos1, demos2):
		is_same = True
		# check one direction
		for i in range(len(demos1)):

			if demos1[i].activated:

				own_demo = demos1[i]
				found_same_demo = False

				for j in range(len(demos2)):

					if demos2[j].activated:
						other_demo = demos2[j]

						if own_demo.is_same(other_demo):
							found_same_demo = True

				if not found_same_demo:
					is_same = False
					break

		return is_same

	def __str__(self):
		string = "list of demos in container\n"
		for demo in self.demos:
			string += str(demo)
			string += "\n"
		return string