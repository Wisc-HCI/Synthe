from interaction_driver import InteractionDriver
import os
import socket
import sys
import select
import time

# network stuff
s=socket.socket()
s.connect((sys.argv[1], 8889))

soundfile = 'soundfile.wav'

interaction_id = 0

# DO one of the following:
# 1) if argument 2 exists and the argument is "train", then train a new file
# 2) if argument 2 exists and the argument is "test", then test the file specified
# 2) otherwise if the default directory is empty then exit prematurely
# 3) otherwise (DEBUGGING PURPOSES ONLY), use the most recently-generated file

# if not empty, determine the most recently-created subdirectory
most_recent_model = None
intent_filename = sys.argv[2]

driver = InteractionDriver("169.254.28.227", 9559, interaction_id, 'interaction.xml',
    intent_filename, soundfile, 0.05, s)

if len(sys.argv) > 3 and sys.argv[3] == "test":
    driver.complete_interaction()
    driver.automata.reset()

try:
    while True:
        interaction_id += 1
        #print("Hit enter when you're ready to start the interaction")
        #raw_input()

        # wait for the signal to begin
        print("waiting...")
        ready_to_read, ready_to_write, in_error = select.select([s], [], [], 3600)

        f = open("interaction_test.xml", "wb")
        m = ready_to_read[0].recv(1024)

        data = m
        while "</mma>" not in data:
            m = ready_to_read[0].recv(1024)
            data += m

        f.write(data)
        f.close()

        print("sending ack...")
        ready_to_read, ready_to_write, in_error = select.select([], [s], [])
        ready_to_write[0].sendall(b"ack")

        #exit()
        #try:
        driver = InteractionDriver("169.254.28.227", 9559, interaction_id, 'interaction_test.xml',
            intent_filename, soundfile, 0.005, s)

        driver.complete_interaction()
        driver.automata.reset()
        #except:
        #    print("Robot ran into an error during execution.")

        ready_to_read, ready_to_write, in_error = select.select([], [s], [], 3600)
        ready_to_write[0].send(b"done")

except Exception as e:

    ready_to_read, ready_to_write, in_error = select.select([], [s], [], 3600)
    ready_to_write[0].send(b"error")

    import traceback
    traceback.print_exc()
