from z3 import *
from random import shuffle
from goptimizer import *
import time
import copy
from copy import deepcopy
import faulthandler
import sys
from io_reducer import *

class SMTSolver:
	'''
	Class that contains the solving code
	'''

	def __init__(self, progress_updater, controller, thread_id):
		self.sigma = None
		self.omega = None
		self.gaze = None
		self.gesture = None
		self.solution = None
		self.thread_id = thread_id

		# progress bar stuff, largely unimportant
		self.progress_updater = progress_updater
		self.curr_progress = 20

		# forget the thread
		self.forget_thread = False

		# parent
		self.controller = controller

		# context
		self.ctx = Context()

		# timeout -- after ~a~ solution is found, we'll timeout
		self.timeout_engaged = False
		self.timeout_start_time = None

	def terminate(self):
		print("SAT SOLVER >> forgetting the current thread {}".format(self.thread_id))
		self.forget_thread = True

	def solve(self, bodystorm, n=5):
		faulthandler.enable()
		start_time = time.time()
		'''
		Called externally to generate an automata
		Input: (1) the list of demos (accessible through the bodystorm object)
			   (2) the MAX number of states
		'''

		# for the max sat recursion, this keeps track of the
		# minimal allowable length, and prevents un-needed
		# further recursion
		self.min_solution_length = 0

		# dictionaries of gazes, and gestures that map to their corresponding state ID's
		self.gaze = bodystorm.GAZE_map     # gaze is not part of the model anymore
		self.gesture = bodystorm.GESTURE_map

		# FOR DEBUGGING: store info about each recursion call
		self.recursion_tracker = []

		print("SAT SOLVER >> Finding automata with max n={} (thread_id = {})".format(n, self.thread_id))

		# some demonstrations have been 'disabled' by participants
		active_demos = bodystorm.get_active_demos()
		self.sigma = bodystorm.get_used_sigmas(active_demos)
		self.sigma_rev = {v: k for k, v in self.sigma.items()}
		self.omega = bodystorm.get_used_omegas(active_demos, n=n)
		self.omega_rev = {v: k for k, v in self.omega.items()}
		self.actual_omega = bodystorm.OMEGA_map

		print("SAT SOLVER >> beginning presolve 2 with demos (thread_id = {}): ".format(self.thread_id))
		for demo in active_demos:
			print(demo.pretty_string())
		print("SAT SOLVER >> beginning presolve 2 with omega (thread_id = {}): ".format(self.thread_id))
		print(self.omega)

		# pre-solve to get a list of demos to inpt into the solve_helper
		if not self.forget_thread and not self.thread_id == -1:
			self.progress_updater.emit(20,"constructing interaction")
		elif not self.thread_id == -1:
			return
		enabled_demos = self.pre_solve(n, copy.copy(active_demos))
		if enabled_demos is None:
			return
		else:
			pass
			#print(active_demos)
			#print(enabled_demos)

		# solve
		self.ctx = Context()
		self.min_solution_length = 0
		initial_inc = 100
		initial_threshold = 0
		for demo in enabled_demos:
			initial_threshold += len(demo)*10
		initial_threshold = int(math.ceil(initial_threshold*1.0/initial_inc))*initial_inc
		print("SAT SOLVER >> initial threshold is {} (thread_id = {})".format(initial_threshold, self.thread_id))
		print("SAT SOLVER >> beginning presolve 2 with demos (thread_id = {}): ".format(self.thread_id))
		for demo in enabled_demos:
			print(demo.pretty_string())
		print("SAT SOLVER >> beginning presolve 2 with omega (thread_id = {}): ".format(self.thread_id))
		print(self.omega)

		#gpy = GOptimizer()
		#self.solution = gpy.solve(n, self.sigma, self.omega, enabled_demos)
		#exit()

		# second presolve to reduce the variation of inputs and outputs
		# store each copy and its corresponding actual demo in a dictionary
		copied2actual_demos = {}
		if not self.forget_thread and not self.thread_id == -1:
			self.progress_updater.emit(40,"constructing interaction")
		elif not self.thread_id == -1:
			return
		io_reducer = IOReducer(n,enabled_demos, self.omega, bodystorm.design, self.ctx)
		relaxed_enabled_demos = deepcopy(io_reducer.solve())
		#io_reducer.init_relaxed_outputs()
		#relaxed_enabled_demos = deepcopy(enabled_demos)

		for i in range(len(relaxed_enabled_demos)):
			copied_demo = relaxed_enabled_demos[i]
			actual_demo = enabled_demos[i]
			copied2actual_demos[copied_demo] = actual_demo

		# reduce enabled demos once again
		print(self.omega)
		self.omega = bodystorm.get_used_omegas(active_demos, n=n, relaxed=True)
		print(self.omega)
		self.omega_rev = {v: k for k, v in self.omega.items()}

		# finally, solve
		self.curr_progress = 60
		self.solution = self.solve_helper(n, relaxed_enabled_demos, low=0, thresh=initial_threshold, point=0, inc=initial_inc)

		# if there is a solution,
		if self.forget_thread:
			return
		if self.solution is not None:

			# post-process the solution. This means replacing the copy of each demos object with the actual demos object
			self.solution.demos = enabled_demos
			actual_transition_error = {}
			for demo_obj in copied2actual_demos:
				actual_demo_obj = copied2actual_demos[demo_obj]
				actual_transition_error[actual_demo_obj] = {}
				for i in range(len(demo_obj.demo_array)):
					actual_transition_error[actual_demo_obj][i] = self.solution.transition_error[demo_obj][i]
			self.solution.transition_error = actual_transition_error

			# update the status of active vs. non-active demos
			satisfied_demos = self.solution.demos
			for demo in active_demos:
				if demo not in satisfied_demos:
					demo.setActivated(False)

		# DEBUG the recursive process
		#if self.solution is not None:
		#	for result in self.solution.results:
		#		print(result)
		# self.print_recursion_tracker()

		# in the UI, update the progress bar to 90%
		if not self.forget_thread and not self.thread_id == -1:
			self.progress_updater.emit(90,"finalized interaction")

		end_time = time.time()

		print("SAT SOLVER >> Entire solve process took {} seconds (thread_id = {})".format(end_time - start_time, self.thread_id))
		self.timeout_engaged = False
		self.solution.time = end_time - start_time

	def pre_solve(self, n, demos):
		'''
		recursive method for quickly finding a set of demos that can satisfy the main constraitns

		Input: (1) MAX number of states
			   (2) the list of demos
		'''

		sys.stdout.write("presolve with {} demonstrations ... (thread_id = {})".format(len(demos), self.thread_id))

		# track the time it takes to solve
		then = time.time()

		# in the UI, update the progress bar
		self.increment_progress_bar()

		# add to the recursion tracker
		self.recursion_tracker.append(set(demos))

		# base cases
		if self.solution is not None and len(self.solution.demos) > len(demos):
			print("SAT SOLVER >> Returning, as there exists a better solution impossible to achieve with the current set of demos. (thread_id = {})".format(self.thread_id))
			return None
		elif len(demos) == 0:
			print("SAT SOLVER >> 0 demos provided. (thread_id = {})".format(self.thread_id))
			return None

		'''FUNCTIONS'''
		# f_T: SxA->S mapping of states and inputs to states
		f_T = Function('f_T_pre', IntSort(ctx=self.ctx), IntSort(ctx=self.ctx), IntSort(ctx=self.ctx))

		# f_A: SxA->A mapping of states and inputs to outputs
		f_A = Function('f_A_pre', IntSort(ctx=self.ctx), IntSort(ctx=self.ctx), IntSort(ctx=self.ctx))

		# compute pre-solve constraints
		CONS_presolve = self.compute_presolve_constraints(demos, f_T, f_A, n)

		# set up the optimization problem
		#z3.set_param("auto_config", "false")
		s = Solver(ctx=self.ctx)
		s.add(CONS_presolve)
		now = time.time()
		sys.stdout.write("SAT SOLVER >> set up in {} seconds ... (thread_id = {})".format(round(((now - then)*10.0))/10.0, self.thread_id))

		return_val = s.check()
		now_now = time.time()
		print( "SAT SOLVER >> finished in {} additional seconds. (thread_id = {})".format(round(((now_now - then)*10.0))/10.0, self.thread_id))

		# if there was a solution
		if return_val == sat:

			m = s.model()

			# pyt the solution in a Solution object
			if self.forget_thread:
				return None
			enabled_demos = demos

			# set the minimum recursion length
			if len(demos) > self.min_solution_length:
				self.min_solution_length = len(demos)

			print("SAT SOLVER >>    -> is solvable (thread_id = {})".format(self.thread_id))
			return demos

		# no solution existed given the current set of demos
		# we need to remove a demo and try again
		else:

			enabled_demos = None

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
					new_solution = self.pre_solve(n,sliced_demos)
					solutions.append(new_solution)
					if new_solution is not None and len(sliced_demos) <= self.min_solution_length:
						break


				# get the best solution to return
				maxlen = 0
				for dm in solutions:
					if dm is not None and len(dm) > maxlen:
						maxlen = len(dm)
						enabled_demos = dm

			return enabled_demos

	def solve_helper(self, n, demos, low, thresh, point, inc, best_solution=(None,-1)):
		'''
		Recursive method for generating automata

		Input: (1) MAX number of states
			   (2) the list of demos
		'''

		print("SAT SOLVER >> checking point {}, low {}, threshold {}, inc {} (thread_id = {})".format(point, low, thresh, inc, self.thread_id))

		# return the best solution if this iteration is redundant
		if best_solution[0] is not None and (best_solution[1] > -1 and best_solution[1] <= point):
			print("SAT SOLVER >>    SOLVED: returning existing solution (thread_id = {})".format(self.thread_id))
			return best_solution[0]

		# track the time it takes to solve
		then = time.time()

		# in the UI, update the progress bar
		self.increment_progress_bar()

		# add to the recursion tracker
		self.recursion_tracker.append(set(demos))

		# base cases
		if self.solution is not None and len(self.solution.demos) > len(demos):
			print("SAT SOLVER >> Returning, as there exists a better solution impossible to achieve with the current set of demos. (thread_id = {})".format(self.thread_id))
			return None
		elif len(demos) == 0:
			print("SAT SOLVER >> 0 demos provided. (thread_id = {})".format(self.thread_id))
			return None

		'''FUNCTIONS'''
		# f_T: SxA->S mapping of states and inputs to states
		f_T = Function('f_T', BitVecSort(11,ctx=self.ctx), BitVecSort(11,ctx=self.ctx), BitVecSort(11,ctx=self.ctx))

		# f_A: SxA->A mapping of states and inputs to outputs
		f_A = Function('f_A', BitVecSort(11,ctx=self.ctx), BitVecSort(11,ctx=self.ctx), BitVecSort(11,ctx=self.ctx))

		# f_ge: SxA->Ga mapping of states to gestures
		f_ge = Function('f_ge', BitVecSort(11,ctx=self.ctx), BitVecSort(11,ctx=self.ctx), BitVecSort(11,ctx=self.ctx))

		'''ERROR VARIABLES'''
		# transition error
		t_err = {}
		for i in range(len(demos)):
			demo_object = demos[i]
			t_err[demo_object] = {}
			demo = demo_object.demo_array

			for j in range(len(demo)):
				#print('t_err_%s_%s' % (i,j))
				#t_err[demo_object][j] = Int('t_err_%s_%s' % (i,j), ctx=self.ctx)
				t_err[demo_object][j] = BitVec('t_err_%s_%s' % (i,j), 11, ctx=self.ctx)

		# gesture error
		ge_err = {}
		for i in range(len(demos)):
			demo_object = demos[i]
			ge_err[demo_object] = {}
			demo = demo_object.demo_array

			for j in range(len(demo)):
				ge_err[demo_object][j] = BitVec('ge_err_%s_%s' % (i,j), 11, ctx=self.ctx)

		'''OTHER VARIABLES'''
		# track the number of transitions
		'''
		pos_state = {}
		for i in range(n+1):
			pos_state[i] = {}
			for j in range(len(self.sigma)):
				pos_state[i][j] = Int('pos_state_{}_{}'.format(i,j), ctx=self.ctx)
		'''

		# get the transition 'CONS'traints
		#print("setting up constraints")
		#CONS_transitions = self.compute_transition_constraints(demos, f_T, f_A, f_ge, t_err, ge_err, pos_state, n)
		CONS_transitions, demo2states = self.compute_transition_constraints(demos, f_T, f_A, f_ge, t_err, ge_err, n)

		# set up the optimization problem
		#z3.set_param("auto_config", "false")
		s = Solver(ctx=self.ctx)

		# set the timeout
		if self.timeout_engaged == False and best_solution[0] is not None:
			print("SAT SOLVER >> engaging timeout (thread_id = {})".format(self.thread_id))
			self.timeout_engaged = True
			self.timeout_start_time = time.time()

		if self.timeout_engaged:
			timeout_curr_time = time.time()
			elapsed = int(round((timeout_curr_time - self.timeout_start_time)*1000))
			time_left = 180000 - elapsed
			print("SAT SOLVER >> timeout is {} milliseconds (thread_id = {})".format(time_left, self.thread_id))
			if time_left < 0:
				print("SAT SOLVER >> Engaging timeout")
				return best_solution[0]
			s.set("timeout", time_left)
		#s.set("timeout", 10)
		#set_option(timeout=60000)
		s.add(CONS_transitions)

		# sum up the transition error
		#t_error = BitVec("t_err_sum", 5, ctx=self.ctx)
		#error_sum = []
		#for demo_obj in t_err:
		#	for i in t_err[demo_obj]:
		#		error_sum.append(t_err[demo_obj][i])
		#s.add(t_error==Sum(error_sum))
		t_error = 0
		for demo_obj in t_err:
			for i in t_err[demo_obj]:
				t_error += t_err[demo_obj][i]

		# sum up the gesture error
		#ge_error = 0
		for demo_obj in ge_err:
			for i in ge_err[demo_obj]:
				t_error += ge_err[demo_obj][i]

		# sum up the number of transitions
		'''
		num_transitions = 0
		for i in range(n+1):
			for j in range(len(self.sigma)):
				num_transitions += pos_state[i][j]
		'''

		# set up a cost function that is the sum of both error and number of transitions
		#cost = Real('cost', ctx=self.ctx)
		#s.add(cost == t_error + ge_error + num_transitions) # previously had gaze and time error in the cost function
		point_bv = BitVecVal(point, 11, ctx=self.ctx)
		s.add(point_bv >= t_error) # previously had gaze and time error in the cost function

		# set up the minimization
		#h = s.minimize(cost)
		now = time.time()   # to track the performance of the solver

		#print("~~~~~~~~~TIME ANALYSIS~~~~~~~~")
		print("SAT SOLVER >>    setting up problem took {} seconds (thread_id = {})".format(now - then, self.thread_id))

		# optimize
		with open("constraints.txt", 'w') as outfile:
			outfile.write(str(s))
		return_val = s.check()
		now_now = time.time()

		print("SAT SOLVER >>    after optimizing, checking took {} seconds (thread_id = {})".format(now_now - now, self.thread_id))

		def update_best_solution(best_solution):
			m = s.model()
			solution = self.package_results(m, f_T, f_A, f_ge, t_err, n, demos, demo2states)
			if point <= best_solution[1] or best_solution[1] == -1:
				best_solution = (solution,point)
			return best_solution

		# if there was a solution, and we know the precise error
		if return_val == sat and (point==0 or (point<=low+inc and inc == 1)):

			print("SAT SOLVER >>    SOLVED: found final solution with error {} (thread_id = {})".format(point, self.thread_id))
			#s.lower(h)
			m = s.model()
			#print(m)
			#print("TRANSITION ERRORS~~~~~")
			#print("Number of demos included: {}".format(len(demos)))

			# pyt the solution in a Solution object
			if self.forget_thread:
				return None
			solution = self.package_results(m, f_T, f_A, f_ge, t_err, n, demos, demo2states)

			# set the minimum recursion length
			if len(demos) > self.min_solution_length:
				self.min_solution_length = len(demos)

			#print("\nReturning solution")
			#print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
			return solution

		# if a solution exists, but we must hone in on the precise error
		elif return_val == sat and point<=low+inc:
			print("SAT SOLVER >>    FOUND final solution with inc={}, increasing precision (thread_id = {})".format(inc, self.thread_id))
			if self.forget_thread:
				return None
			best_solution = update_best_solution(best_solution)
			return self.solve_helper(n, demos, low=low, thresh=point, point=int(round(low + (point-low)/2)), inc=inc/10, best_solution=best_solution)

		elif return_val == sat:
			print("SAT SOLVER >>    FOUND a solution with inc={}, modifying upper bound (thread_id = {})".format(inc, self.thread_id))
			if self.forget_thread:
				return None
			best_solution = update_best_solution(best_solution)
			return self.solve_helper(n, demos, low=low, thresh=point, point=int(round(low + (point-low)/2)), inc=inc, best_solution=best_solution)

		# no solution existed given the current set of demos
		# we need to remove a demo and try again
		else:
			#print("did not find solution ... and there are {} demos left".format(len(demos)))
			#print("forget_thread is {}".format(self.forget_thread))
			#print("demos: {}".format(demos))
			if self.forget_thread:
				return None
			new_point = int(round(point + (thresh-point)/2))
			new_point = new_point if new_point > point else point+1
			return self.solve_helper(n, demos, low=point, thresh=thresh, point=new_point, inc=inc, best_solution=best_solution)

	def compute_presolve_constraints(self, demos, f_T, f_A, n):
		'''
		Here will fill CONS_transitions, which contains all transition constraints

		The input includes (1) the list of demos
						   (2-4) the transition and gesture functions
						   (3-4) the error variables
						   (5) the variables for tracking the number of states
						   (6) the number of allowable states
		'''

		CONS_presolve = And(True, self.ctx)

		'''
		CONSTRAINT SET:
			Each demonstration must exist as a path through the final interaction.
			We must iterate through each demonstration to create these constraints
		'''
		demo_num = 0
		for demo_object in demos:
			demo_num += 1

			demo = demo_object.demo_array
			CONS_demo = And(True, self.ctx)

			# add state variables within the scope of this demo
			st = [Int('st_%s_%s_pre' % (str(demo_num),i), ctx=self.ctx) for i in range(len(demo)+2)]
			for state in st:
				CONS_demo = And(CONS_demo, And(state>=1,state<=n, self.ctx), self.ctx)

			# iterate through the demonstration
			for i in range(len(demo)):

				# the initial state is a special case
				if i == 0:
					CONS_demo_error = And(False, self.ctx)
					for om in self.omega:
						CONS_demo_error = Or(CONS_demo_error, And(
											 f_T(0,self.sigma[demo[0][0].inp])==(st[1]),
											 f_A(0,self.sigma[demo[0][0].inp])==self.omega[om],
											 self.ctx), self.ctx)
					CONS_demo = And(CONS_demo, CONS_demo_error, self.ctx)

					# if this is the final state in the demonstration, it's outgoing transitions should lead to -1
					if 1 == len(demo):
						for sig in self.sigma:
							CONS_demo = And(CONS_demo, f_T(st[1], self.sigma[sig]) == -1, self.ctx)

				else:

					# if the above constraint is not satisfied, then we must increase the error
					CONS_demo_error = And(False, self.ctx)
					for om in self.omega:
						CONS_demo_error = Or(CONS_demo_error, And(
											 f_A(st[i],self.sigma[demo[i][0].inp])==self.omega[om],
											 f_T(st[i],self.sigma[demo[i][0].inp])==(st[i+1]),
											 self.ctx), self.ctx)
					CONS_demo = And(CONS_demo, CONS_demo_error, self.ctx)

					# if this is the final state in the demonstration, it's outgoing transitions should lead to -1
					if i+1 == len(demo):
						for sig in self.sigma:
							CONS_demo = And(CONS_demo, f_T(st[i+1], self.sigma[sig]) == -1, self.ctx)

			CONS_presolve = And(CONS_presolve, CONS_demo, self.ctx)

		#CONS_presolve = And(CONS_presolve, self.start_state_constraints(demos, f_T), self.ctx)
		CONS_presolve = And(CONS_presolve, self.start_state_return(f_T, n), self.ctx)
		#CONS_presolve = And(CONS_presolve, self.make_moore_machine(f_T, f_A, n), self.ctx)
		#CONS_presolve = And(CONS_presolve, self.constrain_functions(f_T, f_A, n), self.ctx)

		return CONS_presolve

	def compute_transition_constraints(self, demos, f_T, f_A, f_ge, t_err, ge_err, n):
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
		demo2states = {}
		for demo_object in demos:
			demo_num += 1

			demo = demo_object.demo_array
			#print("demo****")
			CONS_demo = And(True, self.ctx)

			# add state variables within the scope of this demo
			st = [BitVec('st_%s_%s' % (str(demo_num),i), 11, ctx=self.ctx) for i in range(len(demo)+2)]
			for state in st:
				CONS_demo = And(CONS_demo, And(state>=1,state<=n, self.ctx), self.ctx)
			demo2states[demo_object] = st

			# iterate through the demonstration
			for i in range(len(demo)):

				# the initial state is a special case
				if i == 0:
					CONS_demo = And(CONS_demo, f_T(0,self.sigma[demo[0][0].inp])==(st[1]), self.ctx)
					#print(" {} ({}) - {} ({}), ".format(demo[0][0].inp, self.sigma[demo[0][0].inp], demo[0][1].output, self.omega[demo[0][1].output]))
					#print(demo[0][1].relaxed_output)
					CONS_demo_temp = And(CONS_demo,
									f_A(0,self.sigma[demo[0][0].inp])==self.omega[demo[0][1].relaxed_output],
									t_err[demo_object][i] == 0, self.ctx)

					# if the above constraint is not satisfied, then we must loosen the constraint and increase the error
					CONS_demo_error = And(CONS_demo, t_err[demo_object][i] == 10, self.ctx)
					CONS_demo = Or(CONS_demo_temp, CONS_demo_error, self.ctx)

					# if this is the final state in the demonstration, it's outgoing transitions should lead to -1
					if 1 == len(demo):
						for sig in self.sigma:
							CONS_demo = And(CONS_demo, f_T(st[1], self.sigma[sig]) == -1, self.ctx)

				else:
					CONS_demo = And(CONS_demo, f_T(st[i],self.sigma[demo[i][0].inp])==(st[i+1]), self.ctx)
					#print(" {} ({}) - {} ({}), ".format(demo[i][0].inp, self.sigma[demo[i][0].inp], demo[i][1].output, self.omega[demo[i][1].output]))
					CONS_demo_temp = And(CONS_demo,
									f_A(st[i],self.sigma[demo[i][0].inp])==self.omega[demo[i][1].relaxed_output],
									t_err[demo_object][i] == 0, self.ctx)

					# if the above constraint is not satisfied, then we must increase the error
					CONS_demo_error = And(CONS_demo, t_err[demo_object][i] == 10, self.ctx)
					CONS_demo = Or(CONS_demo_temp, CONS_demo_error, self.ctx)

					# if this is the final state in the demonstration, it's outgoing transitions should lead to -1
					if i+1 == len(demo):
						for sig in self.sigma:
							CONS_demo = And(CONS_demo, f_T(st[i+1], self.sigma[sig]) == -1, self.ctx)

				# handle the transition error
				CONS_demo = And(CONS_demo, And(t_err[demo_object][i]>=0,t_err[demo_object][i]<=10, self.ctx), self.ctx)

				# NOTE: COMMENT OUT IF DON"T WANT GESTURES #
				# handle the gesture error
				CONS_demo = And(CONS_demo, Or(And(f_ge(st[i] if i > 0 else 0,self.sigma[demo[i][0].inp])==self.gesture[demo[i][1].gesture], ge_err[demo_object][i]==0, self.ctx),
											  And(f_ge(st[i] if i > 0 else 0,self.sigma[demo[i][0].inp])!=self.gesture[demo[i][1].gesture], If(f_A(st[i] if i > 0 else 0,self.sigma[demo[i][0].inp])==self.omega[demo[i][1].relaxed_output],
											  													    ge_err[demo_object][i]==1,
											  													    ge_err[demo_object][i]==0), self.ctx), self.ctx), self.ctx)
				CONS_demo = And(CONS_demo, And(ge_err[demo_object][i]>=0,ge_err[demo_object][i]<=1, self.ctx), self.ctx)
				# NOTE: END COMMENT OUT #

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
			restrict any pair that doesn't appear in the demos from entering
		'''
		'''
		for sig in self.sigma:
			for om in self.omega:
				exists = False
				for demo_object in demos:
					demo = demo_object.demo_array
					for pair in demo:
						if sig == pair[0].inp and om == pair[1].output:
							exists = True
				if not exists:
					for state in range(n+1):
						CONS_transitions = And(CONS_transitions, f_A(state,self.sigma[sig]) != self.omega[om], self.ctx)
				else:
					print("{} AND {} DO EXIST TOGETHER".format(sig, om))
		'''

		'''
		CONSTRAINT SET:
			force outputs leading to a state to be the same (thus, states correspond with the robot's output)
		'''
		# first enumerate all possible combinations of inputs and sigmas
		'''
		combos = []
		sigmas = list(self.sigma.keys())
		for inp in range(n+1):
			for sig in sigmas:
				combos.append((inp,sig))

		for i in range(len(combos)):
			for j in range(i, len(combos)):
				inp1 = combos[i][0]
				sig1 = self.sigma[combos[i][1]]
				inp2 = combos[j][0]
				sig2 = self.sigma[combos[j][1]]
				CONS_transitions = And(CONS_transitions,
									   Implies(f_T(inp1,sig1)==f_T(inp2,sig2),
											   f_A(inp1,sig1)==f_A(inp2,sig2),self.ctx),self.ctx)
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
														f_A(inp1,sig1)==f_A(inp2,sig2),self.ctx),self.ctx)

		for inp1 in range(n+1):
			for inp2 in range(n+1):
				for sig1 in self.sigma:
					for sig2 in self.sigma:
						CONS_transitions = And(CONS_transitions,
												Implies(f_T(inp1,self.sigma[sig1])==f_T(inp2,self.sigma[sig2]),
														f_A(inp1,self.sigma[sig1])==f_A(inp2,self.sigma[sig2]), self.ctx), self.ctx)
		'''
		'''
		CONSTRAINT SET:
			minimize the number of positive transitions
		'''
		'''
		for state in range(n+1):
			for sig in self.sigma:
				CONS_transitions = And(CONS_transitions,
									   Or(And(f_T(state,self.sigma[sig])==-1, pos_state[state][self.sigma[sig]]==0, self.ctx),And(f_T(state,self.sigma[sig])>=0,pos_state[state][self.sigma[sig]]==1, self.ctx), self.ctx), self.ctx
									   )
				CONS_transitions = And(CONS_transitions,And(pos_state[state][self.sigma[sig]]>=0,pos_state[state][self.sigma[sig]]<=1, self.ctx), self.ctx)
		'''

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
				CONS_transitions = And(CONS_transitions, f_A(inp,self.sigma[sig])<len(self.omega), self.ctx)

		'''
		CONSTRAINT SET
			the results of f_g should never be below 0 or above len(gestures)
		'''
		for inp in range(n+1):
			for sig in self.sigma:
				CONS_transitions = And(CONS_transitions, f_ge(inp,self.sigma[sig])>=0, self.ctx)
				CONS_transitions = And(CONS_transitions, f_ge(inp,self.sigma[sig])<len(self.gesture), self.ctx)

		'''
		CONSTRAINT SET
			the results of f_ge should be bounded
		'''
		#for inp in range(n+1):
		#	CONS_transitions = And(CONS_transitions, f_ge(inp)>=0, self.ctx)
		#	CONS_transitions = And(CONS_transitions, f_ge(inp)<len(self.gesture), self.ctx)

		return CONS_transitions, demo2states

	def start_state_constraints(self, demos, f_T):
		'''
		CONSTRAINT SET:
			The only transitions leaving the start states are directly from the examples provided
		NOTE: this is slightly more redundant with constraint set #5
		'''
		CONS = And(True, self.ctx)
		start_inputs = []
		for demo in demos:
			start_inputs.append(demo.demo_array[0][0].inp)
		for sig in self.sigma:
			if sig not in start_inputs:
				CONS = And(CONS, f_T(0,self.sigma[sig])==-1, self.ctx)

		return CONS

	def start_state_return(self, f_T, n):
		'''
		CONSTRAINT SET:
			no transitions can go back to the start state
		'''
		CONS = And(True, self.ctx)
		for inp in range(n+1):
			for sig in self.sigma:
				CONS = And(CONS,f_T(inp,self.sigma[sig])!=0, self.ctx)
		return CONS

	def make_moore_machine(self, f_T, f_A, n):
		CONS = And(True, self.ctx)
		for inp1 in range(n+1):
			for inp2 in range(n+1):
				for sig1 in self.sigma:
					for sig2 in self.sigma:
						CONS = And(CONS,
									Implies(f_T(inp1,self.sigma[sig1])==f_T(inp2,self.sigma[sig2]),
											f_A(inp1,self.sigma[sig1])==f_A(inp2,self.sigma[sig2]), self.ctx), self.ctx)
		return CONS

	def constrain_functions(self, f_T, f_A, n):
		'''
		CONSTRAINT SET
			the results of f_T should never be below -1 or above n
		'''
		CONS = And(True, self.ctx)
		for inp in range(n+1):
			for sig in self.sigma:
				CONS = And(CONS, f_T(inp,self.sigma[sig])>=-1, self.ctx)
				CONS = And(CONS, f_T(inp,self.sigma[sig])<=n, self.ctx)

		'''
		CONSTRAINT SET
			the results of f_A should never be below 0 or above len(omega)
		'''
		for inp in range(n+1):
			for sig in self.sigma:
				CONS = And(CONS, f_A(inp,self.sigma[sig])>=0, self.ctx)
				CONS = And(CONS, f_A(inp,self.sigma[sig])<len(self.omega), self.ctx)

		return CONS

	def package_results(self, m, f_T, f_A, f_g, t_err, n, demos, demo2states):
		results = []
		gesture_map = {}

		for state in range(0,n+1):
			for inp in self.sigma:
				target = m.evaluate(f_T(state,self.sigma[inp]))
				target_output = m.evaluate(f_A(state,self.sigma[inp]))

				'''
				print("\n**\nITR\n**")
				print(state)
				print(inp)
				print("**")
				print(self.omega)
				print(self.omega_rev)
				print(target_output)
				'''

				mapped_omega = self.omega_rev[int(str(target_output))]   # string
				#print(mapped_omega)
				omega = self.actual_omega[mapped_omega]  # int

				io = (state, inp, target, omega)
				gesture_map[(int(str(state)),str(inp), int(str(target)), int(str(omega)))] = m.evaluate(f_g(state,self.sigma[inp]))
				results.append(io)

		# remove transitions that did not appear in the demos
		results = self.post_process_pruning(results, demo2states, m, f_T)

		# add in the transition error from the main solver
		transition_error = {}
		for i in range(len(demos)):
			demo_object = demos[i]
			transition_error[demo_object] = {}
			demo = demo_object.demo_array

			for j in range(len(demo)):
				transition_error[demo_object][j] = int(str(m.evaluate(t_err[demo_object][j])))

		# account for transition error from the pre-solve
		for demo_object in demos:
			demo_array = demo_object.demo_array
			for i in range(len(demo_array)):
				if demo_array[i][1].output != demo_array[i][1].relaxed_output:
					transition_error[demo_object][i] = 10

		return Solution(results,demos,transition_error,n,gesture_map=gesture_map)

	def post_process_pruning(self, results, demo2states, m, f_T):

		# loop through each result, potentially eliminating some
		for_removal = []
		for result in results:

			# get the source state and the target state
			st_1 = result[0]
			inp = result[1]
			st_2 = int(str(result[2]))

			# loop through the states in each demonstration
			exists = False
			for demo_obj in demo2states:
				states = demo2states[demo_obj]

				for i in range(len(demo_obj.demo_array)):
					# access the source and target states
					if i == 0:
						source_st = 0
					else:
						source_st = int(str(m.evaluate(states[i])))
					target_st = int(str(m.evaluate(states[i + 1])))
					demo_inp = demo_obj.demo_array[i][0].inp

					# check whether the states match
					if st_1 == source_st and st_2 == target_st and demo_inp==inp:
						exists = True
						break

				if exists:
					break

			if not exists:
				for_removal.append(result)

		for item in for_removal:
			results.remove(item)

		return results



	def print_recursion_tracker(self):
		for recur_set in self.recursion_tracker:
			for demo in recur_set:
				print(demo.name, end='')
			print("")

	def increment_progress_bar(self):
		# in the UI, update the progress bar
		if not self.forget_thread and not self.thread_id == -1:
			self.progress_updater.emit(self.curr_progress,"constructing interaction")
		self.curr_progress = self.curr_progress + 1 if self.curr_progress < 90 else 90

class Solution:

	def __init__(self, results, demos, transition_error, n, gesture_map={}):
		self.results = results
		self.demos = demos
		self.transition_error = transition_error
		self.n = n
		self.gesture_map = gesture_map
		self.speech_map = {}
		self.time = -100000

	def compute_speech_map(self, bodystorm, demos=None):

		output_map = {}
		for res in self.results:
			output_map[(int(str(res[0])),str(res[1]))] = bodystorm.OMEGA_map_rev[int(str(res[3]))]

		self.speech_map = {}

		if demos is None:
			demos = self.demos

		for demo_obj in demos:
			demo_arr = demo_obj.demo_array

			curr = 0

			for i in range(len(demo_arr)):
				inp = demo_arr[i][0].inp

				if curr not in self.speech_map:
					self.speech_map[curr] = {}
				if inp not in self.speech_map[curr]:
					self.speech_map[curr][inp] = []

				# check if the output matches the demo output
				if (curr,inp) in output_map and output_map[(curr,inp)] == demo_arr[i][1].output:
					self.speech_map[curr][inp].append(demo_arr[i][1].speech)

				# find the appropriate next state
				for edge in self.results:
					if int(str(edge[0])) == curr and str(edge[1]) == inp:
						curr = int(str(edge[2]))
						break

		'''
		print("KEYS")
		for res in self.results:
			if (int(str(res[0])),str(res[1])) in output_map:
				print((int(str(res[0])),str(res[1])))
				print(output_map[(int(str(res[0])),str(res[1]))])

		for curr in self.speech_map:
			for inp in self.speech_map[curr]:
				print("{}, {}".format(curr,inp))
				print(self.speech_map[curr][inp])
		'''

	def get_reachability(self, bodystorm):
		n = self.n
		# get the gaze/gesture votes
		'''
		votes = {}
		for omega in bodystorm.OMEGA_map:
			votes[omega] = {}
			for gesture in bodystorm.GESTURE_map:
				votes[omega][gesture] = 0
		for demo in self.demos:
			for item in demo.demo_array:
				output = item[1].output
				gesture = item[1].gesture

				votes[output][gesture] += 1

		output_dict = {}
		#gaze_dict = {0:0}
		gesture_dict = {}
		for omega in bodystorm.OMEGA_map:
			gesture_dict[omega] = max(votes[omega], key=lambda key: votes[omega][key])
		'''
		output_dict = {}
		for i in range(n+1):
			output_dict[i] = []
		for result in self.results:

			source = int(str(result[0]))
			target = int(str(result[2]))

			#if source > -1 and target > -1:
			#	print(result)

			if source > -1 and source <= n and target > -1 and target <= n:
				if target not in output_dict[source]:
					output_dict[source].append(target)

				#source_name = bodystorm.OMEGA_map_rev[source]
				target_name = bodystorm.OMEGA_map_rev[int(str(result[3]))]
				#print(target_name)
				#print(votes[target_name])

				#gaze_dict[source] = int(str(result[3]))
				#gesture_dict[source] = max(votes[source_name], key=lambda key: votes[source_name][key])
				#print(source)
				#print(source_name)
				#print(gesture_dict[source])
				#print(votes[source_name])

				#gaze_dict[target] = int(str(result[5]))
				#print(gesture_dict[target])
		#print(bodystorm.OMEGA_map)

		# st_id -> [outputs], reachable, gaze, gesture
		# if reachable and outputs is empty, then it is a final state
		states = {}
		#print("votes: {}".format(votes))
		#print("output: {}".format(output_dict))
		#print("gesture: {}".format(gesture_dict))
		#print("n: {}".format(n))
		for i in range(n+1):
			states[i] = {"outputs": output_dict[i], "reach": False}
		states[0]["reach"] = True

		self.get_reachability_helper(0, output_dict, states)

		return states, {}

	def get_reachability_helper(self, st, output_dict, reach_dict):
		outputs = output_dict[st]

		for output in outputs:
			if reach_dict[output]["reach"] == False:
				reach_dict[output]["reach"] = True
				self.get_reachability_helper(output, output_dict, reach_dict)
