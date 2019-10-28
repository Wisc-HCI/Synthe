#!/bin/bash

datafile=$1
if [ ! -d "./projects" ]; then
	mkdir projects
fi

python3 model_trainer.py ./data/help_desk.json ./config/config_spacy.yml
cd projects
mv projects/model* projects/default
