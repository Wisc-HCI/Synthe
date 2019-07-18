from bodystorming_simulation import *
from sat_solver import *
from grapher import *

def main():
	bodystorm = DeliveryDemo()
	bodystorm.run_demos_set1_hardcoded()
	solver = SMTSolver()
	solver.solve(bodystorm, n=9)
	solution = solver.solution
	Grapher().make_graph(solution,bodystorm)

if __name__ == "__main__":
    main()