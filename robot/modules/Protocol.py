class Protocol():
	def __init__(self, mbp, micro, behavior):
		self.MicrointBehaviorPairs = mbp
		self.numMicros = len(mbp)
		self.ChoiceMicro = micro
		self.ChoiceBehavior = behavior

