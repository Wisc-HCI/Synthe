from gurobipy import *

class GOptimizer():

	def __init__(self):
		pass

	def solve(self, N, sigma, omega, demos):
		self.sigma = sigma
		self.omega = omega
		m = Model("mip")

		'''
		VARIABLES (and bounds)
		'''
		# there should only be one box fox f_T
		f_T = {}
		for i in range(N+1):
			f_T[i] = {}
			for j in range(len(sigma)):
				f_T[i][j] = {}
				for k in range(N+1):
					f_T[i][j][k] = m.addVar(vtype=GRB.BINARY, name="f_T_{}_{}_{}".format(i,j,k))

		# same with f_A
		f_A = {}
		for i in range(N+1):
			f_A[i] = {}
			for j in range(len(sigma)):
				f_A[i][j] = {}
				for k in range(len(omega)):
					f_A[i][j][k] = m.addVar(vtype=GRB.BINARY, name="f_A_{}_{}_{}".format(i,j,k))

		# demo state variables
		'''
		demo_vars = {}
		counter=0
		for demo_obj in demos:
			demo_vars[demo_obj] = {}
			counter+=1
			for i in range(len(demo_obj.demo_array)+1):
				demo_vars[demo_obj][i] = m.addVar(vtype=GRB.INTEGER, name="demo_{}_{}".format(counter, i))
				m.addConstr(demo_vars[demo_obj][i] >= 0)
				m.addConstr(demo_vars[demo_obj][i] <= N)
		'''

		'''
		CONSTRAINTS (not including bounds)
		'''
		# f_T is a function
		for i in range(N+1):
			for j in range(len(sigma)):
				m.addConstr(quicksum(f_T[i][j][k] for k in range(N+1)) <= 1)

		# f_A is a function
		for i in range(N+1):
			for j in range(len(sigma)):
				m.addConstr(quicksum(f_A[i][j][k] for k in range(len(omega))) <= 1)

		# encode the demos into f_T
		# start by "seeding" the demos
		for demo_obj in demos:
			demo = demo_obj.demo_array
			inp = demo[0][0].inp
			m.addConstr(quicksum(f_T[0][sigma[inp]][i] for i in range(N+1)) == 1)
		# then force linkage
		test = None
		for i in range(len(demos)):
			demo_obj = demos[i]
			demo = demo_obj.demo_array
			for item in demo:
				print(" --> ({}-{})".format(item[0].inp, item[1].output))
			for j in range(len(demo_obj.demo_array) - 1):

				inp1 = demo[j][0].inp
				inp2 = demo[j+1][0].inp
				out1 = demo[j][1].output
				out2 = demo[j+1][1].output

				print("\nbeginning constriant adding process")
				#m.addConstr(quicksum(f_T[0][sigma[inp1]][k] * self.recursive_sum(m, N, f_T, demo,1,k) for k in range(N+1)) == 1)

				# special case -- always start at state 0
				if j == 0:
					m.addConstr(quicksum(f_T[0][sigma[inp1]][k] * quicksum(f_T[k][sigma[inp2]][l] for l in range(N+1)) for k in range(N+1)) == 1)
					m.addConstr(f_A[0][sigma[inp1]][omega[out1]] == 1)
				else:
					m.addConstr(quicksum(quicksum(f_T[k][sigma[inp1]][l] + f_A[k][sigma[inp1]][omega[out1]] for k in range(N+1)) * 
										 quicksum(f_T[l][sigma[inp2]][m] + f_A[l][sigma[inp2]][omega[out2]] for m in range(N+1)) for l in range(N+1)) == 4)


		'''
		OBJECTIVE function
		'''
		m.setObjective(quicksum(f_T[i][j][k] for i in range(N+1) for j in range(len(sigma)) for k in range(N+1)) +
						quicksum(f_A[i][j][k] for i in range(N+1) for j in range(len(sigma)) for k in range(len(omega))), GRB.MINIMIZE)

		m.optimize()
		status = m.status
		if status in (GRB.INF_OR_UNBD, GRB.INFEASIBLE, GRB.UNBOUNDED):
			print('The relaxed model cannot be solved \
				   because it is infeasible or unbounded')
			exit(1)

		if status != GRB.OPTIMAL:
			print('Optimization was stopped with status %d' % status)
			exit(1)
		for i in range(N+1):
			for j in range(len(sigma)):
				for k in range(N+1):
					if f_T[i][j][k].X > 0:
						print("{} from state {} on input {} to state {}".format(f_T[i][j][k].X, i, j, k))
				for k in range(len(omega)):
					if f_A[i][j][k].X > 0:
						print("{} from state {} on input {} to omega {}".format(f_A[i][j][k].X, i, j, k))
		print(omega)

	def recursive_sum(self, m, N, f_T, demo, demo_idx, sumVar):

		inp = self.sigma[demo[demo_idx][0].inp]

		if demo_idx == len(demo) - 1:
			print("base case")
			return quicksum(f_T[sumVar][inp][n] for n in range(N+1))
		else:
			print("recursing")
			return quicksum(f_T[sumVar][inp][n] * self.recursive_sum(m, N, f_T, demo,demo_idx+1, n) for n in range(N+1))



