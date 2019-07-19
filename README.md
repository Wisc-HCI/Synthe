# Synthé

Synthé is atool that allows designers of human-robot interactions to bodystorm their interactions. In the bodystorming process, a design team acts out an exampleinteraction between a human and a robot, where one user plays the human and another plays the robot. Synthé records the speech and getures of the designers, and synthesizes an executable human-robot interaction program, which can be simulated on a robot. 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 

### Prerequisites

To run Synthé, the following are required:

- Python 3
- Python bindings for the Z3 prover
- D3
- Dagre D3 installed in a folder called learner/node_modules
- Rasa

## Running Synthé

From the learner directory, execute

```
./synthe
```

Note that without microphones and a robot hooked up to Synthé,capturing designers' intent is limited to the command line. When you press record, you have the option to enter the inputs and outputs of the human and the robot manually on the command line.
