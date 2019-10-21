import sys

chatitio_file = sys.argv[1]

with open("alphabet_header.txt", "r") as headerfile:

	with open(chatitio_file, "r") as classifications_file:

		with open("../intent_parser/chatito/chatitio_base_microinteractions.txt") as base_classifications_file:

			with open("alphabet.py", "w") as outfile:

				# append the header to the outfile
				for line in headerfile:
					outfile.write(line)

				outfile.write("\nclass Alphabet():\n\n")

				inputs_outputs = []
				for line in base_classifications_file:
					if line[0] == '%':
						inputs_outputs.append(line[2:line.index(']')])
				for line in classifications_file:
					if line[0] == '%':
						inputs_outputs.append(line[2:line.index(']')])

				outfile.write("\t@staticmethod\n\tdef get_inputs():\n\t\treturn [\"Empty\",\n")
				for io in inputs_outputs:
					outfile.write("\"{}\"".format(io))
					if io == inputs_outputs[-1]:
						outfile.write("]\n\n")
					else:
						outfile.write(",\n\t\t\t    ")

				outfile.write("\t@staticmethod\n\tdef get_outputs():\n\t\treturn [\"Empty\",\n")
				for io in inputs_outputs:
					outfile.write("\"{}\"".format(io))
					if io == inputs_outputs[-1]:
						outfile.write("]\n\n")
					else:
						outfile.write(",\n\t\t\t    ")