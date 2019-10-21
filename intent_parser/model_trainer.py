from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer, Metadata, Interpreter
from rasa_nlu import config

import sys

def train_model(data_file, config_file=None):
    """
    :param data_file: string filepath to training data file. The format of
    this file must conform to rasaNLU specifications
    :param config_file: string filepath to the spacy config file.
    Post: A new model directory was created in ./projects/default/
    Return: The new model directory's filepath
    """
    print('Training new model. This will take a minute')
    training_data = load_data(data_file)
    trainer = Trainer(config.load(config_file))
    trainer.train(training_data)
    model_directory = trainer.persist('./projects')
    return model_directory

if __name__ == "__main__":
    trainfile = sys.argv[1]
    configfile = sys.argv[2]
    train_model(trainfile, configfile)
