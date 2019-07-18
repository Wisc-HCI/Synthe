from z3 import *
import time
import sys
import csv

class IOReducer:

	def __init__(self, num_outputs, original_demos, original_omega, design, ctx):
		self.num_outputs = num_outputs
		self.demos = original_demos
		self.original_omega = original_omega
		self.design = design
		self.ctx = ctx

	def init_relaxed_outputs(self):
		for demo in self.demos:
			for item in demo.demo_array:
				item[1].relaxed_output = item[1].output
				#if item[1].relaxed_output is None:
				#	exit()

	def solve(self):

		self.init_relaxed_outputs()
		return self.demos

		'''
		READ THE SCALAR WEIGHTS
		'''
		weights = self.read_weights()

		'''
		SET UP SOLVER
		'''
		#z3.set_param("auto_config", "false")
		s = Optimize(ctx=self.ctx)

		'''
		VARIABLE DECLARATIONS
		'''
		# binary variables that tracks existence of an output
		exists = {}
		for omega in self.original_omega:
			omega_id = self.original_omega[omega]
			exists[omega] = Int('exists_{}'.format(omega_id), ctx=self.ctx)

		# binary variables track the relaxed ID of an output
		f = []
		for i in range(len(self.demos)):
			f.append([])
			for j in range(len(self.original_omega)):
				f[i].append([])
				for k in range(len(self.original_omega)):
					f[i][j].append(Int('f_{}{}{}'.format(i,j,k), ctx=self.ctx))

		keylist = list(self.original_omega.keys())

		'''
		CONSTRAINTS
		'''
		# existence cap
		for output in exists:
			s.add(And(exists[output]>=0,exists[output]<=1,self.ctx))
		num_exists = And(True,Sum(list(exists.values()))<=min(self.num_outputs,len(self.original_omega)),self.ctx)
		s.add(num_exists)

		# there can only be one solution for an omega-omega combo
		for i in range(len(self.demos)):
			for j in range(len(self.original_omega)):
				omega_string = keylist[j]
				if self.exists_within_demo(self.demos[i], omega_string):
					s.add(And(True,Sum(f[i][j])==1,self.ctx))
				for k in range(len(self.original_omega)):
					s.add(And(True,f[i][j][k]>=0,f[i][j][k]<=1,self.ctx))

		# bind existence to f
		for output in exists:
			output_id = keylist.index(output)
			for i in range(len(f)):
				for j in range(len(f[i])):
					s.add(Implies(f[i][j][output_id]==1,exists[output]==1,self.ctx))

		'''
		OBJECTIVE FUNCTION
		'''
		#print(keylist)
		#print(weights)
		cost = 0
		for i in range(len(self.demos)):
			for j in range(len(keylist)):
				for k in range(len(keylist)):
					cost += weights[keylist[j]][keylist[k]]*f[i][j][k]

		h=s.minimize(cost)
		s.check()
		s.lower(h)
		m=s.model()
		
		'''
		PROCESS THE RESULTS
		'''
		for d in range(len(self.demos)):
			for item in self.demos[d].demo_array:
				output = keylist.index(item[1].output)

				for k in range(len(keylist)):
					if int(str(m.evaluate(f[d][output][k]))) == 1:
						print("IO REDUCER >> demo {}, output {} changed to {}".format(d,keylist[output],keylist[k]))
						item[1].relaxed_output = keylist[k]
						if keylist[k] is None:
							print("IO REDUCER >> KEYLIST ENTRY IS NONE")
							exit()
		for output in exists:
			print("IO REDUCER >>   {} exists == {}".format(output,str(m.evaluate(exists[output]))))
		print("IO REDUCER >> total cost == {}".format(str(m.evaluate(cost))))

		return self.demos

	def read_weights(self):
		if self.design == "Delivery":
			filename = "weights_delivery.csv"
		elif self.design == "Ticket_Booth":
			filename = "weights_ticket.csv"
		else:
			filename = "weights_infodesk.csv"

		weights = {}

		with open(filename) as csvfile:
			reader = csv.reader(csvfile, delimiter=',')

			row1 = next(reader)
			cats = [item for item in row1 if item != ""]
			
			for row in reader:
				weights[row[0]] = {}
				#print(row[0])
				for i in range(1,len(row)):
					#print(row[i])
					new_output = cats[i-1]
					weights[row[0]][new_output] = 10-int(row[i])
			#exit()

		return weights

	def exists_within_demo(self, demo, omega):
		exists = False
		for item in demo.demo_array:
			if item[1].output == omega:
				exists = True
				break
		return exists
			




