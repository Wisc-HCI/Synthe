from z3 import *
from random import shuffle
import time
import copy
import faulthandler

class SMTSolver:
	'''
	Class that contains the solving code
	'''

	def __init__(self, progress_updater, controller):
		self.sigma = None
		self.omega = None
		self.gaze = None
		self.gesture = None
		self.solution = None

		# progress bar stuff, largely unimportant
		self.progress_updater = progress_updater
		self.curr_progress = 50

		# forget the thread
		self.forget_thread = False

		# parent
		self.controller = controller

		# context
		self.ctx = Context()

	def terminate(self):
		print("SAT SOLVER >> forgetting the current thread")
		self.forget_thread = True

	def solve(self, bodystorm, n=5):
		faulthandler.enable()
		'''
		Called externally to generate an automata
		Input: (1) the list of demos (accessible through the bodystorm object)
			   (2) the MAX number of states
		'''

		# for the max sat recursion, this keeps track of the
		# minimal allowable length, and prevents un-needed
		# further recursion
		self.min_solution_length = 0

		# dictionaries of inputs, outputs, gazes, and gestures that map to their corresponding state ID's
		self.sigma = bodystorm.SIGMA_map
		self.omega = bodystorm.OMEGA_map
		self.gaze = bodystorm.GAZE_map     # gaze is not part of the model anymore
		self.gesture = bodystorm.GESTURE_map

		# FOR DEBUGGING: store info about each recursion call
		self.recursion_tracker = []

		print("Finding automata with max n={}".format(n))

		# some demonstrations have been 'disabled' by participants
		active_demos = bodystorm.get_active_demos()

		# solve
		self.solution = self.solve_helper(n, copy.copy(active_demos))

		# if there is a solution, 
		if self.forget_thread:
			return
		if self.solution is not None:
			satisfied_demos = self.solution.demos

			# update the status of active vs. non-active demos
			for demo in active_demos:
				if demo not in satisfied_demos:
					demo.setActivated(False)

		# DEBUG the recursive process
		#if self.solution is not None:
		#	for result in self.solution.results:
		#		print(result)
		# self.print_recursion_tracker()

		# in the UI, update the progress bar to 90%
		print(self.sigma)
		if not self.forget_thread:
			self.progress_updater.emit(90)

	def solve_helper(self, n, demos):
		'''
		Recursive method for generating automata

		Input: (1) MAX number of states
			   (2) the list of demos
		'''

		# track the time it takes to solve
		then = time.time()

		# in the UI, update the progress bar
		if not self.forget_thread:
			self.progress_updater.emit(self.curr_progress)
		self.curr_progress = self.curr_progress + 1 if self.curr_progress < 90 else 90

		# add to the recursion tracker
		self.recursion_tracker.append(set(demos))

		# base cases
		if self.solution is not None and len(self.solution.demos) > len(demos):
			print("Returning, as there exists a better solution impossible to achieve with the current set of demos.")
			return None
		elif len(demos) == 0:
			print("0 demos provided.")
			return None

		'''FUNCTIONS'''
		# f_T: SxA->S mapping of states and inputs to states
		f_T = Function('f_T', IntSort(ctx=self.ctx), IntSort(ctx=self.ctx), IntSort(ctx=self.ctx))

		# f_A: SxA->A mapping of states and inputs to outputs
		f_A = Function('f_A', IntSort(ctx=self.ctx), IntSort(ctx=self.ctx), IntSort(ctx=self.ctx))

		# f_ge: S->Ga mapping of states to gestures
		f_ge = Function('f_ge', IntSort(ctx=self.ctx), IntSort(ctx=self.ctx))

		'''ERROR VARIABLES'''
		# transition error
		t_err = {}
		for i in range(len(demos)):
			demo_object = demos[i]
			t_err[demo_object] = {}
			demo = demo_object.demo_array

			for j in range(len(demo)):
				print('t_err_%s_%s' % (i,j))
				t_err[demo_object][j] = Int('t_err_%s_%s' % (i,j), ctx=self.ctx)

		# gesture error
		ge_err = {}
		for i in range(len(demos)):
			demo_object = demos[i]
			ge_err[demo_object] = {}
			demo = demo_object.demo_array

			for j in range(len(demo)):
				ge_err[demo_object][j] = Int('ge_err_%s_%s' % (i,j), ctx=self.ctx)

		'''OTHER VARIABLES'''
		# track the number of transitions
		pos_state = {}
		for i in range(n+1):
			pos_state[i] = {}
			for j in range(len(self.sigma)):
				pos_state[i][j] = Int('pos_state_{}_{}'.format(i,j), ctx=self.ctx)

		# get the transition 'CONS'traints
		print("setting up constraints")
		CONS_transitions = self.compute_transition_constraints(demos, f_T, f_A, f_ge, t_err, ge_err, pos_state, n)

		# set up the optimization problem
		# z3.set_param("auto_config", "false")
		s = Optimize(ctx=self.ctx)
		#s.set("timeout", 10)
		#set_option(timeout=60000)
		s.add(CONS_transitions)

		# sum up the transition error
		t_error = 0
		for demo_obj in t_err:
			for i in t_err[demo_obj]:
				t_error += t_err[demo_obj][i]

		# sum up the gesture error
		ge_error = 0
		for demo_obj in ge_err:
			for i in ge_err[demo_obj]:
				ge_error += ge_err[demo_obj][i]

		# sum up the number of transitions
		num_transitions = 0
		for i in range(n+1):
			for j in range(len(self.sigma)):
				num_transitions += pos_state[i][j]
		
		# set up a cost function that is the sum of both error and number of transitions
		cost = Real('cost', ctx=self.ctx)
		s.add(cost == t_error + ge_error + num_transitions) # previously had gaze and time error in the cost function

		# set up the minimization
		h = s.minimize(cost)
		now = time.time()   # to track the performance of the solver

		print("~~~~~~~~~TIME ANALYSIS~~~~~~~~")
		print("Setting up problem took {} seconds".format(now - then))
		
		# optimize
		with open("constraints.txt", 'w') as outfile:
			outfile.write(str(s))
		return_val = s.check()
		now_now = time.time()

		print("After optimizing, checking took {} seconds".format(now_now - now))

		# if there was a solution
		if return_val == sat:

			s.lower(h)
			m = s.model()
			print(m)
			print("TRANSITION ERRORS~~~~~")
			print("Number of demos included: {}".format(len(demos)))

			# pyt the solution in a Solution object
			if self.forget_thread:
				return None
			solution = self.package_results(m, f_T, f_A, f_ge, t_err, n, demos)

			# set the minimum recursion length
			if len(demos) > self.min_solution_length:
				self.min_solution_length = len(demos)

			print("\nReturning solution")
			print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
			return solution

		# no solution existed given the current set of demos
		# we need to remove a demo and try again
		else:

			final_solution = None

			# only recurse if we are above the minimal length
			# change to >= if we want thoroughness above speed
			# change to > if we want speed above thoroughness
			if len(demos) - 1 > self.min_solution_length:
				solutions = []

				# rearrange the order for randomness (helps with '>')
				# otherwise we can comment this out
				demos_copy = copy.copy(demos)
				shuffle(demos_copy)

				# try every combination of removing a demo
				for demo in demos_copy:
					sliced_demos = copy.copy(demos_copy)
					sliced_demos.remove(demo)
					solutions.append(self.solve_helper(n,sliced_demos))

				# get the best solution to return
				maxlen = 0
				for solution in solutions:
					if solution is not None and len(solution.demos) > maxlen:
						maxlen = len(solution.demos)
						final_solution = solution

			return final_solution

	def compute_transition_constraints(self, demos, f_T, f_A, f_ge, t_err, ge_err, pos_state, n):
		'''
		Here will fill CONS_transitions, which contains all transition constraints

		The input includes (1) the list of demos
						   (2-4) the transition and gesture functions
						   (3-4) the error variables
						   (5) the variables for tracking the number of states
						   (6) the number of allowable states 
		'''

		CONS_transitions = And(True, self.ctx)

		'''
		CONSTRAINT SET:
			Each demonstration must exist as a path through the final interaction.
			We must iterate through each demonstration to create these constraints
		'''
		demo_num = 0
		for demo_object in demos:
			demo_num += 1

			demo = demo_object.demo_array
			print("demo****")
			CONS_demo = And(True, self.ctx)

			# add state variables within the scope of this demo
			print("getting the local vars ready...")
			st = [Int('st_%s_%s' % (str(demo_num),i), ctx=self.ctx) for i in range(len(demo)+2)]
			for state in st:
				CONS_demo = And(CONS_demo, And(state>=0,state<=n, self.ctx), self.ctx)

			print("getting the constraints ready...")
			# iterate through the demonstration
			for i in range(len(demo)):

				# the initial state is a special case
				if i == 0:
					print(" {} ({}) - {} ({}), ".format(demo[0][0].inp, self.sigma[demo[0][0].inp], demo[0][1].output, self.omega[demo[0][1].output]))
					CONS_demo_temp = And(CONS_demo,
									f_T(0,self.sigma[demo[0][0].inp])==(st[1]),
									f_A(0,self.sigma[demo[0][0].inp])==self.omega[demo[0][1].output],
									1 <= st[1],
									st[1] <= n,
									t_err[demo_object][i] == 0, self.ctx)

					# if the above constraint is not satisfied, then we must loosen the constraint and increase the error
					CONS_demo_error = And(False, self.ctx)
					for om in self.omega:
						CONS_demo_error = Or(CONS_demo_error, And(CONS_demo,
											 f_T(0,self.sigma[demo[0][0].inp])==(st[1]),
											 f_A(0,self.sigma[demo[0][0].inp])==self.omega[om],
											 1 <= st[1],
											 st[1] <= n,
											 t_err[demo_object][i] == 100, self.ctx), self.ctx)
					CONS_demo = Or(CONS_demo_temp, CONS_demo_error, self.ctx)

					# if this is the final state in the demonstration, it's outgoing transitions should lead to -1
					if 1 == len(demo):
						for sig in self.sigma:
							CONS_demo = And(CONS_demo, f_T(st[1], self.sigma[sig]) == -1, self.ctx)

				else:
					print(" {} ({}) - {} ({}), ".format(demo[i][0].inp, self.sigma[demo[i][0].inp], demo[i][1].output, self.omega[demo[i][1].output]))
					CONS_demo_temp = And(CONS_demo,
									f_A(st[i],self.sigma[demo[i][0].inp])==self.omega[demo[i][1].output],
									f_T(st[i],self.sigma[demo[i][0].inp])==(st[i+1]),
									#f_T(st[i],self.sigma[demo[i][0]])==st[i+1],
									1 <= st[i],
									st[i] <= n,	
									1 <= st[i+1],
									st[i+1] <= n,
									t_err[demo_object][i] == 0, self.ctx)

					# if the above constraint is not satisfied, then we must increase the error
					CONS_demo_error = And(False, self.ctx)
					for om in self.omega:
						CONS_demo_error = Or(CONS_demo_error, And(CONS_demo,
											 f_A(st[i],self.sigma[demo[i][0].inp])==self.omega[om],
											 f_T(st[i],self.sigma[demo[i][0].inp])==(st[i+1]),
											 1 <= st[i],
											 st[i] <= n,	
											 1 <= st[i+1],
											 st[i+1] <= n,
											 t_err[demo_object][i] == 100, self.ctx), self.ctx)
					CONS_demo = Or(CONS_demo_temp, CONS_demo_error, self.ctx)

					# if this is the final state in the demonstration, it's outgoing transitions should lead to -1
					if i+1 == len(demo):
						for sig in self.sigma:
							CONS_demo = And(CONS_demo, f_T(st[i+1], self.sigma[sig]) == -1, self.ctx)

				# handle the transition error
				CONS_demo = And(CONS_demo, Or(t_err[demo_object][i]>=0,t_err[demo_object][i]<=100, self.ctx), self.ctx)

				# handle the gesture error
				CONS_demo = And(CONS_demo, Or(And(f_ge(st[i+1])==self.gesture[demo[i][1].gesture], ge_err[demo_object][i]==0, self.ctx), 
											  And(f_ge(st[i+1])!=self.gesture[demo[i][1].gesture], If(f_A(st[i] if i > 0 else 0,self.sigma[demo[i][0].inp])==self.omega[demo[i][1].output],
											  													    ge_err[demo_object][i]==1,
											  													    ge_err[demo_object][i]==0), self.ctx), self.ctx), self.ctx)
				CONS_demo = And(CONS_demo, And(ge_err[demo_object][i]>=0,ge_err[demo_object][i]<=1, self.ctx), self.ctx)

			CONS_transitions = And(CONS_transitions, CONS_demo, self.ctx)

		'''
		CONSTRAINT SET: 
			The only transitions leaving the start states are directly from the examples provided
		NOTE: this is slightly more redundant with constraint set #5
		'''
		start_inputs = []
		for demo in demos:
			start_inputs.append(demo.demo_array[0][0].inp)
		for sig in self.sigma:
			if sig not in start_inputs:
				CONS_transitions = And(CONS_transitions,
									   f_T(0,self.sigma[sig])==-1, self.ctx)

		'''
		CONSTRAINT SET:
			no transitions can go back to the start state
		'''
		for inp in range(n+1):
			for sig in self.sigma:
				CONS_transitions = And(CONS_transitions,f_T(inp,self.sigma[sig])!=0, self.ctx)

		'''
		CONSTRAINT SET:
			force outputs leading to a state to be the same (thus, states correspond with the robot's output)
		'''
		'''
		sigmas = list(self.sigma.keys())
		for inp1 in range(n+1):
			for inp2 in range(inp1, n+1):
				for s1 in range(len(sigmas)):
					sig1 = self.sigma[sigmas[s1]]
					for s2 in range(s1, len(sigmas)):
						sig2 = self.sigma[sigmas[s2]]
						CONS_transitions = And(CONS_transitions,
												Implies(f_T(inp1,sig1)==f_T(inp2,sig2),
														f_A(inp1,sig1)==f_A(inp2,sig2)))
		'''
		
		for inp1 in range(n+1):
			for inp2 in range(n+1):
				for sig1 in self.sigma:
					for sig2 in self.sigma:
						CONS_transitions = And(CONS_transitions,
												Implies(f_T(inp1,self.sigma[sig1])==f_T(inp2,self.sigma[sig2]),
														f_A(inp1,self.sigma[sig1])==f_A(inp2,self.sigma[sig2]), self.ctx), self.ctx)
		
		'''
		CONSTRAINT SET: 
			minimize the number of positive transitions
		'''
		for state in range(n+1):
			for sig in self.sigma:
				CONS_transitions = And(CONS_transitions, 
									   Or(And(f_T(state,self.sigma[sig])==-1, pos_state[state][self.sigma[sig]]==0, self.ctx),And(f_T(state,self.sigma[sig])>=0,pos_state[state][self.sigma[sig]]==1, self.ctx), self.ctx), self.ctx
									   )	
				CONS_transitions = And(CONS_transitions,And(pos_state[state][self.sigma[sig]]>=0,pos_state[state][self.sigma[sig]]<=1, self.ctx), self.ctx)		
		
		'''
		CONSTRAINT SET
			the results of f_T should never be below -1 or above n
		'''
		for inp in range(n+1):
			for sig in self.sigma:
				CONS_transitions = And(CONS_transitions, f_T(inp,self.sigma[sig])>=-1, self.ctx)
				CONS_transitions = And(CONS_transitions, f_T(inp,self.sigma[sig])<=n, self.ctx)

		'''
		CONSTRAINT SET
			the results of f_A should never be below 0 or above len(omega)
		'''
		for inp in range(n+1):
			for sig in self.sigma:
				CONS_transitions = And(CONS_transitions, f_A(inp,self.sigma[sig])>=0, self.ctx)
				CONS_transitions = And(CONS_transitions, f_A(inp,self.sigma[sig])<=len(self.omega), self.ctx)

		'''
		CONSTRAINT SET
			the results of f_ge should be bounded
		'''
		for inp in range(n+1):
			CONS_transitions = And(CONS_transitions, f_ge(inp)>=0, self.ctx)
			CONS_transitions = And(CONS_transitions, f_ge(inp)<=len(self.gesture), self.ctx)

		return CONS_transitions

	def package_results(self, m, f_T, f_A, f_ge, t_err, n, demos):
		results = []

		for state in range(0,n+1):
			for inp in self.sigma:
				target = m.evaluate(f_T(state,self.sigma[inp]))
				io = (state, inp, m.evaluate(f_T(state,self.sigma[inp])), m.evaluate(f_A(state,self.sigma[inp])), m.evaluate(f_ge(state)), m.evaluate(f_ge(int(str(target)))))
				results.append(io)

		print(results)

		transition_error = {}
		for i in range(len(demos)):
			demo_object = demos[i]
			transition_error[demo_object] = {}
			demo = demo_object.demo_array

			for j in range(len(demo)):
				transition_error[demo_object][j] = int(str(m.evaluate(t_err[demo_object][j])))

		return Solution(results,demos,transition_error)

	def print_recursion_tracker(self):
		for recur_set in self.recursion_tracker:
			for demo in recur_set:
				print(demo.name, end='')
			print("")

class Solution:

	def __init__(self, results, demos, transition_error):
		self.results = results
		self.demos = demos
		self.transition_error = transition_error

	def get_reachability(self, n):

		output_dict = {}
		#gaze_dict = {0:0}
		gesture_dict = {}
		for i in range(n+1):
			gesture_dict[i] = 0
		for i in range(n+1):
			output_dict[i] = []
		for result in self.results:

			source = int(str(result[0]))
			target = int(str(result[2]))

			if source > -1 and target > -1:
				print(result)

			if source > -1 and source <= n and target > -1 and target <= n:
				if target not in output_dict[source]:
					output_dict[source].append(target)

				#gaze_dict[source] = int(str(result[3]))
				gesture_dict[source] = int(str(result[4]))

				#gaze_dict[target] = int(str(result[5]))
				gesture_dict[target] = int(str(result[5]))

		# st_id -> [outputs], reachable, gaze, gesture
		# if reachable and outputs is empty, then it is a final state
		states = {}
		print("output: {}".format(output_dict))
		print("gesture: {}".format(gesture_dict))
		print("n: {}".format(n))
		for i in range(n+1):
			states[i] = {"outputs": output_dict[i], "reach": False, "gesture": gesture_dict[i]}
		states[0]["reach"] = True

		self.get_reachability_helper(0, output_dict, states)

		return states

	def get_reachability_helper(self, st, output_dict, reach_dict):
		outputs = output_dict[st]

		for output in outputs:
			if reach_dict[output]["reach"] == False:
				reach_dict[output]["reach"] = True
				self.get_reachability_helper(output, output_dict, reach_dict)





