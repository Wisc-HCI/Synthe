class GestureChunk:

	def __init__(self, start, end, clas, prob):
		self.start_idx = start
		self.end_idx = end
		self.length = self.end_idx - self.start_idx

		self.classification = clas
		self.probability = prob

		self.start_time = -1
		self.end_time = -1

	def compare(self, other):
		if other.start_idx == self.start_idx and other.end_idx == self.end_idx:
			return True
		return False

	def stringify(self):
		return "[{},{},{}]".format(self.start_time, self.end_time, self.classification)

	def __str__(self):
		return "{} with probability {} from {} to {}".format(self.classification, self.probability, self.start_idx, self.end_idx)