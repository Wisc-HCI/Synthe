class Pair():

	def __init__(type1, type2):
		self.type1 = t1
		self.type2 = t2
		self.map1 = {}
		self.map2 = {}

	def add(self, obj1, obj2):
		if obj1 is not type1 or obj2 is not type2:
			print("ERROR: wrong type in Pair ({},{})".format(obj1,obj2))
			exit(1)

		map1[obj1] = obj2
		map2[obj2] = obj1