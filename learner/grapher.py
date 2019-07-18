from graphviz import Digraph

class Grapher:

	def make_mealy(self, edges, bodystorm):
		g = Digraph('G', filename='mealy', format='png')

		for edge in edges:
			if str(edge[2]) != '-1':
				g.edge(str(edge[0]), str(edge[2]), label="{}-{}/{}-{}".format(edge[1], edge[0], bodystorm.OMEGA_map_rev[int(str(edge[3]))], edge[2]))

		g.render()

	def make_regular(self, edges, bodystorm):

		g = Digraph('G', filename='graph', format='png')

		id2name = {}
		for edge in edges:
			id2name[str(edge[2])] = bodystorm.OMEGA_map_rev[int(str(edge[3]))]

		for edge in edges:
			if str(edge[2]) != '-1':
				g.edge(id2name[str(edge[0])] if str(edge[0]) in id2name else "Start", bodystorm.OMEGA_map_rev[int(str(edge[3]))], label="{}".format(edge[1]))

		g.render()