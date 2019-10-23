# Synthé

Synthé is atool that allows designers of human-robot interactions to bodystorm their interactions. Bodystorming is an embodied design method that involves brainstorming via role-playing, and in an environment that is true to the product being designed [1].

In bodystorming, a design team acts out an exampleinteraction between a human and a robot, where one user plays the human and another plays the robot. Synthé records the speech and getures of the designers, and employs program synthesis to create an executable human-robot interaction program. This program can be simulated on a Nao robot.

# Software and Hardware

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

## Software Prerequisites and Installation

To install Synthé, the following are required:

- Python 3
- Python bindings for the Z3 prover
- D3
- Dagre D3
- Rasa-nlu
- PyAudio
- sounddevice

Once the above libraries are installed, pull the code from this repository.

```
git clone https://github.com/Wisc-HCI/Synthe.git
```

To use D3 and Dagre D3, place the node_modules folder in /learner.

## Hardware Prerequisites

### Microphones

At minimum, Synthé requires only one microphone be connected to the computer that it is run on. This can be the default microphone on any modern laptop. To acheive full functionality of Synthé, two microphones should be connected. Synthé will automatically detect the presence of microphones.

For your speech to be recognized, you will need to have an account with IBM Watson. Generate username and password credentials with your account, and place them in the ```intent_parser/ibm_keys.json``` file.

### Gesture Recognition

Synthé currently supports gesture recognition through the Myo Armband [2]. Gesture recognition is not required to run Synthé, though. To support the usage of any device that records acceleration and orientation, Synthé interfaces can interface with these technologies through a server-client setup. Support for other gesture recognition technologies must be developed separately.

If you plan on using the Myo armband, you will need to install the SDK from https://support.getmyo.com/hc/en-us/articles/360018409792-Myo-Connect-SDK-and-firmware-downloads.

### Robot Simulation

Synthé also supports the ability to simulate programs created through its program synthesis engine on a real robot. The only robot currently supported is Nao [3]. To support the usage of any robot that simulates programs created through Synthé, Synthé interfaces with these robots through a server-client setup. Support for other robots must be developed separately.

If you plan on simulating the code on a Nao robot, you will need to install the naoqi SDK (version 2.1.4) from softbank robotics. Place the SDK in the /robot folder. Additionally, you will need a credentials file for Google Cloud, and will need to create a ```GOOGLE_APPLICATION_CREDENTIALS``` environment variable with the location of this file.

# Running Synthé

From the top directory, execute ```./synthe```.

Note that without microphones and a robot hooked up to Synthé, capturing designers' intent is limited to the command line. When you press record, you have the option to enter the inputs and outputs of the human and the robot manually on the command line.

# Citing Synthé

To cite Synthé, please use the following bibtex:

```
@inproceedings{porfirio2019bodystorming,
  title={Bodystorming Human-Robot Interactions},
  author={Porfirio, David and Fisher, Evan and Saupp{\'e}, Allison and Albarghouthi, Aws and Mutlu, Bilge},
  booktitle={Proceedings of the 32nd Annual ACM Symposium on User Interface Software and Technology},
  year={2019}
}
```

# References

[1]: Oulasvirta, A., Kurvinen, E., & Kankainen, T. (2003). Understanding contexts by being there: case studies in bodystorming. Personal and ubiquitous computing, 7(2), 125-134.

[2]: The developer blog for myo: https://developerblog.myo.com/

[3]: Pot, E., Monceaux, J., Gelin, R., & Maisonnier, B. (2009, September). Choregraphe: a graphical tool for humanoid robot programming. In RO-MAN 2009-The 18th IEEE International Symposium on Robot and Human Interactive Communication (pp. 46-51). IEEE.
