from time import time

class ProcessTime:
	
	def __init__(self, n):
		self.average_duration = 0.0
		self.n = n
	
	def start(self):
		self. i = 0
		self.last = time()
	
	def update(self):
		now = time()
		duration = now - self.last
		self.last = now
		self.average_duration = (self.i*self.average_duration + duration)/(self.i + 1)
		self.i += 1
	
	def estimate(self):
		return (self.n - self.i) * self.average_duration

